# Full Demo MVP Guide

This guide is the operator package for the current Portfolio MRI Core MVP demo.
It is practical, not promotional: it explains what to run, where to look, and how to interpret honest
`no-trade`, `evidence_insufficient`, or Builder-blocked outcomes.

## What the demo proves

The current demo is a diagnosis-first, current-portfolio-first product loop:

```text
Input portfolio
-> Portfolio Diagnosis
-> Stress Test Lab
-> Problem Classification
-> Candidate Launchpad
-> Portfolio Alternatives Builder
-> one Candidate Generation attempt
-> Current vs Candidate
-> Decision Verdict
-> AI Commentary grounding
```

The demo should answer four questions:

1. What is the current portfolio problem...
2. What one hypothesis was tested...
3. What improved and what worsened, when evidence is available...
4. Is action justified, or should the user keep the current portfolio / review missing evidence...

The demo is **not** an optimizer cockpit, not a candidate arena, and not a polished PDF report. Equal
Weight and Risk Parity are diagnostic reference tests unless a later verdict justifies action. A
candidate attempt is not automatically a recommendation.

## Setup

Install dependencies once from the repository root:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

If `.venv` does not exist, create it first:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

All commands below assume the working directory is the repository root.

## Demo portfolios

Source-controlled demo configs live under `config/demo_portfolios/`:

| Portfolio | Config | Output folder | Story to expect |
| --- | --- | --- | --- |
| Balanced diversified | `config/demo_portfolios/balanced.yml` | `output/demo_portfolios/balanced/final/` | Mixed evidence / no dominant actionable problem; Equal Weight can be tested as a reference comparison. |
| Equity-heavy / concentrated | `config/demo_portfolios/equity_heavy.yml` | `output/demo_portfolios/equity_heavy/final/` | Equity concentration is visible, but the current Block 4 fixture still resolves to mixed evidence / no immediate action. |
| Defensive / rates-sensitive | `config/demo_portfolios/defensive_rates_sensitive.yml` | `output/demo_portfolios/defensive_rates_sensitive/final/` | Weak crisis resilience / rate sensitivity; Builder may block candidate generation when the selected card is monitor-only or data-quality gated. |

## Commands

Canonical one-hypothesis vertical demo:

```powershell
.\.venv\Scripts\python.exe scripts\run_blocks_5_to_9_vertical_flow.py --config config\demo_portfolios\balanced.yml --method equal_weight --force-candidate
```

Run all three demo fixtures:

```powershell
.\.venv\Scripts\python.exe scripts\run_blocks_5_to_9_vertical_flow.py --config config\demo_portfolios\balanced.yml --method equal_weight --force-candidate
.\.venv\Scripts\python.exe scripts\run_blocks_5_to_9_vertical_flow.py --config config\demo_portfolios\equity_heavy.yml --method equal_weight --force-candidate
.\.venv\Scripts\python.exe scripts\run_blocks_5_to_9_vertical_flow.py --config config\demo_portfolios\defensive_rates_sensitive.yml --method equal_weight --force-candidate
```

Optional: attempt fresher backend comparison snapshots with standard factory execution:

```powershell
.\.venv\Scripts\python.exe scripts\run_blocks_5_to_9_vertical_flow.py --config config\demo_portfolios\balanced.yml --method equal_weight --force-candidate --factory-execution-mode standard
```

Use `standard` only when you can tolerate a slow run. In the current environment, full factor/FRED
availability may still fail or time out. That is an infrastructure limitation to surface, not a
reason to fake comparison metrics.

## Where outputs are written

Read the files in this order inside each portfolio's `output_dir_final`.

| Step | File | Meaning |
| --- | --- | --- |
| 1 | `analysis_subject/run_metadata.json` | Confirms the reviewed portfolio, input mode, weights source, and analysis window. |
| 2 | `analysis_subject/portfolio_xray.json` | Current portfolio diagnosis diagnostics. |
| 3 | `analysis_subject/stress_report.json` | Stress Test Lab and factor/stress evidence. |
| 4 | `analysis_subject/problem_classification.json` | The primary diagnosis and key evidence. |
| 5 | `analysis_subject/candidate_launchpad.json` | Hypotheses / tests to consider next. |
| 6 | `analysis_subject/portfolio_alternatives_builder.json` | Builder setup for one selected card; this is setup only, not a candidate. |
| 7 | `candidate_generation.json` | One explicit candidate attempt, if Builder allowed generation. |
| 8 | `current_vs_candidate.json` | Current vs selected candidate, if comparison evidence exists. |
| 9 | `decision_verdict.json` | The action / no-action / no-trade / evidence-insufficient decision framing. |
| 10 | `ai_commentary_context.json` | Grounding context for future commentary; not polished client copy. |
| 11 | `what_changed_summary.json` | Optional monitoring delta when prior snapshot evidence exists. |
| 12 | `output_manifest.json` | Machine-readable index of generated paths and product-bundle discovery. |

