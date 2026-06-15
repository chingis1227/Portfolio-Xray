# Runtime entrypoints (Core MVP vs legacy)

Portfolio MRI is **diagnosis-first**. Use the active commands below for the Core MVP. The canonical Blocks 5-9 demo is the vertical-flow script in section D; section C is an explicit factory-id compatibility path when the candidate id is already known. Everything else is legacy, research, advanced, or an internal engine invoked by those commands.


## Command taxonomy

| Journey step | Primary command | Writes / role | Boundary |
| --- | --- | --- | --- |
| Diagnosis-only | `python run_core_diagnostics.py` for Blocks 1-3, or `python run_portfolio_review.py` for full diagnosis materialization | `analysis_subject/` diagnostics and diagnosis bundle where applicable | Must not make root candidate/comparison/verdict files authoritative |
| Generate one selected candidate | `python scripts/run_blocks_5_to_9_vertical_flow.py --method equal_weight` (calls Block 7 adapter) | `candidate_generation.json` for one explicit attempt | Candidate is diagnostic evidence, not a recommendation |
| Compare and verdict | Vertical demo continues into Block 8/9; technical boundary is `python run_compare_variants.py --block8-only --candidate ID` after candidate evidence exists | `current_vs_candidate.json`, then `decision_verdict.json` / grounding in the vertical flow | Block 8 compares trade-offs; Block 9 decides action / no-action / no-trade / evidence-insufficient |
| Full demo / testing | `python scripts/run_blocks_5_to_9_vertical_flow.py --method equal_weight` | Diagnosis -> Launchpad -> Builder setup -> Candidate Generation -> Compare -> Verdict -> AI grounding | This is the canonical demo path for the staged user journey |
| Explicit factory-id compatibility | `python run_portfolio_review.py --candidates equal_weight` | Diagnosis plus known backend candidate id and comparison | Use only when the factory id is already known; it bypasses the visible Builder-to-Block-7 artifact loop |
| Advanced/research batch | `python run_portfolio_review.py --with-candidates` or `python run_portfolio_review.py --mode full` | Multi-candidate factory/comparison artifacts | Not the Core MVP demo story |

## Windows console encoding

CLI help text must stay readable in a default Windows PowerShell / CP1251 console. Runtime help should avoid non-ASCII glyphs in argparse strings. If a local shell still mis-renders project documentation or logs, run `$env:PYTHONIOENCODING='utf-8'` before the command; this should be a fallback, not a requirement for `--help`.

## Active Core MVP (use these)

### A. Core diagnostics only (Blocks 1-3)

```bash
python run_core_diagnostics.py
```

**Purpose:** Input Layer -> Portfolio Diagnosis -> Stress Test Lab.

**Writes (under `{output_dir_final}/analysis_subject/`):** input/setup JSON, `portfolio_xray.json`,
`stress_report.json`, snapshots, `output_manifest.json`, and related Block 1-3 contracts.

**Does not run:** Problem Classification, Candidate Launchpad, candidate factory, comparison,
Decision Verdict, AI Commentary, monitoring, optimizers, PDF/CSV/HTML exports (default `site_api`).

**Console label:** `Mode: core_diagnostics_only`

### B. Full current product workflow

```bash
python run_portfolio_review.py
```

**Purpose:** Input -> Diagnosis -> Stress -> Client Fit -> Problem Classification -> Candidate
Launchpad -> Portfolio Alternatives Builder -> diagnosis grounding. **Candidates disabled by
default** (no optimizer zoo).

**Console label:** `Mode: product_diagnosis_workflow`, `Candidates: disabled by default`; the flow
line includes Client Fit and Builder setup.

### C. Full workflow + one explicit backend candidate (compatibility path)

```bash
python run_portfolio_review.py --candidates equal_weight
```

**Purpose:** Full diagnosis path plus one explicit factory candidate id -> Current vs Candidate ->
Decision Verdict. Use this when you already know the backend id; it is not the canonical Builder
setup -> Candidate Generation demo path and does not prove the visible Block 6/7 loop.

**Console label:** `Mode: product_one_candidate`, `Selected candidate: equal_weight`, plus
`Path classification: explicit factory-id compatibility path`. This warning is intentional: this
path remains useful for known backend ids, but it is not the canonical visible Builder-to-Block-7
demo handoff.

Optional flags: `--dry-run`, `--no-cache`, `--with-pdf` (explicit PDF only), `--with-candidates`
(backend research batch - **not** Core MVP default).

### D. Blocks 5-9 vertical demo (one selected hypothesis)

```bash
python scripts/run_blocks_5_to_9_vertical_flow.py --method equal_weight
```

