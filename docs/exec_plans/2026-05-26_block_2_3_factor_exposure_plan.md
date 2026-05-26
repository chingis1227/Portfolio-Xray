# Block 2.3 Factor Exposure / Factor Sensitivity MVP

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`,
`Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.
This plan follows `PLANS.md` from the repository root.

## Purpose / Big Picture

Portfolio MRI is adding the third product-facing Portfolio X-Ray block: Block 2.3 Factor Exposure / Factor Sensitivity. After this change, a user can open `analysis_subject/portfolio_xray.json` and see which market factors appear to drive the current portfolio, alongside the already implemented Block 2.1 asset allocation and Block 2.2 portfolio metrics. The block is diagnostic-only and does not change weights, generate candidates, run stress shocks, or recommend rebalancing.

Block 2.3 is intentionally an adapter over existing `stress_report.json` factor diagnostics. The stress report generation layer owns all factor calculations. If required fields such as `factor_betas_5y` are missing, Block 2.3 must emit `partial` or `unavailable` with warnings; the missing data issue must be fixed upstream in stress report generation or `src/stress_factors.py`.

## Progress

- [x] (2026-05-26) Session 1 audit completed: existing factor pipeline and X-Ray wiring identified.
- [x] (2026-05-26) ExecPlan created with the adapter-only architecture decision.
- [x] (2026-05-26) Session 2 product contract docs and decision register updated.
- [x] (2026-05-26) Session 3 builder module implemented as a read-only adapter over `stress_report`.
- [x] (2026-05-26) Session 4 Portfolio X-Ray wiring implemented.
- [x] (2026-05-26) Session 5 manifest and E2E checks updated.
- [x] (2026-05-26) Session 6 tests and golden fixture updated.
- [x] (2026-05-26) Session 7 runtime validation completed.
- [x] (2026-05-26) Session 8 closure summary recorded.

## Surprises & Discoveries

- Observation: The repository already has mature factor diagnostics in `src/stress_factors.py`, including weekly OLS/HAC regressions, Kalman beta diagnostics, and factor variance decomposition.
  Evidence: `portfolio_factor_regression_weekly`, `attach_kalman_factor_betas_to_stress_report`, and `factor_variance_decomposition_weekly` already write or support the `stress_report` fields needed by Block 2.3.
- Observation: `src/portfolio_xray.py` already has a legacy `sections.factor_exposure` section, but not a top-level product block.
  Evidence: `build_portfolio_xray_v2` returns `block_2_1_asset_allocation` and `block_2_2_portfolio_metrics`, while factor exposure is only present inside `sections`.
- Observation: The live demo `stress_report` contains enough 5Y data and variance decomposition for a partial product block, but 10Y beta diagnostics are missing `beta_credit` and Kalman current beta is not available.
  Evidence: `Main portfolio/analysis_subject/portfolio_xray.json` generated on 2026-05-26 has Block 2.3 status `partial`, `factor_betas_5y.status=available`, `factor_betas_10y.status=partial`, `kalman_current_beta.available=false`, and warnings for missing 10Y `beta_credit`, normalized `usd/vix` names, and unavailable Kalman.
- Observation: The root `Main portfolio/portfolio_xray.json` remains a legacy surface without product blocks; the portfolio-first product X-Ray contract is under `Main portfolio/analysis_subject/portfolio_xray.json`.
  Evidence: manual JSON inspection after `run_portfolio_review.py --candidates equal_weight`.

## Decision Log

- Decision: Implement Block 2.3 as a product-facing adapter over `stress_report` factor diagnostics only.
  Rationale: This avoids a second independent factor calculation engine and keeps stress/factor methodology in the existing stress layer.
  Date/Author: 2026-05-26 / Codex.
- Decision: Missing `stress_report` fields produce `partial` or `unavailable` output with warnings; Block 2.3 must not trigger OLS, Kalman, variance decomposition, data loading, or any other factor calculation.
  Rationale: Missing factor fields are upstream pipeline issues and should be fixed where the canonical calculations are produced.
  Date/Author: 2026-05-26 / Codex.
