# Dirty Tree Cleanup Plan

Date: 2026-05-25  
Mode: audit and planning only. No staging, commits, deletes, or cleanup performed.  
Context: Post–architecture-alignment roadmap (Sessions 01–12) is **Completed**; the working tree still mixes uncommitted docs, migration artifacts, generated outputs, config/provider work, and phantom dirty flags.

Related inputs:

- Prior classification: [DIRTY_TREE_CLASSIFICATION.md](DIRTY_TREE_CLASSIFICATION.md) (2026-05-25; partially stale counts)
- Closure: [docs/audits/2026-05-25_post_architecture_alignment_session12_closure_report.md](docs/audits/2026-05-25_post_architecture_alignment_session12_closure_report.md)
- ExecPlan: [docs/exec_plans/2026-05-25_post_architecture_alignment_roadmap.md](docs/exec_plans/2026-05-25_post_architecture_alignment_roadmap.md)

---

## Git snapshot (this audit)

Commands run:

```text
git status --short
git diff --stat
git diff --name-only
git diff --cached --name-only
```

| Metric | Value |
| --- | --- |
| Total dirty entries | **347** |
| Modified tracked (`M`) | **319** |
| Untracked (`??`) | **28** |
| Staged (`git diff --cached --name-only`) | **0** |
| `git diff --stat` | **315 files**, +107 867 / −656 429 lines (dominated by generated `stress_report.json` shrink/rewrite and portfolio reruns) |

**Important:** Diagnosis-first adapter **source modules and migration tests are already tracked in git and are not dirty** (e.g. `src/problem_classification.py`, `src/candidate_launchpad.py`, `run_report.py`, `tests/test_problem_classification.py`). The remaining dirty tree is mostly **docs alignment**, **generated portfolio/PDF artifacts**, **IBKR/provider wiring**, and **uncommitted planning/spec files**.

---

## Summary by category

| # | Category | Count | Risk |
| --- | --- | ---: | --- |
| 1 | Safe to keep — architecture / migration docs & alignment | **37** | Low–Medium |
| 2 | Generated outputs / artifacts | **292** | High if staged with source |
| 3 | Config / environment | **3** | High |
| 4 | Provider / IBKR / data-source | **9** | High |
| 5 | Test changes (provider-related only; migration tests clean) | **3** | Medium |
| 6 | Documentation still pending commit | **36** (+ this plan) | Low |
| 7 | Unknown / requires human review | **4** | Medium |
| — | **Total** | **347** (+ `DIRTY_TREE_CLEANUP_PLAN.md` when saved) | — |

Counts treat folder groups as enumerated in detail below. Overlap: bucket 6 files are a subset of bucket 1 pending docs.

---

## 1. Safe to keep and commit as architecture / migration work

These belong to Portfolio MRI documentation alignment, code-migration planning, or a small `core_fast` runtime doc/code consistency fix. **Commit in one or two allowlisted docs commits**, separate from generated outputs and provider work.

### 1A. Root source-of-truth docs (modified, uncommitted)

| Path | Why dirty | Recommended action | Risk |
| --- | --- | --- | --- |
| `ARCHITECTURE.md` | Sessions 02–11 diagnosis-first / implemented-vs-target reconciliation | Commit separately (docs commit 1) | Low |
| `BUSINESS_VISION.md` | Session 10 AI Commentary wording fix | Commit separately | Low |
| `GLOSSARY.md` | Session 10 grounding-context terms | Commit separately | Low |
| `OUTPUTS.md` | Sessions 05–07–11 output bundle + refresh policy + paths | Commit separately | Low |
| `PRODUCT.md` | Sessions 02–04–10 product boundary | Commit separately | Low |
| `README.md` | Sessions 02–03 command matrix + artifact list | Commit separately | Low |
| `SPEC.md` | Session 02 status matrix reconciliation | Commit separately | Low |
| `TESTING.md` | Session 06 post-architecture verification matrix | Commit separately | Low |
| `WORKFLOW.md` | Session 07 generated-output refresh policy pointer | Commit separately | Low |

### 1B. `docs/` alignment (modified)

