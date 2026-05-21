# Operational Runbook

Short guide for the portfolio-first review command and for legacy policy optimization compatibility.
See `docs/specs/production_workflow.md` for legacy policy status and gate semantics. Blocks 1-5
MVP core reliability handoff:
[Blocks 1-5 MVP Core Reliability Plan](exec_plans/2026-05-21_blocks_1_5_mvp_core_reliability_plan.md).

## 0. Portfolio-First Review Workflow

The portfolio-first path starts with the resolved `analysis_subject`, writes its diagnostics first,
and only then builds or compares candidate portfolios.

```bash
python run_portfolio_review.py
python run_portfolio_review.py --dry-run
python run_portfolio_review.py --mode full --no-skip-existing
python run_portfolio_review.py --mode full --resume-candidates
python run_portfolio_review.py --skip-candidates
python run_portfolio_review.py --candidate-profile default_v1
```

| Review mode | Command | Factory profile | Typical use |
| --- | --- | --- | --- |
| **Core** (default) | `python run_portfolio_review.py` or `--mode core` | `core_v1` (benchmarks + risk budgets, 6 builders) | Routine monthly review within normal session limits |
| **Full** | `python run_portfolio_review.py --mode full` | `default_v1` (16 builders incl. optimizers + robust) | Explicit refresh when all script-backed candidates are needed |
| **Full resume** | `python run_portfolio_review.py --mode full --resume-candidates` | `default_v1` with factory `--resume` | Recovery after an interrupted full factory run |

| Stage | Purpose | Primary command | Key artifacts |
| --- | --- | --- | --- |
| **Subject diagnosis** | Diagnose the starting portfolio before alternatives | `run_report.py --materialize-analysis-subject` via `run_portfolio_review.py` | `{output_dir_final}/analysis_subject/` |
| **Candidates** | Build non-policy comparison alternatives | `run_candidate_factory.py` via `run_portfolio_review.py` | Candidate output folders, `candidate_factory_run.json` |
| **Comparison** | Merge available subject/candidate evidence | `run_compare_variants.py` via factory `--then-compare` or directly | `candidate_comparison.json` (`candidate_menu` block) and decision-package artifacts |
| **Package** | Refresh portfolio-first PDFs | `rebuild_pdf_reports.py --portfolio-first` via `run_portfolio_review.py` unless `--skip-pdf` is set | `Main portfolio_decision_package.pdf`, `analysis_subject_*` PDFs when sidecar outputs exist |
| **Package (legacy)** | Full EW/RP/policy/baseline PDF suite | `run_portfolio_review.py --legacy-full-pdf` or `rebuild_pdf_reports.py` without `--portfolio-first` | All PDFs under `pdf files/` |

The default portfolio-first command does not call `run_optimization.py`. The old policy workflow
below remains available for compatibility and historical policy runs.

### Blocks 1-5 MVP acceptance (operator checklist)

Use this checklist when validating the first-five product blocks without prior chat context.

| Step | Action | Pass criterion |
| --- | --- | --- |
| 1 | Configure `analysis_subject` with five tickers and explicit weights summing to `1.0` for `current_portfolio` / `model_portfolio` | Config validation accepts; overallocated positive sums above `1.0` fail before reports |
| 2 | Run routine review | `python run_portfolio_review.py --mode core --skip-pdf` completes subject materialization, `core_v1` factory, and comparison |
| 3 | Open subject folder first | `{output_dir_final}/analysis_subject/` contains `run_metadata.json`, `portfolio_xray.json`, `stress_report.json` |
| 4 | Read trust summaries | `data_trust_summary` / `data_trust_signals` and commentary `user_summary_lines` surface data-quality and young-ETF warnings when present |
| 5 | Confirm factory evidence | `candidate_comparison.json` → `candidate_menu.factory_evidence_status` is `current`, or warnings explain stale/missing factory evidence |
| 6 | Scan optimizer rows | Optimizer-backed rows are fair-comparison-ready or visibly `degraded` with readiness warning codes — not silent ordinary `available` evidence |

