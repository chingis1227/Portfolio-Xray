---
title: "Main Portfolio: Target Weights"
date: "Analysis results for the 10-year window as of 2026-05-08"
documentclass: article
geometry: "left=18mm, right=18mm, top=24mm, bottom=20mm, head=20pt, foot=20pt, footskip=40pt"
fontsize: 10pt
---

## Executive Summary

Main Portfolio was reviewed on the latest available reporting window. CAGR is 6.10%, annualized volatility is 6.80%, maximum drawdown is -17.40%, Sharpe is 0.574, Sortino is 0.802, and market sensitivity is 0.182. Stress diagnostics show: Passed with diagnostic warning; worst scenario loss is -12.30%.

## Key Metrics

```{=latex}
\begin{center}\begin{tabular}{@{}>{\centering\arraybackslash}m{0.30\textwidth}@{\hspace{0.45em}}>{\centering\arraybackslash}m{0.30\textwidth}@{\hspace{0.45em}}>{\centering\arraybackslash}m{0.30\textwidth}@{}} \KPIone{6.10\%}{CAGR} & \KPIone{6.80\%}{Volatility} & \KPIone{-17.40\%}{Max Drawdown}\\[0.55em] \KPIone{0.574}{Sharpe} & \KPIone{0.802}{Sortino} & \KPIone{0.182}{Market Sensitivity}\end{tabular}\end{center}
```

## What This Means

The portfolio profile should be read as a trade-off between return, realized drawdown, and market sensitivity. CAGR measures compound annual growth, volatility measures annualized variability, and maximum drawdown captures the largest peak-to-trough loss in the reporting window. Sharpe and Sortino summarize risk-adjusted return, while market sensitivity indicates how strongly the portfolio moves with the broad benchmark.

## Risk Structure

Stress status: Passed with diagnostic warning. Worst scenario loss: -12.30%. Flagged scenario: N/A; flagged test: N/A. These diagnostics are used to identify risk concentrations and scenario vulnerability; they do not by themselves replace the mandate checks.

## Scenario Analysis

| Scenario | PnL | Pass | Top RC Asset | Top 3 RC |
| --- | ---: | --- | --- | ---: |
| equity_shock | -5.24% | True | SCHD | 69.49% |
| credit_shock | -2.02% | True | SCHD | 67.02% |
| rates_shock | -12.30% | True | TLT | 64.94% |
| inflation_stagflation | -5.85% | True | GLD | 65.39% |
| liquidity_shock | -3.81% | True | SCHD | 69.67% |
| recession_severe | -6.37% | True | SCHD | 69.35% |

## Conclusion

This English PDF was generated from the current structured portfolio outputs. Use the metrics, stress status, and scenario table together: the headline return profile is only meaningful when read alongside drawdown resilience and scenario behavior.
