"""
Assumption Sensitivity — variant-grid stability of selection and evidence ranks.

See docs/specs/assumption_sensitivity_spec.md.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.config_schema import PortfolioConfig
from src.selection_engine import (
    ELIGIBLE_STATUSES,
    _composite_row,
    _composite_sort_key,
    _finite,
    _load_json,
    _mandate_component,
    _score_maps,
)

SCHEMA_VERSION = "assumption_sensitivity_v1"

TIER_A_CATALOG: tuple[dict[str, Any], ...] = (
    {
        "variant_id": "baseline_selection",
        "w_health": 0.45,
        "w_robust": 0.45,
        "w_mandate": 0.10,
        "apply_policy_default": True,
    },
    {
        "variant_id": "health_heavy",
        "w_health": 0.55,
        "w_robust": 0.35,
        "w_mandate": 0.10,
        "apply_policy_default": True,
    },
    {
        "variant_id": "robust_heavy",
        "w_health": 0.35,
        "w_robust": 0.55,
        "w_mandate": 0.10,
        "apply_policy_default": True,
    },
    {
        "variant_id": "health_dominant",
        "w_health": 0.60,
        "w_robust": 0.30,
        "w_mandate": 0.10,
        "apply_policy_default": True,
    },
    {
        "variant_id": "robust_dominant",
        "w_health": 0.30,
        "w_robust": 0.60,
        "w_mandate": 0.10,
        "apply_policy_default": True,
    },
    {
        "variant_id": "health_only_proxy",
        "w_health": 0.90,
        "w_robust": 0.00,
        "w_mandate": 0.10,
        "apply_policy_default": True,
    },
    {
        "variant_id": "robust_only_proxy",
        "w_health": 0.00,
        "w_robust": 0.90,
        "w_mandate": 0.10,
        "apply_policy_default": True,
    },
    {
        "variant_id": "composite_only_no_policy_default",
        "w_health": 0.45,
        "w_robust": 0.45,
        "w_mandate": 0.10,
        "apply_policy_default": False,
    },
)

TIER_B_CATALOG: tuple[dict[str, str], ...] = (
    {"variant_id": "sharpe_rank_3y", "window": "3y", "kind": "sharpe"},
    {"variant_id": "sharpe_rank_5y", "window": "5y", "kind": "sharpe"},
    {"variant_id": "sharpe_rank_10y", "window": "10y", "kind": "sharpe"},
    {"variant_id": "stress_worst_loss_rank", "window": "", "kind": "stress_worst_loss"},
)

_STABILITY_BANDS = (
    ("stable", 0.80),
    ("moderate", 0.60),
    ("fragile", 0.0),
)


def _candidates_by_id(comparison: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {c["candidate_id"]: c for c in comparison.get("candidates", []) if c.get("candidate_id")}


def _weights_dict(spec: dict[str, Any]) -> dict[str, float]:
    return {
        "w_health": float(spec["w_health"]),
        "w_robust": float(spec["w_robust"]),
        "w_mandate": float(spec["w_mandate"]),
    }


def _rank_composite(
    by_id: dict[str, dict[str, Any]],
    health_by_id: dict[str, dict[str, Any]],
    robust_by_id: dict[str, dict[str, Any]],
    weights: dict[str, float],
) -> list[dict[str, Any]]:
    composite: list[dict[str, Any]] = []
    for cid, cand in by_id.items():
        row = _composite_row(
            cand,
            health_row=health_by_id.get(cid),
            robust_row=robust_by_id.get(cid),
            weights=weights,
        )
        if row:
            composite.append(row)
    composite.sort(key=_composite_sort_key)
    return composite


def _effective_favored(
    by_id: dict[str, dict[str, Any]],
    composite: list[dict[str, Any]],
    *,
    apply_policy_default: bool,
) -> tuple[str | None, str | None]:
    policy = by_id.get("policy")
    if apply_policy_default and policy and policy.get("status") in ELIGIBLE_STATUSES:
        mandate_pts, _ = _mandate_component(policy)
        if mandate_pts > 0:
            return "policy", str(policy.get("display_name", "Policy Portfolio"))
    if composite:
        winner = composite[0]
        return str(winner["candidate_id"]), str(winner.get("display_name", winner["candidate_id"]))
    return None, None


def _worst_scenario_loss(cand: dict[str, Any]) -> float | None:
    stress = cand.get("stress") or {}
    scenarios = stress.get("scenarios") or []
    losses: list[float] = []
    for row in scenarios:
        if not isinstance(row, dict):
            continue
        pnl = _finite(row.get("portfolio_pnl_pct"))
        if pnl is not None:
            losses.append(pnl)
    if not losses:
        return None
    return min(losses)


def _tier_b_sharpe(by_id: dict[str, dict[str, Any]], window: str) -> dict[str, Any]:
    ranked: list[tuple[str, float]] = []
    for cid, cand in by_id.items():
        if cand.get("role") == "user_current":
            continue
        if cand.get("status") not in ELIGIBLE_STATUSES:
            continue
        sharpe = _finite(((cand.get("metrics") or {}).get(window) or {}).get("sharpe"))
        if sharpe is None:
            continue
        ranked.append((cid, sharpe))
    if not ranked:
        return {
            "variant_id": f"sharpe_rank_{window}",
            "tier": "B",
            "status": "skipped",
            "skipped_reason": f"metrics_{window}_sharpe_missing",
            "evidence_leader_id": None,
            "matches_baseline_favored": False,
            "margin_vs_runner_up": None,
            "runner_up_id": None,
        }
    ranked.sort(key=lambda x: (-x[1], x[0]))
    leader_id, leader_sharpe = ranked[0]
    runner_up = ranked[1] if len(ranked) > 1 else None
    margin = round(leader_sharpe - runner_up[1], 3) if runner_up else None
    return {
        "variant_id": f"sharpe_rank_{window}",
        "tier": "B",
        "status": "evaluated",
        "skipped_reason": None,
        "evidence_leader_id": leader_id,
        "matches_baseline_favored": False,
        "margin_vs_runner_up": margin,
        "runner_up_id": runner_up[0] if runner_up else None,
    }


def _tier_b_stress_worst_loss(by_id: dict[str, dict[str, Any]]) -> dict[str, Any]:
    ranked: list[tuple[str, float]] = []
    for cid, cand in by_id.items():
        if cand.get("role") == "user_current":
            continue
        if cand.get("status") not in ELIGIBLE_STATUSES:
            continue
        loss = _worst_scenario_loss(cand)
        if loss is None:
            continue
        ranked.append((cid, loss))
    if not ranked:
        return {
            "variant_id": "stress_worst_loss_rank",
            "tier": "B",
            "status": "skipped",
            "skipped_reason": "stress_summary_incomplete",
            "evidence_leader_id": None,
            "matches_baseline_favored": False,
            "margin_vs_runner_up": None,
            "runner_up_id": None,
        }
    ranked.sort(key=lambda x: (-x[1], x[0]))
    leader_id, leader_loss = ranked[0]
    runner_up = ranked[1] if len(ranked) > 1 else None
    margin = round(leader_loss - runner_up[1], 3) if runner_up else None
    return {
        "variant_id": "stress_worst_loss_rank",
        "tier": "B",
        "status": "evaluated",
        "skipped_reason": None,
        "evidence_leader_id": leader_id,
        "matches_baseline_favored": False,
        "margin_vs_runner_up": margin,
        "runner_up_id": runner_up[0] if runner_up else None,
    }


def _evaluate_tier_b(
    by_id: dict[str, dict[str, Any]],
    baseline_id: str | None,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for spec in TIER_B_CATALOG:
        if spec["kind"] == "sharpe":
            row = _tier_b_sharpe(by_id, spec["window"])
        else:
            row = _tier_b_stress_worst_loss(by_id)
        leader = row.get("evidence_leader_id")
        row["matches_baseline_favored"] = (
            baseline_id is not None and leader is not None and leader == baseline_id
        )
        rows.append(row)
    return rows


def _stability_status(rate: float, evaluated_count: int) -> str:
    if evaluated_count == 0:
        return "not_evaluated"
    for label, threshold in _STABILITY_BANDS:
        if rate >= threshold:
            return label
    return "fragile"


def _summary_plain_en(
    *,
    baseline_name: str | None,
    stability_status: str,
    stable_count: int,
    evaluated_count: int,
    policy_default_sensitive: bool,
    evidence_rate: float,
    model_risk: dict[str, Any] | None,
) -> str:
    if evaluated_count == 0:
        return "Selection stability was not evaluated because score inputs were incomplete."
    rate_pct = int(round(100 * stable_count / evaluated_count))
    name = baseline_name or "the favored profile"
    parts = [
        f"{name} remained favored in {stable_count} of {evaluated_count} "
        f"selection-weight variants ({rate_pct}%)."
    ]
    if policy_default_sensitive:
        parts.append(
            "Composite-only ranking without the policy default would favor a different profile."
        )
    if stability_status == "fragile":
        parts.append("Treat the selection as assumption-sensitive until trade-offs are reviewed.")
    elif stability_status == "stable" and evidence_rate < 0.6:
        parts.append(
            "Selection weights are stable, but single-metric window leaders sometimes differ."
        )
    elif stability_status == "stable":
        parts.append("Favored profile is stable under reviewable weight and evidence checks.")
    severity = (model_risk or {}).get("overall_severity")
    if stability_status == "fragile" and severity in ("high", "medium"):
        parts.append("Ranking instability coincides with elevated model-risk warnings.")
    return " ".join(parts)


def build_assumption_sensitivity(
    comparison: dict[str, Any],
    *,
    selection: dict[str, Any] | None = None,
    health: dict[str, Any] | None = None,
    robustness: dict[str, Any] | None = None,
    model_risk: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build assumption_sensitivity_v1 document."""
    warnings: list[str] = []
    by_id = _candidates_by_id(comparison)
    health_by_id, robust_by_id = _score_maps(health, robustness)
    has_both_scores = bool(health_by_id) and bool(robust_by_id)

    base: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "diagnostic_only": True,
        "non_executing": True,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "analysis_end": comparison.get("analysis_end"),
        "sensitivity_status": "complete",
        "baseline_favored_id": None,
        "baseline_favored_display_name": None,
        "baseline_decision_status": None,
        "stability_status": "not_evaluated",
        "favored_stable_rate": 0.0,
        "policy_default_sensitive": False,
        "tier_a_variants": [],
        "tier_b_variants": [],
        "flippers": [],
        "evidence_agreement_rate": 0.0,
        "evidence_conflict_variants": [],
        "summary_plain_en": "",
        "warnings": warnings,
        "input_artifacts": {
            "selection_decision.json": "selection_decision.json" if selection else None,
            "portfolio_health_score.json": "portfolio_health_score.json" if health else None,
            "robustness_scorecard.json": "robustness_scorecard.json" if robustness else None,
            "candidate_comparison.json": "candidate_comparison.json",
        },
    }

    if not selection:
        base["sensitivity_status"] = "selection_unavailable"
        base["summary_plain_en"] = (
            "Assumption sensitivity requires a selection decision artifact; none was available."
        )
        warnings.append("selection_unavailable")
        base["warnings"] = warnings
        return base

    baseline_id = selection.get("favored_candidate_id")
    baseline_name = selection.get("favored_display_name")
    base["baseline_favored_id"] = baseline_id
    base["baseline_favored_display_name"] = baseline_name
    base["baseline_decision_status"] = selection.get("decision_status")

    if baseline_id is None:
        base["sensitivity_status"] = "no_baseline_favored"
        base["summary_plain_en"] = (
            "No favored profile was recorded in the selection decision; "
            "stability variants are not applicable."
        )
        tier_a = []
        for spec in TIER_A_CATALOG:
            tier_a.append(
                {
                    "variant_id": spec["variant_id"],
                    "tier": "A",
                    "status": "not_applicable",
                    "skipped_reason": "no_baseline_favored",
                    "w_health": spec["w_health"],
                    "w_robust": spec["w_robust"],
                    "w_mandate": spec["w_mandate"],
                    "apply_policy_default": spec["apply_policy_default"],
                    "effective_favored_id": None,
                    "effective_favored_display_name": None,
                    "matches_baseline_favored": False,
                    "top_three_composite": [],
                }
            )
        base["tier_a_variants"] = tier_a
        base["tier_b_variants"] = _evaluate_tier_b(by_id, baseline_id)
        base["warnings"] = warnings
        return base

    tier_a_rows: list[dict[str, Any]] = []
    flippers: list[dict[str, Any]] = []
    evaluated = 0
    stable_count = 0
    policy_sensitive = False

    for spec in TIER_A_CATALOG:
        weights = _weights_dict(spec)
        row: dict[str, Any] = {
            "variant_id": spec["variant_id"],
            "tier": "A",
            "w_health": spec["w_health"],
            "w_robust": spec["w_robust"],
            "w_mandate": spec["w_mandate"],
            "apply_policy_default": spec["apply_policy_default"],
            "skipped_reason": None,
            "effective_favored_id": None,
            "effective_favored_display_name": None,
            "matches_baseline_favored": False,
            "top_three_composite": [],
        }
        if not has_both_scores:
            row["status"] = "skipped"
            row["skipped_reason"] = "partial_score_inputs"
            tier_a_rows.append(row)
            continue

        composite = _rank_composite(by_id, health_by_id, robust_by_id, weights)
        eff_id, eff_name = _effective_favored(
            by_id,
            composite,
            apply_policy_default=bool(spec["apply_policy_default"]),
        )
        row["status"] = "evaluated"
        row["effective_favored_id"] = eff_id
        row["effective_favored_display_name"] = eff_name
        matches = eff_id == baseline_id
        row["matches_baseline_favored"] = matches
        row["top_three_composite"] = [
            {"candidate_id": r["candidate_id"], "selection_score": r["selection_score"]}
            for r in composite[:3]
        ]

        if spec["variant_id"] == "baseline_selection" and eff_id != baseline_id:
            warnings.append("baseline_recompute_mismatch")

        if spec["variant_id"] == "composite_only_no_policy_default" and not matches:
            policy_sensitive = True

        evaluated += 1
        if matches:
            stable_count += 1
        elif eff_id:
            flippers.append(
                {
                    "variant_id": spec["variant_id"],
                    "effective_favored_id": eff_id,
                    "effective_favored_display_name": eff_name,
                    "flip_note": (
                        f"Variant {spec['variant_id']} favors {eff_name or eff_id} over baseline."
                    ),
                }
            )
        tier_a_rows.append(row)

    favored_rate = round(stable_count / evaluated, 3) if evaluated else 0.0
    stability = _stability_status(favored_rate, evaluated)

    tier_b_rows = _evaluate_tier_b(by_id, baseline_id)
    evidence_evaluated = [r for r in tier_b_rows if r.get("status") == "evaluated"]
    evidence_matches = sum(1 for r in evidence_evaluated if r.get("matches_baseline_favored"))
    evidence_rate = (
        round(evidence_matches / len(evidence_evaluated), 3) if evidence_evaluated else 0.0
    )
    conflicts = [
        r["variant_id"]
        for r in evidence_evaluated
        if not r.get("matches_baseline_favored")
    ]

    if not has_both_scores:
        base["sensitivity_status"] = "partial"
        warnings.append("partial_score_inputs")

    base.update(
        {
            "stability_status": stability,
            "favored_stable_rate": favored_rate,
            "policy_default_sensitive": policy_sensitive,
            "tier_a_variants": tier_a_rows,
            "tier_b_variants": tier_b_rows,
            "flippers": flippers,
            "evidence_agreement_rate": evidence_rate,
            "evidence_conflict_variants": conflicts,
            "summary_plain_en": _summary_plain_en(
                baseline_name=baseline_name,
                stability_status=stability,
                stable_count=stable_count,
                evaluated_count=evaluated,
                policy_default_sensitive=policy_sensitive,
                evidence_rate=evidence_rate,
                model_risk=model_risk,
            ),
            "warnings": warnings,
        }
    )
    return base


