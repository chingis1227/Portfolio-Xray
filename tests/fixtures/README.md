# Test fixtures

## Portfolio X-Ray golden contract (`RM-949`)

- **File:** `portfolio_xray_golden_v2.json` — committed reference output for `build_portfolio_xray_v2`.
- **Regenerate** after intentional contract changes:

  ```bash
  python tests/portfolio_xray_golden_inputs.py
  python -m pytest tests/test_portfolio_xray_contract.py -q
  ```

- **Inputs:** `tests/portfolio_xray_golden_inputs.py`
- **Tests:** `tests/test_portfolio_xray_contract.py`
