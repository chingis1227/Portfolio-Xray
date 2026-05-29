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
            "Flow: Input -> X-Ray -> Stress -> Problem Classification -> "
            "Candidate Launchpad -> Current vs Candidate -> Decision Verdict"
        )
        return
    print("Mode: product_diagnosis_workflow")
    print(
        "Flow: Input -> X-Ray -> Stress -> Problem Classification -> "
        "Candidate Launchpad -> AI Commentary / Monitoring"
    )
    print("Candidates: disabled by default")
