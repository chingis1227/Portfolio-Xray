# Block 2.4 Hidden Exposure — Session 10 Tests + Golden

Date: 2026-05-29

Status: **CLOSED**

Prior: [Session 09 legacy PCA cross-ref](2026-05-29_block_2_4_session_09_legacy_pca_cross_ref.md)

## Scope delivered

| Item | Result |
| --- | --- |
| `tests/test_block_2_4_matrix_coverage.py` — parametrized §10 ✅ v2 row coverage | **PASS** |
| `assert_block_2_4_product_contract` in contract tests | **PASS** |
| Golden `block_2_4` v2 surface test (`heuristic_v2`, limitations, contributors, PCA cross-ref) | **PASS** |
| Expanded `contract_fingerprint` Block 2.4 fields | **PASS** |
| Golden fixture regen (`portfolio_xray_golden_v2.json`) | **PASS** |
| Session 10 regression bundle | **PASS** — **129 passed** |

## Matrix coverage (Session 10)

- **69 parametrized evidence rows** — one pytest case per implementable ✅ v2 sub-dimension (D1–D11 evidence metrics).
- **Deferred upstream rows** — `blocked_upstream_fields` registry (all `BLOCKED_UPSTREAM_FIELDS`) + limitation snippets on owning alerts.
- **Cross-ref rows** — PCA legacy (D4) and stress hedge confirmation (D9) exercised in rich matrix fixture.
- **D12/D13** — mandatory `contributing_assets`, `limitations`, `confidence_reason`, `heuristic_v2` metadata.

Deferred ⏸ rows remain documented via registry/limitations tests (not scored in Block 2.4).

## Regression command

```bash
python -m pytest tests/test_block_2_4_hidden_exposure.py tests/test_block_2_4_matrix_coverage.py tests/test_portfolio_xray_contract.py -q
```

Regenerate golden after intentional contract changes:

```bash
python tests/portfolio_xray_golden_inputs.py
python -m pytest tests/test_portfolio_xray_contract.py -q
```

Session 10 — see [Session 10 tests + golden](2026-05-29_block_2_4_session_10_tests_golden.md) (**CLOSED**).

## Next

Session 11 — see [Session 11 Core MVP validation](2026-05-29_block_2_4_session_11_core_mvp_validation.md) (**CLOSED**).
