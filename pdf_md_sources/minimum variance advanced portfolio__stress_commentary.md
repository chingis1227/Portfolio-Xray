---
title: "Main Portfolio: Stress Analysis"
date: "Analysis results for the 10-year window as of 2026-04-30"
documentclass: article
geometry: "left=18mm, right=18mm, top=24mm, bottom=20mm, head=20pt, foot=20pt, footskip=40pt"
fontsize: 10pt
---

## Executive Summary

Main Portfolio was reviewed on the latest available reporting window. CAGR is 6.30%, annualized volatility is 8.50%, maximum drawdown is -19.60%, Sharpe is 0.495, Sortino is 0.762, and market sensitivity is 0.347. Stress diagnostics show: Passed with diagnostic warning; worst scenario loss is -12.76%.

## Key Metrics

```{=latex}
\begin{center}\begin{tabular}{@{}>{\centering\arraybackslash}m{0.30\textwidth}@{\hspace{0.45em}}>{\centering\arraybackslash}m{0.30\textwidth}@{\hspace{0.45em}}>{\centering\arraybackslash}m{0.30\textwidth}@{}} \KPIone{6.30\%}{CAGR} & \KPIone{8.50\%}{Volatility} & \KPIone{-19.60\%}{Max Drawdown}\\[0.55em] \KPIone{0.495}{Sharpe} & \KPIone{0.762}{Sortino} & \KPIone{0.347}{Market Sensitivity}\end{tabular}\end{center}
```

## What This Means

The portfolio profile should be read as a trade-off between return, realized drawdown, and market sensitivity. CAGR measures compound annual growth, volatility measures annualized variability, and maximum drawdown captures the largest peak-to-trough loss in the reporting window. Sharpe and Sortino summarize risk-adjusted return, while market sensitivity indicates how strongly the portfolio moves with the broad benchmark.

## Risk Structure

Stress status: Passed with diagnostic warning. Worst scenario loss: -12.76%. Flagged scenario: N/A; flagged test: N/A. These diagnostics are used to identify risk concentrations and scenario vulnerability; they do not by themselves replace the mandate checks.

## Scenario Analysis

| Scenario | PnL | Pass | Top RC Asset | Top 3 RC |
| --- | ---: | --- | --- | ---: |
| equity_shock | -9.11% | True | TLT | 60.05% |
| credit_shock | -1.76% | True | TLT | 58.37% |
| rates_shock | -12.76% | True | TLT | 65.77% |
| inflation_stagflation | -8.28% | True | TLT | 62.79% |
| liquidity_shock | -5.30% | True | TLT | 57.26% |
| recession_severe | -10.09% | True | TLT | 57.27% |

## Conclusion

This English PDF was generated from the current structured portfolio outputs. Use the metrics, stress status, and scenario table together: the headline return profile is only meaningful when read alongside drawdown resilience and scenario behavior.
