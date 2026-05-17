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

Issue ID: KI-2026-05-17-007
Title: Source/generator mojibake and English-language normalization remain in user-facing paths

- Status: in_progress
- Severity: high
- Area: reports
- Risk: Generated reports can still contain stale broken text until they are regenerated from cleaned source strings.
- Evidence: Session 05 cleaned source/generator text in CLI/log/report/PDF/config/docs paths and targeted source scans now pass for Cyrillic and common mojibake markers. Existing generated output folders were not hand-edited and may still contain older text.
- Current mitigation: Source and generator defaults are English; generated outputs are not treated as source.
- Next action: Regenerate representative report/PDF outputs during the reporting/PDF sessions and visually/readably check the result.
- Source links: [post-session audit](docs/audits/2026-05-17_post_session_deep_system_audit.md), [OUTPUTS](OUTPUTS.md), [TESTING](TESTING.md).
- Remove when: Targeted source scans pass and regenerated representative outputs no longer show broken or non-English default text.


Issue ID: KI-2026-05-17-004
Title: Partial utility UI status is under-described in top-level docs

- Status: planned
- Severity: medium
- Area: docs
- Risk: Contributors may not know whether `config_ui/` and `results_dashboard/` are supported utility surfaces, abandoned experiments, or part of the future full product UI.
- Evidence: Audit item `AUD-005` reports that partial utility UIs exist while top-level docs mostly state full UI is TBD.
- Current mitigation: `SPEC.md`, `PRODUCT.md`, and `ARCHITECTURE.md` correctly keep the full product workspace as TBD.
- Next action: Add consistent wording that partial utility UIs exist for config editing and read-only result viewing, while the full product workspace remains TBD.
- Source links: [full audit](docs/audits/2026-05-17_full_project_system_audit.md), [README](README.md), [SPEC](SPEC.md), [PRODUCT](PRODUCT.md), [ARCHITECTURE](ARCHITECTURE.md), [DESIGN](DESIGN.md).
- Remove when: The wording is synced across the owning top-level docs and stale UI-status references are checked.

## Update Rules

- Update this file when a known issue is discovered, fixed, accepted, or no longer relevant.
- If a code change fixes an active issue, remove the issue only after verification passes and related docs are synced.
- If a fixed issue is meaningful at project level, add one short `Fixed` entry to [CHANGELOG.md](CHANGELOG.md).
- If a code change introduces a known limitation that is not fixed in the same change, add it here before considering the task done.
- If the issue affects data behavior, also check [DATA.md](DATA.md).
- If the issue affects verification strategy, also check [TESTING.md](TESTING.md).
- If the issue affects implementation behavior, also check [SPEC.md](SPEC.md) and the owning file under [docs/specs/](docs/specs/README.md).
- If the issue requires multi-step implementation, create or update an ExecPlan under `docs/exec_plans/`.
