"""
Block selection for Duration and Inflation (per optimization_duration_spec, optimization_inflation_spec).

Duration: candidate scoring by downside hedge (beta_down ≤ 0.2), worst-Growth-month score, ES95.
Inflation: candidate scoring by Type1/Type2 stress windows, ES95; optional TIPS/GOLD/COMM floors.
Returns selected internal weights for Duration and Inflation; optimizer enforces them via equality constraints.
"""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from policy_math.feasibility import (
    FeasibilityContext,
    check_feasible,
    resolve_rc_asset_cap as _feasibility_rc_cap,
    resolve_weight_caps,
)
from src.config_schema import GROWTH_EM_DEBT_KEY, GROWTH_HY_KEY
from src.risk_contrib import cov_matrix_monthly
from src.optimization import (
    RISK_BUDGET_BLOCKS,
    get_risk_portfolio_tickers,
    ticker_to_block_map,
)

GROWTH_PROXY = "VOO"
N_WORST_GROWTH = 12


def _resolve_growth_proxy(monthly_returns: pd.DataFrame, config: Any) -> str | None:
    """
    Equity series for worst-Growth-month / stress-window scoring (duration & inflation selection).
    Prefer VOO; if not in universe, use first growth_core_candidate with history, else VTI/VT.
    """
    if GROWTH_PROXY in monthly_returns.columns:
        return GROWTH_PROXY
    candidates = getattr(config, "growth_core_candidates", None)
    if isinstance(config, dict) and candidates is None:
        candidates = config.get("growth_core_candidates")
    if not candidates:
        candidates = ["VOO", "VT", "VTI"]
    for t in candidates:
        if t and str(t) in monthly_returns.columns:
            return str(t)
    for t in ("VT", "VTI"):
        if t in monthly_returns.columns:
            return t
    return None
ES95_BASELINE_TOL = 0.003
BETA_DOWN_SOFT_PASS = 0.2


def _get_duration_universe(config: Any, blocks: dict[str, list[str]]) -> list[str]:
    """Build Duration universe from config (duration_int_ticker, duration_long_ticker, duration_ig_ticker) or blocks."""
    int_t = getattr(config, "duration_int_ticker", None) or (config.get("duration_int_ticker") if isinstance(config, dict) else None)
    long_t = getattr(config, "duration_long_ticker", None) or (config.get("duration_long_ticker") if isinstance(config, dict) else None)
    ig_t = getattr(config, "duration_ig_ticker", None) or (config.get("duration_ig_ticker") if isinstance(config, dict) else None)
    out = [t for t in (int_t, long_t, ig_t) if t]
    if out:
        return out
    return list(blocks.get("Duration", []))


def _get_inflation_universe(config: Any, blocks: dict[str, list[str]]) -> list[str]:
    """Build Inflation universe from config (tips_ticker, gold_ticker, comm_ticker) or blocks."""
    tips = getattr(config, "tips_ticker", None) or (config.get("tips_ticker") if isinstance(config, dict) else None)
    gold = getattr(config, "gold_ticker", None) or (config.get("gold_ticker") if isinstance(config, dict) else None)
    comm = getattr(config, "comm_ticker", None) or (config.get("comm_ticker") if isinstance(config, dict) else None)
    out = [t for t in (tips, gold, comm) if t]
    if out:
        return out
    return list(blocks.get("Inflation", []))


