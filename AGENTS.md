---
description: 
alwaysApply: true
---

# AGENTS.md

## Project
Python portfolio optimization/reporting system. It builds optimized portfolio weights, runs portfolio analytics, stress diagnostics, robustness checks, and exports CSV/JSON/HTML/TXT/PDF-style report artifacts.

Main flow:
1. `python run_optimization.py`
2. `python run_report.py`

Weights are optimizer output, not manual user input. Manual post-optimization tilt is allowed only through View After Optimization.

## Stack
- Python
- pandas, numpy, scipy, scikit-learn
- yfinance, pandas-datareader
- PyYAML / ruamel.yaml
- matplotlib
- pytest

Install:
```bash
pip install -r requirements.txt
```

## Key Commands
Run tests:
```bash
python -m pytest
```

Run optimization:
```bash
python run_optimization.py [--no-cache] [--write-config] [--config PATH] [--profile NAME] [--no-report]
```

Run report:
```bash
python run_report.py [--no-cache] [--clear-cache] [--backtest-mode dynamic_nan_safe]
```

Run post-optimization tilt:
```bash
python run_view_after_optimization.py --asset VOO --delta 2
```

## ExecPlans
For new complex tasks, large changes, or refactors, follow `PLANS.md` before implementation.

- Read `PLANS.md` fully before authoring or changing an ExecPlan.
- Create or update checked-in ExecPlans under `docs/exec_plans/`.
- Keep ExecPlans as living documents: update `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` as work proceeds.
- Small, localized fixes do not need a separate ExecPlan unless the user asks for one.

## Done When

A task is considered done only when all applicable conditions are true:

- The requested behavior is implemented, removed, or intentionally left unchanged with a clear justification.
- The result is verifiable: the final response includes exact changed file paths, a concise description of what changed, and concrete proof via command output, test results, UI state, or report snippets (descriptions like "it works" are not sufficient).
- The change is contextualized: the previous behavior/state, the new behavior/state, and the reason the change matters are explicitly stated.
- Validation was performed using the narrowest reliable check (unit test, CLI command, script, or reproducible manual check); failures were fixed and rerun, or any unverified part is explicitly reported with the reason and blocker.
- No stale references remain to renamed or removed functions, configs, metrics, files, commands, outputs, or workflows.
- Documentation is updated if the change affects behavior, logic, formulas, configs, workflows, outputs, interfaces, or agent instructions, with explicit mention of what was updated and how.
- The relevant source-of-truth (specification, model, or design document) was checked before modifying logic, formulas, or data flow; any deviation is explicitly justified.
- Generated outputs are not treated as source unless the task explicitly targets generated artifacts.
- Any uncertainty, assumption, or unverified aspect is explicitly stated; no silent assumptions are allowed.

## Documentation Sync
Documentation sync is a blocking part of the definition of done for every meaningful code change.

Meaningful changes include architecture changes, new or removed modules, functions, metrics, data flow, configs, interfaces, optimization logic, reporting behavior, UI behavior, or shared helpers used by those areas.

Required documentation checks:
- Update `AGENTS.md` when behavior, rules, workflows, verification requirements, or agent instructions change.
- Update `README.md` when usage, setup, commands, project structure, outputs, or user-facing workflows change.
- Update `SPEC.md` when functionality, expected behavior, formulas, configs, interfaces, or acceptance criteria change.
- Update any affected component `.md` files that describe the changed code path, including specs under `docs/`.

Blocking rules:
- Do not consider a meaningful code change complete until all related documentation is updated.
- Do not proceed past implementation if documentation is known to be outdated or inconsistent with the code.
- Verify no stale references remain to deleted or renamed functions, metrics, configs, files, commands, outputs, or workflows.
- Keep documentation concise and aligned with the current implementation; do not add speculative behavior.
- In the final response, report the documentation files checked or changed and the stale-reference verification performed.

## UI / Design
For any web UI, dashboard, generated HTML report, or visual interface work, follow `DESIGN.md`.

Relevant surfaces:
- `config_ui/`
- `results_dashboard/`
- generated HTML in `src/snapshot.py`
- Plotly HTML in `src/stress_factors.py`

Keep `DESIGN.md` as the source of truth for tokens, typography, spacing, buttons, and dashboard styling.

