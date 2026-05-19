"""
Auto-generate commentary.txt and stress_commentary.txt next to portfolio outputs.

Called after each full metrics run so commentary stays aligned with summary, stress_report,
and exported CSVs (per .cursor/rules/portfolio-commentary.mdc).
"""
from __future__ import annotations

import json
import math
import os
from pathlib import Path
from typing import Any

import pandas as pd

from src.portfolio_xray import (
    build_portfolio_xray_v2,
    format_portfolio_xray_commentary,
    load_rc_vol_map_from_csv,
)
from src.stress_factors import BASE_BETA_ROW_ORDER, BETA_ROW_ORDER

# Missing-value tokens for exported commentary (English-only artifacts).
_NA = "n/a"
_MDASH = "\u2014"


def _folder_portfolio_label(output_dir_final: Path) -> str:
    name = output_dir_final.name.strip().lower()
    if name == "main portfolio":
        return "Main portfolio (policy)"
    if "equal" in name and "weight" in name:
        return "Equal-Weight baseline"
    if "risk" in name and "parity" in name:
        return "Risk-Parity baseline"
    return output_dir_final.name


def _fmt_pct(x: Any, digits: int = 2) -> str:
    if x is None:
        return _NA
    try:
        v = float(x)
    except (TypeError, ValueError):
        return _NA
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
        return _NA
    return f"{v * 100:.{digits}f}%"


def _fmt_float(x: Any, digits: int = 3) -> str:
    if x is None:
        return _NA
    try:
        v = float(x)
    except (TypeError, ValueError):
        return _NA
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
        return _NA
    return f"{v:.{digits}f}"


def _load_rc_top5(output_dir_csv: Path) -> list[tuple[str, float]]:
    """Top 5 assets by RC_vol from rc_vol_10y.csv (fallback 5y, 3y)."""
    for suffix in ("10y", "5y", "3y"):
        path = output_dir_csv / f"rc_vol_{suffix}.csv"
        if not path.is_file():
            continue
        try:
            df = pd.read_csv(path, index_col=0)
            if df.shape[1] < 1:
                continue
            col = df.columns[0]
            s = df[col].dropna()
            # drop non-ticker rows
            s = s[s.index.astype(str).str.len() > 0]
            s = s.sort_values(ascending=False)
            out: list[tuple[str, float]] = []
            for t, val in s.head(5).items():
                try:
                    out.append((str(t), float(val)))
                except (TypeError, ValueError):
                    continue
            if out:
                return out
        except Exception:
            continue
    return []


def _scenario_snippets(stress_report: dict[str, Any] | None) -> list[str]:
    if not stress_report:
        return []
    lines = []
    for row in stress_report.get("scenario_results") or []:
        sid = row.get("scenario_id", "?")
        pnl = row.get("portfolio_pnl_pct")
        ok = row.get("pass")
        if pnl is not None:
            lines.append(f"{sid}: PnL ~ {_fmt_pct(pnl, 2)}, pass={ok}")
    return lines[:6]


def _fmt_beta_dict(d: dict[str, Any] | None) -> str:
    if not d:
        return _NA
    parts = []
    for k in sorted(d.keys()):
        parts.append(f"{k}={_fmt_float(d.get(k), 4)}")
    return ", ".join(parts) if parts else _NA


def _fmt_factor_driver(driver: dict[str, Any] | None) -> str:
    if not isinstance(driver, dict):
        return "n/a"
    factor = driver.get("factor") or driver.get("beta_key") or "factor"
    beta = driver.get("beta_key")
    beta_suffix = f" ({beta})" if beta and beta != factor else ""
    return f"{factor}{beta_suffix}={_fmt_pct(driver.get('pnl_pct'), 2)}"


def _historical_driver_line(row: dict[str, Any]) -> str | None:
    drivers = row.get("top_factor_drivers")
    if not isinstance(drivers, list):
        attr = row.get("historical_factor_attribution") or {}
        drivers = attr.get("top_factor_drivers") if isinstance(attr, dict) else None
    if not isinstance(drivers, list) or not drivers:
        return None
    return ", ".join(_fmt_factor_driver(d) for d in drivers[:3] if isinstance(d, dict))


def _historical_vulnerability_summary(hist: list[dict[str, Any]]) -> str | None:
    totals: dict[str, float] = {}
    counts: dict[str, int] = {}
    for row in hist:
        largest = row.get("largest_negative_factor")
        if not isinstance(largest, dict):
            attr = row.get("historical_factor_attribution") or {}
            largest = attr.get("largest_negative_factor") if isinstance(attr, dict) else None
        if not isinstance(largest, dict):
            continue
        key = str(largest.get("factor") or largest.get("beta_key") or "factor")
        try:
            pnl = float(largest.get("pnl_pct"))
        except (TypeError, ValueError):
            continue
        totals[key] = totals.get(key, 0.0) + pnl
        counts[key] = counts.get(key, 0) + 1
    if not totals:
        return None
    top = sorted(totals, key=lambda k: (counts.get(k, 0), abs(totals[k])), reverse=True)[0]
    return (
        f"Structural historical factor vulnerability: most repeated largest negative driver is "
        f"{top} ({counts[top]} episodes, cumulative model contribution {_fmt_pct(totals[top], 2)})."
    )


def _ordered_beta_keys(
    *maps: Any,
    beta_order: tuple[str, ...] = BETA_ROW_ORDER,
    include_extra: bool = True,
) -> list[str]:
    ordered: list[str] = []
    seen: set[str] = set()
    for key in beta_order:
        if any(isinstance(m, dict) and key in m for m in maps):
            ordered.append(key)
            seen.add(key)
    if not include_extra:
        return ordered
    extra = sorted(
        {
            str(key)
            for m in maps
            if isinstance(m, dict)
            for key in m.keys()
            if str(key) not in seen
        }
    )
    ordered.extend(extra)
    return ordered


def _base_beta_map(values: Any) -> dict[str, Any]:
    if not isinstance(values, dict):
        return {}
    return {k: v for k, v in values.items() if str(k) in BASE_BETA_ROW_ORDER}


def _relpath_for_pdf_md_image(image_file: Path, output_dir_final: Path) -> str | None:
    """Relative POSIX path from pdf_md_sources/ to image; for Pandoc when building stress_commentary PDF."""
    try:
        project_root = output_dir_final.resolve().parent
        md_sources = project_root / "pdf_md_sources"
        if not md_sources.is_dir():
            return None
        rel = os.path.relpath(image_file.resolve(), md_sources.resolve())
        return Path(rel).as_posix()
    except Exception:
        return None


def _fmt_p_value(x: Any) -> str:
    if x is None:
        return _NA
    try:
        v = float(x)
    except (TypeError, ValueError):
        return _NA
    if v == 0.0 or (isinstance(v, float) and v < 1e-6):
        return "<1e-6"
    return _fmt_float(v, 6)


def _append_factor_multicollinearity_section(lines: list[str], mc: Any) -> None:
    """Append factor multicollinearity (same rows as OLS regressors); from factor_multicollinearity in stress_report."""
    if not isinstance(mc, dict) or not mc:
        return
    lines.append("Factor multicollinearity")
    err = mc.get("error")
    if err:
        lines.append(f"Factor multicollinearity diagnostics: not computed — {err}")
        lines.append("")
        return
    sev = mc.get("severity", _MDASH)
    mvif_str = "inf" if mc.get("max_vif_is_infinite") else _fmt_float(mc.get("max_vif"), 3)
    mvf = mc.get("max_vif_factor")
    fac_suffix = f" (factor {mvf})" if mvf else ""
    lines.append(
        f"Multicollinearity (same weekly sample as regression): severity={sev}; "
        f"cond(R)={mc.get('cond_correlation_matrix', _NA)}; "
        f"max VIF={mvif_str}{fac_suffix}."
    )
    sp = mc.get("strongest_pair")
    if isinstance(sp, dict) and sp.get("factor_i"):
        lines.append(
            f"Strongest pairwise correlation: {sp.get('factor_i')} vs {sp.get('factor_j')}, "
            f"rho={_fmt_float(sp.get('rho'), 4)}."
        )
    assess = mc.get("assessment_en") or mc.get("assessment_ru")
    if assess:
        lines.append(f"Assessment: {assess}")
    pairs = mc.get("pairwise_correlations") or []
    if isinstance(pairs, list) and pairs:
        lines.append("Pairwise correlations rho (sorted by |rho|):")
        for row in pairs:
            if not isinstance(row, dict):
                continue
            lines.append(
                f"  {row.get('factor_i')} — {row.get('factor_j')}: rho={_fmt_float(row.get('rho'), 4)}"
            )
    vif_bf = mc.get("vif_by_factor") or {}
    if isinstance(vif_bf, dict) and vif_bf:
        lines.append("VIF by factor:")
        for fname in sorted(vif_bf.keys()):
            v = vif_bf[fname]
            vs = "inf" if v is None else _fmt_float(v, 3)
            lines.append(f"  {fname}: {vs}")
    lines.append(f"Method: {mc.get('method', _MDASH)}; n_obs_factors={mc.get('n_obs_factors', _MDASH)}.")
    lines.append("")


