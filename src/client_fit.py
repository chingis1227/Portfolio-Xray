"""Client Fit V1 preset, questionnaire, and artifact helpers.

The preset/questionnaire helpers validate Client Fit configuration and derive a suggested preset
from questionnaire answers. The artifact builder compares already-produced X-Ray and Stress Lab
evidence against the provided Client Fit profile. It does not optimize, approve suitability, or
issue trade instructions.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

PROFILE_IDS = ("ultra_conservative", "conservative", "balanced", "growth", "aggressive")
QUESTION_IDS = (
    "main_objective",
    "target_return_expectation",
    "investment_horizon",
    "max_temporary_loss",
    "reaction_to_20_decline",
    "comfortable_yearly_fluctuation",
    "investment_experience",
    "profile_confirmation",
)
SOURCE_VALUES = {"questionnaire", "preset_override", "manual_override", "imported", "missing"}
SOURCE_QUALITY_VALUES = {"high", "medium", "low", "missing"}
CLIENT_FIT_CHECK_VERSION = "client_fit_check_v1"
CLIENT_FIT_CHECK_FILENAME = "client_fit_check.json"
RECOMMENDATION_BOUNDARY = (
    "Client Fit is a non-binding diagnostic overlay. It does not approve suitability, "
    "recommend trades, or replace downstream diagnosis and comparison evidence."
)


@dataclass(frozen=True)
class ClientFitValidationResult:
    ok: bool
    errors: list[str] = field(default_factory=list)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def client_profiles_path() -> Path:
    return repo_root() / "config" / "client_profiles.yml"


def questionnaire_path() -> Path:
    return repo_root() / "config" / "client_fit_questionnaire.yml"


def _load_yaml(path: Path | str) -> dict[str, Any]:
    with open(path, encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a YAML mapping.")
    return data


def _range_from_profile_spec(spec: dict[str, Any]) -> dict[str, float]:
    return {"min": float(spec["min_pct"]) / 100.0, "max": float(spec["max_pct"]) / 100.0}


def load_client_fit_presets(path: Path | str | None = None) -> dict[str, dict[str, Any]]:
    """Return Client Fit V1 ranges derived from config/client_profiles.yml.

    Liquidity fields are deliberately omitted because Client Fit V1 excludes liquidity.
    """
    data = _load_yaml(Path(path) if path is not None else client_profiles_path())
    profiles = data.get("profiles") or {}
    result: dict[str, dict[str, Any]] = {}
    for profile_id in PROFILE_IDS:
        profile = profiles.get(profile_id) or {}
        if not profile:
            continue
        result[profile_id] = {
            "preset_id": profile_id,
            "label": profile.get("client_fit_label") or profile.get("name") or profile_id.replace("_", " ").title(),
            "target_return_range": _range_from_profile_spec(profile["target_return_annual"]),
            "target_vol_range": _range_from_profile_spec(profile["target_vol_annual"]),
            "target_max_drawdown_pct": float(profile["target_max_drawdown_pct"]),
        }
    return result


def validate_client_fit_presets(path: Path | str | None = None) -> ClientFitValidationResult:
    errors: list[str] = []
    data = _load_yaml(Path(path) if path is not None else client_profiles_path())
    meta = data.get("client_fit_v1") or {}
    if meta.get("liquidity_in_scope") is not False:
        errors.append("client_fit_v1.liquidity_in_scope must be false for V1.")
    profiles = data.get("profiles") or {}
    for profile_id in PROFILE_IDS:
        profile = profiles.get(profile_id)
        if not isinstance(profile, dict):
            errors.append(f"missing profile: {profile_id}")
            continue
        for field_name in ("target_return_annual", "target_vol_annual"):
            spec = profile.get(field_name)
            if not isinstance(spec, dict):
                errors.append(f"{profile_id}.{field_name} must be a mapping.")
                continue
            for key in ("min_pct", "max_pct", "midpoint"):
                if key not in spec:
                    errors.append(f"{profile_id}.{field_name}.{key} is required.")
            if "min_pct" in spec and "max_pct" in spec and float(spec["min_pct"]) >= float(spec["max_pct"]):
                errors.append(f"{profile_id}.{field_name} min_pct must be below max_pct.")
        dd = profile.get("target_max_drawdown_pct")
        if not isinstance(dd, (int, float)) or float(dd) >= 0:
            errors.append(f"{profile_id}.target_max_drawdown_pct must be a negative number.")
    return ClientFitValidationResult(ok=not errors, errors=errors)


def load_questionnaire(path: Path | str | None = None) -> dict[str, Any]:
    return _load_yaml(Path(path) if path is not None else questionnaire_path())


def validate_questionnaire(path: Path | str | None = None) -> ClientFitValidationResult:
    errors: list[str] = []
    data = load_questionnaire(path)
    if data.get("schema_version") != "client_fit_questionnaire_v1":
        errors.append("schema_version must be client_fit_questionnaire_v1.")
    if data.get("liquidity_in_scope") is not False:
        errors.append("liquidity_in_scope must be false for V1.")
    if tuple(data.get("profile_order") or ()) != PROFILE_IDS:
        errors.append("profile_order must match the canonical Client Fit profile ids.")
    source_quality = data.get("source_quality") or {}
    for key in ("questionnaire_confirmed", "preset_override", "manual_override_complete", "missing"):
        value = source_quality.get(key)
        if value not in SOURCE_QUALITY_VALUES:
            errors.append(f"source_quality.{key} must be one of {sorted(SOURCE_QUALITY_VALUES)}.")
    questions = data.get("questions")
    if not isinstance(questions, list):
        errors.append("questions must be a list.")
        questions = []
    question_ids = [q.get("id") for q in questions if isinstance(q, dict)]
    if tuple(question_ids) != QUESTION_IDS:
        errors.append("questions must contain the eight canonical V1 ids in order.")
    for question in questions:
        if not isinstance(question, dict):
            errors.append("question entries must be mappings.")
            continue
        qid = question.get("id")
        if "liquidity" in str(qid).lower():
            errors.append("Client Fit V1 questionnaire must not include liquidity questions.")
        options = question.get("options")
        if not isinstance(options, list) or not options:
            errors.append(f"{qid}.options must be a non-empty list.")
            continue
        for option in options:
            if not isinstance(option, dict):
                errors.append(f"{qid}.options entries must be mappings.")
                continue
            if not option.get("id") or not option.get("label_en"):
                errors.append(f"{qid}.options entries require id and label_en.")
            for profile_id in (option.get("profile_scores") or {}):
                if profile_id not in PROFILE_IDS:
                    errors.append(f"{qid}.{option.get('id')} references unknown profile {profile_id}.")
            if option.get("source") and option["source"] not in SOURCE_VALUES:
                errors.append(f"{qid}.{option.get('id')} has invalid source {option['source']}.")
    return ClientFitValidationResult(ok=not errors, errors=errors)


def _option_by_question(data: dict[str, Any]) -> dict[str, dict[str, dict[str, Any]]]:
    result: dict[str, dict[str, dict[str, Any]]] = {}
    for question in data.get("questions") or []:
        qid = str(question.get("id"))
        result[qid] = {str(option.get("id")): option for option in question.get("options") or []}
    return result


def suggest_preset_from_answers(
    answers: dict[str, str],
    questionnaire: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Score questionnaire answers and return a suggested preset plus extracted targets."""
    data = questionnaire or load_questionnaire()
    options_by_question = _option_by_question(data)
    scores = {profile_id: 0.0 for profile_id in PROFILE_IDS}
    extracted: dict[str, Any] = {}
    answered: list[str] = []
    for question_id, option_id in answers.items():
        option = options_by_question.get(question_id, {}).get(option_id)
        if not option:
            continue
        answered.append(question_id)
        for profile_id, points in (option.get("profile_scores") or {}).items():
            if profile_id in scores:
                scores[profile_id] += float(points)
        for key in ("target_return_range", "target_vol_range", "target_max_drawdown_pct", "horizon_years"):
            if key in option:
                extracted[key] = option[key]
    best_profile = max(PROFILE_IDS, key=lambda profile_id: (scores[profile_id], -PROFILE_IDS.index(profile_id)))
    return {
        "suggested_preset_id": best_profile,
        "scores": scores,
        "answered_question_ids": answered,
        "extracted_targets": extracted,
        "source": "questionnaire",
        "source_quality": "medium",
        "source_quality_reason": "Based on the short Client Fit questionnaire and pending user confirmation.",
    }


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _as_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _range_or_none(value: Any) -> dict[str, float] | None:
    if not isinstance(value, dict):
        return None
    lo = _as_float(value.get("min"))
    hi = _as_float(value.get("max"))
    if lo is None or hi is None or lo >= hi:
        return None
    return {"min": lo, "max": hi}


