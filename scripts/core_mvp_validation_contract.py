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


# ---------------------------------------------------------------------------
# Block 4 v2 — Problem Classification + Candidate Launchpad (Decision entry)
# Spec: docs/specs/block_4_diagnosis_v2_spec.md
# V1 product validators removed Session 14 (DEC-2026-05-29-013). Legacy builders
# src/problem_classification.py and src/candidate_launchpad.py remain for unit tests.
# ---------------------------------------------------------------------------

PROBLEM_CLASSIFICATION_CONFIDENCE = frozenset({"low", "medium", "high"})

LAUNCHPAD_KNOWN_METHOD_IDS = frozenset(
    {
        "minimum_variance",
        "risk_parity",
        "equal_weight",
        "minimum_cvar_constrained",
        "equal_weight_by_asset_class",
        "maximum_diversification",
        "risk_budget_by_asset",
        "robust_mv_constrained",
        "robust_scenario",
    }
)

LAUNCHPAD_KNOWN_GOALS = frozenset(
    {
        "Reduce volatility",
        "Reduce drawdown",
        "Improve diversification",
        "Reduce concentration",
        "Improve crisis resilience",
        "Improve return/risk balance",
        "Compare against simple benchmark",
        "Keep current portfolio and monitor",
        "Review data quality",
    }
)

PROBLEM_CLASSIFICATION_V2_VERSION = "problem_classification_v2"
CANDIDATE_LAUNCHPAD_V2_VERSION = "candidate_launchpad_v2"
BLOCK_4_V2_RULESET_VERSION = "block_4_v2_2026_06"

PROBLEM_CLASSIFICATION_V2_IDS = frozenset(
    {
        "high_volatility",
        "high_drawdown",
        "high_equity_beta",
        "high_concentration",
        "poor_diversification",
        "weak_hedge_behavior",
        "poor_rates_up_behavior",
        "weak_crisis_resilience",
        "high_tail_risk",
        "credit_liquidity_fragility",
        "duration_rates_vulnerability",
        "low_return_risk_efficiency",
        "current_portfolio_acceptable",
        "evidence_insufficient_data_quality",
        "evidence_insufficient_conflicting_signals",
    }
)

PROBLEM_CLASSIFICATION_V2_SEVERITY = frozenset({"low", "medium", "high", "unavailable"})
PROBLEM_CLASSIFICATION_V2_STATUS = frozenset({"ok", "partial", "unavailable"})
NO_TRADE_OUTCOMES = frozenset({"proceed_to_launchpad", "monitor", "do_not_act_yet"})
RECOMMENDED_NEXT_STEPS = frozenset(
    {
        "select_launchpad_card",
        "monitor_quarterly",
        "rerun_diagnostics",
        "resolve_data",
    }
)

BLOCK_4_V2_ACTION_PATH_IDS = frozenset(
    {
        "reduce_volatility",
        "reduce_drawdown_risk",
        "improve_diversification",
        "reduce_concentration",
        "improve_crisis_resilience",
        "reduce_equity_beta",
        "reduce_duration_rates_sensitivity",
        "improve_hedge_behavior",
        "reduce_tail_risk",
        "reduce_credit_liquidity_risk",
        "improve_return_risk_balance",
        "compare_against_simple_benchmark",
        "keep_current_portfolio_and_monitor",
        "test_another_candidate",
        "evidence_insufficient_do_not_act_yet",
    }
)

STRESS_CONFIRMATION_VALUES = frozenset(
    {"confirmed", "contradicted", "pre_stress_only", "unavailable"}
)
MATERIALITY_VALUES = frozenset({"high", "medium", "low", "none"})
EVIDENCE_PATH_VALUES = frozenset({"primary", "legacy_fallback", "pre_stress_only"})

LAUNCHPAD_V2_DISCLAIMER_PREFIX = "This card suggests a hypothesis to test, not a buy or sell instruction."


def _validate_evidence_ref(row: Any, prefix: str) -> list[str]:
    violations: list[str] = []
    if not isinstance(row, dict):
        return [f"{prefix}: evidence ref must be an object"]
    for key in (
        "evidence_id",
        "source_block",
        "source_artifact",
        "signal",
        "interpretation_en",
        "why_relevant_to_problem_en",
        "evidence_path",
    ):
        if not str(row.get(key) or "").strip():
            violations.append(f"{prefix}: missing {key}")
    path = str(row.get("evidence_path") or "")
    if path and path not in EVIDENCE_PATH_VALUES:
        violations.append(f"{prefix}: invalid evidence_path {path!r}")
    return violations


