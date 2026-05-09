---
title: "Main Portfolio: Executive Commentary"
date: "Analysis results for the 10-year window as of 2026-04-30"
documentclass: article
geometry: "left=18mm, right=18mm, top=24mm, bottom=20mm, head=20pt, foot=20pt, footskip=40pt"
fontsize: 10pt
---

## Executive Summary

Main Portfolio was reviewed on the latest available reporting window. CAGR is 2.20%, annualized volatility is 4.90%, maximum drawdown is -14.10%, Sharpe is 0.015, Sortino is 0.020, and market sensitivity is 0.161. Stress diagnostics show: Passed with diagnostic warning; worst scenario loss is -12.14%.

## Key Metrics

```{=latex}
\begin{center}\begin{tabular}{@{}>{\centering\arraybackslash}m{0.30\textwidth}@{\hspace{0.45em}}>{\centering\arraybackslash}m{0.30\textwidth}@{\hspace{0.45em}}>{\centering\arraybackslash}m{0.30\textwidth}@{}} \KPIone{2.20\%}{CAGR} & \KPIone{4.90\%}{Volatility} & \KPIone{-14.10\%}{Max Drawdown}\\[0.55em] \KPIone{0.015}{Sharpe} & \KPIone{0.020}{Sortino} & \KPIone{0.161}{Market Sensitivity}\end{tabular}\end{center}
```

## What This Means

The portfolio profile should be read as a trade-off between return, realized drawdown, and market sensitivity. CAGR measures compound annual growth, volatility measures annualized variability, and maximum drawdown captures the largest peak-to-trough loss in the reporting window. Sharpe and Sortino summarize risk-adjusted return, while market sensitivity indicates how strongly the portfolio moves with the broad benchmark.

## Risk Structure

Stress status: Passed with diagnostic warning. Worst scenario loss: -12.14%. Flagged scenario: N/A; flagged test: N/A. These diagnostics are used to identify risk concentrations and scenario vulnerability; they do not by themselves replace the mandate checks.

## Scenario Analysis

| Scenario | PnL | Pass | Top RC Asset | Top 3 RC |
| --- | ---: | --- | --- | ---: |
| equity_shock | -0.73% | True | SCHP | 100.00% |
| credit_shock | -0.21% | True | SCHP | 100.00% |
| rates_shock | -12.14% | True | BND | 100.00% |
| inflation_stagflation | -4.54% | True | SCHP | 100.00% |
| liquidity_shock | -0.48% | True | SCHP | 100.00% |
| recession_severe | 2.41% | True | SCHP | 100.00% |

## Conclusion

This English PDF was generated from the current structured portfolio outputs. Use the metrics, stress status, and scenario table together: the headline return profile is only meaningful when read alongside drawdown resilience and scenario behavior.
