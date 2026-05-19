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

Issue ID: KI-2026-05-19-002
Title: Candidate freshness is not guaranteed in portfolio-first review runs

- Status: planned
- Severity: high
- Area: architecture
- Risk: Selection, robustness, and Pareto outputs can compare a fresh `analysis_subject` against stale candidate snapshots.
- Evidence: The 2026-05-19 audit observed one candidate succeeded and fifteen were `skipped_existing`; factory skip logic checks only for `snapshot_10y.json`, not matching `analysis_end`.
- Current mitigation: Users can manually pass `--no-skip-existing`, but stale reuse is not clearly surfaced as a trust warning.
- Next action: Implement RM-902 by comparing candidate `snapshot_10y.analysis_end` to review `analysis_end` and rebuilding or explicitly labeling stale candidates.
- Source links: [candidate_factory.py](src/candidate_factory.py), [run_portfolio_review.py](run_portfolio_review.py), [candidate_factory_spec.md](docs/specs/candidate_factory_spec.md).
- Remove when: Factory outputs and tests distinguish fresh, reused, stale, failed, and skipped candidates, and portfolio review no longer silently uses stale snapshots.

Issue ID: KI-2026-05-19-004
Title: Decision artifacts are weak when mandate_risk_reduction blocks favored selection

- Status: planned
- Severity: medium
- Area: architecture
- Risk: No-favored runs can feel empty or confusing even when candidates rank above the subject, because downstream outputs do not clearly explain the mandate block.
- Evidence: The 2026-05-19 audit found empty trade-off pairs, `assumption_sensitivity` marked `not_evaluated`, favored regret unavailable, and baseline naming drift when `favored_candidate_id` was null.
- Current mitigation: `selection_decision.json` records the mandate block, but downstream narrative is thin.
- Next action: Implement RM-904 after metadata and freshness fixes; align trade-off baseline to `analysis_subject` and add useful blocked-decision explanation.
- Source links: [selection_engine.py](src/selection_engine.py), [tradeoff_and_model_risk.py](src/tradeoff_and_model_risk.py), [assumption_sensitivity.py](src/assumption_sensitivity.py), [regret_analysis.py](src/regret_analysis.py).
- Remove when: No-favored mandate-block outputs explain the evidence, use `analysis_subject` consistently, and have focused regression coverage.

Issue ID: KI-2026-05-19-007
Title: Monitoring first run can show contradictory deltas

- Status: planned
- Severity: medium
- Area: architecture
- Risk: A first review can appear to compare against prior history even when no prior snapshot exists.
- Evidence: The 2026-05-19 audit found `diff_status: no_prior_snapshot` with non-zero profile changes and prior/current snapshot paths pointing to the same latest snapshot.
- Current mitigation: The `diff_status` field is present, but generated deltas can still mislead readers.
- Next action: Implement RM-908 so first-run monitoring emits narrative-only or empty deltas when there is no valid prior snapshot.
- Source links: [monitoring.py](src/monitoring.py), [monitoring_spec.md](docs/specs/monitoring_spec.md).
- Remove when: Focused tests prove `no_prior_snapshot` does not include fake profile deltas or identical prior/current paths as meaningful evidence.

Issue ID: KI-2026-05-18-001
Title: Decision package PDF build can fail Pandoc/LaTeX on some analysis-end dates

- Status: planned
- Severity: low
- Area: reports
- Risk: `Main portfolio_decision_package.pdf` may be missing while other representative PDFs rebuild successfully.
- Evidence: Session 08 regeneration logged `Pandoc failed for Main portfolio_decision_package.pdf` with `Extra }, or forgotten \endgroup` near the analysis-end date line; `decision_package_summary.txt` and Markdown sidecar remain available.
- Current mitigation: Text/JSON decision package artifacts are generated; other Main PDFs rebuild successfully.
- Next action: Implement RM-909 by hardening decision-package Markdown/Pandoc sanitization for LaTeX-special characters in plain summary text.
- Source links: [pdf_reports.py](src/pdf_reports.py), [decision_package_reporting.py](src/decision_package_reporting.py).
- Remove when: `Main portfolio_decision_package.pdf` rebuilds successfully on a fresh `run_report.py` without Pandoc errors.


## Update Rules

- Update this file when a known issue is discovered, fixed, accepted, or no longer relevant.
- If a code change fixes an active issue, remove the issue only after verification passes and related docs are synced.
- If a fixed issue is meaningful at project level, add one short `Fixed` entry to [CHANGELOG.md](CHANGELOG.md).
- If a code change introduces a known limitation that is not fixed in the same change, add it here before considering the task done.
- If the issue affects data behavior, also check [DATA.md](DATA.md).
- If the issue affects verification strategy, also check [TESTING.md](TESTING.md).
- If the issue affects implementation behavior, also check [SPEC.md](SPEC.md) and the owning file under [docs/specs/](docs/specs/README.md).
- If the issue requires multi-step implementation, create or update an ExecPlan under `docs/exec_plans/`.
