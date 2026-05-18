---
title: "Main Portfolio: Executive Commentary"
date: "Analysis results for the 10-year window as of 2026-05-15"
documentclass: article
geometry: "left=18mm, right=18mm, top=24mm, bottom=20mm, head=20pt, foot=20pt, footskip=40pt"
fontsize: 10pt
---

## Executive Summary

Main Portfolio was reviewed on the latest available reporting window. CAGR is 5.90%, annualized volatility is 6.40%, maximum drawdown is -18.00%, Sharpe is 0.571, Sortino is 0.796, and market sensitivity is 0.212. Stress diagnostics show: Passed with diagnostic warning; worst scenario loss is -11.22%.

## Key Metrics

```{=latex}
\begin{center}\begin{tabular}{@{}>{\centering\arraybackslash}m{0.30\textwidth}@{\hspace{0.45em}}>{\centering\arraybackslash}m{0.30\textwidth}@{\hspace{0.45em}}>{\centering\arraybackslash}m{0.30\textwidth}@{}} \KPIone{5.90\%}{CAGR} & \KPIone{6.40\%}{Volatility} & \KPIone{-18.00\%}{Max Drawdown}\\[0.55em] \KPIone{0.571}{Sharpe} & \KPIone{0.796}{Sortino} & \KPIone{0.212}{Market Sensitivity}\end{tabular}\end{center}
```

## What This Means

The portfolio profile should be read as a trade-off between return, realized drawdown, and market sensitivity. CAGR measures compound annual growth, volatility measures annualized variability, and maximum drawdown captures the largest peak-to-trough loss in the reporting window. Sharpe and Sortino summarize risk-adjusted return, while market sensitivity indicates how strongly the portfolio moves with the broad benchmark.

## Risk Structure

Stress status: Passed with diagnostic warning. Worst scenario loss: -11.22%. Flagged scenario: N/A; flagged test: N/A. These diagnostics are used to identify risk concentrations and scenario vulnerability; they do not by themselves replace the mandate checks.

## Scenario Analysis

| Scenario | PnL | Pass | Top RC Asset | Top 3 RC |
| --- | ---: | --- | --- | ---: |
| equity_shock | -8.14% | True | GLD | 48.04% |
| credit_shock | -2.10% | True | SCHP | 51.64% |
| rates_shock | -11.22% | True | SCHP | 69.58% |
| inflation_stagflation | -7.50% | True | SCHP | 55.84% |
| liquidity_shock | -5.13% | True | SCHD | 46.68% |
| recession_severe | -7.74% | True | SCHP | 46.83% |

## Conclusion

This English PDF was generated from the current structured portfolio outputs. Use the metrics, stress status, and scenario table together: the headline return profile is only meaningful when read alongside drawdown resilience and scenario behavior.
