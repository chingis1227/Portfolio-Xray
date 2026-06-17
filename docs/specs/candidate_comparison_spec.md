# Candidate Comparison Specification

This document owns the canonical **Candidate Comparison** artifact contract. It defines how multiple portfolio candidates are assembled into one machine-readable comparison table for diagnostics, scorecards, selection, monitoring, and report surfaces.

It does not own metric formulas, stress scenarios, candidate construction methods, or optimizer policy. Those remain in [metrics_specification.md](metrics_specification.md), [stress_testing_spec.md](stress_testing_spec.md), [candidate_portfolios_spec.md](candidate_portfolios_spec.md), and [portfolio_construction_policy.md](portfolio_construction_policy.md).

## Scope

The Candidate Comparison layer:

- reads **existing** per-candidate report artifacts (snapshots, stress reports, run metadata);
- normalizes them into one JSON contract;
- marks candidates `available`, `unavailable`, or `degraded`;
- stays **diagnostic-only** (no selection, no-trade, ranking, or trade instructions).

For the vertical web path, `current_vs_candidate.json` may add a bounded degraded fallback when the
selected same-run `candidate_generation.json` contains generated weights but the candidate row lacks
full snapshot metrics. In that case `src/current_vs_candidate.py` can compute weight-only
concentration and turnover evidence from the generated weights, mark the row as degraded, and keep
return, volatility, stress, factor, and risk-contribution dimensions unavailable. This fallback does
not change `candidate_comparison.json` availability rules and must not be presented as full
performance or stress evidence.

Implementation: `src/candidate_comparison.py` (builder) and `run_compare_variants.py` (CLI). Legacy `portfolio_comparison.json` / `ew_rp_comparison.json` remain for backward compatibility.

Upstream orchestration (optional): [candidate_factory_spec.md](candidate_factory_spec.md) defines how existing per-candidate `run_*.py` scripts are run before comparison so the registry is populated deliberately rather than by ad hoc manual runs.

Portfolio-first workflow note: when `{output_dir_final}/analysis_subject/` has been materialized,
the comparison includes candidate id `analysis_subject` as the baseline row. Downstream Selection,
No-Trade, Action, Monitoring, and Journal artifacts use that row before falling back to legacy
`current`. In that portfolio-first context, any root `policy` artifacts are compatibility evidence
only and are not default candidate evidence; the `policy` row remains in the registry but is emitted
as `unavailable` with `unavailable_reason:
legacy_policy_not_default_portfolio_first_candidate`.

### Factory run vs comparison scope (operator note)

`candidate_factory_run.json` and `candidate_comparison.json` answer **different questions** and must
not be read as the same scope:

| Artifact | Question it answers | Typical pitfall |
| --- | --- | --- |
| `candidate_factory_run.json` | What did the **last factory orchestration** attempt (profile, steps, reuse)... | Assuming six `core_v1` steps mean comparison contains only six scored families |
| `candidate_comparison.json` | What candidate evidence exists **on disk** for this `analysis_end` / bundle context... | Treating 16+ rows as proof the last run was `--mode full` when optimizers were reused from disk |

The comparison builder scans the product registry and existing variant folders; it does **not** limit
rows to the last factory `steps[]` unless freshness/unavailability rules mark them unavailable.
`candidate_menu` (and, when present, `factory_evidence_status` / `factory_steps_used`) carries the
intended menu versus scored evidence. Glossary:
[GLOSSARY.md](../../GLOSSARY.md) (**Candidate factory run evidence**, **Candidate comparison
evidence**). Confusion audit:
[2026-05-23 core/full artifact audit](../audits/2026-05-23_core_full_artifact_documentation_confusion_audit.md)
§4.2, §8. Portfolio-first workflow:
[portfolio_review_workflow_spec.md](portfolio_review_workflow_spec.md).

## Product Boundary

- Comparison output is **evidence for decision support**, not a recommendation.
- Wording in downstream reports must not imply "choose this portfolio" unless [selection_engine_spec.md](selection_engine_spec.md) decision artifacts and reporting rules explicitly allow decision-support phrasing for that surface.
- Portfolio Diagnosis, commentary, and stress diagnostics remain non-binding inputs; comparison does not override them.

## Canonical Artifact

| Field | Value |
| --- | --- |
| File name | `candidate_comparison.json` |
| Location | `{output_dir_final}/candidate_comparison.json` (default folder: `Main portfolio/`) |
| Companion (optional) | `{output_dir_final}/candidate_comparison.txt` - human-readable summary table |
| Schema version | `candidate_comparison_v1` |

`output_dir_final` is the configured main output folder from `config.yml` (see [input_assumptions_spec.md](input_assumptions_spec.md)).

Do not place the canonical file under a separate project-root `comparison/` folder in V1.

## V1 User Decisions (2026-05-17)

Recorded for the canonical comparison contract (development Session 08, 2026-05-17):

1. **Candidate set:** full registry of supported families; each row may be `unavailable` when its artifact folder or required files are missing.
2. **Current portfolio:** include candidate `current` (role `user_current`) when the user runs or has materialized a current-portfolio report (`analyze_current_weights` or equivalent artifacts tagged `user_current_portfolio`, or sidecar under `{output_dir_final}/current_portfolio/` per [current_vs_policy_workflow_spec.md](current_vs_policy_workflow_spec.md)).
3. **Location:** single canonical JSON under `output_dir_final` (Main).

## Top-Level JSON Contract

