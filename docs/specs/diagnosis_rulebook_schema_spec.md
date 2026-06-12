# Diagnosis Rulebook Contract and YAML Schema

Status: **parity interface contract with a read-only Session 03 implementation**. This document
defines the human-readable diagnosis rulebook shape that mirrors the current Block 4 Python
registry. `config/diagnosis_rulebook.yml` and the read-only loader/validator in
`src/block_4/diagnosis_rulebook.py` exist as parity evidence only. They do not change runtime
behavior, formulas, thresholds, diagnosis ids, scoring, generated artifacts, API models, frontend
behavior, dependencies, or `config.yml`.

Owning plan:
[2026-06-11 Diagnosis Interpretation Foundation ExecPlan](../exec_plans/2026-06-11_diagnosis_interpretation_foundation_plan.md).

Methodology source:
[Diagnosis Interpretation Methodology Spec](diagnosis_interpretation_methodology_spec.md).

Current runtime source:
`src/block_4/problem_taxonomy.py`, `src/block_4/evidence_extraction.py`,
`src/block_4/problem_scoring.py`, and `config/block_4_thresholds.yml`.

## Purpose

The diagnosis rulebook is the future editable registry that explains why a controlled diagnosis can
be selected. It must make the interpretation layer auditable without moving financial math or
activation thresholds into narrative code. A reviewer should be able to open the YAML, see the
allowed diagnosis ids, understand the professional rationale, see which evidence signals support or
contradict each diagnosis, and trace the diagnosis to a hypothesis test and success criteria.

The first implementation goal is parity, not new behavior. Session 03 proves that the YAML contains
the same problem ids, roles, action paths, signal references, Launchpad copy, false-positive notes,
and downstream comparison focus as the current Python registry before any runtime code reads it as
product behavior.

## Scope

This spec governs `config/diagnosis_rulebook.yml`.

The planned YAML owns interpretation metadata only:

- controlled `problem_id` entries;
- diagnosis role (`root_cause`, `symptom`, or `outcome`);
- professional rationale and false-positive / false-negative notes;
- required, supporting, and contrary evidence signal references;
- action-path and Launchpad handoff metadata;
- narrative templates or display fragments that remain bounded to evidence;
- hypothesis tests and success criteria;
- source references to owning specs and runtime modules.

It does not own numeric thresholds. Numeric activation, materiality, severity, confidence, signal
strength, and stress-confirmation settings remain in `config/block_4_thresholds.yml` and the owning
Block 2 / Block 3 / Block 4 specs.

## Non-goals

The rulebook schema does not:

- add new diagnosis ids;
- change current Block 4 v3 primary-selection order;
- change evidence extraction or scoring formulas;
- duplicate numeric thresholds from `config/block_4_thresholds.yml`;
- authorize trade recommendations;
- change Candidate Launchpad from diagnostic tests into recommendations;
- add generated output fields;
- change FastAPI or frontend contracts.

## Source-of-truth boundaries

For Session 03 parity, the current runtime source remains authoritative:

| Contract area | Current source | Future YAML role |
| --- | --- | --- |
| Problem ids and roles | `src/block_4/problem_taxonomy.py` | Mirror exactly before behavior changes |
| Action paths and candidate method hints | `src/block_4/problem_taxonomy.py` | Mirror exactly before behavior changes |
| Evidence signal names | `src/block_4/evidence_extraction.py` and taxonomy signal fields | Reference by id only |
| Numeric thresholds and scoring weights | `config/block_4_thresholds.yml` | Reference by threshold key only |
| Primary selection order | `docs/specs/block_4_diagnosis_v3_spec.md` and current prioritization code | Document rationale; do not replace yet |
| Product methodology | `docs/specs/diagnosis_interpretation_methodology_spec.md` | Implement as structured metadata |

When sources disagree during Session 03, do not silently choose the YAML. Fail validation and update
the ExecPlan with the mismatch.

## Controlled ids

The YAML must use only the current Block 4 v3 problem ids unless an accepted later spec changes the
taxonomy.

Root-cause diagnoses:

- `weak_crisis_resilience`
- `poor_diversification`
- `high_concentration`
- `duration_rates_vulnerability`
- `credit_liquidity_fragility`
- `weak_hedge_behavior`

Symptoms:

- `high_volatility`
- `high_drawdown`
- `high_equity_beta`
- `high_tail_risk`
- `low_return_risk_efficiency`
- `poor_rates_up_behavior`

