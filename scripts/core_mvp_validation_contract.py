"""
Shared Core MVP fixture-matrix validation contract (Steps 4–6).

Distinguishes required Core MVP product fields from optional diagnostics so
aggregating validators do not mark fixtures partial for advanced/optional gaps only.
"""
from __future__ import annotations

from typing import Any

from src.block_2_4_hidden_exposure import (
    ALERT_IDS,
    BLOCK_2_4_ID,
    BLOCKED_UPSTREAM_FIELDS,
    CONFIRMATION_STATUSES,
    MAX_CONTRIBUTING_ASSETS,
    RULE_VERSION,
)

# Blocks that must satisfy the Core MVP product contract for fixture rollup.
BLOCK2_CORE_MVP_ROLLUP_KEYS = (
    "block_2_1_asset_allocation",
    "block_2_2_portfolio_metrics",
    "block_2_3_factor_exposure",
    "block_2_5_risk_budget_view",
)

# Rule-based diagnostic blocks: product status may be partial when some alerts are unavailable.
BLOCK2_OPTIONAL_DIAGNOSTIC_KEYS = (
    "block_2_4_hidden_exposure",
    "block_2_6_portfolio_weakness_map",
)

# Warnings that are informational for Core MVP (do not fail block 2.3 contract).
BLOCK23_INFORMATIONAL_WARNING_PREFIXES = (
    "factor_variance_decomposition factor names normalized",
    "Kalman current beta unavailable",
    "Cash holdings are treated as real cash",
)

# Block 3: optional per-scenario enrichments for Core MVP (presence of stress_results_v1 row is required).
BLOCK3_OPTIONAL_SCENARIO_FIELDS = frozenset(
    {
        "assets_helped_hurt_available",
        "hedge_gap_available",
        "factor_attribution_available",
        "asset_loss_contribution_available",
    }
)

BLOCK24_REQUIRED_TOP_LEVEL_FIELDS = (
    "block",
    "block_id",
    "block_name",
    "status",
    "summary",
    "alerts",
    "top_hidden_risks",
    "data_quality_warnings",
    "diagnostics_meta",
)

BLOCK24_BLOCK_STATUS_VALUES = frozenset({"ok", "partial", "unavailable"})

BLOCK24_ALERT_REQUIRED_FIELDS = frozenset(
    {
        "status",
        "score",
        "evidence",
        "explanation",
        "why_it_matters",
        "next_tests",
        "confidence",
        "confidence_reason",
        "confirmation_status",
        "limitations",
        "contributing_assets",
        "data_quality_warnings",
        "insufficient_evidence_reasons",
        "calculation_notes",
    }
)

BLOCK24_EVIDENCE_REQUIRED_FIELDS = frozenset(
    {
        "metric",
        "value",
        "threshold",
        "direction",
        "source",
        "interpretation",
    }
)

BLOCK24_FORBIDDEN_EMBEDDED_STRESS_KEYS = frozenset(
    {
        "stress_report",
        "stress_results_v1",
        "scenario_results",
        "historical_results",
        "hedge_gap_analysis_v1",
        "current_portfolio_stress_scorecard_v1",
    }
)

BLOCK33_VERSION = "hedge_gap_analysis_v1"
BLOCK33_RULESET_VERSION = "hedge_gap_rules_v1_2"
BLOCK33_BLOCK_STATUS_VALUES = frozenset({"ok", "partial", "unavailable"})
BLOCK33_EXPECTED_RISK_TYPE_COUNT = 8

BLOCK33_REQUIRED_TOP_LEVEL_FIELDS = (
    "version",
    "ruleset_version",
    "block_status",
    "loss_gate_mode",
    "diagnosis_method",
    "scenario_library",
    "scenario_coverage",
    "by_risk_type",
    "summary",
    "n_risk_types",
)

BLOCK33_FORBIDDEN_PRODUCT_KEYS = frozenset(
    {
        "pass",
        "loss_ok",
        "gap_detected",
        "status",
        "max_dd_limit",
        "mandate_pass",
    }
)


