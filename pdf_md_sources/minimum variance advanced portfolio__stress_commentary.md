---
title: "Main Portfolio: Stress Analysis"
date: "Analysis results for the 10-year window as of 2026-04-30"
documentclass: article
geometry: "left=18mm, right=18mm, top=24mm, bottom=20mm, head=20pt, foot=20pt, footskip=40pt"
fontsize: 10pt
---

## Executive Summary

Main Portfolio was reviewed on the latest available reporting window. CAGR is 8.80%, annualized volatility is 8.50%, maximum drawdown is -19.30%, Sharpe is 0.777, Sortino is 1.221, and market sensitivity is 0.467. Stress diagnostics show: Passed with diagnostic warning; worst scenario loss is -17.53%.

## Key Metrics

```{=latex}
\begin{center}\begin{tabular}{@{}>{\centering\arraybackslash}m{0.30\textwidth}@{\hspace{0.45em}}>{\centering\arraybackslash}m{0.30\textwidth}@{\hspace{0.45em}}>{\centering\arraybackslash}m{0.30\textwidth}@{}} \KPIone{8.80\%}{CAGR} & \KPIone{8.50\%}{Volatility} & \KPIone{-19.30\%}{Max Drawdown}\\[0.55em] \KPIone{0.777}{Sharpe} & \KPIone{1.221}{Sortino} & \KPIone{0.467}{Market Sensitivity}\end{tabular}\end{center}
```

## What This Means

The portfolio profile should be read as a trade-off between return, realized drawdown, and market sensitivity. CAGR measures compound annual growth, volatility measures annualized variability, and maximum drawdown captures the largest peak-to-trough loss in the reporting window. Sharpe and Sortino summarize risk-adjusted return, while market sensitivity indicates how strongly the portfolio moves with the broad benchmark.

## Risk Structure

Stress status: Passed with diagnostic warning. Worst scenario loss: -17.53%. Flagged scenario: N/A; flagged test: N/A. These diagnostics are used to identify risk concentrations and scenario vulnerability; they do not by themselves replace the mandate checks.

## Scenario Analysis

| Scenario | PnL | Pass | Top RC Asset | Top 3 RC |
| --- | ---: | --- | --- | ---: |
| equity_shock | -15.18% | True | QQQ | 63.93% |
| credit_shock | -3.34% | True | QQQ | 57.86% |
| rates_shock | -9.10% | True | QQQ | 50.53% |
| inflation_stagflation | -9.75% | True | QQQ | 56.23% |
| liquidity_shock | -9.15% | True | QQQ | 61.16% |
| recession_severe | -17.53% | True | QQQ | 61.06% |

## Conclusion

This English PDF was generated from the current structured portfolio outputs. Use the metrics, stress status, and scenario table together: the headline return profile is only meaningful when read alongside drawdown resilience and scenario behavior.