- Decision: Keep legacy `sections.factor_exposure` unchanged.
  Rationale: Existing report formatters and golden tests may depend on that shape; the product-facing contract is additive.
  Date/Author: 2026-05-26 / Codex.

## Outcomes & Retrospective

Completed on 2026-05-26.

Implemented `src/block_2_3_factor_exposure.py` as an additive product-facing adapter. It emits
`block_2_3_factor_exposure` with all eight production beta keys, 5Y/10Y windows, Kalman availability,
confidence/significance, variance contribution, top-three factor ranking, interpretation, data quality
warnings, naming validation, and an explicit Stress Lab separation note. The builder reads existing
`stress_report` fields only and does not trigger factor calculations.

Wired the block into `src/portfolio_xray.py::build_portfolio_xray_v2`, added product bundle helpers
and live E2E checks, updated docs/specs/decision log/changelog, and intentionally regenerated the
Portfolio X-Ray golden fixture.

Validation evidence:

    .\.venv\Scripts\python.exe -m py_compile src\block_2_3_factor_exposure.py src\portfolio_xray.py src\product_bundle_paths.py src\live_core_e2e.py src\live_full_e2e.py
    .\.venv\Scripts\python.exe -m pytest tests/test_block_2_3_factor_exposure.py tests/test_block_2_3_pipeline_integration.py -q
    # 9 passed
    .\.venv\Scripts\python.exe -m pytest tests/test_portfolio_xray_contract.py -q
    # 6 passed
    .\.venv\Scripts\python.exe -m pytest tests/test_block_2_3_factor_exposure.py tests/test_block_2_3_pipeline_integration.py tests/test_block_2_1_asset_allocation.py tests/test_block_2_2_portfolio_metrics.py tests/test_portfolio_xray_contract.py tests/test_product_bundle_paths.py tests/test_blocks_1_5_mvp_smoke.py -q
    # 56 passed
    .\.venv\Scripts\python.exe -m pytest tests/test_portfolio_xray.py tests/test_block_2_1_pipeline_integration.py tests/test_block_2_2_pipeline_integration.py tests/test_block_2_3_pipeline_integration.py -q
    # 46 passed
    .\.venv\Scripts\python.exe -m pytest tests/test_runtime_mode_regression_boundaries.py tests/test_product_bundle_paths.py -q
    # 31 passed
    .\.venv\Scripts\python.exe run_portfolio_review.py
    # PASS, product_diagnosis_only, candidate_count=0
    .\.venv\Scripts\python.exe run_portfolio_review.py --candidates equal_weight
    # PASS, product_one_candidate, explicit equal_weight scope
    .\.venv\Scripts\python.exe scripts\validate_one_candidate_demo.py
    # RESULT: PASS
    .\.venv\Scripts\python.exe scripts\verify_docs.py
    # docs verification: OK

Limitations / follow-up: live Block 2.3 is `partial` because upstream diagnostics do not provide every
10Y beta key and do not provide current Kalman beta output. Per the architecture decision, these are
upstream `stress_report` / `src/stress_factors.py` issues, not X-Ray fallback calculations.

## Context and Orientation

`src/stress_factors.py` owns factor calculations. It defines the production factor registry and beta keys, loads weekly factor series, computes weekly regressions, provides HAC/Newey-West inference, computes Kalman current betas, and calculates factor variance decomposition. `run_report.py` and legacy `run_optimization.py` attach those diagnostics to `stress_report.json`.

`src/portfolio_xray.py` builds `portfolio_xray.json`. It already emits top-level `block_2_1_asset_allocation` from `src/block_2_1_asset_allocation.py` and `block_2_2_portfolio_metrics` from `src/block_2_2_portfolio_metrics.py`. Block 2.3 should follow that pattern with a new module `src/block_2_3_factor_exposure.py`, while leaving the existing legacy `sections.factor_exposure` intact.

The production factors and beta keys for Block 2.3 are fixed:

- `equity` -> `beta_eq`
- `real_rates` -> `beta_rr`
- `inflation` -> `beta_inf`
- `credit` -> `beta_credit`
- `USD` -> `beta_usd`
- `commodity` -> `beta_cmd`
- `VIX_volatility` -> `beta_vix`
- `us_growth` -> `beta_us_growth`