def block_2_4_product_contract_violations(block: dict[str, Any] | None) -> list[str]:
    """Return Block 2.4 institutional v2 product-contract violations (empty = pass)."""
    if not isinstance(block, dict):
        return ["block_2_4_hidden_exposure: block is missing or not an object"]

    violations: list[str] = []
    missing_top = [field for field in BLOCK24_REQUIRED_TOP_LEVEL_FIELDS if field not in block]
    if missing_top:
        violations.append(f"block_2_4_hidden_exposure: missing top-level fields: {', '.join(missing_top)}")

    if block.get("block") != BLOCK_2_4_ID:
        violations.append(
            f"block_2_4_hidden_exposure: block id expected {BLOCK_2_4_ID!r}, got {block.get('block')!r}"
        )

    status = str(block.get("status") or "").strip().lower()
    if status not in BLOCK24_BLOCK_STATUS_VALUES:
        violations.append(f"block_2_4_hidden_exposure: invalid status {block.get('status')!r}")

    alerts = block.get("alerts")
    if not isinstance(alerts, dict):
        violations.append("block_2_4_hidden_exposure: alerts must be an object")
        alerts = {}

    if tuple(alerts.keys()) != ALERT_IDS:
        violations.append(
            "block_2_4_hidden_exposure: alerts keys must match ALERT_IDS "
            f"(expected {ALERT_IDS}, got {tuple(alerts.keys())})"
        )

    meta = block.get("diagnostics_meta")
    if not isinstance(meta, dict):
        violations.append("block_2_4_hidden_exposure: diagnostics_meta must be an object")
        meta = {}

    if meta.get("ruleset") != RULE_VERSION:
        violations.append(
            f"block_2_4_hidden_exposure: diagnostics_meta.ruleset expected {RULE_VERSION!r}, "
            f"got {meta.get('ruleset')!r}"
        )
    if meta.get("confidence_model") != "v2":
        violations.append(
            "block_2_4_hidden_exposure: diagnostics_meta.confidence_model expected 'v2', "
            f"got {meta.get('confidence_model')!r}"
        )
    if meta.get("does_not_run_stress_lab") is not True:
        violations.append("block_2_4_hidden_exposure: diagnostics_meta.does_not_run_stress_lab must be true")

    blocked = meta.get("blocked_upstream_fields")
    if not isinstance(blocked, list):
        violations.append("block_2_4_hidden_exposure: diagnostics_meta.blocked_upstream_fields must be a list")
    elif len(blocked) != len(BLOCKED_UPSTREAM_FIELDS):
        violations.append(
            "block_2_4_hidden_exposure: blocked_upstream_fields count "
            f"expected {len(BLOCKED_UPSTREAM_FIELDS)}, got {len(blocked)}"
        )

    for alert_id in ALERT_IDS:
        alert = alerts.get(alert_id)
        if not isinstance(alert, dict):
            violations.append(f"block_2_4_hidden_exposure.alerts.{alert_id}: alert must be an object")
            continue
        missing_alert = sorted(BLOCK24_ALERT_REQUIRED_FIELDS - set(alert))
        if missing_alert:
            violations.append(
                f"block_2_4_hidden_exposure.alerts.{alert_id}: missing fields: {', '.join(missing_alert)}"
            )
        if not isinstance(alert.get("limitations"), list):
            violations.append(f"block_2_4_hidden_exposure.alerts.{alert_id}: limitations must be a list")
        contributors = alert.get("contributing_assets")
        if not isinstance(contributors, list):
            violations.append(
                f"block_2_4_hidden_exposure.alerts.{alert_id}: contributing_assets must be a list"
            )
        elif len(contributors) > MAX_CONTRIBUTING_ASSETS:
            violations.append(
                f"block_2_4_hidden_exposure.alerts.{alert_id}: contributing_assets exceeds "
                f"{MAX_CONTRIBUTING_ASSETS}"
            )
        confirmation = alert.get("confirmation_status")
        if confirmation not in CONFIRMATION_STATUSES:
            violations.append(
                f"block_2_4_hidden_exposure.alerts.{alert_id}: invalid confirmation_status "
                f"{confirmation!r}"
            )
        evidence = alert.get("evidence")
        if not isinstance(evidence, list):
            violations.append(f"block_2_4_hidden_exposure.alerts.{alert_id}: evidence must be a list")
            continue
        for idx, item in enumerate(evidence):
            if not isinstance(item, dict):
                violations.append(
                    f"block_2_4_hidden_exposure.alerts.{alert_id}.evidence[{idx}]: row must be an object"
                )
                continue
            missing_evidence = sorted(BLOCK24_EVIDENCE_REQUIRED_FIELDS - set(item))
            if missing_evidence:
                violations.append(
                    f"block_2_4_hidden_exposure.alerts.{alert_id}.evidence[{idx}]: "
                    f"missing fields: {', '.join(missing_evidence)}"
                )

    for key in block:
        if key in BLOCK24_FORBIDDEN_EMBEDDED_STRESS_KEYS:
            violations.append(f"block_2_4_hidden_exposure: forbidden embedded stress key at top level: {key}")

    return violations


