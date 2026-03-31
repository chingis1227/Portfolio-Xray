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


def _folder_portfolio_label(output_dir_final: Path) -> str:
    name = output_dir_final.name.strip().lower()
    if name == "main portfolio":
        return "основной портфель (Main portfolio)"
    if "equal" in name and "weight" in name:
        return "Equal-Weight baseline"
    if "risk" in name and "parity" in name:
        return "Risk-Parity baseline"
    return output_dir_final.name


def _fmt_pct(x: Any, digits: int = 2) -> str:
    if x is None:
        return "н/д"
    try:
        v = float(x)
    except (TypeError, ValueError):
        return "н/д"
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
        return "н/д"
    return f"{v * 100:.{digits}f}%"


def _fmt_float(x: Any, digits: int = 3) -> str:
    if x is None:
        return "н/д"
    try:
        v = float(x)
    except (TypeError, ValueError):
        return "н/д"
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
        return "н/д"
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
            lines.append(f"{sid}: PnL≈{_fmt_pct(pnl, 2)}, pass={ok}")
    return lines[:6]


def _fmt_beta_dict(d: dict[str, Any] | None) -> str:
    if not d:
        return "н/д"
    parts = []
    for k in sorted(d.keys()):
        parts.append(f"{k}={_fmt_float(d.get(k), 4)}")
    return ", ".join(parts) if parts else "н/д"


_BETA_ROW_ORDER = (
    "beta_eq",
    "beta_rr",
    "beta_inf",
    "beta_credit",
    "beta_usd",
    "beta_cmd",
)


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
        return "н/д"
    try:
        v = float(x)
    except (TypeError, ValueError):
        return "н/д"
    if v == 0.0 or (isinstance(v, float) and v < 1e-6):
        return "<1e-6"
    return _fmt_float(v, 6)


def _append_factor_multicollinearity_block(lines: list[str], mc: Any) -> None:
    """Append factor multicollinearity (same rows as OLS regressors); from factor_multicollinearity in stress_report."""
    if not isinstance(mc, dict) or not mc:
        return
    err = mc.get("error")
    if err:
        lines.append(f"Мультиколлинеарность факторов (диагностика): не посчитана — {err}")
        lines.append("")
        return
    sev = mc.get("severity", "—")
    mvif_str = "∞" if mc.get("max_vif_is_infinite") else _fmt_float(mc.get("max_vif"), 3)
    mvf = mc.get("max_vif_factor")
    fac_suffix = f" (фактор {mvf})" if mvf else ""
    lines.append(
        f"Мультиколлинеарность факторов (те же недели, что регрессия): оценка={sev}; "
        f"cond(R)={mc.get('cond_correlation_matrix', 'н/д')}; "
        f"max VIF={mvif_str}{fac_suffix}."
    )
    sp = mc.get("strongest_pair")
    if isinstance(sp, dict) and sp.get("factor_i"):
        lines.append(
            f"Сильнейшая попарная корреляция: {sp.get('factor_i')} vs {sp.get('factor_j')}, ρ={_fmt_float(sp.get('rho'), 4)}."
        )
    lines.append(f"Интерпретация: {mc.get('assessment_ru', '—')}")
    pairs = mc.get("pairwise_correlations") or []
    if isinstance(pairs, list) and pairs:
        lines.append("Все попарные ρ (|ρ| по убыванию):")
        for row in pairs:
            if not isinstance(row, dict):
                continue
            lines.append(
                f"  {row.get('factor_i')} — {row.get('factor_j')}: ρ={_fmt_float(row.get('rho'), 4)}"
            )
    vif_bf = mc.get("vif_by_factor") or {}
    if isinstance(vif_bf, dict) and vif_bf:
        lines.append("VIF по факторам:")
        for fname in sorted(vif_bf.keys()):
            v = vif_bf[fname]
            vs = "∞" if v is None else _fmt_float(v, 3)
            lines.append(f"  {fname}: {vs}")
    lines.append(f"Метод: {mc.get('method', '—')}; n_obs_f={mc.get('n_obs_factors', '—')}.")
    lines.append("")


