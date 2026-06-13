---
description: Full Equal-Weight baseline run, metrics, stress, finalization, EW vs RP comparison, and PDF refresh
---

Run the **full Equal-Weight baseline** strictly under the project rules. Handle one variant per request; do not recalculate Main or Risk Parity unless the user explicitly asks.

### 1) Run command (the only required command)

From the **repository root** where `config.yml` and the scripts live:

```bash
python run_equal_weight.py
```

This script already:
- builds equal weights from the same universe and coverage rules as the policy report;
- runs the **full** report through `run_portfolio_report_for_weights` (metrics, stress, CSV, JSON, `commentary.txt`, and stress commentary through the pipeline);
- calls **`try_rebuild_pdfs_after_variant`** at the end: it refreshes **EW vs RP** comparison (`run_compare_ew_rp.py`) and rebuilds PDFs in `pdf files/`.

**Do not** add manual weight edits to `config.yml`.

### 2) After a successful run, read and briefly report the key results

Artifact directory: **`equal-weight portfolio/`**. Do not invent another root.

Always check existence and meaning of:
- `equal-weight portfolio/summary.txt`, `equal-weight portfolio/summary.json`
- `equal-weight portfolio/weights.json`, `weights.txt` if present
- `equal-weight portfolio/stress_report.json`
- `equal-weight portfolio/commentary.txt`, `stress_commentary.txt` if generated
- `equal-weight portfolio/results_csv/` for rolling betas, matrices, and other stress-factor outputs

In the user-facing answer, include:
- baseline status from `summary.json` / `summary.txt`
- top weights in descending order
- key window metrics that exist in summary: CAGR, Vol, MaxDD, Sharpe, Sortino, Beta, Corr_base
- stress `status`, failure or warning reason, and client-fit / `portfolio_valid` if present in meta or summary
- confirmation that the log/output did not show failures in `run_compare_ew_rp.py` or PDF rebuild; if failures occurred, quote the warning

### 3) If the run fails

- Show the exact reason and stage: data, feasibility, stress, or PDF.
- List which files were still created in `equal-weight portfolio/`.
- Suggest the next step, such as checking `config.yml`, cache, or pandoc/xelatex for PDF generation.

### 4) Optional only when the user explicitly asks

- The **Policy vs EW vs RP** triplet is refreshed after the full Main report (`run_report` / optimization with report), not by this script. Do not run `run_compare_variants.py` unless the user explicitly asks to refresh the Policy comparison.
