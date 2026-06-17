# AI Commentary Grounding Context Spec

This spec owns the deterministic grounding contract for the target Portfolio MRI
AI Commentary layer.

The implemented artifact is `ai_commentary_context.json`, written by
`src/ai_commentary_context.py` after `decision_verdict.json` is produced in the
candidate comparison / decision-package pipeline or the one-candidate vertical
product loop.

## Status

Implemented as an additive evidence bundle:

- module: `src/ai_commentary_context.py`
- artifact: `{output_dir_final}/ai_commentary_context.json`
- schema version: `ai_commentary_context_v1`
- tests: `tests/test_ai_commentary_context.py`

This is not a generated natural-language AI commentary. No LLM is called. The
artifact only defines what a later AI Commentary layer may read and how it must
ground claims.

## Product role

Target product architecture includes:

```text
Decision Verdict -> AI Commentary -> Monitoring / What Changed
```

In the current implementation, `ai_commentary_context.json` sits between the
product-facing `decision_verdict.json` and later narrative/commentary surfaces.
It is a safety and grounding layer, not a calculator and not a verdict engine.

## Allowed source artifacts

AI Commentary may use only evidence from allowed deterministic artifacts:

- `portfolio_xray.json`
- `stress_report.json`
- `client_fit_check.json`
- `problem_classification.json`
- `candidate_launchpad.json`
- `portfolio_alternatives_builder.json`
- `candidate_generation.json`
- `candidate_comparison.json`
- `current_vs_candidate.json`
- `selection_decision.json`
- `decision_verdict.json`
- `action_plan.json`
- `monitoring_diff.json`

The current writer may receive either the legacy comparison-flow downstream
bundle (`candidate_comparison.json`, `selection_decision.json`,
`current_vs_candidate.json`, and `decision_verdict.json`) or the direct vertical
loop bundle (`candidate_generation.json`, `current_vs_candidate.json`, and
`decision_verdict.json`). Earlier diagnosis artifacts and monitoring may be
absent in some runs; absent sources must be treated as evidence gaps, not
inferred.

## Forbidden claim categories

AI Commentary must not make claims in these categories unless a future canonical
spec explicitly changes this boundary:

- new metric calculation
- unsupported verdict
- trade execution instruction
- schema rename
- data-quality status creation
- performance guarantee
- optimizer formula change
- unstated tax advice

## Required grounding rules

Every future commentary generator that consumes `ai_commentary_context.json`
must obey these rules:

1. Use only values and statuses present in allowed source artifacts.
2. Cite an artifact and field path for every material claim.
3. Do not compute new metrics, thresholds, rankings, or optimizer results.
4. Do not rename or reinterpret Selection Engine statuses.
5. Do not issue trade execution instructions or binding investment advice.
6. State evidence gaps and confidence limitations when source artifacts warn or
   are missing.

## Artifact shape

Top-level fields:

- `schema_version`: `ai_commentary_context_v1`
- `diagnostic_only`: `true`
- `generated_at`: UTC timestamp
- `purpose`: `grounded_ai_commentary_context` (post-compare) or `diagnosis_grounding_only` (diagnosis-only)
- `grounding_phase`: `diagnosis_only` | `post_compare`
- `allowed_source_artifacts`: list of readable source artifact filenames
- `forbidden_claim_categories`: list of forbidden claim types
- `required_grounding_rules`: list of rules for any future commentary generator
- `commentary_topics`: topic-to-grounding guidance map
- `client_explanation_draft`: deterministic 5-11 sentence plain-language preview over grounded fields only
- `light_decision_journal`: compact decision-record scaffold over grounded fields only
- `evidence_references`: material source references with artifact and field path
- `hedge_gap_context`: optional Block 3.3 hedge-gap grounding slice (see below)
- `current_portfolio_stress_scorecard_context`: optional Block 3.4 stress scorecard grounding slice (see below)
- `source_artifacts`: presence map for the inputs actually available
- `guardrails`: booleans proving this layer does not call an LLM, calculate
  metrics, alter selection/verdict, or execute trades
- `warnings`: missing-source and upstream-warning list

