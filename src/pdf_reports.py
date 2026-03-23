"""
Rebuild investor-facing PDF reports from latest run outputs (Markdown → Pandoc → PDF).

Style target: formal single-column report (Times New Roman, 11pt, 1in margins), structured
sections and tables — aligned with the Equal-Weight vs Risk-Parity comparison report suite.

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

_METRIC_KEYS = [
    "cagr",
    "vol_annual",
    "max_drawdown",
    "sharpe",
    "sortino",
    "beta_portfolio",
    "treynor",
    "corr_base",
    "downside_deviation_annual",
    "skewness",
    "kurtosis",
    "es_95",
    "es_99",
    "eee_10pct",
    "ttr_months",
]
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

_COMMENTARY_SECTIONS = (
    "Executive Summary",
    "Metric-by-Metric Interpretation",
    "Risk Structure",
    "Strengths",
    "Weaknesses",
    "Scenario Behavior",
    "Final Conclusion",
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M %Z")


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


def _yaml_front_matter(title: str, subtitle: str | None = None) -> str:
    lines = [
        "---",
        f'title: "{title.replace(chr(34), chr(39))}"',
    ]
    if subtitle:
        lines.append(f'subtitle: "{subtitle.replace(chr(34), chr(39))}"')
    lines.extend(
        [
            f'date: "{_now_iso()}"',
            "documentclass: article",
            "geometry: margin=1in",
            "fontsize: 11pt",
            "---",
            "",
        ]
    )
    return "\n".join(lines)


def _build_executive_summary_bullets(comp: dict[str, Any]) -> list[str]:
    ew = comp.get("equal_weight") or {}
    rp = comp.get("risk_parity") or {}
    dm = (comp.get("delta") or {}).get("metrics") or {}
    em = ew.get("metrics") or {}
    rm = rp.get("metrics") or {}
    bullets = [
        f"Период: **{(comp.get('period') or {}).get('window_label', '—')}** "
        f"({(comp.get('period') or {}).get('window_months', '—')} мес.), "
        f"**analysis_end** = {(comp.get('period') or {}).get('analysis_end', '—')}.",
        f"Дельта: **{comp.get('delta_definition', 'EW − RP')}**.",
        (
            f"Доходность: EW **{_fmt_scalar(em.get('cagr'), pct=True)}** vs RP **{_fmt_scalar(rm.get('cagr'), pct=True)}** "
            f"(Δ **{_fmt_scalar(dm.get('cagr'), pct=True)}**)."
        ),
        (
            f"Риск: EW **{_fmt_scalar(em.get('vol_annual'), pct=True)}** vs RP **{_fmt_scalar(rm.get('vol_annual'), pct=True)}**; "
            f"max DD EW **{_fmt_scalar(em.get('max_drawdown'), pct=True)}** vs RP **{_fmt_scalar(rm.get('max_drawdown'), pct=True)}**."
        ),
        (
            f"Стресс: EW **{ew.get('stress_status', '—')}** ({ew.get('stress_fail_reason', '—')}); "
            f"RP **{rp.get('stress_status', '—')}** ({rp.get('stress_fail_reason', '—')})."
        ),
    ]
    return bullets


def build_ew_rp_markdown(comp: dict[str, Any], *, source_json: Path) -> str:
    ew = comp.get("equal_weight") or {}
    rp = comp.get("risk_parity") or {}
    eq_m = {**(ew.get("metrics") or {})}
    rp_m = {**(rp.get("metrics") or {})}
    delta_m = (comp.get("delta") or {}).get("metrics") or {}

    parts: list[str] = []
    parts.append(
        _yaml_front_matter(
            "Equal-Weight vs Risk-Parity — Comparison Report",
            "Analytical comparison of baseline portfolios",
        )
    )
    parts.append("## Report scope / source context\n")
    parts.append("- **Primary data:** `ew_rp_comparison.json` (machine-readable comparison).\n")
    parts.append(f"- **Source file:** `{source_json.as_posix()}`\n")
    parts.append(f"- **Generated:** {_now_iso()}\n")
    parts.append(
        f"- **Window:** {(comp.get('period') or {}).get('window_label', '—')} "
        f"(`window_months={(comp.get('period') or {}).get('window_months', '—')}`), "
        f"**analysis_end** = {(comp.get('period') or {}).get('analysis_end', '—')}.\n"
    )
    parts.append(f"- **Delta rule:** {comp.get('delta_definition', 'EW − RP')}.\n")

    parts.append("\n## Executive summary\n")
    for b in _build_executive_summary_bullets(comp):
        parts.append(f"- {b}\n")

    parts.append("\n## Core metrics (10Y window)\n")
    parts.append("\n| Metric | Equal-Weight | Risk-Parity | Delta (EW − RP) |\n")
    parts.append("| --- | ---: | ---: | ---: |\n")
    for k in _METRIC_KEYS:
        pct = k in _PCT_METRICS
        label = _METRIC_LABELS.get(k, k)
        parts.append(
            f"| {_escape_md_cell(label)} | {_escape_md_cell(_fmt_scalar(eq_m.get(k), pct=pct))} | "
            f"{_escape_md_cell(_fmt_scalar(rp_m.get(k), pct=pct))} | "
            f"{_escape_md_cell(_fmt_scalar(delta_m.get(k), pct=pct))} |\n"
        )

    roll = comp.get("rolling") or {}
    for label, key, pct in (
        ("Rolling Sharpe (36m)", "sharpe_36m", False),
        ("Rolling Sharpe (12m)", "sharpe_12m", False),
        ("Rolling vol (12m)", "vol_12m", True),
    ):
        block = roll.get(key) or {}
        parts.append(f"\n## {label}\n")
        parts.append("\n| Statistic | EW | RP | Delta |\n| --- | ---: | ---: | ---: |\n")
        for stat in ("last", "mean", "p10", "p90"):
            ew_s = (block.get("equal_weight") or {}).get(stat)
            rp_s = (block.get("risk_parity") or {}).get(stat)
            d_s = (block.get("delta") or {}).get(stat)
            parts.append(
                f"| **{stat}** | {_escape_md_cell(_fmt_scalar(ew_s, pct=pct))} | "
                f"{_escape_md_cell(_fmt_scalar(rp_s, pct=pct))} | "
                f"{_escape_md_cell(_fmt_scalar(d_s, pct=pct))} |\n"
            )

    parts.append("\n## Volatility stability\n")
    vs = (roll.get("vol_stability") or {})
    parts.append("\n| Measure | EW | RP | Delta |\n| --- | ---: | ---: | ---: |\n")
    for m in ("vol_of_vol", "rel_vol_of_vol"):
        ew_s = (vs.get("equal_weight") or {}).get(m)
        rp_s = (vs.get("risk_parity") or {}).get(m)
        d_s = (vs.get("delta") or {}).get(m)
        parts.append(
            f"| **{m}** | {_escape_md_cell(_fmt_scalar(ew_s))} | "
            f"{_escape_md_cell(_fmt_scalar(rp_s))} | {_escape_md_cell(_fmt_scalar(d_s))} |\n"
        )

    eq_rb = ew.get("rc_block") or {}
    rp_rb = rp.get("rc_block") or {}
    d_rb = (comp.get("delta") or {}).get("rc_block") or {}
    blocks = sorted(set(eq_rb.keys()) | set(rp_rb.keys()))
    parts.append("\n## RC_vol by block\n")
    parts.append("\n| Block | EW | RP | Delta |\n| --- | ---: | ---: | ---: |\n")
    for b in blocks:
        parts.append(
            f"| **{b}** | {_escape_md_cell(_fmt_scalar(eq_rb.get(b), pct=True))} | "
            f"{_escape_md_cell(_fmt_scalar(rp_rb.get(b), pct=True))} | "
            f"{_escape_md_cell(_fmt_scalar(d_rb.get(b), pct=True))} |\n"
        )

    eq_ra = ew.get("rc_asset") or {}
    rp_ra = rp.get("rc_asset") or {}
    d_ra = (comp.get("delta") or {}).get("rc_asset") or {}
    tickers = sorted(set(eq_ra.keys()) | set(rp_ra.keys()))
    parts.append("\n## RC_vol by asset\n")
    parts.append("\n| Ticker | EW | RP | Delta |\n| --- | ---: | ---: | ---: |\n")
    for t in tickers:
        parts.append(
            f"| **{t}** | {_escape_md_cell(_fmt_scalar(eq_ra.get(t), pct=True))} | "
            f"{_escape_md_cell(_fmt_scalar(rp_ra.get(t), pct=True))} | "
            f"{_escape_md_cell(_fmt_scalar(d_ra.get(t), pct=True))} |\n"
        )

    top = comp.get("rc_vol_top5_asset") or {}
    eq5 = top.get("equal_weight") or {}
    rp5 = top.get("risk_parity") or {}
    d5 = top.get("delta") or {}
    top_tickers = sorted(set(eq5.keys()) | set(rp5.keys()))
    parts.append("\n## RC_vol — top risk contributors (union of top-5 sets)\n")
    parts.append("\n| Ticker | EW | RP | Delta |\n| --- | ---: | ---: | ---: |\n")
    for t in top_tickers:
        parts.append(
            f"| **{t}** | {_escape_md_cell(_fmt_scalar(eq5.get(t), pct=True))} | "
            f"{_escape_md_cell(_fmt_scalar(rp5.get(t), pct=True))} | "
            f"{_escape_md_cell(_fmt_scalar(d5.get(t), pct=True))} |\n"
        )

    parts.append("\n## Stress and validation flags\n")
    parts.append(
        f"- **EW:** stress **{ew.get('stress_status', '—')}**, "
        f"reason `{ew.get('stress_fail_reason', '—')}`, "
        f"portfolio_valid **{ew.get('portfolio_valid', '—')}**.\n"
    )
    parts.append(
        f"- **RP:** stress **{rp.get('stress_status', '—')}**, "
        f"reason `{rp.get('stress_fail_reason', '—')}`, "
        f"portfolio_valid **{rp.get('portfolio_valid', '—')}**.\n"
    )

    parts.append("\n## Key takeaways\n")
    parts.append(
        "- Сравнение построено на **одинаковом универсуме тикеров** и **одном окне**; интерпретация дельт — относительная (EW vs RP).\n"
        "- При **FAIL_STRESS** пояснения по сценариям см. `stress_report.json` в соответствующих папках прогонов.\n"
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
    source_bullets: list[str],
    commentary_path: Path,
    commentary_text: str,
) -> str:
    parts: list[str] = []
    parts.append(_yaml_front_matter(report_title, "Commentary"))
    parts.append("## Report scope / source context\n")
    for b in source_bullets:
        parts.append(f"- {b}\n")
    parts.append(f"- **Commentary file:** `{commentary_path.as_posix()}`\n")
    parts.append(f"- **Generated:** {_now_iso()}\n")

    sections = _parse_commentary_sections(commentary_text)
    exec_body = ""
    rest: list[tuple[str, str]] = []
    for title, body in sections:
        if title == "Executive Summary":
            exec_body = body
        else:
            rest.append((title, body))

    parts.append("\n## Executive summary\n")
    if exec_body:
        for para in [p.strip() for p in exec_body.split("\n\n") if p.strip()]:
            if para.startswith("- "):
                parts.append(f"{para}\n")
            else:
                parts.append(f"{para}\n\n")
    else:
        parts.append("_No executive summary block parsed._\n")

    for title, body in rest:
        parts.append(f"\n## {title}\n\n")
        if title in ("Strengths", "Weaknesses") or body.strip().startswith("-"):
            parts.append(body if body.endswith("\n") else body + "\n")
        else:
            for para in [p.strip() for p in body.split("\n\n") if p.strip()]:
                parts.append(f"{para}\n\n")

    return "".join(parts)


def build_weights_report_md(*, title: str, weights: dict[str, float], source_path: Path) -> str:
    parts: list[str] = []
    parts.append(_yaml_front_matter(title, "Weights"))
    parts.append("## Report scope / source context\n")
    parts.append(f"- **Weights source:** `{source_path.as_posix()}`\n")
    parts.append(f"- **Generated:** {_now_iso()}\n")
    items = sorted(weights.items(), key=lambda kv: (-kv[1], kv[0]))
    parts.append("\n## Weights\n")
    parts.append("\n| Ticker | Weight |\n| --- | ---: |\n")
    for t, w in items:
        parts.append(f"| **{t}** | {_escape_md_cell(f'{w * 100:.2f}%')} |\n")
    parts.append(f"\n**Sum:** {_fmt_scalar(sum(weights.values()), pct=True)}\n")
    return "".join(parts)


def build_ips_summary_md(text: str, *, source_path: Path) -> str:
    parts: list[str] = []
    parts.append(_yaml_front_matter("IPS Summary — Policy Run", "Main portfolio"))
    parts.append("## Report scope / source context\n")
    parts.append(f"- **Source:** `{source_path.as_posix()}`\n")
    parts.append(f"- **Generated:** {_now_iso()}\n")

    raw = text.replace("\r\n", "\n").strip()
    lines = [ln.rstrip() for ln in raw.split("\n") if ln.strip() != "=================================================="]
    # Drop decorative title line if present
    if lines and lines[0].startswith("IPS Summary"):
        lines = lines[1:]

    parts.append("\n## Executive summary\n")
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
        parts.append("\n".join(f"- {x}" if not x.startswith("-") else x for x in exec_lines) + "\n")
    else:
        parts.append("_See numbered sections below._\n")

    parts.append("\n## Detailed results\n")
    rest = "\n".join(lines[i:]).strip()
    sections = re.split(r"\n(?=\d+\.\s)", rest)
    for sec in sections:
        sec = sec.strip()
        if not sec:
            continue
        slines = sec.split("\n")
        head = slines[0].strip()
        body_lines = [
            x.rstrip()
            for x in slines[1:]
            if x.strip() and not re.match(r"^-+$", x.strip()) and not x.strip().startswith("---")
        ]
        parts.append(f"\n### {head}\n\n")
        if not body_lines:
            continue
        for bl in body_lines:
            bls = bl.strip()
            if bls.startswith("-"):
                parts.append(f"{bls}\n")
            elif ":" in bls:
                parts.append(f"- {bls}\n")
            else:
                parts.append(f"{bls}\n\n")

    parts.append("\n## Key takeaways\n")
    parts.append(
        "- Сводка отражает **последний прогон оптимизации** по policy; при смене конфигурации перезапустите пайплайн.\n"
    )
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

    mainfont = "Times New Roman" if sys.platform == "win32" else "Liberation Serif"
    cmd = [
        pandoc,
        str(md_out),
        "-o",
        str(pdf_out),
        "--pdf-engine=xelatex",
        "-V",
        f"mainfont={mainfont}",
        "-V",
        "geometry:margin=1in",
        "-V",
        "fontsize=11pt",
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
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
            md = build_ew_rp_markdown(comp, source_json=comp_path)
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
            source_bullets=[
                f"**Variant folder:** `{folder.name}`",
                "**Basis:** post-run commentary (metrics interpreted as reported).",
            ],
            commentary_path=cpath,
            commentary_text=text,
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

    _commentary_pair(eq_dir, "equal-weight_portfolio", "Equal-Weight Portfolio — Commentary")
    _commentary_pair(rp_dir, "risk_parity_portfolio", "Risk-Parity Portfolio — Commentary")

    mp_comm = out_final / "commentary.txt"
    if mp_comm.is_file():
        md = build_commentary_report_md(
            report_title="Main Portfolio — Commentary (policy run)",
            source_bullets=[
                f"**Output folder:** `{out_final.name}`",
                "**Basis:** policy portfolio commentary.",
            ],
            commentary_path=mp_comm,
            commentary_text=mp_comm.read_text(encoding="utf-8"),
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

    # --- Weights ---
    for folder, slug, title in (
        (eq_dir, "equal-weight_portfolio", "Equal-Weight — Weights"),
        (rp_dir, "risk_parity_portfolio", "Risk-Parity — Weights"),
    ):
        wpath = folder / "weights.json"
        if wpath.is_file():
            w = json.loads(wpath.read_text(encoding="utf-8"))
            if isinstance(w, dict):
                wf = {str(k): float(v) for k, v in w.items()}
                md = build_weights_report_md(title=title, weights=wf, source_path=wpath)
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
                title="Main Portfolio — Optimized Weights",
                weights=wf,
                source_path=ypath,
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
        md = build_ips_summary_md(ipath.read_text(encoding="utf-8"), source_path=ipath)
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
            report_title="IPS Summary — Commentary",
            source_bullets=[
                f"**Folder:** `{out_final.name}`",
                "**Basis:** commentary on IPS summary.",
            ],
            commentary_path=icpath,
            commentary_text=icpath.read_text(encoding="utf-8"),
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