**Purpose:** Diagnosis-only review -> selected Launchpad card -> Builder setup -> one Candidate
Generation attempt -> scoped Current vs Candidate -> direct Decision Verdict -> AI Commentary
grounding. The default demo prefers a reference or mixed-evidence card when one exists and tests
Equal Weight first. It clears stale vertical-loop root artifacts before the one-candidate run so an
old candidate zoo is not treated as current product evidence.

**Boundary wording:** Builder setup is not a candidate; Candidate Generation is one diagnostic attempt, not a recommendation; reference tests are diagnostic comparisons; Decision Verdict is where action/no-action, no-trade, and evidence-insufficient outcomes are evaluated.

**Console label:** `Blocks 5-9 vertical flow completed.`

This is the only current full-demo command that proves the visible product loop from Launchpad to
Builder setup, one Candidate Generation attempt, Block 8 comparison, Block 9 verdict, and AI
Commentary grounding.

## Internal engines (do not treat as product CLI)

| Script | Role |
| --- | --- |
| `run_report.py` | Calculation/materialization engine; prefer wrappers above for CLI use |
| `run_candidate_factory.py` | Candidate builders; only via explicit review flags |
| `run_compare_variants.py` | Comparison/decision package; `--block8-only --candidate ID` is the vertical-loop comparison boundary |
| `scripts/generate_candidate_from_builder_setup.py` | Block 7 one-attempt adapter used by the vertical demo |

Direct `python run_report.py --materialize-analysis-subject` is **legacy/advanced** CLI surface.

FastAPI staged diagnosis does not require operators to run a root CLI command. The normal staged
adapter calls the in-process service `src/review_runtime/staged_diagnosis_service.py`, which reuses
`run_report.run_materialize_analysis_subject_report` and writes the same run-local
`analysis_subject/` artifacts. Set `PMRI_STAGED_REVIEW_RUNTIME=subprocess` only for compatibility
debugging when the older `run_report.py` / `run_portfolio_review.py` subprocess boundary is needed.
The hosted FastAPI default allows one staged diagnosis worker at a time
(`PMRI_STAGED_REVIEW_MAX_WORKERS=1`) to avoid overlapping memory-heavy market-data and artifact
materialization work on small Render instances. Candidate generation also constrains common numeric
thread pools in its factory child process. Increase these limits only after checking service memory
metrics under live staged-review and candidate-generation load.
Portfolio review endpoints exposed by FastAPI are protected internal API surfaces as of the
security remediation Session 02. Normal browser traffic must enter through the Next.js
`app/api/portfolio/*` compatibility routes, which authenticate the user and then send a short-lived
signed internal context to FastAPI. For local-only demos without Supabase, set
`PMRI_PORTFOLIO_API_AUTH_MODE=dev_bypass` for Next.js and `PMRI_FASTAPI_AUTH_MODE=dev_bypass` for
FastAPI in a non-production shell; production deployments must configure
`PMRI_FASTAPI_INTERNAL_SECRET` and must not enable either bypass.

## Legacy / research / advanced (not Core MVP)

Moved under [`legacy/runners/`](../legacy/runners/) with root deprecation wrappers:

- Policy / MVP: `run_optimization.py`, `run_mvp_workflow.py`
- Optimizer zoo: `run_equal_weight.py`, `run_risk_parity.py`, min-var / robust / HRP / max-div / risk-budget scripts
- Utilities: `run_stress_variant.py`, `run_rebalance.py`, `run_view_after_optimization.py`, `run_compare_ew_rp.py`
- PDF rebuild: `rebuild_pdf_reports.py` (explicit export only)

Root legacy wrappers now print a runtime warning before delegating to `legacy/runners/`: they are
legacy compatibility runners and are not the Core MVP product path.

Data/universe maintenance (advanced): `run_etf_universe.py`, `run_stock_universe.py`, `run_ibkr_market_data.py`

### Root `run_*.py` inventory and retirement classes

Use this inventory before removing, hiding, or changing warnings on root runner scripts. Retirement
means removal from the current operator surface, not deletion of useful implementation history.
No script in this table should be deleted unless a replacement command is documented here and the
focused tests or smoke checks for that use case pass.

