# Factor beta shrinkage overlay

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`,
`Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document follows `PLANS.md` from the repository root.

## Purpose / Big Picture

After this change, a user reading `stress_report.json` or `stress_commentary.txt` can see not only the raw 5Y and 10Y factor betas, but also a conservative stability-adjusted overlay. The overlay shows when unstable 5Y betas should be interpreted more cautiously, where 5Y and 10Y disagree strongly, and whether raw-vs-adjusted factor-model PnL changes materially in synthetic stress scenarios or historical explainability rows.

## Progress

- [x] (2026-04-29 14:10+02:00) Read `PLANS.md`, reviewed the current factor beta, stress, OOS explainability, and commentary paths in `src/stress_factors.py`, `src/stress.py`, `run_report.py`, and `run_optimization.py`.
- [x] (2026-04-29 14:25+02:00) Implemented shared adjusted-beta overlay helpers, divergence diagnostics, adjusted synthetic PnL overlay, adjusted OOS explainability, and raw-vs-adjusted material-difference signal.
- [x] (2026-04-29 14:35+02:00) Wired the overlay into both report and optimization stress-report paths and added commentary output.
- [x] (2026-04-29 14:45+02:00) Added focused tests and updated documentation.
- [x] (2026-04-29 14:55+02:00) Ran focused and adjacent factor-suite pytest commands; all targeted tests passed.

## Surprises & Discoveries

- Observation: The stress engine itself only needs raw 5Y betas for the primary contract, so the adjusted path could stay entirely additive at the reporting layer.
  Evidence: `src/stress.py` only consumes `portfolio_betas` to compute `pnl_by_factor_pct` and recession calibration; no optimizer or pass/fail wiring depends on adjusted fields.
- Observation: Historical explainability already had a clean enrichment point, so adjusted attribution could reuse the same logic with suffixed output fields instead of inventing a second historical row format.
  Evidence: `src/stress_factors.py` already centralized historical factor attribution in `enrich_historical_results_with_factor_attribution`.

## Decision Log

- Decision: Keep raw `scenario_results`, raw `factor_betas_*`, and raw historical attribution as the primary contract, and publish the adjusted path only in new additive fields.
  Rationale: The user requested shrinkage as diagnostics for sensitivity and stress interpretation, not as a replacement for the existing raw stress engine.
  Date/Author: 2026-04-29 / Codex
- Decision: Use a fixed severity-to-confidence map with no new config keys in v1.
  Rationale: The user asked for implementation, not a new tuning surface; fixed defaults make the overlay deterministic and testable.
  Date/Author: 2026-04-29 / Codex
- Decision: Define strong 5Y-vs-10Y divergence as sign mismatch or relative gap at least 1.0, and define material raw-vs-adjusted PnL change as relative delta at least 25% or absolute delta at least 1%.
  Rationale: These thresholds are conservative enough to catch visibly different interpretations without turning small numerical drift into noise.
  Date/Author: 2026-04-29 / Codex

## Outcomes & Retrospective

Implemented. `stress_report.json` now carries `factor_betas_adjusted`, `synthetic_factor_pnl_adjusted`, `factor_beta_shock_oos_adjusted`, suffixed adjusted historical attribution fields, and `raw_vs_adjusted_pnl_signal`. `stress_commentary.txt` now reports strong 5Y-vs-10Y divergence, reduced adjusted betas, and material raw-vs-adjusted model PnL differences. Focused regression coverage passed and the change stayed non-binding for optimizer and mandate gates.

## Context and Orientation

Factor betas, rolling beta stability, and OOS explainability live in `src/stress_factors.py`. Synthetic stress scenarios and historical episodes are built in `src/stress.py`. Both `run_report.py` and `run_optimization.py` assemble `stress_report.json` by computing raw factor betas, regressions, rolling stability, and then exporting the report. Human-readable stress commentary is generated in `src/portfolio_commentary.py`.

In this repository, a “beta overlay” means an additive diagnostic block that sits next to the existing raw outputs and never replaces them. “Adjusted beta” means a raw 5Y beta shrunk toward the 10Y anchor when stability diagnostics say the 5Y estimate is noisy. “Material raw-vs-adjusted PnL difference” means the factor-model interpretation changed enough that a PM should notice it, even though the primary stress engine remains unchanged.

## Plan of Work

Implement shared helpers in `src/stress_factors.py` for three behaviors. First, compute `factor_betas_adjusted` from raw 5Y betas, raw 10Y betas, and `factor_betas_stability`, including per-beta confidence, adjustment reasons, and 5Y-vs-10Y divergence diagnostics. Second, compute additive synthetic stress overlays and adjusted OOS episode explainability using the adjusted betas while preserving the raw stress-report fields. Third, compute a compact `raw_vs_adjusted_pnl_signal` summary that marks material differences for synthetic scenarios and historical explainability episodes.

