"""
Rebuild investor-facing PDF reports from latest run outputs (Markdown → Pandoc → PDF).

Style target: institutional executive PDF — sans-serif, wide margins, navy/gray palette,
subtle top/footer rules, footer label + page number, generous whitespace. Layout is driven by
`pdf_latex/pandoc_preamble.tex` and per-build `pdf_latex/pandoc_doc_meta.tex` (see user style brief).

Client-facing PDF Markdown: короткие, связные формулировки на русском, **без** имён файлов,
внутренних кодов, «экспортного» тона; статусы и сценарии — бытовым языком.

Requires: pandoc and xelatex on PATH (or Pandoc under %LOCALAPPDATA%\\Pandoc on Windows).
"""
from __future__ import annotations

import json
import math
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from src.config import load_validated_config

# --- Paths (project root = parent of src/) ---
_ROOT = Path(__file__).resolve().parent.parent
_PDF_OUT = _ROOT / "pdf files"
_PDF_MD_SOURCES = _ROOT / "pdf_md_sources"
_OPTIONAL_ARCHIVE = _ROOT / "00_ВАЖНОЕ" / "11_pdf files"
_PDF_LATEX_DIR = _ROOT / "pdf_latex"
_PANDOC_PREAMBLE = _PDF_LATEX_DIR / "pandoc_preamble.tex"
_PANDOC_DOC_META = _PDF_LATEX_DIR / "pandoc_doc_meta.tex"

_PCT_METRICS = {
    "cagr",
    "vol_annual",
    "max_drawdown",
    "es_95",
    "es_99",
    "downside_deviation_annual",
}
_METRIC_LABELS: dict[str, str] = {
    "cagr": "CAGR",
    "vol_annual": "Vol (annual)",
    "max_drawdown": "Max drawdown",
    "sharpe": "Sharpe",
    "sortino": "Sortino",
    "beta_portfolio": "Beta (portfolio)",
    "treynor": "Treynor",
    "corr_base": "Corr (base)",
    "downside_deviation_annual": "Downside dev. (annual)",
    "skewness": "Skewness",
    "kurtosis": "Kurtosis",
    "es_95": "ES 95%",
    "es_99": "ES 99%",
    "eee_10pct": "EEE 10%",
    "ttr_months": "TTR (months)",
}
_METRIC_LABELS_RU: dict[str, str] = {
    "cagr": "Доходность (CAGR)",
    "vol_annual": "Волатильность (г/г)",
    "max_drawdown": "Макс. просадка",
    "sharpe": "Шарп",
    "sortino": "Сортино",
    "beta_portfolio": "Чувствительность к рынку",
    "treynor": "Показатель на рыночный риск",
    "corr_base": "Связь с широким рынком",
    "downside_deviation_annual": "Ниж. откл. (г/г)",
    "skewness": "Скв.",
    "kurtosis": "Эксцесс",
    "es_95": "ES 95%",
    "es_99": "ES 99%",
    "eee_10pct": "EEE 10%",
    "ttr_months": "TTR, мес.",
}

_COMMENTARY_SECTIONS = (
    "Executive Summary",
    "Metric-by-Metric Interpretation",
    "Risk Structure",
    "Strengths",
    "Weaknesses",
    "Scenario Behavior",
    "Final Conclusion",
)

# PDF: якоря в commentary.txt (EN) -> видимый заголовок (RU, клиентский)
_COMMENTARY_PDF_ALIASES: dict[str, str] = {
    "Metric-by-Metric Interpretation": "Что это значит для инвестора",
    "Risk Structure": "Структура риска",
    "Strengths": "Сильные стороны",
    "Weaknesses": "Слабые стороны и риски",
    "Scenario Behavior": "Сценарный анализ",
    "Final Conclusion": "Итог",
}

