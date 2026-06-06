# Full Demo MVP Readiness Gate - Session 10

Date: 2026-06-06

Related plan: [Full Demo MVP Readiness Audit and Hardening](../exec_plans/2026-06-05_full_demo_mvp_readiness_audit_and_hardening_plan.md)

## Final status

**DEMO_READY_WITH_LIMITATIONS**.

Do **not** mark the project `FULL_DEMO_MVP_READY` yet. The product path is truthful and operator-documented, focused regression tests pass, legacy and reference-benchmark boundaries are labelled, and the three demo fixtures have understandable honest outcomes. However, the hard full-ready gate is not met because the balanced and equity-heavy demo outputs still cannot explain grounded `what_improved` / `what_worsened` trade-offs when Block 8 candidate metrics are unavailable, and the defensive/rates-sensitive fixture remains a Builder-blocked case rather than a full candidate-comparison-verdict story.

This is not `NOT_READY_BLOCKED` because the demo can still be run and explained as a limited Core MVP: diagnosis, one tested reference hypothesis when allowed, evidence-insufficient safety behavior, and Builder blocking are all visible without treating a candidate as a recommendation.

## Gate checklist

| Gate | Result | Evidence |
| --- | --- | --- |
| Focused tests pass or blockers are classified | Pass | Block 6, Block 7, Block 8, Block 9, vertical flow / AI, freshness / runtime-label checks passed in Session 10. |
| Docs validation passes | Pass | `scripts/verify_docs.py` passed after this audit and plan update. |
| Three demo portfolios complete or produce honest blocked / evidence-insufficient outputs | Qualified pass | Existing demo outputs under `output/demo_portfolios/*/final/` show two evidence-insufficient flows and one Builder-blocked flow. Fresh full live reruns were not forced because the FRED/factor cache gate is not demo-safe. |
| Required output chain exists for successful vertical flows | Qualified pass | Balanced and equity-heavy have `candidate_generation.json`, `current_vs_candidate.json`, `decision_verdict.json`, and `ai_commentary_context.json`; defensive/rates-sensitive correctly lacks post-candidate root artifacts because Builder blocked generation. |
| Each portfolio has a human-readable summary | Pass with limitations | This audit records the three summaries below; `docs/demo/full_demo_mvp.md` explains how to read the same result without oral developer narration. |
| Output freshness / stale-artifact behavior verified | Pass by regression | `tests/test_no_stale_candidate_generation.py`, `tests/test_no_stale_verdict_in_ai_context.py`, `tests/test_product_bundle_paths.py`, and adjacent runtime workflow tests passed. Existing old demo outputs do not all contain newer `product_run` fields, so treat them as historical evidence, not fresh run proof. |
| FRED/factor behavior documented and demo-safe | Limited | `warm_factor_cache.py --check-only --start 2007-01-01 --end 2026-06-05` failed fast in about 3.25s with named missing / insufficient cache coverage. This is safe because it is explicit and documented, but it blocks claiming fresh full live demo safety. |
| Runtime commands are clear | Pass | Runtime-label and workflow tests passed; Session 09 guide documents canonical vertical commands. |
| Legacy paths are labelled | Pass | `tests/test_legacy_runner_wrappers.py` and `tests/test_runtime_entrypoint_labels.py` passed. |
| AI Commentary grounding is demo-usable | Qualified pass | Focused AI tests passed. Existing generated demo `ai_commentary_context.json` files may predate the Session 07 client-explanation fields; code-level readiness is verified, but old generated outputs should not be presented as fresh client-ready artifacts. |
| No forced rebalance when evidence is insufficient | Pass | Decision Verdict tests passed; balanced/equity-heavy verdicts remain `evidence_insufficient`. |
| No reference benchmark treated as recommendation | Pass | Candidate generation no-recommendation tests and reference-benchmark vertical tests passed. |
| No candidate zoo in default product path | Pass | The documented canonical path is one selected method via `scripts/run_blocks_5_to_9_vertical_flow.py --method equal_weight`. |

## Focused verification evidence

Commands were run from the repository root `D:\Рабочий стол\КУРСОР ТУЛА ДИАГНОСТИКА` with `\.venv\Scripts\python.exe`.

- Block 6 Builder setup tests: **45 passed** in 4.46s.
- Candidate Generation tests: **18 passed** in 0.46s.
- Block 8 Current vs Candidate tests: **12 passed** in 2.97s.
- Block 9 Decision Verdict tests: **16 passed** in 0.76s.
- Blocks 5-9 vertical flow and AI Commentary tests: **16 passed** in 7.96s.
- Stale-artifact / runtime-label / workflow checks: **61 passed** in 11.39s.
- Factor cache check-only gate: failed honestly with `EXIT_CODE=1`, elapsed about 3.247s, because required full-range FRED-backed factor cache is missing or too short for `2007-01-01..2026-06-05`.
- Documentation verification after writing this audit and updating the ExecPlan/register: **docs verification: OK**.

## Demo portfolio summaries

### Balanced diversified

- Output folder: `output/demo_portfolios/balanced/final/`.
- Diagnosis: `mixed_evidence_no_action`.
- Builder: `status: ok`, `can_generate_candidate: true`.
- Candidate/comparison/verdict chain: root `candidate_generation.json`, `current_vs_candidate.json`, `decision_verdict.json`, and `ai_commentary_context.json` exist.
- Trade-off evidence: `what_improved` and `what_worsened` are empty in the inspected output.
- Verdict: `evidence_insufficient`; action text says to review missing or degraded evidence before acting.
- Readiness interpretation: safe limited demo; not a full trade-off success story.

### Equity-heavy / concentrated

- Output folder: `output/demo_portfolios/equity_heavy/final/`.
- Diagnosis: `mixed_evidence_no_action`.
- Builder: `status: ok`, `can_generate_candidate: true`.
- Candidate/comparison/verdict chain: root `candidate_generation.json`, `current_vs_candidate.json`, `decision_verdict.json`, and `ai_commentary_context.json` exist.
- Trade-off evidence: `what_improved` and `what_worsened` are empty in the inspected output.
- Verdict: `evidence_insufficient`; action text says to review missing or degraded evidence before acting.
- Readiness interpretation: safe limited demo; not a full trade-off success story.

### Defensive / rates-sensitive

- Output folder: `output/demo_portfolios/defensive_rates_sensitive/final/`.
- Diagnosis: `weak_crisis_resilience`.
- Builder: `status: blocked`, `reason: data_quality_blocker`, `can_generate_candidate: false`.
- Candidate/comparison/verdict chain: root post-candidate artifacts are absent, which is correct for a Builder-blocked path.
- Trade-off evidence: not applicable because no candidate was generated.
- Verdict: no Block 9 verdict exists because the flow stops before candidate generation.
- Readiness interpretation: safe blocked-case demo; not a full comparison/verdict demo.

## Final decision

Use `DEMO_READY_WITH_LIMITATIONS` for the current repository state.

The Core MVP can be demonstrated as an honest diagnosis-first workflow that refuses to recommend action when evidence is missing, but `FULL_DEMO_MVP_READY` remains blocked until at least one representative successful candidate comparison can show grounded improvements and deteriorations, and until the factor/FRED data path is either reliably cached for the demo range or the live demo is explicitly scoped away from that dependency.
