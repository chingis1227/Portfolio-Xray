# DECISIONS.md

This file is the concise living decision log for Portfolio X-Ray & Optimization Terminal / Portfolio MRI.

It records important decisions, why they were made, what alternatives were rejected, and which assumptions existed at the time. It is not a changelog, roadmap, issue tracker, implementation spec, or ExecPlan.

Accepted project-level decisions are listed below. Add entries here only when a real decision is made.

## Purpose

- Preserve the reasoning behind important project choices.
- Prevent the same architectural, product, or methodology questions from being reopened without context.
- Make assumptions visible when a decision is made.
- Keep rationale separate from implementation details and change history.

## What Belongs Here

- Architecture decisions that affect module boundaries, workflows, interfaces, or source-of-truth ownership.
- Product boundary decisions, such as diagnostic-only vs production policy behavior.
- Financial methodology decisions, such as optimizer policy, stress governance, data assumptions, metrics behavior, or model-risk boundaries.
- Testing and quality decisions that affect verification strategy.
- Documentation governance decisions that affect how project knowledge is organized.

## What Does Not Belong Here

- Every code change; use [CHANGELOG.md](CHANGELOG.md) for concise completed-change history.
- Active bugs, weak spots, or technical debt; use [KNOWN_ISSUES.md](KNOWN_ISSUES.md).
- Long formulas or module contracts; use `SPEC.md`, `DATA.md`, and `docs/specs/*.md`.
- Step-by-step implementation plans; use [PLANS.md](PLANS.md) and `docs/exec_plans/`.
- Future product ideas without a decision; use `PRODUCT.md`, `BUSINESS_VISION.md`, or `docs/DIAGNOSTIC_PRODUCT_CONCEPT.md`.

## When To Add Or Update

- Add an entry when the project chooses one path among meaningful alternatives.
- Add an entry when a decision affects behavior, source-of-truth structure, methodology, API/UI boundaries, data policy, testing policy, or reporting contracts.
- Update an entry when the decision is superseded, narrowed, expanded, or its assumptions are no longer true.
- Do not rewrite history silently; mark old decisions as `superseded` and link the newer decision.
- If a decision changes current behavior, update the owning spec and add a short entry to [CHANGELOG.md](CHANGELOG.md).
- If a decision exposes an unresolved risk or debt item, add it to [KNOWN_ISSUES.md](KNOWN_ISSUES.md).

## Entry Format

Keep entries short. Use this format:

```markdown
Decision ID: DEC-YYYY-MM-DD-NNN
Title: Short title

- Status: proposed | accepted | superseded
- Date: YYYY-MM-DD
- Decision: What was decided.
- Context: What problem or trade-off triggered the decision.
- Rationale: Why this option was chosen.
- Alternatives considered: What was rejected and why.
- Assumptions: What was believed to be true at the time.
- Consequences: What changes or constraints follow from the decision.
- Related documents: Links to specs, plans, code, tests, or docs.
- Review trigger: When this decision should be revisited.
```

## Decisions

Decision ID: DEC-2026-06-04-002
Title: Launchpad cards prefill Portfolio Alternatives Builder but do not generate or recommend candidates

- Status: accepted
- Date: 2026-06-04
- Decision: Treat `candidate_launchpad_v3` cards as the canonical source for Portfolio Alternatives Builder prefill. The Builder copies the diagnosis, hypothesis, success criteria, tradeoff, skip rule, method role, and decision boundary into a setup object, but candidate generation requires a separate explicit user action and no Launchpad-derived setup is a rebalance recommendation.
- Context: Block 4 v3 cards already carried enough diagnostic context for the next product step, while the previous Builder path only extracted method id, goal, and source card id.
- Rationale: Users need a guided handoff from diagnosis to a test setup without confusing a hypothesis test or benchmark comparison with a trading recommendation.
- Alternatives considered: Auto-generate a candidate whenever a Launchpad card is selected (rejected because it blurs user consent and generation cost); keep Builder as method-id-only (rejected because it drops diagnosis and decision-boundary context); promote Equal Weight / Risk Parity cards to recommendations (rejected because they are reference benchmarks only).
- Assumptions: Decision Verdict remains the only downstream product layer that can justify action after Current vs Candidate Comparison; batch candidate factory remains backend/advanced/research infrastructure.
- Consequences: Builder prefill supports `guided_from_diagnosis`, `monitor_only`, and `blocked_data_quality` modes; `candidate_generation_allowed` only controls whether an explicit generate action may be shown; Launchpad-derived prefill preserves `is_rebalance_recommendation: false`.
- Related documents: [block_4_diagnosis_v3_spec.md](docs/specs/block_4_diagnosis_v3_spec.md), [candidate_launchpad_spec.md](docs/specs/candidate_launchpad_spec.md), [portfolio_alternatives_builder_spec.md](docs/specs/portfolio_alternatives_builder_spec.md), [Block 4 to Portfolio Alternatives Builder Handoff](docs/exec_plans/2026-06-04_block_4_portfolio_alternatives_builder_handoff.md).
- Review trigger: Revisit if Builder becomes a persistent UI artifact, starts writing generated setup files, or if Decision Verdict semantics are migrated to a new schema.

Decision ID: DEC-2026-06-04-001
Title: Block 4 v3 diagnosis-first contract replaces score-heavy v2 product path

- Status: accepted (implemented)
- Date: 2026-06-04
- Decision: Use `problem_classification_v3` and `candidate_launchpad_v3` as the current Block 4 product contracts on the same filenames. Block 4 must present one clear investment diagnosis/outcome with root cause, supporting symptoms, max-five key evidence, why-not-other-problems, confidence/materiality/actionability, `next_diagnostic_step`, and launchpad success criteria.
- Context: User review found the prior Block 4 contract too score-heavy and product-risky when mixed evidence could become the primary verdict.
- Rationale: Portfolio MRI should read as a professional current-portfolio diagnosis, not as a scoring dashboard. Root-cause triage gives a clearer investment thesis and prevents symptoms such as volatility or drawdown from becoming shallow primary conclusions when stress evidence identifies a deeper issue.
- Alternatives considered: Keep v2 schema and add more score weights (rejected — increases opacity); keep conflict as a normal primary verdict (rejected — sounds like the system failed); preserve v2 as a current legacy product path (rejected — current product contract should be unambiguous).
- Assumptions: Blocks 1-3 evidence and formulas remain unchanged; scoring remains useful as backend audit metadata but should not dominate user-facing output.
- Consequences: Current validators are `check_problem_classification_v3`, `check_candidate_launchpad_v3`, and `check_block_4_v3_diagnosis_handoff`; `mixed_evidence_no_action` replaces the old conflict-as-primary behavior; Launchpad cards require success criteria. Block 4 must always expose a next diagnostic step: targeted hypothesis test for actionable diagnoses, data-quality improvement for unreliable evidence, or Equal Weight / Risk Parity reference benchmark tests for mixed or acceptable outcomes. These reference tests are not rebalance recommendations; Decision Verdict remains the downstream rebalance decision boundary.
- Related documents: [block_4_diagnosis_v3_spec.md](docs/specs/block_4_diagnosis_v3_spec.md), [Block 4 v3 Investment Diagnosis Plan](docs/exec_plans/2026-06-04_block_4_v3_investment_diagnosis_plan.md).
- Review trigger: Revisit only on a future breaking schema bump or validated historical model replacing the expert-rule triage.

Decision ID: DEC-2026-05-29-013
Title: Block 4 v2 additive migration with transitional V1 compatibility shim

- Status: accepted (implemented — Session 14 closure 2026-05-29)
- Date: 2026-05-29
- Decision: Upgrade Block 4 entry from thin `problem_classification_v1` to structured `Block 4 v2 problem-classification schema` (evidence extraction → scoring → severity/confidence → prioritization → actions → launchpad) via additive schema bump on the same filenames (`analysis_subject/problem_classification.json`, `candidate_launchpad.json`). During Sessions 10–13, dual validation ran; compatibility shim (`problems[]` mirror, severity `medium` → `moderate`) retained. **Session 14:** V1 product validators removed; that contract was canonical for live E2E and decision-entry tests until DEC-2026-06-04-001 superseded it; legacy V1 builders remain for unit tests only. Block 4 remains read-only over Blocks 2–3.
- Context: [Block 4 v2 Session 00 gap audit](docs/audits/2026-05-29_block_4_v2_session_00_gap_audit.md); V1 accepted Session 09 but uses legacy `sections.*` readers, severity-only prioritization, and 9 problem IDs vs 15-target taxonomy.
- Rationale: Institutional diagnosis requires auditable evidence_refs and honest no-trade outcomes without breaking operators mid-migration.
- Alternatives considered: In-place V1 rewrite without schema_version bump (rejected — silent contract drift); separate bundle files (rejected — six-file product bundle unchanged); big-bang cutover without shim (rejected — breaks Session 09 E2E gates).
- Assumptions: Blocks 2.1–2.6 and 3.3–3.4 product blocks remain stable evidence sources; core-only hygiene continues to omit Block 4 artifacts.
- Consequences: ExecPlan [Block 4 v2 Evidence-to-Problem](docs/exec_plans/2026-05-29_block_4_v2_evidence_to_problem_plan.md) **Completed**; `src/block_4/` package; `config/block_4_thresholds.yml`; [Session 14 closure audit](docs/audits/2026-05-29_block_4_v2_session_14_institutional_closure.md).
- Related documents: DEC-2026-05-29-011, [problem_classification_spec.md](docs/specs/problem_classification_spec.md), [candidate_launchpad_spec.md](docs/specs/candidate_launchpad_spec.md).
- Review trigger: Closed Session 14 — superseded by DEC-2026-06-04-001.

Decision ID: DEC-2026-05-29-012
Title: Block 5 compare/verdict validated via product contracts and live E2E (Session 10)

- Status: accepted
- Date: 2026-05-29
- Decision: Current vs Candidate (`current_vs_candidate_v1`) and Decision Verdict (`decision_verdict_v1`) at `{output_dir_final}/` are gated by shared product-contract validators in `scripts/core_mvp_validation_contract.py` and enforced in `validate_live_core_artifacts` for `product_one_candidate` when compare artifacts exist (handoff from scoped `candidate_comparison.json`; tombstone `no_candidate_v1` cannot form a live compare handoff).
- Context: Phase D Session 10 after Session 09 Block 4 closure; Block 5 builders existed but lacked the same institutional contract + live profile gates as Blocks 3–4.
- Rationale: One-candidate product path must expose authoritative root compare/verdict JSON with fail-loud drift detection before Sessions 11–12 extend decision-package grounding.
- Alternatives considered: Validate only in offline unit tests (rejected — no operator workspace proof); merge verdict into `candidate_comparison.json` only (rejected — separate product contracts per spec).
- Assumptions: `write_candidate_comparison_outputs()` continues to emit CVC + verdict after factory compare on `explicit_list` runs; diagnosis-only runs keep tombstone and omit Block 5 handoff.
- Consequences: `tests/test_block_5_decision_compare_contract.py`; live E2E evidence keys `block_5_*`; Session 11+ can add AI commentary / package validators on the same pattern.
- Related documents: [Session 10 audit](docs/audits/2026-05-29_block_5_session_10_current_vs_candidate_decision_verdict.md), [current_vs_candidate_spec.md](docs/specs/current_vs_candidate_spec.md), [decision_verdict_spec.md](docs/specs/decision_verdict_spec.md), DEC-2026-05-29-011.
- Review trigger: Revisit if Block 5 schema version bumps or product adds multi-candidate shortlist compare as default Core MVP path.

Decision ID: DEC-2026-05-29-011
Title: Block 4 decision entry validated via product contracts and live E2E (Session 09)

- Status: accepted
- Date: 2026-05-29
- Decision: Problem Classification (`problem_classification_v1`) and Candidate Launchpad (`candidate_launchpad_v1`) under `analysis_subject/` are gated by shared product-contract validators in `scripts/core_mvp_validation_contract.py` and enforced in `validate_live_core_artifacts` for `diagnosis_only` and `product_one_candidate` profiles (handoff + schema + no weights on cards).
- Context: Phase D Session 09 after Phase A `READY_FOR_DECISION_WORKFLOW`; Block 4 logic existed but lacked institutional contract checks comparable to Blocks 3.3/3.4.
- Rationale: Decision Workflow UI and operators need the same “fail loud on contract drift” standard as Blocks 1–3; offline tests alone are insufficient without live profile integration.
- Alternatives considered: Only document specs without validators (rejected — regression risk); merge Block 4 into a separate script (rejected — duplicate subject checks).
- Assumptions: `run_report.py` continues to write PC then Launchpad on non–core-only materialize; core-only runs remain without Block 4 subject files.
- Consequences: `tests/test_block_4_decision_entry_contract.py`; live E2E evidence keys `block_4_*`; Session 10+ extended compare/verdict on same pattern. **Superseded for live gates (Session 14):** v2 validators replace v1 per `DEC-2026-05-29-013`.
- Related documents: [Session 09 audit](docs/audits/2026-05-29_block_4_session_09_problem_classification_launchpad.md), [problem_classification_spec.md](docs/specs/problem_classification_spec.md), [candidate_launchpad_spec.md](docs/specs/candidate_launchpad_spec.md), DEC-2026-05-29-010.
- Review trigger: Revisit if Block 4 schema version bumps or Launchpad gains portfolio-generating cards in product V1.

Decision ID: DEC-2026-05-29-010
Title: Blocks 1–3 diagnostic foundation ready for Decision Workflow (Phase A closure)

