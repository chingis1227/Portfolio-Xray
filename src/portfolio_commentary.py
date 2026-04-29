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

from src.stress_factors import BETA_ROW_ORDER


def _folder_portfolio_label(output_dir_final: Path) -> str:
    name = output_dir_final.name.strip().lower()
    if name == "main portfolio":
        return "РѕСЃРЅРѕРІРЅРѕР№ РїРѕСЂС‚С„РµР»СЊ (Main portfolio)"
    if "equal" in name and "weight" in name:
        return "Equal-Weight baseline"
    if "risk" in name and "parity" in name:
        return "Risk-Parity baseline"
    return output_dir_final.name


def _fmt_pct(x: Any, digits: int = 2) -> str:
    if x is None:
        return "РЅ/Рґ"
    try:
        v = float(x)
    except (TypeError, ValueError):
        return "РЅ/Рґ"
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
        return "РЅ/Рґ"
    return f"{v * 100:.{digits}f}%"


def _fmt_float(x: Any, digits: int = 3) -> str:
    if x is None:
        return "РЅ/Рґ"
    try:
        v = float(x)
    except (TypeError, ValueError):
        return "РЅ/Рґ"
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
        return "РЅ/Рґ"
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
            lines.append(f"{sid}: PnLв‰€{_fmt_pct(pnl, 2)}, pass={ok}")
    return lines[:6]


def _fmt_beta_dict(d: dict[str, Any] | None) -> str:
    if not d:
        return "РЅ/Рґ"
    parts = []
    for k in sorted(d.keys()):
        parts.append(f"{k}={_fmt_float(d.get(k), 4)}")
    return ", ".join(parts) if parts else "РЅ/Рґ"


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


def _ordered_beta_keys(*maps: Any) -> list[str]:
    ordered: list[str] = []
    seen: set[str] = set()
    for key in BETA_ROW_ORDER:
        if any(isinstance(m, dict) and key in m for m in maps):
            ordered.append(key)
            seen.add(key)
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
        return "РЅ/Рґ"
    try:
        v = float(x)
    except (TypeError, ValueError):
        return "РЅ/Рґ"
    if v == 0.0 or (isinstance(v, float) and v < 1e-6):
        return "<1e-6"
    return _fmt_float(v, 6)


def _append_factor_multicollinearity_section(lines: list[str], mc: Any) -> None:
    """Append factor multicollinearity (same rows as OLS regressors); from factor_multicollinearity in stress_report."""
    if not isinstance(mc, dict) or not mc:
        return
    lines.append("Мультиколлинеарность факторов")
    err = mc.get("error")
    if err:
        lines.append(f"РњСѓР»СЊС‚РёРєРѕР»Р»РёРЅРµР°СЂРЅРѕСЃС‚СЊ С„Р°РєС‚РѕСЂРѕРІ (РґРёР°РіРЅРѕСЃС‚РёРєР°): РЅРµ РїРѕСЃС‡РёС‚Р°РЅР° вЂ” {err}")
        lines.append("")
        return
    sev = mc.get("severity", "вЂ”")
    mvif_str = "в€ћ" if mc.get("max_vif_is_infinite") else _fmt_float(mc.get("max_vif"), 3)
    mvf = mc.get("max_vif_factor")
    fac_suffix = f" (С„Р°РєС‚РѕСЂ {mvf})" if mvf else ""
    lines.append(
        f"РњСѓР»СЊС‚РёРєРѕР»Р»РёРЅРµР°СЂРЅРѕСЃС‚СЊ С„Р°РєС‚РѕСЂРѕРІ (С‚Рµ Р¶Рµ РЅРµРґРµР»Рё, С‡С‚Рѕ СЂРµРіСЂРµСЃСЃРёСЏ): РѕС†РµРЅРєР°={sev}; "
        f"cond(R)={mc.get('cond_correlation_matrix', 'РЅ/Рґ')}; "
        f"max VIF={mvif_str}{fac_suffix}."
    )
    sp = mc.get("strongest_pair")
    if isinstance(sp, dict) and sp.get("factor_i"):
        lines.append(
            f"РЎРёР»СЊРЅРµР№С€Р°СЏ РїРѕРїР°СЂРЅР°СЏ РєРѕСЂСЂРµР»СЏС†РёСЏ: {sp.get('factor_i')} vs {sp.get('factor_j')}, ПЃ={_fmt_float(sp.get('rho'), 4)}."
        )
    lines.append(f"РРЅС‚РµСЂРїСЂРµС‚Р°С†РёСЏ: {mc.get('assessment_ru', 'вЂ”')}")
    pairs = mc.get("pairwise_correlations") or []
    if isinstance(pairs, list) and pairs:
        lines.append("Р’СЃРµ РїРѕРїР°СЂРЅС‹Рµ ПЃ (|ПЃ| РїРѕ СѓР±С‹РІР°РЅРёСЋ):")
        for row in pairs:
            if not isinstance(row, dict):
                continue
            lines.append(
                f"  {row.get('factor_i')} вЂ” {row.get('factor_j')}: ПЃ={_fmt_float(row.get('rho'), 4)}"
            )
    vif_bf = mc.get("vif_by_factor") or {}
    if isinstance(vif_bf, dict) and vif_bf:
        lines.append("VIF по факторам:")
        lines.append("VIF РїРѕ С„Р°РєС‚РѕСЂР°Рј:")
        for fname in sorted(vif_bf.keys()):
            v = vif_bf[fname]
            vs = "в€ћ" if v is None else _fmt_float(v, 3)
            lines.append(f"  {fname}: {vs}")
    lines.append(f"РњРµС‚РѕРґ: {mc.get('method', 'вЂ”')}; n_obs_f={mc.get('n_obs_factors', 'вЂ”')}.")
    lines.append("")


