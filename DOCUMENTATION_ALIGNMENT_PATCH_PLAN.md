# DOCUMENTATION_ALIGNMENT_PATCH_PLAN.md

## 1. Executive Summary

This document converts `DOCUMENTATION_ALIGNMENT_AUDIT.md` into a small, session-by-session documentation patch roadmap.

The active product narrative is broadly aligned with the new Portfolio MRI architecture, but several documentation layers still need careful cleanup:

- `README.md` and `AGENTS.md` still carry legacy-heavy `Optimization Terminal` positioning that can weaken the diagnosis-first product identity.
- `SPEC.md`, `OUTPUTS.md`, and `docs/specs/*.md` correctly preserve implementation truth, but need narrow clarification that product-facing `Decision Verdict` language maps to current technical contracts such as `Selection Engine` and `selection_decision.json` without renaming them.
- `GLOSSARY.md` should remain the shared terminology bridge between new product language and current implementation terminology.
- Historical docs (`CHANGELOG.md`, `docs/exec_plans/*.md`, `docs/audits/*.md`, `docs/archive/*`) should not be rewritten; they may only need classification notes so they are not mistaken for current product direction.
- Advanced / Later capabilities may remain documented as current backend/advanced capabilities where verified, but must not be promoted to Core MVP UX.

This plan is documentation-only. It does not authorize code changes, schema changes, output contract changes, CLI changes, formula changes, or generated artifact changes.

## 2. Guardrails

All sessions in this plan must follow these rules:

- Do not change code.
- Do not change CLI behavior.
- Do not change JSON schemas.
- Do not change generated output contracts.
- Do not change formulas, gates, constraints, scoring logic, or data rules.
- Do not rename public fields, commands, output files, generated folders, or artifact contracts.
- Do not rewrite historical docs.
- Do not rename technical contracts unless a separate migration plan exists and is approved.
- Product-facing language may map old technical terms to new terminology.
- `Decision Verdict` is product-facing language for now; `Selection Engine`, `selection_decision.json`, and No-Trade artifact names remain current technical contracts until separately migrated.
- Technical/spec docs must continue to describe current implementation truth, not target product vision.
- `SPEC.md`, `OUTPUTS.md`, and `docs/specs/*.md` must not be softened into aspirational product documents.
- Advanced / Later features must stay outside Core MVP unless explicitly specified, implemented, tested, documented, and approved.
- Existing implementation capabilities must not be deleted or demoted solely because they are not Core MVP UX.
- Generated and archived files must not be treated as active source-of-truth unless the task explicitly targets them.

## 3. Session-by-Session Plan

### Session 01 — README and AGENTS positioning cleanup

**Files to inspect:**

- `README.md`
- `AGENTS.md`
- `DOCUMENTATION_ALIGNMENT_AUDIT.md`
- `PRODUCT.md`
- `ARCHITECTURE.md`

**Files allowed to edit:**

- `README.md`
- `AGENTS.md`

**Objective:**

Lightly align the project front door and agent operating summary with the new Portfolio MRI positioning:

- diagnosis-first;
- current portfolio first;
- no black-box optimizer;
- candidate portfolios as investment hypotheses;
- optimization/candidate builders as supporting infrastructure, not the product identity.

**What to preserve:**

- Current commands.
- Source-of-truth routing.
- Generated-output policy.
- Current CLI/file-driven implementation notes.
- Legacy compatibility commands.
- Agent operating rules.
- Documentation verification rules.
- Existing warnings that product concepts do not override `SPEC.md`, detailed specs, or code.

**What to change:**

- Reframe legacy-heavy `Portfolio X-Ray & Optimization Terminal / Portfolio MRI` language where it weakens the product identity.
- Lead with `Portfolio MRI / Portfolio X-Ray` as a diagnostics and investment decision-support system.
- State that optimization and candidate generation remain available as current/legacy/backend capabilities, but are not the product's black-box core.
- Clarify that V1 artifacts such as Portfolio Health Score, Robustness Scorecard, Selection/No-Trade, Action Plan, Monitoring, and Decision Journal are current generated artifacts, not necessarily Core MVP product UI.

**What not to touch:**

- No commands.
- No code references unless wording-only context requires it.
- No schema or artifact names.
- No generated paths.
- No detailed specs.

**Verification command:**

```powershell
git status --short
git diff --stat -- README.md AGENTS.md
git diff --name-only -- README.md AGENTS.md
```

**Expected output:**

- A concise summary of wording changes.
- Confirmation that only `README.md` and `AGENTS.md` changed in this session.
- Confirmation that commands and source-of-truth routing were preserved.

---

### Session 02 — SPEC and OUTPUTS clarification

**Files to inspect:**