- Status: accepted
- Date: 2026-05-29
- Decision: After ExecPlan Phase A Sessions 01–06, the project treats Blocks 1–3 runtime artifact scope as **frozen for Decision Workflow entry**: verdict **`READY_FOR_DECISION_WORKFLOW`**; operators use [runtime_artifact_contract.md](docs/runtime_artifact_contract.md) and `scripts/verify_live_core_e2e.py` (auto-detect or `--profile`) after each canonical CLI. Pre-decision audit `NOT_READY_RUNTIME_CONTRACT_MISMATCH` is superseded by [foundation closure audit](docs/audits/2026-05-29_blocks_1_3_foundation_closure_audit.md).
- Context: Pre-decision audit (2026-05-29) blocked Decision Workflow on R2–R5 (stale compare, 19-row menu, core-only leakage, E2E false failures). Sessions 02–05 implemented fixes; Session 06 re-ran three CLIs and re-scored acceptance criteria 1–18.
- Rationale: Live evidence on demo portfolio plus **261** pytest passes demonstrates product-scoped comparison and hygiene; downstream Blocks 4–7 consumers can treat root compare JSON as authoritative when tombstone / scope metadata match the active CLI mode.
- Alternatives considered: Keep `NOT_READY` until R6/R7 polish (rejected — P2 UX/scoring gaps do not invalidate runtime contract); skip live re-run and rely on offline tests only (rejected — audit required operator workspace proof).
- Assumptions: Research batches with `core_fast` still use `research_batch_core_fast` profile; optional R6/R7 remain non-blocking backlog.
- Consequences: Phase D (Decision workflow Sessions 09–12) may proceed; ExecPlan Phase A marked complete; `docs/audits/README.md` active closure pointer updated.
- Related documents: [docs/exec_plans/2026-05-29_blocks_1_3_post_audit_development_plan.md](docs/exec_plans/2026-05-29_blocks_1_3_post_audit_development_plan.md), DEC-2026-05-29-006 through DEC-2026-05-29-009, [docs/audits/2026-05-29_blocks_1_3_foundation_closure_audit.md](docs/audits/2026-05-29_blocks_1_3_foundation_closure_audit.md).
- Review trigger: Re-open if a canonical CLI regresses artifact contract without a spec change, or if product introduces a fifth runtime mode without validator profile.

Decision ID: DEC-2026-05-29-009
Title: Live core E2E validator uses runtime artifact profiles (R5)

- Status: accepted
- Date: 2026-05-29
- Decision: `validate_live_core_artifacts` auto-detects one of four profiles from on-disk layout and applies profile-specific root checks: `core_blocks_1_3` (no Block 4+ subject or root compare files), `diagnosis_only` (`no_candidate_v1` tombstones, diagnosis bundle present, no factory), `product_one_candidate` (`explicit_list` factory + scoped `product_candidate_scope`), `research_batch_core_fast` (legacy RM-1021 `core_fast` menu gate). Callers may override with `profile=`. `scripts/verify_live_core_e2e.py` prints `detected_profile` and supports `--profile`.
- Context: Pre-decision audit R5 — validator assumed every workspace was a `core_fast` batch compare (`review_mode=core`, 19-row menu), so one-candidate and diagnosis-only workspaces failed after Sessions 02–04 fixes.
- Rationale: Operator acceptance must match the three canonical CLIs in [runtime_artifact_contract.md](docs/runtime_artifact_contract.md) without false failures on scoped comparison or tombstones.
- Alternatives considered: Re-run only `core_fast` before validate (rejected — wrong product contract); drop comparison checks entirely (rejected — loses regression signal); separate scripts per mode (rejected — duplicated subject Block 1–3 checks).
- Assumptions: Profile detection prioritizes `candidate_factory_run.factory_profile_id` when present; tombstone `no_candidate_v1` marks diagnosis-only compare roots.
- Consequences: `tests/test_live_core_e2e_validation.py` covers all four profiles; DEC-2026-05-29-006 consequence (live E2E alignment) closed; Session 06 re-audit can require `verify_live_core_e2e.py` after each CLI on a clean tree.
- Related documents: [docs/exec_plans/2026-05-29_blocks_1_3_post_audit_development_plan.md](docs/exec_plans/2026-05-29_blocks_1_3_post_audit_development_plan.md), [docs/runtime_artifact_contract.md](docs/runtime_artifact_contract.md), [src/live_core_e2e.py](src/live_core_e2e.py), DEC-2026-05-29-006.
- Review trigger: Revisit if a fifth profile (e.g. `default_v1` research batch) needs first-class validation separate from `research_batch_core_fast`.

Decision ID: DEC-2026-05-29-008
Title: Core Blocks 1–3 runs prune stale Block 4+ subject and root compare JSON

- Status: accepted
- Date: 2026-05-29
- Decision: After successful `run_materialize_analysis_subject_report` with `core_diagnostics_only=True` (`product_bundle_scope=core_blocks_1_3`), call `apply_core_blocks_product_bundle_hygiene` to **delete** stale `analysis_subject/{problem_classification,candidate_launchpad,ai_commentary_context}.json` and all root post-compare/decision JSON (compare, verdict, factory, selection, advanced package). Core-only root artifacts remain **absent** (not tombstoned). Blocks 1–3 subject JSON (`portfolio_xray`, `stress_report`, snapshots, manifest) is untouched.
- Context: Pre-decision audit R4 — `run_core_diagnostics.py` refreshed Blocks 1–3 but left Block 4+ product JSON from prior full review looking authoritative on disk while manifest excluded those keys.
- Rationale: Operators and validators must not read stale Problem Classification / Launchpad / compare files after a core-only run; deletion matches runtime contract “Absent” for core mode root artifacts.
- Alternatives considered: Tombstone Block 4+ subject files (rejected — core mode contract is absence, not “not authoritative” sentinel); rely on manifest only (rejected — files remained on disk); prune in a separate CLI step (rejected — hygiene must be automatic on materialize).
- Assumptions: Diagnosis-only path continues to use Session 03 tombstones at variant root; one-candidate compare overwrites root JSON normally.
- Consequences: `apply_core_blocks_product_bundle_hygiene` in `src/product_bundle_hygiene.py`; tests in `tests/test_product_bundle_hygiene.py`; runtime artifact contract Session 04 rows updated.
- Related documents: [docs/exec_plans/2026-05-29_blocks_1_3_post_audit_development_plan.md](docs/exec_plans/2026-05-29_blocks_1_3_post_audit_development_plan.md), [docs/runtime_artifact_contract.md](docs/runtime_artifact_contract.md), DEC-2026-05-29-007.
- Review trigger: Revisit if core-only should retain diagnosis-only tombstones at root for UI consistency.

Decision ID: DEC-2026-05-29-007
Title: Diagnosis-only runs tombstone stale post-compare root JSON

- Status: accepted
- Date: 2026-05-29
- Decision: After successful `run_materialize_analysis_subject_report` on the diagnosis-only product path (not `core_diagnostics_only`), call `apply_diagnosis_only_product_bundle_hygiene` on `{output_dir_final}` to write explicit `no_candidate_v1` tombstones to `current_vs_candidate.json`, `decision_verdict.json`, and `candidate_comparison.json`, and remove stale advanced compare artifacts (`selection_decision.json`, registry, health/robustness, action/journal, etc.). Tombstones carry `artifact_status: not_authoritative` and `workflow_state: diagnosis_only`. Core-only runs (`core_blocks_1_3`) do **not** invoke hygiene (Session 04 handles subject-side prune).
- Context: Pre-decision audit R3 — default `run_portfolio_review.py` left stale `decision_verdict.json` / `current_vs_candidate.json` from prior one-candidate runs, misleading operators and UI consumers.
- Rationale: Explicit tombstones remove absent-file vs stale-file ambiguity while preserving a machine-readable signal that no candidate was selected for this run.
- Alternatives considered: Silent delete only (rejected — UI may interpret missing files as “not yet run”); leave stale files (rejected — audit failure); tombstone only verdict without comparison file (rejected — comparison menu was the primary misread surface before Session 02 scoping).
- Assumptions: One-candidate and research-batch runs still overwrite tombstones via `write_candidate_comparison_outputs`; hygiene runs only at end of non-core materialization.
- Consequences: `tests/test_product_bundle_hygiene.py`, updated architecture consistency test, runtime artifact contract Session 03 rows; operators must check `tombstone` / `artifact_status` before treating root compare JSON as authoritative on diagnosis-only runs. Core-only prune is separate (DEC-2026-05-29-008).
- Related documents: [docs/exec_plans/2026-05-29_blocks_1_3_post_audit_development_plan.md](docs/exec_plans/2026-05-29_blocks_1_3_post_audit_development_plan.md), [docs/runtime_artifact_contract.md](docs/runtime_artifact_contract.md), [src/product_bundle_hygiene.py](src/product_bundle_hygiene.py), DEC-2026-05-29-006.
- Review trigger: Revisit if product UI prefers absent files over tombstones, or if hygiene should also run from a standalone CLI flag.

Decision ID: DEC-2026-05-29-006
Title: Product candidate comparison scopes JSON write for explicit-list factory runs

- Status: accepted
- Date: 2026-05-29
- Decision: When `candidate_factory_run.json` uses `factory_profile_id: explicit_list`, `write_candidate_comparison_outputs` writes the **product-scoped** comparison document (baseline + `product_candidate_scope.candidate_ids` only) to `candidate_comparison.json`. The full on-disk candidate scan remains available as `candidate_comparison_registry.json` with cross-reference fields (`full_comparison_registry_artifact` on product doc; `product_comparison_artifact` on registry doc). Batch / research compare paths (`advanced_package=True`, no explicit-list scope) continue to write the full registry to `candidate_comparison.json` unchanged.
- Context: Pre-decision foundation audit (2026-05-29) found one-candidate CLI runs left **19-row** `candidate_comparison.json` while product adapters (`current_vs_candidate`, `decision_verdict`) were already scoped — operators could misread the comparison menu as the product answer (gap R2).
- Rationale: Core MVP one-candidate and shortlist UX must not require filtering stale on-disk variant folders; advanced multi-candidate research still needs the full registry artifact without breaking existing compare consumers.
- Alternatives considered: Filter rows only in UI adapters while leaving JSON full (rejected — stale file remains authoritative on disk); omit full registry entirely (rejected — research and debugging still need on-disk scan); tombstone-only without scoped rewrite (deferred to Session 03 for diagnosis-only stale compare).
- Assumptions: `scoped_product_comparison` and `product_candidate_ids_from_factory_run` remain the scoping source; `current_vs_candidate.json` and product verdict paths already consume scoped comparison in memory.
- Consequences: Operators read `candidate_comparison.json` as product truth for explicit-list runs; use `candidate_comparison_registry.json` for full menu / research. Update OUTPUTS, runtime artifact contract, and comparison regression tests; live E2E profile alignment closed in Session 05 ([DEC-2026-05-29-009](DECISIONS.md)).
- Related documents: [docs/exec_plans/2026-05-29_blocks_1_3_post_audit_development_plan.md](docs/exec_plans/2026-05-29_blocks_1_3_post_audit_development_plan.md), [docs/runtime_artifact_contract.md](docs/runtime_artifact_contract.md), [docs/audits/2026-05-29_blocks_1_3_pre_decision_diagnostic_foundation_audit.md](docs/audits/2026-05-29_blocks_1_3_pre_decision_diagnostic_foundation_audit.md), [docs/specs/candidate_comparison_spec.md](docs/specs/candidate_comparison_spec.md), [src/candidate_comparison.py](src/candidate_comparison.py).
- Review trigger: Revisit if product menu must also scope `candidate_menu` counts in the same write, or if registry artifact should move under an `advanced_evidence/` subfolder.

Decision ID: DEC-2026-05-29-001
Title: Block 2.6 uses canonical Stress Lab risk ids and heuristic_v2 scoring

