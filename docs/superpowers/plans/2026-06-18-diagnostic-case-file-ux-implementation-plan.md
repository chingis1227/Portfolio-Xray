# Diagnostic Case File UX Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rework the current Portfolio MRI frontend route hierarchy so each platform screen reads as a Diagnostic Case File: conclusion first, evidence second, metrics with investor meaning third, technical details collapsed.

**Architecture:** This is a frontend presentation change using existing Next.js route components, existing review-state data, and existing shared UI primitives. No backend schema, formula, artifact, or route-unlock behavior changes are planned. Route-level copy and docs are updated in the same session.

**Tech Stack:** Next.js 14, React 18, TypeScript, Tailwind CSS, existing Portfolio MRI UI components.

---

## File structure

- Create `docs/superpowers/specs/2026-06-18-diagnostic-case-file-ux-design.md` as the approved UX design source for this pass.
- Modify `frontend/components/ui/VerdictHero.tsx`, `frontend/components/ui/EvidenceSummary.tsx`, and `frontend/components/ui/MetricMatrix.tsx` only if shared wording needs to support the new hierarchy.
- Modify route presentation components under `frontend/components/portfolio`, `frontend/components/diagnosis`, `frontend/components/evidence`, `frontend/components/client-fit`, `frontend/components/hypothesis`, `frontend/components/comparison`, `frontend/components/verdict`, and `frontend/components/report` without changing backend calls or review-state semantics.
- Update `docs/design/current_website_structure.md`, `docs/contracts/SCREEN_CONTRACTS.md`, `docs/specs/frontend_screen_contracts.md`, and `CHANGELOG.md` to match the implemented visible order.

## Tasks

### Task 1: Establish the written UX design

**Files:**
- Create: `docs/superpowers/specs/2026-06-18-diagnostic-case-file-ux-design.md`

- [x] Write the design document with route-by-route block order, top cards, top metrics, drill-down content, user understanding, and forbidden primary UI words.
- [x] Self-review the spec for placeholders, contradictions, scope creep, and ambiguous route language.
- [ ] Do not commit the spec in this session unless the user explicitly asks, because repository workflow says commits happen only on request.

### Task 2: Add or adjust shared case-file wording helpers

**Files:**
- Modify: `frontend/components/ui/VerdictHero.tsx`
- Modify: `frontend/components/ui/EvidenceSummary.tsx`
- Modify: `frontend/components/ui/MetricMatrix.tsx`

- [x] Keep hero facts capped and secondary to the finding.
- [x] Make empty evidence text explain the blocked conclusion rather than saying only that evidence is unavailable.
- [x] Make MetricMatrix descriptions emphasize investor meaning and drill-down placement.
- [x] Preserve current dark case-file styling and avoid new visual theme tokens.

### Task 3: Rework route-level hierarchy and copy

**Files:**
- Modify: `frontend/components/portfolio/PortfolioInputScreen.tsx`
- Modify: `frontend/components/portfolio/PortfolioInputTable.tsx`
- Modify: `frontend/components/diagnosis/DiagnosisSummaryPanel.tsx`
- Modify: `frontend/components/evidence/EvidenceScreen.tsx`
- Modify: `frontend/components/client-fit/ClientFitScreen.tsx`
- Modify: `frontend/components/hypothesis/HypothesisScreen.tsx`
- Modify: `frontend/components/comparison/ComparisonScreen.tsx`
- Modify: `frontend/components/verdict/VerdictScreen.tsx`
- Modify: `frontend/components/report/ReportScreen.tsx`

- [x] Portfolio Input shows Portfolio to diagnose, Input readiness, and Client Fit context before technical recovery details.
- [x] Diagnosis leads with Main diagnosis, Why it matters, and Key evidence; full metrics stay collapsed.
- [x] Stress Lab leads with Stress failure mode, Worst scenario, and Loss drivers/protection gap.
- [x] Client Fit leads with Fit interpretation, Main mismatch, and Profile context; missing profile text explains next action.
- [x] Hypothesis visibly splits Problem Classification, Candidate Launchpad, Alternatives Builder, and Candidate Generation Result.
- [x] Comparison leads with What improved, What worsened, and Is the trade-off meaningful.
- [x] Verdict uses allowed stance language only: Keep current, Review rebalance, Test another candidate, or Evidence insufficient.
- [x] Report leads with Plain-English explanation, Evidence used, and Limitations; grounding trace stays secondary.

### Task 4: Documentation sync

**Files:**
- Modify: `docs/design/current_website_structure.md`
- Modify: `docs/contracts/SCREEN_CONTRACTS.md`
- Modify: `docs/specs/frontend_screen_contracts.md`
- Modify: `CHANGELOG.md`

- [x] Update route block order and visible copy.
- [x] Update screen contracts so top-level states do not lead with raw availability labels.
- [x] Update frontend screen acceptance criteria for Diagnostic Case File hierarchy.
- [x] Add a concise changelog entry for the UX restructuring.

### Task 5: Verification and review

**Files:**
- Inspect changed files and terminal output.

- [x] Run `npm run lint` from `frontend` if the installed Next version supports it. Result: blocked by interactive ESLint setup prompt, not auto-configured.
- [x] Run `npm run typecheck` from `frontend`. Result: passed using `npm.cmd run typecheck`.
- [x] Run targeted forbidden-primary-language scans over `frontend/app` and `frontend/components`. Result: only sanitizer/presenter-layer matches remained.
- [x] Start a fresh local frontend server and visually inspect changed routes at desktop and mobile widths where time and environment allow. Result: not run because multiple existing `next dev` processes already write to the same `frontend/.next`.
- [x] Run `git diff --check` and `git status --short`.
- [x] Report any visual QA gaps, pre-existing dirty files, and unverified areas.

## Self-review

Spec coverage: the plan covers the written UX spec, shared presentation helpers, every requested route, documentation sync, and verification. No backend/API changes are included.

Placeholder scan: no TODO/TBD placeholders are present. The unchecked boxes are execution tracking items, not missing requirements.

Type consistency: route and component names match existing repository paths inspected before writing this plan.
