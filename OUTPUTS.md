# OUTPUTS.md

This file is the root map for generated outputs, report artifacts, output folders, and output-format ownership in Portfolio MRI / Portfolio X-Ray.

It explains what the project creates, where it is written, which formats are used, which files are source vs generated, and which detailed specs own the behavior. It does not replace metric formulas, stress logic, scenario definitions, or implementation contracts.

Update this file when output folders, artifact names, formats, report sections, generated-vs-source boundaries, visual/report packaging, or output-producing workflows change.

## Core Rule

Generated outputs are evidence and deliverables, not source files, unless a task explicitly targets generated artifacts.

Source files define behavior. Generated files show the result of a run.

The canonical current product truth is **ДИАГНОСТИКА 2**. Output interpretation must follow this product boundary:

```text
Input portfolio
-> Portfolio X-Ray
-> Stress Test Lab
-> Problem Classification
-> Candidate Launchpad
-> Portfolio Alternatives Builder
-> Candidate Generation
-> Current vs Candidate Comparison
-> Decision Verdict
-> AI Commentary / grounding
-> Monitoring / What Changed
```

Only the diagnosis-first decision bundle listed below, the Block 6 Builder setup artifact, and the explicit Block 7 `candidate_generation.json` attempt artifact are the current Core MVP product-facing output layer. Portfolio Alternatives Builder writes `portfolio_alternatives_builder.json` under `analysis_subject/` after Launchpad; it is setup state, not a generated portfolio. Candidate Generation writes one candidate attempt only and is not a rebalance recommendation. Older/generated artifacts such as Health Score, Robustness Scorecard, Selection Engine outputs, Action Plan, Decision Journal, macro dashboards, full candidate arenas, sensitivity/Pareto/regret, and PDF/report packages may exist, but they are advanced/backend/legacy/generated support unless a task explicitly targets them.

Documentation migration records such as `DOCUMENTATION_MIGRATION_PLAN.md`, `DOCUMENTATION_MIGRATION_SESSION09_AUDIT.md`, and archived legacy Markdown files are source/planning documents, not generated run outputs. They do not define output contracts.

Default execution is now site/API-first: JSON contracts and required cache are the machine-readable
source of truth for new workflows. CSV, TXT, HTML, PNG, PDF, Markdown PDF sidecars, and CSS/visual
presentation assets are export/report artifacts only and must be requested explicitly through
`full_report`, `legacy_export`, or PDF export commands. CSV exporters remain supported for audit,
Excel review, debugging, and legacy reporting, but CSV is not produced by default.

## Read this first

When `{output_dir_final}` is `Main portfolio/` (typical), **two artifact trees coexist**. They describe
**different portfolios** — do not merge them when interpreting a portfolio-first review.

| Location | Meaning | Authoritative for |
| --- | --- | --- |
| `{output_dir_final}/analysis_subject/` | Portfolio-first **subject** diagnosed before candidates | Starting weights, Blocks 1–3 diagnostics (X-Ray, stress, snapshots, `run_metadata.json`) for the reviewed portfolio |
| `{output_dir_final}/` root — `run_result.json`, `portfolio_weights.yml`, root `portfolio_xray.json`, `stress_report.json`, `run_metadata.json` | **Legacy policy optimization** (`run_optimization.py`, optionally `--with-report`) | Policy release checks and historical policy runs only — **not** the portfolio-first subject |

**Operator rules:**

1. After `python run_portfolio_review.py`, open **`analysis_subject/` first**; candidate comparison uses that baseline.
2. Do **not** mix subject weights/diagnostics with root policy weights or root stress/X-Ray files.
3. Default `site_api` review writes **JSON + cache only**. TXT, HTML, PNG, CSV under `analysis_subject/` or variant folders, and PDFs under `pdf files/`, may be **stale** from earlier export runs unless you explicitly requested `--with-pdf`, `--legacy-full-pdf`, or `--output-profile full_report` / `legacy_export`.
4. `candidate_factory_run.json` records the **last factory orchestration** (profile, steps, reuse). For **`explicit_list`** product runs (`--candidates <id>`), `candidate_comparison.json` is **product-scoped** (baseline + selected ids only); the full on-disk scan is in `candidate_comparison_registry.json` when present. Batch/research compare still writes the full registry to `candidate_comparison.json`. Read `candidate_menu` before trusting rankings on batch paths.

