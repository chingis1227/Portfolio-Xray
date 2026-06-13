# Client Fit V1 final acceptance audit

Date: 2026-06-12
Plan: [Client Fit V1 Foundation](../exec_plans/2026-06-12_client_fit_v1_foundation_plan.md)

## Scope

This audit closes Session 21 of the Client Fit V1 foundation plan. It verifies that the active
source-of-truth documentation no longer describes Client Fit as future-only or as absent from the
Core MVP web journey, while preserving the important calculation boundary: Blocks 1-3 do not use
client-profile targets and the backend/CLI path remains compatible when Client Fit is missing.

This audit is documentation and acceptance evidence. It does not treat generated output folders as
source.

## Stale-reference audit

Search command used:

    rg -n -i "full web journey pending|routes are still pending|Planned V1|future Client-Fit Check|later Client-Fit Check|later — not Core MVP input|Client Fit V1 foundation input contract|Target/TBD.*Client|Client.*Target/TBD|no client profile in Core MVP|does not require client profile|client profile.*not required|not required.*client profile" AGENTS.md SPEC.md OUTPUTS.md README.md PRODUCT.md ARCHITECTURE.md DESIGN.md DATA.md TESTING.md GLOSSARY.md DECISIONS.md CHANGELOG.md docs/contracts docs/specs docs/runtime_artifact_contract.md frontend/README.md src tests config scripts

Result: no matches after Session 21 edits.

Session 21 updated active wording in:

- `DECISIONS.md`: `/client-profile` and `/client-fit` are active routes, not pending work.
- `CHANGELOG.md`: the Sessions 09A-11 entry is historical stabilization wording, not a current
  claim that the web journey is pending.
- `GLOSSARY.md`: Client Fit, Client Fit status, Diagnostic Quality status, and Goal-risk conflict
  are implemented V1 concepts, not planned-only concepts.
- `PRODUCT.md`, `docs/specs/stress_testing_spec.md`, `docs/specs/portfolio_xray_layer_spec.md`,
  and `docs/specs/input_assumptions_spec.md`: Blocks 1-3 still do not compare client-profile
  targets, but this is now explicitly separated from the active web Client Profile and post-Stress
  Client Fit Check.
- `src/analysis_setup.py`: exported explanatory strings no longer say client profile is only
  legacy/advanced context; they describe the Blocks 1-3 boundary and post-Stress Client Fit.
- `src/input_assumptions.py`, `tests/test_input_assumptions.py`, and
  `docs/specs/input_assumptions_spec.md`: the stale `client_fit_later` tier was replaced with
  `client_fit_v1`; portfolio value / initial investable amount remain risk-guardrail context because
  liquidity is excluded from Client Fit V1.

## Acceptance matrix

| Requirement | Status | Evidence |
| --- | --- | --- |
| Web users complete Client Fit before portfolio diagnosis | PASS | `/client-profile` route, `frontend/lib/journey.ts`, `frontend/components/portfolio/PortfolioInputTable.tsx`, and Session 20 Playwright QA. |
| Backend/CLI missing profile compatibility | PASS | `client_fit_status = not_provided` covered by `tests/test_client_fit_check.py` and `tests/test_client_fit_v1_matrix.py`. |
| `analysis_subject/client_fit_check.json` generated after Stress Lab and before Problem Classification | PASS | `run_report.py`, `src/client_fit.py`, Client Fit artifact tests, and runtime artifact docs. |
| Client Fit is evidence/context, not a universal diagnosis | PASS | `tests/test_client_fit_check.py` and `tests/test_client_fit_v1_matrix.py`. |
| Client Fit status, Diagnostic Quality status, and Decision Action stay separate | PASS | `tests/test_client_fit_check.py`, `tests/test_decision_verdict_client_fit.py`, and public display model tests. |
| Launchpad, Builder, Current vs Candidate, and Verdict are client-fit-aware | PASS | Sessions 09-12 tests listed in the ExecPlan plus frontend downstream context card tests. |
| No primary UI/report/API copy uses suitability/advice language as a conclusion | PASS | Guardrail search and Session 20 rendered-copy QA. Search may still find explicit forbidden-term guardrails, tests, or safe labels such as `Equity sell-off`; those are not product conclusions. |
| Supabase stores compact summaries only | PASS | `tests/test_supabase_client_fit_compact_storage.py` and `docs/supabase/README.md`. |
| Client Fit pass plus material issue does not become automatic no-trade | PASS | `tests/test_block_4_launchpad_cards.py` and `tests/test_decision_verdict_client_fit.py`. |
| Goal-risk conflict routes to objective review, not optimizer promise | PASS | `tests/test_client_fit_v1_matrix.py` and `tests/test_decision_verdict_client_fit.py`. |
| Same portfolio under different profiles changes Client Fit interpretation but not objective X-Ray/Stress metrics | PASS | `tests/test_client_fit_v1_matrix.py`. |
| UI presents three separate questions: what do you own, what does it look like, does it fit you | PASS | `/portfolio-input`, `/diagnosis` / `/evidence`, and `/client-fit` route contracts plus Session 20 screenshots. |

## Verification commands for final close

Run from repository root:

    .\.venv\Scripts\python.exe -m pytest tests\test_client_fit_profiles.py tests\test_client_fit_questionnaire.py tests\test_client_fit_check.py tests\test_client_fit_v1_matrix.py tests\test_decision_verdict_client_fit.py tests\test_input_assumptions.py -q
    .\.venv\Scripts\python.exe scripts\verify_docs.py
    .\.venv\Scripts\python.exe scripts\verify_fastapi_contract_governance.py
    cd frontend
    npm.cmd run test:api
    npm.cmd run typecheck
    cd ..
    rg -n -i "full web journey pending|routes are still pending|Planned V1|future Client-Fit Check|later Client-Fit Check|later — not Core MVP input|Client Fit V1 foundation input contract|Target/TBD.*Client|Client.*Target/TBD|no client profile in Core MVP|does not require client profile|client profile.*not required|not required.*client profile" AGENTS.md SPEC.md OUTPUTS.md README.md PRODUCT.md ARCHITECTURE.md DESIGN.md DATA.md TESTING.md GLOSSARY.md DECISIONS.md CHANGELOG.md docs/contracts docs/specs docs/runtime_artifact_contract.md frontend/README.md src tests config scripts
    rg -n "\bsuitable\b|\bsuitability approved\b|\bapproved\b|\bbuy\b|\bsell\b|\bmust rebalance\b|\bbest portfolio\b" frontend src docs config tests
    git diff --check

## Full-suite note

A full backend `pytest -q` run was attempted after the focused acceptance checks. It completed in
26:43 with `1898 passed`, `3 skipped`, and `13 failed`. The failures are broad repository regressions
outside the focused Client Fit acceptance path, including existing current-vs-candidate/comparison
status drift, pandas `QE` frequency compatibility in macro tests, ETF/stock universe seed-size
expectations, MVP workflow command expectations, and a Portfolio X-Ray golden fixture drift. They are
not hidden by this audit and should be handled by separate owning fixes before claiming the entire
repository test suite is green.

## Final verdict

Client Fit V1 foundation is accepted for the current Client Fit implementation boundary and focused
acceptance checks. The product now has an active web onboarding/display journey and
backend-compatible missing-profile behavior. The remaining important boundary is intentional: Client
Fit is diagnostic context and decision support, not suitability approval, trade advice, optimizer
mandate, or proof that no action is needed. This audit does not claim that the full repository
backend suite is green.