The topic map explicitly covers diagnosis, Client Fit context, key problems, hidden exposures,
hypothesis tested, candidate generated or Builder-blocked status, current vs
candidate comparison, improvements, deteriorations, turnover/cost,
success-criteria result, Decision Verdict, no-trade rationale,
evidence-insufficient rationale, monitoring trigger grounding, and the Light
Decision Journal.

### `client_explanation_draft`

`client_explanation_draft` is a deterministic preview, not an LLM result. It
contains:

- `version`: `client_explanation_draft_v1`
- `purpose`: `deterministic_plain_language_preview`
- `does_not_call_llm`: `true`
- `does_not_create_new_metrics`: `true`
- `sentences`: ordered 5-11 topic rows, each with `topic`,
  `evidence_status`, `text`, and source `references`

The draft may say that evidence is missing, unavailable, limited, or blocked.
That is intentional. It must not turn missing Block 8 metrics into invented
improvements/worsening, and it must not turn a generated candidate into a
recommendation.

### `light_decision_journal`

`light_decision_journal` is a compact deterministic decision-record scaffold:

- `version`: `light_decision_journal_v1`
- `date`
- `current_portfolio`
- `selected_candidate` or blocked Builder status
- `untested_or_rejected_alternatives`
- `key_assumptions_and_limits`
- `decision_verdict`
- `accepted_tradeoffs`
- `next_review_trigger`

It is populated only from context inputs and warnings. It does not create a
full Decision Journal product and does not issue trade instructions.

## Evidence references

Each `evidence_references` row contains:

- `artifact`: source artifact filename
- `field_path`: field path inside the artifact
- optional `value`: source value or compact excerpt
- optional `summary`: short source summary

The context may include compact excerpts such as candidate IDs, statuses,
dimension counts, verdict IDs, and no-trade metadata. It must not create new
calculated metrics.

### Candidate Generation artifacts

When `candidate_generation.json` is available, the writer emits compact Block 7
references for:

- `generation_status`
- `method_availability`
- `source_builder_setup`
- candidate identity, source diagnosis/card ids, method, variant, capped/uncapped
  constraint summary, and status
- `hypothesis_to_test`, `success_criteria`, `tradeoff_to_watch`, and
  `decision_boundary`
- `handoff_to_comparison`

The writer does not treat the generated candidate as a rebalance
recommendation. It does not calculate weights, compare metrics, issue a
verdict, or turn failed/infeasible candidate generation into hidden fallback
evidence.

### Portfolio Alternatives Builder artifacts

When `portfolio_alternatives_builder.json` is available, the writer emits
compact Block 6 references for Builder `status`, `can_generate_candidate`,
`reason`, `validation`, and `builder_prefill`. This lets AI Commentary explain
monitor-only or data-quality-blocked cases without pretending a candidate was
generated.

### Current-vs-candidate and verdict references

When `current_vs_candidate.json` is available in a post-compare context, the
writer includes references for the selected comparison row's improvements,
deteriorations, risks reduced/added, practicality turnover/cost evidence,
success-criteria result, materiality review gate, and trade-off summary. These
are citations to the Block 8 artifact only; they are not new calculations.

When `decision_verdict.json` is available, the writer includes verdict id,
Selection-compatible status, vertical-loop `verdict_reason_id` when present,
reviewed/selected candidate ids, confidence, no-trade metadata, and rationale
summary. This lets a future AI Commentary layer explain no-trade and
evidence-insufficient outcomes without inventing a recommendation.

### Diagnosis artifacts (summary fields only)

When `portfolio_xray.json` and/or `stress_report.json` are available, the writer
must emit top-level summary references (not full block bodies), for example:

- `portfolio_xray.json`: `version`, `diagnostic_only`, `block_2_6_portfolio_weakness_map.status` / `.summary`
- `stress_report.json`: `status`, `loss_gate_mode`, `primary_diagnostic_code`, `worst_scenario_loss_pct`
- `stress_report.json` (v1-primary): `current_portfolio_stress_scorecard_v1.block_status`, `stress_diagnosis.headline`, `stress_diagnosis.diagnosis_confidence`, worst-scenario selectors — see `current_portfolio_stress_scorecard_context`
- Legacy only when Block 3.4 missing/unavailable: `stress_scorecard_v1.overall_status`