- Status: accepted
- Date: 2026-05-29
- Decision: Block 2.6 Portfolio Weakness Map is the pre-stress vulnerability map using exactly eight canonical Stress Lab risk identifiers (`equity_shock`, `credit_shock`, `rates_shock`, `inflation_stagflation`, `liquidity_shock`, `usd_shock`, `commodity_shock`, `recession_severe`) as `risk_type` values, with `score_0_100` based on a transparent `heuristic_v2` ruleset over Blocks 2.1–2.5. Legacy weakness ids (`equity_crash`, `rates_up`, `inflation_shock`, `credit_spreads`, `liquidity_shock`, `usd_shock`, `commodity_shock`, `volatility_spike`, `recession`) remain only in `sections.weakness_map` and may be exposed as a read-only alias map in Block 2.6 metadata for one release. Block 2.6 must not read `stress_report.json` or Stress Lab loss/attribution blocks and may only output `next_tests` pointing to Stress Lab scenarios.
- Context: The v1 Block 2.6 MVP used a parallel weakness namespace with nine ids and a `heuristic_v1` ruleset, while Stress Lab scenarios, hedge gap, and historical replay use the canonical synthetic ids. This created naming drift and made it harder for operators to see which pre-stress weaknesses correspond to which crash tests. The product also needs institutional-grade, explainable scoring and narrative output that can be shown directly to advisors and institutional clients.
- Rationale: Aligning Block 2.6 `risk_type` with Stress Lab `scenario_id` simplifies reasoning about which weaknesses map to which stress scenarios, avoids duplicate naming layers, and clarifies that Block 2.6 is a pre-stress hypothesis map, not a mini Stress Lab. Moving to `heuristic_v2` with explicit rule tables, status bands, confidence model v2, and narrative fields improves transparency and makes the Weakness Map suitable for professional use.
- Alternatives considered: Keep the nine v1 weakness ids and add a separate `linked_scenarios` field (rejected because it preserves naming confusion and makes downstream mapping more complex); extend Block 2.6 to read `stress_report` and reuse Stress Lab loss numbers directly (rejected because it breaks the architecture boundary and duplicates Stress Lab responsibilities); keep `heuristic_v1` and only patch usd_shock (rejected because it would not address institutional transparency requirements).
- Assumptions: Stress Lab synthetic scenario ids remain fixed as defined in `SYNTHETIC_SCENARIO_IDS` and Stress Lab layer specs; Block 2.3 continues to export factor betas and variance contributions; Block 2.4 `heuristic_v2` remains the single source for hidden exposure alert status, confidence, evidence, and contributing assets. Any consumer that still needs v1 weakness ids can read them from legacy `sections.weakness_map` or from a transitional alias map in Block 2.6 metadata.
- Consequences: Specs and contracts must describe Block 2.6 using canonical Stress Lab-aligned ids and `heuristic_v2`; unit and contract tests must assert the eight-risk set and forbid `volatility_spike` in the product block; Problem Classification, AI commentary grounding, and X-Ray formatters should migrate to `block_2_6_portfolio_weakness_map` as the single source of truth for pre-stress weakness diagnosis. Legacy `sections.weakness_map` remains available for backward compatibility and legacy report surfaces but must not drive new product-facing conclusions after migration.
- Related documents: [docs/specs/portfolio_xray_diagnostics_spec.md](docs/specs/portfolio_xray_diagnostics_spec.md) §2.6.1, [docs/specs/block_2_6_weakness_map_ui_pareto_spec.md](docs/specs/block_2_6_weakness_map_ui_pareto_spec.md), [docs/specs/stress_lab_layer_spec.md](docs/specs/stress_lab_layer_spec.md), [docs/specs/stress_testing_spec.md](docs/specs/stress_testing_spec.md), [docs/exec_plans/2026-05-29_block_2_6_weakness_map_heuristic_v2_plan.md](docs/exec_plans/2026-05-29_block_2_6_weakness_map_heuristic_v2_plan.md) (**Completed**), [docs/audits/2026-05-29_block_2_6_weakness_map_heuristic_v2_acceptance_audit.md](docs/audits/2026-05-29_block_2_6_weakness_map_heuristic_v2_acceptance_audit.md).
- Review trigger: Revisit if Stress Lab scenario ids are extended or renamed, or if product requires exposing additional, non-Stress-Lab weakness types in Block 2.6 beyond the canonical eight.

Decision ID: DEC-2026-05-29-003
Title: Block 3.3 institutional upgrade — v1-primary downstream and main-gap scoring v2

- Status: accepted
- Date: 2026-05-29
- Decision: Complete Phase 2 institutional upgrade on `hedge_gap_analysis_v1`: eight protection rows (`recession_severe_protection` included), product contract v1.1 fields, calculation hardening, `hedge_gap_rules_v1_2` weighted `main_gap_score` selection, read-only confirmation bridges to Block 2.4 (`hidden_exposure_confirmation`) and Block 2.6 (`weakness_map_confirmation`), and v1-primary downstream surfaces (Problem Classification with `hedge_gap_source`, `candidate_comparison.hedge_gap_comparison`, `ai_commentary_context.hedge_gap_context`, snapshot/scorecard mirrors, `scripts/core_mvp_validation_contract.check_hedge_gap_analysis_v1`). Legacy `hedge_gap_analysis` and `stress_conclusions.hedge_gap_status` remain secondary; do not extend legacy for new product behavior.
- Context: MVP Block 3.3 (2026-05-27) delivered contribution-based offset coverage but legacy taxonomy hedge block was often `not_applicable`, main-gap selection favored tiny zero-offset losses, and consumers still read `hedge_gap_status`. Phase 2 ExecPlan Sessions 02–10 closed implementation gaps before acceptance audit.
- Rationale: Institutional-grade hedge-gap diagnosis requires transparent scoring, cross-block confirmation without circular imports, and a single v1 read path for classification, comparison, commentary grounding, and Core MVP validation — without re-running stress or pre-labeling hedges.
- Alternatives considered: Migrate by overwriting legacy `hedge_gap_analysis` in place (rejected — breaks contract tests and taxonomy semantics); drive Block 3.3 from `portfolio_xray.json` (rejected — Stress Lab boundary); drop legacy block in this wave (deferred — compatibility for scorecard rollups and older commentary paths).
- Assumptions: Block 3.2 `stress_results_v1` remains the evidence source for per-scenario contributions; bridges are attach-time only via `build_portfolio_xray_v2` kwargs; Block 2.6 does not read `stress_report.json`.
- Consequences: SPEC/OUTPUTS/TESTING document Block 3.3 as **Implemented**; regression bundle includes materialization, downstream integration, and live E2E validator tests; Session 12 acceptance audit closes the institutional upgrade ExecPlan; legacy deprecation waits until all external consumers drop `hedge_gap_status`-only paths.
- Related documents: [docs/exec_plans/2026-05-29_block_3_3_hedge_gap_institutional_upgrade_plan.md](docs/exec_plans/2026-05-29_block_3_3_hedge_gap_institutional_upgrade_plan.md), [docs/specs/hedge_gap_analysis_spec.md](docs/specs/hedge_gap_analysis_spec.md), DEC-2026-05-27-002, [docs/audits/2026-05-29_block_3_3_session_11_documentation_sync.md](docs/audits/2026-05-29_block_3_3_session_11_documentation_sync.md).
- Review trigger: Revisit when legacy `hedge_gap_analysis` / `stress_conclusions.hedge_gap_status` can be deprecated or when main-gap scoring rules change (`ruleset_version` bump).

Decision ID: DEC-2026-05-29-005
Title: Block 3.4 institutional upgrade — v1-primary downstream and live-output gates

- Status: accepted
- Date: 2026-05-29
- Decision: Complete Phase 2 institutional upgrade on `current_portfolio_stress_scorecard_v1`: v1.1 product fields (`stress_diagnosis`, summaries, `stress_coverage`, optional `pre_stress_confirmation_summary`), downstream signal blocks, v1-primary consumers (Problem Classification with `stress_scorecard_source` and `problem_classification_signals`, `candidate_comparison.stress_scorecard_comparison`, `ai_commentary_context.current_portfolio_stress_scorecard_context`, snapshot mirror, `scripts/core_mvp_validation_contract.check_current_portfolio_stress_scorecard_v1` with live-output gates). Legacy `stress_scorecard_v1` remains for explicit mandate rollup only; `legacy_fallback_used` must be a boolean on Block 3.4.
- Context: MVP Block 3.4 (DEC-2026-05-27-003) and frozen contract (DEC-2026-05-29-004) defined the key; Sessions 02–11 implemented builders and migrations; documentation and top-level SPEC/OUTPUTS still described Phase 2 as in progress until Session 12.
- Rationale: Institutional executive stress diagnosis requires a single v1 read path for classification, comparison, commentary grounding, and Core MVP validation — without recomputing stress or emitting mandate pass/fail inside Block 3.4.
- Alternatives considered: Repurpose `stress_scorecard_v1` as the only scorecard (rejected — mandate semantics); drop legacy scorecard in Phase 2 (deferred — mandate path); drive Block 3.4 from X-Ray only (rejected — Stress Lab boundary).
- Assumptions: Worst selectors remain on Block 3.2 envelope; hedge gap evidence remains `hedge_gap_analysis_v1` only; optional 2.4/2.6 bridges do not downgrade `block_status`.
- Consequences: SPEC/OUTPUTS/TESTING document Block 3.4 as **Implemented**; regression bundle includes materialization, downstream integration, and live E2E validator tests; Session 13 acceptance audit closed the institutional upgrade ExecPlan ([acceptance audit](docs/audits/2026-05-29_block_3_4_institutional_upgrade_acceptance_audit.md)); legacy deprecation waits until all external consumers drop `stress_scorecard_v1`-only paths.
- Related documents: [docs/exec_plans/2026-05-29_block_3_4_current_portfolio_stress_scorecard_institutional_upgrade_plan.md](docs/exec_plans/2026-05-29_block_3_4_current_portfolio_stress_scorecard_institutional_upgrade_plan.md), [docs/specs/current_portfolio_stress_scorecard_spec.md](docs/specs/current_portfolio_stress_scorecard_spec.md), DEC-2026-05-29-004, DEC-2026-05-27-003, [docs/audits/2026-05-29_block_3_4_session_12_documentation_sync.md](docs/audits/2026-05-29_block_3_4_session_12_documentation_sync.md).
- Review trigger: Revisit when `stress_scorecard_v1` can be deprecated for all Core MVP consumers or when diagnosis_confidence / worst-selector rules change (`ruleset_version` bump).

Decision ID: DEC-2026-05-29-004
Title: Block 3.4 institutional upgrade — frozen v1.1 scorecard contract (Session 01)

- Status: accepted
- Date: 2026-05-29
- Decision: Freeze Phase 2 product contract for `current_portfolio_stress_scorecard_v1` under ruleset `current_portfolio_stress_scorecard_rules_v1_1` in [current_portfolio_stress_scorecard_spec.md](docs/specs/current_portfolio_stress_scorecard_spec.md): executive stress diagnosis read-only over Blocks 3.1–3.3; `stress_diagnosis.diagnosis_confidence` enum; `next_decision_uses[]`; `relatively_resilient_scenarios` / `less_damaging_scenarios` (no “passes normally”); optional 2.4/2.6 `pre_stress_confirmation_summary` with `not_applicable` when unattached; Core MVP must not create internal mandate pass/fail (`legacy_fallback_used` boolean for explicit legacy scorecard use). Keep MVP field names one release alongside v1.1 aliases. Implementation Sessions 02–11 follow the spec status matrix.
- Context: MVP Block 3.4 (2026-05-27) ships an adapter but lacks institutional metadata, structured diagnosis, downstream signals, and v1-primary consumers (Problem Classification, Candidate Comparison, AI Commentary still prefer `stress_scorecard_v1`).
- Rationale: A dedicated frozen spec separates diagnostic Core MVP scorecard from legacy mandate scorecard, mirrors Block 3.3 institutional upgrade pattern, and gives implementers a single contract before code changes.
- Alternatives considered: Extend `stress_lab_layer_spec.md` only without a dedicated spec (rejected — insufficient depth for v1.1 field rules); merge Block 3.4 into Block 3.2 envelope (rejected — product layer and downstream hooks are distinct); remove `stress_scorecard_v1` in Phase 2 (rejected — mandate path and explicit fallback required).
- Assumptions: Worst synthetic/historical selectors remain owned by Block 3.2 envelope; hedge gap evidence remains `hedge_gap_analysis_v1` only; `block_status` for 3.4 is derived from stress blocks, not from optional X-Ray bridges.
- Consequences: SPEC indexes dedicated spec; Phase 2 ExecPlan Session 01 closed; Sessions 02–11 implemented against the spec matrix (see DEC-2026-05-29-005); Session 12 synced SPEC/OUTPUTS/TESTING; acceptance at Session 13 requires live-output gates in the spec.
- Related documents: [docs/exec_plans/2026-05-29_block_3_4_current_portfolio_stress_scorecard_institutional_upgrade_plan.md](docs/exec_plans/2026-05-29_block_3_4_current_portfolio_stress_scorecard_institutional_upgrade_plan.md), [docs/audits/2026-05-29_block_3_4_session_01_contract_v1_1.md](docs/audits/2026-05-29_block_3_4_session_01_contract_v1_1.md), DEC-2026-05-27-003 (MVP scorecard key), DEC-2026-05-29-005.
- Review trigger: Revisit when `stress_scorecard_v1` can be deprecated for all Core MVP consumers or when diagnosis_confidence rules change (`ruleset_version` bump).

Decision ID: DEC-2026-05-28-001
Title: Core MVP historical stress replay is direct-history-only on the product surface

