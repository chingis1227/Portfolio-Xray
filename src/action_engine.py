"""
Action Engine and Rebalancing Advisor (non-executing implementation plan).

See docs/specs/action_engine_spec.md.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.config_schema import PortfolioConfig
from src.rebalance import compute_trades
from src.selection_engine import (
    _drawdown_improvement_pp,
    _resolve_weights,
    _turnover_half_sum_pct,
)

SCHEMA_VERSION = "action_plan_v1"
TRANSACTION_COST_BPS = 10
TRANSACTION_COST_MODEL = "bps_on_turnover_half_sum"
PRIORITY_TRADE_LIMIT = 5
ELIGIBLE_STATUSES = frozenset({"available", "degraded"})


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else None
    except (OSError, json.JSONDecodeError):
        return None


def _candidates_by_id(comparison: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {c["candidate_id"]: c for c in comparison.get("candidates", []) if c.get("candidate_id")}


def _weight_deltas(
    w_current: dict[str, float],
    w_target: dict[str, float],
) -> list[dict[str, Any]]:
    keys = sorted(set(w_current) | set(w_target))
    rows: list[dict[str, Any]] = []
    for ticker in keys:
        cw = float(w_current.get(ticker, 0.0))
        tw = float(w_target.get(ticker, 0.0))
        dw = tw - cw
        rows.append(
            {
                "ticker": ticker,
                "current_weight": round(cw, 6),
                "target_weight": round(tw, 6),
                "delta_weight": round(dw, 6),
                "delta_pct": round(dw * 100.0, 3),
            }
        )
    rows.sort(key=lambda r: abs(r["delta_pct"]), reverse=True)
    return rows


def _trade_rows(trades: list[Any]) -> list[dict[str, Any]]:
    return [
        {
            "ticker": t.ticker,
            "direction": t.direction,
            "delta_weight": round(t.delta_weight, 6),
            "delta_pct": round(t.delta_pct, 3),
        }
        for t in trades
    ]


def _priority_trades(trades: list[dict[str, Any]], limit: int = PRIORITY_TRADE_LIMIT) -> list[dict[str, Any]]:
    ordered = sorted(trades, key=lambda t: abs(t.get("delta_pct") or 0.0), reverse=True)
    return ordered[:limit]


def _estimated_transaction_cost_pct(turnover_half_sum_pct: float | None) -> float | None:
    if turnover_half_sum_pct is None:
        return None
    return round(turnover_half_sum_pct * TRANSACTION_COST_BPS / 10000.0, 4)


def _risk_improvement_per_turnover(
    drawdown_improvement_pp: float | None,
    turnover_half_sum_pct: float | None,
) -> float | None:
    if (
        drawdown_improvement_pp is None
        or turnover_half_sum_pct is None
        or turnover_half_sum_pct <= 0
    ):
        return None
    return round(drawdown_improvement_pp / turnover_half_sum_pct, 4)


def _no_trades_reason(
    *,
    decision_status: str,
    action_status: str,
    selection_summary: str | None,
    no_trade_summary: str | None,
    workflow_status: dict[str, Any] | None = None,
) -> str:
    if workflow_status and not workflow_status.get("no_trade_actionable"):
        skip_msg = workflow_status.get("user_message_en")
        if skip_msg:
            return str(skip_msg)
    if decision_status == "no_material_rebalance":
        if workflow_status and not workflow_status.get("no_trade_actionable"):
            return (
                workflow_status.get("user_message_en")
                or "No-Trade versus current was not evaluated for this workflow."
            )
        base = no_trade_summary or "No material rebalance suggested versus current weights."
        return f"{base} Trade list omitted per Selection Engine outcome."
    if decision_status == "mandate_risk_reduction":
        return (
            selection_summary
            or "Mandate constraints require risk reduction before allocation changes."
        )
    if decision_status == "inconclusive":
        return selection_summary or "Selection inconclusive; no implementation plan proposed."
    if decision_status == "data_review_required":
        return selection_summary or "Score or comparison inputs require review before action planning."
    if action_status == "trades_skipped_missing_weights":
        return "Weight vectors for current or target profile could not be loaded from snapshots."
    if action_status == "advisory_only":
        return "No favored target profile on selection artifact; weights shown for reference only."
    if decision_status == "selected_candidate" and action_status == "trades_for_review":
        return "Review trade rows below; this is not an execution instruction."
    return selection_summary or "No trades listed for this selection outcome."


def build_action_plan(
    comparison: dict[str, Any],
    selection: dict[str, Any],
    *,
    project_root: Path,
    min_trade_pct: float | None = None,
    workflow_status: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build action_plan_v1 from comparison and selection artifacts."""
    warnings: list[str] = []
    by_id = _candidates_by_id(comparison)
    decision_status = str(selection.get("decision_status") or "inconclusive")
    favored_id = selection.get("favored_candidate_id")
    favored_display = selection.get("favored_display_name")

    current = by_id.get("current")
    target = by_id.get(favored_id) if favored_id else None

    w_current: dict[str, float] | None = None
    w_target: dict[str, float] | None = None
    if current and current.get("status") in ELIGIBLE_STATUSES:
        w_current = _resolve_weights(current, project_root=project_root)
    if target and target.get("status") in ELIGIBLE_STATUSES:
        w_target = _resolve_weights(target, project_root=project_root)

    turnover: float | None = None
    weight_delta_rows: list[dict[str, Any]] = []
    if w_current and w_target:
        turnover = _turnover_half_sum_pct(w_target, w_current)
        weight_delta_rows = _weight_deltas(w_current, w_target)

    no_trade_block = selection.get("no_trade") or {}
    health_delta = no_trade_block.get("health_score_delta")
    robust_delta = no_trade_block.get("robustness_score_delta")
    dd_improvement = no_trade_block.get("drawdown_improvement_pp")
    if target and current and dd_improvement is None:
        dd_improvement = _drawdown_improvement_pp(target, current)

    risk_context: dict[str, Any] = {
        "health_score_delta": health_delta,
        "robustness_score_delta": robust_delta,
        "drawdown_improvement_pp": dd_improvement,
        "turnover_half_sum_pct": turnover,
        "risk_improvement_per_one_pct_turnover": _risk_improvement_per_turnover(
            dd_improvement if isinstance(dd_improvement, (int, float)) else None,
            turnover,
        ),
    }

    trades: list[dict[str, Any]] = []
    action_status: str

    if decision_status == "no_material_rebalance":
        action_status = "no_trades_no_material_rebalance"
    elif decision_status in (
        "inconclusive",
        "data_review_required",
        "mandate_risk_reduction",
    ):
        action_status = "no_trades_other"
    elif favored_id is None:
        action_status = "advisory_only"
    elif decision_status == "selected_candidate":
        if w_current and w_target:
            raw_trades, _ = compute_trades(
                w_current,
                w_target,
                min_trade_pct=min_trade_pct,
            )
            trades = _trade_rows(raw_trades)
            action_status = "trades_for_review"
        else:
            action_status = "trades_skipped_missing_weights"
            warnings.append("action_missing_weight_vectors")
    else:
        action_status = "no_trades_other"

    rationale = selection.get("rationale") or {}
    no_trades_reason = _no_trades_reason(
        decision_status=decision_status,
        action_status=action_status,
        selection_summary=rationale.get("summary"),
        no_trade_summary=no_trade_block.get("summary"),
        workflow_status=workflow_status,
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "non_executing": True,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "analysis_end": comparison.get("analysis_end"),
        "investor_currency": comparison.get("investor_currency"),
        "output_dir_final": comparison.get("output_dir_final"),
        "action_status": action_status,
        "selection_decision_status": decision_status,
        "baseline_candidate_id": "current" if current else None,
        "target_candidate_id": favored_id,
        "target_display_name": favored_display,
        "current_weights": w_current,
        "target_weights": w_target,
        "weight_deltas": weight_delta_rows,
        "trades": trades,
        "no_trades_reason": no_trades_reason,
        "turnover_half_sum_pct": turnover,
        "transaction_cost_bps": TRANSACTION_COST_BPS,
        "transaction_cost_model": TRANSACTION_COST_MODEL,
        "estimated_transaction_cost_pct": _estimated_transaction_cost_pct(turnover),
        "risk_context": risk_context,
        "priority_trades": _priority_trades(trades),
        "warnings": sorted(set(warnings)),
        "input_artifacts": {
            "candidate_comparison": "candidate_comparison.json",
            "selection_decision": "selection_decision.json",
        },
    }


