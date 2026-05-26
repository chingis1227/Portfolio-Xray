# Test fixtures

## Core MVP portfolio YAML (`Input Layer MVP Session 04`)

- **Directory:** `mvp_portfolios/`
- **Files:**
  - `minimal_usd_no_cash.yml` — eight-ticker USD demo weights, no explicit bank cash
  - `minimal_usd_with_cash.yml` — same universe plus `Cash USD` holding (10% cash)
  - `demo_usd_asset_allocation_with_cash_5pct.yml` — `config.yml` tickers rescaled ×0.95 plus 5% `Cash USD` (Block 2.1)
- **Tests:** `tests/test_mvp_portfolio_fixtures.py`, `tests/test_mvp_portfolio_review_materialization.py`
- **Offline helpers:** `tests/mvp_offline_fixtures.py` (`validate_mvp_fixture`, `build_offline_run_metadata`)

```bash
python -m pytest tests/test_mvp_portfolio_fixtures.py tests/test_mvp_portfolio_review_materialization.py -q
```

## Optimization Engine golden contracts (`RM-1001`)

- **Files:**
  - `legacy_policy_optimizer_run_metadata_golden_v1.json` — `legacy_policy_optimizer_run_metadata_v1`
  - `candidate_optimizer_run_metadata_golden_v1.json` — `candidate_optimizer_run_metadata_v1`
  - `optimization_comparison_block5_golden_v1.json` — comparison row Block 5 disclosure slice
- **Regenerate** after intentional Block 5 disclosure contract changes:

  ```bash
  python tests/optimization_engine_golden_inputs.py
  python -m pytest tests/test_optimization_engine_contract.py -q
  ```

- **Inputs:** `tests/optimization_engine_golden_inputs.py`
- **Tests:** `tests/test_optimization_engine_contract.py`

## Full-menu optimizer fair-comparison golden (`RM-1023`)

- **File:** `optimization_comparison_full_menu_fair_ready_golden_v1.json` — sorted
  `fair_ready_optimizer_ids` after offline `default_v1` optimizer seed with builder metadata.
- **Regenerate** (also via `python tests/optimization_engine_golden_inputs.py`):

  ```bash
  python -m pytest tests/test_optimizer_fair_comparison_full_menu.py -q
  ```

- **Inputs:** `tests/optimizer_fair_comparison_fixtures.py`
- **Tests:** `tests/test_optimizer_fair_comparison_full_menu.py`

## Portfolio X-Ray golden contract (`RM-949`)

- **File:** `portfolio_xray_golden_v2.json` — committed reference output for `build_portfolio_xray_v2`.
- **Regenerate** after intentional contract changes:

  ```bash
  python tests/portfolio_xray_golden_inputs.py
  python -m pytest tests/test_portfolio_xray_contract.py -q
  ```

- **Inputs:** `tests/portfolio_xray_golden_inputs.py`
- **Tests:** `tests/test_portfolio_xray_contract.py`
