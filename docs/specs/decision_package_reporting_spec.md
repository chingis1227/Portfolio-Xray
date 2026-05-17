# Decision Package Reporting Specification

This document owns the **reporting integration layer** for the V1 file-first decision package. It defines how existing JSON/TXT decision artifacts are projected into compact English summaries for humans, CLI messaging, `report.txt`, and PDF-facing Markdown.

It does not own metric formulas, score component math, selection rules, action trade logic, or monitoring snapshot construction. Those remain in the owning specs listed under [Related specifications](#related-specifications).

Implementation: [src/decision_package_reporting.py](../../src/decision_package_reporting.py).

## Scope

The reporting layer:

- reads generated artifacts under `{output_dir_final}` after `write_candidate_comparison_outputs` completes;
- emits **`decision_package_summary.txt`** and optional **`decision_package_summary.json`** (`decision_package_report_v1`);
- may append a **Decision package** section to an existing `{output_dir_final}/report.txt` when that file is already present;
- supplies PDF Markdown builders consumed by [pdf_reports.py](../../src/pdf_reports.py) when summary files exist;
- uses **neutral decision-support English** (no imperative buy/sell, no performance guarantees);
- does **not** recompute scores, rankings, selection outcomes, or trade lists.

## V1 defaults (2026-05-17)

Recorded when the user continues the plan without overrides:

1. **Owning spec:** this file plus cross-links in [reporting_outputs_spec.md](reporting_outputs_spec.md).
2. **Primary human surface:** `decision_package_summary.txt` under `output_dir_final`.
3. **Missing upstream artifact:** emit an explicit `Not available` subsection with the reason; do not invent values.
4. **Integration point:** called at the end of `write_candidate_comparison_outputs` in [candidate_comparison.py](../../src/candidate_comparison.py).
5. **PDF (V1):** optional `Main portfolio__decision_package.md` / PDF when summary exists and PDF rebuild runs.

## Canonical outputs

| File | Schema / format | Required |
| --- | --- | --- |
| `decision_package_summary.txt` | UTF-8 English plain text | Yes |
| `decision_package_summary.json` | `decision_package_report_v1` | Yes (machine index + section statuses) |

Location: `{output_dir_final}/` (default `Main portfolio/`).

## Inputs (read-only)

| Input file | Minimum fields used |
| --- | --- |
| `candidate_comparison.json` | `analysis_end`, `candidates[]` with `candidate_id`, `display_name`, `status`, `role`, `metrics.10y`, `mandate`, `stress.overall` |
| `robustness_scorecard.json` | `candidates[]` with `candidate_id`, `total_score`, `robustness_rank`, `score_status` |
| `portfolio_health_score.json` | `candidates[]` with `candidate_id`, `total_score`, `health_rank`, `score_status` |
| `selection_decision.json` | `decision_status`, `favored_candidate_id`, `favored_display_name`, `rationale.summary`, `no_trade`, `warnings` |
| `action_plan.json` | `action_status`, `no_trades_reason`, `turnover_half_sum_pct`, `trades[]` (top rows only in summary) |
| `monitoring_diff.json` | `diff_status`, `summary_plain_en`, `prior_analysis_end`, `current_analysis_end` |
| `decision_journal.json` | `analysis_end`, `artifact_index` or `artifact_links` when present |

If a file is missing, the corresponding summary section uses `availability: not_available` in JSON and a plain-English skip line in TXT.

## Summary section order (TXT)

Fixed order for V1:

1. **Header** — analysis end, investor currency, non-executing disclaimer.
2. **Comparison highlights** — policy and current rows when present; top three scored non-current candidates by health rank when scores exist.
3. **Robustness** — favored candidate robustness total and rank when scored.
4. **Health** — favored candidate health total and rank when scored.
5. **Selection** — decision status line and favored profile; No-Trade summary when evaluated.
6. **Action** — action status, turnover, top priority trades (max 5) or no-trades reason.
7. **Monitoring** — diff status and `summary_plain_en`; explicit message when no prior snapshot.
8. **Journal** — pointer to `decision_journal.json` and latest/history copies.
9. **Artifact index** — relative filenames for all V1 decision JSON files.

## Client-safe wording

- Use display names, not internal enum codes, in TXT and PDF surfaces.
- Map `decision_status` to short English lines (see [selection_engine_spec.md](selection_engine_spec.md)).
- Prefix trade rows with "For review:" — not execution instructions.
- Portfolio X-Ray and commentary remain separate diagnostic surfaces; this summary does not replace them.

## `report.txt` integration

When `write_decision_package_reporting_outputs` runs:

- If `{output_dir_final}/report.txt` exists and does not already contain the marker `## Decision package (non-executing)`, append a section built from the same plain-text body as `decision_package_summary.txt` (truncation is not applied in V1).
- If `report.txt` does not exist, only write the standalone summary files.

## PDF integration

When [pdf_reports.py](../../src/pdf_reports.py) rebuilds Main portfolio PDFs and `decision_package_summary.txt` exists:

- build Markdown via `build_decision_package_report_md`;
- write `pdf_md_sources/Main portfolio__decision_package.md` and `pdf files/Main portfolio_decision_package.pdf` using the standard Pandoc path.

## Pipeline boundary

```text
run_compare_variants.py
  -> write_candidate_comparison_outputs
       -> comparison, scores, selection, action, monitoring, journal
       -> write_decision_package_reporting_outputs  (this spec)
```

`run_report.py` does not invoke this layer automatically in V1. Users run comparison after reports when they need the decision package summary.

## Related specifications

- [reporting_outputs_spec.md](reporting_outputs_spec.md) — main report flow and artifact map
- [candidate_comparison_spec.md](candidate_comparison_spec.md) — orchestration boundary
- [robustness_scorecard_spec.md](robustness_scorecard_spec.md)
- [portfolio_health_score_spec.md](portfolio_health_score_spec.md)
- [selection_engine_spec.md](selection_engine_spec.md)
- [action_engine_spec.md](action_engine_spec.md)
- [monitoring_spec.md](monitoring_spec.md)
- [decision_journal_spec.md](decision_journal_spec.md)

## Verification

- `tests/test_decision_package_reporting.py` — section presence, missing-input behavior, client-safe lines.
- After a comparison smoke run: `decision_package_summary.txt` and `.json` exist under `output_dir_final`.
- `python scripts/verify_docs.py` passes after doc updates.
