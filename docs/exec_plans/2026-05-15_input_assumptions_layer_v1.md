# Input and Assumptions Layer V1

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`,
`Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document follows `PLANS.md` from the repository root. A future contributor should be
able to continue this work from this file alone.

## Purpose / Big Picture

The first product layer must make the analysis base explicit before the system optimizes,
reports, or recommends anything. After this change, a user can distinguish between building
a policy portfolio from a ticker universe and analyzing an existing portfolio with supplied
weights. The system will also export a structured `input_assumptions` object so reports,
future UI surfaces, and comparison workflows can show the same assumptions instead of
reconstructing them ad hoc.

The observable result for this first increment is additive: existing optimization and report
commands continue to work, `config.yml.example` documents the input modes, and generated
`run_result.json` / `run_metadata.json` contain a clear input-and-assumptions summary.

## Progress

- [x] (2026-05-15 18:16+02:00) Reviewed `PLANS.md`, current config loading, client profiles, portfolio construction policy, feasibility constraints, data policy, report metadata, and product concept documents.
- [x] (2026-05-15 18:16+02:00) Identified the main current ambiguity: `weights` are already supported for fixed reports, but the policy workflow also treats final production weights as generated output.
- [x] (2026-05-15 18:35+02:00) Added canonical `docs/specs/input_assumptions_spec.md` and linked it from `SPEC.md`, `RULES.md`, `README.md`, `ARCHITECTURE.md`, `DATA.md`, `GLOSSARY.md`, `OUTPUTS.md`, and detailed specs.
- [x] (2026-05-15 18:35+02:00) Added config support for `analysis_mode` and `current_weights` without changing the default `optimize_from_universe` behavior.
- [x] (2026-05-15 18:35+02:00) Exported a structured `input_assumptions` summary in optimization `run_result.json` and report `run_metadata.json`.
- [x] (2026-05-15 18:35+02:00) Added focused tests for input-mode validation, current-weight mapping, and metadata summary output.
- [x] (2026-05-15 18:36+02:00) Ran focused and adjacent tests; all selected tests passed with isolated pytest temp directories.

## Surprises & Discoveries

- Observation: The product concept already allows "current weights when an existing portfolio is analyzed" and "no current weights when building from a universe", while `portfolio_construction_policy.md` says final production weights are not manually authored.
  Evidence: `PRODUCT.md` separates current weights from optimized target weights; `portfolio_construction_policy.md` section 10 says final weights come from optimization.
- Observation: `load_validated_config` already loads generated `portfolio_weights.yml` when `config.yml` has no `weights`, and `run_report.py` refuses to run without fixed weights.
  Evidence: `src/config.py::load_validated_config` merges `output_dir_final/portfolio_weights.yml`; `run_report.py::main` exits when `cfg.weights` is empty.
- Observation: `horizon_years` is validated and exported but is currently report/context only, not an optimizer input.
  Evidence: `PortfolioConfig.horizon_years` comment says report-only; optimization code does not use it for constraints or objective.
- Observation: The default pytest temp root in this environment can fail with `WinError 5` during cleanup.
  Evidence: Running `.venv\Scripts\python.exe -m pytest tests\test_config_weights_sync.py tests\test_input_assumptions.py -vv` errored while removing `C:\Users\ShumeikoYe\.cache\codex-pytest-temp`; rerunning with `--basetemp='.pytest_tmp_input_assumptions'` passed.

## Decision Log

- Decision: Keep `optimize_from_universe` as the default analysis mode.
  Rationale: This preserves the current main workflow where the user supplies tickers and the optimizer writes policy weights.
  Date/Author: 2026-05-15 / Codex
- Decision: Add `current_weights` for existing-portfolio analysis, but only map it to fixed report weights when `analysis_mode` is `analyze_current_weights`.
  Rationale: This separates user-supplied current weights from generated policy weights and avoids accidentally causing a post-optimization report to analyze stale current weights.
  Date/Author: 2026-05-15 / Codex
- Decision: Make `run_optimization.py` reject `analysis_mode: analyze_current_weights` with a clear error.
  Rationale: That mode is a fixed-weight diagnostic flow; optimizing in that mode would be ambiguous because current weights are not final policy weights.
  Date/Author: 2026-05-15 / Codex

## Outcomes & Retrospective

First increment completed. The repository now has an explicit Input and Assumptions Layer V1 with two supported modes: `optimize_from_universe` and `analyze_current_weights`. Existing optimization behavior stays the default. Existing-portfolio analysis can now use `current_weights` without merging stale generated `portfolio_weights.yml`. Runtime metadata exports a structured `input_assumptions` block for future UI and report surfaces. Remaining product work includes UI controls, transaction costs, horizon effects on optimizer policy, assumption sensitivity, and selection/no-trade logic.

## Context and Orientation

The current repository is a CLI/file-driven portfolio analytics system. `config.yml` defines tickers, investor currency, client profile, targets, constraints, output folders, and technical settings. `run_optimization.py` reads the config, builds data panels, optimizes policy weights, and writes `portfolio_weights.yml` plus `run_result.json`. `run_report.py` reads fixed weights, builds metrics and diagnostics, and writes `run_metadata.json`, snapshots, CSVs, stress reports, commentary, and report artifacts.

The phrase "policy portfolio" means the main portfolio generated by `run_optimization.py`. The phrase "current weights" means user-supplied weights for an existing portfolio that the user wants to diagnose. The phrase "fixed report weights" means any already-decided weights consumed by `run_report.py`, including generated policy weights, candidate weights, or current weights in an existing-portfolio analysis.

