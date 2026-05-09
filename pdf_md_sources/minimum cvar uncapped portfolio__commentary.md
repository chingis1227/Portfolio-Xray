---
title: "Main Portfolio: Target Weights"
date: "Analysis results for the 10-year window as of 2026-05-08"
documentclass: article
geometry: "left=18mm, right=18mm, top=24mm, bottom=20mm, head=20pt, foot=20pt, footskip=40pt"
fontsize: 10pt
---

## Executive Summary

Main Portfolio was reviewed on the latest available reporting window. CAGR is 3.10%, annualized volatility is 5.10%, maximum drawdown is -15.50%, Sharpe is 0.190, Sortino is 0.260, and market sensitivity is 0.085. Stress diagnostics show: Passed with diagnostic warning; worst scenario loss is -11.68%.

## Key Metrics

```{=latex}
\begin{center}\begin{tabular}{@{}>{\centering\arraybackslash}m{0.30\textwidth}@{\hspace{0.45em}}>{\centering\arraybackslash}m{0.30\textwidth}@{\hspace{0.45em}}>{\centering\arraybackslash}m{0.30\textwidth}@{}} \KPIone{3.10\%}{CAGR} & \KPIone{5.10\%}{Volatility} & \KPIone{-15.50\%}{Max Drawdown}\\[0.55em] \KPIone{0.190}{Sharpe} & \KPIone{0.260}{Sortino} & \KPIone{0.085}{Market Sensitivity}\end{tabular}\end{center}
```

## What This Means

The portfolio profile should be read as a trade-off between return, realized drawdown, and market sensitivity. CAGR measures compound annual growth, volatility measures annualized variability, and maximum drawdown captures the largest peak-to-trough loss in the reporting window. Sharpe and Sortino summarize risk-adjusted return, while market sensitivity indicates how strongly the portfolio moves with the broad benchmark.

## Risk Structure

Stress status: Passed with diagnostic warning. Worst scenario loss: -11.68%. Flagged scenario: N/A; flagged test: N/A. These diagnostics are used to identify risk concentrations and scenario vulnerability; they do not by themselves replace the mandate checks.

## Scenario Analysis

| Scenario | PnL | Pass | Top RC Asset | Top 3 RC |
| --- | ---: | --- | --- | ---: |
| equity_shock | -1.71% | True | BND | 96.12% |
| credit_shock | -1.16% | True | BND | 97.01% |
| rates_shock | -11.68% | True | BND | 98.93% |
| inflation_stagflation | -4.86% | True | BND | 96.23% |
| liquidity_shock | -1.62% | True | BND | 96.36% |
| recession_severe | 0.74% | True | BND | 96.17% |

## Conclusion

This English PDF was generated from the current structured portfolio outputs. Use the metrics, stress status, and scenario table together: the headline return profile is only meaningful when read alongside drawdown resilience and scenario behavior.
