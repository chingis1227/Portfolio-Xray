---
title: "Main Portfolio: Executive Commentary"
date: "Analysis results for the 10-year window as of 2026-05-08"
documentclass: article
geometry: "left=18mm, right=18mm, top=24mm, bottom=20mm, head=20pt, foot=20pt, footskip=40pt"
fontsize: 10pt
---

## Executive Summary

Main Portfolio was reviewed on the latest available reporting window. CAGR is 5.50%, annualized volatility is 7.60%, maximum drawdown is -19.20%, Sharpe is 0.443, Sortino is 0.620, and market sensitivity is 0.107. Stress diagnostics show: Passed with diagnostic warning; worst scenario loss is -11.90%.

## Key Metrics

```{=latex}
\begin{center}\begin{tabular}{@{}>{\centering\arraybackslash}m{0.30\textwidth}@{\hspace{0.45em}}>{\centering\arraybackslash}m{0.30\textwidth}@{\hspace{0.45em}}>{\centering\arraybackslash}m{0.30\textwidth}@{}} \KPIone{5.50\%}{CAGR} & \KPIone{7.60\%}{Volatility} & \KPIone{-19.20\%}{Max Drawdown}\\[0.55em] \KPIone{0.443}{Sharpe} & \KPIone{0.620}{Sortino} & \KPIone{0.107}{Market Sensitivity}\end{tabular}\end{center}
```

## What This Means

The portfolio profile should be read as a trade-off between return, realized drawdown, and market sensitivity. CAGR measures compound annual growth, volatility measures annualized variability, and maximum drawdown captures the largest peak-to-trough loss in the reporting window. Sharpe and Sortino summarize risk-adjusted return, while market sensitivity indicates how strongly the portfolio moves with the broad benchmark.

## Risk Structure

Stress status: Passed with diagnostic warning. Worst scenario loss: -11.90%. Flagged scenario: N/A; flagged test: N/A. These diagnostics are used to identify risk concentrations and scenario vulnerability; they do not by themselves replace the mandate checks.

## Scenario Analysis

| Scenario | PnL | Pass | Top RC Asset | Top 3 RC |
| --- | ---: | --- | --- | ---: |
| equity_shock | -5.52% | True | SLV | 76.09% |
| credit_shock | 0.16% | True | TLT | 72.12% |
| rates_shock | -11.90% | True | TLT | 73.93% |
| inflation_stagflation | -5.92% | True | SLV | 75.63% |
| liquidity_shock | -2.30% | True | TLT | 71.06% |
| recession_severe | -7.64% | True | TLT | 71.09% |

## Conclusion

This English PDF was generated from the current structured portfolio outputs. Use the metrics, stress status, and scenario table together: the headline return profile is only meaningful when read alongside drawdown resilience and scenario behavior.