### `current_portfolio_stress_scorecard_context` (Block 3.4 Session 10)

Optional top-level object on `ai_commentary_context.json`. Compact Block 3.4 stress scorecard grounding.

| Field | Description |
| --- | --- |
| `version` | `current_portfolio_stress_scorecard_context_v1` |
| `stress_scorecard_source` | `current_portfolio_stress_scorecard_v1` when Block 3.4 `block_status` is not `unavailable`; otherwise `stress_scorecard_v1` (legacy fallback) |
| `legacy_fallback_used` | `true` when legacy mandate scorecard was used because v1 is missing or unavailable |
| `headline`, `diagnosis_confidence` | From Block 3.4 `stress_diagnosis` / nested `ai_commentary_context` |
| `forbidden_legacy_field_paths` | Field paths that must not be cited when v1-primary (e.g. `stress_scorecard_v1.overall_status`) |

**Source priority:** read `current_portfolio_stress_scorecard_context` and cite
`stress_report.json` → `current_portfolio_stress_scorecard_v1`. Use legacy
`stress_scorecard_v1.overall_status` only when v1 is missing or `block_status = unavailable`.

`commentary_topics.stress_scorecard` documents this boundary for future LLM layers.

### `hedge_gap_context` (Block 3.3 Session 09)

Optional top-level object on `ai_commentary_context.json`. Compact hedge-gap grounding for a future
commentary generator — not a second hedge-gap calculation.

| Field | Description |
| --- | --- |
| `version` | `hedge_gap_context_v1` |
| `hedge_gap_source` | `hedge_gap_analysis_v1` when v1 is present and `block_status` is not `unavailable`; otherwise `stress_conclusions.hedge_gap_status` (legacy fallback) or comparison-only source |
| `legacy_fallback_used` | `true` when legacy `hedge_gap_status` was used because v1 is missing or unavailable |
| `block_status`, `ruleset_version`, `protection_profile`, main-gap fields | Copied from `stress_report.json` → `hedge_gap_analysis_v1.summary` when v1-primary |
| `bridges_applied` | Optional map from v1 `bridge_meta` (2.4 / 2.6 confirmation bridges) |
| `comparison` | Compact slice of `candidate_comparison.json` → `hedge_gap_comparison` when post-compare |

**Source priority:** read `hedge_gap_context` and cite `stress_report.json` → `hedge_gap_analysis_v1`.
Use legacy `stress_conclusions.hedge_gap_status` and taxonomy `hedge_gap_analysis` only when v1 is
missing or `block_status = unavailable`. For candidate peer context, cite
`candidate_comparison.json` → `hedge_gap_comparison` when present.

`commentary_topics.hedge_gap` documents this boundary for future LLM layers.

### Grounding phases

| Phase | When | `purpose` | Compare-source warnings |
| --- | --- | --- | --- |
| Diagnosis-only | After materialize / before compare | `diagnosis_grounding_only` | No `missing_required_source:*` for compare bundle |
| Post-compare | After `decision_verdict.json` plus `current_vs_candidate.json`, with either Selection evidence or `candidate_generation.json` | `grounded_ai_commentary_context` | Warn when required sources for the active path are missing; ignore explicitly mismatched `product_run` verdict evidence |

Diagnosis-only `ai_commentary_context.json` may be written under `analysis_subject/` during
`run_report.py --materialize-analysis-subject`. The post-compare file at variant root replaces
or supplements it after candidate comparison.

## Integration

`run_report.py` (materialize path) writes diagnosis-only `ai_commentary_context.json` when
problem classification and launchpad are produced.

`src.candidate_comparison.write_candidate_comparison_outputs()` writes
`ai_commentary_context.json` after:

1. `current_vs_candidate.json`
2. `selection_decision.json`
3. `action_plan.json`
4. `decision_verdict.json`

When a `candidate_generation.json` artifact is present beside the comparison
bundle, `write_candidate_comparison_outputs()` passes it into the AI grounding
writer as additional Block 7 evidence.

