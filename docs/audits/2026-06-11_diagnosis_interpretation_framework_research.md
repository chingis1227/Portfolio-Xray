# Diagnosis Interpretation Framework Research

Date: 2026-06-11

Status: **Session 01 research and design baseline**. This is a documentation/audit artifact for
Portfolio MRI. It does not change calculations, thresholds, FastAPI runtime, frontend behavior,
dependencies, generated outputs, or `config.yml`.

## User question in plain language

The question is not "how do we calculate volatility, drawdown, beta, or stress loss?" The question is:

> After Portfolio X-Ray and Stress Test Lab calculate many metrics, what professional process turns
> those metrics into a clear diagnosis, a root cause, and a suggested next test without hallucinating
> or pretending to give trade advice?

The short answer is: the product needs an explicit **evidence-to-diagnosis framework**. Metrics should
not speak directly to the user. Each metric should first become a bounded evidence signal; related
signals should then be grouped into a problem family; the system should pick root causes before
symptoms; and every diagnosis should carry its evidence, confidence, materiality, actionability,
contrary evidence, and next diagnostic test.

## What the current project already does

The current project already has the right high-level direction:

    Input portfolio
    -> Portfolio X-Ray
    -> Stress Test Lab
    -> Problem Classification
    -> Candidate Launchpad
    -> Builder setup
    -> one explicit candidate test
    -> current-vs-candidate comparison
    -> Decision Verdict
    -> grounded explanation

The important current implementation pieces are:

- `docs/specs/block_4_diagnosis_v3_spec.md` says Block 4 is an investment diagnosis handoff, not a
  scoring dashboard. It requires `primary_diagnosis`, `root_cause`, `supporting_symptoms`,
  `key_evidence`, `why_this_matters`, `confidence`, `materiality`, `actionability`,
  `suggested_hypothesis`, `next_diagnostic_step`, and `success_criteria`.
- `src/block_4/problem_taxonomy.py` is the controlled taxonomy of problem ids, action paths,
  required evidence signals, supporting evidence signals, negative evidence signals, and method
  suggestions. This is the closest current code asset to the desired professional framework.
- `src/block_4/evidence_extraction.py`, `problem_scoring.py`, `problem_prioritization.py`,
  `severity_confidence.py`, `action_path_mapping.py`, and `diagnosis_builder.py` implement the
  current deterministic bridge from X-Ray/Stress evidence into diagnosis and Launchpad.
- `docs/contracts/ARTIFACT_TO_SCREEN_MAP.md` and `SCREEN_CONTRACTS.md` already say that frontend
  screens should show product meaning, not raw artifacts or backend ids.

What still needs strengthening is the governance around **why** a metric creates a diagnosis, when it
is only a symptom, when evidence is too weak, and how suggested actions stay tied to explicit success
criteria.

## Professional sources reviewed

The following open sources are useful because they support pieces of the framework, not because any
one vendor gives us a complete copyable system.

1. Morningstar Portfolio X-Ray help and report materials describe portfolio look-through as a way to
   inspect holdings from multiple angles: asset allocation, style, region, sector, and overlap. This
   supports Portfolio MRI's idea that X-Ray should answer "what do I really own?" before any
   optimization step. Sources: `https://www.morningstar.com/help-center/portfolio/xray`,
   `https://workstation.morningstar.com/support/article/bltb6b826111507c791/UnderstandingtheclassicPortfolioX-RayReport`,
   and Morningstar Portfolio X-Ray report examples.

2. Morningstar Global Risk Model materials describe comparing portfolios and benchmarks on a
   standardized basis, running what-if/scenario analysis, and measuring exposures to many factors.
   This supports the idea that factor exposure should explain hidden drivers and scenario sensitivity,
   not just produce a generic risk number. Sources:
   `https://morningstardirect.morningstar.com/clientcomm/RiskModel.pdf` and
   `https://morningstardirect.morningstar.com/clientcomm/RiskModelMethodology.pdf`.

3. BlackRock Aladdin Risk materials describe a whole-portfolio view where users decompose risk by
   portfolio, factor, sector, or security and build stress tests, what-if analyses, and optimization
   analyses. This supports a layered workflow: know what you own, identify risk/opportunity, test
   scenarios, then consider portfolio construction. Sources:
   `https://www.blackrock.com/aladdin/products/aladdin-risk`,
   `https://www.blackrock.com/aladdin/products/aladdin-wealth/insights/risk-layers`, and
   `https://www.blackrock.com/aladdin/products/aladdin-wealth/insights/power-of-stress-testing`.

4. CFA Institute performance evaluation and attribution material stresses that attribution should
   identify sources of return/risk and reflect the investment decision process. This supports keeping
   diagnosis tied to decision logic rather than disconnected metric dashboards. Sources:
   `https://rpc.cfainstitute.org/topics/performance-attribution` and
   `https://www.cfainstitute.org/insights/professional-learning/refresher-readings/2026/portfolio-performance-evaluation`.

