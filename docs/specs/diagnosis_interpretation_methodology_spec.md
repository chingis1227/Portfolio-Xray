# Diagnosis Interpretation Methodology Spec

Status: **methodology baseline for the dynamic interpretation foundation**. This document is a
product and methodology source for the evidence-to-diagnosis framework. It does not change runtime
behavior, formulas, thresholds, stress scenarios, optimizer policy, API schemas, frontend behavior,
generated outputs, dependencies, or `config.yml`.

Owning plan:
[2026-06-11 Diagnosis Interpretation Foundation ExecPlan](../exec_plans/2026-06-11_diagnosis_interpretation_foundation_plan.md).

Supporting research note:
[2026-06-11 Diagnosis Interpretation Framework Research](../audits/2026-06-11_diagnosis_interpretation_framework_research.md).

Rulebook schema:
[Diagnosis Rulebook Contract and YAML Schema](diagnosis_rulebook_schema_spec.md).

## Purpose

Portfolio MRI must explain an existing portfolio as a professional diagnosis, not as a loose list of
metrics and not as an optimizer-first recommendation. This spec defines the interpretation method
that turns deterministic Portfolio X-Ray and Stress Lab outputs into a controlled diagnosis,
supporting symptoms, rejected alternatives, and a next diagnostic test.

Session 04 begins implementing this methodology by adding deterministic interpretation-chain fields
to `problem_classification_v3`. A reviewer should be able to trace every material diagnosis claim
from:

    source artifact field
    -> evidence signal
    -> candidate diagnosis
    -> selected root cause
    -> supporting symptoms and rejected alternatives
    -> testable hypothesis and success criteria
    -> downstream comparison and Decision Verdict

The method is deterministic and LLM-free. Future AI Commentary may edit or summarize an already
grounded package, but it must not invent diagnoses, evidence, or trade actions.

## Scope

This document governs interpretation boundaries for:

- `portfolio_xray.json` product Blocks 2.1-2.6;
- `stress_report.json` Stress Lab Blocks 3.1-3.4;
- `problem_classification.json` / `problem_classification_v3`;
- `candidate_launchpad.json` / `candidate_launchpad_v3`;
- `site_explanation_bundle.json` diagnosis, evidence, hypothesis, comparison, verdict, and report
  copy rules;
- the future diagnosis-rulebook YAML and Block 4 rulebook loader/validator planned by the owning
  ExecPlan and specified in [diagnosis_rulebook_schema_spec.md](diagnosis_rulebook_schema_spec.md).

It is a methodology source, not a formula source. Numeric activation thresholds remain in the
owning specs and runtime registries such as `config/block_4_thresholds.yml`, Portfolio X-Ray
threshold registries, and Stress Lab specs. If a later session adds rulebook fields, those fields
must preserve the numeric source of truth instead of duplicating threshold values here.

## Non-goals

This spec does not:

- add a new diagnosis id;
- change any score, severity, confidence, materiality, or actionability formula;
- change the Stress Lab scenario set;
- add candidate generation;
- authorize automatic rebalancing;
- turn Launchpad cards into recommendations;
- promote Portfolio Health Score, Robustness Scorecard, macro dashboard, full arena ranking, or
  optimizer objectives into the current Core MVP product surface;
- require generated output refresh.

## Professional anchors

The framework is aligned to broad, stable portfolio-management principles from professional
analytics and portfolio-construction sources. These references are not copied as implementation
contracts. They justify the product method and vocabulary only.

Morningstar's Portfolio X-Ray materials frame portfolio review as a look-through exercise across
holdings, asset allocation, style, region, sector, and overlap. Portfolio MRI uses that principle
for Blocks 2.1-2.6: first answer what the user actually owns and where exposures are hidden before
asking whether anything should change.

BlackRock Aladdin Risk materials describe whole-portfolio risk analysis, risk decomposition by
portfolio/factor/sector/security, stress testing, and what-if analysis. Portfolio MRI uses that
sequence as a workflow boundary: identify structure, decompose risk, test stress, then evaluate
candidate alternatives only after an explicit user action.

CFA Institute performance evaluation and attribution material emphasizes identifying sources of
risk and return and connecting them to the investment decision process. Portfolio MRI uses that
principle by requiring a diagnosis to explain which evidence drove the conclusion, which evidence
was only symptomatic, and which alternative explanations were rejected.

Vanguard portfolio-construction materials emphasize broad asset allocation and diversification
before fund-level or optimization details. Portfolio MRI uses that hierarchy to keep the current
Core MVP diagnosis-first and current-portfolio-first: concentration, diversification, hidden
exposure, hedge gaps, rates/credit/liquidity fragility, and data quality are interpreted before any
optimizer-first narrative.

## Core definitions

An **evidence chain** is the auditable path from a source artifact field to a user-facing diagnosis.
It must preserve the source artifact, field path, interpretation, and confidence/quality context.

A **raw metric** is a computed fact such as top-3 capital weight, risk contribution, beta, max
drawdown, expected shortfall, worst stress loss, offset coverage, rates sensitivity, or data
coverage. A raw metric is not a diagnosis by itself.

