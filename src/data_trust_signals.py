"""User-facing data-quality and young-ETF trust signals (disclosure only; no formula changes)."""
from __future__ import annotations

from typing import Any

STRESS_DATA_TRUST_SUMMARY_VERSION = "stress_data_trust_summary_v1"
INPUT_DATA_TRUST_SIGNALS_VERSION = "input_data_trust_signals_v1"
XRAY_DATA_TRUST_SIGNALS_VERSION = "xray_data_trust_signals_v1"

_HISTORICAL_QUALITY_OK = frozenset({"reliable", "usable_with_gaps"})
_QUALITY_RANK = {
    "insufficient_data": 0,
    "low_confidence": 1,
    "usable_with_gaps": 2,
    "reliable": 3,
}


def _young_etf_policy_summary(policy: dict[str, Any] | None) -> str:
    pol = policy if isinstance(policy, dict) else {}
    if not pol.get("enabled", True):
        return "Young ETF optimization policy is disabled; optimizer paths use the standard covariance panel only."
    min_months = pol.get("min_history_months")
    mode = pol.get("mode") or "configured_default"
    cap = pol.get("max_weight_cap_for_young")
    extras: list[str] = [f"mode={mode}"]
    if min_months is not None:
        extras.append(f"min_history_months={min_months}")
    if cap is not None:
        extras.append(f"max_weight_cap_for_young={cap}")
    detail = ", ".join(extras)
    return (
        f"Young ETF policy is enabled for optimizer-backed runs ({detail}). "
        "Short-history holdings may receive tighter caps or dual-covariance treatment."
    )


def _episode_replay_available(row: dict[str, Any]) -> bool:
    n_obs = row.get("n_obs")
    if not isinstance(n_obs, (int, float)) or int(n_obs) < 2:
        return False
    if row.get("max_dd") is None and row.get("pnl_real_episode") is None:
        return False
    return str(row.get("data_quality") or "") != "insufficient_data"


def _episode_plain_english(row: dict[str, Any]) -> str:
    episode = str(row.get("episode") or "unknown")
    quality = str(row.get("data_quality") or "unknown")
    coverage = row.get("coverage_ratio")
    n_obs = row.get("n_obs")
    replay = _episode_replay_available(row)
    if quality == "insufficient_data":
        return (
            f"{episode}: insufficient history for reliable historical stress; "
            "episode PnL and replay are not decision-grade."
        )
    if quality == "low_confidence":
        cov = f", coverage={float(coverage):.0%}" if isinstance(coverage, (int, float)) else ""
        return (
            f"{episode}: low confidence historical evidence{cov}; "
            + ("crisis replay available but interpret cautiously." if replay else "no crisis replay path.")
        )
    if quality == "usable_with_gaps":
        cov = f" (coverage={float(coverage):.0%})" if isinstance(coverage, (int, float)) else ""
        return f"{episode}: usable with data gaps{cov}; replay={'yes' if replay else 'no'}."
    if quality == "reliable":
        return f"{episode}: reliable historical coverage (n_obs={n_obs})."
    return f"{episode}: data_quality={quality}."


