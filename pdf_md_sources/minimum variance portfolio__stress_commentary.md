---
title: "Main Portfolio: Stress Analysis"
date: "Analysis results for the 10-year window as of 2026-04-30"
documentclass: article
geometry: "left=18mm, right=18mm, top=24mm, bottom=20mm, head=20pt, foot=20pt, footskip=40pt"
fontsize: 10pt
---

## Executive Summary

Main Portfolio was reviewed on the latest available reporting window. CAGR is 6.40%, annualized volatility is 7.20%, maximum drawdown is -16.00%, Sharpe is 0.580, Sortino is 0.907, and market sensitivity is 0.305. Stress diagnostics show: Passed with diagnostic warning; worst scenario loss is -11.34%.

## Key Metrics

```{=latex}
\begin{center}\begin{tabular}{@{}>{\centering\arraybackslash}m{0.30\textwidth}@{\hspace{0.45em}}>{\centering\arraybackslash}m{0.30\textwidth}@{\hspace{0.45em}}>{\centering\arraybackslash}m{0.30\textwidth}@{}} \KPIone{6.40\%}{CAGR} & \KPIone{7.20\%}{Volatility} & \KPIone{-16.00\%}{Max Drawdown}\\[0.55em] \KPIone{0.580}{Sharpe} & \KPIone{0.907}{Sortino} & \KPIone{0.305}{Market Sensitivity}\end{tabular}\end{center}
```

## What This Means

The portfolio profile should be read as a trade-off between return, realized drawdown, and market sensitivity. CAGR measures compound annual growth, volatility measures annualized variability, and maximum drawdown captures the largest peak-to-trough loss in the reporting window. Sharpe and Sortino summarize risk-adjusted return, while market sensitivity indicates how strongly the portfolio moves with the broad benchmark.

## Risk Structure

Stress status: Passed with diagnostic warning. Worst scenario loss: -11.34%. Flagged scenario: N/A; flagged test: N/A. These diagnostics are used to identify risk concentrations and scenario vulnerability; they do not by themselves replace the mandate checks.

## Scenario Analysis

| Scenario | PnL | Pass | Top RC Asset | Top 3 RC |
| --- | ---: | --- | --- | ---: |
| equity_shock | -6.10% | True | GLD | 66.99% |
| credit_shock | -1.52% | True | GLD | 64.27% |
| rates_shock | -11.34% | True | GLD | 60.71% |
| inflation_stagflation | -5.60% | True | GLD | 66.90% |
| liquidity_shock | -3.81% | True | SCHD | 66.26% |
| recession_severe | -8.64% | True | SCHD | 66.22% |

## Conclusion

This English PDF was generated from the current structured portfolio outputs. Use the metrics, stress status, and scenario table together: the headline return profile is only meaningful when read alongside drawdown resilience and scenario behavior.