5. CFA Institute market-risk material frames risk management as identifying and measuring risk and
   making sure the risks taken are consistent with desired risks. This supports separating measurement
   from judgment: a metric is not automatically a problem unless it is inconsistent with the
   portfolio's objective, risk appetite, or decision context. Source:
   `https://www.cfainstitute.org/insights/professional-learning/refresher-readings/2026/measuring-managing-market-risk`.

6. MSCI materials on multi-asset factor attribution and risk attribution emphasize linking risk and
   return to common drivers and matching factor granularity to the reporting audience. This supports
   the Portfolio MRI principle that the user-facing diagnosis should not expose every raw factor if a
   higher-level root cause explains the decision better.

7. The MSCI Barra paper "Stress Testing in the Investment Process" is directly relevant because it
   explains why stress tests are useful: they connect potential loss to a named event, which is often
   more meaningful to portfolio managers than a single distribution statistic. This supports Stress
   Lab as a confirmation layer for X-Ray weaknesses. Source:
   `https://papers.ssrn.com/sol3/Delivery.cfm/SSRN_ID1708243_code1141713.pdf?abstractid=1708243&mirid=1`.

8. AQR's practical guide to measuring factor exposures supports the idea that regression/factor
   analysis helps investors understand what risks are actually present in the portfolio. This is useful
   for hidden exposure and factor-sensitivity diagnosis, but it also reinforces the need for model
   limitations and confidence flags. Source:
   `https://www.aqr.com/-/media/AQR/Documents/Insights/Trade-Publications/Measuring-Portfolio-Factor-Exposures-A-Practical-Guide.pdf`.

9. Vanguard portfolio-construction materials emphasize beginning with broad asset allocation and
   diversification before specific funds or advanced optimization. This supports Portfolio MRI's
   product boundary: diagnose current allocation and diversification first; do not start with Max
   Sharpe or optimizer output. Sources:
   `https://www.vanguardmexico.com/content/dam/intl/americas/documents/mexico/en/mx-en-pf-vanguards-framework-for-constructing-globally-diversified-portfolios.pdf`
   and `https://www.vanguard.co.uk/professional/vanguard-365/investment-knowledge/portfolio-construction/portfolio-construction-framework`.

10. FactSet and Axioma public materials describe portfolio analytics as combining exposures,
    benchmark-relative metrics, risk decomposition, factor analysis, stress testing, and historical
    tracking. This supports a production architecture where the API returns typed, comparable,
    auditable evidence instead of unstructured prose. Sources:
    `https://www.factset.com/solutions/portfolio-analytics`,
    `https://insight.factset.com/hubfs/Resources%20Section/Brochures/portfolio-analysis-brochure.pdf`,
    and `https://www.simcorp.com/solutions/axioma-solutions/axioma-risk`.

## Practical synthesis for Portfolio MRI

A professional diagnosis framework should have six layers.

### Layer 1. Raw metric

Examples: top holding weight, top-3 weight, annual volatility, max drawdown, beta, correlation,
contribution to risk, worst stress loss, offset coverage, rate sensitivity, credit sensitivity,
liquidity warning.

Rule: raw metrics are facts, not diagnoses. The user should rarely see a long raw metric list as the
main answer.

### Layer 2. Evidence signal

A metric becomes an evidence signal only after the system knows:

- source artifact and field;
- calculation window;
- data quality;
- threshold or comparison basis;
- direction of concern;
- magnitude band;
- whether the signal is confirmed, partial, or weak.

Example:

    Metric: top-3 holdings = 72% of capital.
    Evidence signal: high capital concentration, high confidence, source Block 2.1.

### Layer 3. Problem family

Signals should map into controlled problem families, not free-form AI labels. Current project problem
families already include concentration, poor diversification, weak crisis resilience, weak hedge
behavior, duration/rates vulnerability, credit/liquidity fragility, high volatility, high drawdown,
high equity beta, high tail risk, low return/risk efficiency, mixed evidence, acceptable portfolio,
and evidence-insufficient data quality.

Rule: if a problem id is not in the controlled taxonomy, the system should not invent it in
user-facing output.

### Layer 4. Root cause versus symptom

This is the most important professional improvement. Many metrics are symptoms. The diagnosis should
prefer the root cause that explains the symptoms.

Examples:

- high volatility may be a symptom of equity concentration;
- high drawdown may be a symptom of weak crisis resilience;
- high equity beta may be a symptom of hidden equity exposure;
- poor stress behavior may be caused by weak hedge behavior or duration/rates vulnerability;
- low Sharpe can be an outcome of concentration, high volatility, or poor diversification, not always
  a standalone reason to optimize.