def _validate_problem_row_v2(row: Any, prefix: str) -> list[str]:
    violations: list[str] = []
    if not isinstance(row, dict):
        return [f"{prefix}: must be an object"]
    pid = str(row.get("problem_id") or "").strip()
    if not pid:
        violations.append(f"{prefix}: missing problem_id")
    elif pid not in PROBLEM_CLASSIFICATION_V2_IDS:
        violations.append(f"{prefix}: unknown problem_id {pid!r}")
    severity = str(row.get("severity") or "").strip().lower()
    if severity not in PROBLEM_CLASSIFICATION_V2_SEVERITY:
        violations.append(f"{prefix}: invalid severity {row.get('severity')!r}")
    confidence = str(row.get("confidence") or "").strip().lower()
    if confidence not in PROBLEM_CLASSIFICATION_CONFIDENCE:
        violations.append(f"{prefix}: invalid confidence {row.get('confidence')!r}")
    for text_key in ("label_en", "short_diagnosis_en", "why_it_matters_en"):
        if not str(row.get(text_key) or "").strip():
            violations.append(f"{prefix}: missing {text_key}")
    action_id = str(row.get("suggested_action_path_id") or "").strip()
    if not action_id:
        violations.append(f"{prefix}: missing suggested_action_path_id")
    elif action_id not in BLOCK_4_V2_ACTION_PATH_IDS:
        violations.append(f"{prefix}: unknown suggested_action_path_id {action_id!r}")
    evidence_refs = row.get("evidence_refs")
    if not isinstance(evidence_refs, list) or not evidence_refs:
        violations.append(f"{prefix}: must include non-empty evidence_refs[]")
    else:
        for idx, ref in enumerate(evidence_refs):
            violations.extend(_validate_evidence_ref(ref, f"{prefix}.evidence_refs[{idx}]"))
    neg = row.get("negative_evidence_refs")
    if neg is not None and not isinstance(neg, list):
        violations.append(f"{prefix}: negative_evidence_refs must be a list")
    scoring = row.get("scoring")
    if not isinstance(scoring, dict):
        violations.append(f"{prefix}: scoring must be an object")
    else:
        sc = str(scoring.get("stress_confirmation") or "")
        if sc and sc not in STRESS_CONFIRMATION_VALUES:
            violations.append(f"{prefix}: invalid scoring.stress_confirmation {sc!r}")
        mat = str(scoring.get("materiality") or "")
        if mat and mat not in MATERIALITY_VALUES:
            violations.append(f"{prefix}: invalid scoring.materiality {mat!r}")
    paths = row.get("reasonable_paths_to_test")
    if not isinstance(paths, list) or not paths:
        violations.append(f"{prefix}: must include reasonable_paths_to_test[]")
    return violations