- `SPEC.md`
- `OUTPUTS.md`
- `PRODUCT.md`
- `ARCHITECTURE.md`
- `docs/specs/selection_engine_spec.md`
- `docs/specs/reporting_outputs_spec.md`

**Files allowed to edit:**

- `SPEC.md`
- `OUTPUTS.md`

**Objective:**

Add narrow, non-breaking clarification that current technical contracts remain authoritative while product-facing docs may map them to new Portfolio MRI terminology.

Specifically:

- `Selection Engine`, `selection_decision.json`, and No-Trade artifact names remain current implementation/output contracts.
- Product-facing docs may describe the same decision layer as `Decision Verdict`.
- Advanced/backend generated artifacts may exist without becoming Core MVP UX.

**What to preserve:**

- Current implementation truth.
- All schemas.
- All generated output paths.
- All artifact names.
- All CLI commands and flags.
- All formulas, scoring rules, gates, statuses, and field names.
- Existing generated-vs-source boundaries.
- Existing JSON/cache default output policy.

**What to change:**

- Add a short clarification in the current-vs-target boundary section.
- Add a short clarification in generated output policy that product-facing naming does not rename output contracts.
- Label Health/Robustness/Selection/Monitoring artifacts as current generated/backend evidence where appropriate, not automatically Core MVP UI.

**What not to touch:**

- Do not make `SPEC.md` or `OUTPUTS.md` product-vision docs.
- Do not replace technical terms with product terms inside contracts.
- Do not rename `Selection Engine`, `selection_decision.json`, No-Trade artifacts, Health Score, Robustness Scorecard, or any generated output.
- Do not alter implementation status unless verified against specs/code.

**Verification command:**

```powershell
git status --short
git diff --stat -- SPEC.md OUTPUTS.md
git diff --name-only -- SPEC.md OUTPUTS.md
```

**Expected output:**

- A concise summary of the clarification added.
- Confirmation that no technical contract, schema, output name, CLI command, or generated artifact contract changed.
- Confirmation that `SPEC.md` and `OUTPUTS.md` still describe current implementation truth, not aspirational product behavior.

---

### Session 03 — GLOSSARY terminology alignment

**Files to inspect:**

- `GLOSSARY.md`
- `PRODUCT.md`
- `ARCHITECTURE.md`
- `SPEC.md`
- `docs/DIAGNOSTIC_PRODUCT_CONCEPT.md`

**Files allowed to edit:**

- `GLOSSARY.md`

**Objective:**

Make `GLOSSARY.md` the safe bridge between product-facing Portfolio MRI terminology and current technical implementation terms.

Terms to add or refine:

- `Decision Verdict`
- `Candidate Launchpad`
- `Portfolio Alternatives Builder`
- `Current vs Candidate Comparison`
- `Diagnosis-only State`
- `Reasonable paths to test`
- `Advanced / Later Product Backlog`

**What to preserve:**

- Existing technical terms.
- Existing aliases for current artifacts.
- Current implementation notes.
- Current-vs-target separation.

**What to change:**

- Clarify which terms are product-facing target language.
- Clarify which terms are current technical contracts.
- Add aliases where useful, for example: `Decision Verdict` maps conceptually to current Selection/No-Trade evidence but does not rename contracts.
- Prefer `reasonable paths to test` over recommendation-like wording.

**What not to touch:**

- No specs.
- No schemas.
- No output names.
- No historical decisions.

**Verification command:**

```powershell
git status --short
git diff --stat -- GLOSSARY.md
git diff --name-only -- GLOSSARY.md
```

**Expected output:**

- A concise terminology summary.
- Confirmation that `GLOSSARY.md` changed only as a terminology bridge.

---

### Session 04 — Detailed specs alignment scan

**Files to inspect:**

- `docs/specs/*.md`
- `SPEC.md`
- `OUTPUTS.md`
- `PRODUCT.md`
- `ARCHITECTURE.md`

Priority candidates for inspection:

- `docs/specs/selection_engine_spec.md`
- `docs/specs/candidate_factory_spec.md`
- `docs/specs/candidate_portfolios_spec.md`
- `docs/specs/portfolio_health_score_spec.md`
- `docs/specs/robustness_scorecard_spec.md`
- `docs/specs/assumption_sensitivity_spec.md`
- `docs/specs/pareto_dominance_spec.md`
- `docs/specs/regret_analysis_spec.md`
- `docs/specs/tradeoff_and_model_risk_spec.md`
- `docs/specs/macro_regime_spec.md`

**Files allowed to edit:**

- Only selected `docs/specs/*.md` files that contain product-facing contradictions.
- If no contradiction is found, edit nothing and produce an inspection report only.

**Objective:**

Inspect detailed specs for wording that could accidentally conflict with the new product direction, while preserving specs as current implementation contracts.

Focus only on preventing accidental product-facing confusion:

- optimizer-first framing;
- `best portfolio` wording as product promise;
- automatic recommendation framing;
- batch candidate generation described as Core MVP UX;
- Advanced / Later modules implied as Core MVP;
- target modules implied as currently implemented without verification.

**What to preserve:**

- Current implementation contracts.
- Formulas.
- Schemas.
- Fields.
- Output paths.
- Gates.
- Statuses.
- Decision semantics.
- Module ownership.
- Existing tests and verification references.

**What to change:**

- Only small wording/status notes where needed.
- Use wording such as: `This spec documents current/advanced backend artifacts. Product Core MVP exposure is governed by PRODUCT.md and ARCHITECTURE.md.`
- Keep technical names when they are actual contract names.

**What not to touch:**

- Do not turn specs into product documents.
- Do not rename technical contracts.
- Do not alter any formula, field, status, artifact, path, schema, or implementation semantics.
- Do not demote implemented backend capabilities merely because they are not Core MVP UX.

**Verification command:**

```powershell
git status --short
git diff --stat -- docs/specs
git diff --name-only -- docs/specs
```

Optional red-flag search:

```powershell
rg -n -i --glob "*.md" --glob "!tmp/**" --glob "!.venv/**" --glob "!pdf_md_sources/**" "black-box optimizer|best portfolio|automatic recommendation|optimizer-first|automatic batch|Macro Dashboard|Portfolio Health Score|Robustness Score|AI.*calculation|AI.*decision" docs/specs
```

**Expected output:**

- Either a no-edit inspection report or a small list of precise wording-only changes.
- Confirmation that specs still describe current implementation truth.
- Confirmation that no contracts changed.

---

### Session 05 — Historical docs classification

**Files to inspect:**

- `CHANGELOG.md`
- `docs/exec_plans/*.md`
- `docs/audits/*.md`
- `docs/archive/*`
- `docs/exec_plans/README.md`
- `docs/audits/README.md`

**Files allowed to edit:**

- Prefer only register/index files:
  - `CHANGELOG.md`
  - `docs/exec_plans/README.md`
  - `docs/audits/README.md`
- Do not edit individual historical plans/audits/archive files unless explicitly approved.

**Objective:**

Make clear that historical docs are evidence/reference records and do not override current product direction.

**What to preserve:**

- Historical entries.
- Old decisions and rationale.
- Completed session records.
- Audit evidence.
- Archive contents.

**What to change:**

- If needed, add short classification notes at the top/register level:
  - older audits are snapshot-at-time evidence;
  - completed ExecPlans are planning memory;
  - archived docs are legacy references;
  - current product direction is owned by active canonical docs.
- Optionally add a `CHANGELOG.md` entry for the documentation migration if project policy requires it.

**What not to touch:**

- Do not rewrite history.
- Do not normalize old wording inside completed records.
- Do not delete archive files.
- Do not convert old plans into current roadmap.

**Verification command:**

```powershell
git status --short
git diff --stat -- CHANGELOG.md docs/exec_plans/README.md docs/audits/README.md
git diff --name-only -- CHANGELOG.md docs/exec_plans/README.md docs/audits/README.md
```

**Expected output:**

- A short summary of classification notes added, or a no-edit finding if register-level notes are already sufficient.
- Confirmation that historical content was not rewritten.

---

### Session 06 — Final documentation consistency audit

**Files to inspect:**

- Active root Markdown docs.
- `docs/DIAGNOSTIC_PRODUCT_CONCEPT.md`.
- `docs/specs/*.md`.
- Register files under `docs/exec_plans/` and `docs/audits/`.
- `docs/archive/*` only as legacy reference.

**Files allowed to edit:**

- None by default.
- Create or update a final audit note only if explicitly requested.

**Objective:**

Confirm the documentation set is consistently aligned after the patch sessions.

Check that:

- Advanced / Later items are not described as Core MVP.
- Target modules are not described as implemented without verification.
- AI is not described as calculation or decision source.
- Product-facing docs do not promise `best portfolio` or automatic recommendations.
- Candidate portfolios remain investment hypotheses.
- Current implementation remains separated from target architecture.
- Technical/spec docs still state implementation truth.
- No broken links were introduced.

**What to preserve:**

- All implementation contracts.
- All historical records.
- All generated-output boundaries.
- All source-of-truth routing.

**What to change:**

- No changes unless the user explicitly asks to create a final audit file or patch a discovered issue.

**What not to touch:**

- No code.
- No configs.
- No generated files.
- No JSON/PDF/image/cache/data files.
- No schemas or output contracts.

**Verification command:**

```powershell
git status --short
git diff --stat
git diff --name-only
```

Suggested red-flag search:

