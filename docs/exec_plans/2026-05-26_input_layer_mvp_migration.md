# Input Layer MVP Migration

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`,
`Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document follows [PLANS.md](../../PLANS.md) in the repository root. A future contributor
should be able to continue this work from this file alone without prior chat context.

**Canonical spec (updated Session 01):** [docs/specs/input_assumptions_spec.md](../specs/input_assumptions_spec.md).

**Origin:** User-approved Input Layer redesign for «Diagnosis 2» Core MVP — diagnosis-first
product flow with minimal first-screen input (tickers, weights, investor currency).

## Purpose / Big Picture

Portfolio MRI / Portfolio X-Ray is a diagnosis-first decision-support product. The Input Layer
must not behave like an onboarding-heavy wealth-management form. After this migration, an
operator can run the Core MVP path (`python run_portfolio_review.py` and
`python run_portfolio_review.py --candidates equal_weight`) with only tickers, weights (or
`current_weights`), and `investor_currency` in config. The system resolves currency defaults
(risk-free source, cash proxy, benchmark, FX logic), treats explicit real cash (for example
`Cash USD`) as a zero-return portfolio holding, and defers client goals, liquidity floors,
mandate caps, and technical run settings to later layers or legacy/advanced paths.

The observable outcome is that `validate_config` and product review accept minimal USD configs
without `client_profile`, liquidity fields, `portfolio_value`, or manually set benchmark/RF,
while `run_metadata.json` still exposes full `analysis_setup` and explanatory `input_assumptions`
for Block 1 acceptance checks in [OUTPUTS.md](../../OUTPUTS.md).

## Progress

- [x] (2026-05-26) Read `PLANS.md`, current [input_assumptions_spec.md](../specs/input_assumptions_spec.md), [ARCHITECTURE.md](../../ARCHITECTURE.md) §4.1, audit notes from Input Layer planning chat.
- [x] (2026-05-26) **Session 01 — Contract & spec foundation:** Rewrote spec sections 1.1–1.6, Real Cash Holdings rule, field classification table; created this ExecPlan; registered plan as **Active** in [docs/exec_plans/README.md](README.md).
- [x] (2026-05-26) **Session 02 — MVP input normalization:** `apply_mvp_input_defaults` in `src/mvp_input.py`; wired into `validate_config`; tests in `tests/test_mvp_input_defaults.py`.
- [x] (2026-05-26) **Session 03 — Real cash holdings:** `src/real_cash.py`; pipeline/metrics/analysis_setup; `tests/test_real_cash.py`.
- [x] (2026-05-26) **Session 04 — Config surface & fixtures:** `tests/fixtures/mvp_portfolios/minimal_usd_no_cash.yml`, `minimal_usd_with_cash.yml`; restructure `config.yml.example` MVP-first; slim demo `config.yml`; `tests/test_mvp_portfolio_fixtures.py`.
- [x] (2026-05-26) **Session 05 — config_ui MVP first screen:** three-field panel + advanced collapse in `config_ui/`.
- [x] (2026-05-26) **Session 06 — Export & disclosure:** `input_surface`, `field_tiers` in `src/input_assumptions.py`.
- [x] (2026-05-26) **Session 07 — Portfolio review integration:** updated `tests/mvp_offline_fixtures.py`; `tests/test_mvp_portfolio_review_materialization.py`.
- [x] (2026-05-26) **Session 08 — Regression suite:** `tests/test_input_layer_mvp_regression.py`.
- [x] (2026-05-26) **Session 09 — Documentation sweep:** README, SPEC, WORKFLOW, OUTPUTS, GLOSSARY, product operator guide; `verify_docs.py` OK.
- [x] (2026-05-26) **Session 10 — Acceptance report:** live dry-run, live materialize (Block 1), `validate_one_candidate_demo.py` PASS, pytest 36 passed, [acceptance audit](../audits/2026-05-26_input_layer_mvp_acceptance_audit.md).

## Surprises & Discoveries

- Observation: Config validation already requires only `investor_currency` and `tickers` in `REQUIRED_FIELDS`; many “onboarding” fields are optional with defaults.
  Evidence: `src/config_schema.py` `REQUIRED_FIELDS`; `validate_config` defaults for `liquidity_need_months`, `client_profile`, etc.

- Observation: Without explicit `analysis_subject`, `resolve_analysis_subject()` defaults to `universe_baseline`, not user current portfolio — minimal weights-only YAML does not yet match product intent.
  Evidence: `src/analysis_setup.py` `resolve_analysis_subject()` final branch.

- Observation: Real cash labels (`Cash USD`) are not implemented; cash handling tracks `cash_proxy_ticker` weight only.
  Evidence: grep for `Cash USD` / `real_cash` in `src/` returns no implementation (Session 03 target).

- Observation: Validation fixtures will use tickers/weights from root `config.yml` (8-ticker USD portfolio), not external “sticker” files (none exist in repo).
  Evidence: user clarification 2026-05-26; Session 04 fixture plan.

## Decision Log