Wire the shared overlay into both `run_report.py` and `run_optimization.py` after the existing raw `factor_beta_shock_oos` and primary historical enrichment are available. Persist the new top-level JSON blocks and replace `historical_results` only with rows that still contain the raw fields plus the new `_adjusted` suffixed fields.

Update `src/portfolio_commentary.py` to emit one short section summarizing strong divergence, reduced adjusted betas, and material raw-vs-adjusted PnL differences. Keep the tone diagnostic only and do not frame the overlay as an optimizer warning.

## Concrete Steps

From the repository root, run:

    C:\Users\ShumeikoYe\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m py_compile run_report.py run_optimization.py src\stress_factors.py src\portfolio_commentary.py

Expected result: command exits with no output.

Then run focused regression tests:

    C:\Users\ShumeikoYe\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest tests\test_factor_oos_explainability.py tests\test_factor_beta_adjusted_overlay.py tests\test_portfolio_commentary.py tests\test_stress_mandate_pass.py -vv

Expected result: all tests pass.

Then run adjacent factor-suite checks:

    C:\Users\ShumeikoYe\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest tests\test_factor_beta_stability.py tests\test_factor_matrix_builders.py -vv

Expected result: all tests pass.

## Validation and Acceptance

Acceptance is satisfied when `stress_report.json` preserves the raw factor fields and additionally contains `factor_betas_adjusted`, `synthetic_factor_pnl_adjusted`, `factor_beta_shock_oos_adjusted`, and `raw_vs_adjusted_pnl_signal`. The `historical_results` rows must still contain the raw 5Y attribution fields and also carry `_adjusted` suffixed attribution mirrors. `stress_commentary.txt` must mention the adjusted overlay section, strong 5Y-vs-10Y divergence when present, and any material raw-vs-adjusted PnL differences.

Test acceptance is satisfied by the focused pytest command covering OOS explainability, adjusted overlay logic, commentary rendering, and existing stress behavior, plus the adjacent factor-suite command proving no regression in rolling/stability analytics.

## Idempotence and Recovery

All code changes are additive and deterministic. Re-running the report or optimization entrypoints will recompute the same raw and adjusted diagnostics from the same inputs. If any adjusted overlay helper fails, the raw stress-report path still exists and can be inspected independently via the existing raw fields.

## Artifacts and Notes

Evidence from validation:

    tests/test_factor_oos_explainability.py ... PASSED
    tests/test_factor_beta_adjusted_overlay.py ... PASSED
    tests/test_portfolio_commentary.py ... PASSED
    tests/test_stress_mandate_pass.py ... PASSED
    tests/test_factor_beta_stability.py ... PASSED
    tests/test_factor_matrix_builders.py ... PASSED

Plan update note: this plan was written after implementation to capture the final design, validation commands, and output contract for the new adjusted-beta overlay so future contributors can reproduce or extend it without reconstructing the reasoning from commit history.

## Interfaces and Dependencies

In `src/stress_factors.py`, define helpers that produce the following stable interfaces:

    build_factor_beta_adjustment_overlay(
        factor_betas_5y: dict[str, Any] | None,
        factor_betas_10y: dict[str, Any] | None,
        factor_betas_stability: dict[str, Any] | None,
    ) -> dict[str, Any]

    build_synthetic_factor_pnl_adjusted_overlay(
        scenario_results: list[dict[str, Any]],
        raw_betas: dict[str, Any] | None,
        adjusted_betas: dict[str, Any] | None,
    ) -> dict[str, Any]

    build_raw_vs_adjusted_pnl_signal(
        synthetic_overlay: dict[str, Any] | None,
        factor_beta_shock_oos_raw: dict[str, Any] | None,
        factor_beta_shock_oos_adjusted: dict[str, Any] | None,
    ) -> dict[str, Any]

    build_factor_beta_diagnostic_overlay(
        *,
        weights: dict[str, float],
        tickers: list[str],
        scenario_results: list[dict[str, Any]],
        historical_results: list[dict[str, Any]],
        factor_betas_5y: dict[str, Any] | None,
        factor_betas_10y: dict[str, Any] | None,
        factor_betas_stability: dict[str, Any] | None,
        factor_beta_shock_oos_raw: dict[str, Any] | None = None,
        rolling_window_weeks: int = FACTOR_WEEKS_3Y,
    ) -> dict[str, Any]

Also expose:

    enrich_historical_results_with_adjusted_factor_attribution(
        historical_results: list[dict[str, Any]],
        factor_beta_shock_oos_adjusted: dict[str, Any] | None,
    ) -> list[dict[str, Any]]

These helpers must stay dependency-local to the existing factor analytics stack and must not introduce a new config surface, external service, or optimizer dependency.