## Important Files
- `config.yml` - active local config.
- `config.yml.example` - reference config.
- `config/etf_universe.yml` - curated ETF taxonomy source of truth; V1 validates/annotates config tickers but does not change optimizer membership or weights.
- `config/stock_universe.yml` - curated stock taxonomy source of truth for current S&P 500 constituents; V1 is CLI-only and does not change optimizer membership or weights.
- `config/client_profiles.yml` - client risk profiles.
- `assets.yml` - optional asset metadata.
- `src/optimization.py` - optimization logic.
- `src/config_schema.py` - config validation.
- `src/data_loader.py`, `src/data_yf.py`, `src/fx.py` - data and FX.
- `src/metrics_asset.py`, `src/metrics_portfolio.py` - metrics.
- `src/risk_contrib.py` - RC_vol diagnostics.
- `src/stress.py`, `src/stress_factors.py` - stress and factor diagnostics.
- `src/portfolio_dynamic.py` - NaN-safe portfolio returns.
- `src/pdf_reports.py`, `src/portfolio_commentary.py`, `src/snapshot.py` - reporting. Auto-generated `commentary.txt` and `stress_commentary.txt` are English-only (UTF-8).

## Source Of Truth
Before changing formulas or portfolio logic, check the relevant spec:
- `metrics_specification.md` - metric formulas, estimators, windows, FX rules.
- `PROJECT_RULES.md` - project-wide metric/data standards.
- `docs/portfolio_construction_policy.md` - optimizer policy.
- `docs/data_policy_nan_young_etfs.md` - NaN and young ETF handling.
- `docs/docs/stress_testing_spec.md` - stress testing.
- `docs/docs/feasibility_constraints_spec.md` - feasibility and weight limits.
- `docs/docs/view_after_optimization_spec.md` - allowed post-optimization tilt.
- `docs/production_workflow.md` - production statuses and blocking rules.
- `docs/etf_universe_spec.md` - ETF taxonomy schema, enums, duplicate/canonical policy, and diagnostics statuses.
- `docs/stock_universe_spec.md` - stock taxonomy schema, snapshot header requirements, and CLI workflow.

Do not invent formulas if a spec exists.