def _duration_candidates(uni: list[str], int_t: str | None, long_t: str | None, ig_t: str | None) -> list[dict]:
    """Build Duration candidate mixes per optimization_duration_spec A1."""
    if len(uni) == 1:
        return [{"name": "D0", "weights": {uni[0]: 1.0}}]
    order = [t for t in (int_t, long_t, ig_t) if t and t in uni]
    if not order:
        order = sorted(uni)
    if len(uni) == 2:
        a, b = order[0], order[1]
        return [
            {"name": "D1", "weights": {a: 1.0, b: 0.0}},
            {"name": "D2", "weights": {a: 0.5, b: 0.5}},
            {"name": "D3", "weights": {a: 0.0, b: 1.0}},
            {"name": "D4", "weights": {a: 0.7, b: 0.3}},
            {"name": "D5", "weights": {a: 0.3, b: 0.7}},
        ]
    # 3 tickers: INT, LONG, IG
    a, b = order[0], order[1]
    c = order[2] if len(order) > 2 else None
    cands = [
        {"name": "D1", "weights": {a: 1.0, b: 0.0, **({c: 0.0} if c else {})}},
        {"name": "D2", "weights": {a: 0.0, b: 1.0, **({c: 0.0} if c else {})}},
        {"name": "D3", "weights": {a: 0.7, b: 0.3, **({c: 0.0} if c else {})}},
        {"name": "D4", "weights": {a: 0.5, b: 0.5, **({c: 0.0} if c else {})}},
    ]
    if c:
        cands.append({"name": "D5", "weights": {a: 0.4, b: 0.4, c: 0.2}})
    for cnd in cands:
        cnd["weights"] = {k: v for k, v in cnd["weights"].items() if v > 0}
    return cands


def _inflation_candidates(
    uni: list[str],
    tips_t: str | None,
    gold_t: str | None,
    comm_t: str | None,
) -> list[dict]:
    """Build Inflation candidate mixes per optimization_inflation_spec B1."""
    if len(uni) == 1:
        return [{"name": "I0", "weights": {uni[0]: 1.0}}]
    order = [t for t in (tips_t, gold_t, comm_t) if t and t in uni]
    if not order:
        order = sorted(uni)
    if len(uni) == 2:
        a, b = order[0], order[1]
        return [
            {"name": "I1", "weights": {a: 0.7, b: 0.3}},
            {"name": "I2", "weights": {a: 0.5, b: 0.5}},
            {"name": "I3", "weights": {a: 0.3, b: 0.7}},
        ]
    # 3-mechanism: TIPS ≥ 0.30, GOLD ≥ 0.25, COMM ≥ 0.15
    t, g, c = (tips_t or order[0]), (gold_t or order[1]), (comm_t or order[2])
    return [
        {"name": "I1", "weights": {t: 0.30, g: 0.25, c: 0.45}},
        {"name": "I2", "weights": {t: 0.40, g: 0.25, c: 0.35}},
        {"name": "I3", "weights": {t: 0.50, g: 0.25, c: 0.25}},
        {"name": "I4", "weights": {t: 0.35, g: 0.35, c: 0.30}},
        {"name": "I5", "weights": {t: 0.45, g: 0.35, c: 0.20}},
    ]


def _candidate_return_series(weights: dict[str, float], returns_df: pd.DataFrame) -> pd.Series | None:
    """Weighted monthly return series for a candidate; None if any ticker missing."""
    common = [t for t in weights if t in returns_df.columns]
    if len(common) < len(weights):
        return None
    out = pd.Series(0.0, index=returns_df.index)
    for t in common:
        out = out + weights[t] * returns_df[t]
    return out


def _es95(series: pd.Series) -> float:
    """Mean of bottom 5% monthly returns."""
    s = series.dropna()
    if len(s) < 4:
        return float(s.min()) if len(s) else 0.0
    n = max(1, int(round(0.05 * len(s))))
    return float(s.nsmallest(n).mean())


def _check_portfolio_feasible(
    w_dict: dict[str, float],
    cols: list[str],
    cov: np.ndarray,
    ticker_to_block: dict[str, str],
    rc_cap: float,
    min_weight: float,
    bounds: list[tuple[float, float]],
) -> bool:
    """True if w_dict satisfies per-asset RC <= rc_cap and weight bounds."""
    w = np.array([w_dict.get(t, 0.0) for t in cols])
    if np.abs(w.sum() - 1.0) > 1e-6:
        return False
    var_p = w @ cov @ w
    if var_p <= 1e-16:
        return True
    pc = (w * (cov @ w)) / var_p
    for i, t in enumerate(cols):
        if pc[i] > rc_cap + 1e-9:
            return False
        lo, hi = bounds[i]
        if w[i] < lo - 1e-9 or w[i] > hi + 1e-9:
            return False
    return True