Offline regression gate (no network):

```bash
python -m pytest tests/test_blocks_1_5_mvp_smoke.py -q --basetemp='tmp\pytest_blocks_1_5_smoke'
```

Full verification matrix: [TESTING.md](../TESTING.md) Blocks 1-5 section; output map:
[OUTPUTS.md](../OUTPUTS.md) Blocks 1-5 MVP Output Acceptance.

### Runtime limits and partial menus

| Situation | What happens | What to do |
| --- | --- | --- |
| Routine review | Core mode builds six lightweight candidates; compare + decision package finish in one session when snapshots are fresh | `python run_portfolio_review.py` |
| Snapshots already match review `analysis_end` | Factory mostly `skipped_existing`; core path is fast | Default core command |
| Need all optimizers / robust suite | Full mode runs all 16 `default_v1` builders; can take hours when stale | `python run_portfolio_review.py --mode full --no-skip-existing` |
| Session/agent timeout | Subject may refresh; factory may not finish; compare may run on incomplete intended menu | Rerun `python run_portfolio_review.py --mode full --resume-candidates`; then read `candidate_factory_run.json`, `candidate_comparison.json` → `candidate_menu`, and row `unavailable_reason` |

**Trust rule:** stale candidates are marked `unavailable` in comparison — they are not silently scored.
**Interpretation rule:** `candidate_menu.is_partial_menu` and decision-package summary text disclose when selection used a **reduced** menu (core vs product `default_v1`) or when intended candidates are missing. Rankings apply only to scored rows in the intended menu.

**Resume after interrupt:** when a portfolio-first full factory run stops mid-menu, prefer the
orchestrator recovery command so subject materialization, factory resume, comparison, and packaging
stay in the same workflow:

```bash
python run_portfolio_review.py --mode full --resume-candidates
```

For advanced factory-only recovery, rerun with the same profile and candidate list:

```bash
python run_candidate_factory.py --profile default_v1 --resume
```

`candidate_factory_manifest.json` under `{output_dir_final}/` records completed steps; `--resume`
skips prior `succeeded` and fresh `skipped_existing` rows when `run_checksum` matches (profile,
menu, `analysis_end`, `config_fingerprint`). Failed steps are retried. Use `--force` to ignore
manifest skips. Optional parallel builders remain deferred ([ROADMAP.md](ROADMAP.md) `RM-921` non-resume scope).

### Robust suite prerequisites (Block 4 — `robust_suite` profile)

The factory **does not** run λ calibration. Robust MV builders (`robust_mv_constrained`, `robust_mv_uncapped`) read λ from:

1. `analysis_robust_mv_lambda_calibration/selected_lambda.txt` (after `python run_robust_mv_lambda_calibration.py`), or
2. `--robust-mv-lambda` on the builder CLI (factory does not pass this flag).

Before a **full** review that includes `robust_suite`, run λ calibration once per project root (or confirm `selected_lambda.txt` exists). Each factory step and comparison row for robust MV candidates carries `robust_paths_disclosure` / `construction_disclosure.robust_paths` with `lambda_resolution_key` and `lambda_ready_for_build`.

**`robust_scenario`** is a two-script chain that depends on **Main** stress artifacts, not on the candidate folder:

| Prerequisite | Location | Produced by |
| --- | --- | --- |
| `scenario_library_normalized.json` | `{output_dir_final}/` | `run_report.py` / stress pipeline on Main |
| `stress_report.json` | `{output_dir_final}/` | Same |

If either file is missing, the factory step is `skipped_dependency` (whole factory continues unless `--fail-fast`). This is **intentional shared calibration**: scenario weights use the Main scenario library and portfolio factor betas from the policy/Main report path, not a per-candidate stress library. Per-candidate `stress_report.json` after a successful build is a separate diagnostic for that portfolio only.

**Operator sequence for full menu with robust scenario:**