def problem_classification_v2_product_contract_violations(
    doc: dict[str, Any] | None,
) -> list[str]:
    """Return Problem Classification v2 product-contract violations (empty = pass)."""
    if not isinstance(doc, dict):
        return [f"{PROBLEM_CLASSIFICATION_V2_VERSION}: document is missing or not an object"]

    prefix = PROBLEM_CLASSIFICATION_V2_VERSION
    violations: list[str] = []

    if doc.get("schema_version") != PROBLEM_CLASSIFICATION_V2_VERSION:
        violations.append(
            f"{prefix}: schema_version expected {PROBLEM_CLASSIFICATION_V2_VERSION!r}, "
            f"got {doc.get('schema_version')!r}"
        )
    if doc.get("diagnostic_only") is not True:
        violations.append(f"{prefix}: diagnostic_only must be true")
    if doc.get("diagnosis_mode") != "current_portfolio_problem_classification":
        violations.append(f"{prefix}: invalid diagnosis_mode")
    if doc.get("ruleset_version") != BLOCK_4_V2_RULESET_VERSION:
        violations.append(
            f"{prefix}: ruleset_version expected {BLOCK_4_V2_RULESET_VERSION!r}, "
            f"got {doc.get('ruleset_version')!r}"
        )
    status = str(doc.get("status") or "")
    if status not in PROBLEM_CLASSIFICATION_V2_STATUS:
        violations.append(f"{prefix}: invalid status {doc.get('status')!r}")

    primary = doc.get("primary_problem")
    violations.extend(_validate_problem_row_v2(primary, f"{prefix}.primary_problem"))

    secondary = doc.get("secondary_problems")
    if not isinstance(secondary, list):
        violations.append(f"{prefix}: secondary_problems must be a list")
        secondary = []
    elif len(secondary) > 2:
        violations.append(f"{prefix}: at most 2 secondary_problems allowed")
    else:
        for idx, row in enumerate(secondary):
            violations.extend(_validate_problem_row_v2(row, f"{prefix}.secondary_problems[{idx}]"))

    rejected = doc.get("rejected_problems")
    if not isinstance(rejected, list):
        violations.append(f"{prefix}: rejected_problems must be a list")

    suggested = doc.get("suggested_actions")
    if not isinstance(suggested, list):
        violations.append(f"{prefix}: suggested_actions must be a list")

    no_trade = doc.get("no_trade_or_monitoring_view")
    if not isinstance(no_trade, dict):
        violations.append(f"{prefix}: no_trade_or_monitoring_view must be an object")
    else:
        outcome = str(no_trade.get("outcome") or "")
        if outcome not in NO_TRADE_OUTCOMES:
            violations.append(f"{prefix}: invalid no_trade outcome {outcome!r}")
        if not str(no_trade.get("headline_en") or "").strip():
            violations.append(f"{prefix}: no_trade headline_en required")
        step = str(no_trade.get("recommended_next_step") or "")
        if step not in RECOMMENDED_NEXT_STEPS:
            violations.append(f"{prefix}: invalid recommended_next_step {step!r}")
        if "launchpad_suppressed" not in no_trade:
            violations.append(f"{prefix}: no_trade launchpad_suppressed required")

    dq = doc.get("data_quality_warnings")
    if not isinstance(dq, list):
        violations.append(f"{prefix}: data_quality_warnings must be a list")

    meta = doc.get("diagnostics_meta")
    if not isinstance(meta, dict):
        violations.append(f"{prefix}: diagnostics_meta must be an object")
    else:
        for key in ("evidence_signal_count", "problems_evaluated", "problems_activated"):
            if key not in meta:
                violations.append(f"{prefix}: diagnostics_meta missing {key}")

    problems = doc.get("problems")
    if not isinstance(problems, list):
        violations.append(f"{prefix}: problems compatibility shim must be a list")
    elif len(problems) > 3:
        violations.append(f"{prefix}: problems shim at most 3 rows")

    summary = doc.get("summary")
    if not isinstance(summary, dict):
        violations.append(f"{prefix}: summary must be an object")
    elif isinstance(primary, dict):
        primary_id = primary.get("problem_id")
        if summary.get("primary_problem_id") != primary_id:
            violations.append(f"{prefix}: summary.primary_problem_id mismatch")
        acceptable = summary.get("current_portfolio_acceptable")
        if acceptable is True and primary_id != "current_portfolio_acceptable":
            violations.append(f"{prefix}: current_portfolio_acceptable inconsistent with primary")
        if isinstance(no_trade, dict) and summary.get("no_trade_outcome") != no_trade.get("outcome"):
            violations.append(f"{prefix}: summary.no_trade_outcome mismatch")

    return violations