def select_duration_block(
    monthly_returns: pd.DataFrame,
    blocks: dict[str, list[str]],
    config: Any,
    rc_block_targets: dict[str, float],
    window_months: int,
    baseline_duration_weights: dict[str, float] | None = None,
) -> dict[str, Any]:
    """
    Select Duration block internal weights per optimization_duration_spec.
    Returns dict with status "OK" | "FAIL_DATA" | "FAIL_FEASIBILITY", and on OK:
    selected_internal_weights, selected_candidate_name, diagnostics, selection_method.
    """
    growth_proxy = _resolve_growth_proxy(monthly_returns, config)
    if growth_proxy is None:
        return {"status": "FAIL_DATA", "reason": "Growth proxy data missing (add VOO or a growth_core_candidate with history)"}

    duration_uni = _get_duration_universe(config, blocks)
    if not duration_uni:
        return {"status": "OK", "selection_method": "SKIP_INTERNAL_SELECTION", "reason": "No Duration tickers", "selected_internal_weights": None}

    int_t = getattr(config, "duration_int_ticker", None) or (config.get("duration_int_ticker") if isinstance(config, dict) else None)
    long_t = getattr(config, "duration_long_ticker", None) or (config.get("duration_long_ticker") if isinstance(config, dict) else None)
    ig_t = getattr(config, "duration_ig_ticker", None) or (config.get("duration_ig_ticker") if isinstance(config, dict) else None)

    # Only tickers that have data
    duration_uni = [t for t in duration_uni if t in monthly_returns.columns]
    if not duration_uni:
        return {"status": "FAIL_DATA", "reason": "No Duration tickers with data"}

    if len(duration_uni) == 1:
        return {
            "status": "OK",
            "selection_method": "SKIP_INTERNAL_SELECTION",
            "reason": "Single Duration ticker",
            "selected_internal_weights": {duration_uni[0]: 1.0},
            "selected_candidate_name": "D0",
        }

    candidates = _duration_candidates(duration_uni, int_t, long_t, ig_t)
    r_voo = monthly_returns[growth_proxy].dropna()
    bad_months = r_voo < 0
    worst_12_idx = r_voo.nsmallest(N_WORST_GROWTH).index

    # A2: Downside hedge — discard beta_down > 0.2
    passed = []
    for cnd in candidates:
        r_c = _candidate_return_series(cnd["weights"], monthly_returns)
        if r_c is None:
            continue
        common = r_voo.index.intersection(r_c.index).dropna(how="any")
        if len(common) < 6:
            continue
        x = r_voo.reindex(common).dropna().values
        y = r_c.reindex(common).dropna().values
        if len(x) != len(y) or len(x) < 4:
            continue
        bad = bad_months.reindex(common).fillna(False)
        if bad.sum() < 3:
            # full sample
            beta_down = np.cov(y, x, ddof=1)[0, 1] / (np.var(x, ddof=1) + 1e-20)
            low_sample_beta = True
        else:
            xb, yb = x[bad.values], y[bad.values]
            beta_down = np.cov(yb, xb, ddof=1)[0, 1] / (np.var(xb, ddof=1) + 1e-20)
            low_sample_beta = False
        if beta_down > BETA_DOWN_SOFT_PASS:
            continue
        avg_worst = float(r_c.reindex(worst_12_idx).mean()) if worst_12_idx.isin(r_c.index).any() else 0.0
        worst_month = float(r_c.reindex(worst_12_idx).min()) if worst_12_idx.isin(r_c.index).any() else 0.0
        score = avg_worst - 0.5 * abs(worst_month)
        es95 = _es95(r_c)
        passed.append({
            **cnd,
            "beta_down": float(beta_down),
            "low_sample_beta": low_sample_beta,
            "score_duration": score,
            "avg_ret_in_worst12": avg_worst,
            "worst_month_in_worst": worst_month,
            "ES95": es95,
            "r_c": r_c,
        })

    if not passed:
        return {"status": "FAIL_FEASIBILITY", "reason": "No Duration candidate passed downside hedge (beta_down ≤ 0.2)"}

    baseline_es95 = None
    if baseline_duration_weights:
        r_baseline = _candidate_return_series(baseline_duration_weights, monthly_returns)
        if r_baseline is not None:
            baseline_es95 = _es95(r_baseline)

    # A4: ES95 filter
    if baseline_es95 is not None:
        passed = [p for p in passed if p["ES95"] >= baseline_es95 - ES95_BASELINE_TOL]

    if not passed:
        return {"status": "FAIL_FEASIBILITY", "reason": "No Duration candidate passed ES95 baseline filter"}

    # Sort by score_duration desc, ES95 desc
    passed.sort(key=lambda p: (-p["score_duration"], -p["ES95"]))

    # A5: Feasibility in full RiskPortfolio context
    risk_tickers = get_risk_portfolio_tickers(blocks)
    cols = [t for t in risk_tickers if t in monthly_returns.columns]
    ret = monthly_returns[cols].iloc[-window_months:].dropna(how="any")
    if len(ret) < 11:
        return {"status": "FAIL_DATA", "reason": "Insufficient months for feasibility check"}
    use_shrinkage = getattr(config, "covariance_shrinkage", False) if not isinstance(config, dict) else config.get("covariance_shrinkage", False)
    cov = cov_matrix_monthly(ret, ddof=1, use_shrinkage=use_shrinkage).values
    n = len(cols)
    ticker_to_block = ticker_to_block_map(blocks)
    rb = rc_block_targets or {}
    rb_g = float(rb.get("Growth", 1.0 / 3))
    rb_d = float(rb.get("Duration", 1.0 / 3))
    rb_i = float(rb.get("Inflation", 1.0 / 3))
    total_rb = rb_g + rb_d + rb_i
    if total_rb <= 0:
        total_rb = 1.0
    rb_g, rb_d, rb_i = rb_g / total_rb, rb_d / total_rb, rb_i / total_rb
    rc_cap = _feasibility_rc_cap(n, equity_only=(rb_g >= 0.90))
    min_weight = 0.01
    growth_core = getattr(config, "growth_core_candidates", None) or config.get("growth_core_candidates", ["VOO", "VT", "VTI"])
    from src.optimization import build_bounds
    bounds = build_bounds(cols, ticker_to_block, list(growth_core), n, min_weight, None, rb_g)
    growth_tickers = [t for t in cols if ticker_to_block.get(t) == "Growth"]
    inflation_tickers = [t for t in cols if ticker_to_block.get(t) == "Inflation"]
    duration_tickers = [t for t in cols if ticker_to_block.get(t) == "Duration"]

    for p in passed:
        w_dict = {}
        for t in cols:
            if ticker_to_block.get(t) == "Growth":
                w_dict[t] = rb_g / len(growth_tickers) if growth_tickers else 0.0
            elif ticker_to_block.get(t) == "Duration":
                w_dict[t] = rb_d * p["weights"].get(t, 0.0)
            elif ticker_to_block.get(t) == "Inflation":
                w_dict[t] = rb_i / len(inflation_tickers) if inflation_tickers else 0.0
            else:
                w_dict[t] = 0.0
        if _check_portfolio_feasible(w_dict, cols, cov, ticker_to_block, rc_cap, min_weight, bounds):
            return {
                "status": "OK",
                "selected_candidate_name": p["name"],
                "selected_internal_weights": p["weights"],
                "diagnostics": {
                    "beta_down": round(p["beta_down"], 4),
                    "avg_ret_in_worst12": round(p["avg_ret_in_worst12"], 4),
                    "worst_month_in_worst": round(p["worst_month_in_worst"], 4),
                    "ES95": round(p["ES95"], 4),
                    "low_sample_beta": p["low_sample_beta"],
                },
            }

    return {"status": "FAIL_FEASIBILITY", "reason": "No Duration candidate satisfies caps", "violated_constraints": []}