The Blocks 5-9 vertical product loop may write `ai_commentary_context.json`
after Block 9 using `candidate_generation.json`, `current_vs_candidate.json`,
and `decision_verdict.json` without requiring `selection_decision.json`. When these artifacts carry
explicit `product_run.run_id` metadata, the AI grounding builder treats mismatched downstream
artifacts as stale: for example, a `decision_verdict.json` from another run is ignored,
`source_artifacts.decision_verdict` becomes `null`, and the context warns with
`artifact_lineage_mismatch:decision_verdict.json` rather than citing the stale verdict.

The staged web report bridge is stricter for active `/report` generation: for generated candidates,
it requires `candidate_generation.json`, `current_vs_candidate.json`, and `decision_verdict.json` to
refer to the same selected candidate and requires the active comparison row to include displayable
public evidence. If the comparison row is stale or evidence-insufficient, report generation is
blocked and the UI should ask for a fresh comparison rather than creating confident report text.
The produced context must preserve the guardrails `does_not_execute_trades`,
`does_not_call_llm`, `does_not_calculate_metrics`, and
`does_not_change_selection_or_verdict`.

Monitoring is integrated later in the product flow. If `monitoring_diff.json`
is not available at context build time, future commentary must state monitoring
context is absent instead of inventing a "what changed" narrative.
When `monitoring_diff_v1` is available, AI Commentary grounding uses its `diff_status`
field. It must not look for legacy or non-schema `change_status` fields, and it must not
emit placeholder text such as a `None` monitoring status.

## Non-goals

- no LLM invocation
- no prompt template for a provider
- no new scoring or optimizer calculation
- no JSON field renames in existing artifacts
- no replacement of `selection_decision.json`
- no generated report/PDF wording changes in this session

## Relationship to deterministic report commentary

`commentary.txt`, `stress_commentary.txt`, and decision-package summary text are produced by
deterministic report modules (`src/portfolio_commentary.py`, `src/decision_package_reporting.py`).
They are English narrative exports over structured evidence, not the target AI Commentary product
layer and not LLM output.

| Layer | Artifact | When written | Role |
| --- | --- | --- | --- |
| AI Commentary contract | `ai_commentary_context.json` | Diagnosis materialize + post-compare | Grounding only; no LLM |
| Legacy report export | `commentary.txt`, `stress_commentary.txt` | `output_profile` with `write_txt` (e.g. `full_report`) | Rule-based narrative; not AI Commentary |
| Client PDF | `pdf files/*.pdf` | `--with-pdf` / legacy rebuild | Sanitized summary of exports |

Mandate PASS/FAIL and `mandate_check` wording in `commentary.txt` / `stress_commentary.txt` applies
only when `stress_report.json` has `loss_gate_mode=mandate` (legacy policy path). Core MVP
diagnostic materialize uses `loss_gate_mode=diagnostic`; those exports are omitted on default
`site_api` (`write_txt=false`).

Product docs must not describe `commentary.txt` as proof that generated AI Commentary already exists.
The Core MVP bundle includes `ai_commentary_context.json` as the current AI Commentary contract:
grounding and guardrails only.

## Future work (not current implementation)

Natural-language AI Commentary generation requires a separate approved spec before implementation.
That future contract must define at minimum:

- provider and prompt policy
- allowed/forbidden inputs (must consume `ai_commentary_context.json`)
- output artifact name and schema
- evidence citation requirements per claim
- tests that block metric invention, verdict fabrication, and trade instructions

Until that spec exists, active docs must state **grounding context only** for AI Commentary.
Track the backlog item in [../ROADMAP.md](../ROADMAP.md) (`RM-ARCH-010`).

## Verification

Required focused checks:

```bash
python -m pytest tests/test_ai_commentary_context.py
python -m pytest tests/test_decision_verdict.py tests/test_current_vs_candidate.py
python run_portfolio_review.py --dry-run
```

Use `scripts/verify_docs.py` for documentation link checks. If archived legacy
documentation has stale links, record the failure as unrelated unless the task
explicitly targets archive repair.
