# ETF Universe Specification

## Purpose

`config/etf_universe.yml` is the curated source of truth for ETF classification. It annotates ETF economic exposure for portfolio analytics, duplicate diagnostics, factor/risk review, reporting, and future risk budgeting work.

V1 is validation and annotation only. It does not change `config.yml`, does not select the optimizer universe, and does not alter optimized weights.

## Record Schema

Each ETF record is a YAML mapping with these required fields:

- `ticker`
- `name`
- `issuer`
- `asset_class`
- `subtype`
- `sector`
- `thematic_primary`
- `thematic_tags`
- `risk_role`
- `main_risk_factor`
- `secondary_risk_factors`
- `region`
- `currency_exposure`
- `duration_bucket`
- `credit_quality`
- `duplicate_group_id`
- `canonical_ticker`
- `data_source`

Optional fields:

- `notes`
- `hybrid_fixed_income_fields_allowed`

Forbidden fields:

- `optimization_rule`
- `eligibility_bucket`
- any optimizer-specific allow/block flag.

## Closed Enums

`asset_class`: `equity`, `fixed_income`, `commodity`, `cash`, `alternative`, `crypto`.

`subtype`: `broad_market`, `large_cap`, `mid_cap`, `small_cap`, `regional_etf`, `country_etf`, `sector_etf`, `thematic_etf`, `factor_etf`, `dividend`, `growth`, `value`, `quality`, `momentum`, `low_volatility`, `equal_weight`, `treasury`, `tips`, `aggregate_bond`, `corporate_ig`, `high_yield`, `em_debt`, `floating_rate`, `bank_loan`, `preferred`, `t_bill`, `ultra_short_bond`, `commodity_etf`, `gold`, `silver`, `energy_commodity`, `agriculture`, `industrial_metals`, `currency_etf`, `reit`, `infrastructure`, `managed_futures`, `volatility_etf`, `tail_risk`, `covered_call`, `multi_asset`, `bitcoin_spot`, `ether_spot`.

`sector`: `technology`, `healthcare`, `financials`, `energy`, `industrials`, `utilities`, `consumer_discretionary`, `consumer_staples`, `communication_services`, `real_estate`, `materials`, `multi_sector`, `none`.

`risk_role`: `risk_on`, `defensive`, `inflation_hedge`, `duration`, `liquidity`, `cash_like`, `crisis_hedge`, `diversifier`, `carry`, `growth`, `cyclical`, `income`, `volatility_hedge`, `tail_hedge`, `unknown`.

`main_risk_factor`: `equity`, `real_rates`, `inflation`, `credit`, `usd`, `commodity`, `vix`, `us_growth`, `short_rates`, `liquidity`, `crypto_beta`.

`secondary_risk_factors`: same values as `main_risk_factor`, plus descriptive tags only when prefixed with `tag:`.

`region`: `US`, `Europe`, `EM`, `Global`, `China`, `Japan`, `Developed_ex_US`, `Asia_ex_Japan`, `LatAm`, `Frontier`, `Single_Country`, `Canada`, `Australia`, `UK`, `India`.

`currency_exposure`: `USD`, `EUR`, `JPY`, `GBP`, `CNY`, `CAD`, `AUD`, `CHF`, `local_EM`, `hedged`, `mixed`.

`duration_bucket`: `cash`, `short`, `intermediate`, `long`, `ultra_long`, `floating`, `none`.

`credit_quality`: `Treasury`, `Agency`, `IG`, `HY`, `EM_debt`, `Mixed`, `Unrated`, `none`.

`data_source`: `manual_seed`, `issuer`, `yahoo`, `inferred`.

## Cross-Field Rules

- `data_source` is required and must be a non-empty list.
- `risk_role` is a non-empty list; the first value is the primary role.
- `thematic_primary` is required; use `none` when no theme applies.
- `thematic_tags` is always a list; an empty list is allowed.
- Broad equity ETFs use `sector: multi_sector`; `sector: none` is only for assets where sector is not applicable.
- `currency_exposure` means economic currency exposure, not trading currency.
- If `ticker != canonical_ticker`, the canonical ticker must exist in the same universe.
- If `asset_class = fixed_income`, `duration_bucket` and `credit_quality` must be non-empty and not `none`.
- If `asset_class != fixed_income`, `duration_bucket = none` and `credit_quality = none`, unless `hybrid_fixed_income_fields_allowed: true` is set and `notes` explains the hybrid.
- `oil` is not allowed as a production `main_risk_factor`. Use `secondary_risk_factors: [tag:oil]` or `notes` for oil sensitivity.

## Diagnostics Status

- `PASS`: universe source is structurally valid and config tickers produce no warnings.
- `PASS_WITH_WARNINGS`: structural validation passed, but there are warnings such as unknown config tickers, duplicate groups in config, non-canonical selections, or missing optional metadata.
- `FAIL`: malformed YAML, missing required field, invalid enum, forbidden field, broken canonical reference, or fixed-income cross-field violation.

## Commands

Run from repository root:

```bash
python run_etf_universe.py validate
python run_etf_universe.py check-config --config config.yml
python run_etf_universe.py export --format csv
python run_etf_universe.py export --format json
python run_etf_universe.py list --asset-class equity
python run_etf_universe.py list --risk-factor real_rates
python run_etf_universe.py enrich-yahoo
```

`enrich-yahoo` writes generated coverage data only. It must not rewrite `config/etf_universe.yml`.

## Outputs

- Source of truth: `config/etf_universe.yml`
- Generated exports: `results_csv/etf_universe.csv`, `results_csv/etf_universe.json`
- Optional Yahoo enrichment: `results_csv/etf_universe_yahoo_enrichment.csv`
- Run annotation: `output_dir_final/etf_universe_validation.json`
