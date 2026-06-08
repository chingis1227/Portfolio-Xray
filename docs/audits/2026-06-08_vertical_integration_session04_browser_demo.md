# Session 04 Manual Browser Demo Evidence — Vertical Integration Post-Audit Hardening

Date: 2026-06-08
Operator: Codex
Plan: `docs/exec_plans/2026-06-08_vertical_integration_post_audit_hardening_plan.md`, Session 04
Frontend URL: `http://localhost:3003` (`npm.cmd run dev`; ports 3000-3002 were already in use)
Run id: `frontend_review_20260608T211411Z_37eacc28`
Run directory: `runs/frontend_review_20260608T211411Z_37eacc28/`

## Scope

This was a manual in-app browser click-through from Portfolio Input through Report / AI Commentary grounding. It used the real Next.js API routes and the Python bridge. It did not edit Python calculation logic, root `config.yml`, PDFs, or generated source artifacts.

The input portfolio was the valid default frontend portfolio that was already present on Portfolio Input and summed to 100%:

- SPY 40%
- QQQ 20%
- BND 20%
- GLD 10%
- Cash USD 10%

## Observed flow

1. Portfolio Input accepted the portfolio as ready for diagnosis and called the diagnosis route.
2. Diagnosis completed and navigated to `/diagnosis`.
   - UI showed a real run diagnosis summary.
   - Main evidence included CAGR 12.5%, volatility 10.6%, max drawdown -20.1%, and worst stress `recession_severe` at -30.86%.
3. Evidence page displayed current-portfolio X-Ray and Stress evidence before candidate generation.
4. Hypothesis page displayed backend Candidate Launchpad cards.
   - Selected card: `Compare Against Simple References`.
   - Selected card id observed from backend artifacts: `launchpad_01_compare_against_simple_benchmark`.
   - UI wording preserved the boundary that the Launchpad card is a hypothesis test only and not a recommendation.
5. Builder / candidate stage generated one diagnostic candidate.
   - Candidate id: `equal_weight`.
   - UI showed `Candidate generated`, `generated`, and `Compare-ready: yes · no comparison or verdict was generated.`
6. Comparison page ran Current vs Candidate evidence.
   - UI showed `Active comparison` and `No-trade valid`.
   - Comparison conclusion said evidence was visible but did not automatically justify action.
   - Detailed metrics were mostly `n/a` / `Unclear` because backend comparison materiality was insufficient.
7. Verdict page generated a decision-support verdict.
   - UI showed `Evidence insufficient`.
   - UI explicitly said the page does not recommend trades, execute trades, or identify a best portfolio.
8. Report page generated grounded report commentary.
   - UI showed `Grounded client-ready report summary`.
   - Grounding file shown in UI: `runs/frontend_review_20260608T211411Z_37eacc28/ai_commentary_context.json`.
   - Report ended with `Decision Verdict is evidence_insufficient` and a decision boundary saying the report does not recommend trades, execute trades, provide suitability advice, or identify a best portfolio.

## Artifact chain observed

Server log confirmed successful API calls and bridge outputs:

- `POST /api/portfolio/diagnose` -> `runs/frontend_review_20260608T211411Z_37eacc28/review_result.json`
- `POST /api/portfolio/candidate/generate` -> `runs/frontend_review_20260608T211411Z_37eacc28/candidate_generation_result.json`
- `POST /api/portfolio/comparison/generate` -> `runs/frontend_review_20260608T211411Z_37eacc28/current_vs_candidate_result.json`
- `POST /api/portfolio/verdict/generate` -> `runs/frontend_review_20260608T211411Z_37eacc28/decision_verdict_result.json`
- `POST /api/portfolio/report/generate` -> `runs/frontend_review_20260608T211411Z_37eacc28/report_commentary_result.json`

Files present in the run directory after the demo:

- `review_result.json` — present, status `completed`.
- `candidate_generation_result.json` — present, status `completed`, stage `candidate_generation`, selected card `launchpad_01_compare_against_simple_benchmark`, candidate `equal_weight`.
- `current_vs_candidate_result.json` — present, status `completed`, stage `current_vs_candidate`, selected card `launchpad_01_compare_against_simple_benchmark`, candidate `equal_weight`.
- `decision_verdict_result.json` — present, status `completed`, stage `decision_verdict`, selected card `launchpad_01_compare_against_simple_benchmark`, candidate `equal_weight`.
- `report_commentary_result.json` — present, status `completed`, stage `report_commentary`, selected card `launchpad_01_compare_against_simple_benchmark`, candidate `equal_weight`.
- `ai_commentary_context.json` — present and referenced by the Report UI.

## Important finding

The documented Session 01 / Session 02 flow says the operator should click **Prepare Builder setup** and that the run should contain `builder_setup_result.json`. In this manual browser demo, after selecting the first backend-generatable Launchpad card, the UI immediately showed **Builder setup prepared** and enabled **Generate one diagnostic candidate**. No separate `POST /api/portfolio/builder/prepare` call appeared in the dev-server log, and `runs/frontend_review_20260608T211411Z_37eacc28/builder_setup_result.json` was not present.

This means the full browser flow can currently reach Report, but Session 04 found a mismatch between the documented natural demo path and the observed UI/API artifact chain: the explicit prepare-builder handoff was not evidenced for this run. Treat this as a follow-up hardening item before claiming the documented Builder prepare path is manually verified end-to-end.

## Product wording boundaries observed

The UI preserved the intended non-binding language throughout the demo:

- Candidate / Launchpad: hypothesis test only, not a recommendation.
- Builder setup: setup preview / setup only, not a rebalance instruction.
- Candidate generation: one diagnostic candidate, not comparison or verdict.
- Comparison: diagnostic comparison only, not winner selection or trade instruction.
- Verdict: evidence-insufficient / decision-support only, not a trading instruction.
- Report: grounded in run-local artifacts; does not recommend trades, execute trades, provide suitability advice, or identify a best portfolio.

## Result

Manual browser demo result: completed from Portfolio Input through grounded Report commentary.

Verification caveat: the run did not evidence the explicit `/api/portfolio/builder/prepare` stage or `builder_setup_result.json`; this should be corrected or consciously documented in a later hardening session.
