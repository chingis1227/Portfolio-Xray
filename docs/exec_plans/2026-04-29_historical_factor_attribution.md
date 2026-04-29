# Add historical stress factor attribution

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`,
`Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document follows the repository rules in `PLANS.md`.

## Purpose / Big Picture

After this change, a user reading `stress_report.json` or `stress_commentary.txt` can see not only that the portfolio lost money in each historical stress episode, but which factor channels explain the model-based loss: equity, real rates, inflation, credit, USD, commodity, VIX, US growth, and oil when available. This makes the stress output answer questions such as "was 2008 credit-led or equity-led for this portfolio?" while explicitly warning that the attribution is model-based beta times realized factor shock, not a causal realized decomposition.

## Progress

- [x] (2026-04-29 00:00+02:00) Read `PLANS.md`, stress report generation, existing OOS beta-shock explainability, commentary, and stress specification references.
- [x] (2026-04-29 00:00+02:00) Implemented JSON enrichment for `historical_results` from the existing `factor_beta_shock_oos` episode calculations.
- [x] (2026-04-29 00:00+02:00) Added human-readable historical factor attribution and model-based caveat to `stress_commentary.txt`.
- [x] (2026-04-29 00:00+02:00) Updated focused tests and documentation (`README.md`, `SPEC.md`, `docs/docs/stress_testing_spec.md`).
- [x] (2026-04-29 00:00+02:00) Ran focused validation and recorded results.

## Surprises & Discoveries

- Observation: The project already computes per-episode factor contributions under `factor_beta_shock_oos.episodes[*].factor_contrib_5y`, `factor_contrib_10y`, and `factor_contrib_roll3y_pre`.
  Evidence: `src/stress_factors.py::factor_oos_beta_shock_explainability` builds `factor_shock_sum` and the three contribution maps, but `src/stress.py` only emits aggregate `historical_results` without factor attribution fields.

## Decision Log

- Decision: Use 5Y factor betas as the primary attribution written into `historical_results`, while preserving 10Y and rolling-3Y pre-episode variants in the existing `factor_beta_shock_oos` block.
  Rationale: The existing synthetic stress contract uses current portfolio betas and `factor_betas` mirrors `factor_betas_5y`; using 5Y keeps the main historical attribution aligned with the current portfolio risk profile while `factor_beta_shock_oos` remains available for robustness checks.
  Date/Author: 2026-04-29 / Codex.

- Decision: Add a textual caveat that the decomposition is model-based beta times realized factor shock and not a pure realized causal decomposition.
  Rationale: The user explicitly requested this limitation, and the distinction prevents over-interpreting regression attribution as causality.
  Date/Author: 2026-04-29 / Codex.

## Outcomes & Retrospective

Completed. `run_report.py` now enriches `stress_report.json.historical_results` after `factor_beta_shock_oos` is computed. Each historical row can carry `historical_factor_attribution`, `pnl_by_factor_pct`, `top_factor_drivers`, `largest_negative_factor`, and model-vs-realized error fields. `stress_commentary.txt` now prints a caveat that the attribution is model-based beta times realized factor shock, lists top drivers per historical episode, and summarizes repeated largest negative drivers as a structural vulnerability signal. Documentation and focused tests were updated.

## Context and Orientation

`src/stress.py` creates synthetic `scenario_results` and aggregate `historical_results`. Synthetic rows already have `pnl_by_factor_pct`. Historical rows currently have `max_dd`, `pnl_real_episode`, volatility, and pass/fail diagnostics, but no factor contribution fields.

`src/stress_factors.py` estimates factor betas and contains `factor_oos_beta_shock_explainability`, which already calculates per-episode realized factor shocks and beta times shock model PnL. `run_report.py` stores that object in `stress_report["factor_beta_shock_oos"]`. `src/portfolio_commentary.py` writes `stress_commentary.txt` from `stress_report.json`.

## Plan of Work

Add a helper in `src/stress_factors.py` that takes the current `historical_results` rows and the `factor_beta_shock_oos` object, then returns enriched historical rows. The helper will copy each row and add `historical_factor_attribution` with method, caveat, beta source, model PnL, model error versus realized episode PnL, factor shock sums, factor contributions, top drivers ranked by absolute contribution, and the largest negative driver. It will also add convenience top-level fields `pnl_by_factor_pct`, `top_factor_drivers`, `largest_negative_factor`, `factor_model_pnl_pct`, and `factor_model_error_pct` for easy consumption.

Update `run_report.py` after `factor_beta_shock_oos` is computed so exported `stress_report.json` includes enriched `historical_results`. Update `src/portfolio_commentary.py` to print the caveat and top factor drivers per historical episode, plus a compact structural vulnerability summary based on repeated largest negative drivers.

Update `tests/test_factor_oos_explainability.py` for the enrichment helper and `tests/test_portfolio_commentary.py` for commentary output. Update `docs/docs/stress_testing_spec.md`, `SPEC.md`, and `README.md` so the JSON contract and user-visible reporting are documented.

## Concrete Steps

Work from repository root:

    C:\Users\ShumeikoYe\OneDrive\Рабочий стол\Курсор Модель Блекрока 2

Run focused tests after edits:

    python -m pytest tests\test_factor_oos_explainability.py tests\test_portfolio_commentary.py -vv

In this environment, `python` was not on PATH, so validation used the bundled runtime:

    C:\Users\ShumeikoYe\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest tests\test_factor_oos_explainability.py tests\test_portfolio_commentary.py -vv
    3 passed in 10.31s

    C:\Users\ShumeikoYe\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m py_compile run_report.py src\stress_factors.py src\portfolio_commentary.py
    exited 0

## Validation and Acceptance

Acceptance requires `stress_report.json.historical_results[*]` to contain model-based attribution fields when `factor_beta_shock_oos` can be computed. `stress_commentary.txt` must state that historical attribution is model-based, not a causal realized decomposition, and must list top factor drivers for historical episodes. The focused tests above should pass.

## Idempotence and Recovery

The edits are additive. If factor history is unavailable, the helper must leave historical rows valid and avoid raising. Re-running `run_report.py` overwrites generated reports with the same deterministic schema.

## Artifacts and Notes

Focused validation passed:

    tests/test_factor_oos_explainability.py::test_factor_oos_beta_shock_explainability_basic PASSED
    tests/test_portfolio_commentary.py::test_write_portfolio_commentary_creates_file PASSED
    tests/test_portfolio_commentary.py::test_write_stress_commentary_from_stress_report PASSED

The first attempt to run `python -m pytest ...` failed because `python` is not in PATH in this desktop shell. The bundled Python path was used successfully.

## Interfaces and Dependencies

In `src/stress_factors.py`, define:

    enrich_historical_results_with_factor_attribution(
        historical_results: list[dict[str, Any]],
        factor_beta_shock_oos: dict[str, Any] | None,
        *,
        beta_source: str = "5y",
    ) -> list[dict[str, Any]]

The helper uses existing Python dictionaries and does not add external dependencies.
