# Product Flow Operator Guide

**Single entry map** for operators and agents working the diagnosis-first product path.
Use this file before interpreting generated JSON or starting a new chat on product-flow work.

**Input Layer (frozen 2026-05-26):** [Input Layer MVP Migration](exec_plans/2026-05-26_input_layer_mvp_migration.md) closed; contract frozen — [audit](audits/2026-05-26_input_layer_mvp_acceptance_audit.md), `DEC-2026-05-26-001`. Do not reopen input redesign unless Block 1 regresses.

**Active product focus:** downstream of input — Portfolio X-Ray (Block 2), Stress Lab (Block 3), Problem Classification / Candidate Launchpad (Block 4), compare and verdict adapters (Blocks 4–5). Use this guide’s read order and six-file bundle; not more first-screen fields.
**Product-flow backend (closed):** [Product Flow MVP Backend ExecPlan](exec_plans/2026-05-25_product_flow_mvp_backend_plan.md).
**Origin audit:** [Product-Flow Validation Audit](audits/2026-05-25_product_flow_validation_audit.md).

Canonical contracts: [SPEC.md](../SPEC.md), [OUTPUTS.md](../OUTPUTS.md) (§ Runtime product flow),
[input_assumptions_spec.md](specs/input_assumptions_spec.md) (§ Core MVP Input Surface),
[portfolio_review_workflow_spec.md](specs/portfolio_review_workflow_spec.md).
Runbook: [operational_runbook.md](operational_runbook.md#product-demo-one-candidate).

---

## Core MVP config (before any command)

Portfolio-first runs need only three user-facing groups in root `config.yml`:

| Group | Keys | Notes |
| --- | --- | --- |
| Instruments | `tickers` | ETFs/stocks; add `Cash USD` (or equivalent) for explicit bank cash |
| Allocation | `current_weights` (preferred) or `weights` | Positive map; sum ≤ 1.0; partial sum = cash remainder diagnostic |
| Currency | `investor_currency` | `USD` / `EUR` get RF, cash proxy, benchmark defaults when omitted |

Copy from `config.yml.example` Section 1 or fixtures under `tests/fixtures/mvp_portfolios/`.
`client_profile`, liquidity, `portfolio_value`, and mandate caps are **not** required for
`run_portfolio_review.py`. Optional web editor: `python config_ui/app.py` (three fields + Advanced).

After validation, open `analysis_subject/run_metadata.json` → `analysis_setup.core_mvp_input_surface`
and `input_assumptions.core_mvp_input_contract` for the minimal Core MVP product input contract.
Use `input_assumptions.input_surface` and `field_tiers` only as disclosure of system-resolved,
deferred, and legacy/advanced fields. Real cash must appear in
`analysis_setup.cash_handling.real_cash_holdings`, not as a substitute for `cash_proxy_ticker`.

---

## Recommended read order

Read in this order after a portfolio-first run (new chat, demo prep, or code review of outputs):

| Step | What to open | Why |
| --- | --- | --- |
| 1 | `{output_dir_final}/analysis_subject/run_metadata.json` | Subject type, weights source, `analysis_setup.core_mvp_input_surface` / `input_assumptions.core_mvp_input_contract`, analysis window |
| 2 | `analysis_subject/portfolio_xray.json` | Blocks 1–2 diagnostics; prefer product blocks `block_2_1_asset_allocation` through `block_2_6_portfolio_weakness_map` when present (§2.1.1–§2.6.1 in [portfolio_xray_diagnostics_spec.md](specs/portfolio_xray_diagnostics_spec.md)); legacy seven sections remain for full X-Ray formatters |
| 3 | `analysis_subject/stress_report.json` | Block 3 stress scenarios and factor context |
| 4 | `analysis_subject/problem_classification.json` | Top problems and test paths (product bundle #1) |
| 5 | `analysis_subject/candidate_launchpad.json` | Suggested hypotheses / methods (product bundle #2) |
| 6 | `current_vs_candidate.json` | Current vs selected or shortlist (product bundle #3) — **after compare only** |
| 7 | `decision_verdict.json` | Primary product answer: hold / adjust / no-trade framing (bundle #4) — **after compare only** |
| 8 | `ai_commentary_context.json` | Grounding for future LLM prose — **not** client-facing copy (bundle #5) — **after compare only** |
| 9 | `what_changed_summary.json` | Monitoring delta vs prior snapshot when available (bundle #6) — **after compare only** (may be absent if no prior snapshot) |
| 10 | `output_manifest.json` → `generated_paths` / `artifact_categories` | Resolved paths; confirms sidecar vs legacy root |
| 11 (drill-down only) | `candidate_comparison.json`, `selection_decision.json`, health/robustness/Pareto | Technical comparison and advanced evidence — not the default UI story |

Do **not** start from root `portfolio_xray.json` / `stress_report.json` unless the task is **legacy policy**
(`run_optimization.py`). Portfolio-first truth lives under `analysis_subject/`.

---

## Commands

`{output_dir_final}` is usually `Main portfolio/` from `config.yml`.

| Goal | Command | Notes |
| --- | --- | --- |
| **Product demo (one hypothesis)** | `python run_portfolio_review.py --candidates equal_weight` | Official MVP path; workflow `one_candidate`. Swap id per Launchpad. |
| Dry-run demo plan | `python run_portfolio_review.py --candidates equal_weight --dry-run` | No builders; verify factory argv + `--then-compare` |
| Routine diagnosis-first review | `python run_portfolio_review.py` | Default product runtime; diagnosis-only (`analysis_subject/`), no factory, no compare |
| Explicit diagnosis only | `python run_portfolio_review.py --skip-candidates` | Same diagnosis-only behavior as default; explicit flag for clarity in scripts |
| Backend candidate batch (advanced/research) | `python run_portfolio_review.py --with-candidates` | Runs candidate factory batch with resolved profile (`core_fast`) and compare |
| Full candidate menu (advanced/research) | `python run_portfolio_review.py --mode full` | Runs `default_v1` full menu and compare |
| Legacy policy runtime (compatibility-only) | `python run_optimization.py`, `python run_report.py`, or `python run_mvp_workflow.py --workflow ...` | Keep callable for historical/policy workflows; not Core MVP default product runtime |
| Factory + compare (subject already on disk) | `python run_candidate_factory.py --candidates equal_weight --execution-mode standard --then-compare` | Same factory id as review `--candidates` |
| Launchpad method → command (print) | `python scripts/run_one_candidate_from_method.py --method equal_weight` | Optional; `--run` executes factory only |
| Offline regression (no network) | `python -m pytest tests/test_product_bundle_integration.py tests/test_product_bundle_paths.py -q --basetemp=tmp/pytest_product_bundle` | See [TESTING.md](../TESTING.md) |
| One-candidate demo gate (after live run) | `python scripts/validate_one_candidate_demo.py` | Session 07; see [runtime truth Session 07 audit](audits/2026-05-26_runtime_truth_session07_one_candidate_validation.md) |
| Runtime truth closure (Sessions 01–09) | `python scripts/verify_docs.py`; `pytest tests/test_runtime_mode_regression_boundaries.py -q` | [Final runtime truth audit](audits/2026-05-26_runtime_truth_final_audit.md) |

Replace `equal_weight` with any supported factory id (`risk_parity`, `minimum_variance`, …).
Method allowlist: `supported_candidate_methods()` in `src/portfolio_alternatives_builder.py`.

### Runtime labels (`--dry-run`)

Use dry-run to confirm stages before a long networked run. Labels come from
`summarize_plan()` (`src/portfolio_review_workflow.py`).

| Command | `runtime_mode` | `workflow_state` | Stages |
| --- | --- | --- | --- |
| `python run_portfolio_review.py --dry-run` | `product_diagnosis_only` | `diagnosis_only` | `input -> diagnosis` |
| `... --candidates equal_weight --dry-run` | `product_one_candidate` | `one_candidate` | `input -> diagnosis -> candidates` |
| `... --with-candidates --dry-run` | `research_batch` | `multiple_candidates` (6) | `input -> diagnosis -> candidates` |
| `... --mode full --dry-run` | `research_batch` | `multiple_candidates` (16) | `input -> diagnosis -> candidates` |

Full decision tree and transcript examples:
[portfolio_review_workflow_spec.md](specs/portfolio_review_workflow_spec.md) (Runtime mode and command decision tree).

---

## Product bundle path map

Six JSON files form the **Core MVP product bundle**. There is **no** merged `product_bundle.json`.
Paths are relative to `{output_dir_final}` (typically `Main portfolio/`).

| # | Artifact | Default path | When present | Schema (offline gate) | Primary reader question |
| --- | --- | --- | --- | --- | --- |
| 1 | `problem_classification.json` | `analysis_subject/problem_classification.json` | After default diagnosis / materialize | `problem_classification_v1` | What is wrong with the current portfolio? |
| 2 | `candidate_launchpad.json` | `analysis_subject/candidate_launchpad.json` | After default diagnosis / materialize | `candidate_launchpad_v1` | What hypotheses should we test next? |
| 3 | `current_vs_candidate.json` | `current_vs_candidate.json` | After `--candidates`, `--with-candidates`, or `--mode full` (compare stage) | `current_vs_candidate_v1` | How does current compare to the candidate? |
| 4 | `decision_verdict.json` | `decision_verdict.json` | Same as #3 | `decision_verdict_v1` | What is the recommended decision posture? |
| 5 | `ai_commentary_context.json` | `ai_commentary_context.json` | Same as #3 | `ai_commentary_context_v1` | Grounding only (`purpose=grounded_ai_commentary_context`; no LLM in V1) |
| 6 | `what_changed_summary.json` | `what_changed_summary.json` | Same as #3; file optional if no prior snapshot | `what_changed_summary_v1` | What changed since the last review? |

**RM-ARCH-011 sidecar rule:** diagnosis files **prefer** `analysis_subject/`; compare, AI commentary,
and What Changed resolve via `src/product_bundle_paths.py` (legacy root copies still work).

**Manifest keys:** `problem_classification_json` … `what_changed_summary_json` in
`output_manifest.json` → `generated_paths` / `product_discovery.product_bundle_paths`.
`product_discovery.product_bundle_phase` is `diagnosis_only` after default review (#1–2 only),
`complete` after compare (all six), or `post_compare_partial` when some post-compare files exist.
`product_bundle_complete` is true only when phase is `complete`. `artifact_categories.product_bundle`
lists all six key names; resolved paths appear only for files on disk.

**Technical comparison** (same run, not bundle): `candidate_comparison.json`, `selection_decision.json`,
`portfolio_health_score.json`, `robustness_scorecard.json`, Pareto/regret, action plan, journal — see
[OUTPUTS.md](../OUTPUTS.md) § Runtime product flow.

---

## Anti-patterns

| Do not | Do instead |
| --- | --- |
| Use **Portfolio Health Score** or **robustness scorecard** as the main product answer | Lead with `decision_verdict.json` + `current_vs_candidate.json`; treat scores as supporting evidence |
| Start a Core MVP demo from `run_optimization.py`, `run_report.py`, or `run_mvp_workflow.py` | Start from `python run_portfolio_review.py` and read `analysis_subject/` first |
| Run `--with-candidates` or `--mode full` for a **one-hypothesis demo** | `python run_portfolio_review.py --candidates <id>` |
| Add `--candidate-method` on `run_portfolio_review.py` | `--candidates <factory_id>` only |
| Treat `ai_commentary_context.json` as finished client prose | Grounding stub; LLM is `RM-ARCH-010` / deferred |
| Read root policy `stress_report.json` / `portfolio_xray.json` after portfolio-first review | Open `analysis_subject/` copies first |
| Assume PDFs refreshed after routine review | Default `site_api` is JSON-only; use `--with-pdf` when PDFs matter |
| Trust `candidate_comparison.json` rankings without `candidate_menu` | Check `factory_evidence_status`, reuse warnings, optimizer `degraded` rows |
| Treat Alternatives Builder plan output as weights | Run factory/compare; read verdict + bundle |
| Commit or cite gitignored `Main portfolio/` as spec proof | Session 07 live demo snapshot audit, or offline pytest fixtures |

---

## Launchpad method → one candidate (Alternatives Builder)

Candidate Launchpad cards suggest a `candidate_method_id` (for example `equal_weight` on a
diversification card). **Portfolio Alternatives Builder** does not run optimizers itself; it returns
a `PortfolioAlternativeBuildPlan` that delegates to existing factory plumbing
(`src/portfolio_alternatives_builder.py`).

### `PortfolioAlternativeBuildPlan` fields

| Field | Meaning |
| --- | --- |
| `candidate_method_id` | Launchpad / UI method id (allowlisted) |
| `candidate_id` | Factory registry id (usually identical in V1) |
| `command` | argv tuple for `run_candidate_factory.py` (plan only until executed) |
| `artifact_contract` | Expected JSON after run (`candidate_factory_run.json`, `candidate_comparison.json` when `--then-compare`) |
| `provenance` | Delegation metadata (`delegates_to`, `does_not_change_formulas`, …) |
| `warnings` | e.g. `request_parameters_recorded_not_applied_v1` when optional request fields are not applied in V1 |

### Example: `equal_weight` from Launchpad

Given a card whose first suggested method is `equal_weight`:

```python
from pathlib import Path
from src.portfolio_alternatives_builder import (
    request_from_launchpad_card,
    build_portfolio_alternative_plan,
)

card = {
    "card_id": "launchpad_demo_equal_weight",
    "goal": "Simple diversification baseline",
    "suggested_methods": [{"candidate_method_id": "equal_weight"}],
}
request = request_from_launchpad_card(card, method_index=0)
plan = build_portfolio_alternative_plan(request, project_root=Path("."))
# plan.candidate_id == "equal_weight"
# plan.command → run_candidate_factory.py --candidates equal_weight ...
```

### Equivalent manual commands (no new review CLI flags)

Use **either** path; both end at one factory id and compare.

| Path | Command |
| --- | --- |
| **Full portfolio-first review** (recommended for demo) | `python run_portfolio_review.py --candidates equal_weight` |
| **Factory + compare only** (after diagnosis artifacts exist) | `python run_candidate_factory.py --candidates equal_weight --execution-mode standard --then-compare` |

The builder’s default plan also passes `--output-profile site_api` (JSON-first artifacts). That
matches routine portfolio-first output; it is safe to omit on manual factory runs only when you
accept factory defaults.

Dry-run the review path:

```bash
python run_portfolio_review.py --candidates equal_weight --dry-run
```

Pass criteria: workflow state `one_candidate`; factory step includes `--candidates equal_weight` and
`--then-compare`.

### Helper script (optional)

From a Launchpad `candidate_method_id` without writing Python:

```bash
python scripts/run_one_candidate_from_method.py --method equal_weight
python scripts/run_one_candidate_from_method.py --method equal_weight --run
```

`--run` executes the builder’s factory command (network + disk). Default is print-only.

### Method allowlist

V1 maps product-facing method ids to factory ids 1:1. Supported methods:
`supported_candidate_methods()` in `src/portfolio_alternatives_builder.py` (see
[portfolio_alternatives_builder_spec.md](specs/portfolio_alternatives_builder_spec.md#v1-method-mapping)).

Unknown methods raise `PortfolioAlternativesBuilderError: unsupported_candidate_method:<id>`.

---

## Verification quick reference

| Check | Command |
| --- | --- |
| Input Layer MVP regression (offline) | `python -m pytest tests/test_input_layer_mvp_regression.py tests/test_mvp_input_defaults.py tests/test_real_cash.py tests/test_mvp_portfolio_fixtures.py -q --basetemp=tmp/pytest_input_mvp` |
| Bundle offline gate | `python -m pytest tests/test_product_bundle_integration.py -q --basetemp=tmp/pytest_product_bundle` |
| Sidecar path resolvers | `python -m pytest tests/test_product_bundle_paths.py -q` |
| One-candidate workflow wiring | `python -m pytest tests/test_portfolio_review_workflow.py -q -k one_candidate` |
| Launchpad → documented commands | `python -m pytest tests/test_portfolio_alternatives_builder.py -q -k launchpad_method` |
| Doc link integrity | `python scripts/verify_docs.py` |

---

## Related registers

- ExecPlans: [docs/exec_plans/README.md](exec_plans/README.md)
- Audits: [docs/audits/README.md](audits/README.md)
- Backlog: `RM-ARCH-011` **Done** (2026-05-26, sidecar wiring + manifest keys); `RM-ARCH-010` (LLM commentary — deferred, ExecPlan Session 09)