- Status: accepted
- Date: 2026-05-28
- Decision: On portfolio-first diagnostic stress reports (`loss_gate_mode="diagnostic"`), populate `stress_report.json.historical_stress_replay_v1` (`policy: direct_history_only`) and merge its fields into Block 3.2 `stress_results_v1.historical_episodes[]`. A position counts only when its own ticker has usable direct monthly returns in the episode window (`min_coverage_ratio` 0.45, dates from `HISTORICAL_EPISODES`). Do not substitute missing positions with ETF proxies, asset-class proxies, factor replay, or index/company proxies in these outputs. Portfolio-level `portfolio_loss_pct` / `drawdown_pct` on Block 3.2 historical rows are allowed only when `portfolio_level_result_available` is true (full direct coverage). Partial or unavailable replay must surface explicit unavailable weight, positions, and English `user_note` / `diagnosis_summary_en`; legacy `historical_results` realized PnL must not override cleared portfolio metrics.
- Context: Modern portfolios include young ETFs and stocks without dot-com/2008 history; showing a single portfolio loss from legacy realized paths misstates coverage. Normalized-library proxy waterfall (`historical_stress_fallback`, `config/historical_stress_proxy_map.yml`) remains for advanced/library consumers only (DEC-2026-05-20-001 boundary unchanged for primary `run_stress` `historical_results`).
- Rationale: Stress Test Lab must show honest crisis replay for the current book without false full-portfolio precision; direct-only product copy aligns with user trust and Block 3.2 diagnostic boundary.
- Alternatives considered: Reuse proxy waterfall in Core MVP replay (rejected — false precision); hide historical episodes when coverage is partial (rejected — hides the limitation); replace `historical_results` entirely in `run_stress` (deferred — breaking change for legacy mandate and conclusions rollups).
- Assumptions: `run_report.py` attaches replay before `attach_stress_results_v1`; cash proxy ticker is excluded from risk-weight coverage math per stress conventions; factor attribution on historical rows remains model-based overlay when enrichment exists.
- Consequences: Normative spec [core_mvp_historical_stress_replay_spec.md](docs/specs/core_mvp_historical_stress_replay_spec.md); implementation in `src/core_mvp_historical_stress_replay.py`; contract tests in `tests/test_core_mvp_historical_stress_replay_contract.py`; `data_trust_summary` may cite replay `diagnosis_summary_en` for partial episodes.
- Related documents: [docs/specs/stress_lab_layer_spec.md](docs/specs/stress_lab_layer_spec.md) §3.1.1, §3.2, [docs/specs/stress_testing_spec.md](docs/specs/stress_testing_spec.md) §9.4, [docs/exec_plans/2026-05-28_core_mvp_historical_stress_replay_plan.md](docs/exec_plans/2026-05-28_core_mvp_historical_stress_replay_plan.md), DEC-2026-05-20-001.
- Review trigger: Revisit if product requires Core MVP Stress Lab to show proxy-assisted historical fills on the same rows as honest replay, or if primary `run_stress` historical_results adopts per-asset proxy paths.

Decision ID: DEC-2026-05-27-002
Title: Block 3.3 is contribution-based Hedge Gap Analysis with legacy hedge block retained

- Status: accepted
- Date: 2026-05-27
- Decision: Define Block 3.3 Core MVP product contract as `hedge_gap_analysis_v1` on `stress_report.json` (contribution-based `offset_coverage_ratio` per eight synthetic-linked protection areas; no taxonomy hedge pre-labeling). Renumber Stress Lab Core MVP to 3.1 Scenario Library, 3.2 Stress Results, 3.3 Hedge Gap, 3.4 Scorecard; defer What Happens If simulator and Crisis Replay to advanced/deferred sub-blocks. Keep legacy `hedge_gap_analysis` (`stress_scenario_hedge_evidence_v2`) unchanged for backward compatibility.
- Context: Product brief requires hedge-gap diagnosis from signed scenario asset contributions without re-running stress or labeling hedge assets. Legacy block is often `not_applicable` when no hedge `risk_role` labels exist. Stress Lab layer spec previously numbered hedge gap as §3.5 and simulator as §3.3.
- Rationale: A dedicated v1 block gives stable product semantics (offset coverage, main hedge gap) aligned with Block 3.2 evidence; legacy block preserves `stress_conclusions.hedge_gap_status` and existing contract tests without a breaking migration in this wave.
- Alternatives considered: Extend legacy `hedge_gap_analysis` in place (rejected — taxonomy coupling and different risk-type ids); place Block 3.3 on `portfolio_xray.json` (rejected — Stress Lab boundary); include `recession_severe` as an eighth v1 row (initially rejected — product brief listed seven protection areas; **promoted 2026-05-27** as `recession_severe_protection` for fixture-matrix hedge-gap completeness without changing Stress Results architecture).
- Assumptions: Block 3.2 `stress_results_v1` remains the preferred read path for per-scenario `pnl_by_asset_pct`; Core MVP stays `loss_gate_mode="diagnostic"`; historical episodes stay out of v1 `by_risk_type[]` until a canonical episode→risk map exists.
- Consequences: Specs, PRODUCT §4.3.3, OUTPUTS, and TESTING reference `hedge_gap_analysis_v1` as the Core MVP hedge-gap contract. MVP ExecPlan Sessions 02–08 and institutional upgrade Sessions 02–10 (see DEC-2026-05-29-003) delivered implementation and v1-primary downstream migration; `stress_conclusions.hedge_gap_status` still mirrors **legacy** aggregate status only.
- Related documents: [docs/specs/hedge_gap_analysis_spec.md](docs/specs/hedge_gap_analysis_spec.md), [docs/specs/stress_lab_layer_spec.md](docs/specs/stress_lab_layer_spec.md), [docs/specs/stress_testing_spec.md](docs/specs/stress_testing_spec.md) §12.2.2, [PRODUCT.md](PRODUCT.md) §4.3.3, [docs/exec_plans/2026-05-27_block_3_3_hedge_gap_analysis_plan.md](docs/exec_plans/2026-05-27_block_3_3_hedge_gap_analysis_plan.md), [docs/exec_plans/2026-05-29_block_3_3_hedge_gap_institutional_upgrade_plan.md](docs/exec_plans/2026-05-29_block_3_3_hedge_gap_institutional_upgrade_plan.md), DEC-2026-05-29-003.
- Review trigger: Revisit when legacy `hedge_gap_analysis` / `hedge_gap_status` coupling can be deprecated (partially satisfied — Core MVP consumers migrated; legacy block retained).

Decision ID: DEC-2026-05-27-003
Title: Block 3.4 Core MVP is a new current-portfolio stress scorecard key

- Status: accepted
- Date: 2026-05-27
- Decision: Implement Block 3.4 Core MVP Current Portfolio Stress Scorecard as a new top-level key on `stress_report.json`: `current_portfolio_stress_scorecard_v1`, built as a diagnostic-only adapter over Blocks 3.1–3.3 (`scenario_results` / `historical_results`, `stress_results_v1`, `hedge_gap_analysis_v1`).
- Context: Existing `stress_scorecard_v1` is used by legacy/compat consumers and includes mandate-mode semantics and fields (`DIAG_*` overall statuses, `pass`/`loss_ok` on rows) that are explicitly forbidden in Core MVP diagnostic scorecard output.
- Rationale: A new key keeps backward compatibility for legacy scorecard consumers while delivering a clean product-facing Core MVP summary with explicit linkage to `stress_results_v1` and `hedge_gap_analysis_v1`.
- Alternatives considered: Repurpose `stress_scorecard_v1` as the Core MVP scorecard (rejected — breaks existing contract tests and would mix mandate-mode semantics into a diagnostic-only product layer).
- Assumptions: Block 3.2 remains the canonical selector for worst synthetic and worst historical; Block 3.3 remains the canonical source for offset coverage and main hedge gap; Core MVP portfolio-first path uses `loss_gate_mode="diagnostic"`.
- Consequences: Specs and output maps reference `current_portfolio_stress_scorecard_v1` as Block 3.4. MVP ExecPlan Sessions 02–06 and institutional upgrade Sessions 02–11 (see DEC-2026-05-29-004, DEC-2026-05-29-005) delivered v1.1 fields and v1-primary downstream migration; `stress_scorecard_v1` remains for mandate rollup only.
- Related documents: [docs/specs/stress_lab_layer_spec.md](docs/specs/stress_lab_layer_spec.md) §3.4, [docs/specs/current_portfolio_stress_scorecard_spec.md](docs/specs/current_portfolio_stress_scorecard_spec.md), [OUTPUTS.md](OUTPUTS.md), [TESTING.md](TESTING.md), [docs/exec_plans/2026-05-27_block_3_4_current_portfolio_stress_scorecard_plan.md](docs/exec_plans/2026-05-27_block_3_4_current_portfolio_stress_scorecard_plan.md), [docs/exec_plans/2026-05-29_block_3_4_current_portfolio_stress_scorecard_institutional_upgrade_plan.md](docs/exec_plans/2026-05-29_block_3_4_current_portfolio_stress_scorecard_institutional_upgrade_plan.md), DEC-2026-05-29-005.
- Review trigger: Revisit when legacy `stress_scorecard_v1` can be deprecated for all Core MVP consumers (partially satisfied — Core MVP consumers migrated; legacy block retained).

Decision ID: DEC-2026-05-27-001
Title: Block 3.2 is Stress Results with compatibility conclusions

- Status: accepted
- Date: 2026-05-27
- Decision: Define Block 3.2 product contract as `stress_results_v1` on `stress_report.json` and rename the Block 3.2 product/spec section to **Stress Results**. Keep `stress_conclusions` (`stress_conclusions_v1`) as a backward-compatible worst-case rollup for existing snapshot/comparison/commentary consumers.
- Context: Block 3.2 product brief requires per-scenario diagnosis output (what happened, drivers, offsets, trust) without forcing downstream consumers to parse raw `scenario_results` / `historical_results`. Existing contracts exposed scorecard/conclusions but lacked a dedicated per-scenario product-facing block.
- Rationale: A dedicated `stress_results_v1` block clarifies product boundary and supports stable downstream consumption while preserving compatibility with current consumers already tied to `stress_conclusions`.
- Alternatives considered: Replace `stress_conclusions` entirely (rejected because it would break existing consumers); keep only scorecard and raw arrays (rejected because product-facing per-scenario interpretation would remain fragmented).
- Assumptions: Canonical scenario IDs stay fixed by Scenario Library; Core MVP portfolio-first mode remains `loss_gate_mode="diagnostic"` and Block 3.2 product rows must not reintroduce mandate pass/fail fields.
- Consequences: Stress docs/specs/testing/output inventories must reference `stress_results_v1` as the Block 3.2 product contract; `stress_conclusions` remains present as compatibility rollup until an explicit migration removes it.
- Related documents: [docs/specs/stress_lab_layer_spec.md](docs/specs/stress_lab_layer_spec.md), [docs/specs/stress_testing_spec.md](docs/specs/stress_testing_spec.md), [PRODUCT.md](PRODUCT.md), [OUTPUTS.md](OUTPUTS.md), [TESTING.md](TESTING.md), [docs/exec_plans/2026-05-27_block_3_2_stress_results_plan.md](docs/exec_plans/2026-05-27_block_3_2_stress_results_plan.md).
- Review trigger: Revisit when downstream consumers migrate fully to `stress_results_v1` and `stress_conclusions` can be deprecated safely.

Decision ID: DEC-2026-05-25-001
Title: Documentation migration uses draft-first target documents

- Status: accepted
- Date: 2026-05-25
- Decision: The documentation migration uses a draft-first, archive-before-replace process for business, product, diagnostic concept, and architecture docs. The approved draft content has been merged into `BUSINESS_VISION.md`, `PRODUCT.md`, `docs/DIAGNOSTIC_PRODUCT_CONCEPT.md`, and `ARCHITECTURE.md`; pre-migration versions are archived under `docs/archive/documentation_migration_2026_05_25/`. Migration records do not override `SPEC.md`, `RULES.md`, `OUTPUTS.md`, `DATA.md`, `TESTING.md`, `docs/specs/*.md`, current code behavior, formulas, schemas, generated-output contracts, or existing implementation capabilities.
- Context: New DOCX product concept drafts redefine the target product around diagnosis-first decision support, current-vs-candidate comparison, no-trade verdicts, and AI commentary as explanation. Directly rewriting current source-of-truth files would risk claiming target behavior as current implementation or deleting useful advanced/legacy capabilities.
- Rationale: A draft-first migration lets the project map target product direction safely while preserving current implementation truth, output contracts, operator rules, and advanced/legacy capabilities.
- Alternatives considered: Rewrite current docs directly (rejected because it risks source-of-truth drift); treat DOCX concepts as immediately binding (rejected because product concepts do not verify code behavior); avoid migration entirely (rejected because current product narrative needs alignment with the new direction).
- Assumptions: Existing capabilities absent from the DOCX drafts should be classified as `Preserve`, `Advanced`, `Legacy`, or `Requires Review`, not deleted by default. Target modules such as Problem Classification, Candidate Launchpad, Portfolio Alternatives Builder, Decision Verdict language, and AI Commentary require code/spec verification before being stated as current implementation.
- Consequences: Agents and contributors may consult the migration plan, session audit, and archived legacy docs as traceability inputs only. Current behavior remains governed by canonical specs and code. Future product/architecture changes require review, stale-reference checks, and explicit verification of any implementation claims.
- Related documents: [DOCUMENTATION_MIGRATION_PLAN.md](DOCUMENTATION_MIGRATION_PLAN.md), [DOCUMENTATION_MIGRATION_SESSION09_AUDIT.md](DOCUMENTATION_MIGRATION_SESSION09_AUDIT.md), [BUSINESS_VISION.md](BUSINESS_VISION.md), [PRODUCT.md](PRODUCT.md), [Diagnostic Product Concept](docs/DIAGNOSTIC_PRODUCT_CONCEPT.md), [ARCHITECTURE.md](ARCHITECTURE.md), [SPEC.md](SPEC.md), [WORKFLOW.md](WORKFLOW.md), [OUTPUTS.md](OUTPUTS.md).
- Review trigger: Revisit when a target module is promoted to an owning spec, when archived legacy material must be restored, or when the migration strategy changes away from archive-before-replace governance.

Decision ID: DEC-2026-05-21-002
Title: Optimizer fallback quality is not clean success