The key files for this plan are:

- `src/config_schema.py`, which defines `PortfolioConfig` and validates config fields.
- `src/config.py`, which loads raw YAML, applies client profiles, and optionally merges generated weights.
- `run_optimization.py`, the policy optimization entrypoint.
- `run_report.py`, the fixed-weight report entrypoint.
- `src/io_export.py`, which writes `run_metadata.json`.
- `docs/specs/portfolio_construction_policy.md`, which owns policy weight semantics.
- `docs/specs/feasibility_constraints_spec.md`, which owns weight cap formulas.
- `docs/specs/data_policy_spec.md`, which owns NaN and data-gap behavior.
- `PRODUCT.md` and `docs/DIAGNOSTIC_PRODUCT_CONCEPT.md`, which describe the target product layer but are not binding until promoted into specs.

## Plan of Work

First, add `docs/specs/input_assumptions_spec.md`. It will define the two supported V1 input modes, separate user inputs from system-resolved inputs and technical calculation settings, and document current gaps such as transaction costs and product UI controls.

Second, update `src/config_schema.py` and `src/config.py`. The schema will accept `analysis_mode` values `optimize_from_universe` and `analyze_current_weights`. It will accept `current_weights` as a mapping with the same ticker and non-negative validation as `weights`. In `analyze_current_weights` mode, `current_weights` will be used as `cfg.weights` when legacy `weights` is absent. In the default mode, generated `portfolio_weights.yml` loading keeps its current behavior.

Third, add a small helper module `src/input_assumptions.py` that builds a serializable summary from the validated config and runtime-resolved fields. This summary will be written into `run_result.json` and `run_metadata.json`.

Fourth, update docs that index detailed specs: `SPEC.md`, `docs/specs/README.md`, `README.md`, `ARCHITECTURE.md`, `GLOSSARY.md`, and `OUTPUTS.md` where needed. Keep the top-level docs compact and point to the detailed spec.

Fifth, add focused tests. Tests should prove that default optimization mode still loads generated weights, `analyze_current_weights` uses supplied current weights instead of stale generated weights, and `export_run_metadata` includes `input_assumptions`.

## Concrete Steps

Work from the repository root:

    C:\Users\ShumeikoYe\OneDrive\Desktop\CURSOR TULA DIAGNOSTICS

Use `apply_patch` for manual edits. After implementation, run:

    .venv\Scripts\python.exe -m pytest tests\test_config_weights_sync.py tests\test_input_assumptions.py -vv --basetemp='.pytest_tmp_input_assumptions'

The adjacent constructor/candidate regression suite was also run:

    .venv\Scripts\python.exe -m pytest tests\test_equal_weight_baselines.py tests\test_minimum_cvar_baseline.py tests\test_minimum_variance_baseline.py tests\test_maximum_diversification_baseline.py tests\test_risk_budgeting.py tests\test_risk_parity_baseline.py tests\test_robust_mean_variance.py -vv --basetemp='.pytest_tmp_input_assumptions_adjacent'

The first command passed with 7 tests. The adjacent command passed with 59 tests. Because the change is additive schema/metadata behavior plus docs, and no generated artifacts were intentionally refreshed, no CLI smoke was required for this increment. If generated artifact writing changes beyond metadata shape, run:

    python run_report.py --backtest-mode dynamic_nan_safe

## Validation and Acceptance

Acceptance for the first increment:

1. A config with no `analysis_mode` behaves exactly like the previous policy workflow: `run_report.py` can load generated `portfolio_weights.yml` when `config.yml` has no `weights`.
2. A config with `analysis_mode: analyze_current_weights` and `current_weights` validates and exposes those weights through `cfg.weights`.
3. In `analyze_current_weights` mode, stale generated `portfolio_weights.yml` is not merged over supplied `current_weights`.
4. `run_metadata.json` includes a top-level `input_assumptions` object that lists input mode, tickers, weight status, currency, benchmark, risk-free source, cash proxy, mandate targets, horizon role, return frequency, windows, backtest mode, and current implementation gaps.
5. `run_result.json` from optimization includes the same summary for the policy optimization path.

## Idempotence and Recovery

The changes are additive. Running validation repeatedly should not mutate source files except the existing profile-sync behavior in `load_validated_config`, which is already part of the project. If a test creates temporary config files, it should use pytest `tmp_path`. Generated outputs should not be committed unless the user explicitly asks for refreshed artifacts.

If the new mode causes ambiguity, revert only the new files and field additions from this plan; do not reset unrelated user changes.

## Artifacts and Notes

Important existing behavior:

    config.yml tickers -> run_optimization.py -> Main portfolio/portfolio_weights.yml
    run_report.py -> load_validated_config -> cfg.weights from portfolio_weights.yml

The new fixed-current-weight behavior should be:

    analysis_mode: analyze_current_weights
    current_weights: {VOO: 0.6, BND: 0.4}
    run_report.py -> cfg.weights == current_weights

## Interfaces and Dependencies

Add the following user-facing config fields:

    analysis_mode: optimize_from_universe | analyze_current_weights
    current_weights: {}

Add the following helper interface:

    src.input_assumptions.build_input_assumptions_summary(
        cfg,
        *,
        portfolio_weights=None,
        weights_source=None,
        cash_proxy_ticker=None,
        rf_source=None,
        local_benchmark_map=None,
        analysis_end=None,
        windows_months=None,
        returns_frequency=None,
        periods_per_year=None,
        run_context=None,
    ) -> dict

The helper must not fetch market data, mutate config, or depend on generated files. It only summarizes already-known inputs.