def candidate_launchpad_v2_product_contract_violations(
    doc: dict[str, Any] | None,
) -> list[str]:
    """Return Candidate Launchpad v2 product-contract violations (empty = pass)."""
    if not isinstance(doc, dict):
        return [f"{CANDIDATE_LAUNCHPAD_V2_VERSION}: document is missing or not an object"]

    prefix = CANDIDATE_LAUNCHPAD_V2_VERSION
    violations: list[str] = []

    if doc.get("schema_version") != CANDIDATE_LAUNCHPAD_V2_VERSION:
        violations.append(
            f"{prefix}: schema_version expected {CANDIDATE_LAUNCHPAD_V2_VERSION!r}, "
            f"got {doc.get('schema_version')!r}"
        )
    if doc.get("diagnostic_only") is not True:
        violations.append(f"{prefix}: diagnostic_only must be true")
    if doc.get("ruleset_version") != BLOCK_4_V2_RULESET_VERSION:
        violations.append(
            f"{prefix}: ruleset_version expected {BLOCK_4_V2_RULESET_VERSION!r}, "
            f"got {doc.get('ruleset_version')!r}"
        )
    outcome = str(doc.get("launchpad_outcome") or "")
    if outcome not in NO_TRADE_OUTCOMES:
        violations.append(f"{prefix}: invalid launchpad_outcome {outcome!r}")

    cards = doc.get("cards")
    if not isinstance(cards, list):
        violations.append(f"{prefix}: cards must be a list")
        return violations
    if len(cards) > 4:
        violations.append(f"{prefix}: at most 4 cards allowed")
    if not cards and outcome != "do_not_act_yet":
        violations.append(f"{prefix}: cards must be non-empty unless do_not_act_yet")

    card_ids: list[str] = []
    for idx, card in enumerate(cards):
        cp = f"{prefix}.cards[{idx}]"
        if not isinstance(card, dict):
            violations.append(f"{cp}: must be an object")
            continue
        card_id = str(card.get("card_id") or "").strip()
        if not card_id:
            violations.append(f"{cp}: missing card_id")
        else:
            card_ids.append(card_id)
        for key in (
            "title",
            "goal",
            "description",
            "why_this_path_en",
            "what_this_tests_en",
            "expected_tradeoff_to_check_en",
            "when_to_skip_this_test_en",
        ):
            if not str(card.get(key) or "").strip():
                violations.append(f"{cp}: missing {key}")
        disclaimer = str(card.get("not_a_recommendation_disclaimer_en") or "")
        if not disclaimer.startswith(LAUNCHPAD_V2_DISCLAIMER_PREFIX):
            violations.append(f"{cp}: invalid not_a_recommendation_disclaimer_en")
        if card.get("generates_portfolio") is not False:
            violations.append(f"{cp}: generates_portfolio must be false")
        if "weights" in card:
            violations.append(f"{cp}: must not include weights")
        if "priority_rank" not in card:
            violations.append(f"{cp}: missing priority_rank")
        methods = card.get("suggested_methods")
        if not isinstance(methods, list):
            violations.append(f"{cp}: suggested_methods must be a list")
        else:
            method_ids = []
            for midx, method in enumerate(methods):
                if not isinstance(method, dict):
                    violations.append(f"{cp}.suggested_methods[{midx}] must be an object")
                    continue
                method_id = str(method.get("candidate_method_id") or "").strip()
                if not method_id:
                    violations.append(f"{cp}.suggested_methods[{midx}] missing candidate_method_id")
                elif method_id not in LAUNCHPAD_KNOWN_METHOD_IDS:
                    violations.append(f"{cp}: unknown candidate_method_id {method_id!r}")
                else:
                    method_ids.append(method_id)
            default_method = card.get("default_method")
            if method_ids and not default_method:
                violations.append(f"{cp}: default_method required when suggested_methods non-empty")
            if default_method and str(default_method) not in method_ids:
                violations.append(f"{cp}: default_method must appear in suggested_methods")
        constraints = card.get("simple_constraints")
        if not isinstance(constraints, list):
            violations.append(f"{cp}: simple_constraints must be a list")

    summary = doc.get("summary")
    if not isinstance(summary, dict):
        violations.append(f"{prefix}: summary must be an object")
    else:
        if summary.get("n_cards") != len(cards):
            violations.append(f"{prefix}: summary.n_cards mismatch")
        if summary.get("launchpad_outcome") != outcome:
            violations.append(f"{prefix}: summary.launchpad_outcome mismatch")
        primary = summary.get("primary_card_id")
        if primary is not None and card_ids and str(primary) != card_ids[0]:
            violations.append(f"{prefix}: summary.primary_card_id must match first card")

    return violations


