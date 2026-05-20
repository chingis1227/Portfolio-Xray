# Candidate Portfolio Factory Baseline Snapshot

Date: 2026-05-20

Purpose: fixed baseline for Block 4 (Candidate Portfolio Factory) governance wave (Phase 14,
Sessions 00–11). Session 00: contract freeze and checklist only—no factory/comparison logic changes.

Governed by: [Candidate Portfolio Factory Post-Audit Roadmap](../exec_plans/2026-05-20_candidate_factory_post_audit_roadmap.md).

Methodology reference: [Candidate Factory Methodology Map](2026-05-20_candidate_factory_methodology_map.md).

## Baseline commands (Session 00)

```bash
python scripts/verify_docs.py
python -m pytest tests/test_candidate_factory.py tests/test_candidate_comparison.py tests/test_portfolio_review_workflow.py -q
```

Optional representative run (refresh fingerprints when data/network available):

```bash
python run_portfolio_review.py --mode core
python run_portfolio_review.py --mode full
```

Advanced (factory only, after subject exists):

```bash
python run_report.py --materialize-analysis-subject
python run_candidate_factory.py --profile core_v1 --then-compare
python run_candidate_factory.py --profile default_v1 --then-compare
```

## Baseline artifacts to compare after each session

Under `{output_dir_final}` (default `Main portfolio/`):

| Artifact | Role |
| --- | --- |
| `analysis_subject/snapshot_10y.json` | Review `analysis_end` source for freshness |
| `analysis_subject/run_metadata.json` | `analysis_setup_summary` precedence |
| `candidate_factory_run.json` | Per-step status, reason_code, freshness |
| `candidate_factory_run.txt` | Human factory summary |
| `candidate_comparison.json` | Full registry rows + `candidate_menu` |
| `candidate_comparison.txt` | Optional table |
| `equal-weight portfolio/snapshot_10y.json` | Representative core candidate |
| `decision_package_summary.json` | Partial-menu warnings |

## Baseline snapshot fingerprints (Session 00)

**Status:** not captured in-repo at Session 00 (no committed `Main portfolio/candidate_factory_run.json`
or `candidate_comparison.json` in workspace). After a representative `run_portfolio_review.py --mode core`
(or full), record SHA256 here:

| Relative path | size | sha256 |
| --- | --- | --- |
| `Main portfolio/candidate_factory_run.json` | TBD | TBD |
| `Main portfolio/candidate_comparison.json` | TBD | TBD |
| `Main portfolio/analysis_subject/snapshot_10y.json` | TBD | TBD |
| `equal-weight portfolio/snapshot_10y.json` | TBD | TBD |

Compare command template (after fingerprints exist):

```bash
python -c "from pathlib import Path; import hashlib; base=Path('Main portfolio'); files=['candidate_factory_run.json','candidate_comparison.json','analysis_subject/snapshot_10y.json']; print(chr(10).join(f'{f}|{hashlib.sha256((base/f).read_bytes()).hexdigest()}' for f in files if (base/f).is_file()))"
```

## `candidate_factory_run_v1` contract checklist

Top-level required keys:

1. `schema_version` = `candidate_factory_run_v1`
2. `diagnostic_only` = `true`
3. `generated_at`, `factory_profile_id`, `output_dir_final`, `analysis_end`
4. `options`: `skip_existing`, `force`, `fail_fast`, `then_compare`
5. `steps[]`: each with `candidate_id`, `status`, `reason_code`, `entry_commands`, `freshness_status` when applicable
6. `summary`: `total`, `succeeded`, `failed`, `skipped_existing`, `skipped_dependency`, `rebuilt_stale`
7. `warnings`, `next_recommended_command`

Per-step `status` values (V1): `succeeded`, `failed`, `skipped_existing`, `skipped_dependency`.

Per-step `reason_code` values (V1): `skipped_existing`, `skipped_dependency`,
`missing_snapshot_after_build`, `stale_snapshot_after_build`, `subprocess_failed`,
`unknown_candidate_id`, and builder-mapped codes (`builder_fail_config`, `builder_infeasible_universe`, …).
**G1 closed** Session 02 (`RM-972`): factory reads `summary.json` `FAIL_*` when snapshot missing or subprocess failed.

## `candidate_comparison_v1` contract checklist

Top-level required keys:

1. `schema_version` = `candidate_comparison_v1`
2. `diagnostic_only` = `true`
3. `comparison_baseline_candidate_id` (portfolio-first: `analysis_subject` when sidecar exists)
4. `generated_at`, `analysis_end`, `investor_currency`, `output_dir_final`
5. `analysis_setup_summary`
6. `windows`, `primary_window` (`10y`)
7. `candidates[]` — **18 registry rows** always present (including `unavailable`)
8. `candidate_menu` — `is_partial_menu`, `intended_menu_profile_id`, `product_menu_profile_id`, status counts
9. `warnings`, `legacy_artifacts`

Per-candidate row (when `available` or `degraded`):

- `metrics` keyed by `3y`/`5y`/`10y`
- `stress.overall` (degraded if missing)
- `diversification`, `weight_concentration` (from `snapshot_10y` when present)
- `status` / `unavailable_reason` — including `stale_snapshot_analysis_end` (RM-902)