def select_inflation_block(
    monthly_returns: pd.DataFrame,
    blocks: dict[str, list[str]],
    config: Any,
    rc_block_targets: dict[str, float],
    window_months: int,
    duration_proxy_ticker: str | None,
    baseline_inflation_weights: dict[str, float] | None = None,
) -> dict[str, Any]:
    """
    Select Inflation block internal weights per optimization_inflation_spec.
    duration_proxy_ticker: for Type1 months (prefer duration_int_ticker, else duration_long_ticker).
    """
    growth_proxy = _resolve_growth_proxy(monthly_returns, config)
    if growth_proxy is None:
        return {"status": "FAIL_DATA", "reason": "Growth proxy data missing (add VOO or a growth_core_candidate with history)"}

    inflation_uni = _get_inflation_universe(config, blocks)
    if not inflation_uni:
        return {"status": "OK", "selection_method": "SKIP_INTERNAL_SELECTION", "reason": "No Inflation tickers", "selected_internal_weights": None}

    inflation_uni = [t for t in inflation_uni if t in monthly_returns.columns]
    if not inflation_uni:
        return {"status": "FAIL_DATA", "reason": "No Inflation tickers with data"}

    tips_t = getattr(config, "tips_ticker", None) or (config.get("tips_ticker") if isinstance(config, dict) else None)
    gold_t = getattr(config, "gold_ticker", None) or (config.get("gold_ticker") if isinstance(config, dict) else None)
    comm_t = getattr(config, "comm_ticker", None) or (config.get("comm_ticker") if isinstance(config, dict) else None)

    if len(inflation_uni) == 1:
        return {
            "status": "OK",
            "selection_method": "SKIP_INTERNAL_SELECTION",
            "reason": "Single Inflation ticker",
            "selected_internal_weights": {inflation_uni[0]: 1.0},
            "selected_candidate_name": "I0",
        }

    candidates = _inflation_candidates(inflation_uni, tips_t, gold_t, comm_t)
    r_voo = monthly_returns[growth_proxy].dropna()
    worst_12_idx = r_voo.nsmallest(N_WORST_GROWTH).index

    # Type1: growth proxy < 0 and duration_proxy < 0
    type1_idx = None
    if duration_proxy_ticker and duration_proxy_ticker in monthly_returns.columns:
        r_dur = monthly_returns[duration_proxy_ticker].dropna()
        common = r_voo.index.intersection(r_dur.index)
        mask = (r_voo.reindex(common) < 0) & (r_dur.reindex(common) < 0)
        type1_idx = common[mask].index

    # Type2: growth proxy < 0 and gold > 0
    type2_idx = None
    if gold_t and gold_t in monthly_returns.columns:
        r_gold = monthly_returns[gold_t].dropna()
        common = r_voo.index.intersection(r_gold.index)
        mask = (r_voo.reindex(common) < 0) & (r_gold.reindex(common) > 0)
        type2_idx = common[mask].index

    use_fallback = (type1_idx is None or len(type1_idx) < 12) and (type2_idx is None or len(type2_idx) < 12)
    score_idx = worst_12_idx

    scored = []
    for cnd in candidates:
        r_c = _candidate_return_series(cnd["weights"], monthly_returns)
        if r_c is None:
            continue
        if type1_idx is not None and len(type1_idx) >= 12:
            avg1 = float(r_c.reindex(type1_idx).mean())
            low1 = False
        else:
            avg1 = float(r_c.reindex(score_idx).mean()) if score_idx.isin(r_c.index).any() else 0.0
            low1 = use_fallback
        if type2_idx is not None and len(type2_idx) >= 12:
            avg2 = float(r_c.reindex(type2_idx).mean())
            low2 = False
        else:
            avg2 = float(r_c.reindex(score_idx).mean()) if score_idx.isin(r_c.index).any() else 0.0
            low2 = use_fallback
        worst_all = float(r_c.min())
        score = 0.6 * avg1 + 0.4 * avg2 - 0.2 * abs(worst_all)
        es95 = _es95(r_c)
        scored.append({
            **cnd,
            "score_inflation": score,
            "avg_ret_type1": avg1,
            "avg_ret_type2": avg2,
            "worst_month_all": worst_all,
            "ES95": es95,
            "low_sample_type1": low1,
            "low_sample_type2": low2,
        })

    if not scored:
        return {"status": "FAIL_FEASIBILITY", "reason": "No Inflation candidate with data"}

    baseline_es95 = None
    if baseline_inflation_weights:
        r_baseline = _candidate_return_series(baseline_inflation_weights, monthly_returns)
        if r_baseline is not None:
            baseline_es95 = _es95(r_baseline)
    if baseline_es95 is not None:
        scored = [p for p in scored if p["ES95"] >= baseline_es95 - ES95_BASELINE_TOL]
    if not scored:
        return {"status": "FAIL_FEASIBILITY", "reason": "No Inflation candidate passed ES95 baseline filter"}

    scored.sort(key=lambda p: (-p["score_inflation"], -p["ES95"]))

    risk_tickers = get_risk_portfolio_tickers(blocks)
    cols = [t for t in risk_tickers if t in monthly_returns.columns]
    ret = monthly_returns[cols].iloc[-window_months:].dropna(how="any")
    if len(ret) < 11:
        return {"status": "FAIL_DATA", "reason": "Insufficient months for Inflation feasibility check"}
    use_shrinkage = getattr(config, "covariance_shrinkage", False) if not isinstance(config, dict) else config.get("covariance_shrinkage", False)
    cov = cov_matrix_monthly(ret, ddof=1, use_shrinkage=use_shrinkage).values
    n = len(cols)
    ticker_to_block = ticker_to_block_map(blocks)
    rb = rc_block_targets or {}
    rb_g = float(rb.get("Growth", 1.0 / 3))
    rb_d = float(rb.get("Duration", 1.0 / 3))
    rb_i = float(rb.get("Inflation", 1.0 / 3))
    total_rb = rb_g + rb_d + rb_i
    if total_rb <= 0:
        total_rb = 1.0
    rb_g, rb_d, rb_i = rb_g / total_rb, rb_d / total_rb, rb_i / total_rb
    rc_cap = _feasibility_rc_cap(n, equity_only=(rb_g >= 0.90))
    min_weight = 0.01
    growth_core = getattr(config, "growth_core_candidates", None) or config.get("growth_core_candidates", ["VOO", "VT", "VTI"])
    from src.optimization import build_bounds
    bounds = build_bounds(cols, ticker_to_block, list(growth_core), n, min_weight, None, rb_g)
    growth_tickers = [t for t in cols if ticker_to_block.get(t) == "Growth"]
    duration_tickers = [t for t in cols if ticker_to_block.get(t) == "Duration"]
    inflation_tickers = [t for t in cols if ticker_to_block.get(t) == "Inflation"]

    for p in scored:
        w_dict = {}
        for t in cols:
            if ticker_to_block.get(t) == "Growth":
                w_dict[t] = rb_g / len(growth_tickers) if growth_tickers else 0.0
            elif ticker_to_block.get(t) == "Duration":
                w_dict[t] = rb_d / len(duration_tickers) if duration_tickers else 0.0
            elif ticker_to_block.get(t) == "Inflation":
                w_dict[t] = rb_i * p["weights"].get(t, 0.0)
            else:
                w_dict[t] = 0.0
        if _check_portfolio_feasible(w_dict, cols, cov, ticker_to_block, rc_cap, min_weight, bounds):
            return {
                "status": "OK",
                "selected_candidate_name": p["name"],
                "selected_internal_weights": p["weights"],
                "diagnostics": {
                    "avg_ret_type1": round(p["avg_ret_type1"], 4),
                    "avg_ret_type2": round(p["avg_ret_type2"], 4),
                    "worst_month_all": round(p["worst_month_all"], 4),
                    "ES95": round(p["ES95"], 4),
                    "low_sample_type1": p["low_sample_type1"],
                    "low_sample_type2": p["low_sample_type2"],
                },
            }

    return {"status": "FAIL_FEASIBILITY", "reason": "No Inflation candidate satisfies caps", "violated_constraints": []}


