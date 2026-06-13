# Product Flow Operator Guide

**Single entry map** for operators and agents working the diagnosis-first product path.
Use this file before interpreting generated JSON or starting a new chat on product-flow work.

**Input Layer (frozen 2026-05-26):** [Input Layer MVP Migration](exec_plans/2026-05-26_input_layer_mvp_migration.md) closed; contract frozen — [audit](audits/2026-05-26_input_layer_mvp_acceptance_audit.md), `DEC-2026-05-26-001`. Do not reopen input redesign unless Block 1 regresses.

**Active product focus:** downstream of input - Portfolio X-Ray (Block 2), Stress Lab (Block 3), Problem Classification / Candidate Launchpad (Block 4), Portfolio Alternatives Builder (Block 6), one-attempt Candidate Generation (Block 7), Current vs Candidate (Block 8), Decision Verdict (Block 9), and AI Commentary grounding. Use this guide's read order and product-bundle chain; not more first-screen fields.
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
| 6 | `analysis_subject/portfolio_alternatives_builder.json` | Builder setup from one selected card; setup only, not weights or recommendation |
| 7 | `candidate_generation.json` | One Block 7 candidate attempt after explicit generation; candidate is not a recommendation |
| 8 | `current_vs_candidate.json` | Current vs selected candidate (Block 8) - **after compare only** |
| 9 | `decision_verdict.json` | Primary product answer: action / no-action / no-trade / evidence-insufficient framing (Block 9) - **after compare only** |
| 10 | `ai_commentary_context.json` | Grounding for future LLM prose - **not** client-facing copy - **after compare only** |
| 11 | `what_changed_summary.json` | Monitoring delta vs prior snapshot when available - **after compare only** (may be absent if no prior snapshot) |
| 12 | `output_manifest.json` -> `generated_paths` / `artifact_categories` | Resolved paths; confirms sidecar vs legacy root |
| 13 (drill-down only) | `candidate_comparison.json`, `selection_decision.json`, health/robustness/Pareto | Technical comparison and advanced evidence - not the default UI story |

Do **not** start from root `portfolio_xray.json` / `stress_report.json` unless the task is **legacy policy**
(`run_optimization.py`). Portfolio-first truth lives under `analysis_subject/`.

---

## Commands

`{output_dir_final}` is usually `Main portfolio/` from `config.yml`.

| Goal | Command | Notes |
| --- | --- | --- |
| **Product demo (one hypothesis)** | `python scripts/run_blocks_5_to_9_vertical_flow.py --method equal_weight` | Official Blocks 5-9 vertical path: selected Launchpad card -> Builder setup -> one candidate attempt -> compare -> verdict -> AI grounding. |
| Explicit backend candidate compatibility path | `python run_portfolio_review.py --candidates equal_weight` | Use only when you already know the factory id; this does not prove the Builder/Block 7 vertical artifact loop. |
| Dry-run compatibility plan | `python run_portfolio_review.py --candidates equal_weight --dry-run` | No builders; verify factory argv + `--then-compare` |
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


### Four operator commands for the staged journey

| Stage | Command | Read next |
| --- | --- | --- |
| Diagnose current portfolio | `python run_portfolio_review.py` | `analysis_subject/problem_classification.json`, then Launchpad and Builder setup |
| Generate one selected candidate | `python scripts/run_blocks_5_to_9_vertical_flow.py --method equal_weight` | `candidate_generation.json` |
| Compare / verdict from the same vertical run | Same vertical command, or technical Block 8 boundary `python run_compare_variants.py --block8-only --candidate equal_weight` after candidate evidence exists | `current_vs_candidate.json`, then `decision_verdict.json` |
| Full demo / regression path | `python scripts/run_blocks_5_to_9_vertical_flow.py --method equal_weight` | Full product bundle chain in the read order above |

`python run_portfolio_review.py --candidates equal_weight` remains a useful explicit factory-id
compatibility path, but it is not the canonical visible Builder-to-Block-7 handoff for demos. Its
runtime banner and dry-run summary intentionally say `Path classification: explicit factory-id
compatibility path`.

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

The Core MVP product-bundle chain is a set of separate JSON files, not one merged `product_bundle.json`. The vertical loop uses diagnosis artifacts, Builder setup, one candidate attempt, comparison, verdict, and grounding.
Paths are relative to `{output_dir_final}` (typically `Main portfolio/`).