| Path | Why dirty | Recommended action | Risk |
| --- | --- | --- | --- |
| `docs/DIAGNOSTIC_PRODUCT_CONCEPT.md` | Session 02/10 implementation status | Commit separately | Low |
| `docs/ROADMAP.md` | Sessions 08–10–12 closure + RM-ARCH backlog | Commit separately | Low |
| `docs/archive/documentation_migration_2026_05_25/LEGACY_DIAGNOSTIC_PRODUCT_CONCEPT.md` | Session 09 archive link fix | Commit separately | Low |
| `docs/audits/README.md` | Session 08/12 register update | Commit separately | Low |
| `docs/exec_plans/README.md` | Session 08/12 plan closure | Commit separately | Low |
| `docs/operational_runbook.md` | Session 03 `core_fast` command matrix | Commit separately | Low |
| `docs/specs/README.md` | Session 05 output categories | Commit separately | Low |
| `docs/specs/candidate_factory_spec.md` | Sessions 03–04 factory boundary | Commit separately | Low |
| `docs/specs/portfolio_review_workflow_spec.md` | Session 03 profile alignment | Commit separately | Low |
| `docs/specs/reporting_outputs_spec.md` | Session 05 bundle policy | Commit separately | Low |

### 1C. Planning / audits / ExecPlans / new specs (untracked)

| Path | Why dirty | Recommended action | Risk |
| --- | --- | --- | --- |
| `CODE_MIGRATION_PLAN.md` | Code migration planning artifact | Commit with migration/docs batch or after human review | Medium |
| `DIRTY_TREE_CLASSIFICATION.md` | Prior dirty-tree audit (2026-05-25) | Commit as process doc or supersede with this plan | Low |
| `docs/audits/2026-05-25_full_project_architecture_alignment_audit.md` | Origin audit | Commit (docs commit 2) | Low |
| `docs/audits/2026-05-25_code_migration_session01_runtime_inventory.md` | Migration inventory | Commit with migration docs | Medium |
| `docs/audits/2026-05-25_post_architecture_alignment_session12_closure_report.md` | Session 12 closure | Commit (docs commit 2) | Low |
| `docs/exec_plans/2026-05-25_post_architecture_alignment_roadmap.md` | Completed alignment ExecPlan | Commit (docs commit 2) | Low |
| `docs/exec_plans/2026-05-25_code_migration_to_diagnosis_first_portfolio_mri.md` | Code migration ExecPlan | Commit after review; may overlap CODE_MIGRATION_PLAN | Medium |
| `docs/specs/ai_commentary_grounding_spec.md` | New diagnosis-first spec | Commit (specs commit) | Low |
| `docs/specs/candidate_launchpad_spec.md` | New spec | Commit (specs commit) | Low |
| `docs/specs/current_vs_candidate_spec.md` | New spec | Commit (specs commit) | Low |
| `docs/specs/decision_verdict_spec.md` | New spec | Commit (specs commit) | Low |
| `docs/specs/light_monitoring_summary_spec.md` | New spec | Commit (specs commit) | Low |
| `docs/specs/portfolio_alternatives_builder_spec.md` | New spec | Commit (specs commit) | Low |
| `docs/specs/problem_classification_spec.md` | New spec | Commit (specs commit) | Low |
| `docs/specs/workflow_state_spec.md` | New spec | Commit (specs commit) | Low |

### 1D. Small runtime alignment (modified; content diff present)

| Path | Why dirty | Recommended action | Risk |
| --- | --- | --- | --- |
| `src/live_core_e2e.py` | `LIVE_CORE_FACTORY_PROFILE`: `core_v1` → `core_fast` (aligns with Session 03 docs) | Commit in small **runtime/docs parity** commit after review; not with IBKR bundle | Low |

**Suggested commit split for bucket 1:**

1. **Docs alignment commit:** §1A + §1B (21 files).
2. **Registers / audits / ExecPlan commit:** §1C audit + exec plan + closure (5 files).
3. **New specs commit:** §1C eight `docs/specs/*` files + optional planning files after review.
4. **Optional tiny code commit:** `src/live_core_e2e.py` only.

---

## 2. Generated outputs / artifacts

**Do not commit** with architecture migration unless an explicit generated-output refresh session approves it. These reflect local portfolio reruns, PDF rebuilds, and Python bytecode — not source-of-truth.

### 2A. Candidate portfolio folders (modified tracked — **205 files**)

Eight folders; typical artifacts per folder (~25–29 files): `baseline_weights_metadata.json`, `commentary.txt`, `data_policy.json`, `portfolio_xray.json`, regime summaries, `report.html` / `report.txt`, rolling beta HTML/PNG, `run_metadata.json`, scenario libraries, snapshots, `stress_commentary.txt`, `stress_report.json`, `summary.json` / `summary.txt`, weights (where present), drawdown JSON (where present).