def _append_serial_correlation_section(lines: list[str], ser: Any) -> None:
    """Durbin-Watson + Breusch-Godfrey on portfolio factor OLS residuals (same ordering as regression)."""
    if not isinstance(ser, dict) or not ser:
        return
    lines.append("Durbin-Watson / Breusch-Godfrey")
    if ser.get("error"):
        lines.append(f"Residual autocorrelation (DW / Breusch-Godfrey): not computed — {ser.get('error')}")
        lines.append("")
        return
    dw = ser.get("durbin_watson")
    lines.append(
        f"Factor OLS residual autocorrelation: Durbin-Watson={_fmt_float(dw, 4) if dw is not None else _NA} "
        f"(~2 suggests little first-order AR; method: {ser.get('method', _MDASH)})."
    )
    bg = ser.get("breusch_godfrey") or []
    if isinstance(bg, list) and bg:
        lines.append("Breusch-Godfrey LM (H0: no serial correlation up to order p; LM ~ chi-squared(p)):")
        for row in bg:
            if not isinstance(row, dict):
                continue
            pv = row.get("p_value")
            lines.append(
                f"  lags={row.get('lags', _MDASH)}: LM={_fmt_float(row.get('lm_statistic'), 4)}, "
                f"df={row.get('df_chi2', _MDASH)}, p={_fmt_p_value(pv)}, "
                f"T_aux={row.get('n_aux_observations', _MDASH)}, R2_aux={_fmt_float(row.get('aux_r_squared'), 4)}"
            )
    lines.append("")


def _append_heteroskedasticity_section(lines: list[str], het: Any) -> None:
    """Breusch-Pagan on portfolio factor OLS residuals (same rows as regression)."""
    if not isinstance(het, dict) or not het:
        return
    lines.append("Breusch-Pagan heteroskedasticity")
    if het.get("error"):
        lines.append(f"Breusch-Pagan residual heteroskedasticity test: not computed - {het.get('error')}")
        lines.append("")
        return
    bp = het.get("breusch_pagan") or {}
    if isinstance(bp, dict) and bp:
        lines.append(
            "Breusch-Pagan (H0: homoskedastic OLS residuals; LM ~ chi-square(k_factors)): "
            f"LM={_fmt_float(bp.get('lm_statistic'), 4)}, "
            f"df={bp.get('df_chi2', 'n/a')}, p={_fmt_p_value(bp.get('p_value'))}, "
            f"T_aux={bp.get('n_aux_observations', 'n/a')}, R2_aux={_fmt_float(bp.get('aux_r_squared'), 4)}."
        )
        lines.append(
            f"F-form: F={_fmt_float(bp.get('f_statistic'), 4)}, "
            f"df=({bp.get('f_df_num', 'n/a')}, {bp.get('f_df_den', 'n/a')}), "
            f"p={_fmt_p_value(bp.get('f_p_value'))}."
        )
    lines.append("")


def _append_factor_regression_section(lines: list[str], fr: Any, label: str) -> None:
    if not isinstance(fr, dict) or not fr:
        return
    lines.append(f"Portfolio factor regression ({label})")
    betas = fr.get("betas") or {}
    t_d = fr.get("t") or {}
    p_d = fr.get("p") or {}
    lo = fr.get("ci_low") or {}
    hi = fr.get("ci_high") or {}
    beta_order = _ordered_beta_keys(
        betas,
        t_d,
        p_d,
        lo,
        hi,
        beta_order=BASE_BETA_ROW_ORDER,
        include_extra=False,
    )
    lines.append(
        f"Weekly portfolio factor regression ({label}), OLS: "
        f"n_obs={fr.get('n_obs', _NA)}, R2={_fmt_float(fr.get('r2'), 4)}, "
        f"idiosyncratic risk (1-R2)={_fmt_float(fr.get('idiosyncratic_risk'), 4)}, "
        f"adj R2={_fmt_float(fr.get('adj_r2'), 4)}, intercept={_fmt_float(fr.get('intercept'), 4)}, "
        f"se_type={fr.get('se_type', _MDASH)}, alpha={fr.get('alpha', _MDASH)} (CI level {fr.get('ci_level', _MDASH)})."
    )
    lines.append("By factor (beta, t, p, 95% CI) — classic OLS (se_type=classic_ols):")
    for key in beta_order:
        if key not in betas and key not in t_d:
            continue
        lines.append(
            f"- {key}: beta={_fmt_float(betas.get(key), 4)}, t={_fmt_float(t_d.get(key), 3)}, "
            f"p={_fmt_p_value(p_d.get(key))}, CI=[{_fmt_float(lo.get(key), 4)}; {_fmt_float(hi.get(key), 4)}]"
        )
    hac = fr.get("hac_inference") or {}
    if isinstance(hac, dict) and hac:
        hac_se = hac.get("se")
        hac_t = hac.get("t")
        hac_p = hac.get("p")
        hac_lo = hac.get("ci_low")
        hac_hi = hac.get("ci_high")
        lines.append(
            f"HAC/Newey-West (robust) inference: se_type={hac.get('se_type', 'hac_newey_west')}, "
            f"kernel={hac.get('kernel', 'bartlett')}, max_lags={hac.get('max_lags', _MDASH)}."
        )
        if isinstance(hac_se, list) and isinstance(hac_t, list) and isinstance(hac_p, list):
            lines.append("By factor (HAC t, p, 95% CI):")
            for idx, key in enumerate(beta_order, start=1):
                pos = idx
                if pos >= len(hac_t):
                    continue
                t_v = hac_t[pos]
                p_v = hac_p[pos] if pos < len(hac_p) else None
                lo_v = hac_lo[pos] if isinstance(hac_lo, list) and pos < len(hac_lo) else None
                hi_v = hac_hi[pos] if isinstance(hac_hi, list) and pos < len(hac_hi) else None
                lines.append(
                    f"- {key}: t_HAC={_fmt_float(t_v, 3)}, p_HAC={_fmt_p_value(p_v)}, "
                    f"CI_HAC=[{_fmt_float(lo_v, 4)}; {_fmt_float(hi_v, 4)}]"
                )
    het = fr.get("heteroskedasticity_diagnostics")
    if het is not None:
        _append_heteroskedasticity_section(lines, het)
    ser = fr.get("serial_correlation_diagnostics")
    if ser is not None:
        _append_serial_correlation_section(lines, ser)
    mc = fr.get("factor_multicollinearity")
    if mc is not None:
        _append_factor_multicollinearity_section(lines, mc)
    else:
        lines.append("")


def _append_rolling_betas_section(lines: list[str], st: dict[str, Any], output_dir_final: Path) -> None:
    rw = st.get("factor_betas_rolling_windows_weeks")
    if isinstance(rw, dict) and rw:
        lines.append("Rolling windows")
        lines.append(f"Weekly rolling windows (weeks): {', '.join(f'{k}={v}' for k, v in sorted(rw.items()))}.")

    summ = st.get("factor_betas_rolling_summary")
    if isinstance(summ, dict) and summ:
        lines.append(
            "Rolling beta summary over available history in this run (mean, median, p10, p90):"
        )
        for win in sorted(summ.keys(), key=lambda x: (len(str(x)), str(x))):
            by_b = summ.get(win) or {}
            if not isinstance(by_b, dict):
                continue
            lines.append(f"Window {win}:")
            for bkey in _ordered_beta_keys(by_b, beta_order=BASE_BETA_ROW_ORDER, include_extra=False):
                row = by_b.get(bkey)
                if not isinstance(row, dict):
                    continue
                lines.append(
                    f"  {bkey}: n={row.get('n_points', _MDASH)}, mean={_fmt_float(row.get('mean'), 4)}, "
                    f"median={_fmt_float(row.get('median'), 4)}, p10={_fmt_float(row.get('p10'), 4)}, "
                    f"p90={_fmt_float(row.get('p90'), 4)}"
                )
            lines.append("")
    elif st.get("factor_betas_rolling_error"):
        lines.append(f"Rolling betas: computation error — {st.get('factor_betas_rolling_error')}")

    art = st.get("factor_betas_rolling_artifacts")
    if isinstance(art, dict):
        png_map = art.get("plot_png_by_window") or {}
        if png_map:
            lines.append(
                "Rolling beta chart files (PNG, variant output folder): "
                + ", ".join(f"{k}->{v}" for k, v in sorted(png_map.items()))
            )

    labels = ("3y", "5y", "10y")
    for lbl in labels:
        png = output_dir_final / f"rolling_factor_betas_{lbl}.png"
        if not png.is_file():
            continue
        rel = _relpath_for_pdf_md_image(png, output_dir_final)
        if rel:
            lines.append(f"![Rolling factor betas — {lbl}]({rel})")
    lines.append("")


def _append_factor_beta_stability_section(lines: list[str], st: dict[str, Any]) -> None:
    stability = st.get("factor_betas_stability")
    if not isinstance(stability, dict) or not stability:
        return

    lines.append("Factor beta stability diagnostics")
    lines.append(
        "Sign stability, magnitude stability, specification sensitivity, and OOS rolling-forward stability."
    )

    dist = stability.get("severity_distribution") or {}
    shares = dist.get("shares") if isinstance(dist, dict) else {}
    if isinstance(shares, dict):
        lines.append(
            "Severity distribution: "
            f"low={_fmt_pct(shares.get('low'), 1)}, "
            f"moderate={_fmt_pct(shares.get('moderate'), 1)}, "
            f"high={_fmt_pct(shares.get('high'), 1)}, "
            f"unknown={_fmt_pct(shares.get('unknown'), 1)}."
        )
    warning = stability.get("severity_distribution_warning")
    if warning:
        lines.append(f"Severity distribution warning: {warning}.")

    by_beta = stability.get("by_beta") or {}
    if not isinstance(by_beta, dict):
        lines.append("")
        return
    for beta_key in _ordered_beta_keys(by_beta, beta_order=BASE_BETA_ROW_ORDER, include_extra=False):
        row = by_beta.get(beta_key)
        if not isinstance(row, dict):
            continue
        sign = row.get("sign_stability") or {}
        mag = row.get("magnitude_stability") or {}
        spec = row.get("specification_sensitivity") or {}
        oos = row.get("oos_stability") or {}
        lines.append(
            f"- {beta_key}: severity={row.get('combined_severity', 'unknown')}; "
            f"sign={sign.get('severity', 'unknown')} "
            f"(dominant={sign.get('dominant_sign', 'unknown')}, share={_fmt_float(sign.get('dominant_sign_share'), 3)}, "
            f"changes={sign.get('sign_change_count', '—')}); "
            f"magnitude={mag.get('severity', 'unknown')} "
            f"(band={_fmt_float(mag.get('p90_minus_p10'), 4)}, rel_band={_fmt_float(mag.get('relative_band'), 3)}); "
            f"spec={spec.get('severity', 'unknown')} "
            f"(rel_median_span={_fmt_float(spec.get('relative_median_span'), 3)}, sign_disagreement={spec.get('sign_disagreement', False)}); "
            f"OOS={oos.get('severity', 'unknown') if isinstance(oos, dict) else 'unknown'} "
            f"(sign_match={_fmt_float(oos.get('sign_match_share') if isinstance(oos, dict) else None, 3)}, "
            f"degradation={_fmt_float(oos.get('relative_magnitude_degradation') if isinstance(oos, dict) else None, 3)}, "
            f"n={oos.get('n_tests', '—') if isinstance(oos, dict) else '—'})."
        )
    lines.append("")


