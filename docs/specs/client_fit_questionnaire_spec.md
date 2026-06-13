# Client Fit Questionnaire Specification

Status: current Client Fit V1 questionnaire and web-placement contract.

This document owns the compact planning-profile questionnaire used by the web journey before Portfolio Input. Client Fit is diagnostic context only. It is not legal suitability approval, a trade instruction, or an optimizer mandate.

## Current web placement

Canonical web path:

```text
/
-> /onboarding/sign-in
-> /onboarding/name
-> /onboarding/investor-type
-> /onboarding/loading
-> /portfolio-input
```

Local preview shortcut:

```text
/onboarding/name?dev_bypass=1
```

The shortcut is allowed only while local email sign-in is unavailable or unstable. It is not the product path.

`/client-profile` remains an advanced/manual Client Fit editor for changing the saved context. The normal user journey collects the profile through onboarding and enters Portfolio Input with Client Fit context already saved.

## Current five-question intake

The implemented onboarding screen asks one question at a time:

1. `What is the portfolio's primary job?`
   - Preserve capital first.
   - Balance growth and resilience.
   - Grow over a full cycle.
   - Understand what I already own.

2. `What is the real decision horizon?`
   - Shorter horizon.
   - Medium horizon.
   - Longer horizon.

3. `How much temporary loss can the plan tolerate?`
   - Small temporary losses.
   - Moderate drawdowns.
   - Larger drawdowns.

4. `How should the system treat changes?`
   - Be conservative about change.
   - Test changes when evidence is clear.
   - Look actively for improvements.

5. `What worries you most about the current portfolio?`
   - Hidden concentration.
   - Loss in a stress event.
   - Rates and bond sensitivity.
   - Inflation / real asset protection.
   - I am not sure yet.

## Profile mapping

The frontend stores onboarding state and maps it to the existing `ClientFitInput` shape through `frontend/lib/onboarding.ts`. The saved profile provides bounded display/test context for:

- target return range;
- volatility comfort range;
- maximum temporary-loss limit;
- horizon;
- profile label and confidence/source-quality display.

The mapping must remain conservative and explanatory. Client Fit targets may inform display and hypothesis-test criteria, but they must not become optimizer constraints or suitability approval.

## Required UI behavior

- Portfolio Input must show the saved Client Fit profile summary before diagnosis.
- Run diagnosis must remain blocked until a valid Client Fit profile exists in the normal web journey.
- The manual `/client-profile` editor may update the same bounded profile context.
- Backend/CLI compatibility may still produce a `not_provided` Client Fit state when no profile exists.

## Copy boundaries

Allowed language:

- planning profile;
- diagnostic context;
- target range;
- comfort range;
- temporary-loss limit;
- non-binding Client Fit check.

Forbidden language:

- suitability approved;
- recommendation;
- mandate;
- trade instruction;
- guaranteed fit;
- no action needed solely because Client Fit is acceptable.

## Documentation sync

When onboarding questions, answer options, profile mapping, or Client Fit placement change, update this document, `docs/design/current_website_structure.md`, `frontend/README.md`, `docs/contracts/SCREEN_CONTRACTS.md`, and `docs/specs/frontend_screen_contracts.md` in the same change.
