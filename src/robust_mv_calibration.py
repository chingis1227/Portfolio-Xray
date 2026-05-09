"""
Robust Mean–Variance λ calibration helpers.

Evaluates candidate portfolios against **config IPS fields** (targets / limits) and optional
``robust_mv_calibration`` YAML overrides. Does **not** alter ``run_stress`` internals or mandate
gate implementation in ``run_report.py`` — callers reuse ``portfolio_valid`` and scenario rows.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

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