```json
{
  "schema_version": "candidate_comparison_v1",
  "diagnostic_only": true,
  "comparison_baseline_candidate_id": "analysis_subject",
  "generated_at": "ISO-8601 timestamp",
  "analysis_end": "YYYY-MM-DD",
  "investor_currency": "USD",
  "output_dir_final": "Main portfolio",
  "analysis_setup_summary": { },
  "windows": ["3y", "5y", "10y"],
  "primary_window": "10y",
  "candidates": [ ],
  "legacy_artifacts": {
    "portfolio_comparison_json": "portfolio_comparison.json",
    "ew_rp_comparison_json": "ew_rp_comparison.json"
  },
  "warnings": [ ],
  "candidate_menu": { }
}
```

### `candidate_menu` block (Session 09; factory evidence addendum RM-1012)

When present, describes the **intended** factory menu versus the **full-menu research baseline**
(`default_v1` via `full_menu_baseline_profile_id` / legacy `product_menu_profile_id`), scored counts,
partial-menu flags, unavailable-reason summary, and refresh commands. This baseline is **not** the
Core MVP product default (explicit `--candidates <id>` / selected-candidate-first). Downstream
decision-package reporting must surface `is_partial_menu` when true so selection ranks are not read
as covering the full sixteen-candidate research menu.

Beginning with Blocks 1-5 reliability Session 03 (`RM-1012`), this block also reports whether
`candidate_factory_run.json` is current evidence for the comparison. `factory_evidence_status` is
`current`, `missing`, `stale`, or `not_authoritative`; `factory_steps_used` is true only when the
factory summary matches the current comparison context closely enough for `steps[]` to annotate
candidate rows. `factory_evidence_warnings` carries machine-readable reasons such as
`factory_summary_missing`, `factory_summary_stale_analysis_end:...`,
`factory_summary_stale_config_fingerprint:...`, and
`factory_summary_stale_vs_existing_comparison:...`, and
`factory_summary_timing_skew_accepted:delta_seconds=N` when analysis context matches and the
factory summary trails the on-disk comparison timestamp by at most
`FACTORY_COMPARISON_TIMING_SKEW_SECONDS` (120s, standalone rebuild only).

`run_candidate_factory.py --then-compare` writes `candidate_factory_run.json` before comparison,
passes the in-memory factory document into the comparison builder, and sets rebuild source
`factory_then_compare` so clock ordering within the same orchestrated leg does not mark evidence
stale when `analysis_end` and `config_fingerprint` still match.

### `review_bundle_context` block (Phase 17 Session 07 / RM-1026)

Required on newly built `candidate_comparison.json` documents. Correlates subject sidecar,
factory summary, and comparison under one `review_bundle_fingerprint` and surfaces
`analysis_mode` vs `analysis_subject.type` interpretation (legacy `optimize_from_universe`
with explicit `current_portfolio` subject is informational, not a blocking error).

| Field | Description |
| --- | --- |
| `version` | Always `review_bundle_context_v1`. |
| `review_bundle_fingerprint` | SHA-256 of canonical bundle parts (`analysis_end`, comparison/subject/factory fingerprints, subject id/type, `review_mode`). |
| `bundle_parts` | `analysis_subject`, `factory_run`, `comparison` artifact summaries (paths, timestamps, fingerprints). |
| `fingerprint_alignment` | `subject_vs_comparison_config`, `factory_vs_comparison_config`, `all_aligned`, `mismatch_reasons[]`. |
| `mode_subject_consistency` | `source_analysis_mode`, `analysis_subject_type`, `is_consistent`, `mismatch_codes[]`, `informational_notices[]`, `interpretation_en`. |
| `user_summary_lines[]` | Plain-English lines for commentary and `input_assumptions` trust handoff. |

Run-level `warnings` may include `review_bundle_alignment:*` or `review_bundle_mode_subject:*`
when alignment or mode/subject checks fail.

### `hedge_gap_comparison` block (Block 3.3 Session 08)

Optional top-level block on `candidate_comparison.json`. Emitted when the comparison baseline and at
least one peer candidate folder both expose `hedge_gap_analysis_v1` on `stress_report.json` (or a
snapshot mirror with `version = hedge_gap_analysis_v1`).

| Field | Description |
| --- | --- |
| `version` | `hedge_gap_comparison_v1` |
| `status` | `ok` when baseline + ≥1 peer have v1; `unavailable` with `reason_code` otherwise |
| `baseline_candidate_id` | Usually `analysis_subject` |
| `hedge_gap_source` | Always `hedge_gap_analysis_v1` when present |
| `comparison_candidate_ids` | Peer ids with v1 rows (sorted) |
| `candidates` | Map of candidate id → compact v1 summary (protection profile, main gap, weak-row count) |
| `pairwise[]` | Per-peer deltas vs baseline (`offset_coverage_ratio_delta`, `main_gap_score_delta`, English `comparison_summary_en`) |

Legacy `stress.hedge_gap_analysis` on candidate rows remains for backward compatibility; new
integrations must read `hedge_gap_comparison` and/or `stress.hedge_gap_analysis_v1`.

### `stress_scorecard_comparison` block (Block 3.4 Session 09)

Optional top-level block on `candidate_comparison.json`. Emitted when the comparison baseline and at
least one peer candidate folder both expose `current_portfolio_stress_scorecard_v1` on
`stress_report.json` (or a snapshot mirror with `version = current_portfolio_stress_scorecard_v1`).

