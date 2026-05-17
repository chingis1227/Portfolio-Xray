---
title: "Main Portfolio: Stress Analysis"
date: "Analysis results for the 10-year window as of 2026-05-08"
documentclass: article
geometry: "left=18mm, right=18mm, top=24mm, bottom=20mm, head=20pt, foot=20pt, footskip=40pt"
fontsize: 10pt
---

## Executive Summary

Main Portfolio was reviewed on the latest available reporting window. CAGR is 6.30%, annualized volatility is 7.20%, maximum drawdown is -19.20%, Sharpe is 0.574, Sortino is 0.802, and market sensitivity is 0.194. Stress diagnostics show: Passed with diagnostic warning; worst scenario loss is -13.84%.

## Key Metrics

```{=latex}
\begin{center}\begin{tabular}{@{}>{\centering\arraybackslash}m{0.30\textwidth}@{\hspace{0.45em}}>{\centering\arraybackslash}m{0.30\textwidth}@{\hspace{0.45em}}>{\centering\arraybackslash}m{0.30\textwidth}@{}} \KPIone{6.30\%}{CAGR} & \KPIone{7.20\%}{Volatility} & \KPIone{-19.20\%}{Max Drawdown}\\[0.55em] \KPIone{0.574}{Sharpe} & \KPIone{0.802}{Sortino} & \KPIone{0.194}{Market Sensitivity}\end{tabular}\end{center}
```

## What This Means

The portfolio profile should be read as a trade-off between return, realized drawdown, and market sensitivity. CAGR measures compound annual growth, volatility measures annualized variability, and maximum drawdown captures the largest peak-to-trough loss in the reporting window. Sharpe and Sortino summarize risk-adjusted return, while market sensitivity indicates how strongly the portfolio moves with the broad benchmark.

## Risk Structure

Stress status: Passed with diagnostic warning. Worst scenario loss: -13.84%. Flagged scenario: N/A; flagged test: N/A. These diagnostics are used to identify risk concentrations and scenario vulnerability; they do not by themselves replace the mandate checks.

## Scenario Analysis

| Scenario | PnL | Pass | Top RC Asset | Top 3 RC |
| --- | ---: | --- | --- | ---: |
| equity_shock | -10.78% | True | TLT | 60.27% |
| credit_shock | -2.70% | True | TLT | 58.04% |
| rates_shock | 0.00% | True | TLT | 66.75% |
| inflation_stagflation | -4.97% | True | TLT | 63.39% |
| liquidity_shock | -6.74% | True | TLT | 55.85% |
| recession_severe | -13.84% | True | TLT | 55.77% |

## Conclusion

This English PDF was generated from the current structured portfolio outputs. Use the metrics, stress status, and scenario table together: the headline return profile is only meaningful when read alongside drawdown resilience and scenario behavior.