def block_4_v2_diagnosis_handoff_violations(
    problem_classification: dict[str, Any] | None,
    candidate_launchpad: dict[str, Any] | None,
) -> list[str]:
    """Cross-artifact Block 4 v2 handoff."""
    if not isinstance(problem_classification, dict) or not isinstance(candidate_launchpad, dict):
        return ["block_4_v2_handoff: both artifacts required"]

    violations: list[str] = []
    prefix = "block_4_v2_handoff"

    if problem_classification.get("schema_version") != PROBLEM_CLASSIFICATION_V2_VERSION:
        violations.append(f"{prefix}: problem_classification must be v2")
    if candidate_launchpad.get("schema_version") != CANDIDATE_LAUNCHPAD_V2_VERSION:
        violations.append(f"{prefix}: candidate_launchpad must be v2")

    pc_end = problem_classification.get("analysis_end")
    lp_end = candidate_launchpad.get("analysis_end")
    if pc_end and lp_end and str(pc_end) != str(lp_end):
        violations.append(f"{prefix}: analysis_end mismatch")

    primary = problem_classification.get("primary_problem")
    primary = primary if isinstance(primary, dict) else {}
    secondary = problem_classification.get("secondary_problems")
    secondary = secondary if isinstance(secondary, list) else []
    allowed_ids = {str(primary.get("problem_id"))} if primary.get("problem_id") else set()
    allowed_ids.update(
        str(row.get("problem_id"))
        for row in secondary
        if isinstance(row, dict) and row.get("problem_id")
    )

    no_trade = problem_classification.get("no_trade_or_monitoring_view") or {}
    pc_outcome = no_trade.get("outcome") if isinstance(no_trade, dict) else None
    if candidate_launchpad.get("launchpad_outcome") != pc_outcome:
        violations.append(f"{prefix}: launchpad_outcome mismatch with PC no_trade outcome")

    for idx, card in enumerate(candidate_launchpad.get("cards") or []):
        if not isinstance(card, dict):
            continue
        source_id = card.get("source_problem_id")
        if source_id is None:
            continue
        if str(source_id) not in allowed_ids:
            violations.append(
                f"{prefix}: cards[{idx}] source_problem_id {source_id!r} not in primary/secondary"
            )

    return violations


def check_problem_classification_v2(doc: dict[str, Any] | None) -> dict[str, Any]:
    violations = problem_classification_v2_product_contract_violations(doc)
    summary = (doc or {}).get("summary") if isinstance(doc, dict) else {}
    summary = summary if isinstance(summary, dict) else {}
    primary = (doc or {}).get("primary_problem") if isinstance(doc, dict) else {}
    primary = primary if isinstance(primary, dict) else {}
    return {
        "product_contract_ok": not violations,
        "contract_violations": violations,
        "primary_problem_id": primary.get("problem_id") or summary.get("primary_problem_id"),
        "no_trade_outcome": summary.get("no_trade_outcome"),
        "n_secondary": summary.get("n_secondary"),
        "n_rejected": summary.get("n_rejected"),
    }


def check_candidate_launchpad_v2(doc: dict[str, Any] | None) -> dict[str, Any]:
    violations = candidate_launchpad_v2_product_contract_violations(doc)
    cards = (doc or {}).get("cards") if isinstance(doc, dict) else []
    cards = cards if isinstance(cards, list) else []
    summary = (doc or {}).get("summary") if isinstance(doc, dict) else {}
    summary = summary if isinstance(summary, dict) else {}
    return {
        "product_contract_ok": not violations,
        "contract_violations": violations,
        "n_cards": len(cards),
        "launchpad_outcome": (doc or {}).get("launchpad_outcome") if isinstance(doc, dict) else None,
        "primary_card_id": summary.get("primary_card_id"),
    }


def check_block_4_v2_diagnosis_handoff(
    problem_classification: dict[str, Any] | None,
    candidate_launchpad: dict[str, Any] | None,
) -> dict[str, Any]:
    violations = block_4_v2_diagnosis_handoff_violations(
        problem_classification, candidate_launchpad
    )
    return {
        "handoff_ok": not violations,
        "contract_violations": violations,
    }


# ---------------------------------------------------------------------------
# Block 5 — Current vs Candidate + Decision Verdict (compare path)
# ---------------------------------------------------------------------------

CURRENT_VS_CANDIDATE_VERSION = "current_vs_candidate_v1"
DECISION_VERDICT_VERSION = "decision_verdict_v1"

CURRENT_VS_VIEW_MODES = frozenset({"diagnosis_only", "one_candidate", "shortlist"})

SELECTION_DECISION_STATUSES = frozenset(
    {
        "selected_candidate",
        "no_material_rebalance",
        "inconclusive",
        "data_review_required",
        "mandate_risk_reduction",
    }
)

DECISION_VERDICT_IDS = frozenset(
    {
        "rebalance_to_selected_candidate",
        "no_material_rebalance_recommended",
        "test_another_candidate_or_review_evidence",
        "evidence_insufficient",
        "risk_reduction_required",
    }
)

DECISION_VERDICT_FAMILIES = frozenset({"core_compare", "policy_mandate"})

DECISION_CONFIDENCE_VALUES = frozenset({"low", "medium", "high"})