def assert_block_2_4_product_contract(block: dict[str, Any]) -> None:
    """Raise AssertionError when Block 2.4 institutional v2 contract is violated."""
    violations = block_2_4_product_contract_violations(block)
    if violations:
        raise AssertionError("; ".join(violations))


def hedge_gap_analysis_v1_product_contract_violations(
    block: dict[str, Any] | None,
) -> list[str]:
    """Return Block 3.3 institutional product-contract violations (empty = pass)."""
    if not isinstance(block, dict):
        return ["hedge_gap_analysis_v1: block is missing or not an object"]

    violations: list[str] = []
    prefix = "hedge_gap_analysis_v1"

    if block.get("version") != BLOCK33_VERSION:
        violations.append(
            f"{prefix}: version expected {BLOCK33_VERSION!r}, got {block.get('version')!r}"
        )

    missing_top = [field for field in BLOCK33_REQUIRED_TOP_LEVEL_FIELDS if field not in block]
    if missing_top:
        violations.append(f"{prefix}: missing top-level fields: {', '.join(missing_top)}")

    if block.get("ruleset_version") != BLOCK33_RULESET_VERSION:
        violations.append(
            f"{prefix}: ruleset_version expected {BLOCK33_RULESET_VERSION!r}, "
            f"got {block.get('ruleset_version')!r}"
        )

    block_status = str(block.get("block_status") or "").strip().lower()
    if block_status not in BLOCK33_BLOCK_STATUS_VALUES:
        violations.append(f"{prefix}: invalid block_status {block.get('block_status')!r}")

    if block.get("diagnosis_method") != "contribution_based_offset_coverage_v1":
        violations.append(
            f"{prefix}: diagnosis_method expected contribution_based_offset_coverage_v1, "
            f"got {block.get('diagnosis_method')!r}"
        )

    by_risk = block.get("by_risk_type")
    if not isinstance(by_risk, list):
        violations.append(f"{prefix}: by_risk_type must be a list")
    elif len(by_risk) != BLOCK33_EXPECTED_RISK_TYPE_COUNT:
        violations.append(
            f"{prefix}: by_risk_type length expected {BLOCK33_EXPECTED_RISK_TYPE_COUNT}, "
            f"got {len(by_risk)}"
        )

    n_risk_types = block.get("n_risk_types")
    if isinstance(by_risk, list) and n_risk_types != len(by_risk):
        violations.append(
            f"{prefix}: n_risk_types ({n_risk_types!r}) must match len(by_risk_type) ({len(by_risk)})"
        )

    summary = block.get("summary")
    if not isinstance(summary, dict):
        violations.append(f"{prefix}: summary must be an object")

    if block_status == "ok" and isinstance(by_risk, list):
        available = sum(
            1 for row in by_risk if isinstance(row, dict) and row.get("data_availability") == "available"
        )
        if available == 0:
            violations.append(f"{prefix}: block_status ok but no available by_risk_type rows")

    if isinstance(by_risk, list):
        for idx, row in enumerate(by_risk):
            if not isinstance(row, dict):
                violations.append(f"{prefix}.by_risk_type[{idx}]: row must be an object")
                continue
            forbidden = sorted(BLOCK33_FORBIDDEN_PRODUCT_KEYS & set(row))
            if forbidden:
                violations.append(
                    f"{prefix}.by_risk_type[{idx}]: forbidden legacy keys: {', '.join(forbidden)}"
                )

    for key in block:
        if key in BLOCK33_FORBIDDEN_PRODUCT_KEYS:
            violations.append(f"{prefix}: forbidden legacy key at top level: {key}")

    return violations