## Core Rules
- Use adjusted close prices.
- Convert FX before returns.
- Monthly returns use effective month-end.
- `analysis_end` is the last completed effective month-end before today.
- Use 36M / 60M / 120M windows unless the config/spec says otherwise.
- Use sample estimators with `ddof=1` for std/var/cov.
- Align series with inner joins for excess returns, beta, covariance, correlation, and RC_vol.
- Round only at final export/report stage, not during calculations.
- Factor regression diagnostics in `stress_report.json` include `idiosyncratic_risk = 1 - R²`, rolling beta stability diagnostics (`factor_betas_stability`), plus Breusch-Pagan heteroskedasticity checks on the same weekly OLS rows as reported betas.
- Production factor outputs use `equity`, `real_rates`, `inflation`, `credit`, `usd`, `commodity`, `vix`, and `us_growth`; `commodity` is the production сырьевой factor.
- Extended diagnostic/stress analytics use production factors plus `oil`. `beta_oil` is deprecated and removed from new production beta, rolling stability, OOS, adjusted overlay, and base variance-decomposition outputs. Oil exposure must be read from `diagnostic_oil_beta` or stress-layer metrics, and commentary must label Oil as `diagnostic_warning_only`.
- `factor_betas_kalman` in `stress_report.json` is diagnostic-only: weekly random-walk Kalman betas are capped at `|beta| <= 3.0`, keep uncapped latest values in `latest_raw`, flag Kalman-vs-5Y divergence, and classify state uncertainty. They must not replace raw OLS 5Y/10Y betas, optimizer inputs, mandate gates, or stress pass/fail logic.
- `macro_regime_diagnostics` in `stress_report.json` is diagnostic-only: method `macro_two_axis_v1` (see `src/stress_factors_macro.py` and `docs/docs/stress_testing_spec.md` §8.8.2) is a monthly two-axis macro classifier producing `growth_score`, `inflation_score`, and a **primary regime** (4 quadrants by sign: `goldilocks`, `reflation`, `stagflation`, `recession_disinflation`). Every scored month gets one of these four labels; uncertainty inside `±neutral_band` is reported separately as `transition_flag` plus `transition_reason ∈ {growth_axis_near_neutral, inflation_axis_near_neutral, both_axes_near_neutral}`. The legacy 5-bucket label (with `neutral_transition`) is preserved as `regime_legacy` / `regime_legacy_counts` for backward compat. Look-ahead protection is a 1-month publication lag. Indicator scoring defaults to `discrete` (rolling 10y z-score bucketed at ±0.5 to {−1, 0, +1}); the alternative `clipped_z` mode (signed clipped z, default clip ±2.0, rescaled to ±1.0) is exposed for diagnostics. The default neutral band is `0.20` and the default persistence smoothing is `2` months (regime change confirmed only when 2 consecutive labels agree); the unsmoothed series is preserved as `regime_unlagged_raw`. Indicators are loaded through a layered source resolver (`src/data_macro_sources.py`, FRED → Yahoo → official CSV → official API → keyed API → manual CSV); missing sources degrade `coverage_tier` (`full / extended / reduced / fred_baseline / insufficient`) and `confidence_level` without crashing the run. Per-regime monthly factor analytics (regression, covariance, RC) are gated by n_obs (`<12` insufficient_data, `12–23` low_confidence with linear shrinkage to `base_10y`, `24–59` usable, `60+` reliable). The payload also includes `regime_label_quality_check` (quality stats restricted to scored months — `warmup_months_excluded` and `rows_input_total` are reported separately — plus switching stability, historical sanity windows, metadata distributions, and caution flags). The block must not replace optimizer inputs, mandate gates, stress pass/fail logic, weight release, or raw 5Y/10Y beta outputs.
- Synthetic stress scenarios in `src/stress.py` still map only the first six factors into `shock_*` keys unless the stress spec is explicitly changed; `inflation_stagflation` includes `shock_inf = +0.005`, so `beta_inf` contributes directly to that scenario PnL.
- Portfolio PCA diagnostics in `stress_report.json.portfolio_pca` are diagnostic-only, use weekly adjusted-close returns for current positive-weight assets, and interpret covariance PCA as `risk_dominance` and correlation PCA as `structure`.
- `RC_vol` is diagnostic only, not an optimization constraint.
- Scenario stress is diagnostic; mandate MaxDD can prevent weight release.
- Default backtest mode is `dynamic_nan_safe`.
- Do not manually require weights in `config.yml`; optimization writes `portfolio_weights.yml` / `run_result.json`.
- ETF universe taxonomy is annotation-only in V1: `run_etf_universe.py` validates/lists/exports `config/etf_universe.yml`, and optimization/report runs may write `etf_universe_validation.json`, but taxonomy warnings do not alter portfolio composition or weights.
- Stock universe taxonomy is annotation-only in V1: `run_stock_universe.py` validates/lists/exports `config/stock_universe.yml` and can check an explicit stock config, but it is not wired into optimization/report and does not alter portfolio composition or weights.

## Verification Loop
After any meaningful code change, run tests before considering the task complete.

Meaningful changes include edits to optimization, metrics, config validation, data loading/alignment, NaN handling, stress diagnostics, reporting, generated HTML/UI, CLI flows, or any shared helper used by those areas. Documentation-only changes and tiny comments do not require tests unless they alter executable examples or commands.

Use the narrowest reliable test first, then broaden when risk warrants it:
- For a localized fix, run the directly relevant test file or test case.
- For changes touching portfolio math, optimizer behavior, data alignment, config schema, stress logic, or report exports, run the related focused tests and then `python -m pytest` when feasible.
- For web UI/dashboard/report HTML changes, also run or inspect the affected surface enough to verify it renders without obvious layout or runtime errors.

If tests fail after a change, diagnose the failure, fix the root cause, and rerun the failing tests. Repeat this fix-and-test loop until the relevant tests pass. Do not leave known failing tests unaddressed unless the failure is unrelated to the change, blocked by missing external data/network/service access, or explicitly accepted by the user. In the final response, report what was run and whether anything remains unverified.

## Generated Outputs
Do not treat these as source unless the task is about generated results:
- `cache/`
- `output/`
- `results_csv/`
- `Main portfolio/`
- `equal-weight portfolio/`
- `risk parity portfolio/`
- `portfolio_weights.yml`
- `__pycache__/`
- `.pytest_cache/`

## Editing Guidance
Keep changes scoped. Prefer existing helpers in `src/` over new parallel implementations. Add/update focused tests when changing optimization, metrics, config validation, data alignment, NaN handling, stress, or report outputs.