def write_action_plan_txt(plan: dict[str, Any], path: Path) -> None:
    """Compact English summary for Rebalancing Advisor."""
    lines = [
        "Action plan (non-executing) — Rebalancing Advisor",
        f"Status: {plan.get('action_status')}",
        f"Selection: {plan.get('selection_decision_status')}",
    ]
    if plan.get("target_display_name"):
        lines.append(f"Target profile: {plan['target_display_name']}")
    if plan.get("turnover_half_sum_pct") is not None:
        lines.append(f"Turnover (half-sum): {plan['turnover_half_sum_pct']}%")
    cost = plan.get("estimated_transaction_cost_pct")
    if cost is not None:
        lines.append(
            f"Estimated transaction cost ({plan.get('transaction_cost_bps')} bps on turnover): "
            f"{cost}% of portfolio"
        )
    rc = plan.get("risk_context") or {}
    if rc.get("drawdown_improvement_pp") is not None:
        lines.append(f"Max drawdown change (pp): {rc['drawdown_improvement_pp']}")
    rip = rc.get("risk_improvement_per_one_pct_turnover")
    if rip is not None:
        lines.append(f"Drawdown improvement per 1% turnover (pp): {rip}")

    lines.append("")
    lines.append(plan.get("no_trades_reason") or "")

    trade_rows = plan.get("trades") or []
    if trade_rows:
        lines.append("")
        lines.append("Trades for review (not execution instructions):")
        for t in trade_rows[:15]:
            lines.append(
                f"  {t.get('ticker')} {t.get('direction')} "
                f"Δw={t.get('delta_weight')} ({t.get('delta_pct')}%)"
            )
        if len(trade_rows) > 15:
            lines.append(f"  ... and {len(trade_rows) - 15} more in action_plan.json")

    lines.append("")
    lines.append("See action_plan.json for full weight deltas and priority ordering.")
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def write_action_plan_outputs(
    cfg: PortfolioConfig,
    *,
    project_root: Path | None = None,
    comparison: dict[str, Any] | None = None,
    selection: dict[str, Any] | None = None,
    workflow_status: dict[str, Any] | None = None,
    write_txt: bool = True,
) -> dict[str, Path]:
    """Write action_plan.json when selection and comparison exist."""
    project_root = project_root or Path.cwd()
    out_dir = project_root / str(getattr(cfg, "output_dir_final", "Main portfolio"))

    if comparison is None:
        comparison = _load_json(out_dir / "candidate_comparison.json")
    if selection is None:
        selection = _load_json(out_dir / "selection_decision.json")

    if not comparison or not selection:
        return {}

    if workflow_status is None:
        workflow_status = _load_json(out_dir / "current_vs_policy_status.json")

    plan = build_action_plan(
        comparison,
        selection,
        project_root=project_root,
        workflow_status=workflow_status,
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    json_out = out_dir / "action_plan.json"
    with open(json_out, "w", encoding="utf-8") as f:
        json.dump(plan, f, indent=2, ensure_ascii=False)
    paths["action_plan_json"] = json_out

    if write_txt:
        txt_out = out_dir / "action_plan.txt"
        write_action_plan_txt(plan, txt_out)
        paths["action_plan_txt"] = txt_out

    return paths


__all__ = [
    "SCHEMA_VERSION",
    "TRANSACTION_COST_BPS",
    "build_action_plan",
    "write_action_plan_outputs",
    "write_action_plan_txt",
]