def check_hedge_gap_analysis_v1(block: dict[str, Any] | None) -> dict[str, Any]:
    """Structured Block 3.3 checks for fixture-matrix and live E2E validators."""
    violations = hedge_gap_analysis_v1_product_contract_violations(block)
    summary = (block or {}).get("summary") if isinstance((block or {}).get("summary"), dict) else {}
    main = summary.get("main_hedge_gap") if isinstance(summary.get("main_hedge_gap"), dict) else {}
    bridge_meta = (block or {}).get("bridge_meta") if isinstance((block or {}).get("bridge_meta"), dict) else {}
    by_risk = (block or {}).get("by_risk_type") if isinstance((block or {}).get("by_risk_type"), list) else []
    n_weak = sum(
        1
        for row in by_risk
        if isinstance(row, dict)
        and str(row.get("protection_status") or "") in {"weak_protection", "no_protection"}
    )
    return {
        "product_contract_ok": not violations,
        "contract_violations": violations,
        "block_status": (block or {}).get("block_status"),
        "ruleset_version": (block or {}).get("ruleset_version"),
        "protection_profile": summary.get("protection_profile"),
        "main_hedge_gap_risk_type": main.get("risk_type"),
        "main_hedge_gap_protection_status": main.get("protection_status"),
        "n_weak_protection_rows": n_weak if by_risk else None,
        "bridges_applied": {
            key: bool(bridge_meta.get(key))
            for key in ("block_2_4_hidden_exposure", "block_2_6_portfolio_weakness_map")
            if key in bridge_meta
        }
        if bridge_meta
        else None,
        "has_hidden_exposure_confirmation": isinstance((block or {}).get("hidden_exposure_confirmation"), list),
        "has_weakness_map_confirmation": isinstance((block or {}).get("weakness_map_confirmation"), list),
    }


def assert_hedge_gap_analysis_v1_product_contract(block: dict[str, Any]) -> None:
    """Raise AssertionError when Block 3.3 institutional product contract is violated."""
    violations = hedge_gap_analysis_v1_product_contract_violations(block)
    if violations:
        raise AssertionError("; ".join(violations))


BLOCK34_VERSION = "current_portfolio_stress_scorecard_v1"
BLOCK34_RULESET_VERSION = "current_portfolio_stress_scorecard_rules_v1_1"
BLOCK34_BLOCK_STATUS_VALUES = frozenset({"ok", "partial", "unavailable"})
BLOCK34_SCORECARD_SCOPE = "current_portfolio_diagnostic"

BLOCK34_REQUIRED_TOP_LEVEL_FIELDS = (
    "version",
    "block",
    "ruleset_version",
    "block_status",
    "scorecard_scope",
    "legacy_fallback_used",
    "stress_diagnosis",
    "next_decision_uses",
    "worst_synthetic_scenario",
    "worst_historical_scenario",
    "hedge_gap_summary",
)

BLOCK34_FORBIDDEN_PRODUCT_KEYS = frozenset(
    {
        "pass",
        "loss_ok",
        "max_dd_limit",
        "diagnostic_codes",
        "primary_diagnostic_code",
        "fail_reason_code",
        "failed_scenario",
        "failed_test",
        "overall_status",
    }
)