def apply_block_selection(
    blocks: dict[str, list[str]],
    config: Any = None,
    monthly_returns: Any = None,
    window_months: int = 120,
    rc_block_targets: dict[str, float] | None = None,
    baseline_duration_weights: dict[str, float] | None = None,
    baseline_inflation_weights: dict[str, float] | None = None,
) -> dict[str, Any]:
    """
    Apply Duration and Inflation block selection. Returns dict:
    - status: "OK" | "FAIL_DATA" | "FAIL_FEASIBILITY"
    - blocks: (unchanged)
    - duration_internal_weights: dict or None
    - inflation_internal_weights: dict or None
    - duration_diagnostics, inflation_diagnostics (if any)
    - reason, violated_constraints (on failure)
    """
    if monthly_returns is None or monthly_returns.empty:
        return {"status": "OK", "blocks": dict(blocks), "duration_internal_weights": None, "inflation_internal_weights": None}

    rc = rc_block_targets or {}
    window = window_months or 120

    # Duration proxy for Inflation Type1
    dur_int = getattr(config, "duration_int_ticker", None) if config else None
    dur_long = getattr(config, "duration_long_ticker", None) if config else None
    if isinstance(config, dict):
        dur_int = dur_int or config.get("duration_int_ticker")
        dur_long = dur_long or config.get("duration_long_ticker")
    duration_proxy = dur_int or dur_long

    result = {
        "status": "OK",
        "blocks": dict(blocks),
        "duration_internal_weights": None,
        "inflation_internal_weights": None,
        "duration_diagnostics": None,
        "inflation_diagnostics": None,
    }

    # 1) Duration selection
    if blocks.get("Duration"):
        dr = select_duration_block(
            monthly_returns, blocks, config or {}, rc, window, baseline_duration_weights
        )
        if dr.get("status") == "FAIL_DATA":
            return {"status": "FAIL_DATA", "reason": dr.get("reason", "Duration selection failed"), "blocks": blocks}
        if dr.get("status") == "FAIL_FEASIBILITY":
            return {"status": "FAIL_FEASIBILITY", "reason": dr.get("reason", ""), "violated_constraints": dr.get("violated_constraints", []), "blocks": blocks}
        result["duration_internal_weights"] = dr.get("selected_internal_weights")
        result["duration_diagnostics"] = dr.get("diagnostics")

    # 2) Inflation selection
    if blocks.get("Inflation"):
        ir = select_inflation_block(
            monthly_returns, blocks, config or {}, rc, window, duration_proxy, baseline_inflation_weights
        )
        if ir.get("status") == "FAIL_DATA":
            return {"status": "FAIL_DATA", "reason": ir.get("reason", "Inflation selection failed"), "blocks": blocks}
        if ir.get("status") == "FAIL_FEASIBILITY":
            return {"status": "FAIL_FEASIBILITY", "reason": ir.get("reason", ""), "violated_constraints": ir.get("violated_constraints", []), "blocks": blocks}
        result["inflation_internal_weights"] = ir.get("selected_internal_weights")
        result["inflation_diagnostics"] = ir.get("diagnostics")

    return result
