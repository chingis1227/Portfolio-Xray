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

1. `If this portfolio fell 25% in three months...`
   - Sell all risky positions.
   - Sell some and wait.
   - Hold and review evidence.
   - Buy more if fundamentals hold.

2. `When will this money need to work for withdrawals...`
   - Less than 3 years.
   - 3-10 years.
   - 10+ years.

3. `What temporary loss limit should trigger concern...`
   - Around 10%.
   - Around 15%.
   - Around 25%.
   - Around 35%+.

4. `What return target would make the risk worthwhile...`
   - 3-5% is enough.
   - 5-8% target range.
   - 8-12% target range.
   - 12%+ target range.

5. `If the current portfolio is concentrated...`
   - Reduce concentration first.
   - Diagnose before changing.
   - Hold if evidence is good.
   - Add if upside compensates.

## Profile mapping

The frontend stores onboarding state and maps it to the existing `ClientFitInput` shape through `frontend/lib/onboarding.ts`. The questionnaire scores stress reaction, horizon, temporary-loss limit, return need, and concentration response into one of the bounded Client Fit presets. The saved profile provides bounded display/test context for:

- target return range;
- volatility comfort range;
- maximum temporary-loss limit;
- horizon;
- profile label and confidence/source-quality display.

Manual target edits on Portfolio Input must reclassify the displayed preset from the edited return, volatility, drawdown, and horizon values instead of keeping a stale previous preset label.

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