| # | Artifact | Default path | When present | Schema (offline gate) | Primary reader question |
| --- | --- | --- | --- | --- | --- |
| 1 | `problem_classification.json` | `analysis_subject/problem_classification.json` | After default diagnosis / materialize | `problem_classification_v3` | What is wrong with the current portfolio... |
| 2 | `candidate_launchpad.json` | `analysis_subject/candidate_launchpad.json` | After default diagnosis / materialize | `candidate_launchpad_v3` | What hypotheses should we test next... |
| 3 | `portfolio_alternatives_builder.json` | `analysis_subject/portfolio_alternatives_builder.json` | After Launchpad when a primary card can be mapped | `portfolio_alternatives_builder_v1` | What setup would be tested if the user explicitly generates a candidate... |
| 4 | `candidate_generation.json` | `candidate_generation.json` | After explicit Generate Candidate / vertical demo | `candidate_generation_v1` | What one candidate attempt was created or why did it fail... |
| 5 | `current_vs_candidate.json` | `current_vs_candidate.json` | After Block 8 compare | `current_vs_candidate_v1` | How does current compare to the candidate... |
| 6 | `decision_verdict.json` | `decision_verdict.json` | After Block 9 verdict | `decision_verdict_v1` | Is action justified, or is no-trade / evidence-insufficient the right answer... |
| 7 | `ai_commentary_context.json` | `ai_commentary_context.json` | After verdict | `ai_commentary_context_v1` | Grounding only (`purpose=grounded_ai_commentary_context`; no LLM in V1) |
| 8 | `what_changed_summary.json` | `what_changed_summary.json` | After compare/monitoring; optional if no prior snapshot | `what_changed_summary_v1` | What changed since the last review... |

**RM-ARCH-011 sidecar rule:** diagnosis files **prefer** `analysis_subject/`; compare, AI commentary,
and What Changed resolve via `src/product_bundle_paths.py` (legacy root copies still work).

**Manifest keys:** `problem_classification_json` … `what_changed_summary_json` in
`output_manifest.json` → `generated_paths` / `product_discovery.product_bundle_paths`.
`product_discovery.product_bundle_phase` is `diagnosis_only` after default review (diagnosis, Launchpad, and Builder setup where available),
`complete` after compare/verdict/grounding, or `post_compare_partial` when some post-compare files exist.
`product_bundle_complete` is true only when phase is `complete`. `artifact_categories.product_bundle`
lists the product-bundle key names; resolved paths appear only for files on disk.

**Boundary wording for operators:** Builder setup is not a candidate; a generated candidate is not a recommendation; Equal Weight / Risk Parity reference tests are diagnostic comparisons, not rebalance recommendations; Decision Verdict is where action/no-action is evaluated. `no-trade` and `evidence_insufficient` are valid outcomes, not failures.

**Technical comparison** (same run, not bundle): `candidate_comparison.json`, `selection_decision.json`,
`portfolio_health_score.json`, `robustness_scorecard.json`, Pareto/regret, action plan, journal — see
[OUTPUTS.md](../OUTPUTS.md) § Runtime product flow.

---

## Anti-patterns

| Do not | Do instead |
| --- | --- |
| Use **Portfolio Health Score** or **robustness scorecard** as the main product answer | Lead with `decision_verdict.json` + `current_vs_candidate.json`; treat scores as supporting evidence |
| Start a Core MVP demo from `run_optimization.py`, `run_report.py`, or `run_mvp_workflow.py` | Start from `python run_portfolio_review.py` and read `analysis_subject/` first |
| Run `--with-candidates`, `--mode full`, or the factory-id compatibility path as the **canonical one-hypothesis demo** | `python scripts/run_blocks_5_to_9_vertical_flow.py --method <id>` for the staged Builder -> Block 7 -> compare -> verdict loop |
| Ignore a runtime banner that says compatibility, advanced/research, or legacy | Treat that path as support infrastructure; switch to the vertical Blocks 5-9 script for demo proof |
| Add `--candidate-method` on `run_portfolio_review.py` | `--candidates <factory_id>` only |
| Treat `ai_commentary_context.json` as finished client prose | Grounding stub; LLM is `RM-ARCH-010` / deferred |
| Read root policy `stress_report.json` / `portfolio_xray.json` after portfolio-first review | Open `analysis_subject/` copies first |
| Assume PDFs refreshed after routine review | Default `site_api` is JSON-only; use `--with-pdf` when PDFs matter |
| Trust `candidate_comparison.json` rankings without `candidate_menu` | Check `factory_evidence_status`, reuse warnings, optimizer `degraded` rows |
| Treat Alternatives Builder prefill or plan output as weights | Builder prefill is setup only; explicitly run factory/compare, then read verdict + bundle |
| Commit or cite gitignored `Main portfolio/` as spec proof | Session 07 live demo snapshot audit, or offline pytest fixtures |

---

## Launchpad method → one candidate (Alternatives Builder)

Candidate Launchpad cards suggest a diagnostic test or reference comparison. **Portfolio Alternatives
Builder** first consumes a selected card as Builder prefill: it copies the diagnosis, hypothesis,
success criteria, tradeoff, skip rule, method role, and decision boundary into setup fields. It does
not recommend a rebalance and does not generate candidates automatically.

