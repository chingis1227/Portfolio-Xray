# Build V1 ETF Universe Taxonomy

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`,
`Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This repository contains `PLANS.md`; this document must be maintained in accordance with that file.

## Purpose / Big Picture

After this change the project has a curated ETF universe that describes ETF economic exposure in a consistent taxonomy. The universe is a YAML source of truth, can be validated and exported through a CLI, and can annotate the current `config.yml` ticker list without changing portfolio weights or replacing the optimizer's existing data and eligibility rules. A user can run `python run_etf_universe.py validate`, inspect exported CSV/JSON, and see `etf_universe_validation.json` in report or optimization output directories.

## Progress

- [x] (2026-04-30) Read `PLANS.md`, current config/data flow, `assets.yml`, `run_optimization.py`, `run_report.py`, and existing tests.
- [x] (2026-04-30) Create this ExecPlan before implementation.
- [x] (2026-04-30) Add initial curated `config/etf_universe.yml` with 185 ETF records.
- [x] (2026-04-30) Add `src/etf_universe.py` with schema validation, diagnostics, exports, and config checks.
- [x] (2026-04-30) Add `run_etf_universe.py` CLI.
- [x] (2026-04-30) Integrate universe diagnostics into optimization/report outputs.
- [x] (2026-04-30) Add tests and documentation updates.
- [x] (2026-04-30) Run focused tests and full suite; record results.
- [x] (2026-04-30) Add 30 ETF records from `ETF FUNDS КРАТКАЯ ВЫЖИМКА.docx`, bringing the curated universe to 215 records.

## Surprises & Discoveries

- Observation: `assets.yml` currently stores only optional currency overrides.
  Evidence: `src.config.load_assets_metadata()` returns `{ticker: {currency: ...}}` and data loading uses it only to resolve asset currency before FX conversion.
- Observation: the active optimizer universe is still `config.yml` tickers, with cash excluded by `src.optimization.get_risk_portfolio_tickers()`.
  Evidence: `docs/portfolio_construction_policy.md` states portfolios are built from a single list of tickers in `config.yml`.
- Observation: the gold duplicate group uses `GLD` as the canonical ticker.
  Evidence: `python run_etf_universe.py check-config --config config.yml` returned `PASS` after setting `canonical_ticker: GLD` for the `gold_physical` group.
- Observation: sandboxed pytest runs could not create or clean the default temp directory for tests using `tmp_path`.
  Evidence: the first combined pytest run failed with `PermissionError` on `C:\Users\ShumeikoYe\.cache\codex-pytest-temp`; the same suite passed when rerun with approved elevated execution.
- Observation: the source document contains ETF-like tickers that are not all US-listed symbols in the same way as the existing seed universe.
  Evidence: `IEAC` and `VECP` are described in the source document as EUR corporate bond UCITS ETFs; they were added to taxonomy as raw document tickers, but optimizer data download may still require exchange-specific provider symbols if later used in `config.yml`.

## Decision Log

- Decision: Keep `assets.yml` separate and create `config/etf_universe.yml` for taxonomy.
  Rationale: The current metadata file is part of FX/currency loading; mixing a large ETF taxonomy into it would make the data loader responsible for unrelated classification behavior.
  Date/Author: 2026-04-30 / Codex
- Decision: V1 diagnostics warn but do not change optimizer inputs or weights.
  Rationale: The user explicitly requested annotation/validation only; current optimizer rules for data coverage, young ETFs, constraints, and weights remain the production path.
  Date/Author: 2026-04-30 / Codex
- Decision: Treat malformed YAML, missing required fields, invalid enums, forbidden fields, canonical breakage, and fixed-income cross-field violations as `FAIL`.
  Rationale: These are source-of-truth quality failures, unlike unknown config tickers or duplicate groups, which are portfolio-composition warnings.
  Date/Author: 2026-04-30 / Codex

## Outcomes & Retrospective

Implemented V1 ETF universe taxonomy. The repository now has a 215-record curated YAML seed, a validator/export/list CLI, closed enum and cross-field validation, config diagnostics with `PASS` / `PASS_WITH_WARNINGS` / `FAIL`, generated CSV/JSON exports, and optimization/report integration that writes `etf_universe_validation.json`. Focused validation passed: `tests/test_etf_universe.py` reported 16 passed, the combined config/universe suite reported 19 passed, and the full suite reported 91 passed. The combined and full suites were run with approved elevated execution because pytest temp directory creation is blocked in the sandbox.

## Context and Orientation

