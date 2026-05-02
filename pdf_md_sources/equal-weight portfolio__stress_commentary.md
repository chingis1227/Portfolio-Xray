---
title: "Equal-Weight Portfolio: Stress Analysis"
date: "Analysis results for the 10-year window as of 2026-04-30"
documentclass: article
geometry: "left=18mm, right=18mm, top=24mm, bottom=20mm, head=20pt, foot=20pt, footskip=40pt"
fontsize: 10pt
---

## Executive Summary

Equal-Weight Portfolio was reviewed on the latest available reporting window. CAGR is 10.60%, annualized volatility is 10.30%, maximum drawdown is -19.70%, Sharpe is 0.820, Sortino is 1.356, and market sensitivity is 0.512. Stress diagnostics show: One risk area requires attention; worst scenario loss is -26.30%.

## Key Metrics

```{=latex}
\begin{center}\begin{tabular}{@{}>{\centering\arraybackslash}m{0.30\textwidth}@{\hspace{0.45em}}>{\centering\arraybackslash}m{0.30\textwidth}@{\hspace{0.45em}}>{\centering\arraybackslash}m{0.30\textwidth}@{}} \KPIone{10.60\%}{CAGR} & \KPIone{10.30\%}{Volatility} & \KPIone{-19.70\%}{Max Drawdown}\\[0.55em] \KPIone{0.820}{Sharpe} & \KPIone{1.356}{Sortino} & \KPIone{0.512}{Market Sensitivity}\end{tabular}\end{center}
```

## What This Means

The portfolio profile should be read as a trade-off between return, realized drawdown, and market sensitivity. CAGR measures compound annual growth, volatility measures annualized variability, and maximum drawdown captures the largest peak-to-trough loss in the reporting window. Sharpe and Sortino summarize risk-adjusted return, while market sensitivity indicates how strongly the portfolio moves with the broad benchmark.

## Risk Structure

Stress status: One risk area requires attention. Worst scenario loss: -26.30%. Flagged scenario: recession_severe; flagged test: Loss. These diagnostics are used to identify risk concentrations and scenario vulnerability; they do not by themselves replace the mandate checks.

## Scenario Analysis

| Scenario | PnL | Pass | Top RC Asset | Top 3 RC |
| --- | ---: | --- | --- | ---: |
| equity_shock | -17.36% | True | SLV | 54.47% |
| credit_shock | -1.50% | True | SLV | 54.47% |
| rates_shock | -7.37% | True | SLV | 57.56% |
| inflation_stagflation | -8.61% | True | SLV | 57.56% |
| liquidity_shock | -8.72% | True | SLV | 54.47% |
| recession_severe | -26.30% | False | SLV | 54.34% |

## Conclusion

This English PDF was generated from the current structured portfolio outputs. Use the metrics, stress status, and scenario table together: the headline return profile is only meaningful when read alongside drawdown resilience and scenario behavior.
