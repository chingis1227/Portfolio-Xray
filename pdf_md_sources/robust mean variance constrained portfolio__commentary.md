---
title: "Main Portfolio: Executive Commentary"
date: "Analysis results for the 10-year window as of 2026-05-08"
documentclass: article
geometry: "left=18mm, right=18mm, top=24mm, bottom=20mm, head=20pt, foot=20pt, footskip=40pt"
fontsize: 10pt
---

## Executive Summary

Main Portfolio was reviewed on the latest available reporting window. CAGR is 17.70%, annualized volatility is 16.20%, maximum drawdown is -26.90%, Sharpe is 0.953, Sortino is 1.331, and market sensitivity is 0.726. Stress diagnostics show: One risk area requires attention; worst scenario loss is -49.87%.

## Key Metrics

```{=latex}
\begin{center}\begin{tabular}{@{}>{\centering\arraybackslash}m{0.30\textwidth}@{\hspace{0.45em}}>{\centering\arraybackslash}m{0.30\textwidth}@{\hspace{0.45em}}>{\centering\arraybackslash}m{0.30\textwidth}@{}} \KPIone{17.70\%}{CAGR} & \KPIone{16.20\%}{Volatility} & \KPIone{-26.90\%}{Max Drawdown}\\[0.55em] \KPIone{0.953}{Sharpe} & \KPIone{1.331}{Sortino} & \KPIone{0.726}{Market Sensitivity}\end{tabular}\end{center}
```

## What This Means

The portfolio profile should be read as a trade-off between return, realized drawdown, and market sensitivity. CAGR measures compound annual growth, volatility measures annualized variability, and maximum drawdown captures the largest peak-to-trough loss in the reporting window. Sharpe and Sortino summarize risk-adjusted return, while market sensitivity indicates how strongly the portfolio moves with the broad benchmark.

## Risk Structure

Stress status: One risk area requires attention. Worst scenario loss: -49.87%. Flagged scenario: equity_shock; flagged test: Loss. These diagnostics are used to identify risk concentrations and scenario vulnerability; they do not by themselves replace the mandate checks.

## Scenario Analysis

| Scenario | PnL | Pass | Top RC Asset | Top 3 RC |
| --- | ---: | --- | --- | ---: |
| equity_shock | -30.90% | False | SLV | 85.23% |
| credit_shock | -1.19% | True | SLV | 85.21% |
| rates_shock | -0.08% | True | SLV | 86.00% |
| inflation_stagflation | -10.79% | True | SLV | 84.76% |
| liquidity_shock | -14.41% | True | SLV | 84.57% |
| recession_severe | -49.87% | False | SLV | 84.29% |

## Conclusion

This English PDF was generated from the current structured portfolio outputs. Use the metrics, stress status, and scenario table together: the headline return profile is only meaningful when read alongside drawdown resilience and scenario behavior.