def _append_kalman_factor_betas_section(lines: list[str], st: dict[str, Any]) -> None:
    kalman = st.get("factor_betas_kalman")
    if not isinstance(kalman, dict) or not kalman:
        if st.get("factor_betas_kalman_error"):
            lines.append(f"Kalman factor betas: calculation error - {st.get('factor_betas_kalman_error')}")
            lines.append("")
        return

    if kalman.get("status") != "available":
        warning_codes = ((kalman.get("diagnostics") or {}).get("warning_codes") or [])
        lines.append("Kalman factor betas: unavailable" + (f" ({', '.join(str(x) for x in warning_codes)})." if warning_codes else "."))
        lines.append("")
        return

    latest = _base_beta_map(kalman.get("latest") or {})
    latest_raw = _base_beta_map(kalman.get("latest_raw") or {})
    cap_diag = kalman.get("cap_diagnostics") or {}
    uncertainty = kalman.get("uncertainty_by_beta") or {}
    divergence = kalman.get("divergence_vs_5y") or {}

    lines.append("Kalman factor betas")
    lines.append(
        "Diagnostic-only current-regime Kalman beta estimate "
        f"(date={kalman.get('latest_date', 'n/a')}, n={kalman.get('n_observations', 'n/a')}, "
        f"cap=+/-{_fmt_float(kalman.get('beta_cap_abs'), 1)})."
    )
    if isinstance(latest, dict) and latest:
        lines.append("Latest capped betas: " + _fmt_beta_dict(latest) + ".")

    capped = [
        f"{beta_key}: raw={_fmt_float((cap_diag.get(beta_key) or {}).get('raw_value'), 4)} -> capped={_fmt_float((cap_diag.get(beta_key) or {}).get('capped_value'), 4)}"
        for beta_key in _ordered_beta_keys(latest_raw, beta_order=BASE_BETA_ROW_ORDER, include_extra=False)
        if isinstance(cap_diag.get(beta_key), dict) and (cap_diag.get(beta_key) or {}).get("was_capped")
    ]
    if capped:
        lines.append("Capped Kalman betas: " + "; ".join(capped) + ".")

    divergent = divergence.get("divergent_betas") if isinstance(divergence, dict) else []
    by_div = divergence.get("by_beta") if isinstance(divergence, dict) else {}
    if divergent and isinstance(by_div, dict):
        parts = []
        for beta_key in _ordered_beta_keys(
            {k: 1 for k in divergent},
            beta_order=BASE_BETA_ROW_ORDER,
            include_extra=False,
        ):
            row = by_div.get(beta_key) or {}
            parts.append(
                f"{beta_key}: kalman={_fmt_float(row.get('kalman'), 4)}, "
                f"5Y={_fmt_float(row.get('benchmark'), 4)}, reason={row.get('reason', 'n/a')}"
            )
        lines.append("Kalman vs 5Y divergence flags: " + "; ".join(parts) + ".")

    high_uncertainty = [
        str(beta_key)
        for beta_key in (kalman.get("high_uncertainty_betas") or [])
        if str(beta_key) in BASE_BETA_ROW_ORDER
    ]
    if high_uncertainty:
        lines.append("High state uncertainty betas: " + ", ".join(str(x) for x in high_uncertainty) + ".")
    elif isinstance(uncertainty, dict) and uncertainty:
        dist = kalman.get("uncertainty_severity_distribution") or {}
        shares = dist.get("shares") if isinstance(dist, dict) else {}
        if isinstance(shares, dict):
            lines.append(
                "Kalman uncertainty distribution: "
                f"low={_fmt_pct(shares.get('low'), 1)}, "
                f"moderate={_fmt_pct(shares.get('moderate'), 1)}, "
                f"high={_fmt_pct(shares.get('high'), 1)}."
            )
    lines.append("Kalman beta diagnostics are non-binding and do not change optimizer weights, mandate gates, or raw 5Y/10Y beta outputs.")
    lines.append("")


def _append_diagnostic_oil_beta_section(lines: list[str], st: dict[str, Any]) -> None:
    oil = st.get("diagnostic_oil_beta")
    if not isinstance(oil, dict) or not oil:
        if st.get("diagnostic_oil_beta_error"):
            lines.append(f"Oil diagnostic warning: calculation error - {st.get('diagnostic_oil_beta_error')}")
            lines.append("")
        return
    lines.append("Oil diagnostic/stress warning")
    lines.append(
        "Oil role=diagnostic_warning_only; beta_oil is deprecated in production beta outputs. "
        "Read Oil exposure only from diagnostic_oil_beta or stress-layer metrics."
    )
    lines.append(
        "Oil beta estimates: "
        f"5Y={_fmt_float(oil.get('beta_oil_5y'), 4)}, "
        f"10Y={_fmt_float(oil.get('beta_oil_10y'), 4)}; "
        f"Commodity production beta 5Y={_fmt_float(oil.get('beta_commodity_5y'), 4)}, "
        f"10Y={_fmt_float(oil.get('beta_commodity_10y'), 4)}."
    )
    corr = oil.get("oil_commodity_correlation") or {}
    vif = oil.get("oil_commodity_vif") or {}
    signal = oil.get("collinearity_signal") or {}
    lines.append(
        "Oil/Commodity collinearity: "
        f"corr_5y={_fmt_float(corr.get('factor_regression_5y'), 4)}, "
        f"corr_10y={_fmt_float(corr.get('factor_regression_10y'), 4)}, "
        f"cov_corr={_fmt_float(corr.get('factor_covariance_base'), 4)}, "
        f"oil_vif_5y={_fmt_float(vif.get('oil_5y'), 3)}, "
        f"severity={signal.get('severity', 'unknown')}."
    )
    kalman = oil.get("kalman_oil") or {}
    if isinstance(kalman, dict) and kalman:
        lines.append(
            "Oil Kalman diagnostic: "
            f"latest={_fmt_float(kalman.get('latest'), 4)}, "
            f"raw={_fmt_float(kalman.get('latest_raw'), 4)}, "
            f"uncertainty={kalman.get('uncertainty_class') or kalman.get('state_uncertainty') or 'n/a'}, "
            f"date={kalman.get('latest_date', 'n/a')}."
        )
    lines.append("")


def _append_factor_beta_adjusted_overlay_section(lines: list[str], st: dict[str, Any]) -> None:
    adjusted = st.get("factor_betas_adjusted")
    if not isinstance(adjusted, dict) or not adjusted:
        return
    lines.append("Stability-adjusted factor beta overlay")
    divergence = adjusted.get("beta_5y_vs_10y_divergence") or {}
    raw_map = adjusted.get("raw") or {}
    adj_map = adjusted.get("adjusted") or {}
    severity_map = adjusted.get("severity_by_beta") or {}
    reasons = adjusted.get("adjustment_reason_by_beta") or {}
    if divergence.get("strong_divergence_any"):
        lines.append(
            "Strong 5Y vs 10Y divergence: "
            + ", ".join(str(x) for x in (divergence.get("strong_divergence_betas") or []))
            + "."
        )
    reduced = []
    for beta_key in _ordered_beta_keys(raw_map, adj_map, beta_order=BASE_BETA_ROW_ORDER, include_extra=False):
        raw_val = raw_map.get(beta_key)
        adj_val = adj_map.get(beta_key)
        try:
            if raw_val is None or adj_val is None:
                continue
            if abs(float(adj_val) - float(raw_val)) > 1e-10:
                reduced.append(
                    f"{beta_key}: raw={_fmt_float(raw_val, 4)} -> adjusted={_fmt_float(adj_val, 4)} "
                    f"(severity={severity_map.get(beta_key, 'unknown')}, reason={reasons.get(beta_key, 'n/a')})"
                )
        except (TypeError, ValueError):
            continue
    if reduced:
        lines.append("Adjusted betas:")
        for row in reduced:
            lines.append(f"  {row}")
    signal = st.get("raw_vs_adjusted_pnl_signal") or {}
    if isinstance(signal, dict) and signal:
        synthetic_material = [row for row in (signal.get("synthetic") or []) if isinstance(row, dict) and row.get("material_difference")]
        historical_material = [row for row in (signal.get("historical") or []) if isinstance(row, dict) and row.get("material_difference")]
        if synthetic_material:
            lines.append("Material raw vs adjusted synthetic PnL differences:")
            for row in synthetic_material:
                lines.append(
                    f"  {row.get('scenario_id')}: raw={_fmt_pct(row.get('pnl_raw'))}, adjusted={_fmt_pct(row.get('pnl_adjusted'))}, "
                    f"delta={_fmt_pct(row.get('pnl_delta'))}, rel_delta={_fmt_pct(row.get('pnl_relative_delta'))}."
                )
        if historical_material:
            lines.append("Material raw vs adjusted historical model PnL differences:")
            for row in historical_material:
                lines.append(
                    f"  {row.get('episode')}: raw={_fmt_pct(row.get('pnl_raw'))}, adjusted={_fmt_pct(row.get('pnl_adjusted'))}, "
                    f"delta={_fmt_pct(row.get('pnl_delta'))}, rel_delta={_fmt_pct(row.get('pnl_relative_delta'))}."
                )
    lines.append("")