| Field | Description |
| --- | --- |
| `version` | `stress_scorecard_comparison_v1` |
| `status` | `ok` when baseline + ≥1 peer have Block 3.4; `unavailable` with `reason_code` otherwise |
| `baseline_candidate_id` | Usually `analysis_subject` |
| `stress_scorecard_source` | Always `current_portfolio_stress_scorecard_v1` when present |
| `comparison_candidate_ids` | Peer ids with v1 rows (sorted) |
| `candidates` | Map of candidate id → compact Block 3.4 summary (worst synthetic/historical ids, stress severity, diagnosis confidence, offset targets) |
| `pairwise[]` | Per-peer deltas vs baseline (`worst_synthetic_loss_pct_delta`, optional `offset_coverage_ratio_delta` when `compare_offset_coverage`, English `comparison_summary_en`) |

Legacy `stress.scorecard` on candidate rows remains for backward compatibility; new integrations
must read `stress_scorecard_comparison` and/or `stress.current_portfolio_stress_scorecard_v1`.

### Required top-level fields

| Field | Type | Description |
| --- | --- | --- |
| `schema_version` | string | Always `candidate_comparison_v1` for this contract. |
| `diagnostic_only` | bool | Always `true` in V1. |
| `comparison_baseline_candidate_id` | string | Preferred baseline id for portfolio-first interpretation; `analysis_subject` when the sidecar exists. |
| `generated_at` | string | UTC or local ISO timestamp when the file was written. |
| `analysis_end` | string | Effective month-end used for windows (from config or dominant snapshot). |
| `investor_currency` | string | Investor currency code. |
| `output_dir_final` | string | Relative or absolute path to main output folder. |
| `analysis_setup_summary` | object | Projected summary from `analysis_setup` / `input_assumptions` (mode, roles, weight sources). In portfolio-first runs, prefer `{output_dir_final}/analysis_subject/run_metadata.json`; use root metadata only as fallback. |
| `windows` | array | Window labels present in the comparison (`3y`, `5y`, `10y`). |
| `primary_window` | string | Default window for summary tables (V1: `10y`). |
| `candidates` | array | One object per registered candidate (see below). |
| `legacy_artifacts` | object | Paths to pre-canonical comparison files, if present. |
| `warnings` | array | Run-level warnings (stale artifacts, mixed analysis dates, partial coverage, partial menu). |
| `candidate_menu` | object | Intended vs product menu disclosure (counts, `is_partial_menu`, refresh commands) plus factory-evidence freshness. Optional until comparison is rebuilt; required for new portfolio-first runs after Session 09. |
| `review_bundle_context` | object | Review bundle fingerprint and mode/subject disclosure (`review_bundle_context_v1`). Required on new comparison builds after Phase 17 Session 07. |
| `hedge_gap_comparison` | object | Block 3.3 hedge-gap peer comparison (`hedge_gap_comparison_v1`) when baseline and ≥1 peer have v1 stress blocks. |
| `stress_scorecard_comparison` | object | Block 3.4 stress scorecard peer comparison (`stress_scorecard_comparison_v1`) when baseline and ≥1 peer have Block 3.4 on stress reports. |

## Candidate Object Contract

Each element of `candidates[]`:

```json
{
  "candidate_id": "equal_weight",
  "display_name": "Equal-Weight Portfolio",
  "role": "benchmark",
  "construction_method": "equal_weight_by_asset",
  "weight_source": "candidate_script.fixed_weights",
  "artifact_root": "equal-weight portfolio",
  "status": "available",
  "unavailable_reason": null,
  "portfolio_role": null,
  "recommendation_status": null,
  "metrics": { },
  "stress": { },
  "drawdown": { },
  "factor_regime": { },
  "mandate": { },
  "missing_fields": [ ],
  "warnings": [ ],
  "source_files": [ ],
  "construction_disclosure": { }
}
```

### Identity and metadata

| Field | Required | Description |
| --- | --- | --- |
| `candidate_id` | yes | Stable machine id (snake_case, see registry). |
| `display_name` | yes | English label for reports. |
| `role` | yes | `analysis_subject` \| `policy` \| `user_current` \| `benchmark` \| `optimizer_candidate` \| `robust_candidate`. |
| `construction_method` | yes | Short id matching candidate family (e.g. `risk_parity`, `minimum_cvar_constrained`). |
| `weight_source` | yes | How weights were fixed (e.g. `optimization_result_released`, `config.current_weights`, `candidate_script.fixed_weights`). |
| `artifact_root` | yes | Project-relative folder containing that candidate's report outputs, or `output_dir_final` for policy/current on Main. |
| `status` | yes | `available` \| `unavailable` \| `degraded`. |
| `unavailable_reason` | if unavailable | Machine code, e.g. `missing_artifact_folder`, `missing_snapshot`, `not_applicable_for_analysis_mode`. |
| `portfolio_role` | when known | From `analysis_setup.analysis_portfolio.portfolio_role` when this row is the analyzed Main report. |
| `recommendation_status` | when known | From run metadata; must not be interpreted as advice. |
| `construction_disclosure` | yes | Passthrough of how weights were built (see below). Always present; use `disclosure_status` to interpret completeness. Optimizer rows may also include `optimizer_methodology` when upstream optimizer metadata exists. |

### `construction_disclosure` (comparison v1.3 — Block 4 Session 04, RM-974)

Diagnostic-only disclosure of construction parameters. The comparison builder **must not** recompute weights or optimizer targets; it copies existing metadata from candidate artifact folders.

