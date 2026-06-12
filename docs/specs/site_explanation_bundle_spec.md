# Site Explanation Bundle Spec

This spec owns the deterministic screen-copy hierarchy contract for Portfolio MRI.

## Status

Status: **backend copy rules implemented and runtime-integrated; frontend consumes the hierarchy
for diagnosis, evidence, hypothesis/candidate, comparison, verdict, and report screens**.

Target module: `src/site_explanation_bundle.py`.

Target artifact: `{output_dir_final}/site_explanation_bundle.json` and, for portfolio-first
diagnosis sidecars, `{output_dir_final}/analysis_subject/site_explanation_bundle.json` when the
analysis subject is materialized.

Target schema version: `site_explanation_bundle_v1`.

This artifact is additive. It does not replace `ai_commentary_context.json`, does not call an LLM,
does not calculate new metrics, does not change portfolio formulas, does not change Selection or
Decision Verdict logic, and does not issue trade instructions.

## Product role

`site_explanation_bundle.json` is the site-facing copy hierarchy over existing deterministic
evidence artifacts. It turns backend evidence into structured screen text for the frontend.

The bundle exists to keep three levels of text separate:

1. **Executive text**: one or more short conclusions shown immediately.
2. **Evidence text**: sourced facts that support the executive conclusion.
3. **Technical text**: method, coverage, quality, limitation, and provenance details shown only in
   disclosure or expandable UI.

The frontend may render executive text in screen heroes, evidence text in supporting cards, and
technical text in collapsible details. The frontend must not promote technical text into the
primary executive summary.

Runtime integration:

- `run_report.py` writes diagnosis-sidecar `site_explanation_bundle.json` for analysis-subject
  materialization, including core-diagnostics-only runs when only X-Ray and stress evidence exist.
- `src/candidate_comparison.py` writes or refreshes root `site_explanation_bundle.json` after
  Block 8-only comparison and after the full compare/verdict/monitoring package.
- `scripts/run_review_from_payload.py` exposes the bundle to the local frontend bridge during
  initial diagnosis, comparison, verdict, and report-context stages.
- The frontend renders executive copy first, supporting evidence second, and technical copy inside
  a disclosure panel. It treats the bundle as additive explanation, not as a replacement for the
  underlying artifact-specific panels.

## Allowed source artifacts

The bundle may use only deterministic source artifacts already produced by the portfolio review
workflow:

- `portfolio_xray.json`
- `stress_report.json`
- `problem_classification.json`
- `candidate_launchpad.json`
- `portfolio_alternatives_builder.json`
- `candidate_generation.json`
- `candidate_comparison.json`
- `current_vs_candidate.json`
- `selection_decision.json`
- `decision_verdict.json`
- `ai_commentary_context.json`
- `what_changed_summary.json`
- `monitoring_diff.json`

Absent artifacts must be treated as missing evidence, not inferred evidence.

## Top-level shape

The bundle must use this top-level shape:

```json
{
  "schema_version": "site_explanation_bundle_v1",
  "review_id": "...",
  "generated_at": "...",
  "screens": {
    "diagnosis": {
      "executive": [],
      "evidence": [],
      "technical": []
    }
  },
  "source_artifacts": {},
  "warnings": [],
  "guardrails": {}
}
```

The required screen keys are:

- `diagnosis`
- `evidence`
- `hypothesis`
- `candidate`
- `comparison`
- `verdict`
- `report`
- `monitoring`

Every screen object must contain all three hierarchy arrays: `executive`, `evidence`, and
`technical`. Arrays may be empty only when the screen is not yet available, but the screen key and
the hierarchy keys must still exist.

## Text item shape

Every text item must use this shape:

```json
{
  "id": "diagnosis.executive.primary",
  "level": "executive",
  "text": "The portfolio is equity-led, concentrated in top holdings, and shows weak hedge protection in severe recession stress.",
  "tone": "risk",
  "evidence_status": "available",
  "claim_type": "material_claim",
  "source_refs": [
    {
      "artifact": "portfolio_xray.json",
      "field_path": "block_2_6_portfolio_weakness_map.summary"
    }
  ]
}
```

