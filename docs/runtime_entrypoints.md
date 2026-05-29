# Runtime entrypoints (Core MVP vs legacy)

Portfolio MRI / Portfolio X-Ray is **diagnosis-first**. Only three commands are active Core MVP
runtime entrypoints at the repository root. Everything else is legacy, research, advanced, or an
internal engine invoked by those commands.

## Active Core MVP (use these)

### A. Core diagnostics only (Blocks 1-3)

```bash
python run_core_diagnostics.py
```

**Purpose:** Input Layer → Portfolio X-Ray → Stress Test Lab.

**Writes (under `{output_dir_final}/analysis_subject/`):** input/setup JSON, `portfolio_xray.json`,
`stress_report.json`, snapshots, `output_manifest.json`, and related Block 1-3 contracts.

**Does not run:** Problem Classification, Candidate Launchpad, candidate factory, comparison,
Decision Verdict, AI Commentary, monitoring, optimizers, PDF/CSV/HTML exports (default `site_api`).

**Console label:** `Mode: core_diagnostics_only`

### B. Full current product workflow

```bash
python run_portfolio_review.py
```

**Purpose:** Input → X-Ray → Stress → Problem Classification → Candidate Launchpad → AI Commentary /
Monitoring context. **Candidates disabled by default** (no optimizer zoo).

**Console label:** `Mode: product_diagnosis_workflow`, `Candidates: disabled by default`

### C. Full workflow + one explicit candidate

```bash
python run_portfolio_review.py --candidates equal_weight
```

**Purpose:** Full product path plus one selected candidate → Current vs Candidate → Decision Verdict.

**Console label:** `Mode: product_one_candidate`, `Selected candidate: equal_weight`

Optional flags: `--dry-run`, `--no-cache`, `--with-pdf` (explicit PDF only), `--with-candidates`
(backend research batch — **not** Core MVP default).

## Internal engines (do not treat as product CLI)

| Script | Role |
| --- | --- |
| `run_report.py` | Calculation/materialization engine; prefer wrappers above for CLI use |
| `run_candidate_factory.py` | Candidate builders; only via explicit review flags |
| `run_compare_variants.py` | Comparison/decision package; factory `--then-compare` or explicit compare |

Direct `python run_report.py --materialize-analysis-subject` is **legacy/advanced** CLI surface.

## Legacy / research / advanced (not Core MVP)

Moved under [`legacy/runners/`](../legacy/runners/) with root deprecation wrappers:

- Policy / MVP: `run_optimization.py`, `run_mvp_workflow.py`
- Optimizer zoo: `run_equal_weight.py`, `run_risk_parity.py`, min-var / robust / HRP / max-div / risk-budget scripts
- Utilities: `run_stress_variant.py`, `run_rebalance.py`, `run_view_after_optimization.py`, `run_compare_ew_rp.py`
- PDF rebuild: `rebuild_pdf_reports.py` (explicit export only)

Data/universe maintenance (advanced): `run_etf_universe.py`, `run_stock_universe.py`, `run_ibkr_market_data.py`

## Stale candidate isolation

`run_core_diagnostics.py` materializes only `analysis_subject/` and does not invoke the candidate
factory or comparison writers. A prior candidate run on disk does not change Blocks 1-3 outputs.

## Related docs

- [docs/product_flow_operator_guide.md](product_flow_operator_guide.md)
- [OUTPUTS.md](../OUTPUTS.md)
- [README.md](../README.md) command table
