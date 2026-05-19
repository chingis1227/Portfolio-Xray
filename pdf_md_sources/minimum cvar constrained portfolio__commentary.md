---
title: "Main Portfolio: Target Weights"
date: "Analysis results for the 10-year window as of 2026-04-30"
documentclass: article
geometry: "left=18mm, right=18mm, top=24mm, bottom=20mm, head=20pt, foot=20pt, footskip=40pt"
fontsize: 10pt
---

## Executive Summary

Main Portfolio was reviewed on the latest available reporting window. CAGR is 7.60%, annualized volatility is 7.40%, maximum drawdown is -13.90%, Sharpe is 0.726, Sortino is 1.206, and market sensitivity is 0.300. Stress diagnostics show: Passed with diagnostic warning; worst scenario loss is -13.04%.

## Key Metrics

```{=latex}
\begin{center}\begin{tabular}{@{}>{\centering\arraybackslash}m{0.30\textwidth}@{\hspace{0.45em}}>{\centering\arraybackslash}m{0.30\textwidth}@{\hspace{0.45em}}>{\centering\arraybackslash}m{0.30\textwidth}@{}} \KPIone{7.60\%}{CAGR} & \KPIone{7.40\%}{Volatility} & \KPIone{-13.90\%}{Max Drawdown}\\[0.55em] \KPIone{0.726}{Sharpe} & \KPIone{1.206}{Sortino} & \KPIone{0.300}{Market Sensitivity}\end{tabular}\end{center}
```

## What This Means

The portfolio profile should be read as a trade-off between return, realized drawdown, and market sensitivity. CAGR measures compound annual growth, volatility measures annualized variability, and maximum drawdown captures the largest peak-to-trough loss in the reporting window. Sharpe and Sortino summarize risk-adjusted return, while market sensitivity indicates how strongly the portfolio moves with the broad benchmark.

## Risk Structure

Stress status: Passed with diagnostic warning. Worst scenario loss: -13.04%. Flagged scenario: N/A; flagged test: N/A. These diagnostics are used to identify risk concentrations and scenario vulnerability; they do not by themselves replace the mandate checks.

## Scenario Analysis

| Scenario | PnL | Pass | Top RC Asset | Top 3 RC |
| --- | ---: | --- | --- | ---: |
| equity_shock | -6.07% | True | GLD | 83.15% |
| credit_shock | -0.33% | True | GLD | 80.21% |
| rates_shock | -9.17% | True | GLD | 77.57% |
| inflation_stagflation | -3.61% | True | GLD | 83.55% |
| liquidity_shock | -2.91% | True | GLD | 80.98% |
| recession_severe | -13.04% | True | GLD | 81.18% |

## Conclusion

This English PDF was generated from the current structured portfolio outputs. Use the metrics, stress status, and scenario table together: the headline return profile is only meaningful when read alongside drawdown resilience and scenario behavior.
