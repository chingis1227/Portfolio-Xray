# Build V1 Stock Universe Taxonomy

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`,
`Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This repository contains `PLANS.md`; this document must be maintained in accordance with that file.

## Purpose / Big Picture

After this change the project has a separate stock taxonomy source for current S&P 500 constituents under `config/stock_universe.yml`. A user can validate the stock universe, export it to CSV/JSON, and check an explicit stock config against the universe without mixing stock taxonomy into the ETF workflow or changing optimizer weights.

## Progress

- [x] (2026-04-30 15:25Z) Read `PLANS.md`, inspect existing ETF universe implementation, and confirm the current `config.yml` remains ETF-only.
- [x] (2026-04-30 15:27Z) Create this ExecPlan before implementation.
- [x] (2026-04-30 15:39Z) Add `config/stock_universe.yml` with 503 S&P 500 constituent records and required snapshot header comment.
- [x] (2026-04-30 15:45Z) Add `src/stock_universe.py` with stock-specific validation, diagnostics, list, and export helpers.
- [x] (2026-04-30 15:46Z) Add `run_stock_universe.py` CLI.
- [x] (2026-04-30 15:51Z) Add stock universe tests and update docs.
- [x] (2026-04-30 15:58Z) Run focused validation, exports, and combined tests; record results.

## Surprises & Discoveries

- Observation: the existing ETF universe is CLI-first and only integrated into optimization/report because `config.yml` currently carries ETF tickers.
  Evidence: `run_optimization.py` and `run_report.py` import only `src.etf_universe`, and `config.yml` lists `VOO, QQQ, GLD, SLV, BND, SCHD, SCHP, TLT`.
- Observation: the public constituents table currently resolves to 503 rows and includes class-share symbols such as `BRK.B` and `BF.B`.
  Evidence: the seed generation step fetched the public table and wrote `config/stock_universe.yml` with 503 records; `python run_stock_universe.py validate` returned `record_count: 503`.
- Observation: the local sandbox pytest temp directory remains permission-sensitive for suites that use `tmp_path`.
  Evidence: the combined `tests/test_config_weights_sync.py tests/test_stock_universe.py` run errored under the default temp directory and passed when rerun with `--basetemp='C:\\Users\\ShumeikoYe\\.cache\\codex-pytest-temp-stock-universe'`.

## Decision Log

- Decision: Keep the stock universe completely separate from ETF taxonomy in V1.
  Rationale: The user explicitly asked for `config/stock_universe.yml` and for annotation-only behavior that must not affect current ETF-based optimizer membership.
  Date/Author: 2026-04-30 / Codex
- Decision: Use the current public S&P 500 constituents table as a 503-row seed and pin the date in a YAML header comment.
  Rationale: The user marked snapshot history as critical; the header comment is the simplest source-of-truth marker that stays visible in raw YAML.
  Date/Author: 2026-04-30 / Codex
- Decision: Keep the V1 stock schema intentionally narrow and enforce fixed values for `region`, `currency_exposure`, `main_risk_factor`, `secondary_risk_factors`, `risk_role`, and `index_membership`.
  Rationale: The requested V1 universe is a pinned US large-cap constituent set; strict validation prevents slow drift away from the agreed annotation defaults.
  Date/Author: 2026-04-30 / Codex

## Outcomes & Retrospective

Implemented V1 stock universe taxonomy. The repository now has a separate `config/stock_universe.yml` source with a required snapshot comment header pinned to `2026-04-30`, a stock-specific validator/export/list CLI, focused tests, and generated CSV/JSON exports. Validation passed with `503` records, `tests/test_stock_universe.py` passed with 12 tests, and the combined `tests/test_config_weights_sync.py tests/test_stock_universe.py` suite passed with 15 tests when run with an isolated pytest base temp directory.

## Context and Orientation

