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
- `config/client_profiles.yml` - client risk profiles.
- `assets.yml` - optional asset metadata.
- `src/optimization.py` - optimization logic.
- `src/config_schema.py` - config validation.
- `src/data_loader.py`, `src/data_yf.py`, `src/fx.py` - data and FX.
- `src/metrics_asset.py`, `src/metrics_portfolio.py` - metrics.
- `src/risk_contrib.py` - RC_vol diagnostics.
- `src/stress.py`, `src/stress_factors.py` - stress and factor diagnostics.
- `src/portfolio_dynamic.py` - NaN-safe portfolio returns.
- `src/pdf_reports.py`, `src/portfolio_commentary.py`, `src/snapshot.py` - reporting.

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
- `RC_vol` is diagnostic only, not an optimization constraint.
- Scenario stress is diagnostic; mandate MaxDD can prevent weight release.
- Default backtest mode is `dynamic_nan_safe`.
- Do not manually require weights in `config.yml`; optimization writes `portfolio_weights.yml` / `run_result.json`.

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