| Script | Class | Operator boundary |
| --- | --- | --- |
| `run_core_diagnostics.py` | Current product | Core MVP Blocks 1-3 diagnosis entrypoint. |
| `run_portfolio_review.py` | Current product | Default portfolio-first diagnosis workflow; explicit candidate flags are compatibility or advanced paths. |
| `scripts/run_blocks_5_to_9_vertical_flow.py` | Current product demo | Canonical one-candidate vertical demo, although it is not a root `run_*.py` file. |
| `run_report.py` | Internal/report engine | Calculation and materialization engine; use directly only for advanced or explicit report materialization work. |
| `run_candidate_factory.py` | Advanced/internal engine | Candidate factory orchestration; prefer review flags or vertical-flow adapter for product paths. |
| `run_compare_variants.py` | Advanced/internal engine | Comparison and verdict package writer; product demos call it through the vertical flow. |
| `run_etf_universe.py` | Advanced data maintenance | ETF universe validation/export/enrichment command. |
| `run_stock_universe.py` | Advanced data maintenance | Stock universe validation/export command. |
| `run_ibkr_market_data.py` | Advanced data smoke | Read-only market-data smoke command. |
| `run_optimization.py` | Legacy compatibility | Legacy policy optimizer wrapper under `legacy/runners/`; not a Core MVP entrypoint. |
| `run_mvp_workflow.py` | Legacy compatibility | Older policy/current/full-decision workflow wrapper; not the current product journey. |
| `run_equal_weight.py` | Legacy compatibility | Candidate builder wrapper retained for explicit optimizer/candidate smoke checks. |
| `run_equal_weight_by_asset_class.py` | Legacy compatibility | Candidate builder wrapper retained for explicit advanced checks. |
| `run_risk_parity.py` | Legacy compatibility | Candidate builder wrapper retained for explicit advanced checks. |
| `run_risk_budget_by_asset.py` | Legacy compatibility | Candidate builder wrapper retained for explicit advanced checks. |
| `run_risk_budget_by_asset_class.py` | Legacy compatibility | Candidate builder wrapper retained for explicit advanced checks. |
| `run_hierarchical_risk_parity.py` | Legacy compatibility | Candidate builder wrapper retained for explicit advanced checks. |
| `run_minimum_variance.py` | Legacy compatibility | Candidate builder wrapper retained for explicit advanced checks. |
| `run_minimum_variance_advanced.py` | Legacy compatibility | Candidate builder wrapper retained for explicit advanced checks. |
| `run_minimum_variance_uncapped.py` | Legacy compatibility | Candidate builder wrapper retained for explicit advanced checks. |
| `run_minimum_cvar_constrained.py` | Legacy compatibility | Candidate builder wrapper retained for explicit advanced checks. |
| `run_minimum_cvar_uncapped.py` | Legacy compatibility | Candidate builder wrapper retained for explicit advanced checks. |
| `run_maximum_diversification.py` | Legacy compatibility | Candidate builder wrapper retained for explicit advanced checks. |
| `run_maximum_diversification_unconstrained.py` | Legacy compatibility | Candidate builder wrapper retained for explicit advanced checks. |
| `run_robust_mean_variance_constrained.py` | Legacy compatibility | Robust candidate wrapper retained for explicit advanced checks. |
| `run_robust_mean_variance_uncapped.py` | Legacy compatibility | Robust candidate wrapper retained for explicit advanced checks. |
| `run_robust_mv_lambda_calibration.py` | Legacy compatibility | Robust calibration wrapper retained for explicit advanced checks. |
| `run_robust_scenario_optimization.py` | Legacy compatibility | Robust scenario wrapper retained for explicit advanced checks. |
| `run_robust_scenario_portfolio_report.py` | Legacy compatibility/export | Robust scenario report wrapper retained for explicit export checks. |
| `run_advanced_mv_lambda_sensitivity.py` | Legacy compatibility/research | Research wrapper retained for explicit sensitivity-analysis checks. |
| `run_compare_ew_rp.py` | Legacy compatibility/research | Older equal-weight versus risk-parity comparison helper. |
| `run_rebalance.py` | Legacy compatibility | Legacy rebalancing helper; not a current product recommendation path. |
| `run_stress_variant.py` | Legacy compatibility/export | Variant stress/report rebuild helper retained for explicit artifact refresh work. |
| `run_view_after_optimization.py` | Legacy compatibility | View After Optimization helper retained for its governed legacy protocol. |

Candidate for future retirement is a state reached only after a separate session proves that the
script has no canonical doc or test dependency, a replacement command is documented in this file,
and the replacement smoke check covers the old use case.

## Stale candidate isolation

`run_core_diagnostics.py` materializes only `analysis_subject/` and does not invoke the candidate
factory or comparison writers. A prior candidate run on disk does not change Blocks 1-3 outputs.

## Related docs

- [docs/product_flow_operator_guide.md](product_flow_operator_guide.md)
- [OUTPUTS.md](../OUTPUTS.md)
- [README.md](../README.md) command table