def _append_serial_correlation_block(lines: list[str], ser: Any) -> None:
    """Durbin–Watson + Breusch–Godfrey on portfolio factor OLS residuals (same ordering as regression)."""
    if not isinstance(ser, dict) or not ser:
        return
    if ser.get("error"):
        lines.append(f"Автокорреляция остатков (DW / Breusch–Godfrey): не посчитана — {ser.get('error')}")
        lines.append("")
        return
    dw = ser.get("durbin_watson")
    lines.append(
        f"Автокорреляция остатков факторной OLS: Durbin–Watson={_fmt_float(dw, 4) if dw is not None else 'н/д'} "
        f"(≈2 — мало АК первого порядка; метод: {ser.get('method', '—')})."
    )
    bg = ser.get("breusch_godfrey") or []
    if isinstance(bg, list) and bg:
        lines.append("Breusch–Godfrey LM (H₀: нет АК до порядка p; LM ~ χ²(p)):")
        for row in bg:
            if not isinstance(row, dict):
                continue
            pv = row.get("p_value")
            lines.append(
                f"  lags={row.get('lags', '—')}: LM={_fmt_float(row.get('lm_statistic'), 4)}, "
                f"df={row.get('df_chi2', '—')}, p={_fmt_p_value(pv)}, "
                f"T_aux={row.get('n_aux_observations', '—')}, R²_aux={_fmt_float(row.get('aux_r_squared'), 4)}"
            )
    lines.append("")


def _append_factor_regression_block(lines: list[str], fr: Any, label: str) -> None:
    if not isinstance(fr, dict) or not fr:
        return
    betas = fr.get("betas") or {}
    t_d = fr.get("t") or {}
    p_d = fr.get("p") or {}
    lo = fr.get("ci_low") or {}
    hi = fr.get("ci_high") or {}
    lines.append(
        f"Портфельная факторная регрессия ({label}), недельные ряды, OLS: "
        f"n_obs={fr.get('n_obs', 'н/д')}, R²={_fmt_float(fr.get('r2'), 4)}, "
        f"adj R²={_fmt_float(fr.get('adj_r2'), 4)}, intercept={_fmt_float(fr.get('intercept'), 4)}, "
        f"se_type={fr.get('se_type', '—')}, alpha={fr.get('alpha', '—')} (CI уровень {fr.get('ci_level', '—')})."
    )
    lines.append("По факторам (β, t, p, 95% CI) — классический OLS (se_type=classic_ols):")
    for key in _BETA_ROW_ORDER:
        if key not in betas and key not in t_d:
            continue
        lines.append(
            f"- {key}: β={_fmt_float(betas.get(key), 4)}, t={_fmt_float(t_d.get(key), 3)}, "
            f"p={_fmt_p_value(p_d.get(key))}, CI=[{_fmt_float(lo.get(key), 4)}; {_fmt_float(hi.get(key), 4)}]"
        )
    # HAC / Newey–West inference (робастные SE)
    hac = fr.get("hac_inference") or {}
    if isinstance(hac, dict) and hac:
        hac_se = hac.get("se")
        hac_t = hac.get("t")
        hac_p = hac.get("p")
        hac_lo = hac.get("ci_low")
        hac_hi = hac.get("ci_high")
        lines.append(
            f"HAC/Newey–West (robust) inference: se_type={hac.get('se_type', 'hac_newey_west')}, "
            f"kernel={hac.get('kernel', 'bartlett')}, max_lags={hac.get('max_lags', '—')}."
        )
        if isinstance(hac_se, list) and isinstance(hac_t, list) and isinstance(hac_p, list):
            # Индексы: 0 — intercept, 1.. — факторы в том же порядке, что и factor_cols / beta_keys.
            lines.append("По факторам (HAC t, p, 95% CI):")
            # построим мапу по beta_keys из позиций
            for idx, key in enumerate(_BETA_ROW_ORDER, start=1):
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
    ser = fr.get("serial_correlation_diagnostics")
    if ser is not None:
        _append_serial_correlation_block(lines, ser)
    mc = fr.get("factor_multicollinearity")
    if mc is not None:
        _append_factor_multicollinearity_block(lines, mc)
    else:
        lines.append("")