def _profile_from_context(client_fit: dict[str, Any] | None) -> dict[str, Any] | None:
    raw = client_fit if isinstance(client_fit, dict) else {}
    if not raw:
        return None

    preset_id = raw.get("preset_id")
    preset: dict[str, Any] = {}
    if preset_id:
        preset = load_client_fit_presets().get(str(preset_id), {})

    target_return_range = _range_or_none(raw.get("target_return_range")) or preset.get("target_return_range")
    target_vol_range = _range_or_none(raw.get("target_vol_range")) or preset.get("target_vol_range")
    target_max_drawdown = _as_float(raw.get("target_max_drawdown_pct"))
    if target_max_drawdown is None:
        target_max_drawdown = _as_float(preset.get("target_max_drawdown_pct"))
    horizon_years = _as_float(raw.get("horizon_years"))

    return {
        "preset_id": str(preset_id) if preset_id else None,
        "source": raw.get("source") or "missing",
        "source_quality": raw.get("source_quality") or "missing",
        "source_quality_reason": raw.get("source_quality_reason"),
        "horizon_years": horizon_years,
        "target_return_range": target_return_range,
        "target_vol_range": target_vol_range,
        "target_max_drawdown_pct": target_max_drawdown,
    }


def _metric_from_xray(portfolio_xray: dict[str, Any], *path: str) -> float | None:
    cur: Any = portfolio_xray
    for key in path:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(key)
    return _as_float(cur)


