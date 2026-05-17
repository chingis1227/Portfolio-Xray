# Portfolio X-Ray Diagnostics Layer v2

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`,
`Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.
Maintenance follows [PLANS.md](../../PLANS.md) at the repository root.

## Purpose / Big Picture

After this change, a user can run the existing report workflow and read a structured
Portfolio X-Ray diagnosis before any optimization recommendation or candidate comparison.
The new generated artifact `portfolio_xray.json`, plus `report.txt`, `report.html`, and
`commentary.txt`, explain what the portfolio holds, how risk is distributed, which hidden
exposures are visible in existing diagnostics, what behavioral archetype best describes
the portfolio, and which market environments look weakest.

Portfolio X-Ray v2 is diagnostic-only. It consumes existing report pipeline outputs and
in-memory diagnostics; it must not recompute canonical metrics with alternative formulas.
It must not optimize, change weights, change mandate gates, change stress pass/fail status,
create a recommendation engine, create a Portfolio Health Score, create a Selection Engine,
or make scoring-driven portfolio decisions.

## Progress

- [x] (2026-05-15) Read `PLANS.md`, current `src/portfolio_xray.py`, report snapshot writers,
  commentary writer, reporting spec, and current X-Ray tests.
- [x] (2026-05-15) Captured user decisions: one master ExecPlan, report-first delivery,
  explicit non-goals, top-level `portfolio_xray.json` contract, common section schema,
  rule-based hidden risk detector, archetype confidence/caveats, evidence-summary Weakness
  Map, and centralized thresholds.
- [x] (2026-05-15) Added Portfolio X-Ray v2 builder, section schema, named thresholds,
  hidden-risk rules, archetype rules, weakness map, and generated JSON wiring.
- [x] (2026-05-15) Added focused tests for top-level contract, section schema, taxonomy
  aggregation, risk budget, hidden flags, archetype caveats, weakness map, and degraded
  input status behavior.
- [x] (2026-05-15) Focused verification passed: `tests/test_portfolio_xray.py`
  and `tests/test_portfolio_commentary.py`, 9 passed.
- [x] (2026-05-15) Adjacent stress/factor verification passed:
  `tests/test_stress_mandate_pass.py`, `tests/test_stress_scenario_analytics.py`,
  and `tests/test_factor_variance_decomposition.py`, 21 passed.
- [x] (2026-05-15) Broad verification attempted. Sandbox full suite reported
  318 passed and 2 PermissionError failures when tests attempted to create generated
  directories under `output/codex_test_artifacts`; the two previously failing tests passed
  when rerun outside the sandbox.

## Surprises & Discoveries

- Observation: The current project already had a short `src/portfolio_xray.py` summary and
  report/commentary wiring, so v2 could be implemented as an additive diagnostic layer rather
  than a new report subsystem.
  Evidence: `src/snapshot.py` and `src/portfolio_commentary.py` already called the X-Ray
  formatter before this plan.

- Observation: `src/risk_budgeting.py` already exposes merged ETF/stock taxonomy rows and
  a risk-budget bucket mapper.
  Evidence: `load_merged_universe_rows` and `risk_budget_bucket_from_row` provide the
  taxonomy lookup needed for allocation breakdowns without adding a parallel parser.

- Observation: The default bundled Python for this session did not have `pytest` installed,
  while the project `.venv` did.
  Evidence: `C:\Users\ShumeikoYe\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest`
  failed with `No module named pytest`; `.venv\Scripts\python.exe -m pytest` ran the suite.

- Observation: Full-suite sandbox verification hit a filesystem permission issue unrelated
  to X-Ray code.
  Evidence: the full run reported 318 passed and 2 failures, both `PermissionError` creating
  `output/codex_test_artifacts/kalman` and `output/codex_test_artifacts/factor_png`; rerunning
  those exact two tests outside the sandbox passed.

## Decision Log

- Decision: Keep X-Ray v2 in `src/portfolio_xray.py` while preserving the legacy summary
  helper for compatibility.
  Rationale: Existing report writers and tests already depend on the module. Keeping both
  helpers avoids breaking the current short summary while adding the richer v2 artifact.
  Date/Author: 2026-05-15 / Codex

