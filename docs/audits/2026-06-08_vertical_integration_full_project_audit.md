# Vertical Integration Full Project Audit — 2026-06-08

## 1. Executive verdict

**Overall verdict:** the frontend - API - Python bridge - Python pipeline - product JSON outputs - frontend screen flow is logically connected and mostly coherent for a local scripted demo.

- **Project flow coherent?** Yes, with one important workflow caveat: the backend bridge has a safe `--prepare-builder` step, but the live frontend currently exposes only candidate generation, not a separate prepare-builder API/button. In practice, the user can generate a candidate only for a Launchpad card whose Builder setup already matches the selected card.
- **Frontend/backend integration logically connected?** Yes. The API routes call `scripts/run_review_from_payload.py`; the bridge writes and consumes isolated `runs/frontend_review_*` artifacts; downstream stages re-check selected card/candidate lineage.
- **Current state demo-ready locally?** Yes for a guided local demo if the operator selects the card that has matching Builder setup and follows the runbook cautiously. A manual browser click-through was not run in this audit.
- **Production-ready?** No. This is a local demo/prototype integration: no production auth, database-backed run retrieval, deployment hardening, API route integration tests, or robust multi-user state model.

No Python calculation logic, root `config.yml`, generated run folders, staging, or commits were changed by this audit. This report is documentation-only.

## 2. Audit summary table

| Area | Status | Finding | Evidence | Recommended action |
| --- | --- | --- | --- | --- |
| Frontend route structure | OK | Seven product screens and five API routes map to the vertical flow. | `frontend/app/*`; API routes under `frontend/app/api/portfolio/*`; `npm.cmd run build` lists all routes. | Keep current stage separation. |
| Input > API | OK | Portfolio Input posts validated holdings to `POST /api/portfolio/diagnose`; API repeats validation. | `PortfolioInputTable.tsx`; `frontend/app/api/portfolio/diagnose/route.ts`. | Add route-level JS tests later. |
| API > Python bridge | OK | Diagnosis calls `run_review_from_payload.py --mode diagnosis_plus_problem`; later stages call focused bridge flags. | `diagnose/route.ts`; candidate route line with `--generate-candidate`; bridge `parse_args()`. | Keep one-action-per-command rule. |
| Run isolation | OK | Bridge creates `runs/frontend_review_*`, writes run-local `payload.json`, `input.yml`, `review_result.json`. | `create_run_dir()` and `build_input_config()` in `scripts/run_review_from_payload.py`. | Keep `runs/` ignored and never use generated artifacts as source. |
| Root `config.yml` safety | OK | Frontend bridge writes run-local `input.yml`; it does not modify root config. | `build_input_config()`; API routes pass review id / payload, not root config edits. | Keep this invariant in tests. |
| Candidate zoo prevention | OK | Frontend candidate route calls one selected candidate path; bridge asserts `candidate_factory_run.steps` contains exactly one candidate. | `generate_selected_candidate()` and `_assert_factory_run_scoped_to_one_candidate()`. | Add a JS/API smoke test for route arguments. |
| Builder handoff | Warning | Backend supports `--prepare-builder`, but frontend has no prepare-builder API route/button. Generation is enabled only when an existing Builder setup matches the selected card. | `prepare_selected_builder_setup()` exists; candidate API calls only `--generate-candidate`; Hypothesis page gates on `builderMatches`. | P1: add explicit prepare-builder API/UI or document that only the prebuilt matching card can be generated. |
| Diagnosis outputs | OK | Diagnosis reads `portfolio_xray`, `stress_report`, `problem_classification`, `candidate_launchpad`, and Builder setup from `analysis_subject/`. | `expected_output_paths()` / `read_outputs()`. | Keep required-output failures safe. |
| Evidence screen | OK | Uses compact real evidence summary after reload; demo evidence is only explicit `?sample=1`. | `frontend/app/evidence/page.tsx` `sampleMode`; `reviewSummary.evidence`. | Good current behavior. |
| Hypothesis screen | Warning | Real Launchpad can render from compact state after reload, but selected non-matching cards cannot generate. | `compactLaunchpadCards`; `builderMatches`; `canGenerateCandidate`. | Same P1 Builder handoff fix. |
| Comparison screen | OK | No silent demo fallback; calls comparison API; only matching candidate summaries unlock verdict. | `frontend/app/comparison/page.tsx`. | Good current behavior. |
| Verdict screen | OK | No demo fallback; calls verdict API; wording supports no-trade / evidence-insufficient. | `frontend/app/verdict/page.tsx`; `recordVerdictResult()`. | Good current behavior. |
| Report / AI Commentary | OK | No static demo fallback; calls report API and renders post-compare `ai_commentary_context`. | `frontend/app/report/page.tsx`; `write_selected_report_context()`. | Add persistence/reload strategy later if desired. |
| Stale artifact guards | OK | Bridge rejects mismatched card/candidate; Block 8 ignores downstream stale artifacts; AI context enforces post-compare grounding. | `_assert_candidate_generation_lineage()`, `write_block8_current_vs_candidate_only_outputs()`, `write_selected_report_context()`. | Keep tests in focused suite. |
| Error handling | OK | Bridge and API scrub tracebacks and absolute paths before client responses. | `scrub_failure_text()` and API `scrubForClient()`; focused tests passed. | Add route-level tests for API scrub wrappers. |
| localStorage/state | OK | Browser persists compact `pmri.activeReview.v2`; raw legacy keys are cleaned; downstream summaries are invalidated on new runs. | `frontend/lib/reviewState.tsx`. | Later: backend fetch-by-reviewId for full reload restoration. |
| Generated artifacts ignored | OK | `runs/`, `.next/`, `tmp/`, `Main portfolio/`, candidate folders, `portfolio_weights.yml` are ignored. | `.gitignore`; `git status --ignored` shows ignored generated paths. | Good current behavior. |
| Docs alignment | Warning | Main docs broadly match product truth, but runbook says “Generate Builder setup first” in UI path although no frontend prepare-builder step exists. | `docs/demo/frontend_backend_vertical_runbook.md` line 133; no frontend prepare-builder route. | P1 docs/UI sync. |
| Tests | Needs follow-up | Focused Python bridge/backend tests are strong; no direct Next.js API route tests or browser click-through were run here. | `33 passed` frontend bridge; `27 passed` relevant backend tests. | Add API route and Playwright/manual browser checklist. |