def _top_pair_text(rows: Any, *, corr_key: str = "abs_corr_delta") -> str:
    if not isinstance(rows, list) or not rows:
        return "n/a"
    row = next((r for r in rows if isinstance(r, dict)), None)
    if not row:
        return "n/a"
    return (
        f"{row.get('factor_i')} vs {row.get('factor_j')} "
        f"(corr_delta={_fmt_float(row.get('corr_delta'), 4)}, "
        f"abs_corr_delta={_fmt_float(row.get(corr_key), 4)})"
    )


def _append_factor_covariance_section(lines: list[str], st: dict[str, Any]) -> None:
    fc = st.get("factor_covariance")
    if not isinstance(fc, dict) or not fc:
        return
    lines.append("Factor covariance matrix")
    if fc.get("error"):
        lines.append(f"Factor covariance analytics unavailable: {fc.get('error')}")
        lines.append("")
        return

    risk = fc.get("portfolio_factor_risk") or {}
    for regime in ("base", "stress_empirical", "stress_overlay"):
        row = risk.get(regime) if isinstance(risk, dict) else None
        if not isinstance(row, dict):
            continue
        lines.append(
            f"- {regime} ({row.get('classification', 'unknown')}): "
            f"factor_vol={_fmt_pct(row.get('portfolio_factor_vol'), 2)}, "
            f"factor_variance={_fmt_float(row.get('portfolio_factor_variance'), 6)}."
        )

    comparison = fc.get("comparison") or {}
    empirical = comparison.get("empirical_change") if isinstance(comparison, dict) else None
    overlay = comparison.get("overlay_amplification") if isinstance(comparison, dict) else None
    lines.append(f"Empirical change (stress_empirical vs base): {_top_pair_text(empirical)}.")
    lines.append(f"Overlay amplification (stress_overlay vs stress_empirical): {_top_pair_text(overlay)}.")

    rc_flag = fc.get("RC_stability_flag") or {}
    if isinstance(rc_flag, dict):
        flagged = [
            str(r.get("factor"))
            for r in (rc_flag.get("by_factor") or [])
            if isinstance(r, dict) and r.get("RC_stability_flag")
        ]
        lines.append(
            f"RC_stability_flag threshold={_fmt_float(rc_flag.get('threshold_pct'), 1)}%; "
            f"overall={rc_flag.get('overall_flag', False)}; factors={', '.join(flagged) if flagged else 'none'}."
        )

    sensitivity = fc.get("beta_sensitivity") or {}
    if isinstance(sensitivity, dict) and sensitivity:
        parts = []
        for regime in ("base", "stress_empirical", "stress_overlay"):
            row = sensitivity.get(regime)
            if not isinstance(row, dict):
                continue
            parts.append(
                f"{regime} ({row.get('classification', 'unknown')}) vol_range="
                f"{_fmt_pct(row.get('vol_min'), 2)}..{_fmt_pct(row.get('vol_max'), 2)}"
            )
        if parts:
            lines.append("Beta sensitivity (+/-1 rolling beta std): " + "; ".join(parts) + ".")

    stability = fc.get("covariance_stability_check") or {}
    if isinstance(stability, dict) and stability:
        lines.append(
            f"Covariance stability check 5Y vs 2Y (data_driven): threshold={_fmt_float(stability.get('threshold_pct'), 1)}%; "
            f"overall_flag={stability.get('overall_flag', False)}."
        )

    forecast_quality = fc.get("forecast_quality") or {}
    if isinstance(forecast_quality, dict) and forecast_quality:
        if forecast_quality.get("status") == "available":
            summary = forecast_quality.get("summary") or {}
            lines.append(
                "Forecast quality (5Y covariance vs next 1Y realized factor risk): "
                f"n={summary.get('n_forecasts', 0)}, "
                f"median_abs_vol_error={_fmt_pct(summary.get('median_abs_vol_error_pct'), 1)}, "
                f"hit10={_fmt_pct(summary.get('hit_rate_abs_vol_error_le_10pct'), 1)}, "
                f"hit20={_fmt_pct(summary.get('hit_rate_abs_vol_error_le_20pct'), 1)}, "
                f"hit30={_fmt_pct(summary.get('hit_rate_abs_vol_error_le_30pct'), 1)}, "
                f"median_corr_rmse={_fmt_float(summary.get('median_corr_rmse'), 4)}, "
                f"severity={summary.get('overall_severity', 'unknown')}."
            )
        else:
            lines.append(
                "Forecast quality unavailable: "
                f"reason={forecast_quality.get('reason', 'unknown')}; "
                f"train_weeks={forecast_quality.get('train_weeks')}; "
                f"holdout_weeks={forecast_quality.get('holdout_weeks')}."
            )
    zero_filled = ((fc.get("exposure_vector") or {}).get("zero_filled_beta_keys") or []) if isinstance(fc.get("exposure_vector"), dict) else []
    zero_filled = [x for x in zero_filled if str(x) != "beta_oil"]
    if zero_filled:
        lines.append(f"Zero-filled missing factor betas: {', '.join(str(x) for x in zero_filled)}.")
    lines.append("")


