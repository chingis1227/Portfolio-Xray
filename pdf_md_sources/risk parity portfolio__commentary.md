---
title: "Risk Parity Portfolio: Executive Commentary"
date: "Analysis results for the 10-year window as of 2026-04-30"
documentclass: article
geometry: "left=18mm, right=18mm, top=24mm, bottom=20mm, head=20pt, foot=20pt, footskip=40pt"
fontsize: 10pt
---

## Executive Summary

Risk Parity Portfolio was reviewed on the latest available reporting window. CAGR is 7.80%, annualized volatility is 8.10%, maximum drawdown is -18.20%, Sharpe is 0.689, Sortino is 1.086, and market sensitivity is 0.395. Stress diagnostics show: Passed with diagnostic warning; worst scenario loss is -15.28%.

## Key Metrics

```{=latex}
\begin{center}\begin{tabular}{@{}>{\centering\arraybackslash}m{0.30\textwidth}@{\hspace{0.45em}}>{\centering\arraybackslash}m{0.30\textwidth}@{\hspace{0.45em}}>{\centering\arraybackslash}m{0.30\textwidth}@{}} \KPIone{7.80\%}{CAGR} & \KPIone{8.10\%}{Volatility} & \KPIone{-18.20\%}{Max Drawdown}\\[0.55em] \KPIone{0.689}{Sharpe} & \KPIone{1.086}{Sortino} & \KPIone{0.395}{Market Sensitivity}\end{tabular}\end{center}
```

## What This Means

The portfolio profile should be read as a trade-off between return, realized drawdown, and market sensitivity. CAGR measures compound annual growth, volatility measures annualized variability, and maximum drawdown captures the largest peak-to-trough loss in the reporting window. Sharpe and Sortino summarize risk-adjusted return, while market sensitivity indicates how strongly the portfolio moves with the broad benchmark.

## Risk Structure

Stress status: Passed with diagnostic warning. Worst scenario loss: -15.28%. Flagged scenario: N/A; flagged test: N/A. These diagnostics are used to identify risk concentrations and scenario vulnerability; they do not by themselves replace the mandate checks.

## Scenario Analysis

| Scenario | PnL | Pass | Top RC Asset | Top 3 RC |
| --- | ---: | --- | --- | ---: |
| equity_shock | -11.68% | True | GLD | 46.52% |
| credit_shock | -1.72% | True | GLD | 40.49% |
| rates_shock | -9.65% | True | TLT | 43.74% |
| inflation_stagflation | -7.78% | True | GLD | 47.63% |
| liquidity_shock | -6.40% | True | SCHD | 43.68% |
| recession_severe | -15.28% | True | SCHD | 43.70% |

## Conclusion

This English PDF was generated from the current structured portfolio outputs. Use the metrics, stress status, and scenario table together: the headline return profile is only meaningful when read alongside drawdown resilience and scenario behavior.