If the user explicitly asks to generate a candidate, Builder can also return a
`PortfolioAlternativeBuildPlan` that delegates one selected `candidate_method_id` to existing factory
plumbing (`src/portfolio_alternatives_builder.py`).


### Builder prefill from a Launchpad card

Use `build_builder_prefill_from_launchpad_card(card, next_diagnostic_step=...)` when the UI or an
API consumer opens Builder from `analysis_subject/candidate_launchpad.json`.

| Prefill field | Operator meaning |
| --- | --- |
| `builder_mode` | `guided_from_diagnosis`, `monitor_only`, or `blocked_data_quality` for Launchpad-derived cards |
| `source_diagnosis_id` / `source_card_id` | Traceability back to Problem Classification and Launchpad |
| `hypothesis_to_test` / `success_criteria` | What the candidate or benchmark must prove to be useful |
| `suggested_method` / `alternative_methods` | Candidate method ids to show in Builder setup; no weights are created |
| `method_role` | `targeted_candidate_method` for diagnosis tests or `reference_benchmark` for EW/RP comparisons |
| `decision_boundary` | Must remain visible; actual rebalance decisions wait for compare + Decision Verdict |
| `candidate_generation_allowed` | Whether an explicit generate button may be shown; never auto-generation |

Data-quality and monitor cards should keep `candidate_generation_allowed: false`. Reference benchmark
cards may expose Equal Weight / Risk Parity as comparison methods only; do not describe them as a
recommended allocation.

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
    "card_type": "reference_benchmark_test",
    "is_rebalance_recommendation": False,
    "suggested_methods": [
        {"candidate_method_id": "equal_weight", "method_role": "reference_benchmark"}
    ],
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
| **Blocks 5-9 vertical demo** (recommended for product demo) | `python scripts/run_blocks_5_to_9_vertical_flow.py --method equal_weight` |
| **Factory-id compatibility path** (after diagnosis artifacts exist) | `python run_portfolio_review.py --candidates equal_weight` |
| **Factory + compare only** (technical, after diagnosis artifacts exist) | `python run_candidate_factory.py --candidates equal_weight --execution-mode standard --then-compare` |

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

---

## Block 4 v3 diagnosis (Problem Classification + Launchpad)

Shipped writer: `src/block_4/diagnosis_builder.py` → `write_block_4_diagnosis_outputs()` (called from `run_report.py` when not `core_blocks_only`).

| Step | Command | Pass criteria |
| --- | --- | --- |
| Refresh Block 4 on existing subject | `python scripts/validate_block_4_live.py --refresh-diagnosis` | `Block 4 v3 live validation: OK` |
| Contract bundle (offline) | `python -m pytest <all tests/test_block_4_*.py files> -q` | All pass |
| Diagnosis-only live gate (Block 4 evidence) | `python scripts/verify_live_core_e2e.py --profile diagnosis_only` | `block_4_schema_version=problem_classification_v3` in evidence (full gate may fail if compare tombstones missing) |

Read order after diagnosis:

1. `analysis_subject/problem_classification.json` -> `primary_diagnosis`: diagnosis thesis, root cause, confidence, materiality, actionability.
2. Same file -> `key_evidence` (maximum five): what proves or supports the diagnosis.
3. Same file -> `next_diagnostic_step`: what to test or fix next before any downstream verdict.
4. Same file -> `why_not_other_problems`: why similar labels were not selected as primary.
5. `analysis_subject/candidate_launchpad.json` -> cards with `hypothesis_to_test`, `card_type`, `launch_status`, `why_this_test`, `success_criteria`, `tradeoff_to_watch`, `when_to_skip`, and `decision_boundary`.

For `mixed_evidence_no_action` and `current_portfolio_acceptable`, Block 4 can say that no immediate rebalance is justified while still offering a reference comparison against Equal Weight and Risk Parity. These cards are `reference_benchmark_test` cards, not rebalance recommendations. If an actionable primary diagnosis exists, read the targeted card first; reference benchmark tests must not displace the targeted hypothesis.

Scoring rows are backend audit metadata, not the product answer. Spec: [block_4_diagnosis_v3_spec.md](specs/block_4_diagnosis_v3_spec.md).
| Doc link integrity | `python scripts/verify_docs.py` |

---

## Related registers

- ExecPlans: [docs/exec_plans/README.md](exec_plans/README.md)
- Audits: [docs/audits/README.md](audits/README.md)
- Backlog: `RM-ARCH-011` **Done** (2026-05-26, sidecar wiring + manifest keys); `RM-ARCH-010` (LLM commentary — deferred, ExecPlan Session 09)