def write_assumption_sensitivity_txt(doc: dict[str, Any], path: Path) -> None:
    lines = [
        "Assumption sensitivity (diagnostic only; non-executing)",
        "=" * 50,
        "",
        "Baseline",
        "-" * 40,
        f"  Favored profile: {doc.get('baseline_favored_display_name') or '—'}",
        f"  Decision status: {doc.get('baseline_decision_status') or '—'}",
        "",
        "Selection stability",
        "-" * 40,
        f"  Status: {doc.get('stability_status', '—')}",
        f"  Stable rate (Tier A): {doc.get('favored_stable_rate', 0):.1%}",
    ]
    flippers = doc.get("flippers") or []
    if flippers:
        lines.append("  Variants that change the favored profile:")
        for flip in flippers:
            lines.append(
                f"    - {flip.get('variant_id')}: {flip.get('effective_favored_display_name')}"
            )
    else:
        lines.append("  No Tier A flips versus baseline.")
    lines.extend(
        [
            "",
            "Policy-default check",
            "-" * 40,
        ]
    )
    if doc.get("policy_default_sensitive"):
        lines.append(
            "  Composite-only ranking (no policy default) disagrees with the baseline selection."
        )
    else:
        lines.append("  Policy default alignment: consistent with baseline selection.")
    lines.extend(
        [
            "",
            "Evidence checks (informational)",
            "-" * 40,
            f"  Evidence agreement rate: {doc.get('evidence_agreement_rate', 0):.1%}",
        ]
    )
    conflicts = doc.get("evidence_conflict_variants") or []
    if conflicts:
        lines.append(f"  Conflicts: {', '.join(conflicts)}")
    else:
        lines.append("  No Tier B conflicts with baseline favored profile.")
    lines.extend(
        [
            "",
            "Interpretation",
            "-" * 40,
            f"  {doc.get('summary_plain_en') or ''}",
            "",
            "See assumption_sensitivity.json for full variant rows.",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def write_assumption_sensitivity_outputs(
    cfg: PortfolioConfig,
    *,
    project_root: Path | None = None,
    comparison: dict[str, Any] | None = None,
    selection: dict[str, Any] | None = None,
    health: dict[str, Any] | None = None,
    robustness: dict[str, Any] | None = None,
    model_risk: dict[str, Any] | None = None,
    write_txt: bool = True,
) -> dict[str, Path]:
    """Write assumption sensitivity artifacts when comparison exists."""
    project_root = project_root or Path.cwd()
    out_dir = project_root / str(getattr(cfg, "output_dir_final", "Main portfolio"))

    if comparison is None:
        comparison = _load_json(out_dir / "candidate_comparison.json")
    if not comparison:
        return {}

    if selection is None:
        selection = _load_json(out_dir / "selection_decision.json")
    if health is None:
        health = _load_json(out_dir / "portfolio_health_score.json")
    if robustness is None:
        robustness = _load_json(out_dir / "robustness_scorecard.json")
    if model_risk is None:
        model_risk = _load_json(out_dir / "model_risk_diagnostics.json")

    doc = build_assumption_sensitivity(
        comparison,
        selection=selection,
        health=health,
        robustness=robustness,
        model_risk=model_risk,
    )

    out_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    json_path = out_dir / "assumption_sensitivity.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=2, ensure_ascii=False)
    paths["assumption_sensitivity_json"] = json_path

    if write_txt:
        txt_path = out_dir / "assumption_sensitivity.txt"
        write_assumption_sensitivity_txt(doc, txt_path)
        paths["assumption_sensitivity_txt"] = txt_path

    return paths


__all__ = [
    "SCHEMA_VERSION",
    "TIER_A_CATALOG",
    "build_assumption_sensitivity",
    "write_assumption_sensitivity_outputs",
    "write_assumption_sensitivity_txt",
]
