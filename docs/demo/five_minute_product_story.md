# Five-Minute Product Story

## One-sentence version

Portfolio MRI helps the user move from portfolio confusion to a defensible investment decision:
Diagnosis -> Hypothesis -> Candidate -> Comparison -> Verdict.

## The problem

Many portfolio tools start by proposing an allocation. That is risky because the user may not yet
know what problem the current portfolio has. Is the issue concentration, stress behavior, weak
hedging, poor risk contribution, or simply mixed evidence where no action is justified?

Portfolio MRI starts before the action step. It asks: what is the current portfolio actually
showing, and is there enough evidence to justify testing a change?

## What Portfolio MRI does

Portfolio MRI diagnoses the current portfolio first. It reads the portfolio, builds Portfolio
X-Ray evidence, runs stress evidence, classifies the main problem, and then creates candidate
hypotheses only after the problem is visible.

If a hypothesis is worth testing, the product generates one candidate attempt, compares it against
the current portfolio, and writes a Decision Verdict. The verdict can support review, no-trade,
keep-current, test-another-candidate, or evidence-insufficient outcomes.

## The workflow

```text
Input portfolio
-> Portfolio X-Ray
-> Stress Test Lab
-> Problem Classification
-> Candidate Launchpad
-> Portfolio Alternatives Builder
-> Candidate Generation
-> Current vs Candidate Comparison
-> Decision Verdict
-> AI Commentary grounding
```

In a five-minute demo, show one portfolio, one diagnosis, one tested hypothesis, one candidate, one
comparison, and one verdict.

## What makes it different

The product is not optimizer-first. A candidate does not appear before the current portfolio is
diagnosed. A reference benchmark is not treated as a recommendation. A verdict is not allowed to
hide trade-offs or become a standalone trading instruction.

The important difference is discipline: the system separates diagnosis, hypothesis, candidate
generation, trade-off comparison, and decision-support verdict.

## What the demo shows

The demo shows a working CLI/file-driven Core MVP loop. A new operator can run the vertical-flow
command, then open the JSON files in order:

1. `analysis_subject/problem_classification.json` for the diagnosis;
2. `analysis_subject/candidate_launchpad.json` for the hypothesis cards;
3. `analysis_subject/portfolio_alternatives_builder.json` for the selected setup;
4. `candidate_generation.json` for the generated candidate attempt;
5. `current_vs_candidate.json` for improvements and worsened trade-offs;
6. `decision_verdict.json` for the action / no-action decision-support output;
7. `ai_commentary_context.json` for explanation grounding.

## What the demo does not claim

The demo does not claim to be a full trading platform, a UI product, a polished PDF report, or a
personal investment recommendation. It does not claim Equal Weight is the best portfolio. It does
not claim that `rebalance_to_selected_candidate` is a buy/sell order.

The correct claim is narrower: the MVP can diagnose a current portfolio, test one candidate
hypothesis, compare trade-offs, and produce a bounded decision-support verdict.

## Final takeaway

Portfolio MRI is useful because it turns a vague portfolio question into a structured decision:

```text
What is wrong or uncertain?
What hypothesis should we test?
What candidate represents that hypothesis?
What improved and what worsened?
Is action justified, or should we keep current / no-trade / seek more evidence?
```

That is the product's current demo value.