- Decision: Use a fixed top-level JSON contract with `version`, `diagnostic_only`,
  `diagnostic_only_disclaimer`, and `sections`.
  Rationale: Future consumers can immediately tell the artifact is diagnostic-only and can
  parse sections consistently.
  Date/Author: 2026-05-15 / User and Codex

- Decision: Centralize thresholds in `XRAY_THRESHOLDS`.
  Rationale: Hidden-risk and archetype rules must remain transparent, named, documented, and
  covered by tests; scattered inline thresholds would make the diagnostic opaque.
  Date/Author: 2026-05-15 / User and Codex

- Decision: The Weakness Map aggregates existing evidence only.
  Rationale: It should summarize stress losses, factor betas, RC_vol, drawdown/tail metrics,
  regime/macro diagnostics where available, and taxonomy metadata; it must not become a new
  forecasting or scoring model.
  Date/Author: 2026-05-15 / User and Codex

## Outcomes & Retrospective

Implemented. Portfolio X-Ray v2 now creates the generated `portfolio_xray.json` contract,
renders diagnostic-only X-Ray text in report and commentary surfaces, keeps hidden-risk and
archetype thresholds centralized, and preserves the legacy X-Ray summary helper. Focused and
adjacent tests passed. The full suite was attempted; the only sandbox failures were generated
artifact directory permission errors, and those specific tests passed outside the sandbox.

Focused validation:

    .venv\Scripts\python.exe -m pytest tests\test_portfolio_xray.py tests\test_portfolio_commentary.py -vv --basetemp=tmp\pytest_xray_v2
    9 passed

Adjacent validation:

    .venv\Scripts\python.exe -m pytest tests\test_stress_mandate_pass.py tests\test_stress_scenario_analytics.py tests\test_factor_variance_decomposition.py -vv --basetemp=tmp\pytest_xray_v2_stress
    21 passed

Broad validation attempt:

    .venv\Scripts\python.exe -m pytest -q --tb=short --basetemp=tmp\pytest_xray_v2_full
    318 passed, 2 failed due PermissionError creating output\codex_test_artifacts subdirectories

Previously failing tests rerun outside sandbox:

    .venv\Scripts\python.exe -m pytest tests\test_factor_beta_kalman.py::test_attach_kalman_factor_betas_preserves_raw_ols_fields tests\test_factor_matrix_builders.py::test_write_rolling_betas_plot_pngs_handles_nine_factors -vv --basetemp=tmp\pytest_xray_v2_failed_only
    2 passed

## Context and Orientation

The repository is a Python portfolio diagnostics and reporting system. The main report path
is `run_report.py`, which builds metrics, risk contribution, stress reports, snapshots, and
commentary. The generated report folder, commonly `Main portfolio/`, contains files such as
`stress_report.json`, `snapshot_10y.json`, `report.txt`, `report.html`, and `commentary.txt`.

`src/portfolio_xray.py` owns the X-Ray summary helpers. Before v2 it produced a short summary:
analyzed portfolio role, top capital concentration, top `RC_vol` concentration, main concern,
mandate gate, and stress status. `RC_vol` means percentage contribution to portfolio variance
from the existing risk-contribution pipeline. It is diagnostic-only.

`src/snapshot.py` writes `report.txt` and `report.html` from generated snapshots. It is the
right place to write `portfolio_xray.json` when report files are assembled from disk.
`src/portfolio_commentary.py` writes `commentary.txt` from in-memory report diagnostics. It
should render the same X-Ray v2 text but should not manually write generated JSON.

Taxonomy metadata comes from `config/etf_universe.yml` and `config/stock_universe.yml` through
the existing `src.risk_budgeting.load_merged_universe_rows` helper. Taxonomy is annotation-only:
it explains holdings but does not select assets or change weights.

## Plan of Work