The product should show one primary diagnosis, at most two supporting symptoms, and why other possible
problems were not selected.

### Layer 5. Action path / hypothesis to test

A diagnosis should not jump directly to "rebalance". It should produce a testable hypothesis:

- high concentration -> test whether a simpler equal-weight or max-diversification candidate reduces
  concentration without unacceptable trade-offs;
- weak crisis resilience -> test whether a downside-risk or diversification candidate improves worst
  stress loss and offset coverage;
- weak hedge behavior -> test whether the candidate improves protection in the named risk type;
- duration/rates vulnerability -> test whether rates loss and rates beta can be reduced;
- mixed evidence / acceptable portfolio -> use reference comparison or monitor, not forced action;
- data-quality blocker -> improve data first, do not generate unreliable candidates.

This exactly matches the current product principle: Candidate Launchpad cards are tests, not
recommendations.

### Layer 6. Success criteria and verdict

Every suggested test needs success criteria before the candidate is generated. Otherwise the system can
always rationalize the result after the fact.

Examples:

- lower worst stress loss;
- lower top-3 risk contribution;
- reduce correlation concentration;
- improve offset coverage;
- reduce rates shock loss;
- avoid materially worse return/risk efficiency;
- avoid excessive turnover/cost.

Only after Current vs Candidate Comparison should the system say: keep current, no-trade, test
another, evidence insufficient, or rebalance review. The verdict should be non-binding decision
support.

## Proposed engineering model

The robust future foundation should be a versioned **Diagnosis Rule Registry**. It should be
data-like, reviewable, and tested, not scattered across UI text or ad hoc AI prompts.

Each rule should look conceptually like this:

    problem_id: high_concentration
    role: root_cause
    required_signals:
      - top1_weight_pct or top3_weight_pct
    supporting_signals:
      - top1_risk_contribution
      - top3_risk_contribution
      - duplicate_exposure
    contrary_signals:
      - broad_equal_weights
      - low risk concentration despite capital concentration
    activation:
      materiality threshold + data quality + confidence logic
    narrative:
      why this matters in plain language
    suggested_tests:
      - equal_weight reference test
      - risk_parity risk-distribution test
      - maximum_diversification targeted test
    success_criteria:
      - lower top-3 risk contribution
      - lower concentration score
      - avoid worse stress loss

This can later live as Python dataclasses or YAML/JSON loaded into Python, but it should be validated
by tests. The important point is governance: every user-facing diagnosis should be traceable to a
rule, evidence signals, and source artifacts.

## Recommended project improvements after Session 01

1. **Add a formal diagnosis-rule registry spec.** The project already has `problem_taxonomy.py`, but
   a dedicated spec should define the stable rule contract: problem id, role, evidence signals,
   thresholds, contrary evidence, confidence, materiality, action path, success criteria, and
   narrative templates.

2. **Separate evidence extraction from diagnosis selection even more clearly.** Evidence extraction
   should only say what signals exist. Prioritization should decide what matters. Narrative should
   explain why.

3. **Add contrary-evidence support as a first-class field.** Professional diagnosis is more credible
   when it says why it did not choose another diagnosis.

4. **Make every diagnosis auditable.** The public API should expose compact evidence references;
   debug/internal output can expose full rule matches and scoring rows.

5. **Use confidence as evidence quality, not marketing tone.** High confidence should mean enough
   clean data and confirming signals, not simply a severe problem.

6. **Keep suggested actions as tests.** Suggested action should mean "test this hypothesis," not
   "do this trade." The current product boundary is correct and should be preserved.

7. **Make language templates deterministic before LLM use.** Future AI Commentary should consume a
   grounding package with allowed claims, evidence refs, unsupported sections, and forbidden wording.
   It should not invent diagnoses or tests.

8. **Add a diagnosis matrix test suite.** For each problem family, keep fixtures that prove:
   triggering signals activate the problem, weak/missing data blocks it, contrary evidence lowers
   confidence, root causes outrank symptoms, and success criteria match the suggested test.

## Simple explanation for a non-technical user

Think of the system like a doctor:

1. X-Ray and Stress Lab are the scans and blood tests.
2. Problem Classification is the doctor reading the evidence.
3. A metric by itself is not a diagnosis. High volatility is like a fever: it tells us something is
   wrong, but not why.
4. The framework should ask: what is the underlying cause? Concentration? Weak hedge behavior? Rates
   sensitivity? Bad data?
5. Then it should say: what test would confirm whether fixing that cause helps?
6. Only after testing a candidate should the system give a verdict: keep current, no-trade, test
   another idea, evidence insufficient, or consider a rebalance review.

That is the professional foundation: evidence first, diagnosis second, hypothesis third, verdict last.