- Status: accepted
- Date: 2026-05-21
- Decision: `OK_FALLBACK`, fallback branches, and approximate solver outputs must be disclosed as non-clean optimizer quality. Normalized quality statuses are `clean_solve`, `approximate_fallback`, `approximate_solver`, `failed_solver`, `failed`, and `unknown`; fallback/approximate quality degrades comparison evidence, and failed current factory or optimizer quality makes comparison evidence unavailable.
- Context: Block 5 Session 06 formalizes fallback and failure policy after Sessions 03-05 added optimizer metadata and comparison passthrough. Before this decision, an artifact with a valid `snapshot_10y.json` could look successful in factory/comparison even when upstream optimizer metadata described fallback or approximate quality.
- Rationale: Users need to distinguish a clean solve from a fallback or approximate solve before interpreting candidate comparison or Selection output. The project can preserve existing optimizer formulas and fallback branches while making their quality visible at boundaries.
- Alternatives considered: Treat fallback as ordinary success when weights exist (rejected because it hides model/solver quality); hard-fail all fallback outputs (rejected because fallback weights can still be useful review evidence); change optimizer formulas or retry logic (rejected because Session 06 is disclosure/boundary work only).
- Assumptions: Existing builder artifacts are the source of truth for solver/fallback evidence. Comparison and Selection must not recompute optimizer math.
- Consequences: Factory steps may carry optimizer quality fields in addition to orchestration status. `candidate_comparison.json` may degrade or mark unavailable rows based on visible optimizer/factory quality. `selection_decision.json` warns if a fallback/approximate optimizer row is favored. Optimizer formulas, fallback behavior, mandate gates, and generated weights are unchanged.
- Related documents: [optimization_engine_layer_spec.md](docs/specs/optimization_engine_layer_spec.md), [candidate_factory_spec.md](docs/specs/candidate_factory_spec.md), [candidate_comparison_spec.md](docs/specs/candidate_comparison_spec.md), [selection_engine_spec.md](docs/specs/selection_engine_spec.md), [Optimization Engine Post-Audit Roadmap](docs/exec_plans/2026-05-20_optimization_engine_post_audit_roadmap.md).
- Review trigger: Revisit if fallback outputs become hard-ineligible, if new solver quality states are added, or if Selection should exclude approximate optimizer rows entirely.

Decision ID: DEC-2026-05-21-001
Title: Target-only optimizer objectives require a future spec decision

- Status: accepted
- Date: 2026-05-21
- Decision: Max Sharpe, drawdown-controlled, macro-resilient, stress-test-optimized, tax-aware, and turnover-aware optimizer objectives are target-only concepts in the current Optimization Engine layer. They are not implemented legacy policy objectives, candidate optimizer objectives, robust optimizer modes, comparison candidate ids, hard constraints, mandate gates, or output contract fields unless a future accepted spec, implementation, tests, and documentation update explicitly add them.
- Context: Block 5 governance needs a project-level decision so product-concept names cannot drift into optimizer behavior by implication. Session 01 documented the boundary in the Optimization Engine layer spec; this decision records the methodology choice in the global decision log.
- Rationale: The project already ships multiple optimizer paths with different authority. Treating concept names as current objectives would silently change expectations for policy release, candidate comparison, solver disclosure, and reproducibility metadata.
- Alternatives considered: Implement placeholder optimizer modes now (rejected because Session 02 is governance-only and does not add formulas or solvers); rely only on the spec wording (rejected because this is a methodology boundary that belongs in the project decision log); hide concept names entirely (rejected because product documents may still use them as future direction when clearly labeled).
- Assumptions: New optimizer objectives require quantitative review, an owning spec section, implementation, focused tests, output-contract documentation, and a superseding or companion decision before release.
- Consequences: Future references to these names must label them as target-only, deferred, not implemented, or methodology proposals. Current runtime code, generated outputs, formulas, constraints, gates, and candidate registry remain unchanged by this decision.
- Related documents: [optimization_engine_layer_spec.md](docs/specs/optimization_engine_layer_spec.md), [Optimization Engine Post-Audit Roadmap](docs/exec_plans/2026-05-20_optimization_engine_post_audit_roadmap.md), [Optimization Engine Methodology Map](docs/audits/2026-05-20_optimization_engine_methodology_map.md), [candidate_portfolios_spec.md](docs/specs/candidate_portfolios_spec.md), [DIAGNOSTIC_PRODUCT_CONCEPT.md](docs/DIAGNOSTIC_PRODUCT_CONCEPT.md).
- Review trigger: Revisit when product requests one of these objectives as a shipped policy mode, candidate builder, comparison row, or public output contract.

Decision ID: DEC-2026-05-20-003
Title: Concept-only candidate families — registry boundary (Block 4 P5)

- Status: accepted
- Date: 2026-05-20
- Decision: Product-concept candidate and optimizer variants that are **not** in `_REGISTRY_ROWS` (`src/candidate_comparison.py`) remain **out of scope** for V1 factory and comparison until a future accepted spec adds a `candidate_id`, builder script, and DEC. Each listed concept id has an explicit status in [candidate_portfolios_spec.md](docs/specs/candidate_portfolios_spec.md) § Concept candidates not in registry: **declined** (use a different workflow), **deferred** (future builder/spec), or **covered_by_existing** (partial overlap with shipped ids). No silent registry expansion from [DIAGNOSTIC_PRODUCT_CONCEPT.md](docs/DIAGNOSTIC_PRODUCT_CONCEPT.md) alone.
- Context: Phase 14 governance gap G9 — concept docs name Max Sharpe, tactical tilt, custom constraints, drawdown-controlled, macro-resilient, and stress-test-optimized menu rows that do not exist as comparison registry entries, creating drift vs `_REGISTRY_ROWS`.
- Rationale: Prevents operators and agents from assuming missing builders are bugs; keeps the 18-row registry the implementation truth; tactical tilt stays post-policy (`view_after_optimization`), not a factory hypothesis; stress-robust menu overlap is disclosed via `robust_scenario` rather than a duplicate id.
- Alternatives considered: Add placeholder `unavailable` registry rows for every concept name (rejected — inflates menu without builders); ignore concept drift in docs only (rejected — G9); implement all concept optimizers in Session 11 (rejected — non-goals for Phase 14).
- Assumptions: New families require quant review, factory profile update, golden fixture refresh, and a superseding or companion DEC; registry length stays 18 until then.
- Consequences: G9 / `KI-2026-05-20-007` closed; methodology map P5 documented; Phase 14 Session 11 (`RM-981`) wave closure.
- Related documents: [candidate_portfolios_spec.md](docs/specs/candidate_portfolios_spec.md) (appendix table), [candidate_comparison_spec.md](docs/specs/candidate_comparison_spec.md), [candidate_factory_methodology_map.md](docs/audits/2026-05-20_candidate_factory_methodology_map.md), [view_after_optimization_spec.md](docs/specs/view_after_optimization_spec.md), [docs/exec_plans/2026-05-20_candidate_factory_post_audit_roadmap.md](docs/exec_plans/2026-05-20_candidate_factory_post_audit_roadmap.md) Session 11.
- Review trigger: Revisit when product requests a new comparison `candidate_id` with an accepted builder spec and implementation plan.

Decision ID: DEC-2026-05-20-002
Title: Defer crypto_shock and volatility_shock synthetic scenarios in run_stress

- Status: accepted
- Date: 2026-05-20
- Decision: Do **not** add `crypto_shock` or `volatility_shock` / `vix_shock` to `src/stress.py::SCENARIOS` or the mandatory `run_stress` suite until a follow-up implementation session is explicitly approved. Keep Portfolio X-Ray **volatility_spike** on **factor-only Option B** (`beta_vix` + `es_95`). Keep **crypto_shock** as a conditional Weakness Map row only (taxonomy / weights), not a `scenario_results` row.
- Context: Block 3 governance gap G8 — X-Ray surfaces vol and crypto risks but stress suite has eight synthetic scenarios on the six-shock engine; adding scenarios without a factor/crypto channel plan risks double counting or equity-proxy misstatement.
- Rationale: Session 08 default is spec-only governance; VIX factor exists in analytics but is excluded from synthetic shock mapping by design; crypto has no production `shock_crypto` channel. Deferral preserves suite stability, mandate boundary, and baseline comparability until product requests named PnL rows.
- Alternatives considered: Implement `volatility_shock` now (deferred — see proposal Option A); map crypto to `equity_shock` proxy (rejected); implement both in Session 08 without spec (rejected — violates governance non-goals).
- Assumptions: `liquidity_shock` / `equity_shock` remain acceptable partial risk-off proxies for vol in the eight-scenario suite; historical episodes (2020, 2022) cover realized vol stress paths.
- Consequences: `stress_testing_spec.md` §2.3 documents deferred ids; methodology map G8 closed as spec-only; implementation requires proposal §5 checklist, WEAKNESS_SCENARIO_MAP alignment, and Sessions 10–11 integration if later accepted.
- Related documents: [docs/proposals/2026-05-20_crypto_vol_stress_scenarios_proposal.md](docs/proposals/2026-05-20_crypto_vol_stress_scenarios_proposal.md), [stress_testing_spec.md](docs/specs/stress_testing_spec.md) §2.3, [portfolio_xray_diagnostics_spec.md](docs/specs/portfolio_xray_diagnostics_spec.md) §2.7, [docs/exec_plans/2026-05-20_stress_lab_methodology_governance_plan.md](docs/exec_plans/2026-05-20_stress_lab_methodology_governance_plan.md) Session 08.
- Review trigger: Revisit when product requires vol/crypto PnL in IPS, stress commentary, or hedge-gap mapping alongside other named scenarios, or when crypto factor data policy is approved.

Decision ID: DEC-2026-05-20-001
Title: Primary historical stress stays realized-only; proxy only in normalized library

- Status: accepted
- Date: 2026-05-20
- Decision: `run_stress` historical episodes use aligned portfolio **realized** monthly returns only (`return_method: realized_portfolio_monthly`, `proxy_used: false` on each row). Per-asset historical proxy waterfall remains in `scenario_library_normalized` via `historical_stress_fallback` and is disclosed in `stress_report.json.historical_methodology` and `stress_conclusions.data_quality_warnings`. Do not route primary historical stress through the proxy waterfall unless this decision is superseded.
- Context: Stress Lab methodology audit (G2): consumers could confuse primary `historical_results` with normalized-library proxy fills.
- Rationale: Mandate historical pass/fail and crisis replay must reflect actual portfolio path; proxies are a separate readiness layer for candidate/library analytics.
- Alternatives considered: Enable proxy in `run_stress` primary path (deferred — proposal P1); hide proxy entirely (rejected — misleads library readers).
- Assumptions: `scenario_library_normalized` continues to document waterfall steps; factor attribution on historical rows remains model-based overlay, not a return proxy.
- Consequences: `historical_methodology` block on stress reports; spec §9.3; tests in `test_stress_historical_fields.py`.
- Related documents: [stress_testing_spec.md](docs/specs/stress_testing_spec.md) §9, [scenario_library_spec.md](docs/specs/scenario_library_spec.md), [docs/exec_plans/2026-05-20_stress_lab_methodology_governance_plan.md](docs/exec_plans/2026-05-20_stress_lab_methodology_governance_plan.md) Session 02, [docs/audits/2026-05-20_stress_lab_methodology_map.md](docs/audits/2026-05-20_stress_lab_methodology_map.md).
- Review trigger: Revisit if product requires primary historical stress to use per-asset proxy fills for young ETFs or missing history.

Decision ID: DEC-2026-05-18-001
Title: Portfolio-first workflow and legacy policy engine boundary

- Status: accepted
- Date: 2026-05-18
- Decision: The main product workflow must start from `analysis_subject` diagnostics. Generated policy optimization must not be presented before `analysis_subject` is diagnosed and must not be a default candidate in the portfolio-first workflow. The old policy engine remains available as legacy, archived, or experimental infrastructure until a future canonical spec explicitly reactivates it.
- Context: The user identified that the project contract drifted toward a policy-first mental model: `run_optimization.py` generated policy weights first, then reports and comparisons treated that policy portfolio as the main starting point. This conflicts with the product vision that a user's current, model, or universe-baseline portfolio should be diagnosed first.
- Rationale: A portfolio review product must answer whether to keep, improve, rebalance, or rethink the portfolio the user started with. Showing optimized results before diagnosing that portfolio reverses the product logic and misleads agents and users.
- Alternatives considered: Keep policy as the default candidate; keep policy as the default starting portfolio but change wording; delete the old policy engine. These were rejected because they either preserve the source-of-truth conflict or discard potentially useful infrastructure.
- Assumptions: The transition remains file-first; UI work is not part of this decision; reintroducing policy as a candidate requires a future spec and explicit approval.
- Consequences: New specs, workflow orchestration, comparison, decision artifacts, reports, and docs must center on `analysis_subject`. `run_optimization.py` remains callable but is not part of the default portfolio-first path.
- Related documents: [Portfolio Review Workflow Specification](docs/specs/portfolio_review_workflow_spec.md), [Portfolio-First Transition Plan](docs/exec_plans/2026-05-18_portfolio_first_transition_plan.md), [docs/ROADMAP.md](docs/ROADMAP.md), [KNOWN_ISSUES.md](KNOWN_ISSUES.md), [PRODUCT.md](PRODUCT.md).
- Review trigger: Revisit only if a future accepted spec proposes reintroducing the policy engine as an optional candidate generator or production policy path.

Decision ID: DEC-2026-05-19-001
Title: Portfolio-first policy artifacts are compatibility-only

