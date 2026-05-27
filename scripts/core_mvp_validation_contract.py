"""
Shared Core MVP fixture-matrix validation contract (Steps 4–6).

Distinguishes required Core MVP product fields from optional diagnostics so
aggregating validators do not mark fixtures partial for advanced/optional gaps only.
"""
from __future__ import annotations

from typing import Any

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