| Field | Required | Description |
| --- | --- | --- |
| `disclosure_status` | yes | `available` when `baseline_weights_metadata.json` was loaded; `partial` when only `summary.json`, Main `run_result.json` / sidecar `run_metadata.json`, or factory step excerpts exist; `missing` when no construction sources were found. |
| `source_files` | yes | Relative filenames under `artifact_root` that contributed (e.g. `baseline_weights_metadata.json`, `summary.json`, `candidate_factory_run.json`). |
| `baseline_metadata` | when available | Full JSON object from `{artifact_root}/baseline_weights_metadata.json` (e.g. `equal_weight_method`, `target_risk_budgets`, `target_risk_budgets_effective`, optimizer diagnostics). |
| `builder_summary` | optional | Selected fields from `{artifact_root}/summary.json` (`status`, `reason`, `solver_status`, …) and any `*_metadata` nested blobs when the baseline file is absent. |
| `main_row_excerpt` | optional | For `policy`: excerpt from `run_result.json` (`optimization_status`, mandate gate summary). For `analysis_subject` / `current`: excerpt from `run_metadata.json` `analysis_setup`. |
| `factory_step` | optional | Excerpt from `{output_dir_final}/candidate_factory_run.json` `steps[]` for this `candidate_id` only when the factory summary is current for this comparison (`reason_code`, `builder_status`, `builder_reason`, freshness fields, `robust_paths_disclosure` when present). |
| `optimizer_methodology` | when available | Compact comparison-level optimizer disclosure copied from `baseline_weights_metadata.json.optimizer_run_metadata` for optimizer candidates or `run_result.json.optimizer_run_metadata` for legacy policy. |
| `optimizer_quality` | when available | Normalized optimizer-quality projection from `optimizer_methodology` or factory step evidence. Includes quality status/family, fallback flag/reason, solver status, and evidence source. |
| `optimization_readiness` | optimizer-backed roles | Block 5 Session 10 (`RM-1000`) checklist for `optimizer_candidate`, `robust_candidate`, and `policy` rows only. See below. |
| `robust_paths` | when robust suite | For `robust_mv_constrained`, `robust_mv_uncapped`, `robust_scenario` only (Session 07 / RM-977). Copied from factory step `robust_paths_disclosure` when available; otherwise built from project root + `output_dir_final` + optional `baseline_metadata` (no recomputation of weights or scenarios). |

**`robust_paths` kinds:**

| `kind` | Candidates | Meaning |
| --- | --- | --- |
| `robust_mv_lambda` | `robust_mv_*` | Whether `selected_lambda.txt` exists, `lambda_resolution_key` (`calibration_file` \| `none`), `robust_mv_lambda`, `lambda_ready_for_build`, `factory_runs_lambda_calibration: false`. |
| `robust_scenario_main_prerequisites` | `robust_scenario` | Whether Main `scenario_library_normalized.json` and `stress_report.json` exist; `shared_calibration_scope: main_output_dir_final`; `recommended_before_factory`. |

Emit `construction_disclosure` on **every** registry row, including `unavailable` rows, when artifact files exist (e.g. builder failed but `summary.json` documents `FAIL_*`).

### `optimizer_methodology` (Block 5 Session 05, RM-995)

`optimizer_methodology` is diagnostic-only, read-only disclosure for rows whose source artifacts
already expose normalized optimizer metadata. The comparison builder must not infer objectives,
solve weights, recompute constraints, or upgrade row status from this block.

Sources:

- optimizer candidates: `{artifact_root}/baseline_weights_metadata.json` ->
  `optimizer_run_metadata`;
- robust scenario candidate: `robust scenario portfolio/baseline_weights_metadata.json` ->
  `optimizer_run_metadata` (`robust_scenario_optimizer_run_metadata_v1`) when
  `run_robust_scenario_portfolio_report.py` copied the source robust solver summary;
- legacy policy: `{output_dir_final}/run_result.json` -> `optimizer_run_metadata`.

The block copies the comparison-ready subset needed to read a row fairly:

| Field | Description |
| --- | --- |
| `source` | Source path inside the artifact, e.g. `baseline_weights_metadata.json.optimizer_run_metadata`. |
| `source_schema_version` | Upstream metadata schema version. |
| `optimizer_role` | Upstream role such as `candidate_only` or `legacy_policy`. |
| `candidate_only` | Boolean; true for candidate-only optimizer rows and false for legacy policy. |
| `method_id` | Optimizer method id from the source metadata. |
| `objective` | Objective disclosure copied as-is from upstream metadata. |
| `input_window` | `analysis_end`, window length, and return-frequency fields when present. |
| `expected_return` | Expected-return usage/method disclosure when present. |
| `covariance` | Covariance method disclosure when present; Session 09 may include `methodology` (`optimizer_covariance_methodology_v1`) and `methodology_summary`. |
| `young_etf_methodology` | Young ETF methodology disclosure copied from upstream optimizer metadata when present. |
| `constraints` | Active constraints, bounds, and constraint summary copied from upstream metadata. |
| `solver` | Solver name/status/success plus `fallback_used`, `fallback_reason`, and `optimization_quality_status`. |
| `freshness` | Factory freshness fields (`freshness_status`, snapshot/expected `analysis_end`, config fingerprints) plus optimizer `analysis_end` when present. |

Absence of `optimizer_methodology` means no normalized optimizer metadata was found in source
artifacts. It does not mean the candidate is invalid; row validity is still governed by `status`,
`unavailable_reason`, freshness checks, and required report artifacts.

Beginning with Block 5 Session 09 (`RM-999`), the optional human-readable
`candidate_comparison.txt` appends an "Optimizer methodology notes" section when rows expose
`optimizer_methodology`. The section summarizes covariance method, join policy, shrinkage, PSD
repair, Young ETF policy/caps, and optimizer quality. It is a summary of existing metadata only; it
does not change ranking, readiness, or row status.

### `optimizer_quality` (Block 5 Session 06, RM-996)