| Folder | Modified files | Why dirty | Action | Risk |
| --- | ---: | --- | --- | --- |
| `hierarchical risk parity portfolio/` | 28 | Local report/stress rerun | Ignore / revert / refresh-only commit | High |
| `maximum diversification unconstrained portfolio/` | 29 | Same | Same | High |
| `minimum cvar constrained portfolio/` | 25 | Same | Same | High |
| `minimum cvar uncapped portfolio/` | 25 | Same | Same | High |
| `risk budget by asset portfolio/` | 24 | Same | Same | High |
| `risk budget by asset-class portfolio/` | 24 | Same | Same | High |
| `robust mean variance constrained portfolio/` | 25 | Same | Same | High |
| `robust mean variance uncapped portfolio/` | 25 | Same | Same | High |

**Note:** Large `stress_report.json` diffs (~74k lines removed per folder in `git diff --stat`) dominate repo noise.

### 2B. Untracked manifests inside portfolio folders (**3 files**)

| Path | Why dirty | Action | Risk |
| --- | --- | --- | --- |
| `hierarchical risk parity portfolio/candidate_manifest.json` | Factory/candidate run output | Do not stage with migration | High |
| `risk budget by asset portfolio/candidate_manifest.json` | Same | Same | High |
| `risk budget by asset-class portfolio/candidate_manifest.json` | Same | Same | High |

### 2C. PDF exports (**36 files**, `pdf files/*.pdf`)

All modified PDFs (Main, equal-weight, max diversification, min cvar, min variance, risk parity, robust MV variants). **Why:** PDF rebuild after report runs. **Action:** ignore / revert / separate export commit only if product requires. **Risk:** High.

### 2D. PDF Markdown sidecars (**28 files**, `pdf_md_sources/*`)

Pandoc sources for commentary, stress commentary, weights, decision package, IPS. **Action:** ignore / revert with PDFs. **Risk:** High.

### 2E. Python bytecode (**19 files**, `src/__pycache__/*.cpython-313.pyc`)

**Why:** import/run side effect. **Action:** ignore; ensure `.gitignore` covers `__pycache__/`; never stage. **Risk:** Medium.

### 2F. Run logs (**5 files**, untracked)

| Path | Why dirty | Action | Risk |
| --- | --- | --- | --- |
| `candidate_factory_session9_smoke.log` | Smoke run log | Ignore / delete locally later | Low |
| `candidate_factory_stderr.log` | Factory stderr capture | Ignore | Low |
| `candidate_factory_stdout.log` | Factory stdout capture | Ignore | Low |
| `portfolio_review_stderr.log` | Review stderr | Ignore | Low |
| `portfolio_review_stdout.log` | Review stdout | Ignore | Low |

**Bucket 2 total:** 205 + 3 + 36 + 28 + 19 + 5 = **296** (292 if excluding logs from “must not stage” strict artifact set).

---

## 3. Config / environment files

| Path | Why dirty | Recommended action | Risk |
| --- | --- | --- | --- |
| `config.yml` | Adds `market_data_provider: ibkr_yfinance_fallback` (local operator setting) | **Review manually**; do not commit local IBKR default with docs migration | **High** |
| `config.yml.example` | Documents `market_data_provider` enum | Review; commit **only** with approved provider feature commit | **High** |
| `requirements.txt` | Adds `ib_insync>=0.9.86` | Review; commit **only** with provider feature commit | **High** |

**Diff summary:** all three changes wire IBKR provider support; `config.yml` uses a non-default provider for this machine.

---

## 4. Provider / IBKR / data-source work

Separate from architecture docs migration. Commit only after dedicated review and tests.

| Path | Status | Why dirty | Recommended action | Risk |
| --- | --- | --- | --- | --- |
| `run_ibkr_market_data.py` | Untracked | New IBKR CLI entry | Review; separate provider commit or revert | **High** |
| `src/data_ibkr.py` | Untracked | IBKR data backend | Same | **High** |
| `src/data_provider.py` | Untracked | Provider abstraction + normalization | Same | **High** |
| `src/cache.py` | Modified | Cache keys include `data_provider` | Same | **High** |
| `src/config_schema.py` | Modified | `market_data_provider` field + validation | Same | **High** |
| `src/data_loader.py` | Modified | Routes loads through provider layer | Same | **High** |

**Dependency:** `config_schema.py` imports `src.data_provider` (untracked) — provider bundle must be committed atomically or reverted together.

---

## 5. Test changes

| Path | Belongs to | Why dirty | Recommended action | Risk |
| --- | --- | --- | --- | --- |
| `tests/test_data_cache_key.py` | **Provider / cache** | Expectations updated for `data_provider` in cache keys | Commit with provider bundle after review | Medium |
| `tests/test_data_ibkr.py` | **Provider / IBKR** | Untracked IBKR tests | Commit with provider bundle or drop | Medium |
| `tests/test_data_provider.py` | **Provider** | Untracked provider tests | Same | Medium |