- Status: accepted
- Date: 2026-05-19
- Decision: When `analysis_subject` diagnostics are available, root `policy` artifacts remain readable for legacy compatibility but are not ranked or selected as normal portfolio-first candidate evidence. `current_vs_policy_status.json` may still be written, but it uses `workflow_profile: portfolio_first_review` and is hidden from the main decision-package summary story.
- Context: The post-portfolio-first audit found that policy rows, current-vs-policy status, and Health Score priority still made old policy optimizer artifacts look like the primary workflow in fresh portfolio-first outputs.
- Rationale: Keeping the artifacts avoids breaking legacy consumers, while gating and labeling them prevents users from treating generated policy output as the starting portfolio or default recommendation.
- Alternatives considered: Delete policy artifacts from comparison; leave them fully available with wording only. Deletion was too disruptive for compatibility, while wording-only cleanup would still let Selection and Health Score rank stale policy evidence.
- Assumptions: Reintroducing policy as an explicit portfolio-first candidate requires a future canonical spec.
- Consequences: Candidate Comparison gates `policy` as legacy-only when `analysis_subject` exists, Health Score priority starts with `analysis_subject`, and current-vs-policy status is compatibility metadata in portfolio-first runs.
- Related documents: [Portfolio Review Workflow Specification](docs/specs/portfolio_review_workflow_spec.md), [candidate comparison spec](docs/specs/candidate_comparison_spec.md), [current-vs-policy workflow spec](docs/specs/current_vs_policy_workflow_spec.md), [portfolio health score spec](docs/specs/portfolio_health_score_spec.md).
- Review trigger: Revisit if a future accepted spec adds an explicit opt-in policy-as-candidate mode for portfolio-first reviews.

Decision ID: DEC-2026-05-18-002
Title: Analysis subject is the decision baseline

- Status: accepted
- Date: 2026-05-18
- Decision: When `analysis_subject` diagnostics are materialized, candidate comparison and downstream decision artifacts use `analysis_subject` as the baseline. The legacy `current` baseline remains a fallback for current-vs-policy compatibility only.
- Context: Earlier Selection V1 behavior favored `policy` by default and evaluated No-Trade versus `current`. That was correct for the old current-vs-policy workflow but contradicted the portfolio-first transition once `analysis_subject` became the diagnosed starting portfolio.
- Rationale: Selection, No-Trade, Action, Monitoring, and Journal must answer whether to keep, improve, rebalance, or rethink the starting portfolio, not whether to move from current to generated policy.
- Alternatives considered: Keep policy as default even when `analysis_subject` exists; duplicate a separate subject-only decision artifact. These were rejected because they preserve old policy-first interpretation or split one decision workflow into parallel contracts.
- Assumptions: `current_vs_policy_status.json` remains compatibility-only; the policy engine is not deleted; report language cleanup continues in later transition sessions.
- Consequences: `candidate_comparison.json` includes `analysis_subject`; `selection_decision.json`, `action_plan.json`, monitoring snapshots, and `decision_journal.json` expose baseline fields and prefer `analysis_subject`.
- Related documents: [Portfolio Review Workflow Specification](docs/specs/portfolio_review_workflow_spec.md), [candidate comparison spec](docs/specs/candidate_comparison_spec.md), [selection engine spec](docs/specs/selection_engine_spec.md), [action engine spec](docs/specs/action_engine_spec.md), [monitoring spec](docs/specs/monitoring_spec.md), [decision journal spec](docs/specs/decision_journal_spec.md).
- Review trigger: Revisit if a future spec creates a multi-baseline comparison workflow or reintroduces policy as an explicit portfolio-first candidate.

Decision ID: DEC-2026-05-17-005
Title: Post-session next stage and optimizer-role boundary

- Status: accepted
- Date: 2026-05-17
- Decision: After Sessions 01-20, the next project stage is stabilization and integration of the new decision pipeline before major new analytics or UI. Main optimization remains the production policy path; robust MV and robust scenario optimization remain comparison/candidate paths unless a future accepted spec changes that boundary.
- Context: The post-session audit found that candidate comparison, robustness, health, selection, action, monitoring, and journal artifacts are implemented, while top-level docs, reporting surfaces, source text quality, and current-vs-policy workflow still need cleanup. It also reviewed Main optimizer inputs/objective/gates against robust optimizer paths and the product concept.
- Rationale: The project now has the V1 decision artifacts, but the user-facing and source-of-truth layers are not yet stable enough to safely build larger UI or advanced analytics on top. Keeping Main and robust optimizer roles explicit prevents silent changes to production policy behavior.
- Alternatives considered: Start UI work immediately; replace Main with robust optimization; add assumption sensitivity/Pareto/regret before syncing docs and reports. These were rejected as higher-risk sequencing because they would build on stale docs and incomplete user-facing surfaces.
- Assumptions: Sessions 01-20 remain the accepted V1 artifact baseline; generated outputs are not source of truth; any optimizer role change requires a new owning spec.
- Consequences: Near-term roadmap work should prioritize docs/status sync, decision-log integrity, report/PDF decision-package integration, mojibake cleanup, current-vs-policy workflow, and candidate factory orchestration before Sessions 21-22 or new analytics.
- Related documents: [post-session audit](docs/audits/2026-05-17_post_session_deep_system_audit.md), [docs/ROADMAP.md](docs/ROADMAP.md), [docs/specs/portfolio_construction_policy.md](docs/specs/portfolio_construction_policy.md), [docs/specs/robust_mv_spec.md](docs/specs/robust_mv_spec.md), [docs/specs/robust_scenario_optimization_spec.md](docs/specs/robust_scenario_optimization_spec.md).
- Review trigger: Revisit if robust optimization is proposed as the production policy optimizer, if a candidate factory becomes authoritative, or before implementing the first full product UI.

Decision ID: DEC-2026-05-17-002
Title: V1 candidate comparison contract (full registry, current row, Main output)

- Status: accepted
- Date: 2026-05-17
- Decision: The canonical comparison artifact is `candidate_comparison.json` under `output_dir_final` (default `Main portfolio/`). V1 lists the full candidate registry with `unavailable` when artifact folders are missing, and includes a `current` candidate when user-current portfolio artifacts exist (`analyze_current_weights` or `user_current_portfolio` tagging).
- Context: Legacy `portfolio_comparison.json` and `ew_rp_comparison.json` cover partial subsets with inconsistent schemas; audit AUD-010 requires one contract before scores and selection.
- Rationale: A single diagnostic-only table supports current vs policy vs benchmarks without implying a recommendation; Main placement keeps the comparison next to primary run outputs.
- Alternatives considered: Minimal four-candidate launch only; defer `current` to a later session; place the file in a root `comparison/` folder.
- Assumptions: Session 09 implements a read-only builder that does not recompute metrics; legacy comparison files remain until migration.
- Consequences: Robustness Scorecard, Health Score, and Selection Engine must consume `candidate_comparison.json` per [candidate_comparison_spec.md](docs/specs/candidate_comparison_spec.md).
- Related documents: [docs/specs/candidate_comparison_spec.md](docs/specs/candidate_comparison_spec.md), [OUTPUTS.md](OUTPUTS.md), [docs/ROADMAP.md](docs/ROADMAP.md).
- Review trigger: Revisit when comparison UI, cross-run history, or a dedicated comparison workspace is introduced.

Decision ID: DEC-2026-05-17-004
Title: Portfolio Health Score V1 scoring model

- Status: accepted
- Date: 2026-05-17
- Decision: The Portfolio Health Score uses ten reviewable components under profile `default_weights_reviewable`, within-run percentile normalization plus absolute mandate/liquidity checks, primary window 10y, optional `resilience_reference` (10%) from `robustness_scorecard.json` only, and weight concentration from a comparison `weight_concentration` block (not RC proxies). Output is diagnostic-only for all scored candidates; report surfaces prioritize `current` and `policy`.
- Context: Session 12 specifies holistic quality scoring after canonical comparison and robustness scorecard; product concept section 11 defines investor-facing health components distinct from resilience ranking.
- Rationale: Health answers balance, fit, and implementability; Robustness answers crisis resilience; ingesting robustness total avoids duplicating six robustness formulas while keeping a separate narrative.
- Alternatives considered: Health Score only for current/policy; full duplication of robustness stress/downside components; no cross-reference to robustness scorecard.
- Assumptions: Session 13 implements the health score module and comparison v1.2 `weight_concentration` together.
- Consequences: See [portfolio_health_score_spec.md](docs/specs/portfolio_health_score_spec.md).
- Related documents: [docs/specs/portfolio_health_score_spec.md](docs/specs/portfolio_health_score_spec.md), [docs/specs/robustness_scorecard_spec.md](docs/specs/robustness_scorecard_spec.md), [docs/specs/candidate_comparison_spec.md](docs/specs/candidate_comparison_spec.md), [docs/ROADMAP.md](docs/ROADMAP.md).
- Review trigger: Revisit after empirical validation of weights or when Selection Engine consumes health outputs.

Decision ID: DEC-2026-05-17-003
Title: Robustness Scorecard V1 scoring model

- Status: accepted
- Date: 2026-05-17
- Decision: The Robustness Scorecard uses relative within-run normalization for component sub-scores, product-concept weights under profile `default_weights_reviewable`, primary window 10y, RC-based diversification from a comparison `diversification` block (no vol/beta proxies), and absolute mandate checks only inside `mandate_fit`. Output is diagnostic-only until Selection Engine exists.
- Context: Session 10 specifies the scorecard after canonical `candidate_comparison.json`; the product concept defines six components and example weights.
- Rationale: Relative scoring answers "who is more resilient among these alternatives"; mandate limits stay explicit; RC concentration matches the project's RC_vol diagnostics.
- Alternatives considered: Absolute scoring against fixed thresholds for all components; temporary diversification proxies without RC in comparison.
- Assumptions: Session 11 implements the scorecard module and comparison v1.1 diversification fields together.
- Consequences: See [robustness_scorecard_spec.md](docs/specs/robustness_scorecard_spec.md); `src/robustness.py` remains optimizer weight stability only.
- Related documents: [docs/specs/robustness_scorecard_spec.md](docs/specs/robustness_scorecard_spec.md), [docs/specs/candidate_comparison_spec.md](docs/specs/candidate_comparison_spec.md), [docs/ROADMAP.md](docs/ROADMAP.md).
- Review trigger: Revisit after empirical validation of weights or when Selection Engine consumes score outputs.

Decision ID: DEC-2026-05-17-001
Title: Use docs/ROADMAP.md as the durable development roadmap

- Status: accepted
- Date: 2026-05-17
- Decision: The ordered product-development roadmap lives at `docs/ROADMAP.md`; it is a planning document and does not override canonical specs or current implementation contracts.
- Context: The 2026-05-17 audit found that the project had product concepts, implementation specs, and many analytical modules, but no single execution spine connecting concept layers to ordered development sessions.
- Rationale: `docs/ROADMAP.md` is clearer than `docs/product_backlog.md` for a durable cross-phase plan and matches the audit's first recommended filename.
- Alternatives considered: Use `docs/product_backlog.md`, which is also reasonable but narrower; keep only the ExecPlan, which would make the plan less discoverable from root documentation.
- Assumptions: Future major work continues to use checked-in ExecPlans when changes are large or risky; roadmap items remain non-binding until promoted into owning specs and code.
- Consequences: Future product modules should map to roadmap IDs, source-of-truth specs, artifacts, and verification before implementation. Current behavior remains governed by `SPEC.md` and detailed specs.
- Related documents: [docs/ROADMAP.md](docs/ROADMAP.md), [docs/exec_plans/2026-05-17_project_development_session_plan.md](docs/exec_plans/2026-05-17_project_development_session_plan.md), [docs/audits/2026-05-17_full_project_system_audit.md](docs/audits/2026-05-17_full_project_system_audit.md).
- Review trigger: Revisit if roadmap ownership moves, a separate backlog is introduced, or product planning becomes managed outside the repository.

Decision ID: DEC-2026-05-15-001
Title: Separate current weights from generated policy weights

- Status: accepted
- Date: 2026-05-15
- Decision: The Input and Assumptions Layer supports `analysis_mode=optimize_from_universe` for the default policy workflow and `analysis_mode=analyze_current_weights` for fixed current-portfolio diagnostics using `current_weights`.
- Context: The product concept allows existing-portfolio analysis with current weights, while the current policy rule says final production weights are generated by optimization.
- Rationale: Separating current diagnostic weights from generated policy weights lets users analyze existing portfolios without weakening the rule that policy weights come from the optimizer or approved post-optimization protocols.
- Alternatives considered: Continue using only `weights` for both cases, which keeps ambiguity; allow manual policy weights, which weakens production semantics.
- Assumptions: The first product layer remains CLI/file-driven and report-first; full UI, formal selection, and no-trade logic are still TBD.
- Consequences: `run_optimization.py` rejects `analyze_current_weights`; `run_report.py` can diagnose fixed current weights; artifacts expose an `input_assumptions` summary.
- Related documents: [docs/specs/input_assumptions_spec.md](docs/specs/input_assumptions_spec.md), [docs/exec_plans/2026-05-15_input_assumptions_layer_v1.md](docs/exec_plans/2026-05-15_input_assumptions_layer_v1.md), [docs/specs/portfolio_construction_policy.md](docs/specs/portfolio_construction_policy.md).
- Review trigger: Revisit when the project adds a UI input workflow, formal Selection Engine, or compare-current-to-policy workflow.

Decision ID: DEC-2026-05-15-002
Title: Make analysis_setup the input-layer runtime contract