def _scorecard_v1_forbidden_keys_walk(obj: object) -> list[str]:
    found: list[str] = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key in BLOCK34_FORBIDDEN_PRODUCT_KEYS:
                found.append(key)
            found.extend(_scorecard_v1_forbidden_keys_walk(value))
    elif isinstance(obj, list):
        for item in obj:
            found.extend(_scorecard_v1_forbidden_keys_walk(item))
    return found


def current_portfolio_stress_scorecard_v1_live_output_violations(block: dict[str, Any]) -> list[str]:
    """Session 11 live-output gates when block_status is ok or partial."""
    prefix = BLOCK34_VERSION
    violations: list[str] = []
    block_status = str(block.get("block_status") or "").strip().lower()
    if block_status not in {"ok", "partial"}:
        return violations

    stress_diagnosis = block.get("stress_diagnosis")
    if not isinstance(stress_diagnosis, dict):
        violations.append(f"{prefix}: stress_diagnosis must be an object when block_status is {block_status}")
        stress_diagnosis = {}

    headline = stress_diagnosis.get("headline")
    if not isinstance(headline, str) or not headline.strip():
        violations.append(
            f"{prefix}: stress_diagnosis.headline must be non-empty when block_status is {block_status}"
        )

    confidence = stress_diagnosis.get("diagnosis_confidence")
    if confidence is None or str(confidence).strip().lower() == "unavailable":
        violations.append(
            f"{prefix}: stress_diagnosis.diagnosis_confidence must be present when block_status is {block_status}"
        )

    if not isinstance(block.get("legacy_fallback_used"), bool):
        violations.append(f"{prefix}: legacy_fallback_used must be explicit true or false")

    next_uses = block.get("next_decision_uses")
    if not isinstance(next_uses, list) or not next_uses:
        violations.append(
            f"{prefix}: next_decision_uses must be non-empty when block_status is {block_status}"
        )

    hg_status = str(block.get("hedge_gap_block_status") or "").strip().lower()
    hedge_summary = block.get("hedge_gap_summary")
    hedge_summary = hedge_summary if isinstance(hedge_summary, dict) else {}
    if hg_status in {"ok", "partial"} or hedge_summary.get("availability") == "available":
        gap_sid = hedge_summary.get("main_hedge_gap_scenario_id")
        if gap_sid is None or str(gap_sid).strip() == "":
            violations.append(
                f"{prefix}: hedge_gap_summary.main_hedge_gap_scenario_id required when hedge gap v1 is available"
            )

    from src.current_portfolio_stress_scorecard_block import collect_forbidden_english_phrases

    phrases = collect_forbidden_english_phrases(block)
    for phrase in phrases:
        violations.append(f"{prefix}: forbidden English phrase: {phrase!r}")

    return violations


def current_portfolio_stress_scorecard_v1_product_contract_violations(
    block: dict[str, Any] | None,
) -> list[str]:
    """Return Block 3.4 institutional product-contract violations (empty = pass)."""
    if not isinstance(block, dict):
        return [f"{BLOCK34_VERSION}: block is missing or not an object"]

    violations: list[str] = []
    prefix = BLOCK34_VERSION

    if block.get("version") != BLOCK34_VERSION:
        violations.append(
            f"{prefix}: version expected {BLOCK34_VERSION!r}, got {block.get('version')!r}"
        )

    missing_top = [field for field in BLOCK34_REQUIRED_TOP_LEVEL_FIELDS if field not in block]
    if missing_top:
        violations.append(f"{prefix}: missing top-level fields: {', '.join(missing_top)}")

    if block.get("block") != "3.4":
        violations.append(f"{prefix}: block id expected '3.4', got {block.get('block')!r}")

    if block.get("ruleset_version") != BLOCK34_RULESET_VERSION:
        violations.append(
            f"{prefix}: ruleset_version expected {BLOCK34_RULESET_VERSION!r}, "
            f"got {block.get('ruleset_version')!r}"
        )

    block_status = str(block.get("block_status") or "").strip().lower()
    if block_status not in BLOCK34_BLOCK_STATUS_VALUES:
        violations.append(f"{prefix}: invalid block_status {block.get('block_status')!r}")

    if block.get("scorecard_scope") != BLOCK34_SCORECARD_SCOPE:
        violations.append(
            f"{prefix}: scorecard_scope expected {BLOCK34_SCORECARD_SCOPE!r}, "
            f"got {block.get('scorecard_scope')!r}"
        )

    forbidden_keys = _scorecard_v1_forbidden_keys_walk(block)
    if forbidden_keys:
        violations.append(
            f"{prefix}: forbidden mandate-style keys: {', '.join(sorted(set(forbidden_keys)))}"
        )

    violations.extend(current_portfolio_stress_scorecard_v1_live_output_violations(block))

    return violations


