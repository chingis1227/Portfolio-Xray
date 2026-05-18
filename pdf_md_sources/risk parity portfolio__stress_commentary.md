---
title: "Risk Parity Portfolio: Stress Analysis"
date: "Analysis results for the 10-year window as of 2026-05-15"
documentclass: article
geometry: "left=18mm, right=18mm, top=24mm, bottom=20mm, head=20pt, foot=20pt, footskip=40pt"
fontsize: 10pt
---

## Executive Summary

Risk Parity Portfolio was reviewed on the latest available reporting window. CAGR is 7.40%, annualized volatility is 7.50%, maximum drawdown is -18.90%, Sharpe is 0.698, Sortino is 0.976, and market sensitivity is 0.268. Stress diagnostics show: Passed with diagnostic warning; worst scenario loss is -13.41%.

## Key Metrics

```{=latex}
\begin{center}\begin{tabular}{@{}>{\centering\arraybackslash}m{0.30\textwidth}@{\hspace{0.45em}}>{\centering\arraybackslash}m{0.30\textwidth}@{\hspace{0.45em}}>{\centering\arraybackslash}m{0.30\textwidth}@{}} \KPIone{7.40\%}{CAGR} & \KPIone{7.50\%}{Volatility} & \KPIone{-18.90\%}{Max Drawdown}\\[0.55em] \KPIone{0.698}{Sharpe} & \KPIone{0.976}{Sortino} & \KPIone{0.268}{Market Sensitivity}\end{tabular}\end{center}
```

## What This Means

The portfolio profile should be read as a trade-off between return, realized drawdown, and market sensitivity. CAGR measures compound annual growth, volatility measures annualized variability, and maximum drawdown captures the largest peak-to-trough loss in the reporting window. Sharpe and Sortino summarize risk-adjusted return, while market sensitivity indicates how strongly the portfolio moves with the broad benchmark.

## Risk Structure

Stress status: Passed with diagnostic warning. Worst scenario loss: -13.41%. Flagged scenario: N/A; flagged test: N/A. These diagnostics are used to identify risk concentrations and scenario vulnerability; they do not by themselves replace the mandate checks.

## Scenario Analysis

| Scenario | PnL | Pass | Top RC Asset | Top 3 RC |
| --- | ---: | --- | --- | ---: |
| equity_shock | -10.87% | True | GLD | 45.51% |
| credit_shock | -1.74% | True | TLT | 40.65% |
| rates_shock | -10.16% | True | TLT | 48.91% |
| inflation_stagflation | -7.85% | True | GLD | 47.35% |
| liquidity_shock | -6.06% | True | SCHD | 44.09% |
| recession_severe | -13.41% | True | SCHD | 43.42% |

## Conclusion

This English PDF was generated from the current structured portfolio outputs. Use the metrics, stress status, and scenario table together: the headline return profile is only meaningful when read alongside drawdown resilience and scenario behavior.
