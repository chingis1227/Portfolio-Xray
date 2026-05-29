# US Universe Ingestion Specification

## Purpose

Scale ETF and stock taxonomy onboarding from hundreds to thousands of US-listed symbols using **public, machine-readable listing sources**, without silently overwriting production universe files.

This pipeline produces **draft artifacts only**. Merge into `config/etf_universe.yml` or `config/stock_universe.yml` requires explicit human review and a separate merge step (not automated in V1).

Related specs:

- [asset_taxonomy_onboarding_spec.md](asset_taxonomy_onboarding_spec.md) — per-ticker stress block report after rows exist in universe YAML
- [etf_universe_spec.md](etf_universe_spec.md) / [stock_universe_spec.md](stock_universe_spec.md) — production schemas
- [taxonomy_spec.md](taxonomy_spec.md) — X-Ray allocation taxonomy
- [stress_testing_spec.md](stress_testing_spec.md) — synthetic PnL vs synthetic RC boundaries

## Sources (V1)

| Source | File | Role |
| --- | --- | --- |
| Nasdaq Trader | `nasdaqlisted.txt` | Nasdaq-listed symbols, ETF flag, test issue, financial status |
| Nasdaq Trader | `otherlisted.txt` | NYSE/AMEX/other listings, ETF flag |
| SEC | `company_tickers_exchange.json` | Company names, CIK, exchange cross-check |

Default URLs are wired in `scripts/ingest_us_listed_universe.py`. Local fixture paths are supported for offline tests and air-gapped runs.

## Why not IBKR as primary classification source

Interactive Brokers (and similar broker security masters) are useful for **execution** metadata (conids, exchange routing, margin) but are a poor **primary taxonomy source** for Portfolio MRI because:

- licensing and API access vary by account and region;
- product type labels are broker-specific and not stable for stress RC blocks;
- ingestion should be reproducible from public listings without paid entitlements;
- taxonomy must align with project enums in `etf_universe.yml` / `stock_universe.yml`, not broker symbology.

IBKR or issuer sites may inform **manual review** after draft generation; they are not the V1 ingestion driver.

## Staged flow

```text
Public listing sources (Nasdaq + SEC)
  → scripts/ingest_us_listed_universe.py
  → raw_us_universe.csv
  → clean_us_universe.csv (kept / removed / flagged with reasons)
  → rule-based classification
  → draft_etf_universe.yml / draft_stock_universe.yml
  → stress block derivation (EQ/CR/ND/TI/CO/CA)
  → ingestion_report.json + needs_review.csv
  → manual review (hybrid / low confidence)
  → optional merge into production universe (human-only)
```

## CLI

```bash
python scripts/ingest_us_listed_universe.py \
  --nasdaq-listed-url <url_or_path> \
  --other-listed-url <url_or_path> \
  --sec-company-tickers-url <url_or_path> \
  --output-dir output/universe_ingestion \
  --dry-run
```

`--dry-run` computes the report without writing files. Production paths under `config/` are never modified.

## Automated vs manual

| Automated | Manual review required |
| --- | --- |
| Download/parse sources | Hybrid ETFs (leveraged, inverse, covered call, multi-asset) |
| Deduplicate tickers | Preferred shares, warrants, units (removed or flagged) |
| Remove test issues | Sector/industry for stocks (defaults to `Unknown`) |
| ETF/stock routing from ETF flag + name heuristics | Aggregate bond CR vs ND judgment |
| Rule-based ETF taxonomy (keywords) | REIT and mortgage REIT nuance |
| Stress block assignment via `derive_stress_block_from_taxonomy_row` | Merge into production YAML |
| Draft validation + readiness counts | Confirm price history / factor betas (PnL) |

## Confidence fields (report-only)

Stored in `ingestion_report.json` and `needs_review.csv`, **not** in production universe YAML unless a future schema version adds them:

- `classification_method`: `rule_based` | `source_metadata` | `inferred` | `manual_required`
- `classification_confidence`: `high` | `medium` | `low`
- `needs_review`: boolean
- `warnings`: list of strings

Draft rows use `data_source: [public_listing_ingestion]` where the ETF schema allows it.

## Readiness layers

### X-Ray readiness

Draft rows include required taxonomy fields for routing (asset class, region, currency, risk factors). Full production validation may still fail until enums and index membership are curated (e.g. stocks default to empty `index_membership` until operator assigns `SP500` or another supported value).

### Synthetic PnL readiness

**Not confirmed by ingestion.** Static classification does not prove weekly factor betas or price coverage. After merge, run portfolio review / stress report and confirm factor regression blocks in `stress_report.json`.

### Synthetic RC readiness