Do not start from root legacy `portfolio_xray.json`, `stress_report.json`, `run_result.json`, or
`portfolio_weights.yml` when interpreting the Core MVP demo. Portfolio-first truth starts in
`analysis_subject/`.

## How to read the result

### Diagnosis

Open `analysis_subject/problem_classification.json` first. The important fields are:

- `primary_diagnosis.diagnosis_id`: the product's current best problem label;
- `primary_diagnosis.key_evidence` or equivalent evidence fields: what supports the diagnosis;
- `next_diagnostic_step`: what should be tested next;
- `why_not_other_problems`: why similar diagnoses were not selected.

### Launchpad and Builder

Open `analysis_subject/candidate_launchpad.json`, then
`analysis_subject/portfolio_alternatives_builder.json`.

Rules to keep visible during the demo:

- Launchpad cards are hypotheses, not instructions to rebalance.
- Builder setup records what would be tested.
- Builder setup does not produce weights.
- `can_generate_candidate: false` is valid when the selected path is monitor-only or blocked by data quality.

### Candidate Generation

Open `candidate_generation.json` only after the vertical command explicitly generated a candidate.
A generated candidate means: "one test portfolio / reference benchmark was created or attempted."
It does **not** mean: "the product recommends this allocation."

### Current vs Candidate

Open `current_vs_candidate.json` to answer what improved and what worsened.

If comparison metrics are unavailable, the correct demo statement is:

> The product completed the diagnosis and candidate attempt, but it does not have enough comparable
> candidate metric evidence to claim improvement or deterioration. The Decision Verdict must not
> force a rebalance.

This can be a valid result. It is not a failure if the artifact says the evidence is insufficient;
it would be a failure only if the product invented trade-offs or recommended action without evidence.

### Decision Verdict

Open `decision_verdict.json` last for the primary answer.

| Verdict type | How to explain it |
| --- | --- |
| `evidence_insufficient` | The system refuses to recommend action because comparison evidence is missing, stale, degraded, or incomplete. This is valid and safer than overclaiming. |
| `no_trade` / keep-current style outcome | The tested candidate did not prove enough benefit, or costs/trade-offs outweigh the improvement. No action can be the correct decision. |
| rebalance / review-action style outcome | Action may be justified only when diagnosis, comparison evidence, success criteria, and trade-offs support it. |
| blocked before candidate generation | The product found a diagnosis or monitoring need, but Builder did not allow a candidate. Explain the block reason instead of forcing a test. |

## Expected behavior for the current three fixtures

As of the Session 09 demo package, the existing checked outputs show this acceptance state:

| Portfolio | Expected current result | Demo interpretation |
| --- | --- | --- |
| Balanced diversified | `mixed_evidence_no_action`; Equal Weight attempt can be generated; Block 8 comparison may be unavailable; verdict may be `evidence_insufficient`. | The system can explain diagnosis and the tested reference hypothesis, but must not claim improvement/worsening without candidate metrics. |
| Equity-heavy / concentrated | Similar to balanced: diagnosis and Equal Weight attempt are visible; comparison metrics may be unavailable; verdict may be `evidence_insufficient`. | The result is honest but not a full trade-off success story unless fresh comparable metrics become available. |
| Defensive / rates-sensitive | `weak_crisis_resilience`; Builder may be `blocked` with `reason: data_quality_blocker`; no candidate/comparison/verdict chain is expected when generation is blocked. | This is a valid blocked-case story: show diagnosis and why no candidate was generated. |

These are not marketing claims. They are the practical state a demo operator should be ready to show
and explain from the JSON files.

## Known limitations to say out loud

- Live FRED/factor data can still be unavailable or slow. Use `scripts/warm_factor_cache.py` to check
  factor cache readiness before a live demo.
- Fast one-candidate mode can produce a valid candidate attempt while comparison metrics remain
  unavailable. In that case, `evidence_insufficient` is the safe verdict.
- The defensive/rates-sensitive fixture can honestly stop at Builder because the selected path is
  monitor-only or data-quality blocked.
- `ai_commentary_context.json` is grounding data for future AI commentary, not final client prose.
- PDFs and polished report exports are not refreshed by the default site/API output profile.

## Quick pre-demo checklist

1. Run `scripts/verify_docs.py` after documentation changes.
2. Confirm `config/demo_portfolios/*.yml` still points to separate `output/demo_portfolios/...` folders.
3. Run the chosen vertical command.
4. Open `analysis_subject/problem_classification.json` before any candidate files.
5. Confirm `candidate_generation.json` is from the same fresh vertical run when present.
6. Read `current_vs_candidate.json` before claiming improvement or deterioration.
7. Read `decision_verdict.json` before saying action is justified.
8. If evidence is insufficient or Builder is blocked, say that plainly and do not force a recommendation.

## Related docs

- [Product Flow Operator Guide](../product_flow_operator_guide.md)
- [Runtime Entrypoints](../runtime_entrypoints.md)
- [Output contracts](../../OUTPUTS.md)
- [Testing strategy](../../TESTING.md)
- [AI Commentary grounding spec](../specs/ai_commentary_grounding_spec.md)
