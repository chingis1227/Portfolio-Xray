# Block 2.4 Hidden Exposure — Session 11 Core MVP Validation

Date: 2026-05-29

Status: **CLOSED**

Prior: [Session 10 tests + golden](2026-05-29_block_2_4_session_10_tests_golden.md)

## Scope delivered

| Item | Result |
| --- | --- |
| Shared Block 2.4 v2 contract in `scripts/core_mvp_validation_contract.py` | **PASS** |
| `check_block_2_4_hidden_exposure` wired into `validate_core_mvp_block2_fixture_matrix.py` | **PASS** |
| `core_mvp_block2_block_status` partial when Block 2.4 contract violated | **PASS** |
| `tests/test_core_mvp_block2_4_contract.py` unit coverage | **PASS** |
| Boundaries + contract tests import shared validator | **PASS** |
| Fixture-matrix integration test asserts Block 2.4 v2 on materialized X-Ray | **PASS** |
| Session 11 regression bundle | **PASS** — **140 passed** |

## Validation contract (Session 11)

- **Institutional v2 surface:** `heuristic_v2`, confidence model `v2`, six alerts with mandatory per-alert fields, evidence schema, `contributing_assets` cap, `blocked_upstream_fields` registry count.
- **Stress boundary:** `does_not_run_stress_lab=true`; no embedded Block 3 stress payloads at Block 2.4 top level.
- **Fixture matrix:** optional diagnostic block reports `special_checks.contract_violations`; product/core status `partial` when violated.

## Regression command

```bash
python -m pytest tests/test_core_mvp_block2_4_contract.py tests/test_block_2_4_hidden_exposure.py tests/test_block_2_4_matrix_coverage.py tests/test_portfolio_xray_contract.py tests/test_core_mvp_blocks_1_3_boundaries.py -q
```

Validate Block 2 fixture matrix outputs (when present on disk):

```bash
python scripts/validate_core_mvp_block2_fixture_matrix.py
```

## Next

Session 12 — see [Session 12 live demo + regression](2026-05-29_block_2_4_session_12_live_demo_regression.md) (**CLOSED**).