def check_current_portfolio_stress_scorecard_v1(block: dict[str, Any] | None) -> dict[str, Any]:
    """Structured Block 3.4 checks for fixture-matrix and live E2E validators."""
    violations = current_portfolio_stress_scorecard_v1_product_contract_violations(block)
    stress_diagnosis = (block or {}).get("stress_diagnosis")
    stress_diagnosis = stress_diagnosis if isinstance(stress_diagnosis, dict) else {}
    hedge_summary = (block or {}).get("hedge_gap_summary")
    hedge_summary = hedge_summary if isinstance(hedge_summary, dict) else {}
    worst_syn = (block or {}).get("worst_synthetic_scenario")
    worst_syn = worst_syn if isinstance(worst_syn, dict) else {}
    signals = (block or {}).get("problem_classification_signals")
    signals = signals if isinstance(signals, dict) else {}
    ai_ctx = (block or {}).get("ai_commentary_context")
    ai_ctx = ai_ctx if isinstance(ai_ctx, dict) else {}
    return {
        "product_contract_ok": not violations,
        "contract_violations": violations,
        "block_status": (block or {}).get("block_status"),
        "ruleset_version": (block or {}).get("ruleset_version"),
        "legacy_fallback_used": (block or {}).get("legacy_fallback_used"),
        "diagnosis_confidence": stress_diagnosis.get("diagnosis_confidence"),
        "headline_present": bool(
            isinstance(stress_diagnosis.get("headline"), str) and stress_diagnosis.get("headline", "").strip()
        ),
        "main_hedge_gap_scenario_id": hedge_summary.get("main_hedge_gap_scenario_id"),
        "worst_synthetic_scenario_id": worst_syn.get("scenario_id"),
        "stress_severity": signals.get("stress_severity"),
        "next_decision_uses_count": len((block or {}).get("next_decision_uses") or [])
        if isinstance((block or {}).get("next_decision_uses"), list)
        else None,
        "ai_commentary_context_available": ai_ctx.get("availability") == "available",
    }


def assert_current_portfolio_stress_scorecard_v1_product_contract(block: dict[str, Any]) -> None:
    """Raise AssertionError when Block 3.4 institutional product contract is violated."""
    violations = current_portfolio_stress_scorecard_v1_product_contract_violations(block)
    if violations:
        raise AssertionError("; ".join(violations))


def check_block_2_4_hidden_exposure(block: dict[str, Any] | None) -> dict[str, Any]:
    """Structured Block 2.4 checks for fixture-matrix validators."""
    violations = block_2_4_product_contract_violations(block)
    meta = (block or {}).get("diagnostics_meta") or {}
    alerts = (block or {}).get("alerts") or {}
    unavailable_alerts = 0
    if isinstance(alerts, dict):
        unavailable_alerts = sum(1 for row in alerts.values() if isinstance(row, dict) and row.get("status") == "Unavailable")
    return {
        "institutional_v2_surface_ok": not violations,
        "contract_violations": violations,
        "ruleset": meta.get("ruleset"),
        "confidence_model": meta.get("confidence_model"),
        "does_not_run_stress_lab": meta.get("does_not_run_stress_lab"),
        "blocked_upstream_registry_count": len(meta.get("blocked_upstream_fields") or []),
        "alert_count": len(alerts) if isinstance(alerts, dict) else 0,
        "unavailable_alert_count": unavailable_alerts,
        "stress_boundary_ok": meta.get("does_not_run_stress_lab") is True
        and not any(v.startswith("block_2_4_hidden_exposure: forbidden embedded stress") for v in violations),
    }