_STATUS_TO_VERDICT_ID: dict[str, str] = {
    "selected_candidate": "rebalance_to_selected_candidate",
    "no_material_rebalance": "no_material_rebalance_recommended",
    "inconclusive": "test_another_candidate_or_review_evidence",
    "data_review_required": "evidence_insufficient",
    "mandate_risk_reduction": "risk_reduction_required",
}

_STATUS_TO_VERDICT_FAMILY: dict[str, str] = {
    "selected_candidate": "core_compare",
    "no_material_rebalance": "core_compare",
    "inconclusive": "core_compare",
    "data_review_required": "core_compare",
    "mandate_risk_reduction": "policy_mandate",
}


def _is_no_candidate_tombstone(doc: dict[str, Any] | None) -> bool:
    return isinstance(doc, dict) and doc.get("tombstone") == "no_candidate_v1"


def current_vs_candidate_v1_product_contract_violations(
    doc: dict[str, Any] | None,
) -> list[str]:
    """Return Current vs Candidate v1 product-contract violations (empty = pass)."""
    if not isinstance(doc, dict):
        return [f"{CURRENT_VS_CANDIDATE_VERSION}: document is missing or not an object"]
    if _is_no_candidate_tombstone(doc):
        return [f"{CURRENT_VS_CANDIDATE_VERSION}: tombstone artifact is not a live compare output"]

    prefix = CURRENT_VS_CANDIDATE_VERSION
    violations: list[str] = []

    if doc.get("schema_version") != CURRENT_VS_CANDIDATE_VERSION:
        violations.append(
            f"{prefix}: schema_version expected {CURRENT_VS_CANDIDATE_VERSION!r}, "
            f"got {doc.get('schema_version')!r}"
        )
    if doc.get("diagnostic_only") is not True:
        violations.append(f"{prefix}: diagnostic_only must be true")

    view_mode = str(doc.get("view_mode") or "").strip()
    if view_mode not in CURRENT_VS_VIEW_MODES:
        violations.append(f"{prefix}: invalid view_mode {doc.get('view_mode')!r}")

    selected = doc.get("selected_candidate_ids")
    if not isinstance(selected, list):
        violations.append(f"{prefix}: selected_candidate_ids must be a list")
        selected = []

    comparisons = doc.get("comparisons")
    if not isinstance(comparisons, list):
        violations.append(f"{prefix}: comparisons must be a list")
        comparisons = []

    baseline = doc.get("baseline")
    if not isinstance(baseline, dict):
        violations.append(f"{prefix}: baseline must be an object")

    if view_mode == "one_candidate":
        if len(selected) != 1:
            violations.append(
                f"{prefix}: view_mode one_candidate requires exactly one selected_candidate_id"
            )
        if len(comparisons) != 1:
            violations.append(
                f"{prefix}: view_mode one_candidate requires exactly one comparisons[] row"
            )
        elif selected and comparisons[0].get("candidate_id") != selected[0]:
            violations.append(
                f"{prefix}: comparisons[0].candidate_id must match selected_candidate_ids[0]"
            )
    elif view_mode == "shortlist":
        if len(selected) < 2:
            violations.append(
                f"{prefix}: view_mode shortlist requires at least two selected_candidate_ids"
            )
        if len(comparisons) < 2:
            violations.append(f"{prefix}: view_mode shortlist requires at least two comparisons[] rows")
    elif view_mode == "diagnosis_only":
        if selected:
            violations.append(f"{prefix}: diagnosis_only view_mode must have empty selected_candidate_ids")
        if comparisons:
            violations.append(f"{prefix}: diagnosis_only view_mode must have empty comparisons[]")

    for idx, row in enumerate(comparisons):
        if not isinstance(row, dict):
            violations.append(f"{prefix}: comparisons[{idx}] must be an object")
            continue
        if not row.get("candidate_id"):
            violations.append(f"{prefix}: comparisons[{idx}] missing candidate_id")
        dimensions = row.get("dimensions")
        if not isinstance(dimensions, list) or not dimensions:
            violations.append(f"{prefix}: comparisons[{idx}] must include dimensions[]")
        else:
            for didx, dim in enumerate(dimensions):
                if not isinstance(dim, dict):
                    violations.append(
                        f"{prefix}: comparisons[{idx}].dimensions[{didx}] must be an object"
                    )
                    continue
                if not dim.get("field") or not dim.get("label"):
                    violations.append(
                        f"{prefix}: comparisons[{idx}].dimensions[{didx}] missing field or label"
                    )
                if dim.get("direction") not in {"improved", "worse", "flat", "unknown"}:
                    violations.append(
                        f"{prefix}: comparisons[{idx}].dimensions[{didx}] invalid direction"
                    )

    source = doc.get("source_artifacts") or {}
    if source.get("candidate_comparison") != "candidate_comparison.json":
        violations.append(
            f"{prefix}: source_artifacts.candidate_comparison must be candidate_comparison.json"
        )

    return violations