Requires a valid stress block (not silent default EQ), non-low confidence, and `needs_review=false`. Stress blocks affect **taxonomy_blend_v1** RC diagnostics only; they do **not** change synthetic scenario PnL (linear shock × betas).

## Output artifacts

| File | Description |
| --- | --- |
| `raw_us_universe.csv` | Merged raw rows with source metadata |
| `clean_us_universe.csv` | Kept, flagged, and removed rows with `disposition_reason` |
| `draft_etf_universe.yml` | Draft ETF taxonomy rows |
| `draft_stock_universe.yml` | Draft stock taxonomy rows |
| `needs_review.csv` | Low/medium confidence and hybrid candidates |
| `ingestion_report.json` | Counts, validation, readiness, warning categories |

## Validation

After draft generation:

```bash
# Production validators (against production files — unchanged by ingestion)
python run_etf_universe.py validate
python run_stock_universe.py validate

# Draft validation is embedded in ingestion_report.json
python scripts/ingest_us_listed_universe.py ... --format json
```

### Controlled merge (production write requires confirmation)

```bash
# Preview diff / merge plan (no production writes)
python scripts/merge_draft_universe.py --ingestion-dir output/universe_ingestion

# Apply merge for reviewed ETFs (creates backup under merge_backup/)
python scripts/merge_draft_universe.py --ingestion-dir output/universe_ingestion --confirm

# Merge specific tickers only
python scripts/merge_draft_universe.py --ingestion-dir output/universe_ingestion \
  --tickers NEWETF1,NEWETF2 --confirm

# Stocks: V1 production schema is SP500-only; merge skips non-SP500 rows unless enriched
python scripts/merge_draft_universe.py --ingestion-dir output/universe_ingestion \
  --include-stocks --enrich-stocks-yahoo --confirm
```

### Stock Batch 1 (index-based, up to 1000 names)

Controlled expansion from index membership (not bulk Nasdaq listing merge):

```bash
# Build draft + review artifacts (no production writes)
python scripts/build_stock_batch1.py --output-dir output/stock_batch1

# Preview merge for accepted new tickers only
python scripts/merge_draft_universe.py --stock-batch-dir output/stock_batch1

# Apply merge after explicit review (blocked if stock_batch1_review_report.json merge_ready=false)
python scripts/merge_draft_universe.py --stock-batch-dir output/stock_batch1 --confirm

# Post-merge validation
python run_stock_universe.py validate
python scripts/taxonomy_onboard_report.py --tickers TICK1,TICK2 --format text
```

Sources (live run):

| Field | Source |
| --- | --- |
| S&P 500 | Wikipedia GICS table |
| Russell 1000 | iShares IWB holdings CSV (or local `--r1000-csv`) |
| Russell 3000 | iShares IWV holdings CSV (or local `--r3000-csv`) |
| Sector/industry | Index file / Wikipedia GICS; production lookup; optional Yahoo (`yfinance`) |

Artifacts: `draft_stock_universe_batch1.yml`, `stock_batch1_review_report.json`, `needs_review_stocks.csv`, `stock_batch1_accepted_tickers.txt`.

Stock sector/industry enrichment:

- Automatic cross-reference from production `stock_universe.yml` during ingestion
- Optional `--enrich-sectors-yahoo` on ingestion or `--enrich-stocks-yahoo` on merge (yfinance)

SEC downloads require a User-Agent header (`DEFAULT_SEC_USER_AGENT` in code).

Per-ticker onboarding after manual merge:

```bash
python scripts/taxonomy_onboard_report.py --tickers VOO,HYG,NEW_TICKER
```

## Connection to Portfolio X-Ray and Stress Test Lab

- **Portfolio X-Ray** uses taxonomy fields (asset class, sector, region, risk factors) for allocation breakdowns and diagnostics.
- **Stress Test Lab synthetic PnL** uses estimated factor betas and scenario shocks; ingestion does not compute betas.
- **Stress Test Lab synthetic RC** maps taxonomy → stress blocks (EQ/CR/ND/TI/CO/CA) for block-blended correlation; unknown or wrong taxonomy creates silent EQ risk — the pipeline flags those cases explicitly.

## Non-goals (V1)

- Overwriting production universe files automatically
- New stress blocks or changes to `VOL_MULT_BLOCK` / correlation matrices
- AI classification of every row
- Paid API dependencies
- Factor beta download or full portfolio review inside ingestion
- Optimizer universe selection

## Implementation

- Core logic: `src/universe_ingestion.py`
- CLI: `scripts/ingest_us_listed_universe.py`
- Stress block helper: `derive_stress_block_from_taxonomy_row()` in `src/taxonomy_stress_blocks.py`