Extend `src/portfolio_xray.py` with a v2 builder that accepts existing report diagnostics:
analysis setup, analyzed weights, `RC_vol`, stress report, portfolio metrics, portfolio
analytics, drawdown structure, and optional taxonomy rows. The builder returns a JSON-serializable
object with version, diagnostic-only disclaimer, centralized thresholds, and the seven sections:
asset allocation, risk diagnostics, factor exposure, hidden risk detector, portfolio archetype,
risk budget view, and weakness map.

Each section must have the same shape: `status`, `data_sources_used`, `warnings`, `items`, and
`limitations`. If inputs are missing, the section must be `partial` or `unavailable`; it must
not emit confident text that hides missing data.

Wire the v2 builder into `src/snapshot.py` so `write_report_txt` and `write_report_html` create
or refresh `portfolio_xray.json` and include the X-Ray v2 text in report surfaces. Wire it into
`src/portfolio_commentary.py` so commentary uses the same diagnostic-only wording.

Update `docs/specs/reporting_outputs_spec.md`, `OUTPUTS.md`, `SPEC.md`, `README.md`, and
`CHANGELOG.md` for the new generated artifact and diagnostic-only contract.

## Concrete Steps

From the repository root, run focused tests after implementation:

    python -m pytest tests/test_portfolio_xray.py tests/test_portfolio_commentary.py -vv

If report orchestration or stress references are affected, run:

    python -m pytest tests/test_stress_mandate_pass.py tests/test_stress_scenario_analytics.py tests/test_factor_variance_decomposition.py -vv

When focused tests pass, run the full suite:

    python -m pytest

## Validation and Acceptance

After `python run_report.py`, the output folder contains `portfolio_xray.json`. The JSON has:

    version = "portfolio_xray_v2"
    diagnostic_only = true
    diagnostic_only_disclaimer = diagnostic-only text
    sections.asset_allocation
    sections.risk_diagnostics
    sections.factor_exposure
    sections.hidden_risk_detector
    sections.portfolio_archetype
    sections.risk_budget_view
    sections.weakness_map

Every section has `status`, `data_sources_used`, `warnings`, `items`, and `limitations`.
`report.txt`, `report.html`, and `commentary.txt` include Portfolio X-Ray v2 text. Tests must
show that missing inputs produce `partial` or `unavailable`, taxonomy aggregation handles
unknown tickers, hidden-risk flags are traceable to evidence, archetype output includes
confidence and conflicting signals, and the weakness map uses existing evidence only.

## Idempotence and Recovery

The implementation is additive. Re-running `run_report.py` overwrites generated report files
and `portfolio_xray.json` in the output folder. If taxonomy, stress, factor, or RC inputs are
missing, the X-Ray builder returns degraded section statuses instead of raising or inventing
metrics. To recover from a bad report run, fix the source issue and rerun `python run_report.py`.

## Artifacts and Notes

Expected generated artifact:

    Main portfolio/portfolio_xray.json

The exact output folder follows `output_dir_final` and candidate report folder rules. Generated
outputs are not source files unless the task explicitly targets generated artifacts.

## Interfaces and Dependencies

Use existing project dependencies only. Do not add a new package.

In `src/portfolio_xray.py`, expose:

    PORTFOLIO_XRAY_VERSION = "portfolio_xray_v2"
    DIAGNOSTIC_ONLY_DISCLAIMER = "..."
    XRAY_THRESHOLDS = {...}

    def build_portfolio_xray_v2(
        *,
        analysis_setup: dict[str, Any] | None,
        weights: dict[str, Any] | None,
        rc_asset: Any,
        stress_report: dict[str, Any] | None,
        portfolio_valid: bool | None,
        portfolio_metrics: dict[str, Any] | None = None,
        portfolio_analytics: dict[str, Any] | None = None,
        drawdown_structure: dict[str, Any] | None = None,
        taxonomy_rows: dict[str, dict[str, Any]] | None = None,
        taxonomy_sources: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        ...

Keep the existing `build_portfolio_xray_summary` and `format_portfolio_xray_text` interfaces
working for compatibility. `format_portfolio_xray_text` must render both legacy summary objects
and v2 objects.

Revision note 2026-05-15: initial master ExecPlan created and kept in sync with the first
implementation pass.