Portfolio-first gating:

- `policy` row: `unavailable` + `legacy_policy_not_default_portfolio_first_candidate` when `analysis_subject` available.

## Session 00 checklist result (captured)

- Methodology map on disk: yes
- Active ExecPlan registered: yes
- Phase 14 ROADMAP rows RM-970–RM-981: yes
- `verify_docs.py`: pass (Session 00)
- Factory/comparison focused pytest (3 modules): pass (Session 00)
- Live artifact fingerprints: deferred (not in repo)

## Known gaps at baseline (from methodology map)

| ID | Gap | Target session |
| --- | --- | --- |
| G1 | ~~Builder FAIL_* → generic factory reason~~ | **Closed** Session 02 (`RM-972`) |
| G2 | ~~No config fingerprint freshness~~ | **Closed** Session 06 (RM-976) |
| G3 | ~~`freshness_status: unchecked` skip risk~~ | closed Session 03 (RM-973) |
| G6 | ~~No `construction_disclosure` in comparison~~ | closed Session 04 (RM-974) |
| G8 | Robust MV λ path opaque in factory | **Closed** Session 07 (RM-977) |
| G10 | robust_scenario uses Main stress/scenario artifacts | **Closed** Session 07 (RM-977) |
| G7 | ~~Layer spec scaffold only~~ | **Closed** Session 05 (`RM-975`) |
| — | ~~No golden comparison fixture~~ | **Closed** Session 08 (`RM-978`) — `tests/fixtures/candidate_*_golden_v1.json` |
| — | ~~RM-921 resumable factory~~ | **Closed** Session 09 (`RM-979`) |
| G9 | ~~Concept-only candidates not in registry~~ | **Closed** Session 11 (`RM-981`) |

## Phase 14 governance closure (Session 11, 2026-05-20)

Scope: [Candidate Portfolio Factory Post-Audit Roadmap](../exec_plans/2026-05-20_candidate_factory_post_audit_roadmap.md) Sessions 00–11 — P5 concept registry DEC and wave verification (no new factory logic).

### Verification commands (passed)

- Candidate Factory governance bundle ([TESTING.md](../../TESTING.md) § Candidate Factory Governance Wave Bundle): **77 passed**
  (`--basetemp=tmp/pytest_gov_cf_s11`).
- Family math spot-check: **19 passed** (`test_equal_weight_baselines`, `test_risk_parity_baseline`, `test_risk_budgeting`).
- Spot-check family math: `tests/test_equal_weight_baselines.py`, `tests/test_risk_parity_baseline.py`, `tests/test_risk_budgeting.py`.
- `python scripts/verify_docs.py`: **OK**

### Governance gap closure (G1–G10, Phase 14)

| Gap ID | Topic | Status after Sessions 01–11 |
| --- | --- | --- |
| G1 | Builder FAIL_* → factory reason | **Closed** Session 02 (`RM-972`) |
| G2 | Config fingerprint freshness | **Closed** Session 06 (`RM-976`) |
| G3 | Unchecked freshness skip | **Closed** Session 03 (`RM-973`) |
| G4 | Operator playbook / heavy `default_v1` | **Closed** Session 10 (`RM-980`) + RM-920 mitigations |
| G5 | Resumable factory (RM-921) | **Closed** Session 09 (`RM-979`) |
| G6 | `construction_disclosure` | **Closed** Session 04 (`RM-974`) |
| G7 | Layer spec handoff | **Closed** Session 05 (`RM-975`); per-candidate X-Ray in comparison remains **accepted** (`KI-2026-05-20-008`) |
| G8 | Robust MV λ disclosure | **Closed** Session 07 (`RM-977`) |
| G9 | Concept-only candidates vs registry | **Closed** Session 11 (`RM-981`, DEC-2026-05-20-003) |
| G10 | `robust_scenario` Main prerequisites | **Closed** Session 07 (`RM-977`) |
| — | Golden contract fixtures | **Closed** Session 08 (`RM-978`) |

### Baseline hash note

Session 11 did **not** re-run `run_portfolio_review.py` (no committed `Main portfolio/candidate_factory_run.json`
on disk). Session 00 fingerprint table remains **TBD** until the next representative core/full review;
refresh hashes using **Compare command template** above.

### Documentation pack

- **DEC-2026-05-20-003** — concept registry boundary.
- [candidate_portfolios_spec.md](../specs/candidate_portfolios_spec.md) — § Concept candidates not in registry.
- [TESTING.md](../../TESTING.md), [docs/exec_plans/README.md](../exec_plans/README.md), [docs/ROADMAP.md](../ROADMAP.md): Phase 14 **Done** (`RM-970`–`RM-981`).
- [CHANGELOG.md](../../CHANGELOG.md): Session 11 closure entry.

### Wave status

Block 4 Candidate Portfolio Factory governance **Sessions 00–11: complete**. Factory layer is audit-grade for handoff per [methodology map](2026-05-20_candidate_factory_methodology_map.md) §8 (post-Session 11).
