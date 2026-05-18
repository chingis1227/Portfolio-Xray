---
title: "Equal-Weight Portfolio: Target Weights"
date: "Analysis results for the 10-year window as of 2026-05-15"
documentclass: article
geometry: "left=18mm, right=18mm, top=24mm, bottom=20mm, head=20pt, foot=20pt, footskip=40pt"
fontsize: 10pt
---

## Executive Summary

Equal-Weight Portfolio was reviewed on the latest available reporting window. CAGR is 11.20%, annualized volatility is 10.30%, maximum drawdown is -20.60%, Sharpe is 0.858, Sortino is 1.201, and market sensitivity is 0.423. Stress diagnostics show: One risk area requires attention; worst scenario loss is -26.39%.

## Key Metrics

```{=latex}
\begin{center}\begin{tabular}{@{}>{\centering\arraybackslash}m{0.30\textwidth}@{\hspace{0.45em}}>{\centering\arraybackslash}m{0.30\textwidth}@{\hspace{0.45em}}>{\centering\arraybackslash}m{0.30\textwidth}@{}} \KPIone{11.20\%}{CAGR} & \KPIone{10.30\%}{Volatility} & \KPIone{-20.60\%}{Max Drawdown}\\[0.55em] \KPIone{0.858}{Sharpe} & \KPIone{1.201}{Sortino} & \KPIone{0.423}{Market Sensitivity}\end{tabular}\end{center}
```

## What This Means

The portfolio profile should be read as a trade-off between return, realized drawdown, and market sensitivity. CAGR measures compound annual growth, volatility measures annualized variability, and maximum drawdown captures the largest peak-to-trough loss in the reporting window. Sharpe and Sortino summarize risk-adjusted return, while market sensitivity indicates how strongly the portfolio moves with the broad benchmark.

## Risk Structure

Stress status: One risk area requires attention. Worst scenario loss: -26.39%. Flagged scenario: recession_severe; flagged test: Loss. These diagnostics are used to identify risk concentrations and scenario vulnerability; they do not by themselves replace the mandate checks.

## Scenario Analysis

| Scenario | PnL | Pass | Top RC Asset | Top 3 RC |
| --- | ---: | --- | --- | ---: |
| equity_shock | -17.86% | True | SLV | 65.11% |
| credit_shock | -1.53% | True | SLV | 60.28% |
| rates_shock | -7.20% | True | SLV | 60.40% |
| inflation_stagflation | -9.06% | True | SLV | 65.26% |
| liquidity_shock | -8.97% | True | SLV | 61.12% |
| recession_severe | -26.39% | False | SLV | 60.71% |

## Conclusion

This English PDF was generated from the current structured portfolio outputs. Use the metrics, stress status, and scenario table together: the headline return profile is only meaningful when read alongside drawdown resilience and scenario behavior.
