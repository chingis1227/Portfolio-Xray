"""
Robust Mean–Variance λ calibration helpers.

Evaluates candidate portfolios against **config IPS fields** (targets / limits) and optional
``robust_mv_calibration`` YAML overrides. Does **not** alter ``run_stress`` internals or mandate
gate implementation in ``run_report.py`` — callers reuse ``portfolio_valid`` and scenario rows.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Literal, Sequence

import yaml

# Mandatory synthetic scenarios (stress_testing_spec §2) — loss gate vs mandate MaxDD when enabled.
MANDATORY_SYNTHETIC_SCENARIO_IDS: frozenset[str] = frozenset(
    {
        "equity_shock",
        "credit_shock",
        "rates_shock",
        "inflation_stagflation",
        "liquidity_shock",
        "recession_severe",
    }
)

MandateClass = Literal["pass", "fail", "borderline"]

# Default λ grids for ``run_robust_mv_lambda_calibration.py`` (mandate scoring only; not read from config).
LAMBDA_GRID_PRIMARY: tuple[float, ...] = (0.1, 0.2, 0.3, 0.5, 0.8, 1.0)
LAMBDA_GRID_EXTENDED: tuple[float, ...] = (1.5, 2.0, 3.0, 5.0, 7.5, 10.0)

# Human-readable mandate constraint labels for calibration summaries (no ticker-level detail).
MANDATE_FAILURE_LABELS: dict[str, str] = {
    "mandate_max_drawdown_full_history": "Mandate maximum drawdown (full historical backtest)",
    "target_vol_annual": "Target volatility limit",
    "max_single_security_weight_pct": "Maximum single-asset weight limit",
    "synthetic_stress_loss": "Mandatory synthetic stress loss versus mandate drawdown limit",
    "max_top1_rc_pct": "Synthetic scenario RC concentration — largest asset share (calibration YAML)",
    "max_top3_rc_sum_pct": "Synthetic scenario RC concentration — top-three sum (calibration YAML)",
}

NO_FEASIBLE_LAMBDA_POSSIBLE_CAUSES: tuple[str, ...] = (
    "The λ grid may be too narrow: tested values may not be large enough for portfolio variance to dominate shrunk expected returns (consider widening upward, e.g. 5, 10, 20, 50).",
    "The eligible universe may be collectively risk-seeking: if low-volatility or cash-like exposures are scarce, even defensive Robust MV allocations can breach volatility or drawdown limits.",
    "Weight constraints may block defensive positioning: minimum weights, caps, feasibility caps, Young caps, or optional YAML RC caps can prevent reallocating sufficient capital toward lower-risk sleeves.",
    "Shrunk expected returns may still favor riskier sleeves: James–Stein shrinkage reduces estimation noise but does not eliminate cross-sectional expected-return dispersion, so the optimum may retain riskier weights.",
)

NO_FEASIBLE_LAMBDA_SUGGESTED_ACTIONS: tuple[str, ...] = (
    "Expand the λ grid (especially toward larger λ) and re-run calibration.",
    "Review the eligible universe for defensive and cash-like capacity relative to mandate risk limits.",
    "Review bounds and calibration caps (min/max weights, feasibility caps, Young caps, optional synthetic RC limits) for feasibility of a defensive allocation.",
    "Confirm explicit volatility and maximum-drawdown limits in configuration reflect the intended mandate.",
)


def load_optional_robust_mv_calibration_block(config_path: Path | None) -> dict[str, Any]:
    """
    Read optional ``robust_mv_calibration:`` map from config.yml (not part of PortfolioConfig).

    Supported keys (all optional):
    - max_top1_rc_pct: float — max allowed synthetic RC Top1 share (0–1).
    - max_top3_rc_sum_pct: float — max allowed synthetic RC Top3 sum (0–1).
    """
    if config_path is None or not config_path.is_file():
        return {}
    raw = yaml.safe_load(Path(config_path).read_text(encoding="utf-8")) or {}
    blk = raw.get("robust_mv_calibration")
    return dict(blk) if isinstance(blk, dict) else {}


def read_es95_from_var_es_csv(csv_path: Path) -> float | None:
    """Historical ES 95% from ``var_es_10y.csv`` written by ``run_portfolio_report_for_weights``."""
    if not csv_path.is_file():
        return None
    try:
        import pandas as pd

        df = pd.read_csv(csv_path)
        if df.empty or "es_95" not in df.columns:
            return None
        v = float(df.iloc[0]["es_95"])
        return v if v == v else None
    except Exception:
        return None


def max_top1_rc_synthetic(stress_report: dict[str, Any] | None) -> float | None:
    """Maximum ``top1_rc_pct`` across mandatory synthetic rows."""
    if not stress_report:
        return None
    best: float | None = None
    for row in stress_report.get("scenario_results") or []:
        sid = row.get("scenario_id")
        if sid not in MANDATORY_SYNTHETIC_SCENARIO_IDS:
            continue
        v = row.get("top1_rc_pct")
        if v is None:
            continue
        try:
            fv = float(v)
        except (TypeError, ValueError):
            continue
        best = fv if best is None else max(best, fv)
    return best


def max_top3_rc_sum_synthetic(stress_report: dict[str, Any] | None) -> float | None:
    """Maximum ``top3_rc_sum_pct`` across mandatory synthetic rows."""
    if not stress_report:
        return None
    best: float | None = None
    for row in stress_report.get("scenario_results") or []:
        sid = row.get("scenario_id")
        if sid not in MANDATORY_SYNTHETIC_SCENARIO_IDS:
            continue
        v = row.get("top3_rc_sum_pct")
        if v is None:
            continue
        try:
            fv = float(v)
        except (TypeError, ValueError):
            continue
        best = fv if best is None else max(best, fv)
    return best


def synthetic_mandatory_loss_detail(
    stress_report: dict[str, Any] | None,
) -> tuple[bool, list[str]]:
    """True iff each mandatory synthetic row exists and reports ``pass`` True."""
    if not stress_report:
        return False, ["stress_report_missing"]
    failures: list[str] = []
    seen: set[str] = set()
    for row in stress_report.get("scenario_results") or []:
        sid = row.get("scenario_id")
        if sid not in MANDATORY_SYNTHETIC_SCENARIO_IDS:
            continue
        seen.add(str(sid))
        if row.get("pass") is True:
            continue
        failures.append(str(sid))
    missing = sorted(MANDATORY_SYNTHETIC_SCENARIO_IDS - seen)
    failures.extend(missing)
    return len(failures) == 0, failures


def classify_robust_mv_mandate(
    *,
    portfolio_valid: bool | None,
    target_vol_annual: float | None,
    vol_annual_10y: float | None,
    target_max_drawdown_pct: float | None,
    mandate_max_drawdown_realized: float | None,
    max_single_security_weight_pct: float | None,
    weights: dict[str, float],
    stress_report: dict[str, Any] | None,
    calibration_limits: dict[str, Any],
    enforce_synthetic_vs_mandate_dd: bool,
) -> dict[str, Any]:
    """
    Aggregate IPS-aligned checks. ``portfolio_valid`` mirrors ``run_report`` mandate MaxDD gate.

    When ``enforce_synthetic_vs_mandate_dd`` and ``target_max_drawdown_pct`` are set, mandatory
    synthetic scenarios must report ``pass`` True (same loss limit contract as stress spec).
    """
    failures: list[str] = []
    slack: dict[str, float | None] = {}

    ok_dd = bool(portfolio_valid)
    if not ok_dd:
        failures.append("mandate_max_drawdown_full_history")
    slack["mandate_max_dd_hist"] = None
    if mandate_max_drawdown_realized is not None and target_max_drawdown_pct is not None:
        lim = float(target_max_drawdown_pct)
        realized = float(mandate_max_drawdown_realized)
        slack["mandate_max_dd_hist"] = float(realized - lim)

    ok_vol = True
    slack["target_vol"] = None
    if target_vol_annual is not None and vol_annual_10y is not None:
        tv = float(target_vol_annual)
        vol = float(vol_annual_10y)
        ok_vol = vol <= tv + 1e-12
        slack["target_vol"] = float(tv - vol)
        if not ok_vol:
            failures.append("target_vol_annual")

    ok_cap = True
    slack["max_single_asset_weight"] = None
    if max_single_security_weight_pct is not None:
        cap = float(max_single_security_weight_pct)
        pos = [float(w) for w in (weights or {}).values() if float(w) > 1e-15]
        mx = max(pos) if pos else 0.0
        ok_cap = mx <= cap + 1e-9
        slack["max_single_asset_weight"] = float(cap - mx)
        if not ok_cap:
            failures.append("max_single_security_weight_pct")

    ok_syn = True
    syn_failed: list[str] = []
    if enforce_synthetic_vs_mandate_dd and target_max_drawdown_pct is not None:
        ok_syn, syn_failed = synthetic_mandatory_loss_detail(stress_report)
        if not ok_syn:
            failures.append("synthetic_stress_loss")

    ok_fac = True
    slack["factor_rc_top1"] = None
    slack["factor_rc_top3"] = None
    mx1 = max_top1_rc_synthetic(stress_report)
    mx3 = max_top3_rc_sum_synthetic(stress_report)
    lim1 = calibration_limits.get("max_top1_rc_pct")
    lim3 = calibration_limits.get("max_top3_rc_sum_pct")
    if lim1 is not None and mx1 is not None:
        cap1 = float(lim1)
        ok_fac = ok_fac and mx1 <= cap1 + 1e-12
        slack["factor_rc_top1"] = float(cap1 - mx1)
        if mx1 > cap1:
            failures.append("max_top1_rc_pct")
    if lim3 is not None and mx3 is not None:
        cap3 = float(lim3)
        ok_fac = ok_fac and mx3 <= cap3 + 1e-12
        slack["factor_rc_top3"] = float(cap3 - mx3)
        if mx3 > cap3:
            failures.append("max_top3_rc_sum_pct")

    hard_pass = ok_dd and ok_vol and ok_cap and ok_syn and ok_fac

    borderline = False
    if hard_pass:
        if target_vol_annual is not None and vol_annual_10y is not None:
            tv = float(target_vol_annual)
            vol = float(vol_annual_10y)
            if tv > 0 and vol >= 0.92 * tv:
                borderline = True
        if target_max_drawdown_pct is not None and mandate_max_drawdown_realized is not None:
            lim = float(target_max_drawdown_pct)
            realized = float(mandate_max_drawdown_realized)
            margin = realized - lim
            if margin >= 0 and margin < 0.02:
                borderline = True

    klass: MandateClass = "fail"
    if hard_pass:
        klass = "borderline" if borderline else "pass"

    return {
        "mandate_classification": klass,
        "mandate_failures": failures,
        "synthetic_mandatory_failed": syn_failed,
        "checks": {
            "mandate_max_drawdown_full_history": ok_dd,
            "target_vol_annual": ok_vol,
            "max_single_security_weight_pct": ok_cap,
            "synthetic_mandatory_loss": ok_syn,
            "factor_rc_limits": ok_fac,
        },
        "slack": slack,
    }


def _mandate_failure_codes_from_row(row: dict[str, Any] | None) -> list[str]:
    if not row:
        return []
    mf = row.get("mandate_failures")
    if mf is None:
        return []
    if isinstance(mf, list):
        return [str(x).strip() for x in mf if str(x).strip()]
    if isinstance(mf, str):
        return [x.strip() for x in mf.split(";") if x.strip()]
    return []


def mandate_failure_labels_for_codes(codes: list[str]) -> list[str]:
    """Return stable English descriptions for mandate failure codes (benchmark calibration summaries)."""
    out: list[str] = []
    for c in codes:
        label = MANDATE_FAILURE_LABELS.get(c)
        out.append(label if label else str(c))
    return out


def build_no_feasible_lambda_diagnostic(
    *,
    lambda_grid: Sequence[float],
    winner: dict[str, Any] | None,
) -> dict[str, Any]:
    """
    Structured diagnostic when no λ in ``lambda_grid`` satisfies the mandate (pass / borderline).

    ``winner`` is the calibration fallback row when present (typically ``pick_least_bad_lambda``).
    """
    grid_list = [float(x) for x in lambda_grid]
    lam_min = min(grid_list) if grid_list else None
    lam_max = max(grid_list) if grid_list else None

    build_ok = winner is not None and winner.get("build_status") in ("OK", "APPROXIMATE")
    best_lambda = (
        float(winner["robust_mv_lambda"])
        if winner is not None and winner.get("robust_mv_lambda") is not None
        else None
    )

    codes = _mandate_failure_codes_from_row(winner) if build_ok else []
    labels = mandate_failure_labels_for_codes(codes)

    range_sentence = ""
    if lam_min is not None and lam_max is not None and grid_list:
        range_sentence = (
            f"Tested λ range: {lam_min:g}–{lam_max:g} ({len(grid_list)} values). "
        )

    if winner is None:
        fallback_sentence = "No candidate rows were produced for fallback ranking."
        fail_sentence = "Mandate constraint breaches could not be enumerated."
    elif not build_ok:
        bs = winner.get("build_status")
        fallback_sentence = (
            f"Fallback row λ={best_lambda if best_lambda is not None else 'n/a'} "
            f"has build_status={bs!r}; mandate diagnostics were not evaluated on this candidate."
        )
        fail_sentence = "See build logs and Robust MV diagnostics for solver/configuration failures."
    else:
        mc = winner.get("mandate_classification")
        fallback_sentence = (
            f"Among successful solves, the calibration ranks λ={best_lambda:g} as the fallback candidate "
            f"(mandate_classification={mc!r}). "
        )
        if labels:
            fail_sentence = "Limits still breached at that λ: " + "; ".join(labels) + "."
        elif codes:
            fail_sentence = "Limits still breached at that λ: " + "; ".join(codes) + "."
        else:
            fail_sentence = "Mandate failure codes were not recorded for this candidate."

    typical_sentence = (
        "Typical explanations include an overly narrow λ grid, limited defensive capacity in the universe, "
        "binding constraints that block derisking, and shrunk expected returns that still reward riskier sleeves."
    )
    next_sentence = (
        "Consider widening λ, reassessing the universe and constraints, and verifying volatility "
        "and drawdown limits are configured as intended (see suggested_next_actions)."
    )

    narrative = (
        "No λ in the tested grid satisfied the mandate classification (pass or borderline). "
        + range_sentence
        + fallback_sentence
        + " "
        + fail_sentence
        + " "
        + typical_sentence
        + " "
        + next_sentence
    )

    return {
        "lambda_range_tested": {"min": lam_min, "max": lam_max, "n_grid_points": len(grid_list)},
        "best_available_lambda": best_lambda,
        "best_candidate_build_status": winner.get("build_status") if winner else None,
        "best_candidate_mandate_classification": winner.get("mandate_classification") if winner else None,
        "mandate_constraints_failed_codes": codes,
        "mandate_constraints_failed": labels if labels else list(codes),
        "possible_causes": list(NO_FEASIBLE_LAMBDA_POSSIBLE_CAUSES),
        "suggested_next_actions": list(NO_FEASIBLE_LAMBDA_SUGGESTED_ACTIONS),
        "narrative": narrative.strip(),
    }


def pick_least_bad_lambda(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    """When no candidate passes, rank by fewest failures then mildest slack violations."""
    usable = [r for r in rows if r.get("build_status") in ("OK", "APPROXIMATE")]
    if not usable:
        return rows[-1] if rows else None

    def _n_failures(r: dict[str, Any]) -> int:
        mf = r.get("mandate_failures")
        if mf is None:
            return 0
        if isinstance(mf, list):
            return len(mf)
        if isinstance(mf, str):
            return len([x for x in mf.split(";") if x.strip()])
        return 0

    def rank_key(r: dict[str, Any]) -> tuple[int, float, float]:
        nfail = _n_failures(r)
        try:
            sv = float(r.get("slack_target_vol"))
            if sv != sv:
                sv = -1e12
        except (TypeError, ValueError):
            sv = -1e12
        # Prefer larger slack on vol cap (less violation): ascending on (-sv)
        vol_rank = -sv
        try:
            cagr = float(r.get("cagr_10y"))
            if cagr != cagr:
                cagr = -1e9
        except (TypeError, ValueError):
            cagr = -1e9
        return (nfail, vol_rank, cagr)

    usable.sort(key=rank_key)
    return usable[0]


def pick_best_feasible_lambda_row(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    """
    Lowest λ among mandate-eligible builds (pass / borderline), tie-break highest 10Y CAGR.
    """
    eligible = [
        r
        for r in rows
        if r.get("build_status") in ("OK", "APPROXIMATE")
        and r.get("mandate_classification") in ("pass", "borderline")
    ]
    if not eligible:
        return None
    eligible.sort(
        key=lambda r: (float(r.get("robust_mv_lambda", 1e9)), -float(r.get("cagr_10y") or -1e9))
    )
    return eligible[0]


def failure_codes_union_from_rows(rows: list[dict[str, Any]]) -> list[str]:
    """Sorted union of mandate_failure tokens across rows (build diagnostics string or list)."""
    codes: set[str] = set()
    for r in rows:
        mf = r.get("mandate_failures")
        if mf is None:
            continue
        if isinstance(mf, str):
            codes.update(x.strip() for x in mf.split(";") if x.strip())
        elif isinstance(mf, list):
            codes.update(str(x).strip() for x in mf if str(x).strip())
    return sorted(codes)


def select_robust_mv_calibration_winner(
    *,
    primary_rows: list[dict[str, Any]],
    extended_rows: list[dict[str, Any]],
    all_rows: list[dict[str, Any]],
    primary_grid: tuple[float, ...],
    extended_grid_evaluated: tuple[float, ...],
) -> dict[str, Any]:
    """
    Choose calibration outcome: prefer primary feasible λ, else extended, else least-bad fallback.

    Returns keys used by ``robust_mv_lambda_calibration_summary.json``.
    """
    win_pri = pick_best_feasible_lambda_row(primary_rows)
    win_ext = pick_best_feasible_lambda_row(extended_rows)
    feasible_primary = win_pri is not None
    feasible_extended = win_ext is not None

    pg_sorted = sorted(primary_grid) if primary_grid else []
    if len(pg_sorted) >= 2:
        pg_span = f"{pg_sorted[0]:g}–{pg_sorted[-1]:g}"
    elif len(pg_sorted) == 1:
        pg_span = f"{pg_sorted[0]:g}"
    else:
        pg_span = "none"

    failed_primary = failure_codes_union_from_rows(primary_rows)
    failed_extended = failure_codes_union_from_rows(extended_rows)

    if feasible_primary:
        winner = win_pri
        source = "primary_grid"
        feasible_found = True
        explanation = None
    elif feasible_extended:
        winner = win_ext
        source = "extended_grid"
        feasible_found = True
        lam_v = float(winner["robust_mv_lambda"])
        ext_hi = max(extended_grid_evaluated) if extended_grid_evaluated else lam_v
        explanation = (
            f"No feasible λ was found in the primary grid ({pg_span}). "
            f"The search was extended up to {ext_hi:g}, where λ = {lam_v:g} satisfied the mandate."
        )
    else:
        winner = pick_least_bad_lambda(all_rows)
        source = "least_bad"
        feasible_found = False
        ext_hi = max(extended_grid_evaluated) if extended_grid_evaluated else 10.0
        explanation = (
            f"No feasible λ was found in the primary grid ({pg_span}) or extended grid "
            f"(up to {ext_hi:g}); returning least-bad candidate."
        )

    return {
        "winner": winner,
        "feasible_lambda_found": feasible_found,
        "feasible_found_in_primary_grid": feasible_primary,
        "feasible_found_in_extended_grid": feasible_extended,
        "selected_lambda_source": source,
        "failed_constraints_by_grid": {
            "primary": failed_primary,
            "extended": failed_extended,
        },
        "extended_search_explanation": explanation,
    }


def infer_binding_constraints(evaluation: dict[str, Any]) -> list[str]:
    """Names of checks with smallest positive slack (tightest binding)."""
    slack = evaluation.get("slack") or {}
    bindings: list[tuple[str, float]] = []
    for name, key in (
        ("target_vol_annual", "target_vol"),
        ("mandate_max_drawdown_full_history", "mandate_max_dd_hist"),
        ("max_single_security_weight_pct", "max_single_asset_weight"),
        ("factor_rc_top1", "factor_rc_top1"),
        ("factor_rc_top3", "factor_rc_top3"),
    ):
        v = slack.get(key)
        if v is None:
            continue
        try:
            fv = float(v)
        except (TypeError, ValueError):
            continue
        bindings.append((name, fv))
    if not bindings:
        return []
    pos = [(n, s) for n, s in bindings if s >= 0]
    if not pos:
        return [n for n, _ in bindings]
    m = min(s for _, s in pos)
    return sorted({n for n, s in pos if abs(s - m) <= 1e-9})
