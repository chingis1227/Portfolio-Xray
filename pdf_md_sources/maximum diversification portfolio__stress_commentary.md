---
title: "Main Portfolio: Stress Analysis"
date: "Analysis results for the 10-year window as of 2026-04-30"
documentclass: article
geometry: "left=18mm, right=18mm, top=24mm, bottom=20mm, head=20pt, foot=20pt, footskip=40pt"
fontsize: 10pt
---

## Executive Summary

Main Portfolio was reviewed on the latest available reporting window. CAGR is 11.20%, annualized volatility is 10.70%, maximum drawdown is -20.70%, Sharpe is 0.842, Sortino is 1.408, and market sensitivity is 0.504. Stress diagnostics show: One risk area requires attention; worst scenario loss is -23.90%.

## Key Metrics

```{=latex}
\begin{center}\begin{tabular}{@{}>{\centering\arraybackslash}m{0.30\textwidth}@{\hspace{0.45em}}>{\centering\arraybackslash}m{0.30\textwidth}@{\hspace{0.45em}}>{\centering\arraybackslash}m{0.30\textwidth}@{}} \KPIone{11.20\%}{CAGR} & \KPIone{10.70\%}{Volatility} & \KPIone{-20.70\%}{Max Drawdown}\\[0.55em] \KPIone{0.842}{Sharpe} & \KPIone{1.408}{Sortino} & \KPIone{0.504}{Market Sensitivity}\end{tabular}\end{center}
```

## What This Means

The portfolio profile should be read as a trade-off between return, realized drawdown, and market sensitivity. CAGR measures compound annual growth, volatility measures annualized variability, and maximum drawdown captures the largest peak-to-trough loss in the reporting window. Sharpe and Sortino summarize risk-adjusted return, while market sensitivity indicates how strongly the portfolio moves with the broad benchmark.

## Risk Structure

Stress status: One risk area requires attention. Worst scenario loss: -23.90%. Flagged scenario: recession_severe; flagged test: Loss. These diagnostics are used to identify risk concentrations and scenario vulnerability; they do not by themselves replace the mandate checks.

## Scenario Analysis

| Scenario | PnL | Pass | Top RC Asset | Top 3 RC |
| --- | ---: | --- | --- | ---: |
| equity_shock | -16.26% | True | GLD | 74.51% |
| credit_shock | -2.76% | True | SCHD | 69.22% |
| rates_shock | -9.69% | True | GLD | 69.88% |
| inflation_stagflation | -9.07% | True | GLD | 70.49% |
| liquidity_shock | -9.18% | True | SCHD | 71.57% |
| recession_severe | -23.90% | False | SCHD | 71.94% |

## Conclusion

This English PDF was generated from the current structured portfolio outputs. Use the metrics, stress status, and scenario table together: the headline return profile is only meaningful when read alongside drawdown resilience and scenario behavior.
