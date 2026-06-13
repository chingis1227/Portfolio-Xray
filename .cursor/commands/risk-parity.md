---
description: Full Risk-Parity baseline run, metrics, stress, EW vs RP comparison, and PDF refresh
---

Run the **full Risk-Parity baseline** strictly under the project rules. Handle one variant per request; do not recalculate Main or Equal-Weight unless the user explicitly asks.

### 1) Run command (the only required command)

From the **repository root** where `config.yml` and the scripts live:

```bash
python run_risk_parity.py
```

This script already:
- builds risk-parity weights from the same eligible universe and data as the baseline policy, without RC caps or policy overlays; see the script docstring;
- when status is **OK** or **APPROXIMATE**, runs the **full** report through `run_portfolio_report_for_weights` (metrics, stress, CSV, JSON, `commentary.txt`, and stress commentary through the pipeline);
- when the baseline is **infeasible**, writes only `summary.json` / `summary.txt` and stops without a full report; do not expect a full metrics/stress/CSV package;
- calls **`try_rebuild_pdfs_after_variant`** at the end: it refreshes **EW vs RP** comparison (`run_compare_ew_rp.py`) and rebuilds PDFs in `pdf files/`.

**Do not** add manual weight edits to `config.yml`.

### 2) After a successful run, read and briefly report the key results

Artifact directory: **`risk parity portfolio/`** in the repository root. Do not use any legacy final-results directory or another root.

Always check existence and meaning of:
- `risk parity portfolio/summary.txt`, `risk parity portfolio/summary.json`
- `risk parity portfolio/weights.json`, `weights.txt` if present
- `risk parity portfolio/stress_report.json`
- `risk parity portfolio/commentary.txt`, `stress_commentary.txt` if generated
- `risk parity portfolio/results_csv/` for rolling factor betas, correlation matrices, and other stress-factor outputs

In the user-facing answer, include:
- baseline and solver status from `summary.json` / `summary.txt`; for **APPROXIMATE**, include the summary note
- **top 10 weights** in descending order
- **RC_vol by asset** from `weights.txt`; **RC source:** solver / target parity, with fallback logic in `run_risk_parity.py`
- **solver_status** and **max_rc_error** if present in `summary.json`
- key window metrics that exist in summary: CAGR, Vol, MaxDD, Sharpe, Sortino, Beta (`beta_portfolio`), Corr_base
- stress `status` from `stress_report.json` / summary, fail or skip reason, **Client-fit (MaxDD gate)** / `portfolio_valid` from summary or meta
- confirmation that the log/output did not show failures in `run_compare_ew_rp.py` or PDF rebuild; if failures occurred, quote the warning

### 3) If the run fails or the baseline is infeasible

- Show the exact reason and stage: config validation, data, infeasible RP, stress, or PDF.
- If **infeasible**, describe `reason` from summary and state that the full pipeline did not run.
- List which files were still created in `risk parity portfolio/`.
- Suggest the next step, such as checking `config.yml`, cache, eligible asset count, or pandoc/xelatex for PDF generation.

### 4) Optional only when the user explicitly asks

- The **Policy vs EW vs RP** triplet is refreshed after the full Main report (`run_report` / optimization with report), not by this script. Do not run `run_compare_variants.py` unless the user explicitly asks to refresh the Policy comparison.