Outcome/status diagnoses:

- `current_portfolio_acceptable`
- `mixed_evidence_no_action`
- `evidence_insufficient_data_quality`

Allowed diagnosis roles are exactly `root_cause`, `symptom`, and `outcome`.

## File-level schema

The YAML top level must be a mapping with these required keys:

| Key | Type | Required | Meaning |
| --- | --- | --- | --- |
| `schema_version` | string | yes | YAML schema version, initially `diagnosis_rulebook_schema_v1` |
| `ruleset_version` | string | yes | Human-readable ruleset version, initially aligned to Block 4 v3 |
| `status` | string | yes | `planned`, `parity`, or `active`; Session 03 should start as `parity` |
| `threshold_source` | string | yes | Must be `config/block_4_thresholds.yml` for v1 |
| `runtime_parity_source` | mapping | yes | Runtime modules the validator compares against |
| `allowed_roles` | list[string] | yes | Must be `root_cause`, `symptom`, `outcome` |
| `action_paths` | mapping | yes | Action-path registry keyed by `action_path_id` |
| `problems` | mapping | yes | Problem registry keyed by `problem_id` |
| `prioritization_rules` | list[mapping] | yes | Root-cause-over-symptom and outcome ordering hints |
| `governance` | mapping | yes | Anti-hallucination, recommendation-boundary, and validation rules |

Minimal top-level example:

```yaml
schema_version: diagnosis_rulebook_schema_v1
ruleset_version: block_4_v3_2026_06
status: parity
threshold_source: config/block_4_thresholds.yml
runtime_parity_source:
  problem_registry: src/block_4/problem_taxonomy.py::PROBLEM_REGISTRY
  action_path_registry: src/block_4/problem_taxonomy.py::ACTION_PATH_REGISTRY
  evidence_extractor: src/block_4/evidence_extraction.py::extract_evidence_signals
allowed_roles:
  - root_cause
  - symptom
  - outcome
action_paths: {}
problems: {}
prioritization_rules: []
governance: {}
```

## Action-path schema

Each `action_paths.<action_path_id>` entry must contain:

| Key | Type | Required | Meaning |
| --- | --- | --- | --- |
| `label_en` | string | yes | Short product label |
| `goal_label` | string | yes | Launchpad goal label |
| `candidate_method_ids` | list[string] | yes | Candidate builders that can test the path; may be empty |
| `launchpad_description_en` | string | yes | What the diagnostic test is meant to check |
| `decision_boundary_en` | string | yes | Required non-recommendation boundary |
| `source_refs` | list[string] | yes | Owning specs or runtime modules |

The validator must compare `label_en`, `goal_label`, `candidate_method_ids`, and
`launchpad_description_en` to the current `ACTION_PATH_REGISTRY` during parity mode.

## Problem schema

Each `problems.<problem_id>` entry must contain:

| Key | Type | Required | Meaning |
| --- | --- | --- | --- |
| `label_en` | string | yes | User-facing diagnosis label |
| `legacy_ids` | list[string] | yes | Legacy aliases; empty list when none |
| `role` | enum | yes | One of `root_cause`, `symptom`, `outcome` |
| `eligible_as_primary` | boolean | yes | Mirrors current registry eligibility |
| `suppress_launchpad_methods` | boolean | yes | Mirrors current registry method-suppression flag |
| `technical_definition_en` | string | yes | Bounded technical definition |
| `portfolio_manager_interpretation_en` | string | yes | Plain-English professional meaning |
| `professional_rationale_en` | string | yes | Why this diagnosis matters in portfolio review |
| `evidence` | mapping | yes | Required/supporting/contrary signal references |
| `threshold_refs` | list[string] | yes | Threshold keys referenced by id, not numeric values |
| `action_paths` | mapping | yes | Primary and secondary action-path ids |
| `launchpad` | mapping | yes | Launchpad card copy and default candidate methods |
| `false_positive_notes_en` | list[string] | yes | Common over-trigger explanations |
| `false_negative_notes_en` | list[string] | yes | Common under-trigger explanations |
| `when_not_primary_en` | string | yes | Root-cause-over-symptom demotion or selection boundary |
| `do_not_overreact_en` | string | yes | Caution text for user-facing copy |
| `hypothesis_tests` | list[mapping] | yes | Diagnostic tests to pass to Launchpad/Builder |
| `success_criteria` | list[mapping] | yes | What would count as improvement |
| `downstream_comparison_focus_en` | string | yes | Metrics/evidence to inspect after a candidate exists |
| `narrative_templates` | mapping | yes | Bounded copy fragments; no unsupported claims |
| `source_refs` | list[string] | yes | Specs, code modules, or artifact contracts that govern the entry |

