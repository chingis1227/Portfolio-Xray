# Taxonomy Specification

This document maps the taxonomy specs for ETFs and stocks.

## Role

Taxonomy is annotation-only in V1. It validates and annotates configured tickers, supports diagnostics and stress taxonomy mapping, and can export metadata. It does not select the optimizer universe, change optimizer membership, or change weights.

## ETF Taxonomy

The ETF taxonomy source of truth is [etf_universe_spec.md](etf_universe_spec.md).

Implementation files:

- `config/etf_universe.yml`
- `src/etf_universe.py`
- `run_etf_universe.py`

Optimization and report runs may write `etf_universe_validation.json`, but ETF taxonomy warnings do not alter portfolio composition or weights.

## Stock Taxonomy

The stock taxonomy source of truth is [stock_universe_spec.md](stock_universe_spec.md).

Implementation files:

- `config/stock_universe.yml`
- `src/stock_universe.py`
- `run_stock_universe.py`

Stock taxonomy V1 is CLI-only unless a future canonical spec wires it into optimization/report membership. It does not alter portfolio composition or weights.

## Related Specs

- Portfolio policy boundary: [portfolio_construction_policy.md](portfolio_construction_policy.md)
- Stress taxonomy covariance behavior: [stress_testing_spec.md](stress_testing_spec.md)