**Migration adapter tests** (`tests/test_problem_classification.py`, `test_candidate_launchpad.py`, `test_current_vs_candidate.py`, `test_decision_verdict.py`, `test_ai_commentary_context.py`, `test_light_monitoring_summary.py`, `test_portfolio_alternatives_builder.py`, `test_workflow_state.py`): **not dirty** — already in git at HEAD.

---

## 6. Documentation still pending commit

All documentation changed during architecture alignment **remains uncommitted**. This overlaps bucket 1 but highlights **commit backlog**.

### Modified (21)

`ARCHITECTURE.md`, `BUSINESS_VISION.md`, `GLOSSARY.md`, `OUTPUTS.md`, `PRODUCT.md`, `README.md`, `SPEC.md`, `TESTING.md`, `WORKFLOW.md`, `docs/DIAGNOSTIC_PRODUCT_CONCEPT.md`, `docs/ROADMAP.md`, `docs/archive/documentation_migration_2026_05_25/LEGACY_DIAGNOSTIC_PRODUCT_CONCEPT.md`, `docs/audits/README.md`, `docs/exec_plans/README.md`, `docs/operational_runbook.md`, `docs/specs/README.md`, `docs/specs/candidate_factory_spec.md`, `docs/specs/portfolio_review_workflow_spec.md`, `docs/specs/reporting_outputs_spec.md`.

### Untracked (15 + this plan)

`CODE_MIGRATION_PLAN.md`, `DIRTY_TREE_CLASSIFICATION.md`, `DIRTY_TREE_CLEANUP_PLAN.md` (this file), three audits under `docs/audits/`, two ExecPlans under `docs/exec_plans/`, eight new specs under `docs/specs/`.

**Recommended action:** stage allowlisted paths only in §Safe staging candidates; verify `python scripts/verify_docs.py` and `tests/test_docs_links.py` before each docs commit.

---

## 7. Unknown / requires human review

| Path | Why dirty | Issue | Recommended action | Risk |
| --- | --- | --- | --- | --- |
| `src/action_engine.py` | Shows `M` in status | **`git diff` and `git diff HEAD` empty** — likely stat/timestamp/index noise on Windows | Run `git update-index --refresh`; if still `M`, compare `git diff --raw` or re-checkout; do not stage blindly | Medium |
| `src/candidate_comparison.py` | Same | Same | Same — file may already match HEAD; compare wiring vs Session 11 RM-ARCH-011 notes | Medium |
| `src/selection_engine.py` | Same | Same | Same | Medium |
| `src/data_trust_signals.py` | Same | Same | Same | Medium |

If these files truly match HEAD, **`git restore`** (or refresh) clears noise without losing work. If a merge/tool touched mtime only, no commit needed.

---

## Recommended cleanup order

1. **Commit or save remaining migration docs/specs** — use allowlisted paths in §Safe staging candidates; run `verify_docs.py` + `test_docs_links.py` before commit.
2. **Separate generated outputs and artifacts** — leave 292 generated/log/pycache paths unstaged; optionally `git restore` portfolio/PDF folders after backing up if disk cleanliness is needed (human decision; not done in this audit).
3. **Review config/environment changes** — decide whether `config.yml` local IBKR setting should be reverted to `yfinance` before any commit; keep `config.yml.example` + `requirements.txt` with provider commit only.
4. **Review provider/IBKR/data-source changes separately** — one atomic commit for `src/data_provider.py`, `src/data_ibkr.py`, `run_ibkr_market_data.py`, `src/cache.py`, `src/config_schema.py`, `src/data_loader.py`, provider tests, and approved config/example/requirements — **or revert entire provider bundle**.
5. **Fix remaining blockers** — after tree is logically clean: optional approved generated refresh for product-bundle JSON; separate ExecPlan for `RM-ARCH-011`; optional `git update-index --refresh` for phantom `M` files.

---

## Safe staging candidates

Exact paths safe to stage **later** for architecture/documentation work (still **do not stage now**):