`optimizer_quality` is the comparison-level fallback/failure boundary. It is derived only from
source metadata already present in `construction_disclosure`; the comparison builder must not rerun
or reinterpret optimizer math.

| Field | Description |
| --- | --- |
| `source` | Source path used for evidence. |
| `optimization_quality_status` | `clean_solve`, `approximate_fallback`, `approximate_solver`, `failed_solver`, `failed`, or `unknown`. |
| `optimization_quality_family` | `clean`, `approximate`, `failed`, or `unknown`. |
| `fallback_used` | Boolean fallback disclosure. |
| `fallback_reason` | Source fallback reason when present. |
| `solver_status` | Source solver status when present. |

Boundary rules:

- `approximate_fallback` and `approximate_solver` degrade an otherwise `available` optimizer row to
  `degraded` and add warning `optimizer_quality_not_clean:{status}`;
- `failed_solver` and `failed` make the row `unavailable` with
  `unavailable_reason: optimizer_quality_failed`;
- a current factory step with `status: failed` or `skipped_dependency` makes the row `unavailable`
  using the factory `reason_code`, even if an old `snapshot_10y.json` exists;
- `unknown` does not by itself make an optimizer row `unavailable`, but beginning with Blocks 1-5
  reliability Session 05 (`RM-1014`) it degrades an otherwise `available` optimizer-backed row and
  adds warning `optimizer_quality_unknown:{status}`.

### Status rules

| Status | Meaning |
| --- | --- |
| `available` | Required primary-window metrics and stress summary loaded successfully. |
| `degraded` | Partial data (e.g. metrics without stress, or only `summary.json` fallback). List gaps in `missing_fields` and `warnings`. |
| `unavailable` | Candidate is in the V1 registry but artifacts are missing or not applicable for this run. |

Beginning with Block 5 Session 06, fallback/approximate optimizer quality is also a valid reason
for `degraded`, and failed optimizer quality or failed current factory step is a valid reason for
`unavailable`.

Beginning with Blocks 1-5 reliability Session 05 (`RM-1014`), an otherwise `available`
optimizer-backed row (`optimizer_candidate`, `robust_candidate`, or `policy`) must not remain
ordinary `available` when required optimizer readiness evidence is absent or unknown. Missing
`optimizer_methodology` on `optimizer_candidate` / `robust_candidate` rows degrades the row and adds
warning `optimizer_readiness_missing:optimizer_methodology`. Missing `optimizer_quality` on any
optimizer-backed row degrades the row and adds warning
`optimizer_readiness_missing:optimizer_quality`. This does not rerun optimizers or infer missing
methodology; it only makes incomplete evidence visible.

### `optimization_readiness` (Block 5 Session 10, RM-1000)

`optimization_readiness` is diagnostic-only evidence for optimizer-backed comparison rows. The
comparison builder assembles it from existing artifacts after row status and Session 06 optimizer
quality policy are applied. It must not rerun optimizers, recompute weights, or change ranking.

Emitted only when `role` is `optimizer_candidate`, `robust_candidate`, or `policy`.

| Field | Description |
| --- | --- |
| `schema_version` | `optimizer_comparison_readiness_v1` |
| `role` | Registry role copied for auditability |
| `overall_status` | `ready`, `partial`, `not_ready`, `degraded_quality`, or `failed` |
| `comparison_row_status` | Final row `status` after comparison and optimizer-quality policy |
| `unavailable_reason` | Row unavailable reason when present |
| `fair_comparison_ready` | `true` only when the row is `available`, disclosure is `available`, required checks pass, `optimizer_methodology` is present, optimizer quality family is `clean`, and freshness checks pass |
| `required_checks` | Machine-readable checklist for weights, `snapshot_10y`, stress summary, construction disclosure, optimizer methodology, optimizer quality, and freshness |
| `optional_checks` | `portfolio_xray` when present (not a fair-comparison gate) |
| `gaps` | Required checks that failed |
| `optimization_quality_status` | Copied normalized quality status |
| `optimization_quality_family` | Copied quality family (`clean`, `approximate`, `failed`, `unknown`) |

Boundary rules:

- `fair_comparison_ready: false` for `degraded`, `unavailable`, approximate/fallback quality, stale
  artifacts, missing methodology on optimizer/robust rows, or missing required artifacts;
- `overall_status: degraded_quality` when Session 06 marks an optimizer row `degraded` because of
  approximate/fallback quality;
- `overall_status: failed` when the row is `unavailable` because of failed factory/optimizer quality;
- `overall_status: partial` and gap `optimizer_quality` when optimizer quality is present but
  normalized to `unknown`;
- benchmark, analysis-subject, and current rows omit this block.

`candidate_comparison.txt` may append an "Optimization readiness (optimizer-backed rows)" section
summarizing `overall_status`, `fair_comparison_ready`, and `gaps` per row. The section does not
change row status.

**Do not omit** registry candidates from `candidates[]` when artifacts are missing; emit them with `status: unavailable` and a clear `unavailable_reason`.

Freshness rule (RM-902): when comparison has a review `analysis_end`, a candidate
`snapshot_10y.json` with a different `analysis_end` is not current evidence. Emit the candidate as
`status: unavailable`, `unavailable_reason: stale_snapshot_analysis_end`, and include a warning of
the form `stale_snapshot_analysis_end:{snapshot_analysis_end}!={review_analysis_end}`. This prevents
Selection, No-Trade, and downstream decision artifacts from silently using stale candidate metrics.

Unchecked freshness (RM-973): when comparison cannot resolve a review `analysis_end`, candidate
metrics may still load, but each row with a primary snapshot must include warning
`candidate_freshness_unchecked_no_review_analysis_end:{candidate_id}` so operators know freshness
was not certified against the current subject run.