def _append_serial_correlation_section(lines: list[str], ser: Any) -> None:
    """DurbinвЂ“Watson + BreuschвЂ“Godfrey on portfolio factor OLS residuals (same ordering as regression)."""
    if not isinstance(ser, dict) or not ser:
        return
    lines.append("Durbin–Watson / Breusch–Godfrey")
    if ser.get("error"):
        lines.append(f"РђРІС‚РѕРєРѕСЂСЂРµР»СЏС†РёСЏ РѕСЃС‚Р°С‚РєРѕРІ (DW / BreuschвЂ“Godfrey): РЅРµ РїРѕСЃС‡РёС‚Р°РЅР° вЂ” {ser.get('error')}")
        lines.append("")
        return
    dw = ser.get("durbin_watson")
    lines.append(
        f"РђРІС‚РѕРєРѕСЂСЂРµР»СЏС†РёСЏ РѕСЃС‚Р°С‚РєРѕРІ С„Р°РєС‚РѕСЂРЅРѕР№ OLS: DurbinвЂ“Watson={_fmt_float(dw, 4) if dw is not None else 'РЅ/Рґ'} "
        f"(в‰€2 вЂ” РјР°Р»Рѕ РђРљ РїРµСЂРІРѕРіРѕ РїРѕСЂСЏРґРєР°; РјРµС‚РѕРґ: {ser.get('method', 'вЂ”')})."
    )
    bg = ser.get("breusch_godfrey") or []
    if isinstance(bg, list) and bg:
        lines.append("BreuschвЂ“Godfrey LM (Hв‚Ђ: РЅРµС‚ РђРљ РґРѕ РїРѕСЂСЏРґРєР° p; LM ~ П‡ВІ(p)):")
        for row in bg:
            if not isinstance(row, dict):
                continue
            pv = row.get("p_value")
            lines.append(
                f"  lags={row.get('lags', 'вЂ”')}: LM={_fmt_float(row.get('lm_statistic'), 4)}, "
                f"df={row.get('df_chi2', 'вЂ”')}, p={_fmt_p_value(pv)}, "
                f"T_aux={row.get('n_aux_observations', 'вЂ”')}, RВІ_aux={_fmt_float(row.get('aux_r_squared'), 4)}"
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
    lines.append(f"Портфельная факторная регрессия ({label})")
    betas = fr.get("betas") or {}
    t_d = fr.get("t") or {}
    p_d = fr.get("p") or {}
    lo = fr.get("ci_low") or {}
    hi = fr.get("ci_high") or {}
    beta_order = _ordered_beta_keys(betas, t_d, p_d, lo, hi)
    lines.append(
        f"РџРѕСЂС‚С„РµР»СЊРЅР°СЏ С„Р°РєС‚РѕСЂРЅР°СЏ СЂРµРіСЂРµСЃСЃРёСЏ ({label}), РЅРµРґРµР»СЊРЅС‹Рµ СЂСЏРґС‹, OLS: "
        f"n_obs={fr.get('n_obs', 'РЅ/Рґ')}, RВІ={_fmt_float(fr.get('r2'), 4)}, "
        f"idiosyncratic risk (1-RВІ)={_fmt_float(fr.get('idiosyncratic_risk'), 4)}, "
        f"adj RВІ={_fmt_float(fr.get('adj_r2'), 4)}, intercept={_fmt_float(fr.get('intercept'), 4)}, "
        f"se_type={fr.get('se_type', 'вЂ”')}, alpha={fr.get('alpha', 'вЂ”')} (CI СѓСЂРѕРІРµРЅСЊ {fr.get('ci_level', 'вЂ”')})."
    )
    lines.append("РџРѕ С„Р°РєС‚РѕСЂР°Рј (ОІ, t, p, 95% CI) вЂ” РєР»Р°СЃСЃРёС‡РµСЃРєРёР№ OLS (se_type=classic_ols):")
    for key in beta_order:
        if key not in betas and key not in t_d:
            continue
        lines.append(
            f"- {key}: ОІ={_fmt_float(betas.get(key), 4)}, t={_fmt_float(t_d.get(key), 3)}, "
            f"p={_fmt_p_value(p_d.get(key))}, CI=[{_fmt_float(lo.get(key), 4)}; {_fmt_float(hi.get(key), 4)}]"
        )
    # HAC / NeweyвЂ“West inference (СЂРѕР±Р°СЃС‚РЅС‹Рµ SE)
    hac = fr.get("hac_inference") or {}
    if isinstance(hac, dict) and hac:
        hac_se = hac.get("se")
        hac_t = hac.get("t")
        hac_p = hac.get("p")
        hac_lo = hac.get("ci_low")
        hac_hi = hac.get("ci_high")
        lines.append(
            f"HAC/NeweyвЂ“West (robust) inference: se_type={hac.get('se_type', 'hac_newey_west')}, "
            f"kernel={hac.get('kernel', 'bartlett')}, max_lags={hac.get('max_lags', 'вЂ”')}."
        )
        if isinstance(hac_se, list) and isinstance(hac_t, list) and isinstance(hac_p, list):
            # РРЅРґРµРєСЃС‹: 0 вЂ” intercept, 1.. вЂ” С„Р°РєС‚РѕСЂС‹ РІ С‚РѕРј Р¶Рµ РїРѕСЂСЏРґРєРµ, С‡С‚Рѕ Рё factor_cols / beta_keys.
            lines.append("РџРѕ С„Р°РєС‚РѕСЂР°Рј (HAC t, p, 95% CI):")
            # РїРѕСЃС‚СЂРѕРёРј РјР°РїСѓ РїРѕ beta_keys РёР· РїРѕР·РёС†РёР№
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
        lines.append("Скользящие окна")
        lines.append(f"РЎРєРѕР»СЊР·СЏС‰РёРµ РѕРєРЅР° (РЅРµРґРµР»СЊ): {', '.join(f'{k}={v}' for k, v in sorted(rw.items()))}.")

    summ = st.get("factor_betas_rolling_summary")
    if isinstance(summ, dict) and summ:
        lines.append("РЎРІРѕРґРєР° СЃРєРѕР»СЊР·СЏС‰РёС… ОІ (РїРѕ РІСЃРµР№ РґРѕСЃС‚СѓРїРЅРѕР№ РёСЃС‚РѕСЂРёРё РІ РїСЂРѕРіРѕРЅРµ): mean, median, p10, p90:")
        for win in sorted(summ.keys(), key=lambda x: (len(str(x)), str(x))):
            by_b = summ.get(win) or {}
            if not isinstance(by_b, dict):
                continue
            lines.append(f"РћРєРЅРѕ {win}:")
            for bkey in _ordered_beta_keys(by_b):
                row = by_b.get(bkey)
                if not isinstance(row, dict):
                    continue
                lines.append(
                    f"  {bkey}: n={row.get('n_points', 'вЂ”')}, mean={_fmt_float(row.get('mean'), 4)}, "
                    f"median={_fmt_float(row.get('median'), 4)}, p10={_fmt_float(row.get('p10'), 4)}, "
                    f"p90={_fmt_float(row.get('p90'), 4)}"
                )
            lines.append("")
    elif st.get("factor_betas_rolling_error"):
        lines.append(f"РЎРєРѕР»СЊР·СЏС‰РёРµ Р±РµС‚С‹: РѕС€РёР±РєР° СЂР°СЃС‡С‘С‚Р° вЂ” {st.get('factor_betas_rolling_error')}")

    art = st.get("factor_betas_rolling_artifacts")
    if isinstance(art, dict):
        png_map = art.get("plot_png_by_window") or {}
        if png_map:
            lines.append("Р¤Р°Р№Р»С‹ РіСЂР°С„РёРєРѕРІ СЃРєРѕР»СЊР·СЏС‰РёС… ОІ (PNG, РїР°РїРєР° РїСЂРѕРіРѕРЅР°): " + ", ".join(f"{k}в†’{v}" for k, v in sorted(png_map.items())))

    labels = ("3y", "5y", "10y")
    for lbl in labels:
        png = output_dir_final / f"rolling_factor_betas_{lbl}.png"
        if not png.is_file():
            continue
        rel = _relpath_for_pdf_md_image(png, output_dir_final)
        if rel:
            lines.append(f"![Rolling factor betas вЂ” {lbl}]({rel})")
    lines.append("")


def _append_factor_beta_stability_section(lines: list[str], st: dict[str, Any]) -> None:
    stability = st.get("factor_betas_stability")
    if not isinstance(stability, dict) or not stability:
        return

    lines.append("Диагностика стабильности факторных beta")
    lines.append("Factor beta stability diagnostics: sign stability, magnitude stability, specification sensitivity, and OOS rolling-forward stability.")

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
    for beta_key in _ordered_beta_keys(by_beta):
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

    latest = kalman.get("latest") or {}
    latest_raw = kalman.get("latest_raw") or {}
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
        for beta_key in _ordered_beta_keys(latest_raw)
        if isinstance(cap_diag.get(beta_key), dict) and (cap_diag.get(beta_key) or {}).get("was_capped")
    ]
    if capped:
        lines.append("Capped Kalman betas: " + "; ".join(capped) + ".")

    divergent = divergence.get("divergent_betas") if isinstance(divergence, dict) else []
    by_div = divergence.get("by_beta") if isinstance(divergence, dict) else {}
    if divergent and isinstance(by_div, dict):
        parts = []
        for beta_key in _ordered_beta_keys({k: 1 for k in divergent}):
            row = by_div.get(beta_key) or {}
            parts.append(
                f"{beta_key}: kalman={_fmt_float(row.get('kalman'), 4)}, "
                f"5Y={_fmt_float(row.get('benchmark'), 4)}, reason={row.get('reason', 'n/a')}"
            )
        lines.append("Kalman vs 5Y divergence flags: " + "; ".join(parts) + ".")

    high_uncertainty = kalman.get("high_uncertainty_betas") or []
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
    for beta_key in _ordered_beta_keys(raw_map, adj_map):
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
    if zero_filled:
        lines.append(f"Zero-filled missing factor betas: {', '.join(str(x) for x in zero_filled)}.")
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
    ae = analysis_end or "вЂ”"
    st = stress_report or {}

    lines: list[str] = [
        "Source: stress_report.json (С‚РµРєСѓС‰РёР№ РїСЂРѕРіРѕРЅ)",
        "",
        "Executive Summary",
    ]

    if not st:
        lines.append(
            f"РџРѕ {label} РѕР±СЉРµРєС‚ stress_report РїСѓСЃС‚ РёР»Рё РЅРµ РїРµСЂРµРґР°РЅ: СЃС†РµРЅР°СЂРЅР°СЏ Рё С„Р°РєС‚РѕСЂРЅР°СЏ РґРёР°РіРЅРѕСЃС‚РёРєР° РЅРµРґРѕСЃС‚СѓРїРЅР°. "
            f"РљРѕРЅРµС† РІС‹Р±РѕСЂРєРё (analysis_end): {ae}."
        )
        lines.extend(
            [
                "",
                "Metric-by-Metric Interpretation",
                "РќРµС‚ РґР°РЅРЅС‹С… stress_report РґР»СЏ СЂР°Р·Р±РѕСЂР° СЃС†РµРЅР°СЂРёРµРІ Рё Р±РµС‚.",
                "",
                "Risk Structure",
                "РЅ/Рґ",
                "",
                "Strengths",
                "РЅ/Рґ",
                "",
                "Weaknesses",
                "РћС‚СЃСѓС‚СЃС‚РІСѓРµС‚ stress_report вЂ” РЅРµР»СЊР·СЏ РѕС†РµРЅРёС‚СЊ СЃС‚СЂРµСЃСЃ-РїСЂРѕС„РёР»СЊ РїРѕ РїСЂРѕРµРєС‚Сѓ.",
                "",
                "Scenario Behavior",
                "РЅ/Рґ",
                "",
                "Final Conclusion",
                f"РџРѕСЃР»Рµ РїРѕСЏРІР»РµРЅРёСЏ stress_report.json РїРµСЂРµР·Р°РїСѓСЃС‚РёС‚Рµ РѕС‚С‡С‘С‚ (run_report / РїСЂРѕРіРѕРЅ РІР°СЂРёР°РЅС‚Р°), С‡С‚РѕР±С‹ РѕР±РЅРѕРІРёС‚СЊ stress_commentary.txt.",
            ]
        )
        out_path = output_dir_final / "stress_commentary.txt"
        out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return out_path

    status = st.get("status", "N/A")
    primary = st.get("primary_diagnostic_code") or st.get("fail_reason_code") or st.get("skip_reason") or "вЂ”"
    warn = st.get("warning_code")
    dcodes = st.get("diagnostic_codes") or []
    dc_str = ", ".join(str(x) for x in dcodes) if dcodes else "вЂ”"
    worst = st.get("worst_scenario_loss_pct")
    fs = st.get("failed_scenario")
    ft = st.get("failed_test")
    mdd_lim = st.get("max_dd_limit")

    exec_para = [
        f"РџСЂРѕРіРѕРЅ: {label}; РєРѕРЅРµС† РІС‹Р±РѕСЂРєРё (analysis_end): {ae}. "
        f"РС‚РѕРіРѕРІС‹Р№ СЃС‚Р°С‚СѓСЃ СЃС‚СЂРµСЃСЃ-РЅР°Р±РѕСЂР° РІ stress_report: {status}. "
        f"РћСЃРЅРѕРІРЅРѕР№ РєРѕРґ (primary / fail_reason): {primary}. "
        f"РЎРїРёСЃРѕРє diagnostic_codes: {dc_str}.",
        "Это диагностическая справка по стрессам: сценарии и исторические эпизоды здесь используются для диагностики и интерпретации.",
        "РџРѕ СЂР°Р±РѕС‡РµРјСѓ РїСЂРѕС†РµСЃСЃСѓ РїСЂРѕРµРєС‚Р° СЃРёРЅС‚РµС‚РёС‡РµСЃРєРёРµ СЃС†РµРЅР°СЂРёРё Рё РёСЃС‚РѕСЂРёС‡РµСЃРєРёРµ СЌРїРёР·РѕРґС‹ РІ СЌС‚РѕРј С„Р°Р№Р»Рµ вЂ” "
        "РґРёР°РіРЅРѕСЃС‚РёРєР° РґР»СЏ PM Рё РЅРµ Р±Р»РѕРєРёСЂСѓСЋС‚ РІС‹РїСѓСЃРє РІРµСЃРѕРІ; Р±Р»РѕРєРёСЂСѓСЋС‰РёР№ РєРѕРЅС‚СѓСЂ РїРѕ РјР°РєСЃРёРјР°Р»СЊРЅРѕР№ РїСЂРѕСЃР°РґРєРµ "
        "Р·Р°РґР°С‘С‚СЃСЏ РѕС‚РґРµР»СЊРЅРѕ (mandate_check / IPS, РїРѕР»РЅР°СЏ РїРµСЂРµСЃРµРєР°СЋС‰Р°СЏСЃСЏ РёСЃС‚РѕСЂРёСЏ).",
    ]
    if warn:
        exec_para.append(f"РџСЂРµРґСѓРїСЂРµР¶РґРµРЅРёРµ РІ РѕС‚С‡С‘С‚Рµ: {warn}.")
    wl = (
        f"РҐСѓРґС€РёР№ СЃС†РµРЅР°СЂРЅС‹Р№ PnL РїРѕСЂС‚С„РµР»СЏ (worst_scenario_loss_pct): {_fmt_pct(worst)}; "
        f"РёРјРµРЅРѕРІР°РЅРЅС‹Р№ СЃС†РµРЅР°СЂРёР№: {fs or 'вЂ”'}; РїРѕР»Рµ failed_test: {ft or 'вЂ”'}."
        if worst is not None
        else f"РРјРµРЅРѕРІР°РЅРЅС‹Р№ СЃС†РµРЅР°СЂРёР№ (failed_scenario): {fs or 'вЂ”'}; failed_test: {ft or 'вЂ”'}."
    )
    exec_para.append(wl)
    lines.extend(exec_para)
    lines.append("")

    lines.append("Metric-by-Metric Interpretation")
    scen_rows = st.get("scenario_results") or []
    if scen_rows:
        lines.append(
            "РЎРёРЅС‚РµС‚РёС‡РµСЃРєРёРµ СЃС†РµРЅР°СЂРёРё (stress_report.scenario_results): С„Р°РєС‚РѕСЂРЅС‹Рµ С€РѕРєРё Рє РїРѕСЂС‚С„РµР»СЋ РІ С†РµР»РѕРј; "
            "pass = С‚РѕР»СЊРєРѕ РјР°РЅРґР°С‚РЅС‹Р№ РїРѕСЂРѕРі РїРѕ PnL РїРѕСЂС‚С„РµР»СЏ (loss_ok). Top1 / Top3 RC (РґРѕР»СЏ РґРёСЃРїРµСЂСЃРёРё) вЂ” "
            "С‡РёСЃР»РѕРІР°СЏ РґРёР°РіРЅРѕСЃС‚РёРєР° РєРѕРЅС†РµРЅС‚СЂР°С†РёРё, Р±РµР· РїРѕСЂРѕРіРѕРІРѕРіРѕ В«РѕРє/РЅРµ РѕРєВ» РІ stress_report. "
            "РџРѕ Р°РєС‚РёРІР°Рј Рё С„Р°РєС‚РѕСЂР°Рј СЃРј. pnl_by_asset_pct / pnl_by_factor_pct РІ JSON."
        )
        for row in scen_rows:
            sid = row.get("scenario_id", "?")
            pnl = row.get("portfolio_pnl_pct")
            top1a = row.get("top1_rc_asset")
            top1p = row.get("top1_rc_pct")
            top3s = row.get("top3_rc_sum_pct")
            lines.append(
                f"- {sid}: PnLв‰€{_fmt_pct(pnl)}, pass={row.get('pass')}, loss_ok={row.get('loss_ok')}; "
                f"Top1 RC (РґРѕР»СЏ РґРёСЃРїРµСЂСЃРёРё): {top1a} ({_fmt_pct(top1p, 2)}); СЃСѓРјРјР° Top3в‰€{_fmt_pct(top3s, 2) if top3s is not None else 'РЅ/Рґ'}."
            )
        sdiag = []
        for row in scen_rows:
            for c in row.get("diagnostic_codes") or []:
                if c not in sdiag:
                    sdiag.append(c)
        if sdiag:
            lines.append(f"РљРѕРґС‹ РїРѕ СЃС†РµРЅР°СЂРёСЏРј (loss Рё РїСЂРё РЅРµРѕР±С…РѕРґРёРјРѕСЃС‚Рё RC, СѓРЅРёРєР°Р»СЊРЅРѕ): {', '.join(str(x) for x in sdiag)}.")
    else:
        lines.append("РЎС†РµРЅР°СЂРЅС‹Рµ СЃС‚СЂРѕРєРё (scenario_results) РІ РѕС‚С‡С‘С‚Рµ РѕС‚СЃСѓС‚СЃС‚РІСѓСЋС‚.")

    fb5 = st.get("factor_betas_5y") or st.get("factor_betas") or {}
    fb10 = st.get("factor_betas_10y") or {}
    lines.append(
        f"Р¤Р°РєС‚РѕСЂРЅС‹Рµ Р±РµС‚С‹ РїРѕСЂС‚С„РµР»СЏ (РЅРµРґРµР»СЊРЅР°СЏ РѕС†РµРЅРєР°, СЃРј. СЃРїРµС†РёС„РёРєР°С†РёСЋ): 5Yв‰€{{{_fmt_beta_dict(fb5 if isinstance(fb5, dict) else {})}}}; "
        f"10Yв‰€{{{_fmt_beta_dict(fb10 if isinstance(fb10, dict) else {})}}}."
    )
    fr5 = st.get("factor_regression_5y")
    fr10 = st.get("factor_regression_10y")
    if isinstance(fr5, dict) and fr5:
        _append_factor_regression_section(lines, fr5, "5Y")
    elif st.get("factor_regression_5y_error"):
        lines.append(f"Р РµРіСЂРµСЃСЃРёСЏ С„Р°РєС‚РѕСЂРѕРІ 5Y: РЅРµ РїРѕСЃС‡РёС‚Р°РЅР° вЂ” {st.get('factor_regression_5y_error')}")
        lines.append("")
    if isinstance(fr10, dict) and fr10:
        _append_factor_regression_section(lines, fr10, "10Y")
    elif st.get("factor_regression_10y_error"):
        lines.append(f"Р РµРіСЂРµСЃСЃРёСЏ С„Р°РєС‚РѕСЂРѕРІ 10Y: РЅРµ РїРѕСЃС‡РёС‚Р°РЅР° вЂ” {st.get('factor_regression_10y_error')}")
        lines.append("")
    _append_rolling_betas_section(lines, st, output_dir_final)
    _append_factor_beta_stability_section(lines, st)
    _append_kalman_factor_betas_section(lines, st)
    _append_factor_beta_adjusted_overlay_section(lines, st)
    _append_factor_covariance_section(lines, st)
    _append_factor_variance_decomposition_section(lines, st)
    _append_portfolio_pca_section(lines, st)
    lines.append("")

    lines.append("Risk Structure")
    caps_line = []
    if mdd_lim is not None:
        caps_line.append(f"РџРѕСЂРѕРі РїСЂРѕСЃР°РґРєРё РґР»СЏ СЃС†РµРЅР°СЂРЅРѕРіРѕ loss-С‚РµСЃС‚Р° (max_dd_limit РІ JSON)={_fmt_pct(mdd_lim)}")
    lines.append("; ".join(caps_line) if caps_line else "РџРѕСЂРѕРі max_dd_limit РІ stress_report РЅРµ Р·Р°РґР°РЅ РёР»Рё РЅ/Рґ.")
    if scen_rows:
        triples = [(r.get("scenario_id"), r.get("top1_rc_asset"), r.get("top1_rc_pct")) for r in scen_rows]
        tops = ", ".join(
            f"{sid} {asset}={_fmt_pct(p, 1)}"
            for sid, asset, p in triples
            if p is not None and asset is not None
        )
        lines.append(
            f"РџРѕ СЃС†РµРЅР°СЂРёСЏРј Top1 RC РїРѕ СЃС†РµРЅР°СЂРёСЏРј (СЃРј. С‚Р°Р±Р»РёС†Сѓ РІС‹С€Рµ): {tops}."
        )
    hist = st.get("historical_results") or []
    if hist:
        lines.append("РСЃС‚РѕСЂРёС‡РµСЃРєРёРµ СЌРїРёР·РѕРґС‹ (historical_results):")
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
                f"- {ep}: pnl_real_episodeв‰€{_fmt_pct(pnl_real_ep)}, max_ddв‰€{_fmt_pct(mdd)}, pass={vp}, "
                f"vol_annualized_episodeв‰€{_fmt_float(vole, 4) if vole is not None else 'РЅ/Рґ'}, "
                f"diagnostic_code={dcode or 'вЂ”'}."
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
        lines.append("РСЃС‚РѕСЂРёС‡РµСЃРєРёРµ СЌРїРёР·РѕРґС‹ РІ JSON РѕС‚СЃСѓС‚СЃС‚РІСѓСЋС‚.")
    oos = st.get("factor_beta_shock_oos")
    if isinstance(oos, dict) and oos.get("episodes"):
        lines.append("OOS РѕР±СЉСЏСЃРЅРµРЅРёРµ СЌРїРёР·РѕРґРѕРІ С‡РµСЂРµР· ОІГ—shock (5Y/10Y/rolling-3Y pre):")
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
                f"РЎСЂРµРґРЅСЏСЏ |РѕС€РёР±РєР°| РїРѕ СЌРїРёР·РѕРґР°Рј: 5Y={_fmt_pct(summ.get('mean_abs_error_5y'))}, "
                f"10Y={_fmt_pct(summ.get('mean_abs_error_10y'))}, rolling-3Y={_fmt_pct(summ.get('mean_abs_error_roll3y_pre'))} "
                f"(n={summ.get('n_episodes_with_real_pnl', 'вЂ”')})."
            )
    lines.append("")

    lines.append("Strengths")
    str_lines: list[str] = []
    if scen_rows:
        if all(row.get("loss_ok") is True for row in scen_rows):
            str_lines.append("Р’Рѕ РІСЃРµС… СЃРёРЅС‚РµС‚РёС‡РµСЃРєРёС… СЃС†РµРЅР°СЂРёСЏС… loss_ok=true вЂ” РіР»СѓР±РёРЅР° РїРѕС‚РµСЂСЊ РІ СЂР°РјРєР°С… РїРѕСЂРѕРіРѕРІ loss-С‚РµСЃС‚Р°.")
        if any(row.get("pass") is True for row in scen_rows):
            str_lines.append("Р•СЃС‚СЊ СЃС†РµРЅР°СЂРёРё СЃ pass=true РїРѕ РјР°РЅРґР°С‚РЅРѕРјСѓ PnL.")
    for h in hist:
        if h.get("pass") is True:
            str_lines.append(f"РСЃС‚РѕСЂРёС‡РµСЃРєРёР№ СЌРїРёР·РѕРґ {h.get('episode')} РїРѕРјРµС‡РµРЅ pass=true.")
    if status in ("DIAG_PASS", "DIAG_PASS_WITH_WARNING", "PASS", "PASS_WITH_WARNING"):
        str_lines.append(f"РЎС‚Р°С‚СѓСЃ РЅР°Р±РѕСЂР° {status} вЂ” Р±РµР· СѓСЂРѕРІРЅСЏ DIAG_ATTENTION.")
    if not str_lines:
        str_lines.append("РЇРІРЅС‹С… В«Р·РµР»С‘РЅС‹С…В» С„Р»Р°РіРѕРІ РІ JSON РјР°Р»Рѕ РёР»Рё РѕРЅРё РѕС‚СЃСѓС‚СЃС‚РІСѓСЋС‚ вЂ” СЃРј. Weaknesses.")
    lines.extend(str_lines)
    lines.append("")

    lines.append("Weaknesses")
    wk: list[str] = []
    if status == "DIAG_ATTENTION":
        wk.append(
            f"DIAG_ATTENTION: Р·Р°С„РёРєСЃРёСЂРѕРІР°РЅС‹ РґРёР°РіРЅРѕСЃС‚РёС‡РµСЃРєРёРµ РєРѕРґС‹ ({dc_str}); РґР»СЏ PM РёРјРµРµС‚ СЃРјС‹СЃР» СЂР°Р·РѕР±СЂР°С‚СЊ scenario_results Рё historical_results."
        )
    if warn:
        wk.append(f"warning_code={warn} (СЃРј. stress_report; РіСЂР°РЅРёС‡РЅС‹Рµ РёСЃС‚РѕСЂРёС‡РµСЃРєРёРµ РґР°РЅРЅС‹Рµ РёР»Рё РїСЂРѕС‡РёРµ РїСЂРµРґСѓРїСЂРµР¶РґРµРЅРёСЏ).")
    if hist:
        for h in hist:
            if h.get("max_dd") is None and h.get("episode"):
                wk.append(f"Р­РїРёР·РѕРґ {h.get('episode')}: max_dd РЅ/Рґ вЂ” РёРЅС‚РµСЂРїСЂРµС‚Р°С†РёСЏ РѕРіСЂР°РЅРёС‡РµРЅР°.")
    if not wk:
        wk.append("РЎСѓС‰РµСЃС‚РІРµРЅРЅС‹С… РѕС‚РјРµС‚РѕРє РІ JSON РЅРµС‚ РёР»Рё РїСЂРѕС„РёР»СЊ РЅРµР№С‚СЂР°Р»РµРЅ РѕС‚РЅРѕСЃРёС‚РµР»СЊРЅРѕ РїРµСЂРµС‡РёСЃР»РµРЅРЅС‹С… РїСЂРѕРІРµСЂРѕРє.")
    lines.extend(wk)
    lines.append("")

    lines.append("Scenario Behavior")
    if scen_rows:
        for row in scen_rows:
            sid = row.get("scenario_id")
            pnl = row.get("portfolio_pnl_pct")
            lines.append(
                f"{sid}: PnLв‰€{_fmt_pct(pnl)}, pass={row.get('pass')} (РјР°РЅРґР°С‚РЅС‹Р№ loss); "
                f"РґРѕР»Рё RC вЂ” РІ Metric-by-Metric."
            )
    else:
        lines.append("РќРµС‚ scenario_results.")
    lines.append("")

    lines.append("Final Conclusion")
    lines.append(
        f"{label}: СЃС‚СЂРµСЃСЃ-РЅР°Р±РѕСЂ {status} ({primary}). "
        f"РЎРёРЅС‚РµС‚РёС‡РµСЃРєРёРµ РїРѕС‚РµСЂРё Рё RC-РґРёР°РіРЅРѕСЃС‚РёРєР° РѕС‚СЂР°Р¶Р°СЋС‚ С‚РµРєСѓС‰РёР№ СЃРѕСЃС‚Р°РІ Рё ОЈ РёР· РїСЂРѕРіРѕРЅР°; "
        f"СЂРµС€РµРЅРёСЏ РїРѕ РІС‹РїСѓСЃРєСѓ РІРµСЃРѕРІ СЃРІРµСЂСЏР№С‚Рµ СЃ mandate_check Рё run_result, Р° СЌС‚РѕС‚ С„Р°Р№Р» РёСЃРїРѕР»СЊР·СѓР№С‚Рµ РєР°Рє СЃС†РµРЅР°СЂРЅСѓСЋ СЃРїСЂР°РІРєСѓ РґР»СЏ PM."
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
        "summary.txt (РµСЃР»Рё РµСЃС‚СЊ)",
        "stress_report.json",
        "results_csv/portfolio_metrics_10y.csv",
        "results_csv/rc_vol_10y.csv",
        "report.txt",
    ]
    if output_dir_csv.resolve() != (output_dir_final / "results_csv").resolve():
        sources.append(f"CSV РєР°С‚Р°Р»РѕРі: {output_dir_csv.as_posix()}")

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
        or "вЂ”"
    )
    failed_scenario = st.get("failed_scenario")
    failed_test = st.get("failed_test")
    worst_loss = st.get("worst_scenario_loss_pct")

    rc_top = _load_rc_top5(output_dir_csv)
    rc_lines = ", ".join(f"{t} {_fmt_pct(r, 1)}" for t, r in rc_top) if rc_top else "РЅ/Рґ (РЅРµС‚ rc_vol_*.csv РёР»Рё РїСѓСЃС‚Рѕ)"

    client_gate = "PASS" if portfolio_valid else "FAIL"
    if portfolio_valid is None:
        client_gate = "РЅ/Рґ"

    ae = analysis_end or "вЂ”"
    scen_lines = _scenario_snippets(st)

    # Executive summary (3вЂ“5 sentences)
    exec_lines = [
        f"РџСЂРѕРіРѕРЅ РѕС‚РЅРѕСЃРёС‚СЃСЏ Рє {label}; РєРѕРЅРµС† РІС‹Р±РѕСЂРєРё (analysis_end): {ae}. "
        f"РќР° РґР»РёРЅРЅРѕРј РѕРєРЅРµ (10Y РІ РѕС‚С‡С‘С‚РЅРѕРј РєРѕРЅС‚СѓСЂРµ) РїРѕСЂС‚С„РµР»СЊ РїРѕРєР°Р·С‹РІР°РµС‚ CAGR РѕРєРѕР»Рѕ {_fmt_pct(cagr)}, "
        f"РіРѕРґРѕРІСѓСЋ РІРѕР»Р°С‚РёР»СЊРЅРѕСЃС‚СЊ РѕРєРѕР»Рѕ {_fmt_pct(vol)}, РјР°РєСЃРёРјР°Р»СЊРЅСѓСЋ РїСЂРѕСЃР°РґРєСѓ РѕРєРѕР»Рѕ {_fmt_pct(mdd)}.",
        f"Risk-adjusted: Sharpe в‰€ {_fmt_float(sharpe)}, Sortino в‰€ {_fmt_float(sortino)}; "
        f"С‡СѓРІСЃС‚РІРёС‚РµР»СЊРЅРѕСЃС‚СЊ Рє Р±Р°Р·РѕРІРѕРјСѓ Р±РµРЅС‡РјР°СЂРєСѓ: Beta_base в‰€ {_fmt_float(beta)}"
        + (f", РєРѕСЂСЂРµР»СЏС†РёСЏ СЃ Р±РµРЅС‡РјР°СЂРєРѕРј (Corr_base) в‰€ {_fmt_float(corr)}." if corr is not None and not (isinstance(corr, float) and math.isnan(corr)) else "."),
        f"РЎС‚СЂРµСЃСЃ-С‚РµСЃС‚: {stress_status}"
        + (f" ({fail_reason})" if fail_reason != "вЂ”" else "")
        + (f"; С…СѓРґС€РёР№ СЃС†РµРЅР°СЂРёР№ РїРѕ СѓР±С‹С‚РєСѓ: {failed_scenario} ({failed_test})" if failed_scenario else "")
        + (f"; worst_scenario_loss_pct в‰€ {_fmt_pct(worst_loss)}" if worst_loss is not None else "")
        + ".",
        f"РљР»РёРµРЅС‚СЃРєРёР№ MaxDD-gate (portfolio_valid): {client_gate}.",
    ]

    # Sections
    lines: list[str] = []
    lines.append("Source: summary.txt, stress_report.json, results_csv/portfolio_metrics_10y.csv, results_csv/rc_vol_10y.csv, report.txt")
    lines.append("")
    lines.append("Executive Summary")
    lines.extend(exec_lines)
    lines.append("")

    lines.append("Metric-by-Metric Interpretation")
    lines.append(
        f"CAGR ({_fmt_pct(cagr)}) РѕС‚СЂР°Р¶Р°РµС‚ СЃСЂРµРґРЅРµРіРѕРґРѕРІРѕР№ С‚РµРјРї СЂРѕСЃС‚Р° РїРѕ РјРµСЃСЏС‡РЅС‹Рј РїСЂРѕСЃС‚С‹Рј РґРѕС…РѕРґРЅРѕСЃС‚СЏРј РЅР° 10Y-РѕРєРЅРµ РІ С‚РµРєСѓС‰РµРј РїСЂРѕРіРѕРЅРµ. "
        f"Р’РѕР»Р°С‚РёР»СЊРЅРѕСЃС‚СЊ ({_fmt_pct(vol)}) вЂ” РіРѕРґРѕРІР°СЏ РёР· РјРµСЃСЏС‡РЅС‹С… РґРѕС…РѕРґРЅРѕСЃС‚РµР№; MaxDD ({_fmt_pct(mdd)}) вЂ” РїРѕ РјРµСЃСЏС‡РЅРѕР№ equity-РєСЂРёРІРѕР№. "
        f"Sharpe ({_fmt_float(sharpe)}) Рё Sortino ({_fmt_float(sortino)}) РёСЃРїРѕР»СЊР·СѓСЋС‚ СЃРїРµС†РёС„РёРєР°С†РёСЋ РїСЂРѕРµРєС‚Р° (Р·РЅР°РјРµРЅР°С‚РµР»СЊ вЂ” vol СЃС‹СЂРѕР№ РґРѕС…РѕРґРЅРѕСЃС‚Рё РґР»СЏ Sharpe). "
        f"Beta_base ({_fmt_float(beta)}) Рё Treynor ({_fmt_float(treynor)}) Р·Р°РІСЏР·Р°РЅС‹ РЅР° Р±Р°Р·РѕРІС‹Р№ Р±РµРЅС‡РјР°СЂРє; Corr_base РїСЂРё РЅР°Р»РёС‡РёРё РїРѕРєР°Р·С‹РІР°РµС‚ СЃРёРЅС…СЂРѕРЅРЅРѕСЃС‚СЊ СЃ Р±РµРЅС‡РјР°СЂРєРѕРј РЅР° С‚РѕРј Р¶Рµ РѕРєРЅРµ."
    )
    lines.append("")

    lines.append("Risk Structure")
    lines.append(
        f"РќР°РёР±РѕР»СЊС€РёРµ РґРѕР»Рё RC_vol (РІРєР»Р°Рґ РІ РґРёСЃРїРµСЂСЃРёСЋ РїРѕСЂС‚С„РµР»СЏ) РЅР° 10Y: {rc_lines}. "
        f"РЎС‚СЂРµСЃСЃ: status={stress_status}, fail_reason_code={fail_reason}."
        + (f" РџСЂРѕРІР°Р» РІ СЃС†РµРЅР°СЂРёРё В«{failed_scenario}В», С‚РµСЃС‚ В«{failed_test}В»." if failed_scenario else "")
    )
    lines.append("")

    lines.append("Strengths")
    _stress_clear = stress_status in ("PASS", "DIAG_PASS", "DIAG_PASS_WITH_WARNING", "PASS_WITH_WARNING")
    if _stress_clear and client_gate == "PASS":
        lines.append(
            "Р”РёР°РіРЅРѕСЃС‚РёС‡РµСЃРєРёР№ СЃС‚СЂРµСЃСЃ Р±РµР· РєСЂРёС‚РёС‡РЅС‹С… РѕС‚РјРµС‚РѕРє (РёР»Рё С‚РѕР»СЊРєРѕ РїСЂРµРґСѓРїСЂРµР¶РґРµРЅРёСЏ); РјР°РЅРґР°С‚РЅС‹Р№ MaxDD-gate PASS вЂ” "
            "СЃРѕС‡РµС‚Р°РЅРёРµ РёСЃС‚РѕСЂРёС‡РµСЃРєРѕР№ РїСЂРѕСЃР°РґРєРё Рё РєР»РёРµРЅС‚СЃРєРѕРіРѕ РїРѕСЂРѕРіР° РЅРµ РєРѕРЅС„Р»РёРєС‚СѓРµС‚ РІ СЌС‚РѕРј РїСЂРѕРіРѕРЅРµ."
        )
    elif client_gate == "PASS":
        lines.append(
            "РњР°РЅРґР°С‚РЅС‹Р№ MaxDD-gate PASS: СЂРµР°Р»РёР·РѕРІР°РЅРЅР°СЏ РїСЂРѕСЃР°РґРєР° РЅР° РїРѕР»РЅРѕР№ РїРµСЂРµСЃРµРєР°СЋС‰РµР№СЃСЏ РёСЃС‚РѕСЂРёРё РІ РґРѕРїСѓСЃРєРµ (СЃРј. run_metadata / mandate_check)."
        )
    else:
        lines.append("РўСЂРµР±СѓРµС‚СЃСЏ РІРЅРёРјР°РЅРёРµ Рє РєР»РёРµРЅС‚СЃРєРѕРјСѓ gate Рё/РёР»Рё СЃС‚СЂРµСЃСЃ-СЃС‚Р°С‚СѓСЃСѓ вЂ” СЃРј. РЅРёР¶Рµ Weaknesses.")
    if sharpe is not None and float(sharpe) >= 1.0:
        lines.append(f"Sharpe в‰Ґ 1.0 ({_fmt_float(sharpe)}) РЅР° РІС‹Р±СЂР°РЅРЅРѕРј РѕРєРЅРµ вЂ” РѕС‚РЅРѕСЃРёС‚РµР»СЊРЅРѕ СЃРёР»СЊРЅР°СЏ РєРѕРјРїРµРЅСЃР°С†РёСЏ Р·Р° СЂРёСЃРє РїРѕ РёСЃС‚РѕСЂРёРё.")
    lines.append("")

    lines.append("Weaknesses")
    if stress_status == "DIAG_ATTENTION":
        lines.append(
            f"РЎС‚СЂРµСЃСЃ-РґРёР°РіРЅРѕСЃС‚РёРєР°: {stress_status} вЂ” {fail_reason}. "
            f"(РќРµ Р±Р»РѕРєРёСЂСѓРµС‚ РІС‹РїСѓСЃРє; РёРјРµРЅРѕРІР°РЅРЅС‹Р№ СЃС†РµРЅР°СЂРёР№: {failed_scenario or 'вЂ”'}; С‚РµСЃС‚: {failed_test or 'вЂ”'}.)"
        )
    if client_gate == "FAIL":
        lines.append("РљР»РёРµРЅС‚СЃРєРёР№ MaxDD-gate FAIL вЂ” РёСЃС‚РѕСЂРёС‡РµСЃРєРёР№ MaxDD С…СѓР¶Рµ РјР°РЅРґР°С‚Р° (СЃРј. run_metadata / snapshot).")
    if not rc_top:
        lines.append("RC_vol top-5 РЅРµ РёР·РІР»РµС‡С‘РЅ РёР· CSV вЂ” РїСЂРѕРІРµСЂСЊС‚Рµ РЅР°Р»РёС‡РёРµ results_csv/rc_vol_10y.csv РїРѕСЃР»Рµ РїСЂРѕРіРѕРЅР°.")
    lines.append("")

    lines.append("Scenario Behavior")
    if scen_lines:
        lines.append("РљСЂР°С‚РєРѕ РїРѕ СЃС†РµРЅР°СЂРёСЏРј РёР· stress_report.json: " + "; ".join(scen_lines) + ".")
    else:
        lines.append("Р”РµС‚Р°Р»РёР·Р°С†РёСЏ СЃС†РµРЅР°СЂРёРµРІ РІ stress_report.json РѕС‚СЃСѓС‚СЃС‚РІСѓРµС‚ РёР»Рё РЅРµ РїСЂРѕС‡РёС‚Р°РЅР°.")
    if worst_loss is not None:
        lines.append(f"РҐСѓРґС€РёР№ СЃС†РµРЅР°СЂРЅС‹Р№ СѓР±С‹С‚РѕРє РїРѕСЂС‚С„РµР»СЏ (worst_scenario_loss_pct): в‰€ {_fmt_pct(worst_loss)}.")
    lines.append("")

    lines.append("Final Conclusion")
    lines.append(
        f"{label}: РїСЂРѕС„РёР»СЊ РґРѕС…РѕРґРЅРѕСЃС‚Рё/СЂРёСЃРєР° РЅР° 10Y Р·Р°РґР°С‘С‚СЃСЏ CAGRв‰€{_fmt_pct(cagr)} Рё volв‰€{_fmt_pct(vol)} РїСЂРё MaxDDв‰€{_fmt_pct(mdd)}. "
        f"РЎС‚СЂРµСЃСЃ {stress_status} ({fail_reason}); РєР»РёРµРЅС‚СЃРєРёР№ gate {client_gate}. "
        f"Р”Р»СЏ СЃСЂР°РІРЅРµРЅРёСЏ РІР°СЂРёР°РЅС‚РѕРІ РёСЃРїРѕР»СЊР·СѓР№С‚Рµ С‚Рµ Р¶Рµ С„Р°Р№Р»С‹ РІ СЃРѕСЃРµРґРЅРёС… РїР°РїРєР°С… (Equal-Weight / Risk Parity / Main portfolio) РїРѕСЃР»Рµ СЃРёРЅС…СЂРѕРЅРЅРѕРіРѕ РїСЂРѕРіРѕРЅР°."
    )

    text = "\n".join(lines) + "\n"
    out_path = output_dir_final / "commentary.txt"
    out_path.write_text(text, encoding="utf-8")
    return out_path
