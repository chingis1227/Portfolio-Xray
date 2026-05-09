---
title: "Main Portfolio: Stress Analysis"
date: "Analysis results for the 10-year window as of 2026-05-08"
documentclass: article
geometry: "left=18mm, right=18mm, top=24mm, bottom=20mm, head=20pt, foot=20pt, footskip=40pt"
fontsize: 10pt
---

## Executive Summary

Main Portfolio was reviewed on the latest available reporting window. CAGR is 21.90%, annualized volatility is 22.30%, maximum drawdown is -35.10%, Sharpe is 0.901, Sortino is 1.278, and market sensitivity is 1.161. Stress diagnostics show: One risk area requires attention; worst scenario loss is -61.57%.

## Key Metrics

```{=latex}
\begin{center}\begin{tabular}{@{}>{\centering\arraybackslash}m{0.30\textwidth}@{\hspace{0.45em}}>{\centering\arraybackslash}m{0.30\textwidth}@{\hspace{0.45em}}>{\centering\arraybackslash}m{0.30\textwidth}@{}} \KPIone{21.90\%}{CAGR} & \KPIone{22.30\%}{Volatility} & \KPIone{-35.10\%}{Max Drawdown}\\[0.55em] \KPIone{0.901}{Sharpe} & \KPIone{1.278}{Sortino} & \KPIone{1.161}{Market Sensitivity}\end{tabular}\end{center}
```

## What This Means

The portfolio profile should be read as a trade-off between return, realized drawdown, and market sensitivity. CAGR measures compound annual growth, volatility measures annualized variability, and maximum drawdown captures the largest peak-to-trough loss in the reporting window. Sharpe and Sortino summarize risk-adjusted return, while market sensitivity indicates how strongly the portfolio moves with the broad benchmark.

## Risk Structure

Stress status: One risk area requires attention. Worst scenario loss: -61.57%. Flagged scenario: equity_shock; flagged test: Loss. These diagnostics are used to identify risk concentrations and scenario vulnerability; they do not by themselves replace the mandate checks.

## Scenario Analysis

| Scenario | PnL | Pass | Top RC Asset | Top 3 RC |
| --- | ---: | --- | --- | ---: |
| equity_shock | -55.71% | False | QQQ | 100.00% |
| credit_shock | -9.09% | True | QQQ | 100.00% |
| rates_shock | 3.93% | True | QQQ | 100.00% |
| inflation_stagflation | -25.56% | False | QQQ | 100.00% |
| liquidity_shock | -31.19% | False | QQQ | 100.00% |
| recession_severe | -61.57% | False | QQQ | 100.00% |

## Conclusion

This English PDF was generated from the current structured portfolio outputs. Use the metrics, stress status, and scenario table together: the headline return profile is only meaningful when read alongside drawdown resilience and scenario behavior.
