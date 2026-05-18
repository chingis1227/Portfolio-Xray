---
title: "Main Portfolio: Stress Analysis"
date: "Analysis results for the 10-year window as of 2026-05-15"
documentclass: article
geometry: "left=18mm, right=18mm, top=24mm, bottom=20mm, head=20pt, foot=20pt, footskip=40pt"
fontsize: 10pt
---

## Executive Summary

Main Portfolio was reviewed on the latest available reporting window. CAGR is 8.40%, annualized volatility is 8.60%, maximum drawdown is -20.50%, Sharpe is 0.724, Sortino is 1.018, and market sensitivity is 0.304. Stress diagnostics show: One risk area requires attention; worst scenario loss is -13.86%.

## Key Metrics

```{=latex}
\begin{center}\begin{tabular}{@{}>{\centering\arraybackslash}m{0.30\textwidth}@{\hspace{0.45em}}>{\centering\arraybackslash}m{0.30\textwidth}@{\hspace{0.45em}}>{\centering\arraybackslash}m{0.30\textwidth}@{}} \KPIone{8.40\%}{CAGR} & \KPIone{8.60\%}{Volatility} & \KPIone{-20.50\%}{Max Drawdown}\\[0.55em] \KPIone{0.724}{Sharpe} & \KPIone{1.018}{Sortino} & \KPIone{0.304}{Market Sensitivity}\end{tabular}\end{center}
```

## What This Means

The portfolio profile should be read as a trade-off between return, realized drawdown, and market sensitivity. CAGR measures compound annual growth, volatility measures annualized variability, and maximum drawdown captures the largest peak-to-trough loss in the reporting window. Sharpe and Sortino summarize risk-adjusted return, while market sensitivity indicates how strongly the portfolio moves with the broad benchmark.

## Risk Structure

Stress status: One risk area requires attention. Worst scenario loss: -13.86%. Flagged scenario: 2022; flagged test: Historical. These diagnostics are used to identify risk concentrations and scenario vulnerability; they do not by themselves replace the mandate checks.

## Scenario Analysis

| Scenario | PnL | Pass | Top RC Asset | Top 3 RC |
| --- | ---: | --- | --- | ---: |
| equity_shock | -10.93% | True | SCHD | 65.22% |
| credit_shock | -3.09% | True | SCHD | 67.18% |
| rates_shock | -12.11% | True | TLT | 67.78% |
| inflation_stagflation | -8.20% | True | SCHD | 63.63% |
| liquidity_shock | -7.10% | True | SCHD | 67.31% |
| recession_severe | -13.86% | True | SCHD | 66.39% |

## Conclusion

This English PDF was generated from the current structured portfolio outputs. Use the metrics, stress status, and scenario table together: the headline return profile is only meaningful when read alongside drawdown resilience and scenario behavior.