## 3. Flow-by-flow audit

### Input > API

The input flow is coherent. `frontend/components/portfolio/PortfolioInputTable.tsx` validates currency, instrument/cash rows, duplicates, positive weights, and total weight before enabling diagnosis. The API route repeats lightweight validation in `frontend/app/api/portfolio/diagnose/route.ts`.

The frontend payload uses percentage weights. The Python bridge normalizes them to decimal weights and preserves real cash labels such as `Cash USD`; this is covered by `test_normalize_payload_maps_frontend_percent_and_preserves_real_cash`.

### API > Python bridge

The API routes consistently spawn the local Python bridge:

- Diagnosis: `scripts/run_review_from_payload.py --payload <payload> --mode diagnosis_plus_problem`.
- Candidate: `--generate-candidate --review-id <id> --selected-card-id <card>`.
- Comparison: `--run-comparison --review-id <id> --selected-card-id <card>`.
- Verdict: `--run-verdict --review-id <id> --selected-card-id <card>`.
- Report: `--run-report-context --review-id <id> --selected-card-id <card>`.

The bridge enforces one stage flag per CLI call. API responses are read from result JSON files rather than raw stdout, which is safer and easier to audit.

### Python bridge > isolated run directory

`create_run_dir()` creates `runs/frontend_review_<timestamp>_<id>/`. `build_input_config()` writes a run-local `input.yml` with `output_dir` and `output_dir_final` under that run directory. This prevents mutation of root `config.yml` and avoids treating root `Main portfolio/` as active frontend state.

`safe_review_run_dir()` also rejects non-`frontend_review_*` ids and path separators, reducing path traversal risk.

### Diagnosis outputs

For `diagnosis_plus_problem`, the bridge expects and reads:

- `analysis_subject/portfolio_xray.json`
- `analysis_subject/stress_report.json`
- `analysis_subject/problem_classification.json`
- `analysis_subject/candidate_launchpad.json`
- `analysis_subject/portfolio_alternatives_builder.json`
- optional diagnosis-only `ai_commentary_context.json` as debug context

The command uses `run_portfolio_review.py --skip-candidates --output-profile site_api`, which matches the diagnosis-first requirement and prevents candidate zoo execution during initial diagnosis.

### Evidence outputs

The Evidence page uses real compact evidence from `reviewSummary.evidence` after reload. If raw outputs are still in memory during the current tab, it can also derive evidence directly from `portfolio_xray` and `stress_report`. Static demo evidence is gated behind explicit `?sample=1`; there is no silent demo fallback after a real run.

### Hypothesis / Launchpad

The Hypothesis page renders real Launchpad cards from raw `reviewResult.outputs.candidate_launchpad` or compact `reviewSummary.launchpadCards`. Static demo Launchpad is gated behind explicit `?sample=1`.

Product language is correct: Launchpad cards are hypothesis tests, not recommendations.

**Main caveat:** the page shows multiple real cards, but generation is only enabled when `builderDocument.selected_card_id` matches the selected card. There is no frontend call to `--prepare-builder`, although the bridge supports it. This can make non-prebuilt cards appear selectable but non-generatable.

### Builder

The backend bridge has a good Builder safety path: `prepare_selected_builder_setup()` rebuilds a run-local Builder artifact for one selected card and validates lineage. However, the live frontend does not currently call this path. The runbook’s phrase “Generate Builder setup first” is therefore operator-accurate only for CLI replay, not for the visible UI.

### Candidate Generation

Candidate generation is strongly guarded:

- Requires run-local `input.yml` and `analysis_subject/portfolio_alternatives_builder.json`.
- Requires Builder lineage fields to match the selected card.
- Delegates to `generate_candidate_from_builder_setup()` with run-local output paths.
- Asserts `candidate_generation` lineage and `candidate_factory_run.json` scope.
- Returns stage failure rather than silently falling back to old weights.

This supports the principle: Candidate = hypothesis, not recommendation.

### Current vs Candidate

Comparison uses `write_block8_current_vs_candidate_only_outputs()` with exactly the selected generated candidate id. The bridge checks that `current_vs_candidate.selected_candidate_ids == [candidate_id]`. The Block 8 writer records stale downstream verdict/action/journal/AI artifacts as ignored instead of treating them as current.

This supports: Comparison = trade-off, not winner selection.

### Decision Verdict

Verdict generation uses `write_decision_verdict_outputs()` with the active `candidate_generation` and `current_vs_candidate` evidence. The bridge rejects mismatched candidate ids and requires the `does_not_execute_trades` guardrail.

This supports: Verdict = decision-support, not trading instruction. No-trade and evidence-insufficient states are rendered as normal outcomes.

### Report / AI Commentary

Report generation uses `write_selected_report_context()` and writes/reads run-local `ai_commentary_context.json`. The bridge requires candidate, comparison, and verdict scope to match before it accepts the context, and requires `grounding_phase == "post_compare"`.

The frontend report does not call an LLM and does not generate PDFs. It renders deterministic `client_explanation_draft.sentences` from the grounded context.

### Frontend state / localStorage

State is compact and safer than storing raw backend JSON:

- Persisted key: `pmri.activeReview.v2`.
- Raw `review_result.json` is not permanently persisted.
- Legacy `pmri.reviewResult.*` keys are removed.
- New input clears candidate/comparison/verdict state.
- Comparison/verdict summaries are kept only when selected card/candidate lineage matches.

This is coherent for a local demo. Production would need server-side run retrieval and multi-user isolation.

### Error handling

The bridge and API routes scrub tracebacks and local filesystem paths. Tests verify scrub behavior for bridge output. API routes duplicate scrubbing with `scrubForClient()`.

Remaining gap: no direct Next.js API route tests assert scrub behavior at the route layer.

### Documentation alignment

Docs mostly align with the current product truth: diagnosis-first, one selected hypothesis, candidate not recommendation, comparison not winner, verdict not trading instruction, generated artifacts not source.