Operator detail: [WORKFLOW.md § Portfolio-First Operator Checklist](WORKFLOW.md#portfolio-first-operator-checklist);
[docs/operational_runbook.md §0.1](docs/operational_runbook.md#01-read-this-first-main-portfolio-layout);
factory playbooks: [runbook §8](docs/operational_runbook.md#8-candidate-portfolio-factory-operator-playbook).
Confusion audit:
[2026-05-23 core/full artifact audit](docs/audits/2026-05-23_core_full_artifact_documentation_confusion_audit.md).

## Command Matrix

**Review default vs full menu:** default `run_portfolio_review.py` is now diagnosis-only and does not
run candidate factory or compare unless candidate execution is explicitly requested. Use
`--candidates <id>` for product one-candidate/shortlist flows, `--with-candidates` for backend
core batch (`core_fast`), and `--mode full` (or `--candidate-profile default_v1`) for the full
advanced/research menu.

### Portfolio-first review (orchestrated)

| Use case | Command | Factory profile |
| --- | --- | --- |
| Portfolio diagnosis / site/API backend run | `python run_portfolio_review.py` | none (diagnosis-only) |
| **Canonical product demo** (one candidate -> compare -> verdict) | `python scripts/run_blocks_5_to_9_vertical_flow.py --method equal_weight` | one selected Launchpad card and one candidate attempt; not `core_fast` menu |
| One explicit backend candidate compatibility path | `python run_portfolio_review.py --candidates equal_weight` (or another factory id) | explicit id only; not `core_fast` menu |
| Core backend candidate batch (advanced/research) | `python run_portfolio_review.py --with-candidates` | `core_fast` |
| Full advanced/research review (16 builders + compare) | `python run_portfolio_review.py --mode full` | `default_v1` |
| Compare / technical decision package only (no subject/factory) | `python run_compare_variants.py` | ? |
| Portfolio-first PDF export | `python run_portfolio_review.py --with-pdf` | same as mode |
| Full legacy PDF suite | `python run_portfolio_review.py --legacy-full-pdf` or `python rebuild_pdf_reports.py` | — |

### Standalone candidate factory

Use when refreshing candidates without a full portfolio review, or when resuming a factory run.
Profile must match the menu you intend to score (`core_fast` for routine core, `core_v1` for
sequential regression/parity, or `default_v1` for the full menu).

| Use case | Command | Factory profile |
| --- | --- | --- |
| Full menu factory + compare | `python run_candidate_factory.py --profile default_v1 --then-compare` | `default_v1` |
| Core menu factory + compare | `python run_candidate_factory.py --profile core_fast --then-compare` | `core_fast` |
| Core sequential regression factory + compare | `python run_candidate_factory.py --profile core_v1 --then-compare` | `core_v1` |
| Benchmark/timing run (parallel Phase 2) | `python run_candidate_factory.py --profile default_v1 --then-compare --parallel-lightweight-reports` | `default_v1` |

### Legacy policy and report exports

| Use case | Command |
| --- | --- |
| Legacy report orchestration (JSON-first) | `python run_report.py` |
| Legacy policy optimize only | `python run_optimization.py` |
| Legacy policy + report orchestration | `python run_optimization.py --with-report` |
| Legacy full report exports | `python run_report.py --output-profile full_report` |
| Legacy export + PDF-capable sidecars | `python run_report.py --output-profile legacy_export` |
| Legacy policy workflow wrapper | `python run_mvp_workflow.py --workflow policy-only` (or `policy-current` / `full-decision`) |

## Output Policy

Central routing: `src/output_policy.py`. Default profile: `site_api`.

| Profile | JSON contracts | Cache | CSV / TXT / HTML / PNG | PDF / Markdown sidecars / CSS |
| --- | --- | --- | --- | --- |
| `site_api` (default) | Yes | Yes | No | No |
| `core_json` | Yes | Yes | No | No |
| `lightweight_comparison` | Yes | Yes | No | No |
| `full_report` | Yes | Yes | Yes | No |
| `legacy_export` | Yes | Yes | Yes | Yes |

`output_manifest.json` (`output_manifest_v1`) is written under `output_dir_final` after report,
factory, compare, and portfolio-review runs. It indexes `output_profile`, required JSON paths,
`disabled_artifact_classes`, optional `cache_keys`, and `artifact_counts_by_type` for UI/API
consumers. Cache under `cache/` is internal infrastructure, not a client-facing contract.

CSV exporters remain in source for audit, Excel review, debugging, and legacy reporting; they are
not invoked unless `full_report`, `legacy_export`, or an explicit PDF/export command requests them.

## Main Output Flow

The current implementation is site/API-first and CLI/file-driven, but product-facing output should
be interpreted through the ДИАГНОСТИКА 2 bundle first.

Portfolio-first output flow contract:

```text
analysis_subject
-> subject diagnostics
-> problem classification / candidate launchpad
-> portfolio alternatives builder setup
-> explicit candidate generation attempt
-> current-vs-candidate / decision verdict / AI grounding / what changed
```

The portfolio-first orchestrator (`run_portfolio_review.py`) follows this order by default in
diagnosis-only mode. Candidate generation/compare are opt-in (`--candidates`, `--with-candidates`,
`--mode full`). The legacy policy output flow remains callable for compatibility only:

```text
config.yml
-> run_optimization.py
-> optimized weights and run metadata
-> run_report.py
-> metrics, diagnostics, stress reports, scenario libraries, commentary, snapshots, and report artifacts
```

Compatibility commands:

```bash
python run_optimization.py
python run_optimization.py --with-report
python run_report.py
python run_report.py --output-profile full_report
```

## Output Producers

| Producer | Role | Common outputs |
| --- | --- | --- |
| Portfolio-first subject materialization | Subject diagnostics before candidates | `{output_dir_final}/analysis_subject/` snapshots, metadata, X-Ray, and diagnostics from `run_report.py --materialize-analysis-subject` |
| `run_optimization.py` | Legacy policy optimization and release checks | `portfolio_weights.yml`, `run_result.json`, run metadata under `output_dir_final` |
| `run_report.py` | Main report and diagnostics flow | JSON contracts by default (`stress_report.json`, `portfolio_xray.json`, snapshots, scenario libraries); CSV/TXT/HTML/PNG/PDF only with `full_report` / `legacy_export` |
| `run_mvp_workflow.py` | Legacy wrapper over policy/report stages | Legacy policy/current/full-decision orchestration outputs; compatibility-only entrypoint |
| Candidate portfolio scripts | Build fixed benchmark/candidate weights and run the report pipeline | Candidate output folders with the same report contract after weights are fixed |
| Robust/scenario scripts | Build robust candidate weights or reports from existing report artifacts | Robust/scenario JSON, CSV, and candidate report folders |
| Taxonomy scripts | Validate/list/export taxonomy diagnostics; onboarding report for new tickers (`scripts/taxonomy_onboard_report.py`) | Taxonomy validation/list/export artifacts where configured; onboarding report is operator stdout/JSON only (not written by `run_portfolio_review.py` by default) |
| PDF rebuild helpers | Rebuild PDF-style artifacts from report-sidecar content | `pdf files/` and `pdf_md_sources/` artifacts |

## Common Output Locations

| Location | Meaning | Source status |
| --- | --- | --- |
| `Main portfolio/` | Default main portfolio output folder, usually `output_dir_final`; hosts `candidate_comparison.json` | Generated |
| `{output_dir_final}/analysis_subject/` | Portfolio-first diagnostics folder for the subject analyzed before candidates | Generated |
| `results_csv/` | Tabular metrics, stress, factor, scenario, and diagnostic CSV outputs | Generated |
| `output/` | Auxiliary runtime output folder where configured | Generated |
| `cache/` | Cached data/runtime material | Generated |
| Candidate portfolio folders | Outputs for Equal Weight, Risk Parity, MinVar, CVaR, Robust MV, robust scenario, and other variants | Generated |
| `pdf files/` | Generated PDF-style report artifacts | Generated only when explicitly requested (`run_portfolio_review.py --with-pdf`, `--legacy-full-pdf`, `run_report.py --output-profile legacy_export`, or `rebuild_pdf_reports.py`); default site/API review does not write PDFs |
| `pdf_md_sources/` | Generated Markdown sidecars used for PDF-style report builds | Generated |
| `portfolio_weights.yml` | Optimizer-produced weights | Generated runtime output, not normal manual input |

Root documentation files such as `README.md`, `SPEC.md`, `DATA.md`, `TESTING.md`, `WORKFLOW.md`, `RULES.md`, `GLOSSARY.md`, `KNOWN_ISSUES.md`, `DECISIONS.md`, `CHANGELOG.md`, this file, `DOCUMENTATION_MIGRATION_PLAN.md`, `DOCUMENTATION_MIGRATION_SESSION09_AUDIT.md`, and archived legacy Markdown files are source/planning documentation, not generated outputs.

Target product concepts from the documentation migration do not create new artifact contracts until
an owning spec and implementation define their concrete files, schemas, and output policy. This now
includes additive contracts for Problem Classification, Candidate Launchpad, current-vs-candidate,
Decision Verdict mapping, and AI Commentary grounding context; any remaining product UX around those
concepts is still not implemented unless a specific owning spec says so.

Output terminology boundary: product-facing `Decision Verdict` language may map to current generated
Selection/No-Trade evidence, but it does not rename `selection_decision.json`, Selection Engine
contracts, No-Trade artifacts, or any existing output fields. Advanced/backend generated artifacts
such as robustness scorecard, Portfolio Health Score, Selection/No-Trade, action, monitoring, and
journal outputs may remain current implementation outputs without becoming Core MVP product UI. Do not call them the current product just because they are generated.

## Product-Facing Output Bundle Policy

Default product surfaces should present the diagnosis-first bundle first. Technical, advanced, and
legacy artifacts may be linked as evidence or drill-downs, but they should not be promoted as the
main product answer unless a later approved spec changes the boundary.

The product handoff between bundle artifact #2 and candidate generation is:
`candidate_launchpad.json` card selection -> Builder prefill -> explicit Generate Candidate action.
Builder prefill preserves diagnosis, hypothesis, success criteria, tradeoff, skip rule, and
decision boundary. It is not a generated portfolio, not a rebalance recommendation, and not a
Decision Verdict.

Candidate Generation then writes one diagnostic candidate attempt. That candidate is not a recommendation; reference methods such as Equal Weight and Risk Parity remain diagnostic comparisons. Action/no-action is evaluated only in `decision_verdict.json`, where no-trade and evidence-insufficient are valid outcomes.

| Category | Artifacts | Product rule |
| --- | --- | --- |
| **Core MVP product bundle** | `problem_classification.json`, `candidate_launchpad.json`, `portfolio_alternatives_builder.json`, `candidate_generation.json`, `current_vs_candidate.json`, `decision_verdict.json`, `ai_commentary_context.json`, `what_changed_summary.json` | Product-facing diagnosis-first flow: explain the current problem, possible hypotheses, validated Builder setup, one explicit candidate attempt, current-vs-candidate trade-offs, verdict, commentary grounding, and light change summary. `portfolio_alternatives_builder.json` is setup-only: valid cards expose `CandidateSetup`; data-quality cards are blocked; no weights/comparison/verdict are produced by Block 6. `candidate_generation.json` is one attempt from that setup, not a recommendation and not a comparison. `ai_commentary_context.json` is grounding-only (no LLM). `commentary.txt`, `stress_commentary.txt`, and PDF exports remain deterministic report-pipeline prose, not generated AI Commentary. These are adapters/mappings over deterministic evidence; they do not rename lower-level contracts. |
| **Technical comparison / decision contracts** | `candidate_comparison.json`, `selection_decision.json`, `candidate_factory_run.json`, `candidate_factory_manifest.json`, per-candidate `candidate_manifest.json`, `output_manifest.json` | Machine-readable evidence and orchestration contracts. UI/API code may depend on them, but client-facing language should translate them into the product bundle where possible. |
| **Advanced / research evidence** | `portfolio_health_score.json`, `robustness_scorecard.json`, `assumption_sensitivity.json`, `pareto_dominance.json`, `regret_analysis.json`, `tradeoff_explanation.json`, `model_risk_diagnostics.json` | Useful diagnostics for drill-down, research, review, and confidence checks. Do not frame these as the main Portfolio MRI answer or as automatic recommendations. |
| **Action / monitoring / journal evidence** | `action_plan.json`, `monitoring_diff.json`, `decision_journal.json`, `decision_package_summary.json` | Current generated evidence for implementation review, change tracking, and reporting. Product-facing summaries should route through `decision_verdict.json` and `what_changed_summary.json` where available. |
| **Legacy / compatibility artifacts** | `run_result.json`, `portfolio_weights.yml`, root legacy `portfolio_xray.json` / `stress_report.json` from policy runs, `current_vs_policy_status.json`, `portfolio_comparison.json`, `ew_rp_comparison.json` | Preserve for compatibility and historical workflows. Do not treat them as the portfolio-first subject or main diagnosis-first output unless the active workflow explicitly targets the legacy path. |
| **Generated/export artifacts, not source-of-truth** | CSV/TXT/HTML/PNG/PDF/Markdown sidecars, candidate folders, cache, report exports | Generated output only. They may be refreshed by approved runs, but they are not source documentation or implementation contracts. |

No files are deleted, renamed, or schema-migrated by this policy. It is a presentation and
documentation boundary over current generated artifacts.

### Runtime product flow (portfolio-first)

After `python run_portfolio_review.py`, product/UI consumers should present the Core MVP bundle
first and treat other JSON as drill-down evidence. A separate merged `product_bundle.json` is **not**
required; each bundle artifact has its own writer and schema.

| Bundle artifact | Writer (code) | Default path | When present |
| --- | --- | --- | --- |
| `problem_classification.json` | `write_block_4_diagnosis_outputs` in `run_report.py` (`src/block_4/diagnosis_builder.py`) | `{output_dir_final}/analysis_subject/problem_classification.json` | After default diagnosis / materialize (#1); schema `problem_classification_v3` |
| `candidate_launchpad.json` | `write_block_4_diagnosis_outputs` in `run_report.py` | `{output_dir_final}/analysis_subject/candidate_launchpad.json` | After default diagnosis / materialize (#2); schema `candidate_launchpad_v3` |
| `portfolio_alternatives_builder.json` | `write_portfolio_alternatives_builder_outputs` called by `write_block_4_diagnosis_outputs` | `{output_dir_final}/analysis_subject/portfolio_alternatives_builder.json` | After Launchpad when a primary card exists; schema `portfolio_alternatives_builder_v1`; setup only (#2.5) |
| `candidate_generation.json` | `write_candidate_generation_outputs` in `src/candidate_generation.py`; runtime adapter `scripts/generate_candidate_from_builder_setup.py`; one-command wrapper `scripts/run_blocks_5_to_9_vertical_flow.py` | `{output_dir_final}/candidate_generation.json` | After explicit Generate Candidate action or the Blocks 5-9 vertical demo; schema `candidate_generation_v1`; one attempt only (#3) |
| `current_vs_candidate.json` | `write_current_vs_candidate_outputs` in compare chain, or Block 8-only `write_block8_current_vs_candidate_only_outputs` | `{output_dir_final}/current_vs_candidate.json` | After compare only (#4); Block 8-only mode does not write verdict/action/journal/AI context |
| `decision_verdict.json` | `write_decision_verdict_outputs` | `{output_dir_final}/decision_verdict.json` | After compare only (#5) |
| `ai_commentary_context.json` | `write_ai_commentary_context_outputs` | `{output_dir_final}/ai_commentary_context.json` | After compare only (#6) |
| `what_changed_summary.json` | `write_what_changed_summary_outputs` | `{output_dir_final}/what_changed_summary.json` | After compare only (#7); optional if no prior snapshot |

Compare (`write_candidate_comparison_outputs`) still writes technical and advanced contracts
(`candidate_comparison.json`, `selection_decision.json`, health/robustness/Pareto/regret, action,
monitoring, journal, decision-package projections). The Block 8-only helper
(`write_block8_current_vs_candidate_only_outputs`) is narrower: it scopes `candidate_comparison.json`
to the selected candidate and writes `current_vs_candidate.json` without refreshing downstream
verdict/action/journal/AI-context artifacts. Default `site_api` runs omit CSV/TXT/PDF unless
export flags are set. `output_manifest.json` lists generated paths for orchestration; it is not the
product-facing answer—filter with the bundle table above. After compare (and report when diagnosis
artifacts exist), `generated_paths` includes resolved keys for the product bundle JSON files
(`problem_classification_json` through `what_changed_summary_json`, plus `portfolio_alternatives_builder_json` when Block 6 setup exists; diagnosis paths prefer
`analysis_subject/`). `artifact_categories` groups keys by surface (`product_bundle`, `technical_comparison`,
`subject_diagnostics`, `advanced_evidence`, `orchestration`, `legacy_compatibility`,
`generated_export`). `generated_paths_by_category` lists resolved paths per category;
`product_discovery.product_bundle_paths` lists resolved Core MVP files on disk;
`product_bundle_phase` is `diagnosis_only` (diagnosis, Launchpad, and Builder setup where available), `post_compare_partial`, or `complete`
(decision bundle complete). `product_bundle_complete` is true only when `product_bundle_phase` is `complete`.
`artifact_categories.product_bundle` lists the product-bundle manifest key names, including `portfolio_alternatives_builder_json`; resolved
paths appear in `generated_paths_by_category.product_bundle` only for files that exist.

## Output Formats

| Format | Used for | Rules |
| --- | --- | --- |
| YAML | Optimizer-produced weights and source configs | `config.yml` is source config; `portfolio_weights.yml` is generated output |
| JSON | Run metadata, stress reports, scenario libraries, diagnostics, candidate metadata | Preserve structured fields and explicit warnings/metadata for degraded diagnostics |
| CSV | Metrics, stress tables, factor/regime/scenario diagnostics | Export-only (`full_report` / `legacy_export`); numeric rounding only at final export stage |
| TXT | Human-readable commentary and stress commentary | Export-only; English-only UTF-8 when enabled |
| HTML | Snapshots, dashboards, and generated visual report surfaces | Export-only; follow [DESIGN.md](DESIGN.md) for visual/interface work |
| PDF-style artifacts | Client/report packages | Export-only (`legacy_export`, explicit PDF rebuild, or `--with-pdf`) |
| Markdown sidecars | Intermediate report text for PDF-style builds | Export-only under `pdf_md_sources/` when PDF pipeline runs |

## Primary Artifacts

Default `site_api` runs produce the JSON rows below (plus cache). CSV, TXT, HTML, PNG, PDF, and
Markdown sidecar rows apply only when an export profile or explicit PDF command enables them.

Common project artifacts include:

- `output_manifest.json` — UI/API index (`output_manifest_v1`; profile, paths, `artifact_categories`, disabled classes, counts; six product-bundle path keys when present)

- `portfolio_weights.yml`
- `run_result.json`
- `run_metadata.json`
- `stress_report.json`
- Custom shock simulator API (no generated file by default): `src/stress.py::simulate_custom_shock` and
  `shock_vector_from_scenario`; contract in [stress testing spec](docs/specs/stress_testing_spec.md) §12.3
- `custom_shock_runs.json` (optional, opt-in only): versioned audit trail for
  `record_custom_shock_run` / `write_custom_shock_runs`; not written by `run_stress` or default
  `run_report.py` paths; envelope `custom_shock_runs_v1` per stress spec §12.3
- `stress_report.json.current_portfolio_stress_scorecard_v1` (Block 3.4 Core MVP — **Implemented**; ruleset `current_portfolio_stress_scorecard_rules_v1_1`; executive stress diagnosis read-only over Blocks 3.1–3.3; `block_status`, `stress_diagnosis`, `stress_coverage`, loss/risk summaries, `hedge_gap_summary`, optional `pre_stress_confirmation_summary`, `problem_classification_signals`, `candidate_comparison_targets`, nested `ai_commentary_context`, `next_decision_uses[]`, explicit `legacy_fallback_used`; contract in [current_portfolio_stress_scorecard_spec.md](docs/specs/current_portfolio_stress_scorecard_spec.md))
- `stress_report.json.stress_scorecard_v1` (legacy unified stress scorecard; mandate-mode semantics and `DIAG_*` rollups — secondary to Block 3.4 for Core MVP product surfaces)
- `stress_report.json.stress_results_v1` (Block 3.2 product-facing per-scenario stress results)
- `stress_report.json.historical_stress_replay_v1` (Core MVP honest historical crisis replay: direct history only, per-episode coverage and replay status; merged into Block 3.2 historical rows on portfolio-first diagnostic runs; see [core_mvp_historical_stress_replay_spec.md](docs/specs/core_mvp_historical_stress_replay_spec.md) and DEC-2026-05-28-001)
- `stress_report.json.hedge_gap_analysis_v1` (Block 3.3 Core MVP — **Implemented**; eight protection rows, `ruleset_version` `hedge_gap_rules_v1_2`, `summary.main_hedge_gap` / `protection_profile`, optional `hidden_exposure_confirmation` / `weakness_map_confirmation` when Portfolio X-Ray bridges run; contract in [hedge_gap_analysis_spec.md](docs/specs/hedge_gap_analysis_spec.md))
- `stress_report.json.stress_conclusions` (aggregated stress conclusions; `hedge_gap_status` mirrors **legacy** `hedge_gap_analysis` only — prefer v1 for product hedge-gap diagnosis)
- `stress_report.json.hedge_gap_analysis` (legacy hedge gap diagnostic block; taxonomy hedge labels; secondary to `hedge_gap_analysis_v1`)
- `snapshot_10y.json` → `stress_suite_results.hedge_gap_analysis_v1` (compact mirror: `block_status`, `ruleset_version`, `protection_profile`, `main_gap_score`, bridge arrays when present)
- `snapshot_10y.json` → `stress_suite_results.current_portfolio_stress_scorecard_v1` (compact mirror: `block_status`, `ruleset_version`, `stress_diagnosis`, worst-scenario selectors, `hedge_gap_summary`, `next_decision_uses` when present)
- `stress_report.json.historical_episode_paths` (path-level crisis replay block)
- `stress_report.json.data_trust_summary` (`stress_data_trust_summary_v1`; episode quality, young-ETF and taxonomy warnings for user-readable surfaces; RM-1016)
- `portfolio_xray.json`
- `portfolio_xray.json.data_trust_signals` and `input_assumptions.data_trust_signals` (`input_data_trust_signals_v1`; rolled section warnings plus stress trust; RM-1016)
- `scenario_library.json`
- `scenario_library_normalized.json`
- metric CSV files under `results_csv/`
- stress, factor, macro, regime, and scenario CSV files under `results_csv/`
- `results_csv/crisis_replay_{episode}.csv` (path-level historical replay export)
- `results_csv/crisis_replay_{episode}_asset_contrib.csv` (static-weight asset episode attribution)
- `commentary.txt` (deterministic rule-based portfolio commentary from structured metrics/JSON; not LLM-generated AI Commentary; see `src/portfolio_commentary.py`)
- `stress_commentary.txt` (deterministic stress commentary; not LLM-generated AI Commentary)
- generated HTML snapshots
- generated PDF-style reports
- candidate portfolio output folders
- `{output_dir_final}/analysis_subject/` (portfolio-first subject diagnostics from `run_report.py --materialize-analysis-subject`; see [portfolio review workflow spec](docs/specs/portfolio_review_workflow_spec.md))
- `candidate_factory_run.json`, optional `candidate_factory_run.txt`, and `candidate_factory_manifest.json` (under `output_dir_final`; backend/advanced/research factory orchestration from `run_candidate_factory.py`; `--resume` reads the manifest; top-level `run_status` and `execution_summary` disclose partial failure vs full success; `execution_action` per step; contract in [candidate factory spec](docs/specs/candidate_factory_spec.md); methodology map [§4](docs/audits/2026-05-20_candidate_factory_methodology_map.md))
- `problem_classification.json` (under each report output folder where `portfolio_xray.json` and `stress_report.json` are available; **v3 current** schema `problem_classification_v3` via `src/block_4/diagnosis_builder.py`; one primary diagnosis/outcome, root cause, supporting symptoms, max-five key evidence, why-not-other-problems, confidence/materiality/actionability, `next_diagnostic_step`, success criteria, and backend audit metadata; contracts in [block_4_diagnosis_v3_spec.md](docs/specs/block_4_diagnosis_v3_spec.md) and [problem classification spec](docs/specs/problem_classification_spec.md))
- `candidate_launchpad.json` (under each report output folder where Block 4 diagnosis is written; **v3 current** schema `candidate_launchpad_v3`; hypothesis/reference cards with `source_diagnosis_id`, `hypothesis_to_test`, `card_type`, `launch_status`, `why_this_test`, `suggested_methods`, `success_criteria`, trade-off/skip copy, `decision_boundary`, disclaimer; no weights; Equal Weight / Risk Parity reference cards are benchmark tests, not rebalance recommendations; selected cards can derive Builder setup but do not generate candidates automatically; contracts in [block_4_diagnosis_v3_spec.md](docs/specs/block_4_diagnosis_v3_spec.md), [candidate launchpad spec](docs/specs/candidate_launchpad_spec.md), and [portfolio alternatives builder spec](docs/specs/portfolio_alternatives_builder_spec.md))
- `portfolio_alternatives_builder.json` (under each `analysis_subject/` folder where Block 4 diagnosis writes a primary Launchpad card; **v1 current** schema `portfolio_alternatives_builder_v1`; contains `builder_prefill`, validation, and `candidate_setup` only when valid; data-quality blockers write `status: blocked`, `can_generate_candidate: false`, `reason: data_quality_blocker`, and `candidate_setup: null`; no candidate ids, weights, comparison, or verdict; contracts in [portfolio alternatives builder spec](docs/specs/portfolio_alternatives_builder_spec.md), [builder prefill spec](docs/specs/builder_prefill_spec.md), and [candidate setup spec](docs/specs/candidate_setup_spec.md))
- `candidate_generation.json` (under `output_dir_final`; **v1 current** schema `candidate_generation_v1`; one explicit candidate attempt from validated `CandidateSetup`; preserves diagnosis, hypothesis, method variant, constraints, weights when supplied, failure/infeasibility reason when supplied, success criteria, tradeoff, decision boundary, and `is_rebalance_recommendation: false`; does not write comparison or verdict; contract in [candidate generation spec](docs/specs/candidate_generation_spec.md))
- `candidate_factory_run.json.parallel_lightweight_report_summary` (optional; present when `--parallel-lightweight-reports` is requested or effective; records requested/effective status, fallback reasons, worker count, menu-ordered submitted/registered candidate ids, and optional wall-clock seconds for Phase 2 lightweight report generation)
- `{artifact_root}/candidate_manifest.json` per script-backed candidate folder (`candidate_manifest_v1`; factory-written readiness: comparison gates, artifact presence, optional `partial_failure` when weights succeeded but report/snapshot did not; see [candidate factory spec](docs/specs/candidate_factory_spec.md) Session 5)
- `candidate_comparison.json` (under `output_dir_final`; **product-scoped** for `explicit_list` factory runs — baseline + `product_candidate_scope.candidate_ids` only; **full registry** for batch/research compare; includes the portfolio-first `analysis_subject` baseline row when materialized; optional `full_comparison_registry_artifact` pointer when scoped; optional top-level `hedge_gap_comparison` (`hedge_gap_comparison_v1`) when baseline and peers expose `hedge_gap_analysis_v1`; optional top-level `stress_scorecard_comparison` (`stress_scorecard_comparison_v1`) when baseline and peers expose Block 3.4; per-row `stress.hedge_gap_analysis_v1` compact slice and `stress.current_portfolio_stress_scorecard_v1` when present; `candidate_menu` reports `factory_evidence_status`, `factory_steps_used`, `factory_evidence_warnings`, and `factory_execution_summary` for `candidate_factory_run.json` freshness and rebuild/reuse disclosure; per-row `construction_disclosure` passthrough including `optimizer_methodology`, `optimizer_quality`, and `optimization_readiness` (`fair_comparison_ready` checklist) for optimizer-backed rows when artifacts exist; optimizer-backed rows with missing methodology/quality or `unknown` quality degrade instead of ordinary `available` evidence; see [candidate comparison spec](docs/specs/candidate_comparison_spec.md))
- `candidate_comparison_registry.json` (optional; under `output_dir_final` when product comparison is scoped — full on-disk candidate scan with `registry_artifact_role: full_on_disk_candidate_scan`; advanced/research only; see DEC-2026-05-29-006)
- `current_vs_candidate.json` (under `output_dir_final`; product-facing current-vs-selected-candidate or shortlist adapter built from `candidate_comparison.json` and optional `selection_decision.json`; does not replace the canonical comparison contract; see [current vs candidate spec](docs/specs/current_vs_candidate_spec.md))
- `robustness_scorecard.json` and optional `robustness_scorecard.txt` (under `output_dir_final`; written by `run_compare_variants.py` / `write_candidate_comparison_outputs`; see [robustness scorecard spec](docs/specs/robustness_scorecard_spec.md))
- `portfolio_health_score.json` and optional `portfolio_health_score.txt` (under `output_dir_final`; Session 13; see [portfolio health score spec](docs/specs/portfolio_health_score_spec.md))
- `selection_decision.json` and optional `selection_decision.txt` (under `output_dir_final`; contract in [selection engine spec](docs/specs/selection_engine_spec.md))
- `decision_verdict.json` (under `output_dir_final`; product-facing mapping over `selection_decision.json`, optional `current_vs_candidate.json`, and `action_plan.json`; does not rename or replace Selection Engine contracts; see [decision verdict spec](docs/specs/decision_verdict_spec.md))
- `ai_commentary_context.json` (under `output_dir_final`; deterministic grounding contract for future AI Commentary, written after Decision Verdict; may cite `candidate_generation.json` for the tested hypothesis/candidate attempt, `current_vs_candidate.json` for improvements, deteriorations, turnover/cost, and success-criteria results, and `decision_verdict.json` for verdict/no-trade rationale only when the explicit `product_run` lineage matches if present; also includes `hedge_gap_context` (`hedge_gap_context_v1`, v1-primary with legacy fallback) and `current_portfolio_stress_scorecard_context` (`current_portfolio_stress_scorecard_context_v1`, v1-primary with legacy fallback) plus evidence refs for Block 3.4 / `stress_scorecard_comparison` when present; does not call an LLM or calculate metrics; see [AI commentary grounding spec](docs/specs/ai_commentary_grounding_spec.md))
- `tradeoff_explanation.json` and optional `tradeoff_explanation.txt` (under `output_dir_final`; [src/tradeoff_and_model_risk.py](src/tradeoff_and_model_risk.py); [trade-off and model risk spec](docs/specs/tradeoff_and_model_risk_spec.md))
- `model_risk_diagnostics.json` and optional `model_risk_diagnostics.txt` (under `output_dir_final`; same module and spec)
- `assumption_sensitivity.json` and `assumption_sensitivity.txt` (under `output_dir_final` after compare; [assumption sensitivity spec](docs/specs/assumption_sensitivity_spec.md))
- `pareto_dominance.json` and `pareto_dominance.txt` (under `output_dir_final` after compare; [pareto dominance spec](docs/specs/pareto_dominance_spec.md))
- `regret_analysis.json` and `regret_analysis.txt` (under `output_dir_final` after compare; [regret analysis spec](docs/specs/regret_analysis_spec.md); implementation post-audit Session 19)
- `action_plan.json` and optional `action_plan.txt` (under `output_dir_final`; contract in [action engine spec](docs/specs/action_engine_spec.md))
- `monitoring_diff.json` and optional `monitoring_diff.txt` (under `output_dir_final`; [monitoring spec](docs/specs/monitoring_spec.md); compares to prior `monitoring/latest/analysis_snapshot.json`)
- `what_changed_summary.json` (under `output_dir_final`; light product-facing Monitoring / What Changed projection over `monitoring_diff.json`, optional Decision Verdict and diagnosis context; does not replace monitoring snapshots/diff; see [light monitoring summary spec](docs/specs/light_monitoring_summary_spec.md))
- `monitoring/latest/analysis_snapshot.json` and `monitoring/history/analysis_snapshot_{analysis_end}.json` (generated monitoring snapshots; same spec)
- `decision_journal.json` and optional `decision_journal.txt` (under `output_dir_final`; written by `write_candidate_comparison_outputs`; see [decision journal spec](docs/specs/decision_journal_spec.md))
- `journal/latest/decision_journal.json` and `journal/history/decision_journal_{analysis_end}.json` (generated journal copies; same spec)
- `decision_package_summary.json` and `decision_package_summary.txt` (under `output_dir_final`; compact English summary of the full V1 decision package; see [decision package reporting spec](docs/specs/decision_package_reporting_spec.md))
- `current_vs_policy_status.json` and optional `current_vs_policy_status.txt` (under `output_dir_final`; legacy current-vs-policy workflow status and No-Trade actionability; portfolio-first runs may write it with `workflow_profile: portfolio_first_review` as compatibility-only metadata; see [current vs policy workflow spec](docs/specs/current_vs_policy_workflow_spec.md); written after comparison in Session 09 implementation)
- `{output_dir_final}/current_portfolio/` (sidecar folder for materialized current-portfolio snapshots when using the combined current-vs-policy workflow; does not replace policy artifacts on Main root)
- legacy `portfolio_comparison.json` and `ew_rp_comparison.json` (subset comparisons; superseded by canonical contract)

`portfolio_xray.json` is a generated, diagnostic-only Portfolio X-Ray artifact. It summarizes existing report pipeline outputs and in-memory diagnostics; it does not optimize, change weights, change mandate gates, change stress pass/fail status, or make portfolio selection decisions. Its section and disclosure contract is owned by [docs/specs/portfolio_xray_diagnostics_spec.md](docs/specs/portfolio_xray_diagnostics_spec.md). Product Block 2.3 (`block_2_3_factor_exposure`) is an adapter over existing `stress_report` factor diagnostics; missing factor fields are reported as partial/unavailable and fixed upstream, not recalculated inside X-Ray. Product Block 2.4 (`block_2_4_hidden_exposure`) is an additive rule-based hidden exposure detector over completed Blocks 2.1, 2.2, and 2.3 only (`heuristic_v2` scoring). It does not run Stress Lab, candidates, optimizer, or factor-model recalculation. Optional wire-time summaries at X-Ray build: Block 3 stress enrichment (`build_block_2_4_stress_enrichment`) for weak-hedge confirmation and duration cross-ref; legacy PCA enrichment (`build_block_2_4_legacy_enrichment`) for informational `correlation_concentration` cross-ref to `sections.hidden_risk_detector` — neither changes alert scores. Product Block 2.5 (`block_2_5_risk_budget_view`, §2.5.1) compares capital weights to RC_vol and taxonomy risk-budget buckets; it must not recompute RC, read `stress_report` for core fields, or include stress PnL on the product block (legacy `sections.risk_budget_view` may still expose stress fields). Product Block 2.6 (`block_2_6_portfolio_weakness_map`, §2.6.1) reads completed Blocks 2.1–2.5 and emits pre-stress weakness hypotheses only. Core MVP UI/API consumers should prefer top-level product blocks 2.1–2.6; `sections.*` and `legacy_summary` remain compatibility surfaces, and `legacy_summary._scope.product_surface=false`. Human-readable surfaces are rendered from this JSON via `format_portfolio_xray_text` (`report.txt`), `format_portfolio_xray_html` (`report.html`), and `format_portfolio_xray_commentary` (`commentary.txt` compact block).

`run_result.json` and `run_metadata.json` include an `analysis_setup` block, the resolved runtime contract for the input and assumptions layer. They also include `input_assumptions`, the reporting view projected from `analysis_setup`, summarizing the input mode, tickers, fixed/current weight status, resolved market assumptions, mandate inputs, calculation settings, Core MVP `input_surface` / `field_tiers` disclosure, real-cash handling when present, and known V1 gaps. For Core MVP product consumers, the minimal input contract is `analysis_setup.core_mvp_input_surface` mirrored as `input_assumptions.core_mvp_input_contract`; legacy/client/mandate disclosure fields are not required product input. When diagnosis-only materialization uses the approved cached FRED risk-free fallback, `run_metadata.json.derived_assumptions` exposes `risk_free_fallback_used`, `risk_free_fallback_reason`, `risk_free_data_provenance`, and `risk_free_warnings`; `data_policy.json` mirrors the same fallback flag, reason, provenance, and warnings for operator inspection. Legacy policy `run_result.json` also includes `optimizer_run_metadata` (`legacy_policy_optimizer_run_metadata_v1`) with objective, estimator, window, input fingerprints, universe, bounds/caps, cash policy, solver/fallback, release-gate disclosure, covariance methodology, and Young ETF methodology. Optimizer candidate `baseline_weights_metadata.json` exports for Minimum Variance, Maximum Diversification, Minimum CVaR, and Robust Mean-Variance include `optimizer_run_metadata` (`candidate_optimizer_run_metadata_v1`) with candidate-only role, method/objective, input window, input fingerprints, estimator/constraint, solver/fallback, parameter, output-summary disclosure, covariance methodology, and Young ETF methodology while preserving legacy top-level metadata fields. Materialized Robust Scenario candidate metadata may include `optimizer_run_metadata` (`robust_scenario_optimizer_run_metadata_v1`) copied from `robust_optimization_v1_summary.json`, including SLSQP solver/fallback quality. `candidate_comparison.json` copies the comparison-ready subset to `construction_disclosure.optimizer_methodology` when those upstream metadata blocks exist and projects normalized fallback/failure quality to `construction_disclosure.optimizer_quality` when metadata or factory evidence is available. `candidate_comparison.txt` and legacy `ips_summary.txt` include compact optimizer methodology notes when source metadata is present.

The exact artifact set can vary by config, available data, candidate type, and enabled report features.

Optimization output disclosure is governed by the current artifact contracts above and the
[Optimization Engine layer spec](docs/specs/optimization_engine_layer_spec.md). Session 03 adds
legacy policy `optimizer_run_metadata` to `run_result.json`; Session 04 adds candidate optimizer
`optimizer_run_metadata` inside optimizer candidate `baseline_weights_metadata.json` exports.
Session 05 propagates those normalized blocks into `candidate_comparison.json`
`construction_disclosure.optimizer_methodology` without changing optimizer behavior or generated
weights. Session 06 adds `construction_disclosure.optimizer_quality` and factory step optimizer
quality evidence so fallback/approximate solves are degraded, failed factory/optimizer quality is
unavailable, and Selection warnings can surface favored fallback targets. Session 07 adds robust
scenario SLSQP solver status to `robust_optimization_v1_summary.json` and propagates it through the
materialized robust scenario candidate metadata for factory and comparison disclosure. Session 08
adds `input_fingerprints` (`returns_panel_fingerprint`, `config_fingerprint`,
`universe_fingerprint`) and return-panel start/end/row disclosure to legacy policy and optimizer
candidate metadata so stale or mismatched estimator inputs can be audited without regenerating
weights. Session 09 adds `optimizer_covariance_methodology_v1` and
`optimizer_young_etf_methodology_v1` disclosure to optimizer metadata and surfaces compact
methodology notes in `candidate_comparison.txt` / `ips_summary.txt`. Session 10 adds
`construction_disclosure.optimization_readiness` (`optimizer_comparison_readiness_v1`) and compact
readiness notes in `candidate_comparison.txt` for optimizer-backed comparison rows.

## Blocks 1-5 MVP Output Acceptance

When validating the first-five-block MVP core (offline smoke or a representative
`run_portfolio_review.py` (default diagnosis-only) or explicit candidate-mode run, inspect generated artifacts under
`{output_dir_final}/analysis_subject/` before candidate or decision outputs:

| Block | Minimum artifacts | Trust checks |
| --- | --- | --- |
| 1 Input | `run_metadata.json` with `analysis_setup` and `input_assumptions` | Explicit current/model weights sum to at most `1.0`; partial sums disclose cash remainder; `analysis_setup.core_mvp_input_surface` and `input_assumptions.core_mvp_input_contract` expose the minimal Core MVP product input contract; `input_assumptions.input_surface` / `field_tiers` disclose deferred/legacy keys; real-cash labels in `analysis_setup.cash_handling.real_cash_holdings` when used (not substituted by `cash_proxy_ticker`) |
| 2 X-Ray | `portfolio_xray.json` (seven sections + product blocks `block_2_1_asset_allocation` … `block_2_6_portfolio_weakness_map`) | `data_trust_signals.user_summary_lines` when data-quality warnings exist; prefer product blocks for UI/API: capital structure (§2.1.1), portfolio behavior (§2.2.1), factor sensitivity (§2.3.1), hidden exposure (§2.4.1), risk budget (§2.5.1), weakness map (§2.6.1, `heuristic_v2`, eight canonical Stress Lab `risk_type` ids — [acceptance audit](docs/audits/2026-05-29_block_2_6_weakness_map_heuristic_v2_acceptance_audit.md)); Blocks 2.3–2.6 are read-only adapters over upstream evidence; legacy `sections.*` remain for formatters until migration |
| 3 Stress | `stress_report.json` with `scenario_library_meta` plus sidecar `scenario_library.json`, `stress_results_v1`, `historical_stress_replay_v1` (portfolio-first diagnostic), `hedge_gap_analysis_v1`, `current_portfolio_stress_scorecard_v1`, historical methodology, and legacy compatibility rollups | `data_trust_summary.user_summary_lines` for episode/taxonomy/young-ETF warnings and partial historical replay (`historical_stress_replay_v1`); Block 3.2 historical `portfolio_loss_pct` / `drawdown_pct` only when `portfolio_level_result_available`; Block 3.3 eight protection rows with `ruleset_version`, `summary.protection_profile`, and optional 2.4/2.6 bridge arrays after X-Ray build; Block 3.4 when `block_status` ∈ `{ok, partial}`: non-empty `stress_diagnosis.headline`, `diagnosis_confidence`, explicit `legacy_fallback_used`, non-empty `next_decision_uses`, `hedge_gap_summary.main_hedge_gap_scenario_id` when hedge gap v1 available, no mandate pass/fail or forbidden “passes normally” phrasing inside Block 3.4; Core MVP diagnostic mode must not expose row-level mandate `pass` / `loss_ok` / `diagnostic_code(s)` in product rows or raw evidence arrays |
| 4 Factory | `candidate_factory_run.json` at review root | Comparison `candidate_menu.factory_evidence_status` must be `current` or explicitly not authoritative |
| 4–5 Bundle | `candidate_comparison.json` → `review_bundle_context` | `review_bundle_fingerprint` and `mode_subject_consistency` link subject/factory/comparison; read `user_summary_lines` when `analysis_mode` label differs from `analysis_subject.type` |
| 5 Optimizers | Candidate folders + comparison rows | Optimizer-backed rows are `available` only when readiness-critical evidence is complete; otherwise `degraded` with warning codes |

Generated outputs remain evidence, not source files. Do not commit routine run refreshes unless a
session explicitly targets generated artifacts. Offline gates:
`tests/test_blocks_1_5_mvp_smoke.py` ([TESTING.md](TESTING.md)); Input Layer MVP regression:
`tests/test_input_layer_mvp_regression.py` (minimal fixtures, disclosure chain, real cash, product bundle).

## Output Rules

- Preserve full precision inside calculations.
- Round numeric metrics only at final export/report stage.
- If diagnostics degrade because inputs are missing or weak, expose warnings, coverage, confidence, usability flags, or metadata.
- Do not silently imply full confidence when fallback data or partial coverage was used.
- Do not manually edit generated weights or report artifacts as if they were source behavior.
- If generated outputs are refreshed by a run, commit them only when the task explicitly targets generated artifacts.
- Keep output names and folders stable unless a spec or explicit task changes them.

## Generated Output Refresh Policy

Generated-output refreshes are separate work from source/docs/spec migration. A refresh can be useful
to prove that current code writes the product-facing bundle, but it also creates large noisy diffs in
portfolio folders, report exports, manifests, caches, and PDF sidecars. Do not run refresh commands
unless the active session explicitly approves generated-output changes.

When a refresh is approved, prefer the narrowest portfolio-first command that produces the needed
evidence:

| Refresh intent | Preferred command | Expected checks |
| --- | --- | --- |
| Verify routine diagnosis-first bundle without PDFs | `python run_portfolio_review.py --mode core` using default `site_api` output | Inspect `{output_dir_final}/analysis_subject/`, `candidate_comparison.json`, product-bundle JSON, and `output_manifest.json`; do not expect `pdf files/` to refresh. |
| Verify subject diagnostics only | `python run_portfolio_review.py --skip-candidates` or the narrow report command that materializes the subject | Inspect `analysis_subject/portfolio_xray.json`, `analysis_subject/stress_report.json`, `problem_classification.json`, and `candidate_launchpad.json` where applicable. |
| Verify full research menu | `python run_portfolio_review.py --mode full` only when full 16-candidate evidence is explicitly required | Inspect `candidate_factory_run.json.factory_profile_id == default_v1`, `candidate_menu`, and generated diffs separately from source/docs. |
| Verify PDF/report packaging | Add `--with-pdf`, `--legacy-full-pdf`, or an explicit export profile only when PDF/export artifacts are the task target | Inspect generated PDF/Markdown sidecars separately; do not mix with ordinary JSON/cache refreshes. |

After any approved refresh:

1. Run `git status --short` and classify generated diffs separately from source/docs/config/code.
2. Confirm the product-facing bundle expected for the workflow state:
   `problem_classification.json`, `candidate_launchpad.json`, `portfolio_alternatives_builder.json`,
   `candidate_generation.json` when a candidate was explicitly generated, `current_vs_candidate.json`,
   `decision_verdict.json`, `ai_commentary_context.json`, and `what_changed_summary.json`.
3. Confirm technical manifests and comparison evidence:
   `output_manifest.json`, `candidate_comparison.json`, `selection_decision.json`, and
   `candidate_factory_run.json` when candidates ran.
4. Treat missing files as either expected for the workflow state (`diagnosis_only`, `one_candidate`,
   `multiple_candidates`) or as requiring code/spec verification. Do not infer success from stale
   files already present on disk.
5. Do not stage or commit generated outputs automatically. Commit them only when the user explicitly
   asks for generated artifacts to be included.

## Detailed Ownership

| Area | Governing document |
| --- | --- |
| Current implementation output contract | [SPEC.md](SPEC.md) |
| Portfolio-first workflow order and `analysis_subject` output role | [docs/specs/portfolio_review_workflow_spec.md](docs/specs/portfolio_review_workflow_spec.md) |
| Portfolio X-Ray JSON and seven-section diagnostic output | [docs/specs/portfolio_xray_diagnostics_spec.md](docs/specs/portfolio_xray_diagnostics_spec.md) |
| Problem Classification JSON | [docs/specs/problem_classification_spec.md](docs/specs/problem_classification_spec.md) |
| Candidate Launchpad JSON | [docs/specs/candidate_launchpad_spec.md](docs/specs/candidate_launchpad_spec.md) |
| High-level report and artifact contract | [docs/specs/reporting_outputs_spec.md](docs/specs/reporting_outputs_spec.md) |
| Candidate factory run summary JSON | [docs/specs/candidate_factory_spec.md](docs/specs/candidate_factory_spec.md) |
| Candidate Factory layer handoff (Block 4.1–4.9) | [docs/specs/candidate_factory_layer_spec.md](docs/specs/candidate_factory_layer_spec.md) |
| Block 4 methodology map and governance gaps G1–G10 | [docs/audits/2026-05-20_candidate_factory_methodology_map.md](docs/audits/2026-05-20_candidate_factory_methodology_map.md) |
| Canonical candidate comparison JSON | [docs/specs/candidate_comparison_spec.md](docs/specs/candidate_comparison_spec.md) |
| Candidate Generation JSON | [docs/specs/candidate_generation_spec.md](docs/specs/candidate_generation_spec.md) |
| Current-vs-candidate JSON | [docs/specs/current_vs_candidate_spec.md](docs/specs/current_vs_candidate_spec.md) |
| Robustness Scorecard JSON | [docs/specs/robustness_scorecard_spec.md](docs/specs/robustness_scorecard_spec.md) |
| Portfolio Health Score JSON | [docs/specs/portfolio_health_score_spec.md](docs/specs/portfolio_health_score_spec.md) |
| Selection decision JSON | [docs/specs/selection_engine_spec.md](docs/specs/selection_engine_spec.md) |
| Decision Verdict JSON | [docs/specs/decision_verdict_spec.md](docs/specs/decision_verdict_spec.md) |
| AI Commentary grounding context JSON | [docs/specs/ai_commentary_grounding_spec.md](docs/specs/ai_commentary_grounding_spec.md) |
| Trade-off explanation and model risk diagnostics JSON | [docs/specs/tradeoff_and_model_risk_spec.md](docs/specs/tradeoff_and_model_risk_spec.md) |
| Assumption sensitivity JSON | [docs/specs/assumption_sensitivity_spec.md](docs/specs/assumption_sensitivity_spec.md) |
| Pareto / Dominance JSON | [docs/specs/pareto_dominance_spec.md](docs/specs/pareto_dominance_spec.md) |
| Regret Analysis JSON | [docs/specs/regret_analysis_spec.md](docs/specs/regret_analysis_spec.md) |
| Current-vs-policy workflow and status JSON | [docs/specs/current_vs_policy_workflow_spec.md](docs/specs/current_vs_policy_workflow_spec.md) |
| Monitoring snapshot and diff JSON | [docs/specs/monitoring_spec.md](docs/specs/monitoring_spec.md) |
| Light Monitoring / What Changed summary JSON | [docs/specs/light_monitoring_summary_spec.md](docs/specs/light_monitoring_summary_spec.md) |
| Metric formulas, windows, estimators, rounding | [docs/specs/metrics_specification.md](docs/specs/metrics_specification.md) |
| Optimization Engine roles, current optimizer output disclosure, and target-only optimizer boundaries | [docs/specs/optimization_engine_layer_spec.md](docs/specs/optimization_engine_layer_spec.md) |
| Stress, factor, macro, regime, and stress CSV/JSON artifacts | [docs/specs/stress_testing_spec.md](docs/specs/stress_testing_spec.md) |
| Scenario Library and normalized scenario outputs | [docs/specs/scenario_library_spec.md](docs/specs/scenario_library_spec.md) |
| Portfolio construction and weight-release outputs | [docs/specs/portfolio_construction_policy.md](docs/specs/portfolio_construction_policy.md) |
| Production statuses and release semantics | [docs/specs/production_workflow.md](docs/specs/production_workflow.md) |
| Data inputs, data quality, and data-output boundaries | [DATA.md](DATA.md) |
| Output verification and artifact checks | [TESTING.md](TESTING.md) |
| UI, dashboard, HTML, and visual styling | [DESIGN.md](DESIGN.md) |

## Update Rules

Update [OUTPUTS.md](OUTPUTS.md) when any of these change:

- a new output folder or generated artifact is added
- an output folder, file name, or artifact format is renamed or removed
- JSON/CSV/TXT/HTML/PDF-style report contracts change
- report sections, commentary files, snapshots, or generated packages change meaningfully
- generated-vs-source boundaries change
- portfolio-first subject materialization, `run_optimization.py`, `run_report.py`, or candidate scripts
  change what they write
- visual/report formatting rules for generated HTML or PDF-style artifacts change
- verification requirements for generated outputs change

Also update related docs when needed:

- [SPEC.md](SPEC.md) for general output contract changes.
- [docs/specs/reporting_outputs_spec.md](docs/specs/reporting_outputs_spec.md) for detailed report artifact contract changes.
- Owning detailed specs for metrics, stress, scenario, data, optimizer, or production-status behavior.
- [README.md](README.md) for user-facing commands, folders, and output descriptions.
- [TESTING.md](TESTING.md) for output verification strategy.
- [CHANGELOG.md](CHANGELOG.md) for meaningful completed output/reporting changes.
- [DECISIONS.md](DECISIONS.md) when a key output contract or formatting decision is made.
- [KNOWN_ISSUES.md](KNOWN_ISSUES.md) when an output/reporting limitation or bug is discovered but not fixed immediately.

Do not update this file for routine generated-output refreshes that do not change format, meaning, naming, workflow, or contract.

## Verification

For output/reporting changes, use [TESTING.md](TESTING.md).

Typical checks:

- focused tests for the affected report, metric, stress, scenario, or commentary path
- `python run_report.py` when report orchestration or generated artifacts change
- affected candidate or robust script when variant output behavior changes
- artifact inspection for changed JSON/CSV/TXT/HTML/PDF-style outputs
- Markdown link and stale-reference checks when output docs or artifact names change
