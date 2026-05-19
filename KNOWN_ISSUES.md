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

Issue ID: KI-2026-05-19-005
Title: Full candidate factory refresh is operationally heavy for one-shot review runs

- Status: accepted
- Severity: medium
- Area: architecture
- Risk: Users or agents may assume `run_portfolio_review.py` always finishes subject → factory → compare → PDF in one session; when all optimizer builders must rebuild, the run can exceed practical time limits and leave a partial candidate menu while decision outputs still look complete.
- Evidence: Phase 9 closure (RM-911): core portfolio-first logic and freshness gating work; stale rows are marked `unavailable` instead of scored silently. Representative runs showed multi-hour `default_v1` factory duration when snapshots are stale; agent/session limits aborted full factory before compare in some attempts.
- Current mitigation: Run subject materialization and `run_compare_variants.py` separately; use `run_candidate_factory.py` with `--profile` subsets or `--no-skip-existing` only when a full refresh is intended; rely on `candidate_factory_run.json` and comparison `status` / `unavailable_reason` for transparency; reuse snapshots when `snapshot_10y.json.analysis_end` matches review `analysis_end` (RM-902).
- Next action: Implement deferred roadmap items RM-920–RM-922 (core-run vs full-run profiles, resumable/progress factory, explicit partial-menu disclosure in decision outputs). See [ROADMAP.md](docs/ROADMAP.md) Phase 10.
- Source links: [run_portfolio_review.py](run_portfolio_review.py), [candidate_factory.py](src/candidate_factory.py), [candidate_factory_spec.md](docs/specs/candidate_factory_spec.md), [portfolio_review_workflow_spec.md](docs/specs/portfolio_review_workflow_spec.md), [operational_runbook.md](docs/operational_runbook.md), [post-portfolio-first stabilization ExecPlan](docs/exec_plans/2026-05-19_post_portfolio_first_stabilization_plan.md).
- Remove when: Default portfolio-first workflow offers a documented fast core path, optional full refresh path, resumable factory progress, and decision-package warnings when the scored candidate menu is partial; UI work should not start before this operational model is defined.

## Update Rules

- Update this file when a known issue is discovered, fixed, accepted, or no longer relevant.
- If a code change fixes an active issue, remove the issue only after verification passes and related docs are synced.
- If a fixed issue is meaningful at project level, add one short `Fixed` entry to [CHANGELOG.md](CHANGELOG.md).
- If a code change introduces a known limitation that is not fixed in the same change, add it here before considering the task done.
- If the issue affects data behavior, also check [DATA.md](DATA.md).
- If the issue affects verification strategy, also check [TESTING.md](TESTING.md).
- If the issue affects implementation behavior, also check [SPEC.md](SPEC.md) and the owning file under [docs/specs/](docs/specs/README.md).
- If the issue requires multi-step implementation, create or update an ExecPlan under `docs/exec_plans/`.
