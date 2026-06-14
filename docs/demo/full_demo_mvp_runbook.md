# Full Demo MVP Runbook

This runbook explains how to show the current Portfolio MRI Core MVP without
oral hand-holding from the developer. It is practical on purpose: run one command, open the output
files in order, and explain only what the files support.

Portfolio MRI is a diagnosis-first, current-portfolio-first decision-support system. It starts with
the user's current portfolio, diagnoses the main issue, tests one candidate hypothesis when useful,
compares trade-offs, and produces a Decision Verdict.

Core product path:

```text
Input portfolio
-> Portfolio Diagnosis
-> Stress Test Lab
-> Problem Classification
-> Candidate Launchpad
-> Portfolio Alternatives Builder
-> Candidate Generation
-> Current vs Candidate Comparison
-> Decision Verdict
-> AI Commentary grounding
```

## What this demo proves

The demo proves that the current MVP can run a complete file-driven product loop:

- read a demo portfolio config;
- materialize the diagnosed `analysis_subject`;
- produce Portfolio Diagnosis and Stress Test Lab evidence;
- classify the main problem;
- create Launchpad hypotheses;
- create one Builder setup;
- generate one candidate attempt;
- compare the current portfolio with the selected candidate;
- write a Decision Verdict;
- write `ai_commentary_context.json` as deterministic grounding for an explanation.

The demo also proves that the system keeps the key safety boundary visible:

- `candidate_generation.json` = a candidate created as an investment hypothesis;
- `current_vs_candidate.json` = trade-off comparison;
- `decision_verdict.json` = action / no-action decision-support;
- `ai_commentary_context.json` = grounding for explanation, not LLM magic.

## What this demo does not prove

The demo does not prove that the product is a trading system, a full optimizer cockpit, a polished
PDF report product, or a multi-client UI.

It does not claim:

- the reference benchmark is a recommendation;
- Equal Weight is the right answer for every user;
- a generated candidate is the "best portfolio";
- `rebalance_to_selected_candidate` is a personal trading instruction;
- AI Commentary is making unsupported judgment calls.

The product verdict is decision-support based on the tested scenario and available data. It is not
a standalone trading instruction.

## Demo portfolios

Demo configs live in `config/demo_portfolios/`.

| Portfolio | Config | Output folder | Useful demo angle |
| --- | --- | --- | --- |
| Balanced | `config/demo_portfolios/balanced.yml` | `output/demo_portfolios/balanced/final/` | Mixed evidence and a reference comparison test. |
| Equity-heavy | `config/demo_portfolios/equity_heavy.yml` | `output/demo_portfolios/equity_heavy/final/` | Concentration / equity-heavy evidence with a reference comparison test. |
| Defensive / rates-sensitive | `config/demo_portfolios/defensive_rates_sensitive.yml` | `output/demo_portfolios/defensive_rates_sensitive/final/` | Clear stress / crisis-resilience diagnosis, one Equal Weight candidate, visible improvements and trade-offs. |

For a first walkthrough, use `defensive_rates_sensitive` because its diagnosis and comparison are
the easiest to explain from the current checked demo outputs.

## Before running

From the repository root, make sure the virtual environment exists and dependencies are installed:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

If `.venv` already exists, just use:

```powershell
.\.venv\Scripts\python.exe --version
```

The command below writes JSON outputs under the configured `output_dir_final`. It does not build a
new UI and does not refresh a polished PDF report.

## Command

Canonical one-hypothesis demo command:

```powershell
.\.venv\Scripts\python.exe scripts\run_blocks_5_to_9_vertical_flow.py --config config\demo_portfolios\defensive_rates_sensitive.yml --method equal_weight --factory-execution-mode standard --force-candidate
```

Same command for the other demo portfolios:

```powershell
.\.venv\Scripts\python.exe scripts\run_blocks_5_to_9_vertical_flow.py --config config\demo_portfolios\balanced.yml --method equal_weight --factory-execution-mode standard --force-candidate
.\.venv\Scripts\python.exe scripts\run_blocks_5_to_9_vertical_flow.py --config config\demo_portfolios\equity_heavy.yml --method equal_weight --factory-execution-mode standard --force-candidate
```

Use `--help` to confirm the available flags:

```powershell
.\.venv\Scripts\python.exe scripts\run_blocks_5_to_9_vertical_flow.py --help
```

## Expected output files

Read outputs from the portfolio's `output_dir_final`, not from legacy root artifacts.

For the defensive demo portfolio, the folder is:

```text
output/demo_portfolios/defensive_rates_sensitive/final/
```

Read these files in order:

| Step | File | Why it matters |
| --- | --- | --- |
| 1 | `analysis_subject/run_metadata.json` | Confirms the current portfolio, weights, currency, analysis window, and that the subject is diagnostic current-portfolio evidence. |
| 2 | `analysis_subject/portfolio_xray.json` | Current Portfolio Diagnosis evidence. |
| 3 | `analysis_subject/stress_report.json` | Stress Test Lab evidence and hedge-gap context. |
| 4 | `analysis_subject/problem_classification.json` | Primary diagnosis, evidence, and next diagnostic step. |
| 5 | `analysis_subject/candidate_launchpad.json` | Hypothesis cards; these are tests to consider, not rebalance instructions. |
| 6 | `analysis_subject/portfolio_alternatives_builder.json` | Builder setup for one selected card; setup only, not a candidate yet. |
| 7 | `candidate_generation.json` | One explicit candidate attempt generated as a hypothesis. |
| 8 | `current_vs_candidate.json` | Trade-off comparison: what improved, what worsened, and what is unavailable. |
| 9 | `decision_verdict.json` | Decision-support verdict: action review, no-action, no-trade, or evidence-insufficient. |
| 10 | `ai_commentary_context.json` | Grounding for an explanation; deterministic context, not an LLM conclusion. |

Optional monitoring / "what changed" files may be absent in the demo outputs. If absent, say that
monitoring context was not provided instead of inventing a monitoring trigger.

## How to read the result

1. Start with `analysis_subject/run_metadata.json`.
   - Check `analysis_setup.analysis_subject.type`.
   - Check `analysis_setup.analysis_subject.weights`.
   - Meaning: this is the current portfolio being diagnosed, not a proposed allocation.

2. Open `analysis_subject/problem_classification.json`.
   - Check `primary_diagnosis.diagnosis_id`.
   - Check `primary_diagnosis.thesis_en`.
   - Check `key_evidence`.
   - Check `next_diagnostic_step`.
   - Meaning: this is the main diagnosed issue and the next test the product wants to run.

3. Open `analysis_subject/candidate_launchpad.json`.
   - Check `launchpad_outcome`.
   - Check `cards[]`.
   - Meaning: these are possible hypothesis tests. They are not recommendations.

4. Open `analysis_subject/portfolio_alternatives_builder.json`.
   - Check `status`.
   - Check `can_generate_candidate`.
   - Check `candidate_setup`.
   - Meaning: the Builder prepared one test setup. It still has not decided to trade.

5. Open `candidate_generation.json`.
   - Check `generation_status`.
   - Check `candidate.candidate_id`.
   - Check `candidate.weights`.
   - Check `candidate.is_rebalance_recommendation`.
   - Meaning: a candidate was generated as a tested hypothesis, not as the final answer.

6. Open `current_vs_candidate.json`.
   - Check `comparison_status`.
   - Check `comparisons[].what_improved`.
   - Check `comparisons[].what_worsened`.
   - Check `comparisons[].materiality_for_decision_review`.
   - Meaning: this is the trade-off evidence. Do not claim improvement if the field is missing.

7. Open `decision_verdict.json`.
   - Check `verdict_id`.
   - Check `verdict_label`.
   - Check `recommended_action`.
   - Check `rationale_summary`.
   - Check `guardrails`.
   - Meaning: this is the decision-support layer. It can support review, no-trade, keep-current, or
     evidence-insufficient outcomes.

8. Open `ai_commentary_context.json`.
   - Check `purpose`.
   - Check `client_explanation_draft.sentences`.
   - Check `required_grounding_rules`.
   - Meaning: this file tells future commentary what it may cite. It is not free-form AI advice.

## Verdict meanings

| Verdict style | Plain meaning | How to say it safely |
| --- | --- | --- |
| `rebalance_to_selected_candidate` | The tested candidate has enough material evidence to review as a possible action. | "The candidate is material enough for review; confirm trade-offs before implementation." |
| `no_trade` / keep-current | The candidate did not justify action, or trade-offs / costs are too high. | "No action is currently justified by this evidence." |
| `test_another_candidate` | The tested hypothesis did not answer the problem well enough. | "Try another hypothesis before deciding." |
| `evidence_insufficient` | Comparison evidence is missing, stale, degraded, or incomplete. | "The product refuses to force an action because evidence is not enough." |
| Builder blocked | A candidate was not generated because setup or data quality blocked it. | "The correct result is to explain the block, not to force a portfolio." |

## Common limitations

- The demo is CLI/file-driven.
- It uses JSON outputs as the product evidence.
- It does not build a UI.
- It does not build a polished PDF report.
- Monitoring files may be absent when there is no prior snapshot.
- Turnover and estimated cost can be unavailable when baseline or candidate weight evidence is
  insufficient for that calculation.
- Reference benchmarks such as Equal Weight are diagnostic comparison tools, not recommendations.
- The Decision Verdict is only as strong as the current diagnosis, candidate generation, comparison
  evidence, and stated limitations.

## Demo safety boundaries

Use these phrases consistently:

- "Candidate" means a tested investment hypothesis, not a recommendation.
- "Reference benchmark" means a comparison point, not a recommended portfolio.
- "Current vs Candidate" means trade-off evidence, not an instruction to trade.
- "Decision Verdict" means decision-support, not a standalone trading instruction.
- "`rebalance_to_selected_candidate` means review this candidate with the documented trade-offs; it
  is not a personal buy/sell order."
- "`ai_commentary_context.json` is grounding for explanation, not LLM magic."