```powershell
rg -n -i --glob "*.md" --glob "!tmp/**" --glob "!.venv/**" --glob "!.pytest_cache/**" --glob "!pdf_md_sources/**" "black-box optimizer|best portfolio|automatic recommendation|optimizer-first|automatic batch|AI.*calculation|AI.*decision|Macro Dashboard as Core MVP|Portfolio Health Score.*main product output|Robustness Score.*main product output" .
```

Suggested link sanity check:

```powershell
# Use existing project link-check method if available.
# Otherwise run a narrow Markdown link check over active docs only.
```

**Expected output:**

- Final consistency summary.
- List of remaining warnings, if any.
- Confirmation that no unintended files changed.

## 4. Patch Priority

| Session | Priority | Reason |
| --- | --- | --- |
| Session 01 — README and AGENTS positioning cleanup | Required now | These files are high-visibility entry points and still carry legacy-heavy positioning. |
| Session 02 — SPEC and OUTPUTS clarification | Required now | Prevents product-facing terminology from being mistaken for schema/output migration while preserving implementation truth. |
| Session 03 — GLOSSARY terminology alignment | Recommended | Helps keep new and old terms understandable without renaming contracts. |
| Session 04 — Detailed specs alignment scan | Recommended | Important for preventing contradictions, but must be conservative and contract-preserving. |
| Session 05 — Historical docs classification | Optional later | Useful for readers, but historical files should not be rewritten unless needed. |
| Session 06 — Final documentation consistency audit | Required after patch sessions | Confirms the documentation set is safe and aligned after changes. |

## 5. Risk Matrix

| Session | Risk | Why |
| --- | --- | --- |
| Session 01 | Medium | `README.md` and `AGENTS.md` are project entry points; bad wording could mislead users or agents. |
| Session 02 | High | `SPEC.md` and `OUTPUTS.md` are implementation/output source-of-truth docs; accidental product rewrites could corrupt current contracts. |
| Session 03 | Low | `GLOSSARY.md` is terminology-only if aliases and current-vs-target notes are preserved. |
| Session 04 | High | Detailed specs own formulas, schemas, fields, gates, and artifact contracts; edits must be wording-only and conservative. |
| Session 05 | Medium | Historical docs should not be rewritten; only register-level classification is safe by default. |
| Session 06 | Low | Audit-only by default; risk rises only if follow-up patches are made without approval. |

## 6. Verification Checklist

Run these checks for every patch session:

```powershell
git status --short
git diff --stat
git diff --name-only
```

Session-specific diff checks should use explicit pathspecs, for example:

```powershell
git diff --stat -- README.md AGENTS.md
git diff --name-only -- README.md AGENTS.md
```

Optional Markdown link check:

```powershell
# Use existing project link-check method if one exists.
# If not, run a narrow local Markdown link sanity check over active docs only.
```

Each session must confirm:

- no code files changed;
- no config files changed;
- no generated output files changed;
- no cache/data files changed;
- no JSON/PDF/image files changed;
- no CLI behavior changed;
- no JSON schemas changed;
- no generated output contracts changed;
- no public fields, commands, or generated artifact names changed;
- `SPEC.md`, `OUTPUTS.md`, and `docs/specs/*.md` still describe current implementation truth, not aspirational product behavior.

For this plan-creation task specifically, expected verification is:

```powershell
git status --short
git diff --stat -- DOCUMENTATION_ALIGNMENT_PATCH_PLAN.md
git diff --name-only -- DOCUMENTATION_ALIGNMENT_PATCH_PLAN.md
```

Expected result:

- Only `DOCUMENTATION_ALIGNMENT_PATCH_PLAN.md` is new/changed by this task.
- Pre-existing unrelated dirty files may remain, but must not be touched.

## 7. Commit Strategy

Recommended commits:

1. `docs: add documentation alignment patch plan`
   - Include only `DOCUMENTATION_ALIGNMENT_PATCH_PLAN.md`.

2. `docs: align README and agent positioning`
   - Include only `README.md` and `AGENTS.md`.

3. `docs: clarify decision terminology and output boundaries`
   - Include only `SPEC.md`, `OUTPUTS.md`, and optionally `GLOSSARY.md` if Session 03 is bundled with Session 02.

4. Optional later commit: `docs: clarify advanced spec exposure`
   - Include only selected `docs/specs/*.md` files with conservative wording-only clarifications.

5. Optional later commit: `docs: mark historical planning records as reference`
   - Include only `CHANGELOG.md`, `docs/exec_plans/README.md`, and/or `docs/audits/README.md` if register-level notes are added.

Do not use broad staging commands for these sessions:

```powershell
# Do not use:
git add -A
git add .
```

Use explicit pathspec staging only after user approval, for example:

```powershell
git add -- DOCUMENTATION_ALIGNMENT_PATCH_PLAN.md
```
