# KNOWN_ISSUES.md

This file is the living register of known active issues, bugs, weak spots, model limitations, testing gaps, and technical debt for Portfolio X-Ray & Optimization Terminal / Portfolio MRI.

It is not a roadmap, product concept, or technical specification. It does not override `SPEC.md`, `DATA.md`, `TESTING.md`, `RULES.md`, or `docs/specs/*.md`.

## Purpose

- Keep known risks visible until they are fixed or intentionally accepted.
- Prevent agents and developers from rediscovering the same problem repeatedly.
- Separate active issues from future product ideas and target/TBD modules.
- Make model limitations and quality gaps explicit before they affect decisions.

## What Belongs Here

- Confirmed bugs or likely behavioral defects.
- Model risks and assumption limitations.
- Data quality risks and fragile fallback behavior.
- Testing gaps and missing regression coverage.
- Documentation debt that can mislead implementation or users.
- Technical debt that increases maintenance or correctness risk.

## What Does Not Belong Here

- Long formulas or implementation details; put those in the owning spec.
- Pure roadmap ideas; keep those in `PRODUCT.md`, `BUSINESS_VISION.md`, or an ExecPlan when work starts.
- Generated-output diffs unless the generated artifact itself is the problem.
- Resolved issues that no longer affect the current project state.

## Lifecycle

1. Add an issue when a real risk, bug, limitation, or quality gap is discovered and not fixed immediately.
2. Keep active issues short, specific, and linked to the affected source of truth.
3. When an issue is fixed, verified, and documented, remove it from the active list.
4. If the fix needs audit history, record it in the relevant commit, PR, [CHANGELOG.md](CHANGELOG.md), or ExecPlan instead of keeping stale active issues here.
5. If an issue is intentionally accepted, mark it as `accepted` and explain the boundary and mitigation.

## Entry Format

Use this format for new entries:

```markdown
Issue ID: KI-YYYY-MM-DD-NNN
Title: Short title

- Status: open | planned | in_progress | blocked | accepted
- Severity: low | medium | high | critical
- Area: data | metrics | optimizer | stress | factor_macro | reports | config | docs | testing | architecture
- Risk: What can go wrong if this stays unresolved.
- Evidence: Where the issue is observed or why it is believed to exist.
- Current mitigation: What reduces the risk today, if anything.
- Next action: The smallest practical next step.
- Source links: Relevant docs, specs, code, tests, or outputs.
- Remove when: Concrete condition for deleting this active issue.
```

## Active Issues

Issue ID: KI-2026-05-19-010
Title: X-Ray archetype and weakness explanations can create false confidence

- Status: resolved
- Severity: medium
- Area: reports
- Risk: Simple labels or low-severity rows can be read as definitive conclusions instead of partial diagnostics with incomplete evidence and conflicting signals.
- Evidence: Portfolio X-Ray audit found archetype output capable of labeling a portfolio as inflation-sensitive without explaining simultaneous inflation/rates vulnerability.
- Resolution (2026-05-20, Session 07 / RM-937): Archetype V2 emits `positive_evidence`, `negative_evidence`, `archetype_scorecard`, `conflicting_signals`, and `conflict_summary`, including weakness-map regime tensions when inflation-sensitive holdings coexist with inflation/rates vulnerability.
- Source links: [Portfolio X-Ray audit](docs/audits/2026-05-19_portfolio_xray_layer_audit.md), [X-Ray diagnostics spec](docs/specs/portfolio_xray_diagnostics_spec.md), [portfolio_xray.py](src/portfolio_xray.py), [tests/test_portfolio_xray.py](tests/test_portfolio_xray.py).

Issue ID: KI-2026-05-19-005
Title: Full candidate factory refresh is operationally heavy for one-shot review runs

- Status: mitigated
- Severity: medium
- Area: architecture
- Risk: Full `--mode full` rebuild can still exceed session limits when many optimizer snapshots are stale; decision outputs must not be read as covering the full product menu when `candidate_menu.is_partial_menu` is true.
- Resolution (2026-05-20, Session 09 / RM-939): Default `run_portfolio_review.py` uses `--mode core` and factory profile `core_v1`; `--mode full` runs `default_v1` explicitly. Comparison and decision-package outputs include `candidate_menu` partial-menu disclosure and refresh commands.
- Remaining gap: resumable factory progress / optional parallelism (`RM-921`).
- Source links: [run_portfolio_review.py](run_portfolio_review.py), [portfolio_review_workflow.py](src/portfolio_review_workflow.py), [candidate_comparison.py](src/candidate_comparison.py), [operational_runbook.md](docs/operational_runbook.md).
- Remove when: Resumable factory and progress logging ship, or full-run reliably completes within agreed operator time budget without manual staging.

## Update Rules

- Update this file when a known issue is discovered, fixed, accepted, or no longer relevant.
- If a code change fixes an active issue, remove the issue only after verification passes and related docs are synced.
- If a fixed issue is meaningful at project level, add one short `Fixed` entry to [CHANGELOG.md](CHANGELOG.md).
- If a code change introduces a known limitation that is not fixed in the same change, add it here before considering the task done.
- If the issue affects data behavior, also check [DATA.md](DATA.md).
- If the issue affects verification strategy, also check [TESTING.md](TESTING.md).
- If the issue affects implementation behavior, also check [SPEC.md](SPEC.md) and the owning file under [docs/specs/](docs/specs/README.md).
- If the issue requires multi-step implementation, create or update an ExecPlan under `docs/exec_plans/`.
