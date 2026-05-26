"""Core MVP input normalization for portfolio-first diagnosis."""
from __future__ import annotations

from typing import Any

from src.analysis_setup import _clean_tickers, positive_weights


def _has_explicit_analysis_subject_type(cfg: dict[str, Any]) -> bool:
    raw = cfg.get("analysis_subject")
    if not isinstance(raw, dict):
        return False
    return bool(str(raw.get("type") or "").strip())


def _is_generated_weight_source(source: str | None) -> bool:
    text = str(source or "")
    return "portfolio_weights.yml" in text or text.startswith("optimization_result")


def apply_mvp_input_defaults(cfg: dict[str, Any]) -> dict[str, Any]:
    """
    Inject Core MVP diagnosis defaults when the user supplies allocation without
    an explicit ``analysis_subject.type``.

    Sets ``analysis_mode=analyze_current_weights`` and builds
    ``analysis_subject`` as ``current_portfolio`` from positive ``current_weights``
    or non-generated top-level ``weights``. Mutates *cfg* in place.
    """
    if _has_explicit_analysis_subject_type(cfg):
        return cfg

    current = positive_weights(cfg.get("current_weights"))
    top = positive_weights(cfg.get("weights"))
    source = str(cfg.get("_weights_source") or "")

    weight_map: dict[str, float] | None = None
    if current:
        weight_map = current
    elif top and not _is_generated_weight_source(source):
        weight_map = top

    if not weight_map:
        return cfg

    existing = cfg.get("analysis_subject") if isinstance(cfg.get("analysis_subject"), dict) else {}
    cfg["analysis_mode"] = "analyze_current_weights"
    cfg["analysis_subject"] = {
        "id": str(existing.get("id") or "analysis_subject").strip() or "analysis_subject",
        "type": "current_portfolio",
        "display_name": str(existing.get("display_name") or "").strip(),
        "tickers": _clean_tickers(cfg.get("tickers")),
        "weights": dict(weight_map),
    }
    return cfg


__all__ = ["apply_mvp_input_defaults"]
