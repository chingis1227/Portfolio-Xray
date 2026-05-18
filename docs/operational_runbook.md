# Operational Runbook

Short guide for when to run optimization, how to handle universe and config changes, and how to read run results. See `docs/specs/production_workflow.md` for status and gate semantics.

## 0. File-First MVP Workflow

The file-first MVP path is **`input -> diagnosis -> comparison -> action`**. It is implemented as separate CLI entrypoints; `run_mvp_workflow.py` is an optional thin orchestrator that calls them in order without changing formulas or optimizer logic.

| Stage | Purpose | Primary commands | Key artifacts |
| --- | --- | --- | --- |
| **Input** | Universe, profile, optional `current_weights` | Edit `config.yml`; validate via any `run_*.py` load | `config.yml`, optional `assets.yml` |
| **Diagnosis** | Policy optimize/report, stress, metrics | `run_optimization.py`, `run_report.py`; optional `run_report.py --materialize-current` | `Main portfolio/run_result.json`, `snapshot_*.json`, `stress_report.json`, `portfolio_xray.json` |
| **Comparison** | Rank candidates, robustness, health | `run_candidate_factory.py` (optional), `run_compare_variants.py` | `candidate_comparison.json`, `robustness_scorecard.json`, `portfolio_health_score.json` |
| **Action** | Selection, trades, monitoring, package | Emitted by `run_compare_variants.py` / comparison builder | `selection_decision.json`, `action_plan.json`, `monitoring_diff.json`, `decision_package_summary.json` |

**Recommended orchestration (optional):**

```bash
python run_mvp_workflow.py --workflow policy-only
python run_mvp_workflow.py --workflow policy-current
python run_mvp_workflow.py --workflow full-decision
python run_mvp_workflow.py --workflow diagnosis-only
python run_mvp_workflow.py --dry-run
```

| `--workflow` | When to use |
| --- | --- |
| `policy-only` (default) | Fresh policy optimize + report, then comparison/decision package. |
| `policy-current` | Same as policy-only, plus `--materialize-current` when `current_weights` are set (No-Trade versus current). |
| `full-decision` | Policy path, optional current sidecar, candidate factory (`default_v1`), comparison via factory `--then-compare`, PDF rebuild. |
| `diagnosis-only` | Refresh reports from existing weights (`run_report.py`) without re-optimization. |

Manual equivalent for combined current-vs-policy (see [current_vs_policy_workflow_spec.md](specs/current_vs_policy_workflow_spec.md)):

1. `python run_optimization.py`
2. `python run_report.py` (skipped when optimization runs with report enabled)
3. `python run_report.py --materialize-current` (when `current_weights` are configured)
4. `python run_compare_variants.py`
5. `python rebuild_pdf_reports.py` (optional client PDFs)

`run_optimization.py` already chains `run_report.py` unless `--no-report` is set. Use `--skip-optimize` on `run_mvp_workflow.py` when weights and policy snapshots are already current.

## 1. When To Re-Run Optimization

Re-run `python run_optimization.py` from the project root when any of the following happens. The optimizer is the single-stage max-return policy optimizer with weight bounds and soft vol/return targets; see `docs/specs/portfolio_construction_policy.md`.

| Trigger | Action |
| --- | --- |
| **Calendar** | Run monthly or quarterly on a fixed schedule, for example the first business day of the month. |
| **Deviation** | Current or last-rebalance weights drift from target, for example max `|w_current - w_target| > 2%` or total `|delta w| > 5%`. Consider rebalancing and/or re-running optimization. |
| **Universe change** | Any ticker add/remove in `config.yml` requires a full re-run. |
| **Profile / mandate change** | Changes to `client_profile`, `target_vol_annual`, `target_max_drawdown_pct`, or other policy fields require a full re-run. |
| **Stress diagnostics** | `DIAG_ATTENTION` or `FAIL_STRESS` is informational and does not prevent release. Re-run only if the portfolio architecture or config changes. |

## 2. Universe Changes

Adding a ticker: add it to `config.yml` under `tickers`, then run a full optimization. Do not patch existing weights manually; the new weights file will include the new ticker.

Removing a ticker: remove it from `config.yml`, then run a full optimization. The new `portfolio_weights.yml` will omit the ticker or assign zero weight.

There is no partial update path. Every investable-universe change requires a full `run_optimization.py` run.

## 3. Reading `run_result.json`

After each run, check `output_dir_final/run_result.json`, for example `Main portfolio/run_result.json`.

| Field | Meaning |
| --- | --- |
| **status** | `APPROVED`, `OK_FALLBACK`, or `FAIL_*`; see `docs/specs/production_workflow.md`. |
| **weights** | Target weights; empty when a blocking `FAIL_*` prevents writing weights. |
| **violations** | List of `{ "code", "details" }`, including mandate, data, stress, and warning entries. |
| **next_actions** | Suggested next steps when violations or failures occur. |
| **resolved_config** | Merged config used for the run, including profile defaults and overrides. |

If status is `FAIL_DATA` or `FAIL_MANDATE`, weights were not written. Follow `next_actions`, fix data/config/mandate inputs, and rerun before using the output for allocation.

If status is `APPROVED` or `OK_FALLBACK`, weights were written to `portfolio_weights.yml`. Treat them as target weights, while reviewing any non-blocking violations such as stress diagnostics or young-ETF warnings.

## 4. Output Files

| File | Location | Purpose |
| --- | --- | --- |
| `portfolio_weights.yml` | `output_dir_final` | Target weights for execution; present only if weights were written. |
| `run_result.json` | `output_dir_final` | Status, violations, next actions, and resolved config. Always written after a run. |
| `snapshot.json` | `output_dir_final` | Snapshot of weights, RC, constraints, and stress summary; written when weights are written. |
| `ips_summary.txt` | `output_dir_final` | One-page mandate summary and actions by status; written after every run. |

Report CSV and other report outputs are produced by `run_report.py`, which runs after optimization when reporting is enabled. If report generation fails, weights and `run_result.json` remain saved.

## 5. First Run

1. Check `config.yml`: `tickers`, `client_profile`, and `investor_currency` are set. When needed, set `liquidity_need_months`, `monthly_expenses`, and `portfolio_value` for the liquidity floor calculation.
2. Run `python run_optimization.py` from the project root. On first data load, add `--no-cache` if you want a fresh data download.
3. Open `output_dir_final/run_result.json` and check `status`. If status is `APPROVED` or `OK_FALLBACK`, weights were written to `portfolio_weights.yml` and can be used as target weights. For `OK_FALLBACK`, review `rc_breaches` if present.
4. If there are violations, follow `next_actions`. For `FAIL_MANDATE`, the full-history drawdown breached the limit or data was unavailable; adjust risk/mandate inputs and rerun. Stress `DIAG_*` entries do not block release.

## 6. Recurring Run

1. Refresh data when needed by running with `--no-cache`.
2. Run `run_optimization.py` on the chosen schedule, for example the first business day of each month.
3. Compare with the prior run: check status and violations in the new `run_result.json`. If status changes or new violations appear, review `next_actions` and adjust config or mandate if needed.
4. For rebalance trade lists, run `run_rebalance.py --current current_positions.yml --target <path_to_portfolio_weights.yml>`. Use `--threshold` and `--min-trade` when needed. Consider turnover before deciding to rebalance.