def _append_macro_regime_section(lines: list[str], st: dict[str, Any]) -> None:
    mr = st.get("macro_regime_diagnostics")
    if not isinstance(mr, dict) or not mr:
        return
    lines.append("Macro regime diagnostics")
    axis_model = mr.get("axis_model") or {}
    version = axis_model.get("version") or "macro_two_axis_v1"
    if mr.get("error"):
        lines.append(
            f"Macro regime diagnostics unavailable ({version}): {mr.get('error')}"
        )
        coverage_tier = mr.get("coverage_tier") or "insufficient"
        lines.append(f"Coverage tier: {coverage_tier}.")
        disclaimer = mr.get("method_disclaimer")
        if disclaimer:
            lines.append(str(disclaimer))
        lines.append("")
        return

    scores = mr.get("axis_scores_latest") or {}
    lines.append(
        f"Method={version}; frequency={axis_model.get('frequency', 'monthly')}; "
        f"score_lag_months={mr.get('score_lag_months', 1)}."
    )
    primary_regime = (
        mr.get("current_primary_regime")
        or mr.get("current_regime")
        or "n/a"
    )
    legacy_regime = mr.get("current_regime_legacy")
    transition_flag_now = bool(mr.get("current_transition_flag"))
    transition_reason_now = mr.get("current_transition_reason") or "none"
    legacy_suffix = (
        f"; legacy_label={legacy_regime}" if legacy_regime else ""
    )
    lines.append(
        f"Current primary regime: {primary_regime}; "
        f"growth_score={_fmt_float(scores.get('growth_score'), 3)}; "
        f"inflation_score={_fmt_float(scores.get('inflation_score'), 3)}; "
        f"confidence={mr.get('confidence_level', mr.get('regime_confidence', 'unknown'))}; "
        f"transition_flag={transition_flag_now}; "
        f"transition_reason={transition_reason_now}"
        f"{legacy_suffix}."
    )
    growth_blocks = scores.get("growth_blocks") or {}
    inflation_blocks = scores.get("inflation_blocks") or {}
    if isinstance(growth_blocks, dict) and growth_blocks:
        parts = ", ".join(
            f"{k}={_fmt_float(v, 3)}" for k, v in growth_blocks.items() if v is not None
        )
        if parts:
            lines.append(f"Growth block sub-scores: {parts}.")
    if isinstance(inflation_blocks, dict) and inflation_blocks:
        parts = ", ".join(
            f"{k}={_fmt_float(v, 3)}" for k, v in inflation_blocks.items() if v is not None
        )
        if parts:
            lines.append(f"Inflation block sub-scores: {parts}.")

    coverage_tier = mr.get("coverage_tier") or "unknown"
    coverage_ratio = mr.get("coverage_ratio")
    available_blocks = mr.get("available_blocks") or []
    missing_blocks = mr.get("missing_blocks") or []
    optional_missing = mr.get("optional_blocks_missing") or []
    lines.append(
        f"Coverage tier: {coverage_tier}; ratio={_fmt_float(coverage_ratio, 2)}; "
        f"available_blocks={len(available_blocks)}; missing_blocks={len(missing_blocks)}; "
        f"optional_blocks_missing={len(optional_missing)}."
    )
    if missing_blocks:
        lines.append("Missing blocks: " + ", ".join(str(b) for b in missing_blocks) + ".")
    if optional_missing:
        lines.append(
            "Optional blocks missing (do not lower confidence): "
            + ", ".join(str(b) for b in optional_missing) + "."
        )

    by_quality = mr.get("available_regimes_by_quality") or {}
    usable = int(by_quality.get("usable", 0) or 0)
    reliable = int(by_quality.get("reliable", 0) or 0)
    lines.append(
        f"Available usable/reliable regimes: usable={usable}, reliable={reliable}, "
        f"total={mr.get('available_regimes_count', 0)}."
    )
    sources = mr.get("data_sources_used") or {}
    if isinstance(sources, dict):
        eci_source = sources.get("eci")
        if eci_source and eci_source != "unavailable":
            lines.append(
                "ECI is quarterly; values are forward-filled to monthly — treat the "
                "monthly precision as illustrative."
            )
        gdpnow_source = sources.get("gdpnow")
        if gdpnow_source and gdpnow_source != "unavailable":
            lines.append(
                "GDPNow (Atlanta Fed) is published quarterly via FRED:GDPNOW; "
                "values are forward-filled to monthly — treat intra-quarter "
                "monthly steps as illustrative, not a new release."
            )
    stability = mr.get("stability_summary") or {}
    top_unstable = stability.get("top_unstable_betas") or []
    if isinstance(top_unstable, list) and top_unstable:
        parts = []
        for row in top_unstable[:5]:
            if isinstance(row, dict):
                parts.append(
                    f"{row.get('beta_key')}:{row.get('policy_signal')} "
                    f"gap={_fmt_float(row.get('max_abs_regime_beta_gap'), 3)}"
                )
        if parts:
            lines.append("Top unstable regime betas: " + "; ".join(parts) + ".")
    counts = stability.get("policy_signal_counts") or {}
    if isinstance(counts, dict):
        lines.append(
            "Policy signal counts: "
            + ", ".join(f"{k}={v}" for k, v in counts.items())
            + "."
        )
    warning = stability.get("warning")
    if warning:
        lines.append(str(warning))
    look_ahead = axis_model.get("look_ahead_caveat")
    if look_ahead:
        lines.append(str(look_ahead))
    disclaimer = mr.get("method_disclaimer")
    if disclaimer:
        lines.append(str(disclaimer))
    quality = mr.get("regime_label_quality_check") or {}
    if isinstance(quality, dict) and quality:
        lines.append("Regime Label Quality Check")
        if quality.get("status") != "available":
            lines.append(
                "Regime label quality diagnostics are unavailable; treat regime-specific analytics cautiously."
            )
        else:
            overall = quality.get("overall_assessment") or {}
            by_regime = quality.get("by_regime") or {}
            stable = quality.get("stability_summary") or {}
            primary_only = {
                "goldilocks",
                "reflation",
                "stagflation",
                "recession_disinflation",
            }
            reliable = [
                r for r, row in by_regime.items()
                if isinstance(row, dict)
                and r in primary_only
                and row.get("quality_status") == "reliable"
            ]
            weak = [
                r for r, row in by_regime.items()
                if isinstance(row, dict)
                and r in primary_only
                and int(row.get("n_obs") or 0) < 24
            ]
            lines.append(
                f"Regime history usable={overall.get('history_usable', False)}; "
                f"switches={stable.get('n_switches', 'n/a')}; "
                f"avg_months_between_switches={_fmt_float(stable.get('avg_months_between_switches'), 2)}; "
                f"one-month share={_fmt_pct(stable.get('share_one_month_regimes'), 1)}; "
                f"<3m share={_fmt_pct(stable.get('share_regimes_lt_3m'), 1)}."
            )
            lines.append(
                "Reliable regimes: "
                + (", ".join(reliable) if reliable else "none")
                + "; weak regimes (<24 obs): "
                + (", ".join(weak) if weak else "none")
                + "."
            )
            if weak:
                lines.append(
                    "Warning: at least one regime has fewer than 24 observations; treat regime-specific betas/covariance/RC cautiously."
                )
            if overall.get("classifier_noise_warning"):
                lines.append(
                    "Warning: regime labels are unstable; the regime classifier may be too noisy for strong regime-specific conclusions."
                )
            warnings = overall.get("warnings") or []
            if warnings:
                lines.append("Quality-check warnings: " + "; ".join(str(w) for w in warnings) + ".")
            ts = quality.get("transition_summary") or mr.get("transition_summary") or {}
            if isinstance(ts, dict) and ts.get("n_scored_months"):
                reason_counts = ts.get("transition_reason_counts") or {}
                share = ts.get("transition_share")
                legacy_share = ts.get("legacy_neutral_transition_share")
                lines.append(
                    "Transition months: "
                    f"n={ts.get('n_transition_months', 0)} ("
                    f"{_fmt_pct(share, 1)}); "
                    f"growth_axis={reason_counts.get('growth_axis_near_neutral', 0)}, "
                    f"inflation_axis={reason_counts.get('inflation_axis_near_neutral', 0)}, "
                    f"both_axes={reason_counts.get('both_axes_near_neutral', 0)}"
                    + (
                        f"; legacy neutral_transition share={_fmt_pct(legacy_share, 1)}"
                        if legacy_share is not None
                        else ""
                    )
                    + "."
                )
                pivot = ts.get("primary_vs_transition_pivot") or {}
                if isinstance(pivot, dict) and pivot:
                    parts = [
                        f"{r}: non_transition={info.get('non_transition', 0)}, "
                        f"transition={info.get('transition', 0)}"
                        for r, info in pivot.items()
                        if isinstance(info, dict)
                    ]
                    if parts:
                        lines.append("Primary regime x transition pivot: " + "; ".join(parts) + ".")
    lines.append("")


def _append_regime_factor_analytics_window_section(
    lines: list[str], st: dict[str, Any]
) -> None:
    """Disclose label-history span vs fixed 10Y portfolio regime analytics window."""

    rfa = st.get("regime_factor_analytics")
    if not isinstance(rfa, dict) or not rfa:
        return
    lines.append("Regime factor analytics (portfolio window vs label history)")
    span = rfa.get("regime_label_history_span") or {}
    win = rfa.get("portfolio_regime_analytics_window") or {}
    note = rfa.get("portfolio_regime_analytics_note")
    disc = win.get("disclaimer") if isinstance(win, dict) else None
    if not isinstance(span, dict):
        span = {}
    if not isinstance(win, dict):
        win = {}
    lines.append(
        "macro_two_axis_v1 regime labels in macro_regime_diagnostics may cover a longer "
        f"history ({span.get('start', 'n/a')}–{span.get('end', 'n/a')}, "
        f"{span.get('n_months', 'n/a')} scored months in labels_monthly) than the "
        "portfolio-facing regime analytics slice."
    )
    lines.append(
        f"portfolio_regime_analytics_window is {win.get('label', '10Y')} ending at "
        f"{win.get('analysis_end', 'n/a')} (target ~{win.get('target_weeks', 'n/a')} weeks / "
        f"{win.get('target_months', 'n/a')} months); actual overlap in this run: "
        f"{win.get('actual_data_start', 'n/a')}–{win.get('actual_data_end', 'n/a')} "
        f"({win.get('actual_n_periods', 'n/a')} {win.get('frequency', '')} periods). "
        "Per-regime n_obs and all regime-specific covariances, correlations, betas, "
        "portfolio exposures, variance contributions, and average factor moves refer "
        "only to that overlap."
    )
    if note:
        lines.append(str(note))
    elif disc:
        lines.append(str(disc))
    lines.append("")


def _top_factor_rows_text(rows: Any, field: str, *, limit: int = 3) -> str:
    if not isinstance(rows, list) or not rows:
        return "none"
    parts = []
    for row in rows[:limit]:
        if not isinstance(row, dict):
            continue
        parts.append(f"{row.get('factor')}={_fmt_pct(row.get(field), 2)}")
    return "; ".join(parts) if parts else "none"


def _append_factor_variance_decomposition_section(lines: list[str], st: dict[str, Any]) -> None:
    decomp = st.get("factor_variance_decomposition")
    if not isinstance(decomp, dict) or not decomp:
        return
    lines.append("Factor variance decomposition")
    if decomp.get("status") != "available":
        lines.append(
            f"Factor variance decomposition unavailable: reason={decomp.get('reason', 'unknown')}; "
            f"variance_scale={decomp.get('variance_scale', 'weekly')}."
        )
        cross = decomp.get("cross_check") or {}
        if isinstance(cross, dict):
            lines.append(f"Cross-check status={cross.get('status', 'unavailable')}; reason={cross.get('reason') or 'n/a'}.")
        lines.append("")
        return

    lines.append(
        f"Method={decomp.get('method')}; variance_scale={decomp.get('variance_scale')}; "
        f"R2={_fmt_float(decomp.get('r2'), 4)}; residual={_fmt_pct(decomp.get('residual_share'), 2)} "
        f"({decomp.get('residual_severity', 'unknown')})."
    )
    cross = decomp.get("cross_check") or {}
    if isinstance(cross, dict):
        lines.append(
            f"R2 cross-check: status={cross.get('status', 'unknown')}; "
            f"bSigma_b/Var(portfolio)={_fmt_float(cross.get('variance_based_explained_share'), 4)}; "
            f"abs_diff={_fmt_float(cross.get('absolute_difference'), 4)}; "
            f"warning={cross.get('warning_code') or 'none'}."
        )
    warnings = decomp.get("warnings") or []
    if warnings:
        lines.append("Local warnings: " + ", ".join(str(w) for w in warnings) + ".")
    lines.append("Risk adders: " + _top_factor_rows_text(decomp.get("risk_adders"), "net_total_variance_share") + ".")
    lines.append("Hedgers: " + _top_factor_rows_text(decomp.get("hedgers"), "net_total_variance_share") + ".")
    lines.append("Neutral factors: " + _top_factor_rows_text(decomp.get("neutral_factors"), "net_total_variance_share") + ".")
    lines.append("Gross concentration: " + _top_factor_rows_text(decomp.get("gross_top_contributors_abs"), "gross_total_variance_share") + ".")
    stability = decomp.get("stability") or {}
    if isinstance(stability, dict):
        r2_stab = stability.get("r2") or {}
        lines.append(
            f"Decomposition stability: status={stability.get('status', 'unknown')}; "
            f"overall={stability.get('overall_severity', 'unknown')}; "
            f"R2 p10={_fmt_float(r2_stab.get('p10'), 4)}, p90={_fmt_float(r2_stab.get('p90'), 4)}, "
            f"severity={r2_stab.get('severity', 'unknown')}."
        )
    recommendation = decomp.get("residual_recommendation")
    if recommendation:
        lines.append(f"Residual recommendation: {recommendation}")
    lines.append("")