1. `python run_portfolio_review.py --mode full` (subject + core candidates), **or** ensure Main already has fresh `stress_report.json` and `scenario_library_normalized.json` from `python run_optimization.py` / `python run_report.py`.
2. `python run_robust_mv_lambda_calibration.py` when robust MV candidates are in scope.
3. Run factory (`run_portfolio_review.py --mode full` or `run_candidate_factory.py --profile default_v1`).

Inspect `candidate_factory_run.json` → `steps[]` → `robust_paths_disclosure` and `candidate_comparison.json` → `construction_disclosure.robust_paths` when λ source or Main prerequisites are unclear.

**Operator playbook (reason codes, exit codes, recovery):** see [section 8](#8-candidate-portfolio-factory-operator-playbook) below.

## 1. Legacy File-First MVP Policy Workflow

The old MVP policy path remains available for compatibility and historical policy runs. It is not
the default starting command for portfolio-first review. Use it only when the intended baseline is the
legacy policy portfolio generated by `run_optimization.py`.

| Stage | Purpose | Primary commands | Key artifacts |
| --- | --- | --- | --- |
| **Input** | Universe, profile, optional `current_weights` | Edit `config.yml`; validate via any `run_*.py` load | `config.yml`, optional `assets.yml` |
| **Diagnosis** | Policy optimize/report, stress, metrics | `run_optimization.py`, `run_report.py`; optional `run_report.py --materialize-current` | `Main portfolio/run_result.json`, `snapshot_*.json`, `stress_report.json`, `portfolio_xray.json` |
| **Comparison** | Rank candidates, robustness, health | `run_candidate_factory.py` (optional), `run_compare_variants.py` | `candidate_comparison.json`, `robustness_scorecard.json`, `portfolio_health_score.json` |
| **Action** | Selection, trades, monitoring, package | Emitted by `run_compare_variants.py` / comparison builder | `selection_decision.json`, `action_plan.json`, `monitoring_diff.json`, `decision_package_summary.json` |

**Legacy orchestration (optional):**

```bash
python run_mvp_workflow.py --workflow policy-only
python run_mvp_workflow.py --workflow policy-current
python run_mvp_workflow.py --workflow full-decision
python run_mvp_workflow.py --workflow diagnosis-only
python run_mvp_workflow.py --dry-run
```

| `--workflow` | When to use |
| --- | --- |
| `policy-only` (default) | Fresh legacy policy optimize + report, then comparison/decision package. |
| `policy-current` | Same as policy-only, plus `--materialize-current` when `current_weights` are set (No-Trade versus current). |
| `full-decision` | Legacy policy path, optional current sidecar, candidate factory (`default_v1`), comparison via factory `--then-compare`, PDF rebuild. |
| `diagnosis-only` | Refresh reports from existing weights (`run_report.py`) without re-optimization. |

Manual equivalent for combined current-vs-policy (see [current_vs_policy_workflow_spec.md](specs/current_vs_policy_workflow_spec.md)):

1. `python run_optimization.py`
2. `python run_report.py` (skipped when optimization runs with report enabled)
3. `python run_report.py --materialize-current` (when `current_weights` are configured)
4. `python run_compare_variants.py`
5. `python rebuild_pdf_reports.py` (optional client PDFs)

`run_optimization.py` already chains `run_report.py` unless `--no-report` is set. Use `--skip-optimize` on `run_mvp_workflow.py` when weights and policy snapshots are already current.

## 2. When To Re-Run Legacy Policy Optimization

Re-run `python run_optimization.py` from the project root only for the legacy policy workflow or
for compatibility checks that intentionally depend on generated policy weights. The optimizer is the
single-stage max-return policy optimizer with weight bounds and soft vol/return targets; see
`docs/specs/portfolio_construction_policy.md`.

| Trigger | Action |
| --- | --- |
| **Calendar** | Run monthly or quarterly on a fixed schedule, for example the first business day of the month. |
| **Deviation** | Current or last-rebalance weights drift from target, for example max `|w_current - w_target| > 2%` or total `|delta w| > 5%`. Consider rebalancing and/or re-running optimization. |
| **Universe change** | Any ticker add/remove in `config.yml` requires a full re-run. |
| **Profile / mandate change** | Changes to `client_profile`, `target_vol_annual`, `target_max_drawdown_pct`, or other policy fields require a full re-run. |
| **Stress diagnostics** | `DIAG_ATTENTION` or `FAIL_STRESS` is informational and does not prevent release. Re-run only if the portfolio architecture or config changes. |

## 3. Universe Changes In The Legacy Policy Flow

Adding a ticker: add it to `config.yml` under `tickers`, then run a full optimization. Do not patch existing weights manually; the new weights file will include the new ticker.

Removing a ticker: remove it from `config.yml`, then run a full optimization. The new `portfolio_weights.yml` will omit the ticker or assign zero weight.

There is no partial update path. Every investable-universe change requires a full `run_optimization.py` run.

## 4. Reading Legacy `run_result.json`

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

## 5. Legacy Policy Output Files

| File | Location | Purpose |
| --- | --- | --- |
| `portfolio_weights.yml` | `output_dir_final` | Target weights for execution; present only if weights were written. |
| `run_result.json` | `output_dir_final` | Status, violations, next actions, and resolved config. Always written after a run. |
| `snapshot.json` | `output_dir_final` | Snapshot of weights, RC, constraints, and stress summary; written when weights are written. |
| `ips_summary.txt` | `output_dir_final` | One-page mandate summary and actions by status; written after every run. |

Report CSV and other report outputs are produced by `run_report.py`, which runs after legacy
optimization when reporting is enabled. If report generation fails, weights and `run_result.json`
remain saved.

## 6. First Portfolio-First Run

1. Check `config.yml`: `analysis_subject`, `tickers`, `client_profile`, and `investor_currency`
   are set. For `current_portfolio` or `model_portfolio`, provide subject weights; for
   `universe_baseline`, the system creates equal diagnostic weights.
2. Run `python run_portfolio_review.py --dry-run` to inspect the planned order.
3. Run `python run_portfolio_review.py` from the project root. On first data load, add
   `--no-cache` if you want a fresh data download.
4. Open `{output_dir_final}/analysis_subject/` first. Candidate and decision artifacts should be
   interpreted only after this subject diagnosis exists.

For a deliberate legacy policy run, use `python run_optimization.py` and inspect
`output_dir_final/run_result.json` as described above.

## 7. Recurring Portfolio-First Run

1. Refresh data when needed by running with `--no-cache`.
2. Run `run_portfolio_review.py` on the chosen schedule, for example the first business day of each month.
3. Compare the new subject diagnosis and candidate decision artifacts with the prior run. If the
   subject changed, review the assumptions and candidate deltas before acting.
4. For legacy policy rebalancing, run the policy flow intentionally, then use
   `run_rebalance.py --current current_positions.yml --target <path_to_portfolio_weights.yml>`.
   Use `--threshold` and `--min-trade` when needed. Consider turnover before deciding to rebalance.

## 8. Candidate Portfolio Factory operator playbook

Use this section when interpreting `candidate_factory_run.json`, `candidate_factory_run.txt`, or the
factory CLI exit code. Canonical field definitions: [candidate_factory_spec.md](specs/candidate_factory_spec.md).
Layer handoff: [candidate_factory_layer_spec.md](specs/candidate_factory_layer_spec.md).

### 8.1 Standalone factory CLI

```bash
python run_candidate_factory.py
python run_candidate_factory.py --profile default_v1 --resume
python run_candidate_factory.py --profile core_v1 --then-compare
python run_candidate_factory.py --candidates equal_weight,risk_parity --force
python run_candidate_factory.py --profile default_v1 --fail-fast
```

| Flag | When to use |
| --- | --- |
| `--profile core_v1` | Six benchmark/risk-budget builders (routine). |
| `--profile default_v1` | Full 16-builder menu (optimizers + robust). |
| `--candidates ID,...` | Subset or custom order; sets profile to `explicit_list`. |
| `--skip-existing` (default) | Reuse fresh `snapshot_10y.json` per candidate. |
| `--no-skip-existing` / `--force` | Rebuild after config/universe change or bad artifacts. |
| `--resume` | Continue after interrupt; reads `candidate_factory_manifest.json`. |
| `--fail-fast` | Stop on first `failed` step (debugging). |
| `--then-compare` | Run comparison/decision package after factory. |

Portfolio-first review wraps the same factory via `run_portfolio_review.py` (core vs full profile).
Use `run_portfolio_review.py --mode full --resume-candidates` to pass factory `--resume` through
the portfolio-first path after an interrupted full review.

### 8.2 Process exit codes (`run_candidate_factory.py`)

| Code | Meaning | Operator action |
| --- | --- | --- |
| **0** | No `failed` steps (skips and `skipped_dependency` are OK). | Run comparison if not already done (`--then-compare` or `run_compare_variants.py`). |
| **1** | One or more steps `failed`, or `--fail-fast` stopped the run. | Open `candidate_factory_run.txt` → failed `reason_code` rows; follow playbooks in §8.5; rerun with `--resume` after fix. |
| **2** | Config/registry validation before any builder (bad profile, unknown id, missing `config.yml`). | Fix `config.yml` or CLI args; no manifest update for failed builders. |

`candidate_factory_run.txt` repeats the factory-only exit hint (`0` or `1`). Comparison failures with
`--then-compare` add a `comparison_failed:` warning but do not change the factory exit code when
builders succeeded.

### 8.3 Step statuses (per `steps[]`)

| `status` | Meaning |
| --- | --- |
| `succeeded` | Builder finished; `snapshot_10y.json` present and matches review `analysis_end` + `config_fingerprint`. |
| `failed` | Builder or post-build validation failed; see `reason_code`. |
| `skipped_existing` | Fresh snapshot reused (`--skip-existing`). |
| `skipped_dependency` | Prerequisite missing (e.g. Main stress files for `robust_scenario`). |
| `skipped_profile` | Reserved; not used in V1 profiles. |

### 8.4 Reason codes (`reason_code`)

| Code | Typical cause | Recovery |
| --- | --- | --- |
| `skipped_existing` | Fresh snapshot on disk | None — intentional skip. |
| `skipped_dependency` | Main `stress_report.json` / `scenario_library_normalized.json` or λ file missing | §8.5 playbook **Robust / dependency skip**; factory continues unless `--fail-fast`. |
| `subprocess_failed` | Builder exited non-zero; no `FAIL_*` in `summary.json` | Inspect builder logs; open `{artifact_root}/summary.json` if present; fix data/config; `--resume`. |
| `missing_snapshot_after_build` | Exit 0 but no `snapshot_10y.json` | Inspect builder output folder; rerun builder or `--force` for that id. |
| `stale_snapshot_after_build` | Snapshot `analysis_end` still wrong after build | Confirm `analysis_subject` refreshed; `--no-skip-existing` for that candidate. |
| `stale_config_fingerprint_after_build` | Snapshot missing/wrong `candidate_config_fingerprint` | Universe/bounds/currency changed — `--no-skip-existing` or `--force`. |
| `unknown_candidate_id` | Typo in `--candidates` | Fix id against [candidate_factory_spec.md](specs/candidate_factory_spec.md) registry table. |
| `builder_fail_config` | Builder `FAIL_CONFIG` | Fix `config.yml` / profile per builder `reason` in `summary.json`. |
| `builder_fail_data` | Builder `FAIL_DATA` | Data download/cache; young ETF / NaN policy per [data_policy_spec.md](specs/data_policy_spec.md). |
| `builder_infeasible_universe` | `FAIL_INFEASIBLE_UNIVERSE` | Universe too small or illiquid for that optimizer family. |
| `builder_infeasible_targets` | `FAIL_INFEASIBLE_TARGETS` | Soft targets infeasible — review policy targets (diagnostic). |
| `builder_infeasible_bounds` | `FAIL_INFEASIBLE_BOUNDS` | Weight bounds conflict — review min/max per asset. |
| `builder_infeasible_vol_target` | `FAIL_INFEASIBLE_VOL_TARGET` | Vol target not achievable. |
| `builder_fail_numerical` | `FAIL_NUMERICAL` | Solver/numerical issue — retry; check cov/returns panel. |
| `builder_fail_no_assets` | `FAIL_NO_ASSETS` | No eligible assets after filters. |
| `builder_failed` | Other builder `FAIL_*` | Read `builder_status` / `builder_reason` on the step. |

When `builder_status` is present on a failed step, treat builder `summary.json` as the detailed
diagnostic; factory `reason_code` is the stable machine label for comparison and run summaries.

### 8.5 Scenario playbooks

**Interrupted full menu (G4 / RM-979)**

1. Confirm `analysis_subject` exists and `analysis_end` is current.
2. Prefer `python run_portfolio_review.py --mode full --resume-candidates` to rematerialize the subject and pass factory `--resume` through the orchestrator.
3. For factory-only recovery, run `python run_candidate_factory.py --profile default_v1 --resume` with the same profile and menu as the interrupted run.
4. If warning `resume_manifest_stale:run_checksum_mismatch_full_execution`, config or menu changed — use `--no-skip-existing` without `--resume` or delete `candidate_factory_manifest.json` and rerun.

**Config or universe change (G2)**

1. After editing `config.yml` tickers, bounds, or `investor_currency`, do **not** trust old candidate folders.
2. `python run_portfolio_review.py --no-skip-existing` or `run_candidate_factory.py --profile <profile> --no-skip-existing`.
3. In comparison, rows with `unavailable_reason` containing `stale_config_fingerprint` need rebuild.

**Builder infeasible / data failure (G1)**

1. Open `{artifact_root}/summary.json` and step `builder_reason`.
2. Adjust inputs only when mandate/data policy allows; factory does not change optimizer formulas.
3. `python run_candidate_factory.py --profile <profile> --resume` after fix.

**Robust / dependency skip (G8, G10)**

1. `robust_mv_*`: run `python run_robust_mv_lambda_calibration.py` or confirm `analysis_robust_mv_lambda_calibration/selected_lambda.txt`.
2. `robust_scenario`: refresh Main `stress_report.json` and `scenario_library_normalized.json` (`run_report.py` on Main).
3. Rerun factory with `--resume` or targeted `--candidates robust_scenario`.

**Partial menu / core vs full (G4, RM-920)**

1. Read `candidate_comparison.json` → `candidate_menu` (`is_partial_menu`, `intended_candidate_ids`, `available_candidate_ids`).
2. Do not treat rankings as covering `default_v1` when only `core_v1` ran.
3. For full menu: `python run_portfolio_review.py --mode full`.

**Comparison not updated**

1. Factory exit 0 but no `candidate_comparison.json` — run `python run_compare_variants.py` or factory `--then-compare`.
2. Warning `comparison_failed:` — read nested message; fix comparison inputs; rerun compare only.

### 8.6 Artifacts to open first

| Question | Open |
| --- | --- |
| Which step failed and why? | `candidate_factory_run.txt` (summary + reason codes) or `steps[]` in JSON |
| Resume state? | `candidate_factory_manifest.json` (`completed_steps`, `run_checksum`) |
| Fair comparison ready? | `candidate_comparison.json` row `availability` / `unavailable_reason` |
| Construction hypothesis? | Row `construction_disclosure` (not recomputed in factory) |
| Robust λ / Main deps? | Step `robust_paths_disclosure` or §0 robust suite table |

`next_recommended_command` in the factory run JSON is contextual: failed runs suggest `--resume`;
stale manifest suggests full rebuild; success suggests `run_compare_variants.py`.
