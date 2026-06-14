# Runtime Artifact Contract (Core MVP)

Operator reference for **which JSON files must exist, must not exist, or may be stale** after each canonical CLI run. This document implements audit gap **R2-R4** remediation targets from [Blocks 1-3 pre-decision foundation audit](audits/2026-05-29_blocks_1_3_pre_decision_diagnostic_foundation_audit.md).

Canonical commands: [runtime_entrypoints.md](runtime_entrypoints.md). Product read order: [product_flow_operator_guide.md](product_flow_operator_guide.md).

Default output folder: `{output_dir_final}` from `config.yml` (demo: `Main portfolio/`). Portfolio-first subject diagnostics live under `{output_dir_final}/analysis_subject/`.

---

## Canonical runtime modes

| Mode | Command | Workflow state |
| --- | --- | --- |
| Core diagnostics only | `python run_core_diagnostics.py` | Blocks 1-3 only; `product_bundle_scope=core_blocks_1_3` |
| Product diagnosis (no candidates) | `python run_portfolio_review.py` | `diagnosis_only`; factory and compare **not** run |
| Canonical one-hypothesis vertical demo | `python scripts/run_blocks_5_to_9_vertical_flow.py --method <id>` | selected Launchpad card -> Builder setup -> Candidate Generation -> compare -> verdict |
| One explicit backend candidate compatibility path | `python run_portfolio_review.py --candidates <id>` | `one_candidate`; factory `explicit_list` + compare; bypasses visible Builder-to-Block-7 proof |

---

## `analysis_subject/` (always materialized on successful diagnosis)

| Artifact | Core only | Diagnosis only | One candidate |
| --- | --- | --- | --- |
| `run_metadata.json` | **Required** | **Required** | **Required** |
| `portfolio_xray.json` (Blocks 2.1-2.6) | **Required** | **Required** | **Required** |
| `stress_report.json` (3.2-3.4 v1 primary) | **Required** | **Required** | **Required** |
| `client_fit_check.json` | **Absent** for Blocks 1-3-only core diagnostics | **Required**; writes fit/watch/breach/conflict/evidence_insufficient when profile evidence exists, otherwise `not_provided` | **Required**; same analysis-subject check is used as bounded context for Builder/Comparison display criteria |
| `snapshot_10y.json`, `snapshot_index.json` | **Required** | **Required** | **Required** |
| `output_manifest.json` | **Required** | **Required** | **Required** |
| `problem_classification.json` | **Absent** (pruned on core-only) | **Required** (`problem_classification_v3` with `next_diagnostic_step`) | **Required** |
| `candidate_launchpad.json` | **Absent** (pruned on core-only) | **Required** (`candidate_launchpad_v3`; reference cards are tests, not rebalance recommendations) | **Required** |
| `portfolio_alternatives_builder.json` | **Absent** (pruned on core-only) | **Required when a primary Launchpad card can be mapped; otherwise absent with the blocker in Launchpad/Problem Classification** | **Required for the canonical vertical demo; may be absent in the factory-id compatibility path** |
| `ai_commentary_context.json` | **Absent** (pruned on core-only) | **Required** (diagnosis phase) | **Required** (post-compare refresh) |

Core-only runs invoke `apply_core_blocks_product_bundle_hygiene` after materialize (Session 04).

Client Fit V1 is a non-binding interpretation overlay with active web onboarding/display routes and
backend/CLI missing-profile compatibility. The artifact is generated after Diagnosis/Stress and before
Problem Classification. The frontend route chain collects bounded Client Fit context through
onboarding, shows `/client-fit` before Hypothesis, and keeps `/client-profile` as an advanced/manual
editor rather than the normal entry step. Client Fit target return, volatility, maximum drawdown, and
horizon values may appear only as display/test references in Builder and Comparison; they must not
change optimizer objectives, constraints, mandate gates, analysis windows, factory method selection,
or candidate weights.

---

## `{output_dir_final}/` root (decision package)

| Artifact | Core only | Diagnosis only | One candidate |
| --- | --- | --- | --- |
| `candidate_factory_run.json` | **Absent** | **Absent** | **Required** (explicit_list) |
| `candidate_generation.json` | **Absent** | **Absent** (removed as stale downstream evidence) | **Required for the canonical vertical demo; optional/absent in the factory-id compatibility path** |
| `candidate_comparison.json` | **Absent** | **Tombstone** `no_candidate_v1` (Session 03) | **Required** - product scope: baseline + selected id(s) only (Session 02) |
| `candidate_comparison_registry.json` | **Absent** | **Absent** (removed on hygiene) | Optional advanced full registry (Session 02) |
| `current_vs_candidate.json` | **Absent** | **Tombstone** `no_candidate_v1` (Session 03) | **Required** (`selected_candidate_ids` = chosen id only) |
| `decision_verdict.json` | **Absent** | **Tombstone** `no_candidate_v1` (Session 03) | **Required** |
| `what_changed_summary.json` | **Absent** | Optional if prior snapshot | Optional after compare |
| Legacy `stress_scorecard_v1` mandate rollup | Not Core MVP primary | Secondary in `stress_report.json` only | Same |

---

## Stale artifact rules (operator)

1. **Do not trust on-disk files left from a prior run** if the current CLI mode would not regenerate them. After Session 03, default `run_portfolio_review.py` (diagnosis-only) **overwrites** root compare/decision JSON with `no_candidate_v1` tombstones via `apply_diagnosis_only_product_bundle_hygiene`.
2. **`candidate_comparison.json` row count** matches product scope for `explicit_list` runs (baseline + selected ids). Full on-disk scan lives in `candidate_comparison_registry.json` when scoped. Batch compare still writes the full registry to `candidate_comparison.json`.
3. **Read `output_manifest.json` -> `product_discovery` and `artifact_categories`** before interpreting optional files. The manifest is a discovery index, not a trust bypass; same-run and same-candidate lineage still apply.
4. **PDF / CSV / HTML** under subject or `pdf files/` are not refreshed by default `site_api` review (see [OUTPUTS.md](../OUTPUTS.md)).

---

## Verification commands (after Phase A closure, Session 06)

```bash
python run_core_diagnostics.py
python run_portfolio_review.py
python scripts/run_blocks_5_to_9_vertical_flow.py --method equal_weight
python run_portfolio_review.py --candidates equal_weight
python scripts/verify_live_core_e2e.py
# optional: force profile - python scripts/verify_live_core_e2e.py --profile diagnosis_only
```

Target: `validate_live_core_artifacts` -> `ok=True` after each canonical CLI (auto-detected profile: `core_blocks_1_3`, `diagnosis_only`, `product_one_candidate`, or legacy `research_batch_core_fast` for `--with-candidates` / `core_fast` batch).

Phase A closure evidence (2026-05-29): [Blocks 1-3 foundation closure audit](audits/2026-05-29_blocks_1_3_foundation_closure_audit.md) - verdict **`READY_FOR_DECISION_WORKFLOW`**.

---

## Related ExecPlan

Phase A closed: [Blocks 1-3 post-audit development plan](exec_plans/2026-05-29_blocks_1_3_post_audit_development_plan.md) (Session 06). Optional polish: Sessions 07-08.
