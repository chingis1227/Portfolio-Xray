"""Unit tests for package_truthfulness (RM-1028)."""

from __future__ import annotations

from src.package_truthfulness import (
    SCHEMA_VERSION,
    build_review_scope_banner_lines,
    summarize_package_truthfulness,
)


def _optimizer_row(
    cid: str,
    *,
    status: str = "degraded",
    fair_ready: bool = False,
) -> dict:
    return {
        "candidate_id": cid,
        "display_name": cid.replace("_", " ").title(),
        "role": "optimizer_candidate",
        "status": status,
        "construction_disclosure": {
            "optimization_readiness": {"fair_comparison_ready": fair_ready},
        },
    }


def test_partial_menu_implies_not_full_shootout() -> None:
    comparison = {
        "candidate_menu": {
            "review_mode": "core",
            "is_partial_menu": True,
            "partial_menu_reason": "reduced_vs_product_menu",
            "intended_menu_profile_id": "core_v1",
            "product_menu_profile_id": "default_v1",
            "intended_menu_scored_count": 6,
            "product_menu_size": 16,
        },
        "candidates": [],
    }
    truth = summarize_package_truthfulness(comparison)
    assert truth["schema_version"] == SCHEMA_VERSION
    assert truth["is_partial_menu"] is True
    assert truth["implies_full_product_menu_shootout"] is False
    assert any("reduced candidate menu" in line for line in truth["user_summary_lines"])


def test_degraded_optimizer_counted_in_truth_summary() -> None:
    comparison = {
        "candidate_menu": {"is_partial_menu": False},
        "candidates": [
            _optimizer_row("mv_bad"),
            _optimizer_row("mv_ok", status="available", fair_ready=True),
        ],
    }
    truth = summarize_package_truthfulness(comparison)
    assert truth["degraded_optimizer_count"] == 1
    assert truth["fair_ready_optimizer_count"] == 1
    assert truth["degraded_optimizers"][0]["candidate_id"] == "mv_bad"


def test_review_scope_banner_lists_degraded_and_partial() -> None:
    comparison = {
        "candidate_menu": {
            "review_mode": "core",
            "is_partial_menu": True,
            "partial_menu_reason": "reduced_vs_product_menu",
            "intended_menu_profile_id": "core_v1",
            "product_menu_profile_id": "default_v1",
        },
        "candidates": [_optimizer_row("minimum_variance")],
    }
    banner = build_review_scope_banner_lines(comparison)
    joined = "\n".join(banner)
    assert "Review scope (read first)" in joined
    assert "Partial menu" in joined
    assert "Minimum Variance" in joined
    assert "not eligible for favoring" in joined
