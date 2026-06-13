# Blocks 1–5 Deep Audit Snapshot (Post-Phase 16)

Date: 2026-05-21

Status: **Active input** for [Post-Deep-Audit Foundation Plan](../exec_plans/2026-05-21_post_deep_audit_foundation_plan.md) (Phase 17).

This document freezes the second-level audit (methodology, reproducibility, downstream readiness)
after Phase 16 ([Blocks 1-5 MVP Core Reliability Plan](../exec_plans/2026-05-21_blocks_1_5_mvp_core_reliability_plan.md)).
It does not override canonical specs or code.

## Executive verdict

| Question | Answer |
| --- | --- |
| Are Blocks 1–5 a reliable MVP core... | **Yes** for portfolio-first **core** review with explicit `analysis_subject`, subject-first artifacts, offline smoke, and Phase 16 trust fixes. |
| Machine-trustworthy full optimizer menu... | **Not yet** — on-disk comparison shows most optimizer rows `degraded`; only `minimum_variance` was `fair_comparison_ready` at audit time. |
| Safe to wire Blocks 6–10 now... | **Conditional** — proceed on **core menu** with guards; do not rank `degraded` optimizers or treat core (6) as full (16) without reading `candidate_menu`. |

**Operating conditions (mandatory):**

1. Default: `python run_portfolio_review.py --mode core --skip-pdf`
2. Read `{output_dir_final}/analysis_subject/` before candidates or decision outputs
3. Baseline = `analysis_subject`, not legacy policy weights
4. Full menu: explicit `--mode full` + `--resume-candidates` after interrupt
5. Stress `DIAG_*` ≠ mandate `FAIL_*` ([stress_testing_spec.md](../specs/stress_testing_spec.md))

## What Phase 16 fixed (do not reopen)

| Gap | Phase 16 session | Evidence |
| --- | --- | --- |
| Overallocated subject weights warning-only | RM-1011 | `src/config_schema.py` blocks sum > 1.0 |
| Stale factory steps in comparison | RM-1012 | `candidate_menu.factory_evidence_status` |
| No orchestrator resume | RM-1013 | `--resume-candidates` |
| Silent optimizer `available` without readiness | RM-1014 | `degraded` + warning codes |
| No five-ticker offline gate | RM-1015 | `tests/test_blocks_1_5_mvp_smoke.py` (4 passed) |
| Buried data-quality trust | RM-1016 | `data_trust_summary` / `data_trust_signals` |
| Doc handoff | RM-1017–RM-1018 | README, SPEC, OUTPUTS, TESTING, runbook |

## Phase 17 gaps (P0 / P1 / P2)

### P0 — can mislead decision workflow

| ID | Gap | Evidence | Planned session |
| --- | --- | --- | --- |
| P17-G1 | Selection/health treat `degraded` as eligible for ranking | `src/selection_engine.py` `ELIGIBLE_STATUSES` includes `degraded` | RM-1022 |
| P17-G2 | Core run can be read as full optimizer comparison | `candidate_menu.is_partial_menu: true`, product menu 16 vs intended 6 | RM-1022, RM-1028 |
| P17-G3 | Most optimizer rows not fair-comparison-ready on disk | `Main portfolio/candidate_comparison.json`: 9 degraded optimizers, 1 ready (`minimum_variance`) | RM-1023 |
| P17-G4 | No live networked E2E in closure gate | Phase 16 Session 09: offline bundle only for closure | RM-1021 |
| P17-G5 | Invalid ticker not blocked at Block 1 | `UNKNOWN_TICKER_POLICY` warn-only in `analysis_setup` | RM-1024 |

### P1 — trust and reproducibility

| ID | Gap | Evidence | Planned session |
| --- | --- | --- | --- |
| P17-G6 | False `factory_evidence_status: stale` same-run | Factory `generated_at` 3s before comparison rebuild | RM-1025 |
| P17-G7 | `analysis_mode` vs `current_portfolio` naming | `optimize_from_universe` in `run_metadata` with subject current | RM-1026 |
| P17-G8 | No single review bundle fingerprint | Context split across subject/factory/comparison | RM-1026 |
| P17-G9 | Blocks 6–7 lack guarded handoff spec | Comparison contract exists; no downstream readiness spec | RM-1027 |
| P17-G10 | Decision package may understate partial/degraded | Partial lines exist; selection still favors degraded | RM-1028 |

### P2 — accepted or later

| ID | Gap | Notes |
| --- | --- | --- |
| P17-G11 | Full `default_v1` factory heavy | Accepted; `--resume-candidates` |
| P17-G12 | X-Ray G7 deferred (factor/drawdown/ES RC display) | Phase 12; not Phase 17 |
| P17-G13 | `portfolio_xray` optional in comparison readiness | KI-2026-05-21-001 accepted |
| P17-G14 | `robust_scenario` uses Main stress artifacts | Documented G10; not a bug |

## Block maturity (post-audit)

| Block | Classification |
| --- | --- |
| 1 Input | Reliable; needs ticker preflight (P17-G5) |
| 2 X-Ray | Strong MVP foundation; deferred G7 displays |
| 3 Stress | Strong; DIAG vs mandate interpretation risk |
| 4 Factory | Reliable core menu; full menu operational limits |
| 5 Optimizer | Disclosure strong; fairness needs metadata refresh |

## Evidence table (repository)

| Conclusion | Source |
| --- | --- |
| Seven X-Ray sections + trust | `Main portfolio/analysis_subject/portfolio_xray.json` |
| Stress scorecard + trust | `Main portfolio/analysis_subject/stress_report.json` (keys verified 2026-05-21) |
| Baseline `analysis_subject` | `Main portfolio/candidate_comparison.json` |
| Partial core menu | `candidate_menu.review_mode: core`, `is_partial_menu: true` |
| Factory stale vs comparison | `factory_evidence_status: stale`, `factory_steps_used: false` |
| Optimizer degraded mass | Row status audit on `candidate_comparison.json` |
| Offline smoke | `tests/test_blocks_1_5_mvp_smoke.py` |
| Phase 16 closure | `docs/exec_plans/2026-05-21_blocks_1_5_mvp_core_reliability_plan.md` |

## Failure-case summary

| Case | Today | Phase 17 target |
| --- | --- | --- |
| Weights > 100% | Blocked (Phase 16) | Keep |
| Invalid ticker | Late / warn | Block at input (RM-1024) |
| Core as full | Disclosed in menu | Harder guards in selection (RM-1022) |
| Degraded optimizer ranked | Allowed | Exclude from favoring (RM-1022) |
| Stale factory steps used | Blocked (RM-1012) | Fix false stale (RM-1025) |
| DIAG stress misread | Spec only | Package wording (RM-1028) |

## Follow-up plan

All remediation is tracked in [Post-Deep-Audit Foundation Plan](../exec_plans/2026-05-21_post_deep_audit_foundation_plan.md) Sessions 02–10 (`RM-1021`–`RM-1029`).