An **evidence signal** is a raw metric interpreted against a governed threshold, comparison basis,
direction of concern, data-quality status, and materiality context. Evidence signals may be
confirming, supporting, contrary, weak, or unavailable.

A **problem family** is a controlled diagnosis category. Current Block 4 v3 problem families are
defined by [block_4_diagnosis_v3_spec.md](block_4_diagnosis_v3_spec.md) and
`src/block_4/problem_taxonomy.py`. User-facing output must not invent a problem family outside that
controlled taxonomy.

A **root cause** is the underlying portfolio structure that most explains the evidence. Examples are
high concentration, poor diversification, weak crisis resilience, weak hedge behavior,
duration/rates vulnerability, and credit/liquidity fragility.

A **symptom** is an observed bad outcome or surface metric that may be caused by a deeper structure.
Examples are high volatility, high drawdown, high equity beta, high tail risk, poor rates-up
behavior, and low return/risk efficiency.

A **hypothesis test** is the next diagnostic step that tests whether changing a structural driver
would improve the stated success criteria. It is not a trade instruction.

A **Decision Verdict** is the downstream decision-support layer that evaluates current-vs-candidate
comparison evidence. It may produce keep-current, no-trade, test-another, evidence-insufficient, or
review-for-action language. It remains non-binding.

## Interpretation layers

The diagnosis engine must interpret evidence through six layers.

Current implementation note: `problem_classification_v3.interpretation_chain` exposes these layers
additively for the selected Block 4 diagnosis. It mirrors display-ready fields at the top level:
`diagnosis_evidence_items`, `root_cause_narrative`, `metric_to_diagnosis_trace`, and
`professional_rationale_refs`. Session 05 also hardens prioritization so a root-cause diagnosis
outranks symptoms only when that activated root cause has at least medium confidence or medium
materiality, and rejected activated symptoms explain which selected root cause they support. These
fields and explanations do not change scoring, thresholds, candidate generation, FastAPI contracts,
or frontend behavior by themselves.

### Layer 1: source facts

The system starts from deterministic source artifacts. The most important current sources are:

- `portfolio_xray.json` Blocks 2.1-2.6 for allocation, metrics, factor exposure, hidden exposure,
  risk budget, and weakness-map evidence;
- `stress_report.json` Blocks 3.1-3.4 for scenario results, hedge-gap analysis, and stress
  scorecard evidence;
- `problem_classification.json` for current Block 4 diagnosis output;
- downstream candidate/comparison/verdict artifacts only after explicit candidate generation and
  comparison exist.

The interpretation layer must not infer a fact from a missing artifact. Missing evidence remains
missing or limited evidence.

### Layer 2: evidence signals

Evidence extraction must translate source facts into bounded evidence signals. Each signal should
carry at least:

- stable signal id;
- source artifact and field path;
- source block or calculation owner;
- observed value when available;
- threshold or comparison basis when applicable;
- direction of concern;
- severity or magnitude band when already governed elsewhere;
- data-quality status;
- confidence contribution;
- short interpretation.

Evidence extraction should not choose the primary diagnosis. It should answer only what signals are
present, weak, contrary, or unavailable.

### Layer 3: candidate diagnoses

Candidate diagnosis scoring maps evidence signals to controlled problem ids. The rulebook must not
create ad hoc labels in narrative code or frontend adapters. Each diagnosis candidate should expose
why it was activated, which signals were missing, and which contrary signals reduced confidence.

Scoring rows and match diagnostics are backend audit evidence. They may support debugging and QA, but
they must not dominate the product surface.

### Layer 4: root cause over symptom

Primary selection must prefer a root cause when it explains symptoms with enough confidence and
materiality. A symptom may be primary only when no stronger root cause is supported or when the
controlled taxonomy explicitly treats the symptom as the best available diagnosis for the evidence.
In the current runtime, a root-cause row must be activated and have at least medium confidence or
medium materiality before it can use the root-cause-over-symptom priority gate.

Examples:

- high volatility is usually a symptom if concentration, equity beta, or poor diversification
  explains it;
- high drawdown is usually a symptom if weak crisis resilience or weak hedge behavior explains it;
- high equity beta is usually a symptom if hidden equity exposure or equity-led allocation explains
  it;
- low return/risk efficiency is usually an outcome, not a direct reason to optimize.

The selected diagnosis must include rejected-diagnosis reasoning. The user should see why the system
did not choose another plausible problem when that alternative had some evidence.

### Layer 5: hypothesis and success criteria

The diagnosis must produce a next diagnostic step. It may be:

- a targeted hypothesis test;
- a reference benchmark comparison;
- monitoring;
- data-quality improvement.

The step must include a decision boundary explaining that candidate generation and rebalancing are
not automatic. Every test must define success criteria before the candidate is generated. Success
criteria should refer to already governed concepts such as lower worst stress loss, lower top-3 risk
contribution, lower concentration, improved offset coverage, reduced rates shock loss, or avoided
material deterioration in other key diagnostics.