## Plan of Work

First, document the product contract in the Portfolio X-Ray specs and record the architecture decision in `DECISIONS.md`.

Second, add `src/block_2_3_factor_exposure.py`. The builder must accept `stress_report`, `analysis_setup`, and `weights`, then return a JSON-safe dictionary. It reads existing `stress_report` fields, validates naming, builds 5Y/10Y beta snapshots, summarizes HAC confidence, surfaces Kalman availability, maps variance decomposition, ranks at most three factor drivers, and writes plain-English diagnostic interpretation. It must not import or call calculation functions from `src/stress_factors.py`.

Third, wire the builder into `src/portfolio_xray.py::build_portfolio_xray_v2` as top-level `block_2_3_factor_exposure`.

Fourth, update `src/product_bundle_paths.py`, `src/live_core_e2e.py`, and `src/live_full_e2e.py` so product bundle metadata and live gates recognize Block 2.3.

Fifth, add focused unit and pipeline tests, update the X-Ray golden contract intentionally, and run focused validation before broader checks.

## Concrete Steps

Work from `D:\Рабочий стол\КУРСОР ТУЛА ДИАГНОСТИКА`.

Use PowerShell commands. For Python checks, prefer `.\.venv\Scripts\python.exe` if `.venv` exists; otherwise use `py -3` after checking availability.

Planned validation commands:

    python -m pytest tests/test_block_2_3_factor_exposure.py tests/test_block_2_3_pipeline_integration.py -q
    python -m pytest tests/test_block_2_1_asset_allocation.py tests/test_block_2_2_portfolio_metrics.py tests/test_portfolio_xray_contract.py tests/test_product_bundle_paths.py tests/test_blocks_1_5_mvp_smoke.py -q
    python run_portfolio_review.py
    python run_portfolio_review.py --candidates equal_weight
    python scripts/validate_one_candidate_demo.py

## Validation and Acceptance

The implementation is accepted when `analysis_subject/portfolio_xray.json` contains `block_2_3_factor_exposure` with all eight production beta keys, 5Y/10Y beta sections that degrade gracefully, Kalman status, factor confidence, variance contribution or explicit unavailable status, top-three risk ranking, client-facing summary, data quality warnings, and metadata.

Acceptance also requires Block 2.1 and Block 2.2 to remain present, legacy `sections.factor_exposure` to remain compatible, default portfolio review runtime to remain diagnosis-first, and `--candidates equal_weight` to remain one-candidate scoped.

## Idempotence and Recovery

All changes are additive. If tests fail because expected product contracts changed, update only the intended Block 2.3 tests and golden fixture after confirming the output shape is deliberate. Do not edit generated portfolio output folders except when running explicit validation commands. Do not revert unrelated dirty `__pycache__` files already present in the working tree.

## Artifacts and Notes

Session 1 audit found:

    src/stress_factors.py::portfolio_factor_regression_weekly
    src/stress_factors.py::attach_kalman_factor_betas_to_stress_report
    src/stress_factors.py::factor_variance_decomposition_weekly
    src/portfolio_xray.py::build_portfolio_xray_v2
    src/portfolio_xray.py::_factor_exposure_section

## Interfaces and Dependencies

New public builder:

    src/block_2_3_factor_exposure.py
    BLOCK_2_3_ID = "2.3_factor_exposure"
    build_block_2_3_factor_exposure(
        *,
        stress_report: dict[str, Any] | None,
        analysis_setup: dict[str, Any] | None = None,
        weights: dict[str, Any] | None = None,
    ) -> dict[str, Any]

New X-Ray key:

    block_2_3_factor_exposure

New product bundle helper constants/functions:

    PORTFOLIO_XRAY_BLOCK_2_3_KEY
    portfolio_xray_has_block_2_3(doc)

Revision note (2026-05-26): Initial ExecPlan created before implementation. It records the adapter-only architecture rule and the discovered upstream factor diagnostics.

Closure note (2026-05-26): Implementation and validation completed. Block 2.3 is present on the
portfolio-first product X-Ray surface and remains a read-only adapter over `stress_report`.
