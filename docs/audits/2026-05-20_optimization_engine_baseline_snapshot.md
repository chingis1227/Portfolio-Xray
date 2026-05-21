# Optimization Engine Baseline Snapshot (Block 5)

Date: 2026-05-20

Status: **Historical** (Phase 15 closed 2026-05-21, Sessions 00–12). This snapshot records the Block 5
governance baseline and closure evidence. It does not override `SPEC.md`, detailed specs, current code
behavior, formulas, constraints, or generated artifact contracts.

Related audit: [Optimization Engine Methodology Map](2026-05-20_optimization_engine_methodology_map.md).
Related plan: [Optimization Engine Post-Audit Roadmap](../exec_plans/2026-05-20_optimization_engine_post_audit_roadmap.md).

## Baseline Summary

The Optimization Engine currently consists of separate paths rather than one unified auditable
layer:

- legacy policy optimization through `run_optimization.py` and `src/optimization.py`;
- candidate optimizer families through `src/portfolio_variants.py` and per-candidate wrappers;
- Robust Mean-Variance through `src/robust_mv.py` and `src/robust_mv_calibration.py`;
- scenario-aware robust optimization through `src/robust_scenario_optimization.py`;
- downstream factory/comparison readiness through `src/candidate_factory.py` and
  `src/candidate_comparison.py`.

Session 00 does not refresh generated artifacts and does not change optimizer behavior. Generated
outputs under `Main portfolio/`, candidate portfolio folders, `results_csv/`, and
`portfolio_weights.yml` remain evidence only unless a future session explicitly targets them.

## Baseline governance gaps (pre–Phase 15)

The methodology map identified these weak points at audit time (see **Phase 15 governance closure**
below for post-wave status):

- no single canonical Optimization Engine layer spec → **closed** Session 01;
- legacy policy disclosure weaker than candidate metadata → **closed** Session 03;
- comparison artifacts missing optimizer methodology → **closed** Session 05;
- fallback/approximate paths resembling clean success → **closed** Session 06;
- incomplete config/universe/estimator fingerprint → **closed** Session 08;
- robust scenario solver status → **closed** Session 07;
- target-only objectives (Max Sharpe, drawdown, macro, etc.) → **closed** Session 02 (`DEC-2026-05-21-001`).

## Artifact Checklist

The following artifacts are representative evidence to inspect during later sessions. Session 00
does not require regenerating or fingerprinting them.

| Artifact | Purpose | Session that should update/check |
| --- | --- | --- |
| `Main portfolio/run_result.json` | Legacy policy status, mandate gate, optimization result metadata | Session 03 |
| `portfolio_weights.yml` | Legacy generated policy weights | Session 03 when policy output changes |
| `minimum variance portfolio/baseline_weights_metadata.json` | MinVar objective/solver/covariance/constraints metadata | Session 04 |
| `maximum diversification portfolio/baseline_weights_metadata.json` | MaxDiv objective/solver/disclosure metadata | Session 04 |
| `minimum cvar constrained portfolio/baseline_weights_metadata.json` | CVaR LP objective/scenario/confidence metadata | Session 04 |
| `robust mean variance constrained portfolio/baseline_weights_metadata.json` | Robust MV lambda, mu shrinkage, covariance metadata | Session 04 |
| `Main portfolio/robust_optimization_v1_summary.json` | Scenario robust objective and scenario diagnostics | Session 07 |
| `Main portfolio/candidate_factory_run.json` | Builder/factory status propagation | Sessions 05-07 |
| `Main portfolio/candidate_comparison.json` | Comparison readiness and construction disclosure | Sessions 05-06 and 10 (`optimization_readiness`, `fair_comparison_ready`) |

## Verification Baseline

Session 00 verification is documentation-only:

    python scripts/verify_docs.py

Later code/output contract sessions should use the Block 5 governance bundle added to
`TESTING.md`.

## Golden contract checklist (Session 11, captured)

Structural regression when optimizer disclosure contracts change without a full CLI run:

- `tests/fixtures/legacy_policy_optimizer_run_metadata_golden_v1.json`
- `tests/fixtures/candidate_optimizer_run_metadata_golden_v1.json`
- `tests/fixtures/optimization_comparison_block5_golden_v1.json`
- `tests/optimization_engine_golden_inputs.py` — deterministic builders and regenerate entrypoint
- `tests/test_optimization_engine_contract.py` — schema contracts, Block 5 post-audit surface
  fingerprint, live-vs-golden equality

Verified via `tests/test_optimization_engine_contract.py` (Session 11):

- legacy metadata exposes objective, fingerprints, covariance/Young ETF methodology, solver quality;
- candidate metadata exposes `candidate_only`, methodology blocks, and policy-boundary notes;
- comparison Block 5 slice exposes `optimizer_methodology`, `optimizer_quality`, and
  `optimization_readiness` with `optimizer_comparison_readiness_v1`.

Session 11 governance bundle: **159 passed**; `python scripts/verify_docs.py` **OK**.

## Phase 15 governance closure (Session 12, 2026-05-21)

Scope: [Optimization Engine Post-Audit Roadmap](../exec_plans/2026-05-20_optimization_engine_post_audit_roadmap.md) Sessions 00–12 — documentation sync and wave verification (no new optimizer logic).

### Verification commands (passed)

- Optimization Engine governance bundle ([TESTING.md](../../TESTING.md) § Optimization Engine Governance Wave Bundle): **159 passed**
- `python scripts/verify_docs.py`: **OK**

### Governance gap closure (G1–G10, Phase 15)

| Gap ID | Topic | Status after Sessions 01–12 |
| --- | --- | --- |
| G1 | Canonical Optimization Engine layer spec | **Closed** Session 01 (`RM-991`) |
| G2 | Legacy policy optimizer disclosure | **Closed** Session 03 (`RM-993`) |
| G3 | Comparison-level optimizer methodology | **Closed** Session 05 (`RM-995`) |
| G4 | Fallback / approximate-solve policy | **Closed** Session 06 (`RM-996`) |
| G5 | `analysis_end` and input fingerprints | **Closed** Session 08 (`RM-998`) |
| G6 | Robust scenario solver status | **Closed** Session 07 (`RM-997`) |
| G7 | Covariance and Young ETF methodology | **Closed** Session 09 (`RM-999`) |
| G8 | Target-only objective boundary | **Closed** Session 02 (`RM-992`, `DEC-2026-05-21-001`) |
| G9 | Stress `FAIL_*` vs release semantics | **Accepted** — Stress Lab / policy boundary; not Block 5 optimizer scope |
| G10 | Optimization comparison readiness | **Closed** Session 10 (`RM-1000`); per-candidate X-Ray remains optional (`KI-2026-05-21-001`) |
| — | Block 5 golden disclosure fixtures | **Closed** Session 11 (`RM-1001`) |

### Baseline hash note

Session 12 did **not** re-run `run_optimization.py` or candidate optimizer CLIs (no committed refresh of
`Main portfolio/run_result.json` or candidate `baseline_weights_metadata.json` on disk). Session 00
artifact checklist remains representative evidence; refresh hashes on the next representative policy or
candidate optimizer run.

### Documentation pack

- **DEC-2026-05-21-001** — target-only optimizer objectives.
- [optimization_engine_layer_spec.md](../specs/optimization_engine_layer_spec.md) — Block 5 canonical layer spec.
- [TESTING.md](../../TESTING.md), [docs/exec_plans/README.md](../exec_plans/README.md), [docs/ROADMAP.md](../ROADMAP.md): Phase 15 **Done** (`RM-990`–`RM-1002`).
- [CHANGELOG.md](../../CHANGELOG.md): Sessions 11–12 closure entries.

### Wave status

Block 5 Optimization Engine governance **Sessions 00–12: complete**. Optimizer paths are audit-grade for
handoff per [methodology map](2026-05-20_optimization_engine_methodology_map.md) §8 (post-Session 12):
canonical spec, machine-readable disclosures, fallback/solver quality propagation, comparison readiness,
and golden contracts — without changing optimizer formulas, constraints, mandate gates, or generated weights.

## Session 00 Outcome

Session 00 created this snapshot and registered the active Block 5 ExecPlan. It did not modify code,
formulas, objectives, constraints, mandate gates, generated weights, or generated report artifacts.
