# Client Fit Questionnaire Specification

This document owns the planned Client Fit V1 questionnaire, preset, and source-quality contract. It
is documentation-only until the implementation sessions add configuration, validators, API fields,
frontend routes, and persistence.

## Purpose

The Client Fit Questionnaire gathers a compact investment profile before the web user runs a
portfolio diagnosis. The goal is not to provide legal suitability approval. The goal is to give
Portfolio MRI enough stated objectives to interpret portfolio risk against the user's return,
volatility, drawdown, and horizon preferences.

## Web Placement

The primary web journey must ask for Client Fit after sign-in/onboarding and before portfolio
diagnosis:

```text
/client-profile
-> /portfolio-input
```

The primary UI copy should say:

```text
Tell us your investment profile
Quick profile — about 2 minutes
```

The web flow requires a valid Client Fit profile before "Run diagnosis". Backend/CLI paths remain
compatible when the profile is missing.

## Questions

Client Fit V1 uses eight questions:

1. Main objective
   - Preserve capital
   - Moderate growth
   - Balanced growth and risk
   - High growth
   - Maximum growth

2. Target annual return expectation
   - 2-4%
   - 3-6%
   - 5-7%
   - 7-10%
   - 10%+

3. Investment horizon
   - Less than 3 years
   - 3-5 years
   - 6-10 years
   - More than 10 years

4. Maximum temporary portfolio loss the user can accept
   - Up to -10%
   - Up to -15%
   - Up to -20%
   - Up to -30%
   - More than -30%

5. Reaction to a -20% decline
   - Sell most or reduce risk strongly
   - Reduce some risk
   - Hold
   - Add more

6. Comfortable normal yearly fluctuation
   - Very low: 0-5%
   - Low/moderate: 5-8%
   - Moderate: 8-12%
   - High: 12-18%
   - Very high: 18%+

7. Investment experience
   - Beginner
   - Some experience
   - Experienced
   - Professional / advanced

8. Profile confirmation
   - Use suggested profile
   - Choose a different preset
   - Customize targets manually

No liquidity question is included in V1.

## Presets

Reuse existing legacy profile ranges as Client Fit presets while preserving legacy optimizer
compatibility:

- `ultra_conservative`: return 2-4%, volatility 2-5%, target maximum drawdown -10%.
- `conservative`: return 3-6%, volatility 4-7%, target maximum drawdown -15%.
- `balanced`: return 5-7%, volatility 7-10%, target maximum drawdown -20%.
- `growth`: return 7-10%, volatility 10-14%, target maximum drawdown -27.5%.
- `aggressive`: return 10-20%, volatility 14-20%, target maximum drawdown -35%.

Presets are starting points, not advice. A user may confirm the suggested preset, choose a different
preset, or customize targets manually.

## Source and Source Quality

Every Client Fit profile must carry:

- `source`: `questionnaire`, `preset_override`, `manual_override`, `imported`, or `missing`
- `source_quality`: `high`, `medium`, `low`, or `missing`
- `source_quality_reason`: a short readable explanation

Defaults:

- questionnaire plus user confirmation: `medium`
- full manual override: `high`
- preset only: `medium`
- missing profile: `missing`

The UI should expose source quality in plain language, for example:

```text
Profile confidence: Medium — based on a short questionnaire and user confirmation.
```

## Compatibility Boundary

The web journey requires Client Fit, but backend/CLI diagnosis must not fail only because no profile
was provided. Missing profile creates `client_fit_status = not_provided` and downstream copy should
explain that only generic portfolio diagnosis is available.

## Product Copy Boundary

Allowed:

```text
This profile helps compare portfolio risk with your stated comfort range.
```

Forbidden:

```text
This questionnaire approves the portfolio as suitable.
```