- Decision: Core MVP first-screen input is exactly three user-facing groups: tickers, weights/`current_weights`, `investor_currency`.
  Rationale: User brief and «Diagnosis 2» product flow start with portfolio diagnosis, not mandate building.
  Date/Author: 2026-05-26 / user + agent.

- Decision: `analysis_subject.type=current_portfolio` and `analysis_mode=analyze_current_weights` are system-internal for Core MVP when the user supplies weights; not first-screen fields.
  Rationale: Reduces UI/config noise; implementation injects these in Session 02.
  Date/Author: 2026-05-26 / agent.

- Decision: Normative real-cash rule is spec-bound: explicit user cash is a holding (0% return, 0 vol, 0 drawdown, no price series); `cash_proxy_ticker` is never a substitute.
  Rationale: Prevents conflating BIL/PEU technical proxy with client bank cash.
  Date/Author: 2026-05-26 / user + agent.

- Decision: Keep legacy `run_optimization.py` and full config schema fields; reclassify tiers in spec rather than delete keys in Session 01.
  Rationale: Staged migration; optimizer and research batch still need mandate/liquidity fields.
  Date/Author: 2026-05-26 / agent.

- Decision: USD-only validation fixtures for migration tests; EUR explicit cash/RF paths unchanged but not in fixture scope.
  Rationale: User instruction.
  Date/Author: 2026-05-26 / user.

## Outcomes & Retrospective

**Session 01 (2026-05-26):** Spec and ExecPlan foundation complete.

**Session 02 (2026-05-26):** `src/mvp_input.py` + `validate_config` hook inject `current_portfolio` / `analyze_current_weights` when user supplies `current_weights` or non-generated `weights` without explicit `analysis_subject.type`. Tests: `tests/test_mvp_input_defaults.py`; updated `tests/test_input_assumptions.py` for MVP preflight and summary expectations.

**Session 03 (2026-05-26):** `src/real_cash.py`; `data_loader` skips price download and injects zero-return columns; `analysis_setup.cash_handling` exposes `real_cash_holdings`; taxonomy preflight and `get_risk_portfolio_tickers` exclude real-cash labels. Tests: `tests/test_real_cash.py`.

**Session 04 (2026-05-26):** MVP YAML fixtures under `tests/fixtures/mvp_portfolios/`; `config.yml.example` reordered MVP-first (Sections 1–7); demo `config.yml` slimmed to Core MVP fields plus technical run settings; `tests/test_mvp_portfolio_fixtures.py`.

**Session 05 (2026-05-26):** `config_ui` Core MVP first screen (currency + holdings + collapsed Advanced); compact MVP YAML on save; `/run-portfolio-review` endpoint; tests `tests/test_config_ui_mvp_first_screen.py`; updated `tests/test_config_ui_input_modes.py` and `docs/specs/input_assumptions_spec.md`.

**Session 06 (2026-05-26):** `build_input_surface` and `build_field_tiers` in `src/input_assumptions.py`; exported on every `input_assumptions_v1` projection; spec sections for `input_surface` / `field_tiers`; tests extended in `tests/test_input_assumptions.py`.

**Session 07 (2026-05-26):** `tests/mvp_offline_fixtures.py` aligned with Core MVP (`current_weights`, fixture loaders, `build_offline_run_metadata`); `tests/test_mvp_portfolio_review_materialization.py` covers materialization + `build_portfolio_review_plan` for MVP YAML fixtures.

**Session 08 (2026-05-26):** `tests/test_input_layer_mvp_regression.py` — offline regression gate for three-field fixtures, USD defaults, disclosure chain, real cash, product runtime modes, and six-file product bundle after one-candidate compare.

**Session 09 (2026-05-26):** Documentation sweep — [README.md](../../README.md) Key Inputs and Core MVP scope; [SPEC.md](../../SPEC.md) Inputs § and product status matrix; [WORKFLOW.md](../../WORKFLOW.md) portfolio-first checklist step 1; [OUTPUTS.md](../../OUTPUTS.md) Block 1 acceptance + regression pointer; [GLOSSARY.md](../../GLOSSARY.md) Core MVP input surface, real cash, `input_surface`, `field_tiers`; [product_flow_operator_guide.md](../product_flow_operator_guide.md) Core MVP config section and verification commands.

**Session 10 (2026-05-26):** Acceptance closed — diagnosis and one-candidate dry-runs exit 0; live `run_report.py --materialize-analysis-subject` refreshed Block 1 disclosure (`input_surface` = `core_mvp`); `validate_one_candidate_demo.py` PASS; Input Layer pytest bundle **36 passed**; `verify_docs.py` OK. Evidence: [2026-05-26_input_layer_mvp_acceptance_audit.md](../audits/2026-05-26_input_layer_mvp_acceptance_audit.md). **ExecPlan closed.**

**Post-closure (2026-05-26):** Full live `run_portfolio_review.py --candidates equal_weight` + validator PASS recorded in audit §5. Input contract **frozen** (`DEC-2026-05-26-001`, spec § Contract freeze). **Do not reopen** except bug fixes. **Next work:** downstream product layers (Blocks 2–5), not input redesign.