Allowed `level` values:

- `executive`
- `evidence`
- `technical`

Allowed `tone` values:

- `neutral`
- `caution`
- `risk`
- `positive`

Allowed `evidence_status` values:

- `available`
- `limited`
- `missing`
- `preliminary`

Allowed `claim_type` values:

- `material_claim`: any claim about the portfolio, evidence, candidate, comparison, verdict, or
  monitoring state.
- `boundary_note`: static product boundary copy such as "Decision-support only."
- `empty_state`: missing or blocked state copy.

## Source requirement

Every `material_claim` must have at least one `source_refs` row. Each source reference must contain:

- `artifact`
- `field_path`

Static `boundary_note` text may have an empty `source_refs` list. Missing-evidence `empty_state`
text may have an empty `source_refs` list only when the bundle also records an explicit warning such
as `missing_source:portfolio_xray` or `missing_source:stress_report`.

The bundle must never silently emit a material claim without source references.

## Copy hierarchy rules

### Implemented diagnosis, stress, candidate, comparison, and verdict rules

The current backend implementation populates deterministic copy rules for diagnosis, stress,
candidate, comparison, and verdict evidence:

- `screens.diagnosis` prefers the Block 4 v3 interpretation-chain fields when they are available:
  `root_cause_narrative`, `diagnosis_evidence_items`, `metric_to_diagnosis_trace`, and
  `interpretation_chain.next_step_link`.
- Diagnosis executive text uses `root_cause_narrative.statement_en` before falling back to the
  older primary-diagnosis label sentence. It may append materiality and confidence, but it must not
  turn the diagnosis into an instruction.
- Diagnosis evidence text uses `root_cause_narrative.portfolio_manager_interpretation_en` and up to
  three `diagnosis_evidence_items` before falling back to `why_this_matters` and Block 4 key
  evidence.
- Diagnosis interpretation-chain evidence items may source their material claim directly to the
  underlying deterministic artifact named by the evidence item (`portfolio_xray.json` or
  `stress_report.json`) when a supported field path is present; otherwise they source to
  `problem_classification.json`.
- Diagnosis technical text may include the root-cause-over-symptom boundary,
  metric-to-diagnosis trace count, and `interpretation_chain.next_step_link` as disclosure/handoff
  details. If the interpretation chain is absent, it falls back to `next_diagnostic_step`.
- When Block 4 is absent but `portfolio_xray.json.block_2_6_portfolio_weakness_map` exists, the
  diagnosis screen falls back to the weakness-map summary and the top scored risk-type diagnoses.
- Stress Test Lab copy is currently emitted under `screens.evidence` because the v1 screen-key
  contract has no separate `stress` screen key.
- Stress executive text may state the weakest synthetic stress scenario result from
  `stress_results_v1.worst_synthetic` or, when that block is absent,
  `stress_conclusions.worst_synthetic_scenario`.
- Stress evidence text may state the weakest historical replay, top loss contributors, and main
  hedge-gap offset coverage when those deterministic fields are available.
- Stress technical text may state scenario/episode coverage counts and overall confidence from
  `stress_scorecard_v1`.
- Candidate screen copy uses `candidate_generation.json.candidate` to explain the diagnostic
  candidate test, preserved hypothesis, success criteria, trade-off to watch, decision boundary,
  method, and comparison handoff state.
- Candidate copy must continue to describe the candidate as a diagnostic test candidate, not a
  recommendation.
- When source candidate fields contain negated recommendation-boundary wording such as "not a
  recommendation", the site bundle must rewrite that word choice before emitting candidate-screen
  copy. Candidate hierarchy text must not contain `recommend*` wording even when the underlying
  source field is correctly saying that the candidate is not advice.
- Comparison screen copy uses the first active `current_vs_candidate.json.comparisons[]` row to
  state the active current-vs-candidate comparison, improvement/worsening evidence, reduced/added
  risk evidence, success-criteria result, practicality evidence, and the decision-review
  materiality gate.