Main mismatch: the runbook and ExecPlan describe a Builder-prepare capability that exists in the Python bridge, but the normal frontend path does not expose it. The runbook should either specify “select the prebuilt matching Builder card” or the UI/API should add a prepare-builder step.

## 4. Critical issues

No P0 critical issue was found that necessarily breaks the scripted local demo when the operator selects the existing matching Builder card.

Potential demo-breaking issue if the operator behaves naturally:

1. **Selectable Launchpad cards may not be generatable in the UI.**
   - Impact: an operator may select a real Launchpad card, see it in the Builder panel, but be unable to generate because no frontend route prepares a matching Builder setup for that selected card.
   - Evidence: `prepare_selected_builder_setup()` exists in `scripts/run_review_from_payload.py`, but no `frontend/app/api/portfolio/builder/...` route exists; candidate route calls `--generate-candidate` directly; Hypothesis requires `builderMatches`.
   - Severity: P1, or P0 if the upcoming demo must allow arbitrary card selection live.

## 5. Non-critical issues

- `../../frontend/README.md` still says `data/demo/` is used by pages during prototype phase. This is technically true for Portfolio Input defaults and explicit sample modes, but it could be clearer that normal Evidence/Hypothesis/Comparison/Verdict/Report flow does not silently fall back to demo JSON.
- Runbook verification command uses a session-specific basetemp name (`pytest_frontend_bridge_session15`) instead of a generic audit/demo name.
- No automated browser click-through was run in this audit.
- No direct tests import/call Next.js route handlers; route correctness is verified indirectly via TypeScript/build and bridge tests.
- The API routes hard-code `.venv/Scripts/python.exe`, which is OK for this Windows local repo but not portable production behavior.
- The required audit command in the user prompt used `..\.venv\Scripts\python.exe` from repo root. That path does not exist in this workspace; the project-local `.\.venv\Scripts\python.exe` exists and was used.

## 6. Documentation/code mismatches

| File | Section / text | Mismatch | Suggested correction |
| --- | --- | --- | --- |
| `docs/demo/frontend_backend_vertical_runbook.md` | Manual click-through step 4: “Generate Builder setup first.” | There is no frontend prepare-builder API/button in the visible UI. The Python CLI has `--prepare-builder`, but frontend candidate route calls `--generate-candidate` directly. | Either add a frontend prepare-builder step or change runbook to say candidate generation is available only for the card whose Builder setup is already active. |
| `../../frontend/README.md` | `data/demo/` used by pages during prototype phase. | Could be read as silent demo fallback, though later screens mostly avoid silent fallback. | Clarify: demo data is used for initial Portfolio Input defaults and explicit `?sample=1`, not normal post-run stages. |
| `docs/exec_plans/2026-06-08_frontend_backend_vertical_integration_plan.md` | Session 02/04 narrative. | The plan correctly records both backend prepare-builder and frontend generation gating, but final operator outcome can sound like any selected hypothesis works from UI. | Add a final note: current UI generation depends on a matching Builder setup unless/until prepare-builder is wired to frontend. |
| User-facing audit command | `..\.venv\Scripts\python.exe` from repo root. | Actual project venv is `.\.venv\Scripts\python.exe`. | Use project-local `.venv` in docs/commands. |

## 7. Test coverage gaps

Covered by this audit:

- Frontend TypeScript compile.
- Next.js production build with all vertical API routes.
- Python frontend bridge contract tests: 33 passed.
- Candidate generation / comparison / verdict / stale-guard focused backend tests: 27 passed.

Not yet covered or not run here:

- Direct Next.js API route unit/integration tests for payload validation, subprocess errors, timeouts, and scrubbed client responses.
- Automated browser journey test from Portfolio Input through Report.
- Test that Hypothesis UI behavior is clear when selecting a non-matching Launchpad card.
- End-to-end live data run during this audit; existing ExecPlan says prior Session 11 did backend vertical QA for three portfolios, but this audit did not rerun that expensive path.
- Cross-platform backend invocation; API currently assumes Windows `.venv\Scripts\python.exe`.
- Production concurrency / multi-user isolation beyond run-id path guards.

