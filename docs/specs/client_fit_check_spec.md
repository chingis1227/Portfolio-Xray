# Client Fit Check Specification

This document owns the Client Fit V1 product and artifact contract. Client Fit V1 is current,
active, and non-binding diagnostic context. The backend writes the artifact for portfolio-first
diagnosis runs, Block 4 can use it as bounded evidence, the frontend journey shows `/client-fit`
after Stress Lab and before Hypothesis, and downstream Builder, Comparison, Verdict, report, API,
and compact persistence surfaces may consume bounded Client Fit summaries.

## Purpose

Client Fit answers: **Does the diagnosed portfolio fit the client's provided investment profile...**
It compares deterministic Portfolio X-Ray and Stress Lab evidence against the client's stated
return, volatility, maximum drawdown, and horizon inputs. It does not approve suitability, execute
trades, or replace portfolio diagnosis.

Client Fit is inserted after Stress Lab and before Problem Classification:

```text
Portfolio X-Ray
-> Stress Test Lab
-> Client Fit Check
-> Problem Classification
-> Candidate Launchpad
```

## Professional Basis

Client Fit V1 follows common professional portfolio-management framing:

- CFA Institute IPS material describes an investment policy statement as a way to align strategy
  with objectives, risk tolerance, time horizon, and constraints.
- CFA IPS objectives/constraints guidance separates return objectives, risk tolerance, time horizon,
  liquidity, tax, legal/regulatory, and unique circumstances.
- FINRA investor-profile framing includes investment objectives, experience, time horizon,
  liquidity needs, and risk tolerance.
- Vanguard's investor questionnaire uses objectives, experience, time horizon, risk tolerance, and
  financial situation to suggest an allocation.
- Investor.gov explains that longer time horizons can support more volatile investments while
  shorter time horizons may call for less volatility.

Portfolio MRI uses these principles as non-binding decision-support context. It must not use Client
Fit language to claim suitability approval.

## V1 Scope

Client Fit V1 includes:

- target nominal return range
- target volatility range
- target maximum drawdown
- investment horizon
- source and source-quality metadata
- goal-risk conflict detection

Client Fit V1 excludes liquidity. Existing liquidity fields remain legacy/advanced or future
backlog and must not drive V1 Client Fit status, Launchpad logic, comparison, or verdict.

`/client-profile` is an advanced/manual Client Fit editor. It is not the normal onboarding entry
step and must not be documented as a required route before Portfolio Input.

## Status Taxonomy

`client_fit_status` values:

- `fit`: no breach, no conflict, and no material watch item.
- `watch`: one or more mild issues, but no breach or conflict.
- `breach`: volatility is materially above the stated comfort range, historical drawdown is worse
  than the stated limit, or worst stress loss is worse than the stated drawdown limit.
- `conflict`: the stated return objective appears inconsistent with the stated volatility,
  drawdown, or horizon.
- `not_provided`: backend/CLI compatibility state when no Client Fit profile exists.
- `evidence_insufficient`: required portfolio or stress evidence is unavailable.

`diagnostic_quality_status` remains separate:

- `clean`
- `watch`
- `issue`
- `material_issue`
- `evidence_insufficient`

`decision_action` remains downstream Decision Verdict language:

- `keep_current`
- `monitor`
- `review_diversification`
- `test_candidate`
- `revise_objectives`
- `rebalance_review`
- `test_another_candidate`
- `evidence_insufficient`

A Client Fit pass is not sufficient for `keep_current` or no-trade. The Decision Verdict must also
consider diagnostic quality and candidate/comparison evidence.

## Artifact Contract

The artifact path is:

```text
analysis_subject/client_fit_check.json
```

The artifact schema is `client_fit_check_v1`. Minimum fields:

- `schema_version`: fixed value `client_fit_check_v1`
- `client_fit_status`
- `profile`
- `checks`
- `goal_risk_conflict`
- `recommendation_boundary`
- `source_artifacts`
- `warnings`

`profile` carries:

- `preset_id`
- `source`
- `source_quality`
- `source_quality_reason`
- `horizon_years`
- `target_return_range`
- `target_vol_range`
- `target_max_drawdown_pct`

`checks[]` rows carry:

- `dimension`
- `portfolio_value`
- `client_limit` or `client_range`
- `status`
- `interpretation`
- `source_artifact`

## V1 Checks

Client Fit V1 evaluates only:

- `volatility_vs_target`
- `historical_max_drawdown_vs_limit`
- `worst_stress_loss_vs_limit`
- `return_target_gap`
- `horizon_risk_mismatch`
- `goal_risk_conflict`

No liquidity check is allowed in V1.

## Goal-Risk Conflict

Goal-risk conflict is the only new diagnosis family allowed by Client Fit V1. It applies when the
client's stated goals are internally inconsistent, for example:

- target return minimum is growth-level or higher while maximum drawdown tolerance is conservative;
- target return minimum is aggressive while target volatility maximum is balanced or lower;
- horizon is less than three years while the selected profile is growth or aggressive;
- horizon is five years or less while maximum drawdown tolerance is worse than -25%.

Preferred user-facing wording:

```text
The return objective appears inconsistent with the stated drawdown tolerance and horizon.
```

## Product Language Boundary

Allowed:

```text
Based on the provided profile, the portfolio is within the stated drawdown and volatility limits.
```

Forbidden:

```text
This portfolio is suitable for you.
Client suitability approved.
You should buy, sell, or rebalance.
```

Client Fit may say that evidence supports testing a candidate. It must not issue a trade
instruction.

## Downstream Use

Problem Classification uses Client Fit as evidence and context, not as a replacement for X-Ray or
Stress evidence. Block 4 may use dimension-level signals such as
`client_fit_volatility_vs_target`, `client_fit_historical_max_drawdown_vs_limit`, and
`client_fit_worst_stress_loss_vs_limit` as supporting or contrary evidence for existing objective
diagnoses. `client_fit_within_profile` is contrary context, not a reason to suppress a material
structural issue. A generic `breach` status is not a primary diagnosis by itself.

`goal_risk_conflict` is the only Client Fit V1 signal that can become a primary Problem
Classification outcome. It means the stated objectives need review before candidate testing; it is
not a trade instruction and not an optimizer promise. Problem Classification also exposes
`client_fit_status`, `diagnostic_quality_status`, and `client_fit_context` separately so that a
fit/breach result does not overwrite objective diagnostic quality. Candidate Launchpad and Builder
may carry bounded Client Fit context as hypothesis-test criteria. Current vs Candidate may compare
current and candidate portfolios against client targets. Decision Verdict must combine Client Fit
status, diagnostic quality status, and candidate evidence without turning Client Fit into suitability
approval, trade advice, or optimizer constraints.