## Context and Orientation

The repository is CLI/file-driven. Primary config is root `config.yml`. Portfolio-first entrypoint
is `run_portfolio_review.py`, which materializes `analysis_subject` via
`run_report.py --materialize-analysis-subject` before optional candidate factory and compare.

Key modules today:

| Module | Role |
| --- | --- |
| [src/config_schema.py](../../src/config_schema.py) | `validate_config`, `PortfolioConfig`, `REQUIRED_FIELDS` |
| [src/config.py](../../src/config.py) | `resolve_cash_and_rf`, currency defaults |
| [src/analysis_setup.py](../../src/analysis_setup.py) | `build_analysis_setup`, `resolve_analysis_subject` |
| [src/input_assumptions.py](../../src/input_assumptions.py) | Export projection from `analysis_setup` |
| [config_ui/app.py](../../config_ui/app.py) | Core MVP first screen + collapsed Advanced (Session 05) |

Product bundle outputs (unchanged by Input Layer): six JSON files under `{output_dir_final}/`
per [docs/product_flow_operator_guide.md](../product_flow_operator_guide.md).

## Plan of Work (sessions)

### Session 01 — Contract & spec foundation (this session)

Update [input_assumptions_spec.md](../specs/input_assumptions_spec.md) with sections 1.1–1.6,
Real Cash Holdings, field tiers, Core MVP input surface. Create this ExecPlan. Register Active
pointer in [README.md](README.md). Run `python scripts/verify_docs.py`.

**Acceptance:** Spec states Core MVP = 3 fields; real-cash rule is normative; `input_assumptions`
remains export-only; ExecPlan lists Sessions 02–10.

### Session 02 — MVP input normalization

Add `apply_mvp_input_defaults(raw)` called from `validate_config` before subject validation.
When user supplies positive `current_weights` or non-generated top-level `weights` without
explicit `analysis_subject`, inject `current_portfolio` + `analyze_current_weights`.

**Files:** `src/analysis_setup.py` or new `src/mvp_input.py`, `src/config_schema.py`,
`tests/test_mvp_input_defaults.py`.

**Acceptance:** `validate_config({"investor_currency":"USD","tickers":[...],"current_weights":{...}})`
yields `analysis_subject.type=current_portfolio`.

### Session 03 — Real cash holdings

Implement `src/real_cash.py`; skip price download for cash labels; zero return column; extend
`analysis_setup.cash_handling`; taxonomy preflight allows real-cash tickers.

**Acceptance:** `tests/test_real_cash.py` — `Cash USD` not replaced by BIL.

### Session 04 — Config & fixtures

`tests/fixtures/mvp_portfolios/minimal_usd_no_cash.yml` and `minimal_usd_with_cash.yml` from
root `config.yml` tickers/weights. Restructure `config.yml.example` MVP-first.

### Sessions 05–10

See Progress checklist above; full detail in migration plan chat artifact
`input_layer_mvp_migration_68b678af.plan.md` (Cursor plans).

## Validation (end state)

From repository root (after Session 08+):

    python -m pytest tests/test_mvp_portfolio_fixtures.py tests/test_mvp_input_defaults.py tests/test_real_cash.py tests/test_input_layer_mvp_regression.py -q --basetemp=tmp/pytest_input_mvp
    python scripts/verify_docs.py
    python run_portfolio_review.py --dry-run
    python run_portfolio_review.py --dry-run --candidates equal_weight

Session 01 only requires:

    python scripts/verify_docs.py

## Acceptance Criteria (full migration)

1. First-screen / Core MVP config requires only tickers, weights or `current_weights`, and `investor_currency`.
2. Real cash holdings follow the normative rule in the spec; cash proxy does not substitute.
3. USD defaults for RF, cash proxy, and benchmark without user entry.
4. Client profile, liquidity, mandate caps, and portfolio value are not required for `run_portfolio_review` diagnosis path.
5. Technical assumptions remain backend defaults, not user-required for Core MVP.
6. Fixtures `minimal_usd_no_cash` and `minimal_usd_with_cash` pass validation and tests.
7. `product_diagnosis_only` and `product_one_candidate` runtime modes unchanged.
8. Six product bundle JSON contracts still produced on compare runs.
9. Documentation matches code.
10. Targeted pytest suites pass.

## Risks and Legacy Coupling

| Risk | Mitigation |
| --- | --- |
| Legacy `optimize_from_universe` default in schema | Session 02 injection only when weights present; keep explicit subject override |
| `config_ui` legacy full form | Mitigated Session 05 — Advanced collapse; MVP path is default |
| Optimizer still reads `client_profile` / liquidity | Tier `legacy_advanced`; not removed |
| Taxonomy preflight rejects unknown tickers | Session 03 exempt real-cash labels |
| Partial weights vs `Cash USD` | `weight_status` + real cash; document in spec |
