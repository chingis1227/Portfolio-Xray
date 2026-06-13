"""Runtime entrypoint labels keep product, compatibility, and research paths distinct."""

from __future__ import annotations

from src.runtime_entrypoint_labels import print_portfolio_review_banner


def test_explicit_candidate_banner_labels_compatibility_path(capsys) -> None:  # noqa: ANN001
    print_portfolio_review_banner(
        runtime_mode="product_one_candidate",
        candidates="equal_weight",
    )

    out = capsys.readouterr().out

    assert "Mode: product_one_candidate" in out
    assert "Path classification: explicit factory-id compatibility path" in out
    assert "scripts/run_blocks_5_to_9_vertical_flow.py --method <id>" in out
    assert "Client Fit" in out
    assert "known factory-id candidate" in out
    assert "Builder/Candidate Generation proof: bypassed" in out


def test_research_batch_banner_labels_advanced_path(capsys) -> None:  # noqa: ANN001
    print_portfolio_review_banner(runtime_mode="research_batch")

    out = capsys.readouterr().out

    assert "Mode: research_batch" in out
    assert "Path classification: advanced/research candidate factory path" in out
    assert "not the Core MVP demo story" in out
    assert "Client Fit" in out


def test_diagnosis_banner_lists_current_diagnosis_flow(capsys) -> None:  # noqa: ANN001
    print_portfolio_review_banner(runtime_mode="product_diagnosis_only")

    out = capsys.readouterr().out

    assert "Mode: product_diagnosis_workflow" in out
    assert "Client Fit" in out
    assert "Portfolio Alternatives Builder" in out
    assert "Candidates: disabled by default" in out
