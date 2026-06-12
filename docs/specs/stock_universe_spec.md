# Stock Universe Specification

## Purpose

`config/stock_universe.yml` is the curated source of truth for current US stock classification. It annotates common-stock exposure for analytics and config validation while staying separate from ETF taxonomy.

V1 is validation and annotation only. It does not change `config.yml`, does not select the optimizer universe, and does not alter optimized weights.

## Snapshot History

The source-of-truth YAML file must start with a comment header that pins the snapshot:

- `snapshot_date: 2026-04-30`
- `snapshot_source: current public S&P 500 constituents list`
- `verification_note: V1 seed pinned to this snapshot date; later refreshes must update the header comment intentionally`

This header is required source-history metadata, not optional documentation. The original header
still identifies the S&P 500 seed baseline; controlled batch ingestion may add additional index
membership rows such as `R1000` while preserving the same snapshot-date lineage.

## Record Schema

Each stock record is a YAML mapping with these required fields:

- `ticker`
- `company_name`
- `asset_class`
- `sector`
- `industry`
- `thematic_tags`
- `region`
- `currency_exposure`
- `main_risk_factor`
- `secondary_risk_factors`
- `risk_role`
- `index_membership`

Forbidden fields:

- `optimization_rule`
- `eligibility_bucket`
- any optimizer-specific allow/block flag

## Validation Rules

- `ticker` must be unique and uppercase-normalized.
- `asset_class` must be `equity`.
- `company_name`, `sector`, `industry`, `region`, and `currency_exposure` must be non-empty strings.
- `thematic_tags`, `secondary_risk_factors`, `risk_role`, and `index_membership` must be lists.
- `risk_role` must be a non-empty list and uses the same enum as ETF taxonomy.
- `main_risk_factor` must use the same production factor enum as ETF taxonomy and must equal `equity` in V1.
- `secondary_risk_factors` must use the same factor enum as ETF taxonomy, with optional `tag:*` values.
- `index_membership` must be a non-empty list with exactly one primary tag: `SP500`, `R1000`, or `R3000`.
- V1 seed records include the original `SP500` baseline. Controlled stock-batch expansion may add
  `R1000` / `R3000` records via the controlled batch pipeline.

## V1 Seed Defaults

The current checked-in universe is an expanded, validation-only stock taxonomy. It includes the
original S&P 500 seed plus controlled Russell-style batch additions; as of the 2026-06-12
stabilization pass it stores 855 rows, with at least 500 `SP500` records and at least 300 `R1000`
records. Tests should validate structural quality and index-membership coverage rather than
re-impose the old 503-row seed size.

Source-derived fields:

- `ticker` from public symbol
- `company_name` from public security name
- `sector` from GICS Sector
- `industry` from GICS Sub-Industry

Curated V1 defaults:

- `asset_class: equity`
- `thematic_tags: []`
- `region: US`
- `currency_exposure: USD`
- `main_risk_factor: equity`
- `secondary_risk_factors: [us_growth]`
- `risk_role: [risk_on]`
- `index_membership: [SP500]` for the original seed; batch-expanded rows may use `[R1000]` or
  `[R3000]`

## Diagnostics Status

- `PASS`: source is structurally valid and config tickers produce no warnings.
- `PASS_WITH_WARNINGS`: structural validation passed, but config contains unknown tickers.
- `FAIL`: malformed YAML, missing required field, invalid type, invalid enum, or duplicate ticker.

## Commands

Run from repository root:

```bash
python run_stock_universe.py validate
python run_stock_universe.py check-config --config path/to/stock_config.yml
python run_stock_universe.py export --format csv
python run_stock_universe.py export --format json
python run_stock_universe.py list --sector "Information Technology"
python run_stock_universe.py list --industry "Biotechnology"
python run_stock_universe.py list --risk-factor us_growth
```

## Outputs

- Source of truth: `config/stock_universe.yml`
- Generated exports: `results_csv/stock_universe.csv`, `results_csv/stock_universe.json`