def _append_rolling_betas_block(lines: list[str], st: dict[str, Any], output_dir_final: Path) -> None:
    rw = st.get("factor_betas_rolling_windows_weeks")
    if isinstance(rw, dict) and rw:
        lines.append(f"Скользящие окна (недель): {', '.join(f'{k}={v}' for k, v in sorted(rw.items()))}.")

    summ = st.get("factor_betas_rolling_summary")
    if isinstance(summ, dict) and summ:
        lines.append("Сводка скользящих β (по всей доступной истории в прогоне): mean, median, p10, p90:")
        for win in sorted(summ.keys(), key=lambda x: (len(str(x)), str(x))):
            by_b = summ.get(win) or {}
            if not isinstance(by_b, dict):
                continue
            lines.append(f"Окно {win}:")
            for bkey in _BETA_ROW_ORDER:
                row = by_b.get(bkey)
                if not isinstance(row, dict):
                    continue
                lines.append(
                    f"  {bkey}: n={row.get('n_points', '—')}, mean={_fmt_float(row.get('mean'), 4)}, "
                    f"median={_fmt_float(row.get('median'), 4)}, p10={_fmt_float(row.get('p10'), 4)}, "
                    f"p90={_fmt_float(row.get('p90'), 4)}"
                )
            lines.append("")
    elif st.get("factor_betas_rolling_error"):
        lines.append(f"Скользящие беты: ошибка расчёта — {st.get('factor_betas_rolling_error')}")

    art = st.get("factor_betas_rolling_artifacts")
    if isinstance(art, dict):
        png_map = art.get("plot_png_by_window") or {}
        if png_map:
            lines.append("Файлы графиков скользящих β (PNG, папка прогона): " + ", ".join(f"{k}→{v}" for k, v in sorted(png_map.items())))

    labels = ("3y", "5y", "10y")
    for lbl in labels:
        png = output_dir_final / f"rolling_factor_betas_{lbl}.png"
        if not png.is_file():
            continue
        rel = _relpath_for_pdf_md_image(png, output_dir_final)
        if rel:
            lines.append(f"![Rolling factor betas — {lbl}]({rel})")
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
    ae = analysis_end or "—"
    st = stress_report or {}

    lines: list[str] = [
        "Source: stress_report.json (текущий прогон)",
        "",
        "Executive Summary",
    ]

    if not st:
        lines.append(
            f"По {label} объект stress_report пуст или не передан: сценарная и факторная диагностика недоступна. "
            f"Конец выборки (analysis_end): {ae}."
        )
        lines.extend(
            [
                "",
                "Metric-by-Metric Interpretation",
                "Нет данных stress_report для разбора сценариев и бет.",
                "",
                "Risk Structure",
                "н/д",
                "",
                "Strengths",
                "н/д",
                "",
                "Weaknesses",
                "Отсутствует stress_report — нельзя оценить стресс-профиль по проекту.",
                "",
                "Scenario Behavior",
                "н/д",
                "",
                "Final Conclusion",
                f"После появления stress_report.json перезапустите отчёт (run_report / прогон варианта), чтобы обновить stress_commentary.txt.",
            ]
        )
        out_path = output_dir_final / "stress_commentary.txt"
        out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return out_path

    status = st.get("status", "N/A")
    primary = st.get("primary_diagnostic_code") or st.get("fail_reason_code") or st.get("skip_reason") or "—"
    warn = st.get("warning_code")
    dcodes = st.get("diagnostic_codes") or []
    dc_str = ", ".join(str(x) for x in dcodes) if dcodes else "—"
    worst = st.get("worst_scenario_loss_pct")
    fs = st.get("failed_scenario")
    ft = st.get("failed_test")
    cap1 = st.get("rc_asset_cap_used")
    cap3 = st.get("stress_top3_rc_sum_cap")
    mdd_lim = st.get("max_dd_limit")

    exec_para = [
        f"Прогон: {label}; конец выборки (analysis_end): {ae}. "
        f"Итоговый статус стресс-набора в stress_report: {status}. "
        f"Основной код (primary / fail_reason): {primary}. "
        f"Список diagnostic_codes: {dc_str}.",
        "По рабочему процессу проекта синтетические сценарии и исторические эпизоды в этом файле — "
        "диагностика для PM и не блокируют выпуск весов; блокирующий контур по максимальной просадке "
        "задаётся отдельно (mandate_check / IPS, полная пересекающаяся история).",
    ]
    if warn:
        exec_para.append(f"Предупреждение в отчёте: {warn}.")
    wl = (
        f"Худший сценарный PnL портфеля (worst_scenario_loss_pct): {_fmt_pct(worst)}; "
        f"именованный сценарий: {fs or '—'}; поле failed_test: {ft or '—'}."
        if worst is not None
        else f"Именованный сценарий (failed_scenario): {fs or '—'}; failed_test: {ft or '—'}."
    )
    exec_para.append(wl)
    lines.extend(exec_para)
    lines.append("")

    lines.append("Metric-by-Metric Interpretation")
    scen_rows = st.get("scenario_results") or []
    if scen_rows:
        lines.append(
            "Синтетические сценарии (stress_report.scenario_results): для каждого сценария ниже — "
            "PnL портфеля, итог pass, флаги loss_ok / role_ok / rc1_ok / rc3_ok и топ-1 вклад в риск (Top1 RC), "
            "как в JSON. pass=false при нарушении любого из тестов сценария."
        )
        for row in scen_rows:
            sid = row.get("scenario_id", "?")
            pnl = row.get("portfolio_pnl_pct")
            top1a = row.get("top1_rc_asset")
            top1p = row.get("top1_rc_pct")
            lines.append(
                f"- {sid}: PnL≈{_fmt_pct(pnl)}, pass={row.get('pass')}, "
                f"loss_ok={row.get('loss_ok')}, role_ok={row.get('role_ok')}, "
                f"rc1_ok={row.get('rc1_ok')}, rc3_ok={row.get('rc3_ok')}; "
                f"Top1 RC: {top1a} ({_fmt_pct(top1p, 2)})."
            )
        sdiag = []
        for row in scen_rows:
            for c in row.get("diagnostic_codes") or []:
                if c not in sdiag:
                    sdiag.append(c)
        if sdiag:
            lines.append(f"Коды по сценариям (уникально): {', '.join(str(x) for x in sdiag)}.")
    else:
        lines.append("Сценарные строки (scenario_results) в отчёте отсутствуют.")

    fb5 = st.get("factor_betas_5y") or st.get("factor_betas") or {}
    fb10 = st.get("factor_betas_10y") or {}
    lines.append(
        f"Факторные беты портфеля (недельная оценка, см. спецификацию): 5Y≈{{{_fmt_beta_dict(fb5 if isinstance(fb5, dict) else {})}}}; "
        f"10Y≈{{{_fmt_beta_dict(fb10 if isinstance(fb10, dict) else {})}}}."
    )
    fr5 = st.get("factor_regression_5y")
    fr10 = st.get("factor_regression_10y")
    if isinstance(fr5, dict) and fr5:
        _append_factor_regression_block(lines, fr5, "5Y")
    elif st.get("factor_regression_5y_error"):
        lines.append(f"Регрессия факторов 5Y: не посчитана — {st.get('factor_regression_5y_error')}")
        lines.append("")
    if isinstance(fr10, dict) and fr10:
        _append_factor_regression_block(lines, fr10, "10Y")
    elif st.get("factor_regression_10y_error"):
        lines.append(f"Регрессия факторов 10Y: не посчитана — {st.get('factor_regression_10y_error')}")
        lines.append("")
    _append_rolling_betas_block(lines, st, output_dir_final)
    lines.append("")

    lines.append("Risk Structure")
    caps_line = []
    if cap1 is not None:
        caps_line.append(f"rc_asset_cap_used={_fmt_float(cap1, 4)} (доля Top1 RC, контекст отчёта)")
    if cap3 is not None:
        caps_line.append(f"stress_top3_rc_sum_cap={_fmt_float(cap3, 4)}")
    if mdd_lim is not None:
        caps_line.append(f"max_dd_limit (эпизоды/контекст в отчёте)={_fmt_pct(mdd_lim)}")
    lines.append("; ".join(caps_line) if caps_line else "Лимиты в stress_report не заданы или н/д.")
    if scen_rows:
        triples = [(r.get("scenario_id"), r.get("top1_rc_asset"), r.get("top1_rc_pct")) for r in scen_rows]
        tops = ", ".join(
            f"{sid} {asset}={_fmt_pct(p, 1)}"
            for sid, asset, p in triples
            if p is not None and asset is not None
        )
        lines.append(
            f"По сценариям Top1 RC по сценариям (см. таблицу выше): {tops}."
        )
    hist = st.get("historical_results") or []
    if hist:
        lines.append("Исторические эпизоды (historical_results):")
        for h in hist:
            ep = h.get("episode", "?")
            mdd = h.get("max_dd")
            pnl_real_ep = h.get("pnl_real_episode")
            vp = h.get("pass")
            vole = h.get("vol_annualized_episode")
            dcode = h.get("diagnostic_code")
            lines.append(
                f"- {ep}: pnl_real_episode≈{_fmt_pct(pnl_real_ep)}, max_dd≈{_fmt_pct(mdd)}, pass={vp}, "
                f"vol_annualized_episode≈{_fmt_float(vole, 4) if vole is not None else 'н/д'}, "
                f"diagnostic_code={dcode or '—'}."
            )
    else:
        lines.append("Исторические эпизоды в JSON отсутствуют.")
    oos = st.get("factor_beta_shock_oos")
    if isinstance(oos, dict) and oos.get("episodes"):
        lines.append("OOS объяснение эпизодов через β×shock (5Y/10Y/rolling-3Y pre):")
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
                f"Средняя |ошибка| по эпизодам: 5Y={_fmt_pct(summ.get('mean_abs_error_5y'))}, "
                f"10Y={_fmt_pct(summ.get('mean_abs_error_10y'))}, rolling-3Y={_fmt_pct(summ.get('mean_abs_error_roll3y_pre'))} "
                f"(n={summ.get('n_episodes_with_real_pnl', '—')})."
            )
    lines.append("")

    lines.append("Strengths")
    str_lines: list[str] = []
    if scen_rows:
        if all(row.get("loss_ok") is True for row in scen_rows):
            str_lines.append("Во всех синтетических сценариях loss_ok=true — глубина потерь в рамках порогов loss-теста.")
        if all(row.get("rc3_ok") is True for row in scen_rows):
            str_lines.append("Во всех сценариях rc3_ok=true — суммарный Top3 RC не нарушает stress_top3_rc_sum_cap.")
        if any(row.get("pass") is True for row in scen_rows):
            str_lines.append("Есть сценарии с pass=true.")
    for h in hist:
        if h.get("pass") is True:
            str_lines.append(f"Исторический эпизод {h.get('episode')} помечен pass=true.")
    if status in ("DIAG_PASS", "DIAG_PASS_WITH_WARNING", "PASS", "PASS_WITH_WARNING"):
        str_lines.append(f"Статус набора {status} — без уровня DIAG_ATTENTION.")
    if not str_lines:
        str_lines.append("Явных «зелёных» флагов в JSON мало или они отсутствуют — см. Weaknesses.")
    lines.extend(str_lines)
    lines.append("")

    lines.append("Weaknesses")
    wk: list[str] = []
    if status == "DIAG_ATTENTION":
        wk.append(
            f"DIAG_ATTENTION: зафиксированы диагностические коды ({dc_str}); для PM имеет смысл разобрать scenario_results и historical_results."
        )
    if scen_rows and all(row.get("rc1_ok") is False for row in scen_rows):
        wk.append("Во всех сценариях rc1_ok=false — концентрация Top1 RC выше порога rc_asset_cap_used.")
    if warn:
        wk.append(f"warning_code={warn} (роль защитных блоков / прочее — см. stress_report).")
    if hist:
        for h in hist:
            if h.get("max_dd") is None and h.get("episode"):
                wk.append(f"Эпизод {h.get('episode')}: max_dd н/д — интерпретация ограничена.")
    if not wk:
        wk.append("Существенных отметок в JSON нет или профиль нейтрален относительно перечисленных проверок.")
    lines.extend(wk)
    lines.append("")

    lines.append("Scenario Behavior")
    if scen_rows:
        for row in scen_rows:
            sid = row.get("scenario_id")
            pnl = row.get("portfolio_pnl_pct")
            lines.append(
                f"{sid}: PnL≈{_fmt_pct(pnl)}, итог pass={row.get('pass')} — "
                f"см. loss/role/rc в Metric-by-Metric."
            )
    else:
        lines.append("Нет scenario_results.")
    lines.append("")

    lines.append("Final Conclusion")
    lines.append(
        f"{label}: стресс-набор {status} ({primary}). "
        f"Синтетические потери и RC-диагностика отражают текущий состав и Σ из прогона; "
        f"решения по выпуску весов сверяйте с mandate_check и run_result, а этот файл используйте как сценарную справку для PM."
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
        "summary.txt (если есть)",
        "stress_report.json",
        "results_csv/portfolio_metrics_10y.csv",
        "results_csv/rc_vol_10y.csv",
        "report.txt",
    ]
    if output_dir_csv.resolve() != (output_dir_final / "results_csv").resolve():
        sources.append(f"CSV каталог: {output_dir_csv.as_posix()}")

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
        or "—"
    )
    failed_scenario = st.get("failed_scenario")
    failed_test = st.get("failed_test")
    worst_loss = st.get("worst_scenario_loss_pct")

    rc_top = _load_rc_top5(output_dir_csv)
    rc_lines = ", ".join(f"{t} {_fmt_pct(r, 1)}" for t, r in rc_top) if rc_top else "н/д (нет rc_vol_*.csv или пусто)"

    client_gate = "PASS" if portfolio_valid else "FAIL"
    if portfolio_valid is None:
        client_gate = "н/д"

    ae = analysis_end or "—"
    scen_lines = _scenario_snippets(st)

    # Executive summary (3–5 sentences)
    exec_lines = [
        f"Прогон относится к {label}; конец выборки (analysis_end): {ae}. "
        f"На длинном окне (10Y в отчётном контуре) портфель показывает CAGR около {_fmt_pct(cagr)}, "
        f"годовую волатильность около {_fmt_pct(vol)}, максимальную просадку около {_fmt_pct(mdd)}.",
        f"Risk-adjusted: Sharpe ≈ {_fmt_float(sharpe)}, Sortino ≈ {_fmt_float(sortino)}; "
        f"чувствительность к базовому бенчмарку: Beta_base ≈ {_fmt_float(beta)}"
        + (f", корреляция с бенчмарком (Corr_base) ≈ {_fmt_float(corr)}." if corr is not None and not (isinstance(corr, float) and math.isnan(corr)) else "."),
        f"Стресс-тест: {stress_status}"
        + (f" ({fail_reason})" if fail_reason != "—" else "")
        + (f"; худший сценарий по убытку: {failed_scenario} ({failed_test})" if failed_scenario else "")
        + (f"; worst_scenario_loss_pct ≈ {_fmt_pct(worst_loss)}" if worst_loss is not None else "")
        + ".",
        f"Клиентский MaxDD-gate (portfolio_valid): {client_gate}.",
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
        f"CAGR ({_fmt_pct(cagr)}) отражает среднегодовой темп роста по месячным простым доходностям на 10Y-окне в текущем прогоне. "
        f"Волатильность ({_fmt_pct(vol)}) — годовая из месячных доходностей; MaxDD ({_fmt_pct(mdd)}) — по месячной equity-кривой. "
        f"Sharpe ({_fmt_float(sharpe)}) и Sortino ({_fmt_float(sortino)}) используют спецификацию проекта (знаменатель — vol сырой доходности для Sharpe). "
        f"Beta_base ({_fmt_float(beta)}) и Treynor ({_fmt_float(treynor)}) завязаны на базовый бенчмарк; Corr_base при наличии показывает синхронность с бенчмарком на том же окне."
    )
    lines.append("")

    lines.append("Risk Structure")
    lines.append(
        f"Наибольшие доли RC_vol (вклад в дисперсию портфеля) на 10Y: {rc_lines}. "
        f"Стресс: status={stress_status}, fail_reason_code={fail_reason}."
        + (f" Провал в сценарии «{failed_scenario}», тест «{failed_test}»." if failed_scenario else "")
    )
    lines.append("")

    lines.append("Strengths")
    _stress_clear = stress_status in ("PASS", "DIAG_PASS", "DIAG_PASS_WITH_WARNING", "PASS_WITH_WARNING")
    if _stress_clear and client_gate == "PASS":
        lines.append(
            "Диагностический стресс без критичных отметок (или только предупреждения); мандатный MaxDD-gate PASS — "
            "сочетание исторической просадки и клиентского порога не конфликтует в этом прогоне."
        )
    elif client_gate == "PASS":
        lines.append(
            "Мандатный MaxDD-gate PASS: реализованная просадка на полной пересекающейся истории в допуске (см. run_metadata / mandate_check)."
        )
    else:
        lines.append("Требуется внимание к клиентскому gate и/или стресс-статусу — см. ниже Weaknesses.")
    if sharpe is not None and float(sharpe) >= 1.0:
        lines.append(f"Sharpe ≥ 1.0 ({_fmt_float(sharpe)}) на выбранном окне — относительно сильная компенсация за риск по истории.")
    lines.append("")

    lines.append("Weaknesses")
    if stress_status == "DIAG_ATTENTION":
        lines.append(
            f"Стресс-диагностика: {stress_status} — {fail_reason}. "
            f"(Не блокирует выпуск; именованный сценарий: {failed_scenario or '—'}; тест: {failed_test or '—'}.)"
        )
    if client_gate == "FAIL":
        lines.append("Клиентский MaxDD-gate FAIL — исторический MaxDD хуже мандата (см. run_metadata / snapshot).")
    if not rc_top:
        lines.append("RC_vol top-5 не извлечён из CSV — проверьте наличие results_csv/rc_vol_10y.csv после прогона.")
    lines.append("")

    lines.append("Scenario Behavior")
    if scen_lines:
        lines.append("Кратко по сценариям из stress_report.json: " + "; ".join(scen_lines) + ".")
    else:
        lines.append("Детализация сценариев в stress_report.json отсутствует или не прочитана.")
    if worst_loss is not None:
        lines.append(f"Худший сценарный убыток портфеля (worst_scenario_loss_pct): ≈ {_fmt_pct(worst_loss)}.")
    lines.append("")

    lines.append("Final Conclusion")
    lines.append(
        f"{label}: профиль доходности/риска на 10Y задаётся CAGR≈{_fmt_pct(cagr)} и vol≈{_fmt_pct(vol)} при MaxDD≈{_fmt_pct(mdd)}. "
        f"Стресс {stress_status} ({fail_reason}); клиентский gate {client_gate}. "
        f"Для сравнения вариантов используйте те же файлы в соседних папках (Equal-Weight / Risk Parity / Main portfolio) после синхронного прогона."
    )

    text = "\n".join(lines) + "\n"
    out_path = output_dir_final / "commentary.txt"
    out_path.write_text(text, encoding="utf-8")
    return out_path