This repository already contains `config/etf_universe.yml`, `src/etf_universe.py`, and `run_etf_universe.py`. Together they provide a taxonomy source, validator, exporter, list command, and config annotation workflow for ETFs. They do not select the optimizer universe or change weights in V1.

The stock universe will follow the same broad interaction model but with a smaller schema tailored to common stocks. Unlike ETF taxonomy, stock records do not need duplicate-group or canonical-ticker logic in V1. The current portfolio config in `config.yml` is ETF-only, so the stock universe should remain CLI-only and should not be wired into `run_optimization.py` or `run_report.py`.

## Plan of Work

Create `config/stock_universe.yml` as a YAML list of 503 mappings, one per S&P 500 constituent. The file must begin with a comment header containing `snapshot_date: 2026-04-30`, `snapshot_source: current public S&P 500 constituents list`, and a short note explaining that later refreshes must update the header intentionally.

Create `src/stock_universe.py` as a stock-specific module mirroring the ETF workflow. The module should load YAML, validate required fields, enforce `asset_class: equity`, validate list-typed fields, reuse the same diagnostics statuses `PASS`, `PASS_WITH_WARNINGS`, and `FAIL`, export to CSV/JSON, and list records by `sector`, `industry`, and risk factor.

Create `run_stock_universe.py` as a CLI with `validate`, `check-config`, `export`, and `list`. `check-config` should read `tickers` from a provided YAML config path and warn about unknown stock tickers. It must not edit the config or alter optimizer behavior.

Update `README.md`, `SPEC.md`, and `AGENTS.md` to mention the stock universe workflow. Add `docs/specs/stock_universe_spec.md` as the schema and command reference.

## Concrete Steps

From repository root:

    python run_stock_universe.py validate
    python run_stock_universe.py export --format csv
    python run_stock_universe.py export --format json
    python run_stock_universe.py list --sector "Information Technology"
    python run_stock_universe.py check-config --config path/to/stock_config.yml

Expected behavior: validation prints `PASS` for the 503-row seed; exports write generated artifacts under `results_csv/`; list prints matching rows; `check-config` warns on unknown tickers but never mutates the config.

## Validation and Acceptance

Run:

    python -m pytest tests/test_stock_universe.py -vv
    python -m pytest tests/test_config_weights_sync.py tests/test_stock_universe.py -vv

Acceptance: the stock seed validates; invalid fixtures fail as expected; unknown config tickers produce `PASS_WITH_WARNINGS`; the YAML file includes the required snapshot header comment; exports are deterministic.

## Idempotence and Recovery

All CLI commands are safe to rerun. Export commands may overwrite generated CSV/JSON artifacts but do not rewrite the curated stock YAML unless implementation of the seed-generation step is rerun intentionally.

## Artifacts and Notes

Primary source artifact:

    config/stock_universe.yml

Generated artifacts:

    results_csv/stock_universe.csv
    results_csv/stock_universe.json

## Interfaces and Dependencies

Use existing project dependencies: `yaml`, `pandas`, and optional `requests`/`pandas.read_html` during the one-time seed generation step. Do not add new paid data dependencies.

In `src/stock_universe.py`, provide:

    load_stock_universe(path: str | Path | None = None) -> list[dict[str, Any]]
    validate_stock_universe(records: list[dict[str, Any]]) -> dict[str, Any]
    check_config_tickers(config_tickers: list[str], records: list[dict[str, Any]]) -> dict[str, Any]
    build_stock_universe_diagnostics(config_tickers: list[str] | None = None, universe_path: str | Path | None = None) -> dict[str, Any]
    export_stock_universe(records: list[dict[str, Any]], output_path: str | Path, fmt: str) -> Path
    list_stock_universe(records: list[dict[str, Any]], sector: str | None = None, industry: str | None = None, risk_factor: str | None = None) -> list[dict[str, Any]]

Revision note: created this ExecPlan to cover the new stock taxonomy workflow after ETF taxonomy was already implemented separately.