```text
ARCHITECTURE.md
BUSINESS_VISION.md
GLOSSARY.md
OUTPUTS.md
PRODUCT.md
README.md
SPEC.md
TESTING.md
WORKFLOW.md
docs/DIAGNOSTIC_PRODUCT_CONCEPT.md
docs/ROADMAP.md
docs/archive/documentation_migration_2026_05_25/LEGACY_DIAGNOSTIC_PRODUCT_CONCEPT.md
docs/audits/README.md
docs/audits/2026-05-25_full_project_architecture_alignment_audit.md
docs/audits/2026-05-25_post_architecture_alignment_session12_closure_report.md
docs/audits/2026-05-25_code_migration_session01_runtime_inventory.md
docs/exec_plans/README.md
docs/exec_plans/2026-05-25_post_architecture_alignment_roadmap.md
docs/operational_runbook.md
docs/specs/README.md
docs/specs/candidate_factory_spec.md
docs/specs/portfolio_review_workflow_spec.md
docs/specs/reporting_outputs_spec.md
docs/specs/ai_commentary_grounding_spec.md
docs/specs/candidate_launchpad_spec.md
docs/specs/current_vs_candidate_spec.md
docs/specs/decision_verdict_spec.md
docs/specs/light_monitoring_summary_spec.md
docs/specs/portfolio_alternatives_builder_spec.md
docs/specs/problem_classification_spec.md
docs/specs/workflow_state_spec.md
DIRTY_TREE_CLEANUP_PLAN.md
src/live_core_e2e.py
```

**Stage after human review (planning overlap):**

```text
CODE_MIGRATION_PLAN.md
DIRTY_TREE_CLASSIFICATION.md
docs/exec_plans/2026-05-25_code_migration_to_diagnosis_first_portfolio_mri.md
```

---

## Do-not-stage list

**Never stage with architecture/docs migration** (`git add -A` forbidden):

### Folders (all contents)

```text
hierarchical risk parity portfolio/
maximum diversification unconstrained portfolio/
minimum cvar constrained portfolio/
minimum cvar uncapped portfolio/
risk budget by asset portfolio/
risk budget by asset-class portfolio/
robust mean variance constrained portfolio/
robust mean variance uncapped portfolio/
pdf files/
pdf_md_sources/
src/__pycache__/
```

### Logs

```text
candidate_factory_session9_smoke.log
candidate_factory_stderr.log
candidate_factory_stdout.log
portfolio_review_stderr.log
portfolio_review_stdout.log
```

### Config / provider (separate review commit or revert)

```text
config.yml
config.yml.example
requirements.txt
run_ibkr_market_data.py
src/data_ibkr.py
src/data_provider.py
src/cache.py
src/config_schema.py
src/data_loader.py
tests/test_data_cache_key.py
tests/test_data_ibkr.py
tests/test_data_provider.py
```

### Phantom-dirty until verified

```text
src/action_engine.py
src/candidate_comparison.py
src/selection_engine.py
src/data_trust_signals.py
```

---

## Blockers

| Blocker | Status | Notes |
| --- | --- | --- |
| **Stale generated outputs** | **Open** | On-disk portfolio/PDF artifacts do not reflect latest product-bundle policy (`problem_classification.json`, etc. under `analysis_subject/`). Requires **approved refresh session** per `OUTPUTS.md` / Session 07 policy — not a docs blocker. |
| **verify_docs / archive links** | **Closed** | `python scripts/verify_docs.py` → OK; `tests/test_docs_links.py` → 6 passed (verified this audit). |
| **RM-ARCH-010** (LLM AI Commentary spec) | **Open (backlog)** | Intentionally deferred; not a dirty-tree blocker. |
| **RM-ARCH-011** (product bundle runtime wiring) | **Open (backlog)** | Sidecar paths / ai_commentary inputs; separate implementation ExecPlan. |
| **config / IBKR review** | **Open** | `config.yml` points to `ibkr_yfinance_fallback`; provider modules untracked; must not ship accidentally with docs commit. |
| **Failing tests** | **Not observed** | Spot-check: docs links + problem_classification + test_data_cache_key → **14 passed**. Full suite not run in this audit. |
| **Uncommitted docs/specs** | **Open** | 36+ documentation files still dirty; blocks stable baseline until allowlisted commits. |
| **Dirty tree size** | **Open** | 347 entries; obscures attribution until split commits applied. |

---

## Post-audit verification (after creating this file only)

Re-run for report:

```text
git status --short   → 348 entries (347 prior + DIRTY_TREE_CLEANUP_PLAN.md)
git diff --stat      → unchanged except no new source edits
git diff --name-only → unchanged except this plan is untracked (not in diff until added)
```

**Next recommended action:** Human review → **Commit 1 (docs alignment, 21 modified paths in §1A–1B)** → **Commit 2 (audits + ExecPlan + closure + new specs)** → decide **revert vs provider commit** for §3–4 → leave §2 generated artifacts unstaged.