def _worst_stress_loss(stress_report: dict[str, Any]) -> tuple[float | None, str | None]:
    scorecard = stress_report.get("current_portfolio_stress_scorecard_v1")
    if isinstance(scorecard, dict):
        worst_syn = scorecard.get("worst_synthetic_scenario")
        if isinstance(worst_syn, dict) and worst_syn.get("availability") == "available":
            val = _as_float(worst_syn.get("portfolio_loss_pct"))
            if val is not None:
                return val, "current_portfolio_stress_scorecard_v1.worst_synthetic_scenario.portfolio_loss_pct"
    conclusions = stress_report.get("stress_conclusions")
    if isinstance(conclusions, dict):
        worst = conclusions.get("worst_synthetic_scenario")
        if isinstance(worst, dict):
            val = _as_float(worst.get("portfolio_pnl_pct") or worst.get("portfolio_loss_pct"))
            if val is not None:
                return val, "stress_conclusions.worst_synthetic_scenario"
    return None, None


def _check_range(
    *,
    dimension: str,
    portfolio_value: float | None,
    client_range: dict[str, float] | None,
    source_artifact: str,
    source_field: str,
    lower_is_bad: bool = False,
) -> dict[str, Any]:
    if portfolio_value is None or client_range is None:
        status = "evidence_insufficient"
        interpretation = f"{dimension} cannot be evaluated because required evidence or target range is missing."
    elif lower_is_bad and portfolio_value < client_range["min"]:
        status = "watch"
        interpretation = f"{dimension} is below the stated target range."
    elif (not lower_is_bad) and portfolio_value > client_range["max"]:
        status = "breach"
        interpretation = f"{dimension} is above the stated comfort range."
    elif client_range["min"] <= portfolio_value <= client_range["max"]:
        status = "fit"
        interpretation = f"{dimension} is within the stated range."
    else:
        status = "watch"
        interpretation = f"{dimension} is outside the stated range but not a risk-limit breach."
    return {
        "dimension": dimension,
        "portfolio_value": portfolio_value,
        "client_range": client_range,
        "status": status,
        "interpretation": interpretation,
        "source_artifact": source_artifact,
        "source_field": source_field,
    }


