# Diagnosis Interpretation Session 15 Live Vertical QA Attempt

Date: 2026-06-12

## Scope

Session 15 attempted live FastAPI + Next.js + Playwright vertical QA across multiple portfolio scenarios using the new defensive helper:

```powershell
node scripts\qa_browser_vertical.cjs --scenario-limit 3
```

The helper starts fresh local FastAPI and Next.js servers on available ports, uses a clean Playwright browser context, clears browser storage before each scenario, exercises frontend compatibility API routes through FastAPI, verifies same-run lineage, probes stale selected-card rejection, and writes screenshots or DOM fallbacks.

## Result

Status: **Blocked before acceptance**.

The second live run reached the backend through the active frontend route but failed at the first diagnosis stage because live market-data downloads returned no prices for ordinary ETF tickers over the current runtime window.

Evidence:

- Frontend URL: `http://127.0.0.1:64925`
- FastAPI URL: `http://127.0.0.1:64924`
- QA report: `output/playwright/vertical-qa-2026-06-11T22-55-52-464Z/qa-report.json`
- FastAPI health: passed (`GET /api/v1/health` returned 200)
- Next readiness: passed (`GET /portfolio-input` returned 200)
- Next compile diagnostics: no fatal `.next`, module, or React Client Manifest failure detected
- Browser state: fresh Playwright context; storage cleared before the scenario
- Failure: `POST /api/portfolio/diagnose` returned 500 with safe error `Backend run failed.`
- Run-local failure artifact: `runs/frontend_review_20260611T225631Z_8ae5d08e/review_result.json`
- Backend stderr tail reported yfinance/market-data failures for `QQQ`, `VOO`, `SPY`, and `BIL` with no daily prices to cache.

## Interpretation

This is a live-data provider blocker, not evidence of stale browser state, stale server state, stale run-local artifact acceptance, frontend route compile failure, or unsupported product-copy behavior. Session 15 acceptance remains unproven because the live diagnosis stage did not produce the three required completed review chains.

## Follow-up

Before claiming full live acceptance, rerun the helper after the market-data date/provider issue is resolved or after an explicitly approved deterministic live-demo data source is added. The required acceptance target remains: at least three different input portfolios must produce different source-backed explanations, stale review artifacts must not unlock downstream stages, and material site claims must carry deterministic source references.

## Accepted rerun

After hardening empty-cache handling and Playwright route navigation retries, Session 15 was rerun successfully.

Accepted evidence:

- Command: `node scripts\qa_browser_vertical.cjs --scenario-limit 3`
- Frontend URL: `http://127.0.0.1:50797`
- FastAPI URL: `http://127.0.0.1:50796`
- QA report: `output/playwright/vertical-qa-2026-06-12T08-12-35-071Z/qa-report.json`
- Completed scenarios: `concentrated_growth_cash`, `weak_crisis_resilience_live`, `balanced_reference`
- Active review IDs: `frontend_review_20260612T081243Z_d30f0b4d`, `frontend_review_20260612T081403Z_09f0a7d0`, `frontend_review_20260612T081505Z_a3ca678a`
- Distinct diagnosis IDs observed: `mixed_evidence_no_action`, `weak_crisis_resilience`
- Every scenario completed Diagnosis -> Builder -> Candidate -> Comparison -> Verdict -> Report through the frontend compatibility routes and FastAPI.
- Every stale selected-card probe returned HTTP 409.
- Every scenario carried source-artifact evidence for diagnosis, comparison, verdict, and report.

Final Session 15 status: **accepted**.
