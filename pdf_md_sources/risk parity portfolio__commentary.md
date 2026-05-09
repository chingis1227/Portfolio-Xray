---
title: "Risk Parity Portfolio: Executive Commentary"
date: "Analysis results for the 10-year window as of 2026-05-08"
documentclass: article
geometry: "left=18mm, right=18mm, top=24mm, bottom=20mm, head=20pt, foot=20pt, footskip=40pt"
fontsize: 10pt
---

## Executive Summary

Risk Parity Portfolio was reviewed on the latest available reporting window. CAGR is 7.60%, annualized volatility is 7.50%, maximum drawdown is -18.90%, Sharpe is 0.720, Sortino is 1.007, and market sensitivity is 0.268. Stress diagnostics show: Passed with diagnostic warning; worst scenario loss is -13.14%.

## Key Metrics

```{=latex}
\begin{center}\begin{tabular}{@{}>{\centering\arraybackslash}m{0.30\textwidth}@{\hspace{0.45em}}>{\centering\arraybackslash}m{0.30\textwidth}@{\hspace{0.45em}}>{\centering\arraybackslash}m{0.30\textwidth}@{}} \KPIone{7.60\%}{CAGR} & \KPIone{7.50\%}{Volatility} & \KPIone{-18.90\%}{Max Drawdown}\\[0.55em] \KPIone{0.720}{Sharpe} & \KPIone{1.007}{Sortino} & \KPIone{0.268}{Market Sensitivity}\end{tabular}\end{center}
```

## What This Means

The portfolio profile should be read as a trade-off between return, realized drawdown, and market sensitivity. CAGR measures compound annual growth, volatility measures annualized variability, and maximum drawdown captures the largest peak-to-trough loss in the reporting window. Sharpe and Sortino summarize risk-adjusted return, while market sensitivity indicates how strongly the portfolio moves with the broad benchmark.

## Risk Structure

Stress status: Passed with diagnostic warning. Worst scenario loss: -13.14%. Flagged scenario: N/A; flagged test: N/A. These diagnostics are used to identify risk concentrations and scenario vulnerability; they do not by themselves replace the mandate checks.

## Scenario Analysis

| Scenario | PnL | Pass | Top RC Asset | Top 3 RC |
| --- | ---: | --- | --- | ---: |
| equity_shock | -10.60% | True | GLD | 45.48% |
| credit_shock | -1.79% | True | TLT | 40.65% |
| rates_shock | -10.24% | True | TLT | 48.95% |
| inflation_stagflation | -7.71% | True | GLD | 47.33% |
| liquidity_shock | -5.98% | True | SCHD | 44.09% |
| recession_severe | -13.14% | True | SCHD | 43.43% |

## Conclusion

This English PDF was generated from the current structured portfolio outputs. Use the metrics, stress status, and scenario table together: the headline return profile is only meaningful when read alongside drawdown resilience and scenario behavior.
