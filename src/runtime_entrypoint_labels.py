"""Console labels for active Portfolio MRI runtime entrypoints."""

from __future__ import annotations


def print_core_diagnostics_banner() -> None:
    print("Mode: core_diagnostics_only")
    print("Flow: Input -> Portfolio X-Ray -> Stress Test Lab")
    print("Candidates: disabled")


def print_portfolio_review_banner(
    *,
    runtime_mode: str,
    candidates: str | None = None,
) -> None:
    if runtime_mode == "product_one_candidate":
        print("Mode: product_one_candidate")
        print(f"Selected candidate: {candidates or '(unspecified)'}")
        print(
            "Path classification: explicit factory-id compatibility path. "
            "For the canonical Blocks 5-9 demo, use "
            "scripts/run_blocks_5_to_9_vertical_flow.py --method <id>."
        )
        print(
            "Flow: Input -> X-Ray -> Stress -> Client Fit -> Problem Classification -> "
            "Candidate Launchpad -> known factory-id candidate -> Current vs Candidate -> "
            "Decision Verdict"
        )
        print(
            "Builder/Candidate Generation proof: bypassed; use the vertical demo for that "
            "visible product loop."
        )
        return
    if runtime_mode in {"product_shortlist", "research_batch"}:
        print(f"Mode: {runtime_mode}")
        print(
            "Path classification: advanced/research candidate factory path; "
            "not the Core MVP demo story."
        )
        print(
            "Flow: Input -> X-Ray -> Stress -> Client Fit -> Problem Classification -> "
            "Candidate Launchpad -> backend candidate factory -> comparison"
        )
        return
    print("Mode: product_diagnosis_workflow")
    print(
        "Flow: Input -> X-Ray -> Stress -> Client Fit -> Problem Classification -> "
        "Candidate Launchpad -> Portfolio Alternatives Builder -> diagnosis grounding"
    )
    print("Candidates: disabled by default")
