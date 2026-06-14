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

## Legacy / research / advanced (not Core MVP)

Moved under [`legacy/runners/`](../legacy/runners/) with root deprecation wrappers:

- Policy / MVP: `run_optimization.py`, `run_mvp_workflow.py`
- Optimizer zoo: `run_equal_weight.py`, `run_risk_parity.py`, min-var / robust / HRP / max-div / risk-budget scripts
- Utilities: `run_stress_variant.py`, `run_rebalance.py`, `run_view_after_optimization.py`, `run_compare_ew_rp.py`
- PDF rebuild: `rebuild_pdf_reports.py` (explicit export only)

Root legacy wrappers now print a runtime warning before delegating to `legacy/runners/`: they are
legacy compatibility runners and are not the Core MVP product path.

Data/universe maintenance (advanced): `run_etf_universe.py`, `run_stock_universe.py`, `run_ibkr_market_data.py`

## Stale candidate isolation

`run_core_diagnostics.py` materializes only `analysis_subject/` and does not invoke the candidate
factory or comparison writers. A prior candidate run on disk does not change Blocks 1-3 outputs.

## Related docs

- [docs/product_flow_operator_guide.md](product_flow_operator_guide.md)
- [OUTPUTS.md](../OUTPUTS.md)
- [README.md](../README.md) command table
