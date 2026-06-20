# Robust Mean-Variance Specification

This document owns the detailed contract for Robust Mean-Variance benchmark portfolios and lambda calibration.

## Role

Robust Mean-Variance is a return-aware statistical benchmark. It is a comparison point and sanity check versus the policy optimizer and other benchmark portfolios. It is not a replacement for `run_optimization.py`.

## Inputs And Estimation

Robust MV estimates weights from a mean-variance optimum on statistically stabilized inputs:

- James-Stein expected returns
- Ledoit-Wolf or OAS covariance
- internal risk-aversion lambda on monthly portfolio variance

The objective is:

`min lambda * w' Sigma w - mu' w`

subject to `sum(w) = 1` and the relevant long-only or constrained bounds.

## Lambda Contract

Lambda is not a client-facing mandate dial.

`run_robust_mv_lambda_calibration.py` evaluates a lambda grid against IPS limits from `config.yml`, including volatility, mandate maximum drawdown, configured diagnostic synthetic stress alignment, and concentration caps where configured.

Baseline runners resolve lambda from:

- `analysis_robust_mv_lambda_calibration/selected_lambda.txt`
- `--robust-mv-lambda`

`analysis_robust_mv_lambda_calibration/` is generated local calibration output, not a source
fixture. Fresh checkouts do not need a tracked `selected_lambda.txt`; operators must run
`python run_robust_mv_lambda_calibration.py` before Robust MV baseline builders when no CLI lambda
override is supplied.

YAML `robust_mv_lambda` is not read by calibration or baseline CLIs. Tests may still set it programmatically where needed.

### Candidate factory disclosure (Block 4 Session 07)

`run_candidate_factory.py` does **not** invoke `run_robust_mv_lambda_calibration.py`. For `robust_mv_constrained` and `robust_mv_uncapped`, each factory step includes `robust_paths_disclosure` with `kind: robust_mv_lambda` (file presence, resolved λ, `lambda_ready_for_build`). Comparison rows mirror this under `construction_disclosure.robust_paths`. Operator playbook: [operational_runbook.md](../operational_runbook.md) (Robust suite prerequisites).

## Variants

Implemented scripts:

- `run_robust_mv_lambda_calibration.py`
- `run_robust_mean_variance_uncapped.py`
- `run_robust_mean_variance_constrained.py`

Metadata records the variant role through `robust_mv_variant_role` and `robust_mv_variant_summary`.

## Boundaries

Robust MV baseline scripts do not apply ProLiquidity or mandate overlays. Young ETF policy affects bounds on the constrained path only where the existing implementation supports it. The baseline reports are comparison artifacts.