def _check_limit(
    *,
    dimension: str,
    portfolio_value: float | None,
    client_limit: float | None,
    source_artifact: str,
    source_field: str | None,
) -> dict[str, Any]:
    if portfolio_value is None or client_limit is None:
        status = "evidence_insufficient"
        interpretation = f"{dimension} cannot be evaluated because required evidence or limit is missing."
    elif portfolio_value < client_limit:
        status = "breach"
        interpretation = f"{dimension} is worse than the stated drawdown limit."
    else:
        status = "fit"
        interpretation = f"{dimension} is within the stated drawdown limit."
    return {
        "dimension": dimension,
        "portfolio_value": portfolio_value,
        "client_limit": client_limit,
        "status": status,
        "interpretation": interpretation,
        "source_artifact": source_artifact,
        "source_field": source_field,
    }


def _goal_risk_conflict(profile: dict[str, Any]) -> dict[str, Any]:
    reasons: list[str] = []
    preset_id = str(profile.get("preset_id") or "")
    target_return_min = None
    if isinstance(profile.get("target_return_range"), dict):
        target_return_min = _as_float(profile["target_return_range"].get("min"))
    vol_max = None
    if isinstance(profile.get("target_vol_range"), dict):
        vol_max = _as_float(profile["target_vol_range"].get("max"))
    dd_limit = _as_float(profile.get("target_max_drawdown_pct"))
    horizon = _as_float(profile.get("horizon_years"))

    if target_return_min is not None and target_return_min >= 0.08 and dd_limit is not None and dd_limit >= -0.15:
        reasons.append("growth_return_with_conservative_drawdown_limit")
    if target_return_min is not None and target_return_min >= 0.10 and vol_max is not None and vol_max <= 0.12:
        reasons.append("aggressive_return_with_balanced_or_lower_volatility_limit")
    if horizon is not None and horizon < 3 and preset_id in {"growth", "aggressive"}:
        reasons.append("short_horizon_with_growth_or_aggressive_profile")
    if horizon is not None and horizon <= 5 and dd_limit is not None and dd_limit < -0.25:
        reasons.append("short_horizon_with_large_drawdown_tolerance")

    return {
        "status": "conflict" if reasons else "clear",
        "reasons": reasons,
        "interpretation": (
            "The return objective appears inconsistent with the stated drawdown tolerance and horizon."
            if reasons
            else "No internal goal-risk conflict detected from the provided V1 profile."
        ),
    }


def _overall_status(checks: list[dict[str, Any]], conflict: dict[str, Any]) -> str:
    if conflict.get("status") == "conflict":
        return "conflict"
    statuses = {str(row.get("status")) for row in checks}
    if "evidence_insufficient" in statuses:
        return "evidence_insufficient"
    if "breach" in statuses:
        return "breach"
    if "watch" in statuses:
        return "watch"
    return "fit"