def decision_verdict_v1_product_contract_violations(
    doc: dict[str, Any] | None,
) -> list[str]:
    """Return Decision Verdict v1 product-contract violations (empty = pass)."""
    if not isinstance(doc, dict):
        return [f"{DECISION_VERDICT_VERSION}: document is missing or not an object"]
    if _is_no_candidate_tombstone(doc):
        return [f"{DECISION_VERDICT_VERSION}: tombstone artifact is not a live verdict output"]

    prefix = DECISION_VERDICT_VERSION
    violations: list[str] = []

    if doc.get("schema_version") != DECISION_VERDICT_VERSION:
        violations.append(
            f"{prefix}: schema_version expected {DECISION_VERDICT_VERSION!r}, "
            f"got {doc.get('schema_version')!r}"
        )
    if doc.get("diagnostic_only") is not False:
        violations.append(f"{prefix}: diagnostic_only must be false")

    status = str(doc.get("selection_decision_status") or "").strip()
    if status not in SELECTION_DECISION_STATUSES:
        violations.append(f"{prefix}: invalid selection_decision_status {status!r}")

    verdict_id = str(doc.get("verdict_id") or "").strip()
    if verdict_id not in DECISION_VERDICT_IDS:
        violations.append(f"{prefix}: invalid verdict_id {verdict_id!r}")
    elif status in _STATUS_TO_VERDICT_ID and verdict_id != _STATUS_TO_VERDICT_ID[status]:
        violations.append(
            f"{prefix}: verdict_id {verdict_id!r} inconsistent with selection_decision_status {status!r}"
        )

    family = str(doc.get("verdict_family") or "").strip()
    if family not in DECISION_VERDICT_FAMILIES:
        violations.append(f"{prefix}: invalid verdict_family {family!r}")
    elif status in _STATUS_TO_VERDICT_FAMILY and family != _STATUS_TO_VERDICT_FAMILY[status]:
        violations.append(
            f"{prefix}: verdict_family {family!r} inconsistent with selection_decision_status {status!r}"
        )

    confidence = str(doc.get("confidence") or "").strip().lower()
    if confidence not in DECISION_CONFIDENCE_VALUES:
        violations.append(f"{prefix}: invalid confidence {doc.get('confidence')!r}")

    if not isinstance(doc.get("verdict_label"), str) or not str(doc.get("verdict_label")).strip():
        violations.append(f"{prefix}: verdict_label must be non-empty")

    guardrails = doc.get("guardrails")
    if not isinstance(guardrails, dict):
        violations.append(f"{prefix}: guardrails must be an object")
    else:
        for key in (
            "does_not_rename_selection_engine_contract",
            "does_not_change_selection_formulas",
            "does_not_execute_trades",
        ):
            if guardrails.get(key) is not True:
                violations.append(f"{prefix}: guardrails.{key} must be true")

    no_trade = doc.get("no_trade")
    if not isinstance(no_trade, dict):
        violations.append(f"{prefix}: no_trade must be an object")

    return violations


