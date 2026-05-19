---
title: "Main Portfolio: Executive Commentary"
date: "Analysis results for the 10-year window as of 2026-04-30"
documentclass: article
geometry: "left=18mm, right=18mm, top=24mm, bottom=20mm, head=20pt, foot=20pt, footskip=40pt"
fontsize: 10pt
---

## Executive Summary

Main Portfolio was reviewed on the latest available reporting window. CAGR is 18.70%, annualized volatility is 13.50%, maximum drawdown is -24.00%, Sharpe is 1.18, Sortino is 2.11, and market sensitivity is 0.745. Stress diagnostics show: One risk area requires attention; worst scenario loss is -52.43%.

## Key Metrics

```{=latex}
\begin{center}\begin{tabular}{@{}>{\centering\arraybackslash}m{0.30\textwidth}@{\hspace{0.45em}}>{\centering\arraybackslash}m{0.30\textwidth}@{\hspace{0.45em}}>{\centering\arraybackslash}m{0.30\textwidth}@{}} \KPIone{18.70\%}{CAGR} & \KPIone{13.50\%}{Volatility} & \KPIone{-24.00\%}{Max Drawdown}\\[0.55em] \KPIone{1.180}{Sharpe} & \KPIone{2.110}{Sortino} & \KPIone{0.745}{Market Sensitivity}\end{tabular}\end{center}
```

## What This Means

The portfolio profile should be read as a trade-off between return, realized drawdown, and market sensitivity. CAGR measures compound annual growth, volatility measures annualized variability, and maximum drawdown captures the largest peak-to-trough loss in the reporting window. Sharpe and Sortino summarize risk-adjusted return, while market sensitivity indicates how strongly the portfolio moves with the broad benchmark.

## Risk Structure

Stress status: One risk area requires attention. Worst scenario loss: -52.43%. Flagged scenario: equity_shock; flagged test: Loss. These diagnostics are used to identify risk concentrations and scenario vulnerability; they do not by themselves replace the mandate checks.

## Scenario Analysis

| Scenario | PnL | Pass | Top RC Asset | Top 3 RC |
| --- | ---: | --- | --- | ---: |
| equity_shock | -37.79% | False | QQQ | 100.00% |
| credit_shock | -1.38% | True | QQQ | 100.00% |
| rates_shock | 1.07% | True | QQQ | 100.00% |
| inflation_stagflation | -14.89% | True | QQQ | 100.00% |
| liquidity_shock | -17.57% | True | QQQ | 100.00% |
| recession_severe | -52.43% | False | QQQ | 100.00% |

## Conclusion

This English PDF was generated from the current structured portfolio outputs. Use the metrics, stress status, and scenario table together: the headline return profile is only meaningful when read alongside drawdown resilience and scenario behavior.