Problem entries may include `subtypes` when the current registry has `diagnosis_subtypes`.

## Evidence schema

Each problem's `evidence` mapping must contain:

| Key | Type | Required | Meaning |
| --- | --- | --- | --- |
| `required_signals` | list[string] | yes | Signal ids that activate the diagnosis family |
| `supporting_signals` | list[string] | yes | Signal ids that add confidence or materiality context |
| `contrary_signals` | list[string] | yes | Negative evidence or false-positive guards |
| `missing_evidence_policy_en` | string | yes | How to describe unavailable evidence |
| `source_artifacts` | list[string] | yes | Expected source artifacts, usually `portfolio_xray.json` and/or `stress_report.json` |

Signals are ids, not formulas. If a future signal needs a formula, add it to the owning code/spec
first and reference the signal id from the rulebook after implementation.

## Threshold references

`threshold_refs` must contain symbolic keys only. Valid v1 references are paths into
`config/block_4_thresholds.yml`, for example:

- `activation.raw_score_min`
- `materiality_bands.high_min`
- `stress_confirmation_multipliers.confirmed`
- `signal_strength.top_weight_baseline_pct`
- `confidence.partial_data_cap`

The YAML must not contain numeric activation or materiality constants. The Session 03 validator
should fail if a `threshold_refs` entry is not present in `config/block_4_thresholds.yml` or if a
problem entry introduces top-level numeric scoring fields outside examples marked as non-runtime
documentation.

## Hypothesis-test schema

Each `hypothesis_tests[]` item must contain:

| Key | Type | Required | Meaning |
| --- | --- | --- | --- |
| `test_id` | string | yes | Stable id, unique within the problem |
| `hypothesis_to_test_en` | string | yes | Testable, non-advice hypothesis |
| `preferred_action_path_id` | string | yes | Must exist in `action_paths` |
| `suggested_method_ids` | list[string] | yes | Must be a subset of allowed candidate method ids for that action path unless empty |
| `success_criteria_refs` | list[string] | yes | Links to `success_criteria[].criterion_id` |
| `tradeoff_to_watch_en` | string | yes | Trade-off to show before candidate generation |
| `when_to_skip_en` | string | yes | Why the test may be inappropriate |
| `decision_boundary_en` | string | yes | Must state that comparison and Decision Verdict decide action |

## Success-criteria schema

Each `success_criteria[]` item must contain:

| Key | Type | Required | Meaning |
| --- | --- | --- | --- |
| `criterion_id` | string | yes | Stable id |
| `label_en` | string | yes | Short display label |
| `metric_or_signal_refs` | list[string] | yes | Source metrics/signals to inspect |
| `direction` | enum | yes | `lower_is_better`, `higher_is_better`, `non_deterioration`, or `resolved` |
| `source_artifacts` | list[string] | yes | Artifacts that can prove the criterion |
| `explanation_en` | string | yes | Plain-English meaning |

Success criteria must not promise that a candidate is best. They only define what would count as a
successful diagnostic test.

## Narrative-template schema

`narrative_templates` must stay bounded to deterministic evidence. It may contain:

| Key | Type | Required | Meaning |
| --- | --- | --- | --- |
| `headline_en` | string | yes | Evidence-bounded diagnosis headline |
| `root_cause_narrative_en` | string | yes | Root-cause explanation, or outcome/status explanation |
| `evidence_sentence_templates_en` | list[string] | yes | Templates that require explicit signal values/source refs |
| `contrary_evidence_template_en` | string | yes | How to explain why an alternative was not primary |
| `confidence_template_en` | string | yes | How to explain confidence without persuasive tone |

Templates may use placeholders such as `{signal_label}`, `{observed_value}`, `{source_block}`, and
`{threshold_label}`. A renderer must omit a sentence rather than fill it from missing evidence.

## Example problem entry

This example shows shape only. It is not an instruction to change current runtime behavior.

