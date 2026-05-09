# Risk Budgeting baseline construction v1

This ExecPlan is a living document. Maintain it per `PLANS.md`: update **Progress**, **Surprises & Discoveries**, **Decision Log**, and **Outcomes & Retrospective** as work proceeds.

## Purpose / Big Picture

Add two standalone benchmark constructors: **risk budget by asset-class bucket** (SLSQP on aggregated percentage variance contributions) and **risk budget by asset** (Spinu CCD with unequal budgets, SLSQP fallback). Both use the same eligible universe, monthly Ledoit–Wolf covariance with PSD repair as Risk Parity, and the merged ETF + stock universe taxonomy. They do not change main optimization, mandate gates, or stress pass/fail logic.

## Progress

- [x] (2026-05-09) Core implementation: `src/risk_budgeting.py`, `src/risk_budgeting_presets.py`, config, `portfolio_variants`, CLIs, tests, docs.

## Surprises & Discoveries

- (fill as needed)

## Decision Log

- **Decision:** Taxonomy for asset-class buckets uses `config/etf_universe.yml` then `config/stock_universe.yml` with the same merge rule as `load_ticker_asset_class_map`; sub-buckets (`credit`, `inflation_linked`, `real_assets`) derive from YAML row fields only.

## Outcomes & Retrospective

- (fill at milestone completion)

## Concrete Steps

From repository root:

    python run_risk_budget_by_asset_class.py
    python run_risk_budget_by_asset.py
    python -m pytest tests/test_risk_budgeting.py

## Validation and Acceptance

- Presets sum to 1.0; manual overrides validated; outputs under `risk budget by asset-class portfolio/` and `risk budget by asset portfolio/`; full variant report via `run_portfolio_report_for_weights` when baseline succeeds.