def block_5_compare_handoff_violations(
    comparison: dict[str, Any] | None,
    current_vs_candidate: dict[str, Any] | None,
    decision_verdict: dict[str, Any] | None,
    *,
    selection: dict[str, Any] | None = None,
) -> list[str]:
    """Cross-artifact Block 5 handoff: comparison → current_vs_candidate → decision_verdict."""
    if not isinstance(comparison, dict):
        return ["block_5_handoff: candidate_comparison required"]
    if not isinstance(current_vs_candidate, dict) or not isinstance(decision_verdict, dict):
        return ["block_5_handoff: current_vs_candidate and decision_verdict required"]
    if _is_no_candidate_tombstone(comparison) or _is_no_candidate_tombstone(current_vs_candidate):
        return ["block_5_handoff: tombstone artifacts cannot form compare handoff"]
    if _is_no_candidate_tombstone(decision_verdict):
        return ["block_5_handoff: decision_verdict tombstone cannot form compare handoff"]

    violations: list[str] = []
    prefix = "block_5_handoff"

    scope = comparison.get("product_candidate_scope") or {}
    scope_ids = {
        str(cid)
        for cid in (scope.get("candidate_ids") or [])
        if str(cid).strip()
    }
    selected = [
        str(cid) for cid in (current_vs_candidate.get("selected_candidate_ids") or []) if str(cid).strip()
    ]
    if scope_ids and selected and any(cid not in scope_ids for cid in selected):
        violations.append(
            f"{prefix}: selected_candidate_ids {selected!r} outside product_candidate_scope"
        )

    view_mode = str(current_vs_candidate.get("view_mode") or "")
    if view_mode not in {"one_candidate", "shortlist"}:
        violations.append(
            f"{prefix}: product compare path requires view_mode one_candidate or shortlist"
        )

    verdict_selected = decision_verdict.get("selected_candidate_id")
    if selected and verdict_selected is not None and str(verdict_selected) not in selected:
        violations.append(
            f"{prefix}: decision_verdict.selected_candidate_id {verdict_selected!r} "
            f"not in current_vs_candidate.selected_candidate_ids"
        )

    baseline_cvc = (current_vs_candidate.get("baseline") or {}).get("candidate_id")
    baseline_verdict = decision_verdict.get("baseline_candidate_id")
    if baseline_cvc and baseline_verdict and str(baseline_cvc) != str(baseline_verdict):
        violations.append(
            f"{prefix}: baseline mismatch ({baseline_cvc!r} vs {baseline_verdict!r})"
        )

    comparison_end = comparison.get("analysis_end")
    cvc_end = current_vs_candidate.get("analysis_end")
    if comparison_end and cvc_end and str(comparison_end) != str(cvc_end):
        violations.append(
            f"{prefix}: analysis_end mismatch comparison vs current_vs_candidate"
        )

    if isinstance(selection, dict):
        favored = selection.get("favored_candidate_id")
        if favored and verdict_selected and str(favored) != str(verdict_selected):
            violations.append(
                f"{prefix}: selection.favored_candidate_id {favored!r} "
                f"!= decision_verdict.selected_candidate_id {verdict_selected!r}"
            )

    verdict_sources = decision_verdict.get("source_artifacts") or {}
    if verdict_sources.get("current_vs_candidate") != "current_vs_candidate.json":
        violations.append(
            f"{prefix}: decision_verdict.source_artifacts.current_vs_candidate must be set"
        )

    return violations


def check_current_vs_candidate_v1(doc: dict[str, Any] | None) -> dict[str, Any]:
    violations = current_vs_candidate_v1_product_contract_violations(doc)
    return {
        "product_contract_ok": not violations,
        "contract_violations": violations,
        "view_mode": (doc or {}).get("view_mode") if isinstance(doc, dict) else None,
        "n_comparisons": len((doc or {}).get("comparisons") or [])
        if isinstance(doc, dict) and isinstance(doc.get("comparisons"), list)
        else 0,
        "selected_candidate_ids": list((doc or {}).get("selected_candidate_ids") or [])
        if isinstance(doc, dict)
        else [],
    }


def check_decision_verdict_v1(doc: dict[str, Any] | None) -> dict[str, Any]:
    violations = decision_verdict_v1_product_contract_violations(doc)
    return {
        "product_contract_ok": not violations,
        "contract_violations": violations,
        "verdict_id": (doc or {}).get("verdict_id") if isinstance(doc, dict) else None,
        "verdict_family": (doc or {}).get("verdict_family") if isinstance(doc, dict) else None,
        "selection_decision_status": (doc or {}).get("selection_decision_status")
        if isinstance(doc, dict)
        else None,
        "confidence": (doc or {}).get("confidence") if isinstance(doc, dict) else None,
    }


def check_block_5_compare_handoff(
    comparison: dict[str, Any] | None,
    current_vs_candidate: dict[str, Any] | None,
    decision_verdict: dict[str, Any] | None,
    *,
    selection: dict[str, Any] | None = None,
) -> dict[str, Any]:
    violations = block_5_compare_handoff_violations(
        comparison, current_vs_candidate, decision_verdict, selection=selection
    )
    return {
        "handoff_ok": not violations,
        "contract_violations": violations,
    }