### Layer 6: downstream verdict

Only after current-vs-candidate comparison exists may the product evaluate whether the tested
hypothesis helped enough to justify a decision review. The diagnosis layer must not pre-judge the
verdict. It should hand off the hypothesis, success criteria, trade-off to watch, when-to-skip
language, and source diagnosis id.

## Evidence quality and confidence

Confidence means quality and consistency of evidence, not severity and not persuasive tone.

High confidence should require enough clean data, governed thresholds or comparison bases, and
confirming evidence from the relevant source layers. Low confidence should be used when history is
short, taxonomy coverage is incomplete, factor evidence is weak, stress coverage is partial, signals
conflict, or important source artifacts are absent.

Current implementation note: Core MVP product blocks with `partial` or `unavailable` status now
emit the same `partial_sections` evidence signal as legacy partial sections. Partial X-Ray evidence
caps actionable diagnosis confidence. If partial X-Ray evidence is paired with unavailable Stress
Lab evidence, `evidence_insufficient_data_quality` is activated as the primary blocker; partial
X-Ray evidence alone lowers confidence but does not automatically block diagnosis or suppress
Launchpad when Stress Lab still confirms a material primary diagnosis.

Confidence text must explain the reason plainly. It should avoid marketing language and must not
hide data-quality limits.

## Contrary evidence and rejected alternatives

Professional diagnosis is more credible when it records what did not fit. Later rulebook sessions
must support contrary evidence as a first-class concept.

Contrary evidence can include:

- concentration metrics are high but risk contribution is diversified;
- volatility is high but stress losses are not unusually weak;
- hedge-gap evidence is weak because there were no meaningful hurting assets in the mapped scenario;
- rates exposure appears high but rates-up stress evidence is unavailable or offset;
- data coverage is insufficient to support a severe diagnosis.

Rejected-diagnosis explanations should be concise and sourced. They should not imply that a rejected
problem is impossible; they should state that the available evidence did not make it the primary
diagnosis. If the rejected problem is an activated symptom and the selected diagnosis is a supported
root cause, the rejection should say that the symptom supports the selected root cause rather than
competing as the primary diagnosis.

## Data-quality blocker

`evidence_insufficient_data_quality` is a diagnosis/status outcome, not a normal investment problem.
When data quality blocks reliable interpretation, the product must prefer data improvement over
candidate generation. It must not emit Equal Weight / Risk Parity reference tests as if comparison
evidence were reliable.

The blocker is reserved for hard trust failure or the combination of partial X-Ray evidence with
missing Stress Lab evidence. A single partial diagnostic block can still produce an actionable
diagnosis and Launchpad handoff when stress confirmation is available, but the confidence must be
cautious and source limitations must remain visible.

## Display and language rules

User-facing diagnosis copy should:

- lead with the current portfolio diagnosis, not a score;
- distinguish root cause from symptoms;
- show a small number of material evidence points;
- preserve source references through the site explanation bundle and API models;
- use cautious language when evidence is weak or partial;
- describe Launchpad cards as diagnostic tests or reference tests, not recommendations;
- keep technical scoring details behind audit or disclosure surfaces.

User-facing diagnosis copy must not:

- say buy, sell, guaranteed, best portfolio, or must rebalance;
- describe candidate generation as automatic;
- call a reference test a recommendation;
- use raw JSON keys as primary copy;
- invent unsupported narratives from missing artifacts.

## Rulebook implications for later sessions

The future diagnosis rulebook should be a human-readable registry that mirrors the current Python
taxonomy without changing behavior at first. Each rule should be able to express:

- `problem_id`;
- role: root cause, symptom, or outcome/status;
- professional rationale;
- required evidence signals;
- supporting evidence signals;
- contrary evidence signals;
- false-positive notes;
- activation and confidence inputs, with numeric thresholds referenced rather than duplicated;
- materiality and actionability interpretation;
- narrative templates or copy fragments;
- suggested hypothesis tests;
- success criteria;
- decision boundary;
- source references to owning specs.

Session 03 of the owning ExecPlan must prove parity between the rulebook and the current Block 4
registry before behavior changes are allowed.

## Acceptance for this methodology baseline

This spec is accepted when:

- it is linked from `docs/specs/README.md` and `SPEC.md`;
- it clearly states that metrics become evidence signals before diagnoses;
- it preserves the current Block 4 v3 taxonomy and diagnosis-first boundary;
- it states root-cause-over-symptom priority;
- it defines contrary evidence, confidence, data-quality, hypothesis, and verdict boundaries;
- it does not introduce new formulas, thresholds, runtime fields, generated outputs, or API fields;
- documentation verification passes.

## Verification

For this documentation-only methodology baseline, run:

    .\.venv\Scripts\python.exe scripts\verify_docs.py
    git diff --check

If later sessions change code, schemas, or generated artifacts, use the focused test bundles in
[../../TESTING.md](../../TESTING.md), especially the Block 4 v3 regression bundle and site
explanation bundle tests.