def _pca_block_summary(block: Any) -> str:
    if not isinstance(block, dict) or block.get("status") != "available":
        if isinstance(block, dict):
            return f"unavailable ({block.get('reason', 'unknown')})"
        return "unavailable"
    rolling = block.get("rolling_pc1") or {}
    summary = rolling.get("summary") if isinstance(rolling, dict) else {}
    stability = summary.get("stability_severity", "unknown") if isinstance(summary, dict) else "unknown"
    return (
        f"PC1={_fmt_pct(block.get('pc1_explained_variance_ratio'), 2)}, "
        f"concentration={_fmt_float(block.get('pc1_concentration_ratio'), 2)}, "
        f"severity={block.get('pc1_severity', 'unknown')}, "
        f"ENB={_fmt_float(block.get('effective_number_of_bets'), 2)}, "
        f"ENB ratio={_fmt_pct(block.get('effective_number_of_bets_ratio'), 2)}, "
        f"ENB severity={block.get('enb_severity', 'unknown')}, "
        f"PC1 stability={stability}"
    )


def _pca_loading_text(block: Any) -> str:
    if not isinstance(block, dict) or block.get("status") != "available":
        return "n/a"
    comps = block.get("components") or []
    if not comps or not isinstance(comps[0], dict):
        return "n/a"
    pc1 = comps[0]
    pos = pc1.get("top_positive_loadings") or []
    neg = pc1.get("top_negative_loadings") or []

    def _fmt_rows(rows: Any) -> str:
        if not isinstance(rows, list) or not rows:
            return "none"
        parts = []
        for row in rows[:3]:
            if isinstance(row, dict):
                parts.append(f"{row.get('asset')}={_fmt_float(row.get('loading'), 3)}")
        return ", ".join(parts) if parts else "none"

    return f"positive: {_fmt_rows(pos)}; negative: {_fmt_rows(neg)}"


def _pca_factor_corr_text(block: Any) -> str:
    if not isinstance(block, dict) or block.get("status") != "available":
        return "n/a"
    fc = block.get("pc1_factor_correlations") or {}
    if not isinstance(fc, dict) or fc.get("status") != "available":
        return f"unavailable ({fc.get('reason', 'unknown') if isinstance(fc, dict) else 'unknown'})"
    rows = fc.get("top_abs_correlations") or []
    parts = []
    for row in rows[:3]:
        if isinstance(row, dict):
            parts.append(f"{row.get('factor')}={_fmt_float(row.get('correlation'), 3)}")
    return ", ".join(parts) if parts else "none"


def _append_portfolio_pca_section(lines: list[str], st: dict[str, Any]) -> None:
    pca = st.get("portfolio_pca")
    if not isinstance(pca, dict) or not pca:
        return
    lines.append("Portfolio PCA diagnostics")
    if pca.get("status") != "available":
        lines.append(
            f"Portfolio PCA unavailable: reason={pca.get('reason', 'unknown')}; "
            f"window_weeks={pca.get('window_weeks', 'n/a')}."
        )
        lines.append("")
        return

    lines.append(
        "Covariance PCA is interpreted as risk dominance: it includes volatility scale. "
        "Correlation PCA is interpreted as structure: it standardizes asset volatility before extracting common movement."
    )
    lines.append(
        f"Universe: n_assets={pca.get('n_assets')}, n_obs={pca.get('n_obs')}, "
        f"included={', '.join(str(x) for x in (pca.get('included_assets') or []))}."
    )
    raw = pca.get("raw") or {}
    residual = pca.get("residual") or {}
    raw_cov = raw.get("covariance_pca") if isinstance(raw, dict) else None
    raw_corr = raw.get("correlation_pca") if isinstance(raw, dict) else None
    res_cov = residual.get("covariance_pca") if isinstance(residual, dict) else None
    res_corr = residual.get("correlation_pca") if isinstance(residual, dict) else None
    lines.append(f"Raw covariance PCA (risk dominance): {_pca_block_summary(raw_cov)}.")
    lines.append(f"Raw correlation PCA (structure): {_pca_block_summary(raw_corr)}.")
    lines.append(f"Residual covariance PCA (unexplained risk dominance): {_pca_block_summary(res_cov)}.")
    lines.append(f"Residual correlation PCA (unexplained structure): {_pca_block_summary(res_corr)}.")
    lines.append(f"Raw covariance PC1 loadings: {_pca_loading_text(raw_cov)}.")
    lines.append(f"Raw correlation PC1 loadings: {_pca_loading_text(raw_corr)}.")
    lines.append(f"Raw covariance PC1 factor correlations: {_pca_factor_corr_text(raw_cov)}.")
    if isinstance(res_cov, dict) and res_cov.get("pc1_severity") in {"high", "extreme"}:
        lines.append(
            "High residual PC1 means hidden common risk remains after the named factor model; review omitted factors, "
            "factor definitions, and asset-specific concentration."
        )
    lines.append("")