def _overall_historical_trust(quality_counts: dict[str, int], *, n_episodes: int) -> str:
    if n_episodes <= 0:
        return "low"
    insufficient = quality_counts.get("insufficient_data", 0)
    low_conf = quality_counts.get("low_confidence", 0)
    if insufficient > 0 or insufficient + low_conf >= max(1, n_episodes // 2):
        return "low"
    if any(quality_counts.get(q, 0) > 0 for q in ("low_confidence", "usable_with_gaps")):
        return "medium"
    return "high"


def _structure_data_quality_warnings(warnings: list[Any]) -> list[dict[str, Any]]:
    structured: list[dict[str, Any]] = []
    for raw in warnings:
        text = str(raw).strip()
        if not text:
            continue
        if text.startswith("primary_historical_stress:"):
            structured.append(
                {
                    "kind": "methodology_boundary",
                    "plain_english": (
                        "Primary historical stress uses realized portfolio monthly returns only; "
                        "per-asset proxy waterfalls apply in the normalized scenario library, not "
                        "in the primary historical PnL path."
                    ),
                }
            )
            continue
        if ": " in text and "return_method=" in text:
            episode_part, detail = text.split(": ", 1)
            structured.append(
                {
                    "kind": "historical_episode",
                    "episode": episode_part,
                    "plain_english": detail.replace("return_method=", "return method "),
                    "detail": detail,
                }
            )
            continue
        structured.append({"kind": "other", "plain_english": text})
    return structured


def build_stress_data_trust_summary(
    *,
    historical_results: list[dict[str, Any]] | None,
    stress_conclusions: dict[str, Any] | None,
    stress_scorecard_v1: dict[str, Any] | None = None,
    historical_episode_paths: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Compact trust summary for stress_report.json and stress commentary."""
    hist = [h for h in (historical_results or []) if isinstance(h, dict)]
    conclusions = stress_conclusions if isinstance(stress_conclusions, dict) else {}
    scorecard = stress_scorecard_v1 if isinstance(stress_scorecard_v1, dict) else {}

    quality_counts: dict[str, int] = {}
    episode_flags: list[dict[str, Any]] = []
    for row in hist:
        quality = str(row.get("data_quality") or "unknown")
        quality_counts[quality] = quality_counts.get(quality, 0) + 1
        episode_flags.append(
            {
                "episode": row.get("episode"),
                "data_quality": quality,
                "coverage_ratio": row.get("coverage_ratio"),
                "n_obs": row.get("n_obs"),
                "replay_available": _episode_replay_available(row),
                "plain_english": _episode_plain_english(row),
            }
        )

    paths_by_episode = {
        str(p.get("episode")): p
        for p in (historical_episode_paths or [])
        if isinstance(p, dict) and p.get("episode")
    }
    for flag in episode_flags:
        ep = str(flag.get("episode") or "")
        if ep in paths_by_episode:
            flag["replay_available"] = True

    raw_warnings = list(conclusions.get("data_quality_warnings") or [])
    structured_warnings = _structure_data_quality_warnings(raw_warnings)
    n_flagged = sum(1 for row in hist if str(row.get("data_quality") or "") not in _HISTORICAL_QUALITY_OK)
    overall_trust = _overall_historical_trust(quality_counts, n_episodes=len(hist))
    overall_confidence = conclusions.get("overall_confidence") or scorecard.get("overall_confidence")
    if overall_confidence == "low" and overall_trust == "high":
        overall_trust = "medium"

    user_summary_lines: list[str] = []
    if len(hist) == 0:
        user_summary_lines.append(
            "Historical stress: no episode rows were computed; treat historical conclusions as unavailable."
        )
    elif n_flagged:
        user_summary_lines.append(
            f"Historical stress: {n_flagged} of {len(hist)} episodes have incomplete or low-confidence data."
        )
    else:
        user_summary_lines.append(
            f"Historical stress: all {len(hist)} episodes meet reliable or usable-with-gaps data quality."
        )
    for flag in episode_flags:
        if str(flag.get("data_quality") or "") not in _HISTORICAL_QUALITY_OK:
            user_summary_lines.append(str(flag.get("plain_english") or ""))
    if len(user_summary_lines) > 6:
        user_summary_lines = user_summary_lines[:6] + [
            f"{max(0, n_flagged - (6 - 1))} additional episode quality flags are in stress_report.json."
        ]

    worst_hist = conclusions.get("worst_historical_episode")
    if isinstance(worst_hist, dict) and worst_hist.get("episode"):
        wq = worst_hist.get("data_quality")
        if wq and wq not in _HISTORICAL_QUALITY_OK:
            user_summary_lines.append(
                f"Worst historical episode ({worst_hist.get('episode')}) uses {wq} data — "
                "interpret drawdown severity cautiously."
            )

    return {
        "version": STRESS_DATA_TRUST_SUMMARY_VERSION,
        "overall_trust": overall_trust,
        "overall_confidence": overall_confidence,
        "historical_episode_quality_counts": quality_counts,
        "n_historical_episodes_flagged": n_flagged,
        "episode_flags": episode_flags,
        "promoted_warnings": structured_warnings,
        "user_summary_lines": [line for line in user_summary_lines if line],
        "does_not_change_stress_methodology": True,
    }


def _validation_trust_signals(validation_result: dict[str, Any] | None) -> list[dict[str, Any]]:
    vr = validation_result if isinstance(validation_result, dict) else {}
    signals: list[dict[str, Any]] = []
    for conflict in vr.get("legacy_current_repo_conflicts") or []:
        if not isinstance(conflict, dict):
            continue
        code = str(conflict.get("code") or "")
        if code == "UNKNOWN_TICKER_POLICY":
            signals.append(
                {
                    "category": "taxonomy",
                    "severity": "medium",
                    "code": code,
                    "plain_english": (
                        "Legacy run metadata: unknown tickers were warn-only on this path. "
                        "Explicit analysis_subject inputs now fail at config validation; "
                        "review X-Ray allocation warnings on older artifacts."
                    ),
                }
            )
    for warning in vr.get("action_required_warnings") or []:
        if not isinstance(warning, dict):
            continue
        signals.append(
            {
                "category": "input_validation",
                "severity": "medium",
                "code": str(warning.get("code") or "ACTION_REQUIRED"),
                "plain_english": str(warning.get("message") or warning),
            }
        )
    return signals


def build_input_data_trust_signals(
    *,
    young_etf_optimization_policy: dict[str, Any] | None,
    validation_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Exported trust block for input_assumptions.json."""
    policy = dict(young_etf_optimization_policy or {})
    signals = _validation_trust_signals(validation_result)
    signals.insert(
        0,
        {
            "category": "young_etf_policy",
            "severity": "info" if policy.get("enabled", True) else "low",
            "code": "YOUNG_ETF_OPTIMIZATION_POLICY",
            "plain_english": _young_etf_policy_summary(policy),
        },
    )
    user_summary_lines = [str(s.get("plain_english") or "") for s in signals if s.get("plain_english")]
    return {
        "version": INPUT_DATA_TRUST_SIGNALS_VERSION,
        "young_etf_policy_enabled": bool(policy.get("enabled", True)),
        "young_etf_policy_summary": _young_etf_policy_summary(policy),
        "signals": signals,
        "user_summary_lines": user_summary_lines[:5],
        "does_not_change_data_policy": True,
    }


def collect_xray_section_warnings(xray: dict[str, Any] | None) -> list[str]:
    """Gather section-level warnings from a portfolio_xray_v2 document."""
    if not isinstance(xray, dict):
        return []
    warnings: list[str] = []
    for section in (xray.get("sections") or {}).values():
        if not isinstance(section, dict):
            continue
        for warning in section.get("warnings") or []:
            text = str(warning).strip()
            if text:
                warnings.append(text)
        unavailable = section.get("unavailable_warning")
        if unavailable:
            warnings.append(str(unavailable))
    return warnings


def build_xray_data_trust_signals(
    xray: dict[str, Any],
    *,
    stress_data_trust_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Top-level X-Ray trust block for portfolio_xray.json and commentary."""
    section_warnings = collect_xray_section_warnings(xray)
    signals: list[dict[str, Any]] = []
    for text in section_warnings:
        category = "taxonomy"
        severity = "medium"
        lower = text.lower()
        if "taxonomy" in lower or "unknown" in lower:
            category = "taxonomy"
        elif "stress" in lower or "factor" in lower:
            category = "stress_inputs"
        elif "missing" in lower:
            severity = "high"
        signals.append(
            {
                "category": category,
                "severity": severity,
                "code": "XRAY_SECTION_WARNING",
                "plain_english": text,
            }
        )

    user_summary_lines = [str(s["plain_english"]) for s in signals[:4]]
    stress_summary = (
        stress_data_trust_summary
        if isinstance(stress_data_trust_summary, dict)
        else None
    )
    if stress_summary:
        for line in list(stress_summary.get("user_summary_lines") or [])[:2]:
            user_summary_lines.append(f"Stress data trust: {line}")

    overall = "high"
    if any(s.get("severity") == "high" for s in signals):
        overall = "low"
    elif signals or (stress_summary and stress_summary.get("n_historical_episodes_flagged")):
        overall = "medium"
    if stress_summary and stress_summary.get("overall_trust") == "low":
        overall = "low"

    return {
        "version": XRAY_DATA_TRUST_SIGNALS_VERSION,
        "overall_trust": overall,
        "n_section_warnings": len(section_warnings),
        "signals": signals,
        "stress_data_trust_summary_version": (
            stress_summary.get("version") if stress_summary else None
        ),
        "user_summary_lines": [line for line in user_summary_lines if line][:6],
        "does_not_change_xray_methodology": True,
    }


__all__ = [
    "STRESS_DATA_TRUST_SUMMARY_VERSION",
    "INPUT_DATA_TRUST_SIGNALS_VERSION",
    "XRAY_DATA_TRUST_SIGNALS_VERSION",
    "build_input_data_trust_signals",
    "build_stress_data_trust_summary",
    "build_xray_data_trust_signals",
    "collect_xray_section_warnings",
]
