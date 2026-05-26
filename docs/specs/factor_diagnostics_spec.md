# Factor Diagnostics Specification

This document owns the detailed contract for factor diagnostic outputs. The detailed stress and factor scenario formulas remain in [stress_testing_spec.md](stress_testing_spec.md); metric estimators remain in [metrics_specification.md](metrics_specification.md).

## Scope

Factor diagnostics are diagnostic-only unless another canonical spec explicitly makes a field binding. They must not replace optimizer inputs, mandate gates, stress pass/fail logic, or weight release.

Portfolio X-Ray Block 2.3 (`block_2_3_factor_exposure`) is a product-facing adapter over these diagnostics. It must read existing `stress_report.json` fields and must not trigger OLS/HAC regressions, Kalman calculations, factor variance decomposition, or data loading. If `stress_report.json` is missing required fields, Block 2.3 reports `partial` or `unavailable` with warnings; the missing calculation is fixed upstream in stress report generation / `src/stress_factors.py`.

## Production And Extended Factor Registries

Production factor outputs use:

- `equity`
- `real_rates`
- `inflation`
- `credit`
- `usd`
- `commodity`
- `vix`
- `us_growth`

`commodity` is the production commodity factor.

Product-facing Block 2.3 names are `equity`, `real_rates`, `inflation`, `credit`, `USD`, `commodity`, `VIX_volatility`, and `us_growth`. The corresponding beta keys are `beta_eq`, `beta_rr`, `beta_inf`, `beta_credit`, `beta_usd`, `beta_cmd`, `beta_vix`, and `beta_us_growth`. Internal stress-layer names such as `usd` and `vix` are normalized at the adapter boundary and should not be exposed as product names.

Extended diagnostic and stress analytics may use production factors plus `oil`. `beta_oil` is deprecated and must not appear in new production beta, rolling stability, OOS, adjusted overlay, or base variance-decomposition outputs. Oil exposure is surfaced through `diagnostic_oil_beta` or stress-layer metrics and must be labeled diagnostic/stress-only.

## Regression Diagnostics

`stress_report.json` factor regression diagnostics include:

- `factor_regression_5y`
- `factor_regression_10y`
- `idiosyncratic_risk = 1 - r2`
- rolling beta stability diagnostics
- multicollinearity checks
- serial-correlation checks
- Breusch-Pagan heteroskedasticity checks
- HAC/Newey-West inference where implemented

These diagnostics use the same weekly OLS rows as the reported portfolio factor betas. They are non-binding.

## Kalman Betas

`stress_report.json.factor_betas_kalman` is a diagnostic-only current-regime estimate on the extended weekly factor registry.

Required behavior:

- Reported Kalman betas are capped at `abs(beta) <= 3.0`.
- Uncapped latest values are preserved in `latest_raw`.
- Divergence versus 5Y betas is flagged by sign difference, `abs_gap >= 0.25`, or `relative_gap >= 0.75`.
- Posterior state uncertainty is classified as low, moderate, or high at thresholds `0.15` and `0.35`.
- Oil Kalman exposure is surfaced through `diagnostic_oil_beta`.

Kalman betas must not replace raw OLS 5Y/10Y betas, optimizer inputs, mandate gates, or stress pass/fail logic.

## Factor Covariance Forecast Quality

`stress_report.json.factor_covariance.forecast_quality` is diagnostic-only and non-binding.

It compares a 260-week weekly factor covariance forecast with realized factor portfolio risk over the next 52 weekly rows, using 52-week non-overlapping steps and sample `ddof=1` covariance/volatility.

## Factor Variance Decomposition

`stress_report.json.factor_variance_decomposition` is diagnostic-only. It uses 5Y weekly base-factor OLS rows, excludes Oil from production decomposition, reports residual risk, preserves net and gross views, and exports `factor_variance_decomposition_5y.csv`.

See [stress_testing_spec.md](stress_testing_spec.md) for the full JSON and CSV contract.