## 8. Recommended fix plan

### P0 — must fix before demo

No unconditional P0 found for a scripted local demo using the matching Builder card.

If the demo will be unscripted and the presenter may select any Launchpad card, promote the Builder handoff issue to P0.

### P1 — should fix soon

1. **Wire frontend prepare-builder step or tighten UX/docs.**
   - Option A: add `POST /api/portfolio/builder/prepare` calling `--prepare-builder`, then let any valid selected Launchpad card prepare Builder setup before candidate generation.
   - Option B: explicitly mark only the active Builder-matching card as generatable and update the runbook.
2. **Clarify demo-data language in `../../frontend/README.md`.**
3. **Add a small route-level API test strategy or route-handler tests for scrubbed failures.**
4. **Add manual browser demo checklist result after a real click-through.**

### P2 — can wait

1. Add Playwright smoke test for the local vertical journey.
2. Add backend fetch-by-`reviewId` endpoint so full raw artifacts can be reloaded after page refresh without relying only on compact summaries.
3. Make Python executable resolution configurable instead of hard-coded to Windows `.venv`.
4. Add user-facing explanation when candidate generation is blocked because Builder setup does not match the selected card.

### P3 — backlog

1. Production deployment packaging.
2. Server-side run database / durable user workspaces.
3. Rich report export / PDF regeneration from frontend.
4. Multi-candidate research arena, if ever promoted from advanced/backend to product scope.

## 9. Do-not-fix list

Do not touch these as part of the immediate cleanup:

- Production auth.
- Database or cloud deployment.
- PDF generation / polished PDF product.
- Advanced optimizer features.
- Macro Dashboard / Macro Overlay.
- Multi-client workspace.
- Candidate zoo / multi-candidate arena.
- Root `config.yml`.
- Python calculation logic, estimators, stress formulas, or optimizer math.
- Generated run folders, candidate folders, `Main portfolio/`, or cached outputs unless explicitly requested.

## 10. Verification performed

Commands run from `frontend/`:

```powershell
npm.cmd run typecheck
npm.cmd run build
```

Results:

- `npm.cmd run typecheck`: passed.
- `npm.cmd run build`: passed. Build listed `/api/portfolio/diagnose`, `/api/portfolio/candidate/generate`, `/api/portfolio/comparison/generate`, `/api/portfolio/verdict/generate`, and `/api/portfolio/report/generate`.

Command requested from repo root with `..\.venv\Scripts\python.exe`:

```powershell
..\.venv\Scripts\python.exe -m pytest tests\test_frontend_review_bridge.py -q --basetemp="tmp\pytest_frontend_bridge_audit"
```

Result: failed to start because `..\.venv\Scripts\python.exe` does not exist from the repository root.

Equivalent project-local venv command actually run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_frontend_review_bridge.py -q --basetemp="tmp\pytest_frontend_bridge_audit"
```

Result:

```text
33 passed in 2.23s
```

Additional safe focused tests:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_candidate_generation_from_builder_setup.py tests\test_blocks_6_7_downstream_integration.py tests\test_block8_current_vs_candidate_boundary.py tests\test_blocks_8_10_downstream_integration.py tests\test_current_vs_candidate.py tests\test_current_vs_candidate_comparison_contract.py tests\test_decision_verdict.py tests\test_decision_verdict_contract.py tests\test_no_stale_candidate_generation.py tests\test_no_stale_verdict_in_ai_context.py -q --basetemp="tmp\pytest_vertical_audit_relevant"
```

Result:

```text
27 passed in 7.82s
```

Generated artifact ignore check:

- `.gitignore` includes `runs/`, `.next/`, `tmp/`, `Main portfolio/`, candidate output folders, and `portfolio_weights.yml`.
- `git status --ignored --short runs frontend/.next tmp "Main portfolio"` showed those paths as ignored.

## 11. Final recommendation

Next step: **manual browser demo** using the runbook, but keep it scripted: select the Launchpad card whose Builder setup is active/generatable. After that, open a small cleanup/fix session for the P1 Builder handoff mismatch so the UI can either prepare Builder setup for any selected card or clearly restrict generation to the active Builder card.
