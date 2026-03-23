"""
Auto-generate commentary.txt next to portfolio outputs (report/summary/stress/CSV).

Called after each full metrics run so commentary stays aligned with summary, stress_report,
and exported CSVs (per .cursor/rules/portfolio-commentary.mdc).
"""
from __future__ import annotations

import json
import math
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
    fail_reason = st.get("fail_reason_code") or st.get("skip_reason") or "—"
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
    if stress_status == "PASS" and client_gate == "PASS":
        lines.append("Стресс в статусе PASS; MaxDD-gate PASS — сочетание исторической просадки и клиентского порога не конфликтует в этом прогоне.")
    elif client_gate == "PASS":
        lines.append("MaxDD-gate PASS: реализованная просадка в допуске относительно target_max_drawdown_pct (см. run_metadata).")
    else:
        lines.append("Требуется внимание к клиентскому gate и/или стресс-статусу — см. ниже Weaknesses.")
    if sharpe is not None and float(sharpe) >= 1.0:
        lines.append(f"Sharpe ≥ 1.0 ({_fmt_float(sharpe)}) на выбранном окне — относительно сильная компенсация за риск по истории.")
    lines.append("")

    lines.append("Weaknesses")
    if stress_status != "PASS":
        lines.append(
            f"Стресс не пройден ({stress_status}): {fail_reason}. "
            f"Именованный сценарий сбоя: {failed_scenario or '—'}; тип проверки: {failed_test or '—'}."
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