- When only canonical `candidate_comparison.json` is available and no active
  `current_vs_candidate.json` row exists, the comparison screen may emit technical limited-evidence
  disclosure but must not invent an active candidate comparison conclusion.
- Verdict screen copy is emitted only when both `decision_verdict.json` and active comparison
  evidence are available. Without comparison evidence, the verdict screen emits a blocked empty
  state rather than an action/no-action conclusion.
- Verdict executive copy maps verdict IDs to bounded decision-support language, such as keeping the
  current portfolio under review thresholds, testing another candidate, evidence-insufficient, or
  candidate flagged for decision review. It avoids turning backend verdict labels into automatic
  trade instructions.
- Verdict evidence copy may include `rationale_summary` and `no_trade`; technical copy may include
  reason ID and confidence-limitation counts.

These rules only adapt existing deterministic fields. They do not compute new diagnosis, stress,
hedge-gap, ranking, comparison, practicality, materiality, no-trade, or verdict metrics.

### Level 1 — executive text

Executive text is the first user-facing explanation. It must be short, plain-language, and
decision-support oriented. It must not include technical coverage details such as synthetic stress
coverage, replay counts, schema names, raw JSON keys, or method diagnostics.

Example:

> The portfolio is equity-led, concentrated in top holdings, and shows weak hedge protection in
> severe recession stress.

### Level 2 — evidence text

Evidence text contains supporting facts. Evidence text should be specific and sourced.

Examples:

- Top 3 holdings account for 80% of capital.
- SPY and QQQ contribute around 90% of normal portfolio risk.
- Severe recession offset coverage is only 2.4%.

### Level 3 — technical text

Technical text is for disclosure, debug-safe explanation, and advanced review. It should be shown
only behind expansion or detail UI.

Examples:

- Synthetic stress coverage: 8 of 8.
- Historical replay coverage: 3 of 5.
- Factor evidence quality: moderate.

## Missing and limited evidence language

When evidence is absent, stale, partial, or too weak, the bundle must use cautious language.
Accepted cautious formulations include:

- Evidence is limited.
- This signal should be treated as preliminary.
- Historical replay is unavailable for older episodes.

The bundle must not convert missing evidence into a strong executive conclusion.

## Candidate and verdict boundaries

A candidate is a diagnostic test candidate, not a recommendation. Candidate text may use:

- test candidate
- diagnostic candidate
- candidate test

Candidate text must not describe the candidate as a recommendation.

Verdict text must not appear until valid comparison evidence and `decision_verdict.json` are
available for the active candidate. Before that point, the verdict screen may show a blocked or
empty state, but must not create an action/no-action conclusion.

No-trade, keep-current, test-another-hypothesis, and evidence-insufficient are valid
decision-support outcomes.

## Forbidden language

The bundle must not emit these terms or phrases in generated product copy:

- `buy`
- `sell`
- `must rebalance`
- `best portfolio`
- `guaranteed`

The phrase `optimal portfolio` is forbidden except in technical method context. It may appear only
when all of the following are true:

- the item `level` is `technical`;
- the item explains method or optimizer disclosure;
- the item does not describe the active candidate or verdict as advice.

## Guardrails

The top-level `guardrails` object must include:

```json
{
  "does_not_call_llm": true,
  "does_not_create_new_metrics": true,
  "does_not_issue_trade_instruction": true,
  "candidate_is_not_recommendation": true
}
```

The implementation may add additional guardrails, but these four are required.

## Initial test ownership

The implementation must add these focused tests:

- `tests/test_site_explanation_bundle.py`
- `tests/test_site_explanation_guardrails.py`
- `tests/test_site_explanation_sources.py`
- `tests/test_site_explanation_diagnosis_stress.py`
- `tests/test_site_explanation_candidate_comparison_verdict.py`

The minimum test coverage must verify:

- `schema_version == "site_explanation_bundle_v1"`;
- every screen has `executive`, `evidence`, and `technical`;
- missing evidence emits cautious text;
- material claims have source references;
- forbidden language is blocked;
- candidates are not called recommendations;
- verdict text is absent before comparison and `decision_verdict.json`.