- Status: accepted
- Date: 2026-05-15
- Decision: `analysis_setup` is the single resolved runtime contract for portfolio input, analysis portfolio, mandate, assumptions, and validation; `input_assumptions` is a report/export projection from it.
- Context: The product needs a clear analysis contract before diagnostics, stress testing, optimization, comparison, recommendation, or reporting, without adding UI or selection-engine scope.
- Rationale: A single resolved contract prevents `input_assumptions`, generated weights, current weights, and future UI inputs from becoming competing sources of truth.
- Alternatives considered: Keep only `input_assumptions` as the runtime summary, which blurs reporting metadata with business logic; immediately change universe-only report behavior, which would exceed the compatibility scope.
- Assumptions: Backward compatibility takes priority; target MVP conflicts are documented before behavior changes.
- Consequences: Run artifacts expose `analysis_setup`; `input_assumptions` is projected from it; Equal Weight Initial Portfolio is labeled as a baseline, not a recommendation.
- Related documents: [docs/specs/input_assumptions_spec.md](docs/specs/input_assumptions_spec.md), [OUTPUTS.md](OUTPUTS.md), [docs/specs/reporting_outputs_spec.md](docs/specs/reporting_outputs_spec.md).
- Review trigger: Revisit when SPEC authorizes taxonomy hard rejection in current repo mode or equal-weight universe-only diagnostics as executable report behavior.

Decision ID: DEC-2026-05-17-006
Title: Selection Engine V1 contract — composite score, policy default, No-Trade materiality

- Status: accepted
- Date: 2026-05-17
- Decision: Session 14 adopts [selection_engine_spec.md](docs/specs/selection_engine_spec.md) with neutral decision-support tone; favored target defaults to `policy` when mandate-clean; No-Trade compares `current` to favored target using reviewable health/robustness deltas, half-sum turnover, and optional drawdown improvement; Pareto/regret/assumption sensitivity remain out of V1; diagnostic scorecards stay non-binding inputs.
- Context: Comparison and diagnostic scores (Sessions 08–13) exist; the product needs a formal non-executing decision artifact before Action Engine and Decision Journal.
- Rationale: Separates evidence (comparison, health, robustness) from a single machine-readable decision status; No-Trade prevents implying trades when benefit is immaterial relative to turnover.
- Alternatives considered: Auto-select top health rank only (rejected — ignores policy role and robustness); merge Selection into Health Score (rejected — blurs diagnostic vs decision); include Pareto pruning in V1 (deferred — no owning spec).
- Assumptions: Session 15 will implement `selection_decision.json` without changing optimizer release or stress pass/fail.
- Consequences: `selection_decision_v1` is the target artifact; `src/selection_engine.py` and tests follow in Session 15; PDF/report surfaces reference decision rules when integrated.
- Related documents: [docs/specs/selection_engine_spec.md](docs/specs/selection_engine_spec.md), [docs/specs/candidate_comparison_spec.md](docs/specs/candidate_comparison_spec.md), [docs/specs/portfolio_health_score_spec.md](docs/specs/portfolio_health_score_spec.md), [docs/specs/robustness_scorecard_spec.md](docs/specs/robustness_scorecard_spec.md), [docs/ROADMAP.md](docs/ROADMAP.md) RM-300.
- Review trigger: Revisit when Pareto/dominance or regret modules are specified, or when transaction-cost-aware No-Trade is added in Action Engine.

Decision ID: DEC-2026-05-17-009
Title: Assumption Sensitivity V1 — selection-stability grid without optimizer re-run

- Status: accepted
- Date: 2026-05-17
- Decision: Adopt [assumption_sensitivity_spec.md](docs/specs/assumption_sensitivity_spec.md) with Tier A variants (composite weight stress, health/robust-only proxies, policy-default-off) and Tier B evidence variants (Sharpe rank by 3y/5y/10y, stress worst-loss rank). Stability is measured as `favored_stable_rate` on Tier A only; artifact is diagnostic-only and does not change `selection_decision.json`. Explicit V1 exclusions: optimizer re-run, expected-return shocks, covariance re-score, transaction-cost grids.
- Context: Post-audit Session 14 (RM-620 spec phase); product concept section 14 and audit PSA-012; Selection V1 defers sensitivity from binding logic.
- Rationale: Answers whether the favored profile is fragile to reviewable score-weight and policy-role assumptions using existing health/robustness totals; avoids expensive or formula-duplicating perturbations in V1.
- Alternatives considered: Full assumption grid with re-optimization (deferred — out of scope and high model risk); merge into model-risk artifact (rejected — different question); auto-downgrade selection when fragile (rejected — violates diagnostic boundary).
- Assumptions: Session 15 implements the assumption sensitivity builder, wires after trade-off in `write_candidate_comparison_outputs`, and extends decision-package reporting.
- Consequences: `assumption_sensitivity_v1` contract; journal/report may cite stability; Pareto/regret remain separate sessions.
- Related documents: [docs/specs/assumption_sensitivity_spec.md](docs/specs/assumption_sensitivity_spec.md), [docs/specs/selection_engine_spec.md](docs/specs/selection_engine_spec.md), [OUTPUTS.md](OUTPUTS.md), [docs/ROADMAP.md](docs/ROADMAP.md) RM-620.
- Review trigger: Revisit when Health/Robustness can be re-scored on alternate windows without full pipeline re-run, or when No-Trade threshold stress is added.

Decision ID: DEC-2026-05-17-010
Title: Pareto / Dominance Check V1 — strict metric-only dominance diagnostic

- Status: accepted
- Date: 2026-05-17
- Decision: Adopt [pareto_dominance_spec.md](docs/specs/pareto_dominance_spec.md) with strict Pareto dominance on primary-window `cagr`, `vol_annual`, `max_drawdown`, and `stress_worst_loss`, optional `es_95` and `turnover_vs_current_half_sum_pct` when present. Artifact is diagnostic-only, does not change `selection_decision.json`, and runs after assumption sensitivity in the comparison pipeline.
- Context: Post-audit Session 16 (RM-621 spec phase); product concept section 15 and audit PSA-012; Selection V1 defers dominance from binding logic.
- Rationale: Surfaces clearly weaker candidates using existing comparison exports without duplicating metric formulas or auto-pruning Selection output.
- Alternatives considered: Mandate-aware dominance (rejected for V1 — blurs binding gates with metric evidence); auto-remove dominated candidates from Selection (rejected — violates diagnostic boundary); Sharpe-only dominance (rejected — overlaps Assumption Sensitivity Tier B).
- Assumptions: Session 17 implements the Pareto/Dominance builder, wires into `write_candidate_comparison_outputs`, and extends decision-package reporting.
- Consequences: `pareto_dominance_v1` contract; journal/report may cite efficient set and `favored_is_dominated`; Regret Analysis spec in Session 18, implementation Session 19.
- Related documents: [docs/specs/pareto_dominance_spec.md](docs/specs/pareto_dominance_spec.md), [docs/specs/candidate_comparison_spec.md](docs/specs/candidate_comparison_spec.md), [OUTPUTS.md](OUTPUTS.md), [docs/ROADMAP.md](docs/ROADMAP.md) RM-621.
- Review trigger: Revisit when multi-window Pareto surfaces or mandate-aware dominance are product-required.

Decision ID: DEC-2026-05-17-011
Title: Regret Analysis V1 — stress-scenario opportunity-loss diagnostic

- Status: accepted
- Date: 2026-05-17
- Decision: Adopt [regret_analysis_spec.md](docs/specs/regret_analysis_spec.md) with stress-scenario regret `best_pnl - pnl_R` over the evaluable opportunity set, reference profiles `favored`, `current`, and `benchmark`, headline `mean_regret` / `worst_regret`, optional macro regime slice when comparison exports regime PnL, and informational primary-window CAGR regret (Tier B). Artifact is diagnostic-only, does not change `selection_decision.json`, and runs after Pareto dominance in the comparison pipeline.
- Context: Post-audit Session 18 (RM-622 spec phase); product concept section 16 and audit PSA-012; comparison-ranking agent regret guidance.
- Rationale: Surfaces opportunity cost of committing to a reference profile under named stress scenarios using existing comparison exports without duplicating stress engine runs or auto-overriding Selection.
- Alternatives considered: Regret vs Pareto-efficient set only (deferred to V2); auto-switch selection on high regret (rejected — violates diagnostic boundary); full macro regime regret without projected comparison fields (deferred — optional slice with `not_available` when data missing).
- Assumptions: Session 19 implements the Regret Analysis builder, wires into `write_candidate_comparison_outputs`, and extends decision-package reporting.
- Consequences: `regret_analysis_v1` contract; journal/report may cite `worst_regret` for favored reference; implementation remains Session 19.
- Related documents: [docs/specs/regret_analysis_spec.md](docs/specs/regret_analysis_spec.md), [docs/specs/candidate_comparison_spec.md](docs/specs/candidate_comparison_spec.md), [OUTPUTS.md](OUTPUTS.md), [docs/ROADMAP.md](docs/ROADMAP.md) RM-622.
- Review trigger: Revisit when regret-vs-Pareto-set or multi-window regret surfaces are product-required.

Decision ID: DEC-2026-05-17-008
Title: Trade-off Explanation and Model Risk Diagnostics V1 — separate diagnostic artifacts

- Status: accepted
- Date: 2026-05-17
- Decision: Adopt two file-first diagnostic artifacts under `output_dir_final`: `tradeoff_explanation_v1` (baseline `current` → favored target from selection, metric/stress deltas without new formulas, weight-based turnover at write time) and `model_risk_diagnostics_v1` (deduplicated warning catalog from comparison, scores, stress, and run metadata). Pipeline placement is after `selection_decision.json` and before `action_plan.json`. Layer is non-binding and does not change selection, mandate, or stress pass/fail.
- Context: Post-audit Session 12 (RM-616 spec phase); audit PSA-012 and product concept sections 17–18 flagged partial coverage via selection bullets and scattered warnings only.
- Rationale: Makes “price of improvement” and model self-criticism explicit for decision package and journal without conflating them with Health Score or Selection outcomes.
- Alternatives considered: Single combined JSON (rejected — reporting and tests are clearer with two files); compute trade-off after action for action turnover (deferred — V1 uses weight deltas at trade-off write time); auto-veto selection on high model risk (rejected — violates diagnostic boundary).
- Assumptions: Session 13 implements `src/tradeoff_and_model_risk.py`, wires into `write_candidate_comparison_outputs`, and extends decision-package reporting sections.
- Consequences: See [docs/specs/tradeoff_and_model_risk_spec.md](docs/specs/tradeoff_and_model_risk_spec.md); journal and reporting prefer trade-off artifact over selection `tradeoff_bullets` when present.
- Related documents: [docs/specs/tradeoff_and_model_risk_spec.md](docs/specs/tradeoff_and_model_risk_spec.md), [docs/specs/selection_engine_spec.md](docs/specs/selection_engine_spec.md), [docs/specs/decision_package_reporting_spec.md](docs/specs/decision_package_reporting_spec.md), [OUTPUTS.md](OUTPUTS.md), [docs/ROADMAP.md](docs/ROADMAP.md) RM-616.
- Review trigger: Revisit if trade-off should run after action for turnover parity, or if concentration thresholds should become mandate-binding.

Decision ID: DEC-2026-05-26-005
Title: Block 2.5 Risk Budget View is Core MVP; product block excludes stress PnL

- Status: accepted
- Date: 2026-05-26
- Decision: Product **Block 2.5 = Risk Budget View** (`block_2_5_risk_budget_view` on
  `portfolio_xray.json`). Core MVP product diagnosis extends to Blocks 2.1–2.6. Portfolio Archetype
  remains legacy `sections.portfolio_archetype` only (§2.7; forbidden: `block_2_5_portfolio_archetype`).
  The product block compares capital weights to RC_vol and taxonomy risk-budget buckets; it must not
  include stress scenario PnL fields. Legacy `sections.risk_budget_view` stays unchanged and may still
  expose stress loss contribution for formatters.
- Context: [Block 2.5 Risk Budget View MVP](docs/exec_plans/2026-05-26_block_2_5_risk_budget_view_plan.md)
  Session 01; supersedes doc numbering that assigned product 2.5 to archetype (2026-05-26 archetype demotion pass).
- Rationale: Operators need a stable product surface for “who drives portfolio risk?” separate from
  capital allocation (2.1) and hidden-risk heuristics (2.4); Stress Test Lab owns scenario PnL.
- Alternatives considered: Keep risk budget as legacy-only §2.6 (rejected — user-approved Core MVP 2.5);
  include stress PnL on product block (rejected — Stress Lab boundary); promote archetype as Block 2.5
  (rejected — postponed product module).
- Assumptions: Implementation lands Sessions 02–05; RC resolution stays in `build_portfolio_xray_v2`
  via `resolve_rc_asset_for_xray`; Block 2.5 module receives resolved rows only.
- Consequences: [portfolio_xray_diagnostics_spec.md](docs/specs/portfolio_xray_diagnostics_spec.md) §2.5.1;
  planned `src/block_2_5_risk_budget_view.py`; [OUTPUTS.md](OUTPUTS.md) Block 2 row; [SPEC.md](SPEC.md) status matrix.
- Related documents: [portfolio_xray_layer_spec.md](docs/specs/portfolio_xray_layer_spec.md) §2.5,
  [metrics_specification.md](docs/specs/metrics_specification.md) (RC_vol).
- Review trigger: Revisit if UI requires stress PnL on the product block or if legacy `sections.risk_budget_view` can be retired.

Decision ID: DEC-2026-05-26-006
Title: Block 2.6 Portfolio Weakness Map is Core MVP; product block is pre-stress only