def is_informational_block23_warning(message: str) -> bool:
    text = str(message or "").strip()
    if not text:
        return False
    return any(text.startswith(prefix) for prefix in BLOCK23_INFORMATIONAL_WARNING_PREFIXES)


def core_mvp_block2_block_status(
    block: dict[str, Any],
    block_key: str,
    *,
    missing_fields: list[str],
    warnings: list[str],
) -> str:
    """Derive Core MVP contract status for a single Block 2 product block."""
    if missing_fields:
        return "partial"
    if block_key == "block_2_4_hidden_exposure":
        if block_2_4_product_contract_violations(block):
            return "partial"
    if block_key in BLOCK2_OPTIONAL_DIAGNOSTIC_KEYS:
        explicit = str(block.get("status") or "").strip().lower()
        if explicit == "unavailable":
            return "unavailable"
        if explicit == "failed":
            return "failed"
        return "ok"
    if block_key == "block_2_3_factor_exposure":
        hard_warnings = [w for w in warnings if not is_informational_block23_warning(w)]
        if hard_warnings:
            return "partial"
        return "ok"
    explicit = str(block.get("status") or "").strip().lower()
    if explicit in {"failed", "unavailable"}:
        return explicit
    if explicit == "partial" and missing_fields:
        return "partial"
    return "ok"


def core_mvp_block2_fixture_status(block_results: dict[str, Any]) -> str:
    """Fixture-level Block 2 status using Core MVP rollup blocks only."""
    statuses = [
        core_mvp_block2_block_status(
            block_results.get(key) or {},
            key,
            missing_fields=list((block_results.get(key) or {}).get("missing_fields") or []),
            warnings=list((block_results.get(key) or {}).get("warnings") or []),
        )
        for key in BLOCK2_CORE_MVP_ROLLUP_KEYS
    ]
    if "failed" in statuses:
        return "failed"
    if any(s in {"partial", "unavailable"} for s in statuses):
        return "partial"
    return "ok"


def core_mvp_block3_scenario_status(scenario_row: dict[str, Any]) -> str:
    """Core MVP scenario status: require menu row + disclosed availability; enrichments optional."""
    audit_status = str(scenario_row.get("status") or "").strip().lower()
    if audit_status == "failed":
        return "failed"
    if audit_status == "unavailable":
        # Product contract: explicit unavailable disclosure (e.g. dotcom before fund inception) is acceptable.
        if str(scenario_row.get("availability") or "").strip().lower() == "unavailable":
            return "ok"
        return "unavailable"
    scenario_type = str(scenario_row.get("scenario_type") or "")
    if scenario_type == "synthetic":
        if not scenario_row.get("portfolio_pnl_pct_present") and not scenario_row.get("portfolio_loss_available"):
            return "failed"
        return "ok"
    if not scenario_row.get("historical_required_max_dd_or_pnl_real_episode_present") and not scenario_row.get(
        "portfolio_loss_available"
    ):
        return "failed"
    return "ok"


def core_mvp_block3_fixture_status(
    *,
    missing_block3_keys: list[str],
    missing_synthetic: list[str],
    missing_historical: list[str],
    scenario_rows: list[dict[str, Any]],
) -> str:
    if missing_block3_keys:
        return "failed"
    if missing_synthetic or missing_historical:
        return "partial"
    statuses = [core_mvp_block3_scenario_status(row) for row in scenario_rows]
    if "failed" in statuses:
        return "failed"
    if any(s == "unavailable" for s in statuses):
        return "partial"
    if any(s == "partial" for s in statuses):
        return "partial"
    return "ok"