# Заголовок в шапке PDF (слева), по имени итогового файла
_PDF_HEADER_LEFT: dict[str, str] = {
    "Main portfolio_commentary": "Инвестиционный комментарий: основной портфель",
    "Main portfolio_stress_commentary": "Стресс-анализ: основной портфель",
    "Main portfolio_ew_rp_comparison": "Сравнение: equal-weight и risk parity",
    "Main portfolio_weights": "Состав портфеля: целевые веса",
    "Main portfolio_ips_summary": "Реализация политики: сводка (IPS)",
    "Main portfolio_ips_summary_commentary": "Комментарий к сводке IPS",
    "equal-weight_portfolio_commentary": "Комментарий: equal-weight",
    "equal-weight_portfolio_stress_commentary": "Стресс-анализ: equal-weight",
    "equal-weight_portfolio_weights": "Equal-weight: целевые веса",
    "risk_parity_portfolio_commentary": "Комментарий: risk parity",
    "risk_parity_portfolio_stress_commentary": "Стресс-анализ: risk parity",
    "risk_parity_portfolio_weights": "Risk parity: целевые веса",
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M %Z")


def _russian_subtitle_line(
    window_label: str | None, analysis_end: str | None, *, default_window_ru: str = "10-летнем"
) -> str:
    """Вторая строка титульного блока, как в эталоне: «итоги на N-летнем окне, по состоянию на …»."""
    wl = (window_label or "").strip().upper().replace(" ", "")
    if "10" in wl or "10Y" in wl or (window_label and "10" in str(window_label)):
        win = "10-летнем"
    elif "5" in wl or (window_label and "5" in str(window_label)):
        win = "5-летнем"
    elif "3" in wl or (window_label and "3" in str(window_label)):
        win = "3-летнем"
    else:
        win = default_window_ru
    ae = (analysis_end or datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d")).strip()
    return f"Итоги анализа на {win} окне, по состоянию на {ae}"


def _line_dropped_for_client_pdf(line: str) -> bool:
    t = line.strip()
    if not t:
        return False
    low = t.lower()
    if re.match(r"^source\s*:", low) or t.startswith("Источник:") and re.search(r"[/\\]", t):
        return True
    if any(
        x in low
        for x in (
            "stress_report",
            "results_csv",
            "summary.txt",
            "run_result.json",
            "commentary.txt",
            "report.txt",
            "analysis_end",
            "policy run",
            "fail_reason_code",
            "portfolio_valid",
        )
    ):
        return True
    if re.search(
        r"(?:[A-Za-z]:[\\/]|[/\\](?:Users|home|Użytkownicy)[/\\]|\\\\[^/\\]+\\).+\.(json|csv|txt|yml|md|parquet)\b",
        t,
        re.I,
    ):
        return True
    if "`" in t and any(ext in t for ext in (".json", ".csv", ".txt", "yml", "parquet", "md")):
        return True
    return False


def _executive_ru_sanitize(text: str) -> str:
    """
    Клиентский исполненческий тон: убрать внутренние коды, пути, «системные» обозначения.
    Не сохраняет дословно исход — только безопасный для PDF смысл.
    """
    if not text:
        return text
    out_lines: list[str] = []
    for line in text.splitlines():
        if _line_dropped_for_client_pdf(line):
            continue
        out_lines.append(line)
    out = "\n".join(out_lines)

    repl_text = [
        (r"equity\s*shock", "сильный обвал на рынке акций"),
        (r"credit\s*shock", "стресс на рынке кредита"),
        (r"EQUITY_SHOCK", "сильный обвал на рынке акций"),
        (r"CREDIT_SHOCK", "стресс на рынке кредита"),
        (r"DIAG_[A-Z0-9_]+", " "),
        (r"ROLE_[A-Z0-9_]+", " "),
        (r"FAIL_[A-Z0-9_]+", " "),
        (r"\banalysis_end\b", "дата среза"),
        (r"\bportfolio_valid\b", " "),
        (r"\bfail_reason_code\b", " "),
        (r"beta_base", "чувствительность к широкому рынку"),
        (r"corr_base", "связь с рынком в целом"),
        (r"Treynor", "оценка доходности с учётом чувствительности к рынку"),
        (r"treynor", "оценка доходности с учётом чувствительности к рынку"),
        (r"\bDIAG\b", " "),
        (r"policy\s*run", "расчёт по политике"),
    ]
    for pat, to in repl_text:
        out = re.sub(pat, to, out, flags=re.IGNORECASE)
    out = re.sub(r"\bPASS\b", "в норме по проверке", out, flags=re.IGNORECASE)
    out = re.sub(r"\bPreamble\b", "", out, flags=re.IGNORECASE)
    out = re.sub(r"[ \t]{2,}", " ", out)
    out = re.sub(r"\n{3,}", "\n\n", out)
    return out.strip()


def _humanize_stress_status(val: Any) -> str:
    """Короткие формулировки для лицевой стороны — без внутренних кодов движка."""
    if val is None:
        return "—"
    s = str(val).strip()
    if not s or s == "—":
        return "—"
    u = s.upper().replace(" ", "_")
    if u in ("PASS", "OK", "SUCCESS", "PASSED", "SUCCEEDED", "PORTFOLIO_VALID_PASS"):
        return "В рамках согласованного профиля риска"
    if u.startswith("FAIL") or "FAIL" in u:
        return "Выходит за согласованные лимиты — нужен пересмотр состава"
    if "DIAG_ATTENTION" in u or ("ATTENTION" in u and "STRESS" in u):
        return "Один рисковый аспект требует внимания"
    if u.startswith("DIAG_") or u.startswith("ROLE_") or u.startswith("EQUITY_") or u.startswith("CREDIT_"):
        return "—"
    return _executive_ru_sanitize(s)


def _looks_like_code_token(s: str) -> bool:
    t = s.strip()
    if not t or t in ("—", "OK"):
        return False
    if re.match(r"^DIAG[_A-Z0-9]+$", t, re.I):
        return True
    if re.match(r"^FAIL[_A-Z0-9]*$", t, re.I) and t.upper() not in ("FAIL",):
        return True
    if "_" in t and len(t) < 48 and t.upper() == t:
        return True
    return False


def _humanize_stress_detail(val: Any) -> str:
    """Сырые причины-коды не печатаем; осмысленный текст — через санитайзер."""
    if val is None:
        return "—"
    s = str(val).strip()
    if not s or s == "—":
        return "—"
    if _looks_like_code_token(s):
        return "—"
    s2 = _executive_ru_sanitize(s)
    if not s2 or s2 in ("—",) or _looks_like_code_token(s2):
        return "—"
    if len(s2) > 90:
        return s2[:87].rstrip() + "…"
    return s2


def _soft_sanitize_narrative_for_pdf(text: str) -> str:
    """Текст для PDF: без внутренних ярлыков и сухой техники."""
    return _executive_ru_sanitize(text)


def _escape_latex_command_arg(s: str) -> str:
    """Conservative TeX-escape for one-line use inside \\def\\foo{...}."""
    return (
        s.replace("\\", r"\textbackslash{}")
        .replace("#", r"\#")
        .replace("%", r"\%")
        .replace("$", r"\$")
        .replace("&", r"\&")
        .replace("_", r"\_")
        .replace("{", r"\{")
        .replace("}", r"\}")
        .replace("~", r"\textasciitilde{}")
        .replace("^", r"\textasciicircum{}")
    )


def _pdf_descriptor_for_output(pdf_out: Path) -> str:
    """Humanize PDF stem for footer: underscores → spaces, keep readable."""
    t = pdf_out.stem.replace("_", " ")
    t = t.replace("  ", " ").strip()
    return t if t else "Report"


def _default_meta_footer_ru() -> str:
    ts = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M")
    return f"Подготовлено: {ts} | Формат: краткая справка | Язык: русский"


def _header_left_for_pdf(pdf_out: Path) -> str:
    return _PDF_HEADER_LEFT.get(pdf_out.stem, "Портфельный отчёт")


def _write_pandoc_doc_meta_tex(pdf_out: Path) -> None:
    _PDF_LATEX_DIR.mkdir(parents=True, exist_ok=True)
    descriptor = _pdf_descriptor_for_output(pdf_out)
    h = _header_left_for_pdf(pdf_out)
    ftr = _default_meta_footer_ru()
    body = (
        r"\def\PDFDocDescriptor{"
        + _escape_latex_command_arg(descriptor)
        + "}"
        + r"\def\PDFHeaderLeft{"
        + _escape_latex_command_arg(h)
        + "}"
        + r"\def\PDFMetaFooter{"
        + _escape_latex_command_arg(ftr)
        + "}"
        + "\n"
    )
    _PANDOC_DOC_META.write_text(
        "% Auto-generated by src/pdf_reports.py\n" + body,
        encoding="utf-8",
    )


def _find_pandoc() -> str | None:
    exe = shutil.which("pandoc")
    if exe:
        return exe
    if sys.platform == "win32":
        local = os.environ.get("LOCALAPPDATA", "")
        if local:
            p = Path(local) / "Pandoc" / "pandoc.exe"
            if p.is_file():
                return str(p)
    return None


def _find_xelatex() -> bool:
    return shutil.which("xelatex") is not None


def _pandoc_resource_paths(md_out: Path) -> str:
    """
    Resolve search paths for Markdown-linked images.
    We include md directory plus common output folders where plots are generated.
    """
    paths = [
        md_out.parent.resolve(),
        _ROOT.resolve(),
        (_ROOT / "Main portfolio").resolve(),
        (_ROOT / "equal-weight portfolio").resolve(),
        (_ROOT / "risk parity portfolio").resolve(),
    ]
    sep = ";" if sys.platform == "win32" else ":"
    return sep.join(str(p) for p in paths)


def _build_pandoc_pdf_cmd(*, pandoc: str, md_out: Path, pdf_out: Path) -> list[str]:
    if sys.platform == "win32":
        mainfont = "Segoe UI"
    else:
        mainfont = "TeX Gyre Heros"
    _write_pandoc_doc_meta_tex(pdf_out)
    cmd = [
        pandoc,
        str(md_out),
        "-o",
        str(pdf_out),
        "--standalone",
        "--from",
        "markdown+pipe_tables+table_captions+raw_attribute",
        "--pdf-engine=xelatex",
        "-V",
        f"mainfont={mainfont}",
        "-V",
        f"sansfont={mainfont}",
        "-V",
        f"monofont={'Consolas' if sys.platform == 'win32' else 'TeX Gyre Cursor'}",
        "-V",
        "fontsize=10pt",
        "-V",
        "linestretch=1.02",
        "--resource-path",
        _pandoc_resource_paths(md_out),
    ]
    if _PANDOC_DOC_META.is_file():
        cmd.extend(["-H", str(_PANDOC_DOC_META)])
    if _PANDOC_PREAMBLE.is_file():
        cmd.extend(["-H", str(_PANDOC_PREAMBLE)])
    return cmd


def _escape_md_cell(s: str) -> str:
    return s.replace("|", "\\|")


def _fmt_scalar(v: Any, *, pct: bool = False) -> str:
    if v is None:
        return "—"
    try:
        if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
            return "—"
        f = float(v)
        if pct:
            return f"{f * 100:.2f}%"
        if abs(f) < 1.0 and abs(f) > 0 and abs(f) != 0.0:
            return f"{f:.3f}"
        return f"{f:.3f}".rstrip("0").rstrip(".")
    except (TypeError, ValueError):
        return str(v)


def _read_snapshot_10y(folder: Path) -> dict[str, Any] | None:
    p = folder / "snapshot_10y.json"
    if not p.is_file():
        return None
    try:
        o = json.loads(p.read_text(encoding="utf-8"))
        return o if isinstance(o, dict) else None
    except Exception:
        return None


def _fmt_kpi_val_latex(m: dict[str, Any], key: str, *, pct: bool) -> str:
    v = m.get(key)
    if v is None or (isinstance(v, float) and (math.isnan(v) or math.isinf(v))):
        return "—"
    try:
        f = float(v)
        if pct:
            t = f"{f * 100:.2f}".replace(".", ",")
            return t + r"\%"
        return f"{f:.3f}".replace(".", ",") if f >= 0 else f"{f:.3f}".replace(".", ",")
    except (TypeError, ValueError):
        return "—"


def _kpi_block_latex_ru(m: dict[str, Any]) -> str:
    """2×3 сетка KPI (LaTeX), как на эталоне."""
    if not m:
        return ""
    mk = m
    pairs = [
        (_fmt_kpi_val_latex(mk, "cagr", pct=True), "Доходность (CAGR)"),
        (_fmt_kpi_val_latex(mk, "vol_annual", pct=True), "Волатильность"),
        (_fmt_kpi_val_latex(mk, "max_drawdown", pct=True), "Макс. просадка"),
        (_fmt_kpi_val_latex(mk, "sharpe", pct=False), "Коэф. Шарпа"),
        (_fmt_kpi_val_latex(mk, "sortino", pct=False), "Коэф. Сортино"),
        (_fmt_kpi_val_latex(mk, "beta_portfolio", pct=False), "Чувствительность к рынку"),
    ]
    a1, a2, a3 = [r"\KPIone{" + x[0] + "}{" + _escape_latex_arg_for_kpi(x[1]) + "}" for x in pairs[:3]]
    b1, b2, b3 = [r"\KPIone{" + x[0] + "}{" + _escape_latex_arg_for_kpi(x[1]) + "}" for x in pairs[3:6]]
    inner = a1 + " & " + a2 + " & " + a3 + r"\\[0.55em] " + b1 + " & " + b2 + " & " + b3
    return (
        "```{=latex}\n"
        r"\begin{center}\begin{tabular}{@{}>{\centering\arraybackslash}m{0.30\textwidth}@{\hspace{0.45em}}>{\centering\arraybackslash}m{0.30\textwidth}@{\hspace{0.45em}}>{\centering\arraybackslash}m{0.30\textwidth}@{}} "
        + inner
        + r"\end{tabular}\end{center}"
        + "\n```\n"
    )


def _escape_latex_arg_for_kpi(s: str) -> str:
    return s.replace("\\", r"\textbackslash{}").replace("%", r"\%").replace("&", r"\&")


def _yaml_front_matter(
    title: str,
    subtitle: str | None = None,
    *,
    analysis_end: str | None = None,
    window_label: str | None = None,
) -> str:
    """H1: инсайт-заголовок; `date` в YAML — вторая строка, как в эталоне (подзаголовок-описание)."""
    full_title = title if not subtitle else f"{title} — {subtitle}"
    date_line = _russian_subtitle_line(window_label, analysis_end)
    lines = [
        "---",
        f'title: "{full_title.replace(chr(34), chr(39))}"',
        f'date: "{date_line.replace(chr(34), chr(39))}"',
        "documentclass: article",
        "geometry: \"left=18mm, right=18mm, top=24mm, bottom=20mm, head=20pt, foot=20pt, footskip=40pt\"",
        "fontsize: 10pt",
        "---",
        "",
    ]
    return "\n".join(lines)


def _detect_analysis_end(folder: Path) -> str | None:
    for snap in ("snapshot_10y.json", "snapshot_5y.json", "snapshot_3y.json", "snapshot.json"):
        p = folder / snap
        if not p.is_file():
            continue
        try:
            obj = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        value = obj.get("analysis_end")
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


_KPI_EW_RP_KEYS: tuple[str, ...] = (
    "cagr",
    "vol_annual",
    "max_drawdown",
    "sharpe",
    "sortino",
    "beta_portfolio",
)


def _ew_rp_executive_takeaway(comp: dict[str, Any]) -> str:
    p = comp.get("period") or {}
    ae = p.get("analysis_end") or "—"
    wl = (p.get("window_label") or "—")
    em = (comp.get("equal_weight") or {}).get("metrics") or {}
    rm = (comp.get("risk_parity") or {}).get("metrics") or {}
    dm = (comp.get("delta") or {}).get("metrics") or {}
    s_ew = _humanize_stress_status((comp.get("equal_weight") or {}).get("stress_status"))
    s_rp = _humanize_stress_status((comp.get("risk_parity") or {}).get("stress_status"))
    return (
        f"На горизонте **{wl}** (оценка **{ae}**) равные веса обычно сильнее ориентированы на **ожидаемую доходность**, "
        f"а **risk parity** сглаживает **вклад инструментов в общий риск**. "
        f"По доходности равные веса **опережают** вариант с выравниванием риска на **{_fmt_scalar(dm.get('cagr'), pct=True)}**; "
        f"**волатильность** — **{_fmt_scalar(em.get('vol_annual'), pct=True)}** у равных весов и **{_fmt_scalar(rm.get('vol_annual'), pct=True)}** у risk parity. "
        f"По **стресс-проверке** равные веса: **{s_ew}**; risk parity: **{s_rp}**.\n"
    )


def build_ew_rp_markdown(comp: dict[str, Any]) -> str:
    ew = comp.get("equal_weight") or {}
    rp = comp.get("risk_parity") or {}
    eq_m = {**(ew.get("metrics") or {})}
    rp_m = {**(rp.get("metrics") or {})}
    delta_m = (comp.get("delta") or {}).get("metrics") or {}
    p = comp.get("period") or {}
    as_of = p.get("analysis_end") if isinstance(p.get("analysis_end"), str) else None
    wlab = p.get("window_label") if isinstance(p.get("window_label"), str) else None

    parts: list[str] = []
    parts.append(
        _yaml_front_matter(
            "Сравнение: equal-weight и risk parity",
            None,
            analysis_end=as_of,
            window_label=wlab,
        )
    )
    parts.append("## Ключевой вывод\n\n")
    parts.append(_ew_rp_executive_takeaway(comp) + "\n\n")

    parts.append("## Ключевые показатели\n\n")
    parts.append(
        "*Разница (последний столбец) — **насколько больше у равных весов**, чем у risk parity, в тех же единицах, что и метрика.*\n\n"
    )
    parts.append("|  | Равные веса (EW) | Risk parity | Разница (EW − RP) |\n")
    parts.append("| --- | ---: | ---: | ---: |\n")
    for k in _KPI_EW_RP_KEYS:
        pct = k in _PCT_METRICS
        label = _METRIC_LABELS_RU.get(k, k)
        parts.append(
            f"| **{_escape_md_cell(label)}** | {_escape_md_cell(_fmt_scalar(eq_m.get(k), pct=pct))} | "
            f"{_escape_md_cell(_fmt_scalar(rp_m.get(k), pct=pct))} | "
            f"{_escape_md_cell(_fmt_scalar(delta_m.get(k), pct=pct))} |\n"
        )

    top = comp.get("rc_vol_top5_asset") or {}
    eq5 = top.get("equal_weight") or {}
    rp5 = top.get("risk_parity") or {}
    d5 = top.get("delta") or {}
    top_tickers = sorted(set(eq5.keys()) | set(rp5.keys()))
    if top_tickers:
        parts.append("\n## Кто сильнее всего влияет на риск (топ позиций)\n\n")
        parts.append("\n| Инструмент | Равные веса | Risk parity | Разница (EW − RP) |\n| --- | ---: | ---: | ---: |\n")
        for t in top_tickers:
            parts.append(
                f"| **{t}** | {_escape_md_cell(_fmt_scalar(eq5.get(t), pct=True))} | "
                f"{_escape_md_cell(_fmt_scalar(rp5.get(t), pct=True))} | "
                f"{_escape_md_cell(_fmt_scalar(d5.get(t), pct=True))} |\n"
            )

    se = _humanize_stress_status(ew.get("stress_status"))
    sr = _humanize_stress_status(rp.get("stress_status"))
    re_ew = _humanize_stress_detail(ew.get("stress_fail_reason"))
    re_rp = _humanize_stress_detail(rp.get("stress_fail_reason"))
    parts.append("\n## Сценарный анализ (стресс, сравнение)\n\n")
    parts.append(
        f"- **Равные веса (equal-weight):** {se}.\n"
        f"- **Risk parity:** {sr}.\n"
    )
    de, dr = re_ew.strip(), re_rp.strip()
    if (de and de not in ("—",)) or (dr and dr not in ("—",)):
        if de and dr and de not in ("—",) and dr not in ("—",):
            parts.append(
                f"\n*Пояснения к сценарной проверке: **равные веса** — {de}; **risk parity** — {dr}.*\n"
            )
        elif de and de not in ("—",):
            parts.append(f"\n*Пояснение: **равные веса** — {de}.*\n")
        elif dr and dr not in ("—",):
            parts.append(f"\n*Пояснение: **risk parity** — {dr}.*\n")
    parts.append(
        "\n*Оба варианта посчитаны на **одном** наборе инструментов и **одной** истории; отличается только способ взвешивания.*\n"
    )
    return "".join(parts)


def _parse_commentary_sections(text: str) -> list[tuple[str, str]]:
    lines = text.replace("\r\n", "\n").strip().split("\n")
    current_title = "Preamble"
    buf: list[str] = []
    sections: list[tuple[str, str]] = []

    def flush() -> None:
        nonlocal buf
        body = "\n".join(buf).strip()
        if body:
            sections.append((current_title, body))
        buf = []

    for line in lines:
        stripped = line.strip()
        if stripped in _COMMENTARY_SECTIONS:
            flush()
            current_title = stripped
            continue
        buf.append(line)
    flush()
    return sections


def build_commentary_report_md(
    *,
    report_title: str,
    commentary_text: str,
    variant_label: str | None = None,
    analysis_end: str | None = None,
    snapshot_folder: Path | None = None,
) -> str:
    del variant_label
    parts: list[str] = []
    snap = _read_snapshot_10y(snapshot_folder) if snapshot_folder else None
    wlab: str | None = None
    ae = analysis_end
    if snap:
        wlab = str(snap.get("window_label") or "") or None
        if not ae and snap.get("analysis_end"):
            ae = str(snap.get("analysis_end") or "").strip() or None
    parts.append(
        _yaml_front_matter(
            report_title,
            None,
            analysis_end=ae,
            window_label=wlab,
        )
    )
    sections = _parse_commentary_sections(commentary_text)
    smap: dict[str, str] = {}
    for title, body in sections:
        b = _soft_sanitize_narrative_for_pdf(body)
        if not b.strip() and title != "Preamble":
            continue
        if title in smap:
            smap[title] = smap[title].rstrip() + "\n\n" + b
        else:
            smap[title] = b

    pre = (smap.get("Preamble") or "").strip()
    ex = (smap.get("Executive Summary") or "").strip()
    if pre and ex:
        exec_body = _soft_sanitize_narrative_for_pdf(f"{pre}\n\n{ex}")
    else:
        exec_body = _soft_sanitize_narrative_for_pdf(ex or pre)

    parts.append("\n## Ключевой вывод\n\n")
    if exec_body.strip():
        for para in [p.strip() for p in exec_body.split("\n\n") if p.strip()]:
            if para.startswith("- "):
                parts.append(f"{para}\n")
            else:
                parts.append(f"{para}\n\n")
    else:
        parts.append(
            "*Самое главное ещё не вынесено: в начало рабочего комментария к прогону добавьте 3–5 предложений с **итогом** (первый блок по внутреннему шаблону комментария).*\n"
        )

    mets = (snap or {}).get("metrics") or {}
    if isinstance(mets, dict) and mets:
        kpi = _kpi_block_latex_ru(mets)
        if kpi:
            parts.append("\n## Ключевые показатели\n\n")
            parts.append(kpi + "\n")

    wimi_chunks: list[str] = []
    mmm = (smap.get("Metric-by-Metric Interpretation") or "").strip()
    if mmm:
        wimi_chunks.append(mmm)
    st = (smap.get("Strengths") or "").strip()
    if st:
        wimi_chunks.append("**Сильные стороны.**\n\n" + st)
    wk = (smap.get("Weaknesses") or "").strip()
    if wk:
        wimi_chunks.append("**Риски и ограничения.**\n\n" + wk)
    if wimi_chunks:
        parts.append("\n## Что это значит для инвестора\n\n")
        parts.append("\n\n".join(wimi_chunks) + "\n")

    for key in ("Risk Structure", "Scenario Behavior", "Final Conclusion"):
        body = (smap.get(key) or "").strip()
        if not body:
            continue
        head = _COMMENTARY_PDF_ALIASES.get(key, key)
        parts.append(f"\n## {head}\n\n")
        is_listy = bool(re.search(r"(?m)^\s*[-*]\s", body))
        if is_listy:
            parts.append(body if body.endswith("\n") else body + "\n")
        else:
            for para in [p.strip() for p in body.split("\n\n") if p.strip()]:
                parts.append(f"{para}\n\n")

    return "".join(parts)


def build_weights_report_md(
    *,
    title: str,
    weights: dict[str, float],
    variant_label: str | None = None,
    analysis_end: str | None = None,
    snapshot_folder: Path | None = None,
) -> str:
    del variant_label
    parts: list[str] = []
    snap = _read_snapshot_10y(snapshot_folder) if snapshot_folder else None
    wlab = str(snap.get("window_label") or "") if snap else None
    ae = analysis_end
    if snap and not ae and snap.get("analysis_end"):
        ae = str(snap.get("analysis_end") or "").strip() or None
    parts.append(
        _yaml_front_matter(
            title,
            None,
            analysis_end=ae,
            window_label=wlab,
        )
    )
    items = sorted(weights.items(), key=lambda kv: (-kv[1], kv[0]))
    top = items[:5]
    parts.append("\n## Ключевой вывод\n\n")
    if top:
        tlist = ", ".join(f"**{t}** — {_fmt_scalar(w, pct=True)}" for t, w in top)
        parts.append(
            f"**Крупнейшие позиции** по целевому весу: {tlist}. "
            f"**Доли ниже** — ориентир для стратегии; **дата** относится к снимку (см. строку под заголовком), а не к сигналу сделки.\n\n"
        )
    else:
        parts.append("*Нет позиций для отображения.*\n\n")
    mets = (snap or {}).get("metrics") or {}
    if isinstance(mets, dict) and mets:
        k = _kpi_block_latex_ru(mets)
        if k:
            parts.append("## Ключевые показатели\n\n")
            parts.append(k + "\n")
    parts.append("## Состав: все позиции\n\n")
    parts.append("\n| Инструмент | Целевой вес |\n| --- | ---: |\n")
    for t, w in items:
        parts.append(f"| **{t}** | {_escape_md_cell(f'{w * 100:.2f}%')} |\n")
    parts.append(
        f"\n**Сумма долей — {_fmt_scalar(sum(weights.values()), pct=True)}**; при полном инвестировании ожидается **около 100%**.\n"
    )
    return "".join(parts)


def build_ips_summary_md(
    text: str,
    *,
    variant_label: str | None = None,
    analysis_end: str | None = None,
    snapshot_folder: Path | None = None,
) -> str:
    del variant_label
    parts: list[str] = []
    snap = _read_snapshot_10y(snapshot_folder) if snapshot_folder else None
    wlab = str(snap.get("window_label") or "") if snap else None
    ae = analysis_end
    if snap and not ae and snap.get("analysis_end"):
        ae = str(snap.get("analysis_end") or "").strip() or None
    parts.append(
        _yaml_front_matter(
            "Политика и портфель: сводка реализации (IPS)",
            None,
            analysis_end=ae,
            window_label=wlab,
        )
    )
    raw = _soft_sanitize_narrative_for_pdf(text.replace("\r\n", "\n").strip())
    lines = [ln.rstrip() for ln in raw.split("\n") if ln.strip() != "=================================================="]
    if lines and lines[0].startswith("IPS Summary"):
        lines = lines[1:]

    parts.append("\n## Ключевой вывод\n\n")
    exec_lines: list[str] = []
    i = 0
    while i < len(lines):
        ln = lines[i]
        if re.match(r"^\d+\.\s", ln):
            break
        if ln.strip().startswith("---") or not ln.strip():
            i += 1
            continue
        exec_lines.append(ln.strip())
        i += 1
    if exec_lines:
        out_ln: list[str] = []
        for x in exec_lines:
            z = _executive_ru_sanitize(x)
            if not z.strip():
                continue
            if z.startswith("-"):
                out_ln.append(z)
            else:
                out_ln.append(f"- {z}")
        if out_ln:
            parts.append("\n".join(out_ln) + "\n")
        else:
            parts.append("*(Суть изложена в **нумерованных** пунктах ниже.)*\n")
    else:
        parts.append("*(Суть изложена в **нумерованных** пунктах ниже.)*\n")

    parts.append("\n## Реализация: по шагам плана\n\n")
    rest = "\n".join(lines[i:]).strip()
    sections = re.split(r"\n(?=\d+\.\s)", rest)
    for sec in sections:
        sec = sec.strip()
        if not sec:
            continue
        slines = sec.split("\n")
        head = _executive_ru_sanitize(slines[0].strip())
        body_lines = [
            x.rstrip()
            for x in slines[1:]
            if x.strip() and not re.match(r"^-+$", x.strip()) and not x.strip().startswith("---")
        ]
        parts.append(f"\n### {head}\n\n")
        if not body_lines:
            continue
        for bl in body_lines:
            bls = _executive_ru_sanitize(bl.strip())
            if not bls:
                continue
            if bls.startswith("-"):
                parts.append(f"{bls}\n")
            elif ":" in bls:
                parts.append(f"- {bls}\n")
            else:
                parts.append(f"{bls}\n\n")
    return "".join(parts)


def write_md_and_pdf(md_text: str, *, md_out: Path, pdf_out: Path, logger: Any = None) -> bool:
    md_out.parent.mkdir(parents=True, exist_ok=True)
    pdf_out.parent.mkdir(parents=True, exist_ok=True)
    md_out.write_text(md_text, encoding="utf-8")

    pandoc = _find_pandoc()
    if not pandoc:
        if logger:
            logger.warning("Pandoc not found; skipped PDF %s", pdf_out.name)
        return False
    if not _find_xelatex():
        if logger:
            logger.warning("xelatex not found; skipped PDF %s", pdf_out.name)
        return False

    cmd = _build_pandoc_pdf_cmd(pandoc=pandoc, md_out=md_out, pdf_out=pdf_out)
    try:
        subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if logger:
            logger.info("PDF written: %s", pdf_out)
        return True
    except subprocess.CalledProcessError as e:
        if logger:
            logger.warning("Pandoc failed for %s: %s", pdf_out.name, e.stderr or e)
        return False


def _copy_pdf_to_archive(pdf_path: Path, logger: Any = None) -> None:
    if not _OPTIONAL_ARCHIVE.is_dir():
        return
    dest = _OPTIONAL_ARCHIVE / pdf_path.name
    try:
        shutil.copy2(pdf_path, dest)
        if logger:
            logger.info("Archived PDF copy: %s", dest)
    except OSError as e:
        if logger:
            logger.warning("Could not archive PDF %s: %s", pdf_path.name, e)


def rebuild_all_pdfs(*, logger: Any = None) -> dict[str, bool]:
    """Regenerate all suite PDFs from current outputs. Returns {name: ok}."""
    results: dict[str, bool] = {}
    try:
        cfg = load_validated_config()
    except Exception as e:
        if logger:
            logger.error("Cannot load config for PDF rebuild: %s", e)
        return results

    out_final = _ROOT / (getattr(cfg, "output_dir_final", None) or "Main portfolio")
    eq_dir = _ROOT / "equal-weight portfolio"
    rp_dir = _ROOT / "risk parity portfolio"

    # --- EW vs RP ---
    comp_path = out_final / "ew_rp_comparison.json"
    if comp_path.is_file():
        try:
            comp = json.loads(comp_path.read_text(encoding="utf-8"))
            md = build_ew_rp_markdown(comp)
            md_side = _PDF_MD_SOURCES / "Main portfolio__ew_rp_comparison.md"
            ok = write_md_and_pdf(
                md, md_out=md_side, pdf_out=_PDF_OUT / "Main portfolio_ew_rp_comparison.pdf", logger=logger
            )
            results["Main portfolio_ew_rp_comparison.pdf"] = ok
            if ok:
                _copy_pdf_to_archive(_PDF_OUT / "Main portfolio_ew_rp_comparison.pdf", logger)
        except Exception as ex:
            if logger:
                logger.warning("EW/RP comparison PDF skipped: %s", ex)
            results["Main portfolio_ew_rp_comparison.pdf"] = False
    else:
        if logger:
            logger.warning("Missing %s — run run_compare_ew_rp.py", comp_path)
        results["Main portfolio_ew_rp_comparison.pdf"] = False

    def _commentary_pair(folder: Path, slug: str, title: str) -> None:
        cpath = folder / "commentary.txt"
        if not cpath.is_file():
            results[f"{slug}_commentary.pdf"] = False
            return
        text = cpath.read_text(encoding="utf-8")
        md = build_commentary_report_md(
            report_title=title,
            commentary_text=text,
            variant_label=folder.name,
            analysis_end=_detect_analysis_end(folder),
            snapshot_folder=folder,
        )
        name = f"{slug}_commentary.pdf"
        ok = write_md_and_pdf(
            md,
            md_out=_PDF_MD_SOURCES / f"{folder.name}__commentary.md",
            pdf_out=_PDF_OUT / name,
            logger=logger,
        )
        results[name] = ok
        if ok:
            _copy_pdf_to_archive(_PDF_OUT / name, logger)

    _commentary_pair(
        eq_dir, "equal-weight_portfolio", "Equal-weight: ровные веса как база для сравнения"
    )
    _commentary_pair(
        rp_dir, "risk_parity_portfolio", "Risk parity: риск в первую очередь"
    )

    def _stress_commentary_pair(folder: Path, pdf_name_stem: str, title: str) -> None:
        """pdf_name_stem e.g. equal-weight_portfolio or Main portfolio (matches existing PDF filenames)."""
        spath = folder / "stress_commentary.txt"
        if not spath.is_file():
            results[f"{pdf_name_stem}_stress_commentary.pdf"] = False
            return
        md = build_commentary_report_md(
            report_title=title,
            commentary_text=spath.read_text(encoding="utf-8"),
            variant_label=folder.name,
            analysis_end=_detect_analysis_end(folder),
            snapshot_folder=folder,
        )
        out_name = f"{pdf_name_stem}_stress_commentary.pdf"
        ok = write_md_and_pdf(
            md,
            md_out=_PDF_MD_SOURCES / f"{folder.name}__stress_commentary.md",
            pdf_out=_PDF_OUT / out_name,
            logger=logger,
        )
        results[out_name] = ok
        if ok:
            _copy_pdf_to_archive(_PDF_OUT / out_name, logger)

    _stress_commentary_pair(
        eq_dir, "equal-weight_portfolio", "Стресс: как ведёт себя equal-weight"
    )
    _stress_commentary_pair(
        rp_dir, "risk_parity_portfolio", "Стресс: как ведёт себя risk parity"
    )

    mp_comm = out_final / "commentary.txt"
    if mp_comm.is_file():
        md = build_commentary_report_md(
            report_title="Основной портфель: устойчивый риск-профиль при умеренной доходности",
            commentary_text=mp_comm.read_text(encoding="utf-8"),
            variant_label=out_final.name,
            analysis_end=_detect_analysis_end(out_final),
            snapshot_folder=out_final,
        )
        ok = write_md_and_pdf(
            md,
            md_out=_PDF_MD_SOURCES / "Main portfolio__commentary.md",
            pdf_out=_PDF_OUT / "Main portfolio_commentary.pdf",
            logger=logger,
        )
        results["Main portfolio_commentary.pdf"] = ok
        if ok:
            _copy_pdf_to_archive(_PDF_OUT / "Main portfolio_commentary.pdf", logger)
    else:
        results["Main portfolio_commentary.pdf"] = False

    _stress_commentary_pair(
        out_final,
        "Main portfolio",
        "Стресс: текущий состав под давлением сценариев",
    )

    # --- Weights ---
    for folder, slug, title in (
        (eq_dir, "equal-weight_portfolio", "Целевые веса: equal-weight"),
        (rp_dir, "risk_parity_portfolio", "Целевые веса: risk parity"),
    ):
        wpath = folder / "weights.json"
        if wpath.is_file():
            w = json.loads(wpath.read_text(encoding="utf-8"))
            if isinstance(w, dict):
                wf = {str(k): float(v) for k, v in w.items()}
                md = build_weights_report_md(
                    title=title,
                    weights=wf,
                    variant_label=folder.name,
                    analysis_end=_detect_analysis_end(folder),
                    snapshot_folder=folder,
                )
                name = f"{slug}_weights.pdf"
                ok = write_md_and_pdf(
                    md,
                    md_out=_PDF_MD_SOURCES / f"{folder.name}__weights.md",
                    pdf_out=_PDF_OUT / name,
                    logger=logger,
                )
                results[name] = ok
                if ok:
                    _copy_pdf_to_archive(_PDF_OUT / name, logger)
            else:
                results[f"{slug}_weights.pdf"] = False
        else:
            results[f"{slug}_weights.pdf"] = False

    ypath = out_final / "portfolio_weights.yml"
    if ypath.is_file():
        raw_w = yaml.safe_load(ypath.read_text(encoding="utf-8")) or {}
        if isinstance(raw_w, dict):
            wf = {str(k): float(v) for k, v in raw_w.items() if isinstance(v, (int, float))}
            md = build_weights_report_md(
                title="Состав портфеля: куда встаёт капитал",
                weights=wf,
                variant_label=out_final.name,
                analysis_end=_detect_analysis_end(out_final),
                snapshot_folder=out_final,
            )
            ok = write_md_and_pdf(
                md,
                md_out=_PDF_MD_SOURCES / "Main portfolio__weights.md",
                pdf_out=_PDF_OUT / "Main portfolio_weights.pdf",
                logger=logger,
            )
            results["Main portfolio_weights.pdf"] = ok
            if ok:
                _copy_pdf_to_archive(_PDF_OUT / "Main portfolio_weights.pdf", logger)
        else:
            results["Main portfolio_weights.pdf"] = False
    else:
        results["Main portfolio_weights.pdf"] = False

    ipath = out_final / "ips_summary.txt"
    if ipath.is_file():
        md = build_ips_summary_md(
            ipath.read_text(encoding="utf-8"),
            variant_label=out_final.name,
            analysis_end=_detect_analysis_end(out_final),
            snapshot_folder=out_final,
        )
        ok = write_md_and_pdf(
            md,
            md_out=_PDF_MD_SOURCES / "Main portfolio__ips_summary.md",
            pdf_out=_PDF_OUT / "Main portfolio_ips_summary.pdf",
            logger=logger,
        )
        results["Main portfolio_ips_summary.pdf"] = ok
        if ok:
            _copy_pdf_to_archive(_PDF_OUT / "Main portfolio_ips_summary.pdf", logger)
    else:
        results["Main portfolio_ips_summary.pdf"] = False

    icpath = out_final / "ips_summary.commentary.txt"
    if icpath.is_file():
        md = build_commentary_report_md(
            report_title="Сводка IPS: смысловой комментарий",
            commentary_text=icpath.read_text(encoding="utf-8"),
            variant_label=out_final.name,
            analysis_end=_detect_analysis_end(out_final),
            snapshot_folder=out_final,
        )
        ok = write_md_and_pdf(
            md,
            md_out=_PDF_MD_SOURCES / "Main portfolio__ips_summary.commentary.md",
            pdf_out=_PDF_OUT / "Main portfolio_ips_summary_commentary.pdf",
            logger=logger,
        )
        results["Main portfolio_ips_summary_commentary.pdf"] = ok
        if ok:
            _copy_pdf_to_archive(_PDF_OUT / "Main portfolio_ips_summary_commentary.pdf", logger)
    else:
        results["Main portfolio_ips_summary_commentary.pdf"] = False

    return results


def try_rebuild_pdfs_after_variant(*, logger: Any = None) -> None:
    """After EW or RP run: refresh comparison JSON, then rebuild PDF suite."""
    root = _ROOT
    compare = root / "run_compare_ew_rp.py"
    if compare.is_file():
        try:
            subprocess.run([sys.executable, str(compare)], cwd=str(root), check=True)
        except subprocess.CalledProcessError as e:
            if logger:
                logger.warning("run_compare_ew_rp.py exited %s; PDFs may omit fresh comparison.", e.returncode)
    rebuild_all_pdfs(logger=logger)


def try_rebuild_pdfs_only(*, logger: Any = None) -> None:
    """Rebuild PDFs only (comparison JSON must already exist)."""
    rebuild_all_pdfs(logger=logger)


def try_rebuild_pdfs_after_main_report(*, logger: Any = None) -> None:
    """
    After Main portfolio report (run_report / optimization chain): refresh Policy vs EW vs RP
    comparison from on-disk snapshots in output_dir_final + baseline folders, then rebuild PDFs.

    Does not rerun Equal-Weight or Risk-Parity; only refreshes portfolio_comparison.* so the
    triplet summary stays consistent when Policy/Main changed alone.
    """
    root = _ROOT
    cv = root / "run_compare_variants.py"
    if cv.is_file():
        try:
            subprocess.run([sys.executable, str(cv)], cwd=str(root), check=True)
        except subprocess.CalledProcessError as e:
            if logger:
                logger.warning(
                    "run_compare_variants.py exited %s; portfolio_comparison may be stale.",
                    e.returncode,
                )
    rebuild_all_pdfs(logger=logger)