Config fingerprint (RM-976): when comparison has a review `analysis_end` and the candidate
`snapshot_10y.json` date matches, but `candidate_config_fingerprint` is present and differs from the
review `config_fingerprint` (top-level field, or computed from current `config.yml` when no factory
run exists), emit `status: unavailable`, `unavailable_reason: stale_config_fingerprint`, and warning
`stale_config_fingerprint:{snapshot_fp}!={expected_fp}`. When the fingerprint field is absent on an
otherwise date-fresh snapshot, emit warning `candidate_config_fingerprint_missing:{candidate_id}` and
still allow `available`/`degraded` (factory rebuilds missing fingerprints on the next run).

Factory summary coherence (RM-1012): comparison must evaluate
`{output_dir_final}/candidate_factory_run.json` before copying any per-step factory evidence into
candidate rows. The factory summary is current only when it has a valid `factory_profile_id`, a valid
`generated_at`, an `analysis_end` matching the current review when the review date is known, and a
matching `config_fingerprint` when the factory summary exposes one. If an existing
`candidate_comparison.json` on disk has a `generated_at` later than or equal to the factory summary
`generated_at`, the factory summary is treated as stale for the rebuild. Missing, stale, or
not-authoritative factory summaries remain disclosed in `candidate_menu` but their `steps[]` are not
used as current `construction_disclosure.factory_step` evidence and cannot block or upgrade a row.

## Metric, Stress, and Diagnostic Blocks

All numeric values follow [metrics_specification.md](metrics_specification.md) rounding: **three decimals at export only**. The comparison builder must not recompute canonical metrics with alternate formulas; it aggregates from existing artifacts.

### `metrics` (per window)

Keyed by `3y`, `5y`, `10y`. Each window object may include:

| Field | Source priority |
| --- | --- |
| `cagr`, `vol_annual`, `max_drawdown`, `sharpe`, `sortino`, `beta_portfolio` | `snapshot_{window}.json` → `metrics`; else `summary.json` → `metrics_{window}` |
| `correlation_benchmark` | snapshot or summary when present |

### `stress`

| Field | Source |
| --- | --- |
| `overall` | `snapshot_*`.stress_suite_results.overall or `summary.json`.stress_status |
| `fail_reason_code`, `failed_scenario` | stress suite or `stress_report.json` |
| `scenarios` | optional abbreviated list from snapshot stress suite |
| `scorecard`, `conclusions` | **Legacy** — `stress_suite_results` or `stress_report.json` (`stress_scorecard_v1`, `stress_conclusions`) when Block 3.4 is missing |
| `current_portfolio_stress_scorecard_v1` | **Core MVP** — compact Block 3.4 slice from `stress_report.json` (preferred) or snapshot mirror; includes `candidate_comparison_targets` fields |
| `stress_scorecard_source` | `current_portfolio_stress_scorecard_v1` or `stress_scorecard_v1` (legacy fallback) |
| `hedge_gap_analysis` | **Legacy** — `stress_suite_results` or `stress_report.json` (aggregate + `by_risk_type[]`) |
| `hedge_gap_analysis_v1` | **Core MVP** — compact Block 3.3 slice from `stress_report.json` (preferred) or snapshot `stress_suite_results.hedge_gap_analysis_v1` mirror |
| `historical_methodology` | `stress_suite_results` or `stress_report.json` (`historical_methodology_v1`) |
| `crisis_replay_summary` | `stress_suite_results` or compact projection of `historical_episode_paths` (no daily rows) |

### `drawdown`

| Field | Source |
| --- | --- |
| `max_drawdown` | metrics block (duplicate allowed for convenience) |
| `recovered`, `time_to_recovery_months` | snapshot metrics when present |

### `factor_regime`

Optional in V1. Populate when `stress_report.json` or snapshot embeds factor/regime summaries:

| Field | Source |
| --- | --- |
| `factor_regression_5y`, `factor_regression_10y` | `stress_report.json` (betas + HAC inference blocks per stress spec) |
| `macro_regime` | macro/regime artifacts when present in candidate folder |

### `mandate`

| Field | Source |
| --- | --- |
| `portfolio_valid`, `client_fit` | `run_metadata.json`, `summary.json`, or snapshot constraints |
| `constraints_status` | snapshot.constraints_status when present |

### `diversification` (comparison v1.1 — Session 11)

Required for [Robustness Scorecard](robustness_scorecard_spec.md) `diversification_rc` component. Populated from `snapshot_10y.json` `RC_asset` when present (Session 11).

| Field | Source |
| --- | --- |
| `top1_rc_asset`, `top1_rc_pct` | `snapshot_10y.json` -> `RC_asset[0]` (ticker, `rc_pct`) |
| `top3_rc_assets`, `top3_rc_sum_pct` | sum of top three `RC_asset` rows by `rc_pct` |
| `rc_hhi` | optional Herfindahl of `RC_asset` shares when implemented |
| `source_window` | `10y` |

When snapshot has no `RC_asset`, leave block empty and list `diversification` in `missing_fields`.

### `weight_concentration` (comparison v1.2 — Session 13)

Required for [Portfolio Health Score](portfolio_health_score_spec.md) `weight_concentration` component. Populated from `snapshot_10y.json` `final_weights_total` when present (Session 13).

| Field | Source |
| --- | --- |
| `top1_weight_asset`, `top1_weight_pct` | largest weight in `final_weights_total` |
| `top3_weight_assets`, `top3_weight_sum_pct` | top three weights by pct |
| `weight_hhi` | optional Herfindahl of weight shares when implemented |
| `source` | `snapshot_10y.final_weights_total` |