- Status: accepted
- Date: 2026-05-26
- Decision: Promote Portfolio Weakness Map as Core MVP **Block 2.6** (`block_2_6_portfolio_weakness_map` on `portfolio_xray.json`). The product block is a pre-stress hypothesis map: it aggregates signals from Blocks 2.1–2.5 into a 0–100 vulnerability score per risk type plus plain-English explanation and `next_tests` suggestions. It must **not** read `stress_report.json`, scenario PnL, pass/fail, or loss attribution. Legacy `sections.weakness_map` remains for backward compatibility and may remain stress-coupled.
- Context: A legacy Weakness Map section exists under `sections.weakness_map`, but it reads stress artifacts directly (scenario PnL and attribution) and exposes qualitative severity bands without a stable 0–100 scoring contract and explainable weights. Core MVP needs a product-facing “what to test next” surface that stays clearly separated from Stress Test Lab outcomes.
- Rationale: Keeps Portfolio X-Ray diagnosis-first and lightweight, avoids duplicating Stress Lab logic, and preserves an interpretable handoff: X-Ray suggests what to test; Stress Lab computes losses and evidence quality.
- Alternatives considered: Keep weakness map as legacy-only (rejected — requested product surface); compute scenario losses inside X-Ray (rejected — violates Stress Lab ownership); replace legacy section entirely (rejected — breaks compatibility and formatters).
- Assumptions: Block 2.6 can be implemented as a read-only adapter over Blocks 2.1–2.5 with explicit `heuristic_v1` rule weights and evidence rows; Stress Lab continues to own all loss numbers and pass/fail status.
- Consequences: `portfolio_xray_diagnostics_spec.md` adds §2.6.1 contract; `portfolio_xray_layer_spec.md`, `SPEC.md`, `OUTPUTS.md`, and `GLOSSARY.md` align Core MVP as Blocks 2.1–2.6; Archetype remains legacy-only (§2.7).
- Related documents: [Block 2.6 Weakness Map ExecPlan](docs/exec_plans/2026-05-26_block_2_6_portfolio_weakness_map_plan.md), [portfolio_xray_diagnostics_spec.md](docs/specs/portfolio_xray_diagnostics_spec.md) §2.6.1, [stress_testing_spec.md](docs/specs/stress_testing_spec.md) (Stress Lab ownership).
- Review trigger: Revisit if the product requires scenario loss numbers on the X-Ray weakness surface or if `sections.weakness_map` can be retired after a formatter migration.

Decision ID: DEC-2026-05-26-004
Title: Block 2.3 Factor Exposure is a stress_report adapter, not a factor engine

- Status: accepted
- Date: 2026-05-26
- Decision: Expose Block 2.3 as top-level `block_2_3_factor_exposure` on `portfolio_xray.json`
  (portfolio-first: `analysis_subject/portfolio_xray.json`). Block 2.3 reads existing
  `stress_report` factor diagnostics only and must not trigger OLS/HAC regressions, Kalman beta
  calculations, factor variance decomposition, data loading, candidate generation, or Stress Lab
  shocks. Missing fields produce `partial` / `unavailable` plus warnings; upstream
  `stress_report` generation / `src/stress_factors.py` owns the fix.
- Context: [Block 2.3 Factor Exposure MVP](docs/exec_plans/2026-05-26_block_2_3_factor_exposure_plan.md);
  follows Block 2.1 (`DEC-2026-05-26-002`) and Block 2.2 (`DEC-2026-05-26-003`).
- Rationale: Portfolio X-Ray is diagnosis-first and should expose factor sensitivity in product
  language without creating a second independent factor calculation engine or mixing sensitivity
  diagnosis with Stress Lab shock outcomes.
- Alternatives considered: Recompute missing factor fields inside X-Ray (rejected — duplicate
  methodology and hidden fallback); embed stress-shock interpretation inside Block 2.3 (rejected —
  belongs to Stress Lab); standalone `factor_exposure.json` bundle artifact (rejected — Block 2
  product surface stays inside `portfolio_xray.json`).
- Assumptions: Existing `stress_report` fields remain the canonical factor diagnostics source:
  `factor_betas_3y`, `factor_betas_5y`, `factor_betas_10y`, `factor_regression_3y`,
  `factor_regression_5y`, `factor_regression_10y`, `factor_betas_kalman` (including
  `uncertainty_by_beta`), `factor_variance_decomposition`, and `factor_diagnostics_meta`.
  Core MVP product fields (`factor_signal_confidence`, `factor_kalman_uncertainty`,
  `factor_beta_stability`, `factor_exposure_summary`) are adapter outputs only; full regression
  statistics stay in `stress_report.json`.
- Consequences: [portfolio_xray_diagnostics_spec.md](docs/specs/portfolio_xray_diagnostics_spec.md)
  §2.3.1; implementation `src/block_2_3_factor_exposure.py`; tests
  `tests/test_block_2_3_factor_exposure.py`, `tests/test_block_2_3_pipeline_integration.py`, and
  `tests/test_portfolio_xray_contract.py` (golden regenerated via `tests/portfolio_xray_golden_inputs.py`).
- Related documents: [factor_diagnostics_spec.md](docs/specs/factor_diagnostics_spec.md),
  [OUTPUTS.md](OUTPUTS.md) Block 2 row, [portfolio_xray_layer_spec.md](docs/specs/portfolio_xray_layer_spec.md) §2.3.
- Review trigger: Revisit only if the canonical stress-report factor diagnostics move to a new
  upstream artifact or if a future spec intentionally retires legacy `sections.factor_exposure`.

Decision ID: DEC-2026-05-26-003
Title: Block 2.2 Portfolio Metrics product contract on portfolio_xray.json

- Status: accepted
- Date: 2026-05-26
- Decision: Expose Block 2.2 as top-level `block_2_2_portfolio_metrics` on `portfolio_xray.json`
  (portfolio-first: `analysis_subject/portfolio_xray.json`). Keep legacy `sections.risk_diagnostics`
  unchanged. Primary metrics horizon is 10Y (120M) when `snapshot_10y.json` metrics exist, else best
  available snapshot. Map internal `metric_quality` to `data_quality_warnings` only (never expose raw
  `metric_quality` on the product block). Rolling core_view uses `series_ref` to existing
  `results_csv/` files; full correlation matrix stays CSV-only via `full_matrix_ref`.
- Context: [Block 2.2 Portfolio Metrics / Risk Diagnostics MVP](docs/exec_plans/2026-05-26_block_2_2_portfolio_metrics_plan.md)
  Session 02; follows Block 2.1 (`DEC-2026-05-26-002`) and frozen Input Layer (`DEC-2026-05-26-001`).
- Rationale: Operators already read `portfolio_xray.json` for X-Ray; a stable product JSON avoids
  parsing internal `items[]`; aligns with diagnosis-first flow and Block 2.1 pattern.
- Alternatives considered: Embed metrics only in `sections.risk_diagnostics` (rejected — unstable for
  UI); standalone `portfolio_metrics.json` in six-file bundle (rejected); expose `metric_quality` to
  UI (rejected — internal diagnostics only).
- Assumptions: Builder ships Session 03+; pre-implementation on-disk runs lack Block 2.2 until
  re-materialized; `downside_deviation` and top-3 correlation pairs land with the builder (Session 03).
- Consequences: [portfolio_xray_diagnostics_spec.md](docs/specs/portfolio_xray_diagnostics_spec.md)
  §2.2.1; planned `src/block_2_2_portfolio_metrics.py`, `tests/test_block_2_2_portfolio_metrics.py`;
  acceptance audit `docs/audits/2026-05-26_block_2_2_portfolio_metrics_acceptance_audit.md` (Session 08).
- Related documents: [OUTPUTS.md](OUTPUTS.md) Block 2 row, [portfolio_xray_layer_spec.md](docs/specs/portfolio_xray_layer_spec.md) §2.2.
- Review trigger: Revisit if UI requires embedded full correlation matrix or retires legacy section.

Decision ID: DEC-2026-05-26-002
Title: Block 2.1 Asset Allocation product contract on portfolio_xray.json

- Status: accepted
- Date: 2026-05-26
- Decision: Expose Block 2.1 as top-level `block_2_1_asset_allocation` on `portfolio_xray.json`
  (portfolio-first: `analysis_subject/portfolio_xray.json`). Keep legacy `sections.asset_allocation`
  items unchanged. Capital-concentration thresholds live in `ALLOCATION_CONCENTRATION_THRESHOLDS`
  (separate from `XRAY_THRESHOLDS`). Real cash uses synthetic taxonomy, never `cash_proxy_ticker`.
- Context: [Block 2.1 Asset Allocation MVP](docs/exec_plans/2026-05-26_block_2_1_asset_allocation_plan.md)
  Session 02; follows frozen Input Layer (`DEC-2026-05-26-001`).
- Rationale: Operator guide already reads `portfolio_xray.json` for Block 2; a stable product JSON
  avoids parsing internal `items[]`; six-file bundle stays unchanged.
- Alternatives considered: Standalone `asset_allocation.json` (rejected — extra manifest surface);
  replace `sections.asset_allocation` only (rejected — breaks golden contract tests and formatters).
- Assumptions: *(superseded 2026-05-26 Session 08)* — builder shipped; portfolio-first materialize
  paths populate the key; pre-2026-05-26 on-disk runs may lack Block 2.1 until re-materialized.
- Consequences: [portfolio_xray_diagnostics_spec.md](docs/specs/portfolio_xray_diagnostics_spec.md)
  §2.1.1–§2.1.2; drift tests `tests/test_block_2_1_threshold_registry.py`,
  `tests/test_block_2_1_asset_allocation.py`, `tests/test_block_2_1_pipeline_integration.py`;
  live E2E gates in `src/live_core_e2e.py` / `src/live_full_e2e.py`. Closure:
  [Block 2.1 acceptance audit](docs/audits/2026-05-26_block_2_1_asset_allocation_acceptance_audit.md),
  ExecPlan Sessions 01–08 **Completed**.
- Related documents: [OUTPUTS.md](OUTPUTS.md) Block 2 row, [portfolio_xray_layer_spec.md](docs/specs/portfolio_xray_layer_spec.md) §2.1.
- Review trigger: Revisit if UI requires a separate bundle file or if legacy section can be retired.

Decision ID: DEC-2026-05-26-001
Title: Input Layer MVP contract frozen (Core MVP three-field surface)

- Status: accepted
- Date: 2026-05-26
- Decision: Freeze the Input Layer MVP contract after ExecPlan Sessions 01–10. Core MVP user input
  remains tickers + weights/`current_weights` + `investor_currency`; real cash is distinct from
  `cash_proxy_ticker`; `input_surface` / `field_tiers` export is mandatory on diagnosis materialize.
  Do not reopen input redesign unless a regression bug is filed.
- Context: [Input Layer MVP Migration](docs/exec_plans/2026-05-26_input_layer_mvp_migration.md) closed;
  live `run_portfolio_review.py --candidates equal_weight` + validator PASS (2026-05-26).
- Rationale: Prevents endless first-screen churn; shifts active product work to Blocks 2–5 and
  product-bundle layers already wired behind portfolio-first review.
- Alternatives considered: Continue input UX iteration in parallel with X-Ray (rejected — splits
  focus); delete legacy config keys now (rejected — optimizer/research still need them under
  `field_tiers.legacy_advanced`).
- Assumptions: Bug fixes and spec clarifications remain allowed; EUR fixture parity is a separate
  scoped task if needed.
- Consequences: Canonical behavior in [input_assumptions_spec.md](docs/specs/input_assumptions_spec.md)
  § Contract freeze; regression gate `tests/test_input_layer_mvp_regression.py`.
- Related documents: [acceptance audit](docs/audits/2026-05-26_input_layer_mvp_acceptance_audit.md),
  [OUTPUTS.md](OUTPUTS.md) Block 1, [product_flow_operator_guide.md](docs/product_flow_operator_guide.md).
- Review trigger: Reopen only on failed Block 1 acceptance, broken real-cash handling, or explicit
  new ExecPlan for non-USD Core MVP parity.

Decision ID: DEC-2026-05-17-007
Title: Candidate Portfolio Factory V1 — orchestrate before compare

- Status: accepted
- Date: 2026-05-17
- Decision: Adopt a file-first Candidate Portfolio Factory that runs existing per-candidate `run_*.py` builders in defined profiles, writes `candidate_factory_run_v1` under `output_dir_final`, uses continue-on-error and skip-existing-by-default, and hands off to `run_compare_variants.py`. Policy (`run_optimization.py` + Main report) and optional current materialization stay outside factory profiles. Main remains the production policy path; robust MV/scenario stay candidate inputs only.
- Context: Post-audit Session 10 (PSA-008): comparison quality depended on which builders were run manually; the product concept expects a controlled comparison arena.
- Rationale: Makes the intended candidate set auditable without duplicating optimizer formulas or changing comparison/selection contracts.
- Alternatives considered: Require manual script runs only (rejected — opaque and error-prone); embed all builders in one mega-optimizer (rejected — violates Main vs candidate boundary); auto-run policy inside factory (rejected — blurs production release path).
- Assumptions: Registry stays aligned with `_REGISTRY_ROWS` in [src/candidate_comparison.py](src/candidate_comparison.py).
- Consequences: Implemented `run_candidate_factory.py` and [src/candidate_factory.py](src/candidate_factory.py); RM-615 done; factory run summary under `output_dir_final`.
- Related documents: [docs/specs/candidate_factory_spec.md](docs/specs/candidate_factory_spec.md), [docs/specs/candidate_portfolios_spec.md](docs/specs/candidate_portfolios_spec.md), [docs/specs/candidate_comparison_spec.md](docs/specs/candidate_comparison_spec.md), [docs/ROADMAP.md](docs/ROADMAP.md) RM-615.
- Review trigger: Revisit if factory should parallelize builders, change default profile, or include policy/current in automated batches.