def build_client_fit_check(
    *,
    client_fit: dict[str, Any] | None,
    portfolio_xray: dict[str, Any] | None,
    stress_report: dict[str, Any] | None,
    analysis_end: str | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Build the deterministic ``client_fit_check_v1`` artifact."""
    profile = _profile_from_context(client_fit)
    if profile is None:
        return {
            "schema_version": CLIENT_FIT_CHECK_VERSION,
            "client_fit_status": "not_provided",
            "generated_at": generated_at or _utc_now_iso(),
            "analysis_end": analysis_end,
            "profile": {
                "preset_id": None,
                "source": "missing",
                "source_quality": "missing",
                "source_quality_reason": "No Client Fit profile was provided for this backend/CLI-compatible run.",
                "horizon_years": None,
                "target_return_range": None,
                "target_vol_range": None,
                "target_max_drawdown_pct": None,
            },
            "checks": [],
            "goal_risk_conflict": {"status": "not_evaluated", "reasons": [], "interpretation": "No Client Fit profile was provided."},
            "recommendation_boundary": RECOMMENDATION_BOUNDARY,
            "source_artifacts": {"portfolio_xray": None, "stress_report": None},
            "warnings": ["client_fit_not_provided"],
        }

    xray = portfolio_xray if isinstance(portfolio_xray, dict) else {}
    stress = stress_report if isinstance(stress_report, dict) else {}
    cagr = _metric_from_xray(xray, "block_2_2_portfolio_metrics", "return_risk_metrics", "portfolio_cagr")
    vol = _metric_from_xray(xray, "block_2_2_portfolio_metrics", "return_risk_metrics", "vol_annual")
    max_dd = _metric_from_xray(xray, "block_2_2_portfolio_metrics", "drawdown_diagnostics", "max_drawdown")
    worst_stress, worst_stress_field = _worst_stress_loss(stress)

    checks = [
        _check_range(
            dimension="return_target_gap",
            portfolio_value=cagr,
            client_range=profile.get("target_return_range"),
            source_artifact="portfolio_xray.json",
            source_field="block_2_2_portfolio_metrics.return_risk_metrics.portfolio_cagr",
            lower_is_bad=True,
        ),
        _check_range(
            dimension="volatility_vs_target",
            portfolio_value=vol,
            client_range=profile.get("target_vol_range"),
            source_artifact="portfolio_xray.json",
            source_field="block_2_2_portfolio_metrics.return_risk_metrics.vol_annual",
        ),
        _check_limit(
            dimension="historical_max_drawdown_vs_limit",
            portfolio_value=max_dd,
            client_limit=profile.get("target_max_drawdown_pct"),
            source_artifact="portfolio_xray.json",
            source_field="block_2_2_portfolio_metrics.drawdown_diagnostics.max_drawdown",
        ),
        _check_limit(
            dimension="worst_stress_loss_vs_limit",
            portfolio_value=worst_stress,
            client_limit=profile.get("target_max_drawdown_pct"),
            source_artifact="stress_report.json",
            source_field=worst_stress_field,
        ),
    ]
    conflict = _goal_risk_conflict(profile)
    checks.append(
        {
            "dimension": "horizon_risk_mismatch",
            "portfolio_value": profile.get("horizon_years"),
            "client_limit": None,
            "status": "watch" if "short_horizon_with_growth_or_aggressive_profile" in conflict.get("reasons", []) else "fit",
            "interpretation": (
                "Horizon is short for the selected growth-oriented profile."
                if "short_horizon_with_growth_or_aggressive_profile" in conflict.get("reasons", [])
                else "No horizon-risk mismatch detected from the provided V1 profile."
            ),
            "source_artifact": "client_fit_check.json",
            "source_field": "profile.horizon_years",
        }
    )
    checks.append(
        {
            "dimension": "goal_risk_conflict",
            "portfolio_value": conflict.get("status"),
            "client_limit": None,
            "status": "conflict" if conflict.get("status") == "conflict" else "fit",
            "interpretation": conflict.get("interpretation"),
            "source_artifact": "client_fit_check.json",
            "source_field": "goal_risk_conflict",
        }
    )

    return {
        "schema_version": CLIENT_FIT_CHECK_VERSION,
        "client_fit_status": _overall_status(checks, conflict),
        "generated_at": generated_at or _utc_now_iso(),
        "analysis_end": analysis_end,
        "profile": profile,
        "checks": checks,
        "goal_risk_conflict": conflict,
        "recommendation_boundary": RECOMMENDATION_BOUNDARY,
        "source_artifacts": {
            "portfolio_xray": "portfolio_xray.json" if xray else None,
            "stress_report": "stress_report.json" if stress else None,
        },
        "warnings": [],
    }


def write_client_fit_check_outputs(
    *,
    output_dir: str | Path,
    client_fit: dict[str, Any] | None,
    portfolio_xray: dict[str, Any] | None,
    stress_report: dict[str, Any] | None,
    analysis_end: str | None = None,
) -> dict[str, Any]:
    """Write ``client_fit_check.json`` under ``output_dir`` and return the document."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    doc = build_client_fit_check(
        client_fit=client_fit,
        portfolio_xray=portfolio_xray,
        stress_report=stress_report,
        analysis_end=analysis_end,
    )
    with (out / CLIENT_FIT_CHECK_FILENAME).open("w", encoding="utf-8") as handle:
        json.dump(doc, handle, indent=2, ensure_ascii=False, default=str)
    return doc