When snapshot has no weight block, leave empty and list `weight_concentration` in `missing_fields`.

### `source_files`

Relative paths from repo root or `artifact_root` for auditability, e.g. `snapshot_10y.json`, `stress_report.json`, `run_metadata.json`.

## Candidate Registry (V1 Full Set)

Project root is the repository root. `artifact_root` is relative to project root unless noted.

### Core decision rows

| candidate_id | role | construction_method | artifact_root | Notes |
| --- | --- | --- | --- | --- |
| `analysis_subject` | `analysis_subject` | `analysis_subject_diagnostics` | `{output_dir_final}/analysis_subject` | Portfolio-first baseline row from `run_report.py --materialize-analysis-subject`; preferred baseline for Selection, No-Trade, Action, Monitoring, and Journal. |
| `policy` | `policy` | `policy_optimizer` | `{output_dir_final}` | Optimizer-released weights; Main report after `run_optimization` + `run_report`. In portfolio-first runs with an available `analysis_subject`, this row is legacy/compatibility-only and must not be treated as a default candidate. |
| `current` | `user_current` | `user_supplied_weights` | `{output_dir_final}` or `{output_dir_final}/current_portfolio` | **Combined workflow:** sidecar `current_portfolio/` when materialized ([current_vs_policy_workflow_spec.md](current_vs_policy_workflow_spec.md)). **Legacy/single-mode:** Main root when `analyze_current_weights` or `portfolio_role=user_current_portfolio`. If `current_weights` exist in optimize mode but no materialization, `unavailable`, reason `missing_current_report`. |
| `equal_weight` | `benchmark` | `equal_weight_by_asset` | `equal-weight portfolio` | |
| `risk_parity` | `benchmark` | `risk_parity` | `risk parity portfolio` | |
| `robust_scenario` | `robust_candidate` | `scenario_robust_optimization` | `robust scenario portfolio` | |

### Optimizer / baseline candidates (same registry; may be unavailable)

| candidate_id | role | construction_method | artifact_root |
| --- | --- | --- | --- |
| `robust_mv_constrained` | `optimizer_candidate` | `robust_mean_variance_constrained` | `robust mean variance constrained portfolio` |
| `robust_mv_uncapped` | `optimizer_candidate` | `robust_mean_variance_uncapped` | `robust mean variance uncapped portfolio` |
| `minimum_variance` | `optimizer_candidate` | `minimum_variance_constrained` | `minimum variance portfolio` |
| `minimum_variance_uncapped` | `optimizer_candidate` | `minimum_variance_uncapped` | `minimum variance uncapped portfolio` |
| `minimum_variance_advanced` | `optimizer_candidate` | `minimum_variance_advanced` | `minimum variance advanced portfolio` |
| `maximum_diversification` | `optimizer_candidate` | `maximum_diversification_constrained` | `maximum diversification portfolio` |
| `maximum_diversification_uncapped` | `optimizer_candidate` | `maximum_diversification_unconstrained` | `maximum diversification unconstrained portfolio` |
| `minimum_cvar_constrained` | `optimizer_candidate` | `minimum_cvar_constrained` | `minimum cvar constrained portfolio` |
| `minimum_cvar_uncapped` | `optimizer_candidate` | `minimum_cvar_uncapped` | `minimum cvar uncapped portfolio` |
| `equal_weight_by_asset_class` | `benchmark` | `equal_weight_by_asset_class` | `equal-weight by asset-class portfolio` |
| `risk_budget_by_asset_class` | `benchmark` | `risk_budget_by_asset_class` | `risk budget by asset-class portfolio` |
| `risk_budget_by_asset` | `benchmark` | `risk_budget_by_asset` | `risk budget by asset portfolio` |
| `hierarchical_risk_parity` | `benchmark` | `hierarchical_risk_parity` | `hierarchical risk parity portfolio` |

Construction methods and script entry points are defined in [candidate_portfolios_spec.md](candidate_portfolios_spec.md).

### Policy vs current on the same folder

`policy` uses `{output_dir_final}` (Main). `current` uses Main in `analyze_current_weights` mode, or **`{output_dir_final}/current_portfolio/`** sidecar when the user follows the combined current-vs-policy workflow in [current_vs_policy_workflow_spec.md](current_vs_policy_workflow_spec.md).

They are **not** both `available` from a single `analysis_mode` on Main alone:

- `optimize_from_universe`: expect `policy` available when optimization/report artifacts exist; `current` is `unavailable` with `missing_current_report` when `current_weights` is set but sidecar/Main current materialization is missing; otherwise `not_applicable_for_analysis_mode`.
- `analyze_current_weights`: expect `current` available from Main report; `policy` is `unavailable` with reason `not_applicable_for_analysis_mode` unless a prior optimization snapshot still exists (then `degraded` with warning `stale_policy_snapshot`). This mode does not provide primary current-vs-policy No-Trade versus policy.

## Assembly Rules

The comparison builder must:

1. Load config and resolve `output_dir_final`.
2. Iterate the V1 registry in stable order: `analysis_subject`, `policy`, `current`, then remaining ids alphabetically by `candidate_id` (or fixed table order above).
3. For each row, resolve `artifact_root`; if the folder or minimum files are missing, emit `unavailable`.
4. Minimum files for `available`: `snapshot_10y.json` **or** (`summary.json` with `metrics_10y`).
5. Prefer snapshot over summary for all blocks.
6. Copy `analysis_setup_summary` from `{output_dir_final}/analysis_subject/run_metadata.json` when present; otherwise fall back to Main `run_metadata.json`, Main `run_result.json`, then config.
7. Resolve comparison `analysis_end` from `{output_dir_final}/analysis_subject/` snapshots or metadata first, then Main snapshots or metadata, then config. Use that date to enforce candidate snapshot freshness.
8. When `analysis_subject` is available, gate the `policy` row as portfolio-first legacy evidence with `legacy_policy_not_default_portfolio_first_candidate`; this prevents Health Score and Selection from ranking stale root policy artifacts as normal alternatives.
9. Write `candidate_comparison.json` to `output_dir_final`. When `candidate_factory_run.json` uses `factory_profile_id: explicit_list`, write the **product-scoped** document (via `scoped_product_comparison`) to `candidate_comparison.json` and emit the full on-disk scan as optional `candidate_comparison_registry.json` (DEC-2026-05-29-006). Batch/research paths write the full registry to `candidate_comparison.json` unchanged.
10. Optionally refresh legacy `portfolio_comparison.json` for backward compatibility (subset: policy, equal_weight, risk_parity, robust_scenario).

The builder must **not** call the optimizer or candidate scripts; it only reads artifacts.

## Downstream Decision-Package Wiring

`write_candidate_comparison_outputs` is the V1 orchestration point for the generated decision package.
After journal export it also writes the compact report summary via
[decision_package_reporting_spec.md](decision_package_reporting_spec.md).
After writing `candidate_comparison.json`, it writes the existing downstream artifacts in this order:
`robustness_scorecard.json`, `portfolio_health_score.json`, `selection_decision.json`,
`action_plan.json`, `monitoring_diff.json`, and `decision_journal.json` when their required inputs are
available.

This wiring does not change the comparison artifact boundary. `candidate_comparison.json` remains
`diagnostic_only: true`; the formal decision status lives only in `selection_decision.json`, the
implementation-plan surface lives only in `action_plan.json`, temporal change evidence lives in
`monitoring_diff.json`, and the run-level process record lives in `decision_journal.json`.

### Block 8-only vertical product boundary

`write_block8_current_vs_candidate_only_outputs` is the narrow product-loop path for comparison
without verdict. It builds the comparison, writes `candidate_comparison.json` scoped to the selected
candidate, then writes `current_vs_candidate.json`. It must not write or refresh
`decision_verdict.json`, `action_plan.json`, `decision_journal.json`, or
`ai_commentary_context.json`. Existing downstream files are treated as stale downstream artifacts and
are disclosed in `current_vs_candidate.json` instead of being loaded as current evidence.

Frontend/FastAPI consumers must require displayable selected-candidate evidence before unlocking
Verdict. A summary-only response, missing `current_vs_candidate.comparisons[]`, an unavailable row,
or rows without displayable dimensions must remain blocked/partial and must not be converted into
synthetic metric rows.

## Legacy Artifacts

| File | Producer | V1 status |
| --- | --- | --- |
| `portfolio_comparison.json` | `run_compare_variants.py` | Legacy subset; keep until reports migrate to canonical file. |
| `ew_rp_comparison.json` | `run_compare_ew_rp.py` | Legacy EW vs RP deep comparison; optional cross-link in `legacy_artifacts`. |

Canonical consumers (Robustness Scorecard, Health Score, Selection Engine) must read `candidate_comparison.json`, not legacy files.

## Human-Readable Summary

`candidate_comparison.txt` is optional. When written, it should list `display_name`, primary-window CAGR, vol, max drawdown, Sharpe, stress overall, and mandate/client-fit in a fixed-width table. English only.

## Tests

Focused tests: `tests/test_candidate_comparison.py`. Golden contract (Phase 14 Session 08 /
`RM-978`): `tests/test_candidate_comparison_contract.py` and
`tests/fixtures/candidate_comparison_golden_v1.json` (regenerate:
`python tests/candidate_factory_golden_inputs.py`). Governance bundle:
[TESTING.md](../../TESTING.md) § Candidate Factory Governance Wave Bundle.

Coverage should include:

- schema version and required top-level keys;
- full registry length and stable ordering;
- `unavailable` when folder missing;
- `current` available vs unavailable by analysis mode;
- `degraded` when only `summary.json` exists;
- `construction_disclosure` on every row;
- no duplicate formulas (mock snapshots, assert passthrough values).

## Detailed Ownership

| Area | Spec |
| --- | --- |
| Candidate construction | [candidate_portfolios_spec.md](candidate_portfolios_spec.md) |
| Input modes and current weights | [input_assumptions_spec.md](input_assumptions_spec.md) |
| Current-vs-policy workflow | [current_vs_policy_workflow_spec.md](current_vs_policy_workflow_spec.md) |
| Report artifacts per portfolio | [reporting_outputs_spec.md](reporting_outputs_spec.md) |
| Output locations | [OUTPUTS.md](../../OUTPUTS.md) |
| Robustness Scorecard | [robustness_scorecard_spec.md](robustness_scorecard_spec.md) |
| Portfolio Health Score | [portfolio_health_score_spec.md](portfolio_health_score_spec.md) |
| Selection / No-Trade | [selection_engine_spec.md](selection_engine_spec.md) |
| Current-vs-policy workflow | [current_vs_policy_workflow_spec.md](current_vs_policy_workflow_spec.md) |
| Action Engine / Rebalancing Advisor | [action_engine_spec.md](action_engine_spec.md) |
| Monitoring / What Changed | [monitoring_spec.md](monitoring_spec.md) |
| Decision Journal | [decision_journal_spec.md](decision_journal_spec.md) |
