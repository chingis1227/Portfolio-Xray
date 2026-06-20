# Portfolio MRI

Portfolio MRI is a diagnosis-first, current-portfolio-first investment decision-support product.

## Product In One Minute

Portfolio MRI helps an advisor or sophisticated investor review the portfolio they already own
before deciding whether any change is worth testing.

The core problem it solves is not "find the mathematically optimal portfolio." The core problem is:
current portfolios often contain hidden concentration, fragile stress behavior, unclear fit with the
client context, and confusing trade-offs. Portfolio MRI turns that evidence into a structured
diagnosis and one explicit candidate test when a test is justified.

It helps the user answer:

- What risks are hidden in the portfolio I already own?
- How would this portfolio behave under stress?
- Does the evidence fit the provided client context?
- What problem, if any, is worth testing?
- If I test one candidate portfolio, do the trade-offs justify rebalance review, no action, another test, or an evidence-insufficient verdict?

Portfolio MRI is not a black-box optimizer, trading system, suitability approval engine, tax advisor, or polished PDF factory.

## Product Flow

The current product truth is:

```text
Input Portfolio
-> Portfolio Diagnosis
-> Stress Test Lab
-> Client Fit Check
-> Problem Classification
-> Candidate Launchpad
-> Portfolio Alternatives Builder
-> Candidate Generation
-> Current vs Candidate Comparison
-> Decision Verdict
-> AI Commentary / grounding
-> Monitoring / What Changed
```

The product starts with the current portfolio, not with an optimizer menu. Candidate portfolios are hypotheses to test, not recommendations or trade instructions. A valid answer can be "keep current", "no material rebalance", "test another candidate", or "evidence insufficient".

## What It Can Do Today

Current product-facing capabilities:

- Accept a current portfolio with instruments, weights, and investor currency.
- Diagnose the current portfolio before considering alternatives.
- Surface allocation, concentration, hidden exposure, risk/return behavior, weakness, and data-quality signals.
- Run Stress Test Lab evidence and explain where the portfolio can break.
- Use Client Fit V1 as non-binding diagnostic context, not as suitability approval.
- Classify the main portfolio problem and show reasonable hypotheses to test.
- Prepare and generate one selected candidate test when explicitly requested.
- Compare the current portfolio with the selected candidate by improvements, worsened areas, trade-offs, and unavailable evidence.
- Produce a non-binding Decision Verdict.
- Provide grounded AI Commentary context and a light What Changed summary.

Advanced optimizer batches, scorecards, full candidate arenas, legacy reports, and PDF-style artifacts may exist in code or generated output, but they are support/advanced/legacy capabilities unless a current spec promotes them into the Core MVP flow.

## Product Principles

- Diagnosis before action.
- Current portfolio first.
- Problems before methods.
- Candidate equals hypothesis, not recommendation.
- No-trade is a valid outcome.
- Missing or partial evidence must be disclosed, not hidden.
- AI explains grounded evidence; code and specs own calculations.
- Client Fit is context only and must not override material portfolio issues.

## Quick Local Commands

Install dependencies:

```bash
pip install -r requirements.txt
```

Run tests:

```bash
python -m pytest
```

Run the default portfolio-first diagnosis:

```bash
python run_portfolio_review.py
```

Run core diagnostics only:

```bash
python run_core_diagnostics.py
```

Run the canonical one-candidate vertical demo:

```bash
python scripts/run_blocks_5_to_9_vertical_flow.py --method equal_weight
```

For the full runtime command map, use [docs/runtime_entrypoints.md](docs/runtime_entrypoints.md) and [OUTPUTS.md](OUTPUTS.md).

## Documentation Map

Start with [docs/README.md](docs/README.md) for the maintained documentation index,
current-vs-historical boundaries, and update guidance.

Core source-of-truth entry points:

- [PRODUCT.md](PRODUCT.md) - product direction, Core MVP boundaries, and non-goals.
- [SPEC.md](SPEC.md) - current implementation contract and detailed spec index.
- [docs/contracts/](docs/contracts/) - product, screen, staged-review, artifact, copy, doc-sync,
  and QA contracts.
- [docs/specs/README.md](docs/specs/README.md) - detailed module specs.
- [DATA.md](DATA.md), [OUTPUTS.md](OUTPUTS.md), [TESTING.md](TESTING.md), and
  [WORKFLOW.md](WORKFLOW.md) - data, generated outputs, verification, and workflow.

## README Maintenance Rule

Keep this README short, product-facing, and easy to maintain. Do not duplicate formulas, schemas, long command matrices, implementation details, or historical plans here. Link to the owning source-of-truth document instead.