def write_stress_commentary(
    output_dir_final: Path,
    *,
    stress_report: dict[str, Any] | None,
    analysis_end: str | None = None,
) -> Path | None:
    """
    Write stress_commentary.txt from stress_report.json only (same run).

    Sections match portfolio-commentary rule order; numbers are not invented.
    Clarifies that synthetic/historical stress here is PM diagnostics, not the blocking mandate gate.
    """
    output_dir_final = Path(output_dir_final)
    label = _folder_portfolio_label(output_dir_final)
    ae = analysis_end or _MDASH
    st = stress_report or {}

    lines: list[str] = [
        "Source: stress_report.json (current run)",
        "",
        "Executive Summary",
    ]

    if not st:
        lines.append(
            f"For {label}, stress_report is empty or missing: scenario and factor diagnostics are unavailable. "
            f"analysis_end: {ae}."
        )
        lines.extend(
            [
                "",
                "Metric-by-Metric Interpretation",
                "No stress_report payload to expand scenarios and betas.",
                "",
                "Risk Structure",
                _NA,
                "",
                "Strengths",
                _NA,
                "",
                "Weaknesses",
                "stress_report is absent — cannot assess the stress profile from this run.",
                "",
                "Scenario Behavior",
                _NA,
                "",
                "Final Conclusion",
                "After stress_report.json is produced, rerun the report (run_report.py or the variant pipeline) "
                "to refresh stress_commentary.txt.",
            ]
        )
        out_path = output_dir_final / "stress_commentary.txt"
        out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return out_path

    status = st.get("status", "N/A")
    primary = st.get("primary_diagnostic_code") or st.get("fail_reason_code") or st.get("skip_reason") or _MDASH
    warn = st.get("warning_code")
    dcodes = st.get("diagnostic_codes") or []
    dc_str = ", ".join(str(x) for x in dcodes) if dcodes else _MDASH
    worst = st.get("worst_scenario_loss_pct")
    fs = st.get("failed_scenario")
    ft = st.get("failed_test")
    mdd_lim = st.get("max_dd_limit")

    exec_para = [
        f"Run: {label}; analysis_end: {ae}. "
        f"Overall stress bundle status in stress_report: {status}. "
        f"Primary code (primary / fail_reason): {primary}. "
        f"diagnostic_codes: {dc_str}.",
        "Synthetic scenarios and historical episodes in this file are PM diagnostics: they inform interpretation "
        "but do not by themselves release or block weights; mandate drawdown and client gates are enforced "
        "separately (mandate_check / IPS, full-history backtest).",
    ]
    if warn:
        exec_para.append(f"Report warning_code: {warn}.")
    wl = (
        f"Worst scenario portfolio PnL (worst_scenario_loss_pct): {_fmt_pct(worst)}; "
        f"named scenario: {fs or _MDASH}; failed_test: {ft or _MDASH}."
        if worst is not None
        else f"failed_scenario: {fs or _MDASH}; failed_test: {ft or _MDASH}."
    )
    exec_para.append(wl)
    lines.extend(exec_para)
    lines.append("")

    lines.append("Metric-by-Metric Interpretation")
    scen_rows = st.get("scenario_results") or []
    if scen_rows:
        lines.append(
            "Synthetic scenarios (stress_report.scenario_results): factor shocks to the portfolio as a whole; "
            "pass reflects the mandate PnL threshold (loss_ok). Top1 / Top3 RC are concentration diagnostics, "
            "not an extra pass/fail gate in stress_report. See pnl_by_asset_pct / pnl_by_factor_pct in JSON."
        )
        for row in scen_rows:
            sid = row.get("scenario_id", "?")
            pnl = row.get("portfolio_pnl_pct")
            top1a = row.get("top1_rc_asset")
            top1p = row.get("top1_rc_pct")
            top3s = row.get("top3_rc_sum_pct")
            lines.append(
                f"- {sid}: PnL ~ {_fmt_pct(pnl)}, pass={row.get('pass')}, loss_ok={row.get('loss_ok')}; "
                f"Top1 RC (dispersion): {top1a} ({_fmt_pct(top1p, 2)}); Top3 sum ~ {_fmt_pct(top3s, 2) if top3s is not None else _NA}."
            )
        sdiag = []
        for row in scen_rows:
            for c in row.get("diagnostic_codes") or []:
                if c not in sdiag:
                    sdiag.append(c)
        if sdiag:
            lines.append(
                f"Per-scenario codes (loss and RC where present, unique): {', '.join(str(x) for x in sdiag)}."
            )
    else:
        lines.append("scenario_results rows are absent in the report payload.")

    fb5 = _base_beta_map(st.get("factor_betas_5y") or st.get("factor_betas") or {})
    fb10 = _base_beta_map(st.get("factor_betas_10y") or {})
    lines.append(
        f"Portfolio factor betas (weekly estimation; see stress spec): 5Y ~ {{{_fmt_beta_dict(fb5 if isinstance(fb5, dict) else {})}}}; "
        f"10Y ~ {{{_fmt_beta_dict(fb10 if isinstance(fb10, dict) else {})}}}."
    )
    fr5 = st.get("factor_regression_5y")
    fr10 = st.get("factor_regression_10y")
    if isinstance(fr5, dict) and fr5:
        _append_factor_regression_section(lines, fr5, "5Y")
    elif st.get("factor_regression_5y_error"):
        lines.append(f"5Y factor regression: not computed — {st.get('factor_regression_5y_error')}")
        lines.append("")
    if isinstance(fr10, dict) and fr10:
        _append_factor_regression_section(lines, fr10, "10Y")
    elif st.get("factor_regression_10y_error"):
        lines.append(f"10Y factor regression: not computed — {st.get('factor_regression_10y_error')}")
        lines.append("")
    _append_rolling_betas_section(lines, st, output_dir_final)
    _append_factor_beta_stability_section(lines, st)
    _append_kalman_factor_betas_section(lines, st)
    _append_diagnostic_oil_beta_section(lines, st)
    _append_factor_beta_adjusted_overlay_section(lines, st)
    _append_factor_covariance_section(lines, st)
    _append_macro_regime_section(lines, st)
    _append_regime_factor_analytics_window_section(lines, st)
    _append_factor_variance_decomposition_section(lines, st)
    _append_portfolio_pca_section(lines, st)
    lines.append("")

    fd = st.get("frequency_disclosure")
    if isinstance(fd, dict) and fd:
        lines.append("Data cadence (optimization vs stress)")
        lines.append(
            f"returns_frequency={fd.get('returns_frequency')}, optimization_frequency={fd.get('optimization_frequency')}, "
            f"factor_stress_frequency={fd.get('factor_stress_frequency')}, "
            f"macro_regime_frequency={fd.get('macro_regime_frequency')}; "
            f"frequency_mismatch_warning={fd.get('frequency_mismatch_warning')}."
        )
        notes = fd.get("macro_regime_frequency_notes")
        if isinstance(notes, str) and notes.strip():
            lines.append(notes.strip())
        if fd.get("frequency_mismatch_warning"):
            lines.append(
                "Non-uniform cadence: align interpretation of stress/regime blocks with the frequencies above; "
                "full alignment of factor/regime panels with daily/weekly optimization is Phase 2."
            )
        lines.append("")

    lines.append("Risk Structure")
    caps_line = []
    if mdd_lim is not None:
        caps_line.append(
            f"Drawdown threshold for scenario loss test (max_dd_limit in JSON)={_fmt_pct(mdd_lim)}"
        )
    lines.append(
        "; ".join(caps_line)
        if caps_line
        else "max_dd_limit is not set in stress_report or n/a."
    )
    if scen_rows:
        triples = [(r.get("scenario_id"), r.get("top1_rc_asset"), r.get("top1_rc_pct")) for r in scen_rows]
        tops = ", ".join(
            f"{sid} {asset}={_fmt_pct(p, 1)}"
            for sid, asset, p in triples
            if p is not None and asset is not None
        )
        lines.append(f"Top1 RC by scenario (see table above): {tops}.")
    hist = st.get("historical_results") or []
    if hist:
        lines.append("Historical episodes (historical_results):")
        if any(isinstance(h, dict) and h.get("historical_factor_attribution") for h in hist):
            lines.append(
                "Historical factor attribution caveat: model-based attribution = beta times realized factor shock; "
                "it is not a pure realized causal decomposition."
            )
        for h in hist:
            ep = h.get("episode", "?")
            mdd = h.get("max_dd")
            pnl_real_ep = h.get("pnl_real_episode")
            vp = h.get("pass")
            vole = h.get("vol_annualized_episode")
            dcode = h.get("diagnostic_code")
            lines.append(
                f"- {ep}: pnl_real_episode ~ {_fmt_pct(pnl_real_ep)}, max_dd ~ {_fmt_pct(mdd)}, pass={vp}, "
                f"vol_annualized_episode ~ {_fmt_float(vole, 4) if vole is not None else _NA}, "
                f"diagnostic_code={dcode or _MDASH}."
            )
            driver_line = _historical_driver_line(h)
            if driver_line:
                largest = _fmt_factor_driver(h.get("largest_negative_factor"))
                lines.append(
                    f"  Factor attribution (5Y beta, model-based): model_pnl={_fmt_pct(h.get('factor_model_pnl_pct'))}, "
                    f"model_error={_fmt_pct(h.get('factor_model_error_pct'))}; top drivers: {driver_line}; "
                    f"largest loss driver: {largest}."
                )
        vuln = _historical_vulnerability_summary([h for h in hist if isinstance(h, dict)])
        if vuln:
            lines.append(vuln)
    else:
        lines.append("Historical episodes are absent in JSON.")
    oos = st.get("factor_beta_shock_oos")
    if isinstance(oos, dict) and oos.get("episodes"):
        lines.append("Out-of-sample episode explainability via beta x shock (5Y/10Y/rolling-3Y pre):")
        for e in oos.get("episodes") or []:
            if not isinstance(e, dict):
                continue
            lines.append(
                f"- {e.get('episode', '?')}: real={_fmt_pct(e.get('pnl_real_episode'))}, "
                f"model_5y={_fmt_pct(e.get('pnl_model_5y'))}, model_10y={_fmt_pct(e.get('pnl_model_10y'))}, "
                f"model_roll3y={_fmt_pct(e.get('pnl_model_roll3y_pre'))}; "
                f"|err|: 5y={_fmt_pct(e.get('abs_error_5y'))}, 10y={_fmt_pct(e.get('abs_error_10y'))}, roll3y={_fmt_pct(e.get('abs_error_roll3y_pre'))}."
            )
        summ = oos.get("summary") or {}
        if isinstance(summ, dict) and summ:
            lines.append(
                f"Mean absolute error across episodes: 5Y={_fmt_pct(summ.get('mean_abs_error_5y'))}, "
                f"10Y={_fmt_pct(summ.get('mean_abs_error_10y'))}, rolling-3Y={_fmt_pct(summ.get('mean_abs_error_roll3y_pre'))} "
                f"(n={summ.get('n_episodes_with_real_pnl', _MDASH)})."
            )
    lines.append("")

    lines.append("Strengths")
    str_lines: list[str] = []
    if scen_rows:
        if all(row.get("loss_ok") is True for row in scen_rows):
            str_lines.append(
                "All synthetic scenarios have loss_ok=true — portfolio loss within loss-test thresholds."
            )
        if any(row.get("pass") is True for row in scen_rows):
            str_lines.append("At least one scenario has pass=true on mandate PnL.")
    for h in hist:
        if h.get("pass") is True:
            str_lines.append(f"Historical episode {h.get('episode')} is marked pass=true.")
    if status in ("DIAG_PASS", "DIAG_PASS_WITH_WARNING", "PASS", "PASS_WITH_WARNING"):
        str_lines.append(f"Bundle status {status} — not at DIAG_ATTENTION.")
    if not str_lines:
        str_lines.append("Few obvious positive flags in JSON — see Weaknesses.")
    lines.extend(str_lines)
    lines.append("")

    lines.append("Weaknesses")
    wk: list[str] = []
    if status == "DIAG_ATTENTION":
        wk.append(
            f"DIAG_ATTENTION: diagnostic codes recorded ({dc_str}); review scenario_results and historical_results."
        )
    if warn:
        wk.append(
            f"warning_code={warn} (see stress_report for borderline historical data or other warnings)."
        )
    if hist:
        for h in hist:
            if h.get("max_dd") is None and h.get("episode"):
                wk.append(
                    f"Episode {h.get('episode')}: max_dd n/a — interpretation limited."
                )
    if not wk:
        wk.append("No material flags in JSON or profile is neutral versus listed checks.")
    lines.extend(wk)
    lines.append("")

    lines.append("Scenario Behavior")
    if scen_rows:
        for row in scen_rows:
            sid = row.get("scenario_id")
            pnl = row.get("portfolio_pnl_pct")
            lines.append(
                f"{sid}: PnL ~ {_fmt_pct(pnl)}, pass={row.get('pass')} (mandate loss); "
                f"RC shares — Metric-by-Metric."
            )
    else:
        lines.append("No scenario_results.")
    lines.append("")

    lines.append("Final Conclusion")
    lines.append(
        f"{label}: stress bundle {status} ({primary}). "
        f"Synthetic losses and RC diagnostics reflect the current holdings and covariance from this run; "
        f"align weight-release decisions with mandate_check and run_result — use this file as PM scenario reference."
    )

    out_path = output_dir_final / "stress_commentary.txt"
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out_path


