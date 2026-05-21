# Test fixtures

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

## Portfolio X-Ray golden contract (`RM-949`)

- **File:** `portfolio_xray_golden_v2.json` — committed reference output for `build_portfolio_xray_v2`.
- **Regenerate** after intentional contract changes:

  ```bash
  python tests/portfolio_xray_golden_inputs.py
  python -m pytest tests/test_portfolio_xray_contract.py -q
  ```

- **Inputs:** `tests/portfolio_xray_golden_inputs.py`
- **Tests:** `tests/test_portfolio_xray_contract.py`
