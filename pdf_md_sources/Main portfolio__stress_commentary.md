---
title: "Main Portfolio: Stress Analysis"
date: "Analysis results for the 10-year window as of 2026-05-15"
documentclass: article
geometry: "left=18mm, right=18mm, top=24mm, bottom=20mm, head=20pt, foot=20pt, footskip=40pt"
fontsize: 10pt
---

## Executive Summary

Main Portfolio was reviewed on the latest available reporting window. CAGR is 5.50%, annualized volatility is 7.70%, maximum drawdown is -19.20%, Sharpe is 0.443, Sortino is 0.618, and market sensitivity is 0.123. Stress diagnostics show: Passed with diagnostic warning; worst scenario loss is -11.68%.

## Key Metrics

```{=latex}
\begin{center}\begin{tabular}{@{}>{\centering\arraybackslash}m{0.30\textwidth}@{\hspace{0.45em}}>{\centering\arraybackslash}m{0.30\textwidth}@{\hspace{0.45em}}>{\centering\arraybackslash}m{0.30\textwidth}@{}} \KPIone{5.50\%}{CAGR} & \KPIone{7.70\%}{Volatility} & \KPIone{-19.20\%}{Max Drawdown}\\[0.55em] \KPIone{0.443}{Sharpe} & \KPIone{0.618}{Sortino} & \KPIone{0.123}{Market Sensitivity}\end{tabular}\end{center}
```

## What This Means

The portfolio profile should be read as a trade-off between return, realized drawdown, and market sensitivity. CAGR measures compound annual growth, volatility measures annualized variability, and maximum drawdown captures the largest peak-to-trough loss in the reporting window. Sharpe and Sortino summarize risk-adjusted return, while market sensitivity indicates how strongly the portfolio moves with the broad benchmark.

## Risk Structure

Stress status: Passed with diagnostic warning. Worst scenario loss: -11.68%. Flagged scenario: N/A; flagged test: N/A. These diagnostics are used to identify risk concentrations and scenario vulnerability; they do not by themselves replace the mandate checks.

## Scenario Analysis

| Scenario | PnL | Pass | Top RC Asset | Top 3 RC |
| --- | ---: | --- | --- | ---: |
| equity_shock | -6.34% | True | SLV | 75.26% |
| credit_shock | 0.02% | True | TLT | 71.25% |
| rates_shock | -11.68% | True | TLT | 73.19% |
| inflation_stagflation | -6.30% | True | SLV | 75.21% |
| liquidity_shock | -2.75% | True | TLT | 69.74% |
| recession_severe | -8.51% | True | TLT | 69.83% |

## Conclusion

This English PDF was generated from the current structured portfolio outputs. Use the metrics, stress status, and scenario table together: the headline return profile is only meaningful when read alongside drawdown resilience and scenario behavior.