def write_portfolio_commentary(
    output_dir_final: Path,
    *,
    output_dir_csv: Path,
    portfolio_metrics_10y: dict[str, Any] | None,
    stress_report: dict[str, Any] | None,
    portfolio_valid: bool | None,
    analysis_end: str | None = None,
    frequency_disclosure: dict[str, Any] | None = None,
    analysis_setup: dict[str, Any] | None = None,
) -> Path | None:
    """
    Write commentary.txt under output_dir_final using metrics + stress + rc_vol CSV.
    All numbers come from the passed dicts / files from this run.
    """
    output_dir_final = Path(output_dir_final)
    output_dir_csv = Path(output_dir_csv)
    label = _folder_portfolio_label(output_dir_final)
    pm = portfolio_metrics_10y or {}
    st = stress_report or {}

    sources = [
        "summary.txt (if present)",
        "stress_report.json",
        "results_csv/portfolio_metrics_10y.csv",
        "results_csv/rc_vol_10y.csv",
        "run_metadata.json / analysis_setup",
        "report.txt",
    ]
    if output_dir_csv.resolve() != (output_dir_final / "results_csv").resolve():
        sources.append(f"CSV directory: {output_dir_csv.as_posix()}")

    cagr = pm.get("cagr")
    vol = pm.get("vol_annual")
    mdd = pm.get("max_drawdown")
    sharpe = pm.get("sharpe")
    sortino = pm.get("sortino")
    beta = pm.get("beta_portfolio")
    corr = pm.get("corr_base")
    treynor = pm.get("treynor")

    stress_status = st.get("status", "N/A")
    fail_reason = (
        st.get("primary_diagnostic_code")
        or st.get("fail_reason_code")
        or st.get("skip_reason")
        or _MDASH
    )
    failed_scenario = st.get("failed_scenario")
    failed_test = st.get("failed_test")
    worst_loss = st.get("worst_scenario_loss_pct")

    rc_top = _load_rc_top5(output_dir_csv)
    rc_lines = (
        ", ".join(f"{t} {_fmt_pct(r, 1)}" for t, r in rc_top)
        if rc_top
        else "n/a (no rc_vol_*.csv or empty)"
    )

    client_gate = "PASS" if portfolio_valid else "FAIL"
    if portfolio_valid is None:
        client_gate = _NA

    ae = analysis_end or _MDASH
    scen_lines = _scenario_snippets(st)
    snapshot_10y_path = output_dir_final / "snapshot_10y.json"
    portfolio_analytics_10y: dict[str, Any] | None = None
    drawdown_structure_10y: dict[str, Any] | None = None
    if snapshot_10y_path.is_file():
        try:
            snap_10y = json.loads(snapshot_10y_path.read_text(encoding="utf-8"))
            if isinstance(snap_10y, dict):
                portfolio_analytics_10y = snap_10y.get("analytics")
                drawdown_structure_10y = snap_10y.get("drawdown_structure")
        except Exception:
            portfolio_analytics_10y = None
    xray_summary = build_portfolio_xray_v2(
        analysis_setup=analysis_setup,
        weights=None,
        rc_asset=[{"ticker": ticker, "rc_pct": value} for ticker, value in rc_top],
        stress_report=st,
        portfolio_valid=portfolio_valid,
        portfolio_metrics=pm,
        portfolio_analytics=portfolio_analytics_10y if isinstance(portfolio_analytics_10y, dict) else None,
        drawdown_structure=drawdown_structure_10y if isinstance(drawdown_structure_10y, dict) else None,
        rc_vol_map=load_rc_vol_map_from_csv(output_dir_csv),
        output_dir_csv=output_dir_csv,
    )

    # Executive summary (3–5 sentences)
    exec_lines = [
        f"This run is {label}; analysis_end: {ae}. "
        f"On the long window (10Y in the report context) the portfolio shows CAGR ~ {_fmt_pct(cagr)}, "
        f"annualized volatility ~ {_fmt_pct(vol)}, maximum drawdown ~ {_fmt_pct(mdd)}.",
        f"Risk-adjusted: Sharpe ~ {_fmt_float(sharpe)}, Sortino ~ {_fmt_float(sortino)}; "
        f"sensitivity to the base benchmark: Beta_base ~ {_fmt_float(beta)}"
        + (
            f", correlation with benchmark (Corr_base) ~ {_fmt_float(corr)}."
            if corr is not None and not (isinstance(corr, float) and math.isnan(corr))
            else "."
        ),
        f"Stress test: {stress_status}"
        + (f" ({fail_reason})" if fail_reason != _MDASH else "")
        + (
            f"; worst-loss scenario: {failed_scenario} ({failed_test})" if failed_scenario else ""
        )
        + (f"; worst_scenario_loss_pct ~ {_fmt_pct(worst_loss)}" if worst_loss is not None else "")
        + ".",
        f"Client MaxDD gate (portfolio_valid): {client_gate}.",
    ]

    # Sections
    lines: list[str] = []
    lines.append(
        "Source: summary.txt, stress_report.json, results_csv/portfolio_metrics_10y.csv, "
        "results_csv/rc_vol_10y.csv, run_metadata.json / analysis_setup, report.txt"
    )
    lines.append("")
    lines.append(format_portfolio_xray_commentary(xray_summary))
    lines.append("")
    lines.append("Executive Summary")
    lines.extend(exec_lines)
    lines.append("")

    lines.append("Metric-by-Metric Interpretation")
    rf_lbl = str((frequency_disclosure or {}).get("returns_frequency") or "monthly")
    lines.append(
        f"CAGR ({_fmt_pct(cagr)}) is the compound annual growth rate from simple returns at {rf_lbl} cadence on the 10Y window in this run. "
        f"Volatility ({_fmt_pct(vol)}) is annualized using the same return frequency; MaxDD ({_fmt_pct(mdd)}) is from the matching equity curve. "
        f"Sharpe ({_fmt_float(sharpe)}) and Sortino ({_fmt_float(sortino)}) follow project definitions (Sharpe uses raw return vol in the denominator). "
        f"Beta_base ({_fmt_float(beta)}) and Treynor ({_fmt_float(treynor)}) tie to the base benchmark; Corr_base, when present, is correlation with the benchmark on the same window."
    )
    lines.append("")

    lines.append("Risk Structure")
    lines.append(
        f"Largest RC_vol shares (portfolio variance contribution) on 10Y: {rc_lines}. "
        f"Stress: status={stress_status}, fail_reason_code={fail_reason}."
        + (
            f" Failed scenario «{failed_scenario}», test «{failed_test}»." if failed_scenario else ""
        )
    )
    fd = frequency_disclosure or {}
    if fd:
        lines.append("")
        lines.append("Data frequency")
        lines.append(
            f"optimization_frequency={fd.get('optimization_frequency')}, returns_frequency={fd.get('returns_frequency')}, "
            f"factor_stress_frequency={fd.get('factor_stress_frequency')}, "
            f"macro_regime_frequency={fd.get('macro_regime_frequency')}; "
            f"frequency_mismatch_warning={fd.get('frequency_mismatch_warning')}."
        )
        notes = fd.get("macro_regime_frequency_notes")
        if isinstance(notes, str) and notes.strip():
            lines.append(f"macro_regime_frequency_notes: {notes.strip()}")
        if fd.get("frequency_mismatch_warning"):
            lines.append(
                "Non-uniform cadence across blocks: align interpretation of stress/regime diagnostics with the "
                "frequencies above; full factor/regime alignment with daily/weekly optimization is Phase 2."
            )
    lines.append("")

    lines.append("Strengths")
    _stress_clear = stress_status in ("PASS", "DIAG_PASS", "DIAG_PASS_WITH_WARNING", "PASS_WITH_WARNING")
    if _stress_clear and client_gate == "PASS":
        lines.append(
            "Stress diagnostics show no critical flags (or warnings only); mandate MaxDD gate PASS — "
            "realized drawdown vs client threshold does not conflict in this run."
        )
    elif client_gate == "PASS":
        lines.append(
            "Mandate MaxDD gate PASS: realized drawdown on full overlapping history is within tolerance "
            "(see run_metadata / mandate_check)."
        )
    else:
        lines.append("Review client gate and/or stress status — see Weaknesses below.")
    if sharpe is not None and float(sharpe) >= 1.0:
        lines.append(
            f"Sharpe >= 1.0 ({_fmt_float(sharpe)}) on this window — relatively strong risk-adjusted compensation historically."
        )
    lines.append("")

    lines.append("Weaknesses")
    if stress_status == "DIAG_ATTENTION":
        lines.append(
            f"Stress diagnostics: {stress_status} — {fail_reason}. "
            f"(Does not block release by itself; named scenario: {failed_scenario or _MDASH}; test: {failed_test or _MDASH}.)"
        )
    if client_gate == "FAIL":
        lines.append(
            "Client MaxDD gate FAIL — historical max drawdown exceeds mandate (see run_metadata / snapshot)."
        )
    if not rc_top:
        lines.append(
            "RC_vol top-5 not extracted from CSV — verify results_csv/rc_vol_10y.csv exists after the run."
        )
    lines.append("")

    lines.append("Scenario Behavior")
    if scen_lines:
        lines.append("Scenario snapshot from stress_report.json: " + "; ".join(scen_lines) + ".")
    else:
        lines.append("Scenario detail in stress_report.json is missing or not parsed.")
    if worst_loss is not None:
        lines.append(f"Worst scenario portfolio loss (worst_scenario_loss_pct): ~ {_fmt_pct(worst_loss)}.")
    lines.append("")

    lines.append("Final Conclusion")
    lines.append(
        f"{label}: the 10Y return/risk profile is summarized by CAGR ~ {_fmt_pct(cagr)}, vol ~ {_fmt_pct(vol)}, MaxDD ~ {_fmt_pct(mdd)}. "
        f"Stress {stress_status} ({fail_reason}); client gate {client_gate}. "
        f"To compare variants, use the same files in sibling folders (Equal-Weight / Risk Parity / Main portfolio) after a synchronized run."
    )

    text = "\n".join(lines) + "\n"
    out_path = output_dir_final / "commentary.txt"
    out_path.write_text(text, encoding="utf-8")
    return out_path