```yaml
problems:
  high_concentration:
    label_en: High concentration
    legacy_ids: []
    role: root_cause
    eligible_as_primary: true
    suppress_launchpad_methods: false
    technical_definition_en: Top-1 or top-3 capital weights or RC concentration flags exceed governed thresholds.
    portfolio_manager_interpretation_en: A few holdings dominate capital or risk budget.
    professional_rationale_en: Concentration can explain volatility, drawdown, and stress losses better than those symptoms alone.
    evidence:
      required_signals:
        - top1_weight_pct
        - top3_weight_pct
      supporting_signals:
        - rc_top1_share
        - concentration_flags
      contrary_signals:
        - broad_equal_weights
      missing_evidence_policy_en: If concentration snapshots are unavailable, do not infer concentration from volatility alone.
      source_artifacts:
        - portfolio_xray.json
    threshold_refs:
      - signal_strength.top_weight_baseline_pct
      - signal_strength.top_weight_range_pct
      - signal_strength.rc_top1_baseline_pct
      - signal_strength.rc_top1_range_pct
    action_paths:
      primary_action_path_id: reduce_concentration
      secondary_action_path_ids:
        - improve_diversification
    launchpad:
      card_title_en: Reduce Concentration
      what_this_tests_en: Whether equalized or capped exposures reduce dominant holding risk.
      tradeoff_en: Less concentration vs potential return from best ideas.
      skip_when_en: Skip when top weight is intentional mandate expression and risk is acceptable.
      default_candidate_method_ids:
        - equal_weight
        - risk_parity
        - maximum_diversification
    false_positive_notes_en:
      - Many small lines can still hide one dominant factor exposure; do not rely on holding count alone.
    false_negative_notes_en:
      - Low capital weights can still produce risk-contribution concentration.
    when_not_primary_en: Prefer poor_diversification when correlated clones, not a single dominant weight, are the clearer root cause.
    do_not_overreact_en: Moderate top holding in a liquid core may be acceptable if risk contribution is balanced.
    hypothesis_tests:
      - test_id: high_concentration_equalized_exposure_test
        hypothesis_to_test_en: Test whether equalized exposure lowers concentration without unacceptable deterioration elsewhere.
        preferred_action_path_id: reduce_concentration
        suggested_method_ids:
          - equal_weight
          - risk_parity
        success_criteria_refs:
          - lower_top3_capital_weight
          - lower_top3_risk_contribution
        tradeoff_to_watch_en: Diversification improvement vs turnover and loss of intended best-idea exposure.
        when_to_skip_en: Skip when concentration is intentional and already documented as acceptable.
        decision_boundary_en: Candidate comparison and Decision Verdict decide whether any action is justified.
    success_criteria:
      - criterion_id: lower_top3_capital_weight
        label_en: Lower top-three capital concentration
        metric_or_signal_refs:
          - top3_weight_pct
        direction: lower_is_better
        source_artifacts:
          - portfolio_xray.json
          - current_vs_candidate.json
        explanation_en: The candidate should reduce dependence on the largest holdings.
      - criterion_id: lower_top3_risk_contribution
        label_en: Lower top risk contribution
        metric_or_signal_refs:
          - rc_top1_share
        direction: lower_is_better
        source_artifacts:
          - portfolio_xray.json
          - current_vs_candidate.json
        explanation_en: The candidate should reduce dependence on the largest risk contributors.
    downstream_comparison_focus_en: Compare top weights, RC top3 share, and stress loss contributors.
    narrative_templates:
      headline_en: The main issue is concentration.
      root_cause_narrative_en: The portfolio is dominated by a small set of exposures.
      evidence_sentence_templates_en:
        - "{signal_label} is {observed_value} in {source_block}."
      contrary_evidence_template_en: Concentration was not selected when breadth or risk contribution evidence contradicted the capital-weight signal.
      confidence_template_en: Confidence depends on clean concentration snapshots and confirming risk-budget evidence.
    source_refs:
      - docs/specs/block_4_diagnosis_v3_spec.md
      - src/block_4/problem_taxonomy.py
      - src/block_4/evidence_extraction.py
```

## Prioritization-rule schema

`prioritization_rules[]` records human-readable root-cause-over-symptom logic and expected parity
with current elevation hints. Each item must contain:

| Key | Type | Required | Meaning |
| --- | --- | --- | --- |
| `rule_id` | string | yes | Stable id |
| `prefer_primary` | string | yes | Problem id that should usually win |
| `demote_when_present` | list[string] | yes | Problem ids that are symptoms or weaker explanations |
| `requires_signals` | list[string] | yes | Signal ids required for the preference; may be empty |
| `requires_stress_confirmation` | boolean | yes | Whether stress evidence is required |
| `rationale_en` | string | yes | Plain-English reason |
| `source_refs` | list[string] | yes | Runtime/spec references |

Session 03 must compare this section with `ROOT_CAUSE_ELEVATION_RULES` where applicable.

## Governance schema

`governance` must include:

| Key | Type | Required | Meaning |
| --- | --- | --- | --- |
| `no_recommendation_language_en` | string | yes | Mandatory boundary for tests/cards |
| `missing_evidence_policy_en` | string | yes | Missing data cannot become a diagnosis claim |
| `unsupported_claim_policy_en` | string | yes | Renderer/validator must reject unsupported claims |
| `numeric_threshold_policy_en` | string | yes | Thresholds live outside the rulebook |
| `allowed_source_artifacts` | list[string] | yes | Artifact names the rulebook may reference |
| `required_validation_checks` | list[string] | yes | Validator checks expected before activation |

Minimum required validation checks:

- `problem_ids_match_python_registry`
- `action_paths_match_python_registry`
- `roles_match_python_registry`
- `signals_exist_in_registry_or_extractor`
- `threshold_refs_exist_in_threshold_source`
- `no_numeric_activation_thresholds_in_rulebook`
- `launchpad_methods_match_python_registry`
- `source_refs_exist`
- `no_recommendation_language`

## Session 03 loader and validator implementation

The Session 03 loader is read-only. It parses `config/diagnosis_rulebook.yml`, validates the schema,
then compares the YAML to the current Python registry. It must not replace `PROBLEM_REGISTRY`,
`ACTION_PATH_REGISTRY`, evidence extraction, scoring, prioritization, or Launchpad generation until
a later accepted session promotes the YAML from parity evidence to active runtime source.

Implementation files:

- `config/diagnosis_rulebook.yml`
- `src/block_4/diagnosis_rulebook.py`
- `tests/test_diagnosis_rulebook.py`

Expected focused tests for Session 03:

- the YAML parses as a mapping;
- all required top-level keys exist;
- all current Python `problem_id` keys exist in YAML and no extra problem ids are present;
- all current Python `action_path_id` keys exist in YAML and no extra action-path ids are present;
- role, eligibility, method suppression, signal lists, action paths, Launchpad card fields, caution
  notes, and downstream comparison focus match the Python registry;
- every `threshold_refs` path exists in `config/block_4_thresholds.yml`;
- every `source_refs` path exists;
- no current Problem Classification artifact changes when validation runs.

## Acceptance for Session 03

Session 03 is accepted when:

- `config/diagnosis_rulebook.yml` exists and uses `status: parity`;
- `src/block_4/diagnosis_rulebook.py` can load and validate the YAML without mutating Block 4
  runtime registries or generated artifacts;
- the validator checks required top-level keys, problem ids, action-path ids, roles, signal lists,
  Launchpad fields, threshold refs, source refs, root-cause prioritization rules, and governance
  checks;
- `tests/test_diagnosis_rulebook.py` proves parity against `src/block_4/problem_taxonomy.py`,
  `ROOT_CAUSE_ELEVATION_RULES`, and `config/block_4_thresholds.yml`;
- focused tests pass without changing Block 4 diagnosis behavior.

## Acceptance for Session 02

Session 02 is accepted when:

- this spec exists and is linked from `docs/specs/README.md` and `SPEC.md`;
- the spec defines the planned `diagnosis_rulebook.yml` file under `config/`;
- the schema separates interpretation metadata from numeric thresholds;
- the schema covers rationale, required/supporting/contrary evidence, false positives, hypothesis
  tests, success criteria, narrative templates, action paths, and governance;
- it states that Session 03 must prove parity with the current Python registry before behavior
  changes;
- documentation verification and `git diff --check` pass.

## Verification

For the Session 03 parity implementation, run:

    .\.venv\Scripts\python.exe -m pytest tests\test_diagnosis_rulebook.py tests\test_block_4_problem_taxonomy.py -q
    .\.venv\Scripts\python.exe scripts\verify_docs.py
    git diff --check

No portfolio review, generated-output refresh, FastAPI server run, frontend build, or browser QA is
required for Session 03 because the YAML remains read-only parity evidence and no runtime behavior
changes.