The project is a Python portfolio optimizer and reporting system. `config.yml` supplies the active ticker list. `run_optimization.py` writes optimized weights and `run_report.py` reads those weights to produce analytics. `assets.yml` is an optional lightweight asset metadata file used by `src.config.get_asset_currency()` for FX conversion; it is not a taxonomy source.

The ETF universe will be a curated reference dataset under `config/etf_universe.yml`. It describes classification fields such as asset class, subtype, sector, theme, risk roles, risk factors, region, currency exposure, duration, credit quality, duplicate group, canonical ticker, and data source. It must not contain optimizer-specific allow/block fields.

## Plan of Work

Create `config/etf_universe.yml` as a YAML list of mappings. Include 150-250 ETF records across equities, fixed income, commodities, alternatives, and crypto. Keep `duration_bucket` and `credit_quality` as `none` for non-fixed-income assets, except explicit hybrids with `hybrid_fixed_income_fields_allowed: true` and non-empty notes.

Create `src/etf_universe.py` to define closed enum sets, required fields, forbidden fields, a `UniverseValidationError`, loader functions, validation functions, config diagnostics, list filters, and CSV/JSON export helpers. The module returns diagnostics with `status` equal to `PASS`, `PASS_WITH_WARNINGS`, or `FAIL`.

Create `run_etf_universe.py` with subcommands `validate`, `check-config`, `export`, `list`, and `enrich-yahoo`. `enrich-yahoo` writes generated data only and must never rewrite the curated YAML source.

Integrate diagnostics into `run_optimization.py` and `run_report.py` by writing `etf_universe_validation.json` under `output_dir_final` when the universe file exists. Structural validation failure should be visible and fatal because the source-of-truth file is malformed. Config warnings should not block weights or report generation.

Update `README.md`, `SPEC.md`, and `docs/portfolio_construction_policy.md`. Add `docs/etf_universe_spec.md` as the canonical spec for the new taxonomy. Update `AGENTS.md` only if workflow rules change.

## Concrete Steps

From repository root:

    python run_etf_universe.py validate
    python run_etf_universe.py check-config --config config.yml
    python run_etf_universe.py list --asset-class equity
    python run_etf_universe.py list --risk-factor real_rates
    python run_etf_universe.py export --format csv
    python run_etf_universe.py export --format json

Expected behavior: validation prints `PASS` for a clean seed, list commands print matching tickers, exports create generated files under `results_csv/`, and check-config writes diagnostics that do not mutate `config.yml`.

## Validation and Acceptance

Run:

    python -m pytest tests/test_etf_universe.py -vv
    python -m pytest tests/test_config_weights_sync.py tests/test_etf_universe.py -vv

If shared report or optimization flow changes materially, run the full suite:

    python -m pytest

Acceptance: the seed universe validates; invalid fixtures produce `FAIL`; duplicate, unknown, non-canonical, and missing optional metadata checks produce `PASS_WITH_WARNINGS`; optimization/report integration writes `etf_universe_validation.json` without changing the active ticker list or weights.

## Idempotence and Recovery

All commands are safe to rerun. Export commands overwrite generated CSV/JSON artifacts but do not rewrite `config/etf_universe.yml`. Yahoo enrichment is optional and writes generated output only. If a validation rule fails, fix the YAML source and rerun validation.

## Artifacts and Notes

Primary source artifact:

    config/etf_universe.yml

Generated artifacts:

    results_csv/etf_universe.csv
    results_csv/etf_universe.json
    results_csv/etf_universe_yahoo_enrichment.csv
    Main portfolio/etf_universe_validation.json

## Interfaces and Dependencies

Use existing project dependencies: `yaml`, `pandas`, and optional `yfinance`. Do not add paid API dependencies in V1.

In `src/etf_universe.py`, provide:

    load_etf_universe(path: str | Path | None = None) -> list[dict[str, Any]]
    validate_etf_universe(records: list[dict[str, Any]]) -> dict[str, Any]
    check_config_tickers(config_tickers: list[str], records: list[dict[str, Any]]) -> dict[str, Any]
    build_universe_diagnostics(config_tickers: list[str] | None = None, universe_path: str | Path | None = None) -> dict[str, Any]
    export_universe(records: list[dict[str, Any]], output_path: str | Path, fmt: str) -> Path
    list_universe(records: list[dict[str, Any]], asset_class: str | None = None, risk_factor: str | None = None) -> list[dict[str, Any]]

`run_optimization.py` and `run_report.py` should call a small helper that writes diagnostics to `output_dir_final / "etf_universe_validation.json"` when `config/etf_universe.yml` exists.
