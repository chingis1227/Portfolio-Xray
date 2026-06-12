# FastAPI Foundation Session 10 Acceptance and Browser QA

Date: 2026-06-11

## Scope

Session 10 ran final acceptance for the FastAPI foundation migration, including backend contract
checks, frontend compatibility checks, production build, and browser QA of the normal local frontend
path through FastAPI compatibility routes.

No portfolio formulas, generated artifact schemas, root `config.yml`, PDF export behavior, or
FastAPI public schema were intentionally changed in this session.

## Automated verification

Commands run from the repository root unless noted:

```powershell
.\.venv\Scripts\python.exe scripts\verify_fastapi_contract_governance.py
.\.venv\Scripts\python.exe -m pytest tests\test_fastapi_app.py tests\test_fastapi_contract_governance.py tests\test_frontend_review_bridge.py -q
cd frontend
npm.cmd run test:api
npm.cmd run test:smoke
npm.cmd run typecheck
npm.cmd run build
```

Final post-fix results:

- FastAPI contract governance: OK.
- Python focused tests: 45 passed.
- Frontend API route tests: 8 passed.
- Frontend static smoke: 1 passed.
- Frontend typecheck: passed.
- Frontend build: passed.
- Docs verification: OK.
- Docs link tests: 7 passed.

## Browser QA environment

- FastAPI URL: `http://127.0.0.1:8010`
- Frontend URL: `http://127.0.0.1:3010`
- FastAPI command: `.\.venv\Scripts\python.exe -m uvicorn src.api.app:app --host 127.0.0.1 --port 8010`
- Frontend command: `npm.cmd run dev -- --hostname 127.0.0.1 --port 3010`
- Browser state: `localStorage` and `sessionStorage` cleared before the run.
- Sample mode: not used.
- Active `reviewId`: `frontend_review_20260611T154145Z_fe2bd3a3`
- Selected Launchpad card: `launchpad_01_compare_against_simple_benchmark`
- Generated candidate: `equal_weight`

## Browser QA path

The verified browser route chain was:

```text
/portfolio-input
-> /diagnosis
-> /evidence
-> /hypothesis
-> generate candidate
-> /comparison
-> /verdict
-> generate verdict
-> /report
-> create preview
```

Screenshots captured under `output/playwright/`:

- `session10_portfolio_input.png`
- `session10_diagnosis.png`
- `session10_evidence.png`
- `session10_hypothesis_before_candidate.png`
- `session10_hypothesis_candidate_generated.png`
- `session10_comparison_evidence_insufficient_gate.png`
- `session10_verdict_before_generate.png`
- `session10_verdict_after_generate.png`
- `session10_report_before_preview.png`
- `session10_report_after_preview.png`

Logs captured under `output/playwright/`:

- `session10_fastapi_8010.log`
- `session10_fastapi_8010.err.log`
- `session10_next_3010.log`
- `session10_next_3010.err.log`

These are generated QA artifacts and should not be treated as source.

## Finding and fix

Finding: the backend correctly allowed an evidence-insufficient verdict when comparison metrics were
unavailable, but the frontend state gate required at least one displayable comparison metric before
Verdict could be reached. In the browser, the default UI portfolio generated the `equal_weight`
candidate and wrote comparison artifacts, but `/comparison` blocked on "Comparison metrics
unavailable" instead of allowing the safe evidence-insufficient Verdict path.

Fix: `frontend/lib/reviewState.tsx` now treats a completed, same-candidate comparison with
`comparisonStatus=available` as sufficient to generate a Verdict, even when no displayable metrics
exist. `frontend/app/comparison/page.tsx` now shows a clear "Continue to verdict" action in the
metrics-unavailable state when the comparison can produce a safe evidence-insufficient verdict.

This preserves the product boundary: Comparison still does not crown a winner or recommend a trade;
Verdict owns the evidence-insufficient decision-support outcome.

## Browser QA result after fix

After the fix, the same active review continued successfully:

- `/comparison` showed metrics unavailable plus a safe `Continue to verdict` path.
- `/verdict` generated `verdictId=evidence_insufficient` with decision-support-only copy.
- `/report` created a grounded report preview from the evidence-insufficient verdict.

Unverified areas:

- No PDF export was tested; PDF generation is outside the normal FastAPI/site API path.
- No full multi-candidate arena was tested; it is outside the Core MVP route chain.
- No generated `runs/` artifacts are intended for commit.
