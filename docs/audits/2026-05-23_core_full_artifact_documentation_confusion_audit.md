# Core / Full Mode, Artifacts, and Documentation Confusion Audit

Date: 2026-05-23  
Scope: portfolio-first path, Blocks 1–5, `core` vs `full`, JSON vs presentation exports, `run_optimization.py` vs `run_portfolio_review.py`, `candidate_factory_run.json` vs `candidate_comparison.json`, stale on-disk artifacts.  
Method: read-only review of current code, canonical docs/specs, and existing generated artifacts under `Main portfolio/` (no reruns, no code changes, no artifact refresh).

**Not verified in this session:** live CLI execution, full `git status` vs workspace snapshot, byte-level PDF timestamps vs JSON `generated_at`, every optimizer candidate folder freshness, and whether `output_manifest.json` is absent due to an old partial run vs a code-path gap.

---

## Executive summary

The **code** for portfolio-first review is coherent: `run_portfolio_review.py` materializes `analysis_subject`, runs a scoped factory (`core_v1` or `default_v1`), then compares via `--then-compare`, defaulting to `site_api` (JSON/cache only, no PDF). Confusion comes mainly from **(a)** multiple coexisting artifact trees at `Main portfolio/` (legacy policy root vs `analysis_subject/` vs decision JSON), **(b)** comparison ingesting **all** product-menu candidates from disk while the last factory run may be **core-only with snapshot reuse**, and **(c)** docs/audits that describe full-menu or export-heavy runs while the routine command and default profile do not produce those artifacts.

---

## 1. What does the code actually do?

### Portfolio-first orchestration

| Step | Stage | Entry | Output (typical) |
| --- | --- | --- | --- |
| 1 | `diagnosis` | `run_report.py --materialize-analysis-subject --output-profile site_api` | `{output_dir_final}/analysis_subject/*` JSON (+ cache) |
| 2 | `candidates` | `run_candidate_factory.py --profile <core_v1\|default_v1> --execution-mode standard --then-compare` | `candidate_factory_run.json`, per-candidate folders, then comparison chain |
| 3 | `comparison` | (usually embedded in step 2) | `candidate_comparison.json` + decision-package JSON |
| 4 | `action` | `rebuild_pdf_reports.py --portfolio-first` | Only if `--with-pdf` / `--legacy-full-pdf` |

Source: `src/portfolio_review_workflow.py` (`build_portfolio_review_plan`). **`run_optimization.py` is not called.**

### Mode mapping

| CLI `--mode` | Factory profile | Candidate count (ordered menu) |
| --- | --- | --- |
| `core` (default) | `core_v1` | 6 (benchmarks + risk budgets) |
| `full` | `default_v1` | 16 (+ classic optimizers + robust suite) |

Source: `src/candidate_factory.py` — `REVIEW_MODE_PROFILES`, `CORE_V1_CANDIDATE_ORDER`, `DEFAULT_V1_CANDIDATE_ORDER`.

### Output profile

Default: `site_api` — JSON contracts + cache; **no** CSV/TXT/HTML/PNG/PDF unless `full_report`, `legacy_export`, or explicit PDF flags.  
`write_output_manifest()` exists in `run_report.py`, `candidate_factory.py`, and `candidate_comparison.py` (`src/output_policy.py`).

### Blocks 1–5 in code (orchestrator view)

| Block | Product meaning (docs) | Code locus |
| --- | --- | --- |
| 1 | Input & assumptions | Config validation, `analysis_subject` resolution, `run_metadata.json` |
| 2 | Portfolio X-Ray | `portfolio_xray.json` via report pipeline |
| 3 | Stress Lab | `stress_report.json` via report pipeline |
| 4 | Candidate Factory | `run_candidate_factory.py` → `candidate_factory_run.json` |
| 5 | Optimization Engine (candidates) | Optimizer/robust builders in `default_v1` only; readiness in comparison rows |

Blocks 1–3 run **once** on `analysis_subject` before candidates. A default **`core`** review does **not** execute Block 5 classic optimizers unless those folders already exist on disk from an earlier run.

### `candidate_factory_run.json` vs `candidate_comparison.json`

| File | Role | Written by |
| --- | --- | --- |
| `candidate_factory_run.json` | Factory orchestration evidence: profile, per-step status (`succeeded`, `skipped_existing`, …), timing, paths to comparison outputs | `write_candidate_factory_outputs()` in `src/candidate_factory.py` |
| `candidate_comparison.json` | Aggregated multi-candidate diagnostic table, `candidate_menu`, `review_bundle_context`, baseline `analysis_subject` row; feeds scorecard/selection/etc. | `write_candidate_comparison_outputs()` in `src/candidate_comparison.py` (factory `--then-compare` or `run_compare_variants.py`) |

Comparison **reads** factory JSON for freshness/disclosure and **scans candidate artifact roots on disk** — it is not limited to factory steps from the latest run.

---

## 2. What do the docs say?

| Document | Key claims |
| --- | --- |
| `SPEC.md` | Portfolio-first is canonical; `run_portfolio_review.py` default; legacy `run_optimization.py` compatibility only; Blocks 1–5 reliability plan referenced |
| `OUTPUTS.md` | `site_api` default; JSON is machine-readable source of truth; presentation formats export-only; Blocks 1–5 acceptance table under `analysis_subject/` + factory/comparison JSON |
| `docs/specs/portfolio_review_workflow_spec.md` | Command matrix for core/full/resume/PDF; `candidate_menu` on comparison; no policy optimizer in default orchestrator |
| `docs/specs/reporting_outputs_spec.md` | JSON authoritative; TXT/PDF summaries are projections; portfolio-first skips PDF unless flags set |
| `README.md` | Blocks 1–5 MVP; routine `run_portfolio_review.py --mode core`; legacy optimize separate |
| `WORKFLOW.md` | Generic process; **no** step-by-step portfolio-first operator path (only deferred full-factory note) |
| `AGENTS.md` | Same entrypoints as SPEC; inspect `analysis_subject/` first |
| `docs/operational_runbook.md` | §8.5 partial menu / core vs full; read `candidate_menu` before trusting rankings |
| `docs/audits/2026-05-22_blocks_1_5_verification_report.md` | Artifact YES/PARTIAL matrix; item 20 references **16-candidate** factory evidence |
| `docs/audits/2026-05-23_blocks_1_5_*_walkthrough.md` | Code-accurate core path; explicit “core does not prove full” |

Product block names in `README.md` (Input, X-Ray, Stress, Factory, Optimization Engine) align with exec plan `docs/exec_plans/2026-05-21_blocks_1_5_mvp_core_reliability_plan.md`.

---

## 3. Where do code and docs disagree?

| Topic | Code / disk behavior | Doc or operator expectation | Severity |
| --- | --- | --- | --- |
| **Subject location** | Portfolio-first diagnostics live under `analysis_subject/` | `OUTPUTS.md` also lists `stress_report.json`, `portfolio_xray.json` at `output_dir_final` root (legacy policy path) | High — two “Main” portfolios |
| **Routine factory profile** | Review default → `core_v1` | `OUTPUTS.md` command matrix line 28 shows `run_candidate_factory.py --profile default_v1` as “Candidate factory site/API” | Medium |
| **Blocks 1–5 boundary** | `--then-compare` always writes selection/action/journal JSON | Audits and walkthroughs say Blocks 1–5 exclude decision layer; files still appear in `comparison_outputs` | Medium — scope blur |
| **Verification report vs disk** | On-disk `candidate_factory_run.json`: `factory_profile_id: core_v1`, 6 steps, all `skipped_existing` | Verification report §20 cites “fresh **16-candidate** factory run” | High if report read as current state |
| **`output_manifest.json`** | Code writes manifest after report/factory/compare | Documented in `OUTPUTS.md` / workflow spec; **missing** under `Main portfolio/` on inspected disk | Medium — not verified whether last run skipped writers |
| **PDF after review** | Default `skip_pdf=True` | `.cursor/rules/portfolio_run_scope.mdc` still tells agents to ensure PDFs rebuilt after every successful run | Medium — agent/operator drift |
| **ARCHITECTURE candidate flow** | Portfolio-first compares `analysis_subject` vs candidates | § “Candidate Flow” step 5: “Compare candidate against **policy** and other variants” | Low–medium |
| **`run_result.json` at Main root** | `run_context: optimization`, weights differ from `analysis_subject` | Portfolio-first docs say inspect `analysis_subject` first; root artifacts not marked “legacy only” in folder | High |

---

## 4. Where do old artifacts on disk create misleading conclusions?

Evidence: `Main portfolio/` as of audit date (2026-05-22 factory/comparison timestamps).

### 4.1 Dual portfolio at `Main portfolio/` root

| Artifact | Indicates | Risk |
| --- | --- | --- |
| `analysis_subject/run_metadata.json` + weights | User **current** portfolio (e.g. SPY 10%, …) | Correct baseline for portfolio-first |
| `run_result.json` + `portfolio_weights.yml` | **Legacy policy optimizer** weights (e.g. SPY 7.2%, BIL 10%) | Misread as “the” reviewed portfolio |
| Root `portfolio_xray.json`, `stress_report.json`, `run_metadata.json` | Policy-era full report tree | Confused with subject diagnostics |

### 4.2 Core factory run + full-menu comparison

| Field | Value |
| --- | --- |
| `candidate_factory_run.json` → `factory_profile_id` | `core_v1` |
| Factory steps | 6 × `skipped_existing` / `reused_existing_snapshot` |
| `candidate_comparison.json` → `candidates` length | **19** rows (`analysis_subject`, legacy `policy`/`current`, 6 core + 10 optimizer/robust ids) |
| `candidate_menu` | `review_mode: core`, `intended_menu_size: 6`, `product_menu_scored_count: 16`, `is_partial_menu: true` |

**Misleading conclusion:** “Last review scored 16/18 candidates” or optimizer rankings reflect the latest factory run — they largely reflect **reused snapshots** from prior full/legacy runs.

### 4.3 Presentation files under `site_api` subject path

`analysis_subject/` contains `commentary.txt`, `report.html`, `rolling_factor_betas_*.png`, etc. Default `site_api` should not write these on a fresh run. **Likely stale** from earlier `full_report` / `legacy_export` runs.  
Workspace `git status` shows widespread `pdf files/` and variant-folder modifications while routine review is JSON-only — **PDFs can contradict latest JSON**.

### 4.4 Optimizer variant folders

Folders such as `minimum cvar constrained portfolio/`, `hierarchical risk parity portfolio/` show modified reports in git status while last factory run was `core_v1` with reuse — disk is a **museum** of runs, not a single coherent review generation.

---

## 5. Where can users confuse `core` with `full`?

| Trap | Why |
| --- | --- |
| Default CLI is `core` | Users expect “full product” from `python run_portfolio_review.py` |
| `candidate_menu.product_menu_*` vs `intended_menu_*` | Both appear in comparison; scored count can be 16 while factory ran 6 |
| `is_partial_menu: true` buried at end of large JSON | Easy to miss without runbook §8.5 |
| `--skip-existing` default | Core run completes fast with **zero** rebuilt steps; feels “done” while evidence is old |
| Audits citing 16-candidate success | Implies full Block 5 proof; disk may be core + reuse |
| `--resume-candidates` documented for full | Correct, but reinforces that core is the silent default |

**Code is explicit; UX and artifact surfaces are not.**

---

## 6. JSON vs PDF / TXT / CSV — confusion points

| Layer | Source of truth (docs) | Common mistake |
| --- | --- | --- |
| Formulas / gates | `docs/specs/*.md` | Treating commentary prose as binding |
| Machine workflow | JSON (`stress_report.json`, `candidate_comparison.json`, …) | Reading `commentary.txt` or PDF KPIs as canonical |
| Human / client | PDF via `pdf_md_sources/` + `rebuild_pdf_reports.py` | Assuming PDF exists after default review (it does not) |
| Tabular audit | CSV under `results_csv/` | Expecting CSV after `site_api` (export-only) |
| Summaries | `decision_package_summary.txt`, `*.txt` sidecars | Treating as authoritative over JSON (spec says JSON wins) |

**Extra trap:** subject folder contains TXT/HTML/PNG from older exports while operators believe “JSON-only run = JSON-only folder.”

---

## 7. Legacy policy optimization vs portfolio-first review

| Dimension | `run_portfolio_review.py` | `run_optimization.py` |
| --- | --- | --- |
| Purpose | Diagnose `analysis_subject`, build/compare **non-policy** candidates | Legacy **policy** max-return optimization + release gate |
| Weights source | `config.analysis_subject` (or resolved subject) | Optimizer → `portfolio_weights.yml` |
| Main artifacts | `analysis_subject/`, factory/comparison JSON | `run_result.json`, `portfolio_weights.yml`, root stress/xray when `--with-report` |
| Default report | Materialize subject (`site_api`) | No report unless `--with-report` |

Docs (`SPEC.md`, `OUTPUTS.md`, `README.md`) state portfolio-first is default; **coexistence on disk** reverses that story unless operators follow runbook ordering.

`candidate_comparison.json` still includes **`policy`** and **`current`** rows (legacy compatibility), reinforcing a three-way mental model (subject / policy / candidates) that portfolio-first spec de-emphasizes.

`review_bundle_context.mode_subject_consistency` correctly warns when `analysis_mode=optimize_from_universe` but subject is `current_portfolio` — easy to ignore in a 24k-line JSON file.

---

## 8. Top 5 confusion sources

1. **Two portfolios at `Main portfolio/`** — `analysis_subject/` vs root `run_result.json` / policy xray-stress (different weights).
2. **Comparison menu wider than last factory run** — `core_v1` + reuse vs 16+ scored rows including optimizers from disk.
3. **`site_api` default vs presentation files on disk** — JSON-only command does not imply JSON-only folders; PDFs/TXT/HTML may be stale.
4. **`candidate_factory_run.json` vs `candidate_comparison.json`** — factory describes last orchestration; comparison describes aggregated evidence (not the same scope).
5. **Blocks 1–5 vs decision package** — same command produces `selection_decision.json` etc., while audits say “Blocks 1–5 only”; docs disagree on what “the run” includes.

---

## 9. Minimal fixes (documentation and workflow only — no code)

| Priority | Action |
| --- | --- |
| P0 | Add a **“Read this first”** box to `OUTPUTS.md` and `docs/operational_runbook.md`: portfolio-first baseline = `analysis_subject/`; root `run_result.json` / `portfolio_weights.yml` = legacy policy only; do not mix. |
| P0 | Add **operator checklist** to `WORKFLOW.md` (or extend runbook §0): command used (`--mode core\|full`), `factory_profile_id`, `candidate_menu.is_partial_menu`, `factory_execution_summary.reused_existing`, then open comparison. |
| P1 | Fix **stale audit wording**: `2026-05-22_blocks_1_5_verification_report.md` §20 — qualify “16-candidate” as snapshot-at-write-time or re-verify against current `candidate_factory_run.json`. |
| P1 | `OUTPUTS.md` command matrix: split **“factory standalone (full menu)”** vs **“review default (core)”** commands. |
| P1 | Register this audit in `docs/audits/README.md`; mark verification report “Active input” with caveat that disk may lag. |
| P2 | `ARCHITECTURE.md` candidate flow bullet — “policy” → “analysis_subject and candidates (legacy policy row optional).” |
| P2 | `.cursor/rules/portfolio_run_scope.mdc` — note PDF rebuild applies when `--with-pdf` / export profile used, not default `site_api` review. |
| P2 | `AGENTS.md` / `README.md` — one line: default run does **not** refresh `pdf files/`. |
| P3 | Glossary entry: **Blocks 1–5 deliverable** vs **decision package** (same CLI, different audit scope). |

Optional hygiene (not doc): operator run with `--no-skip-existing` when changing inputs; archive or label stale variant folders — **out of scope** for this audit per user rules.

---

## 10. Quick reference — what to open for each question

| Question | Open first |
| --- | --- |
| What portfolio was diagnosed? | `Main portfolio/analysis_subject/run_metadata.json` |
| Last factory scope? | `Main portfolio/candidate_factory_run.json` → `factory_profile_id`, `steps[]` |
| Is menu partial / reused? | `Main portfolio/candidate_comparison.json` → `candidate_menu`, `review_bundle_context` |
| Policy optimizer output? | `Main portfolio/run_result.json` (legacy; not subject) |
| Client PDF current? | Only if `run_portfolio_review.py --with-pdf` or rebuild was run after JSON |

---

## Remediation status

**Closed:** 2026-05-24 (ExecPlan Sessions 01–06, `RM-1101`–`RM-1106`).  
**Scope delivered:** documentation and agent rules only — no Python, JSON contract, or on-disk artifact refresh.

| Audit §9 priority | Action | Status | Session / deliverable |
| --- | --- | --- | --- |
| P0 | «Read this first» — subject vs legacy policy root; stale exports | Done | 01 — [OUTPUTS.md](../../OUTPUTS.md), [operational_runbook.md](../operational_runbook.md) §0.1 |
| P0 | Portfolio-first operator checklist | Done | 02 — [WORKFLOW.md](../../WORKFLOW.md), runbook §8 cross-links |
| P1 | Verification report §20 snapshot caveat | Done | 03 — [Blocks 1–5 verification report](2026-05-22_blocks_1_5_verification_report.md) |
| P1 | Command matrix: core review vs standalone `default_v1` factory | Done | 03 — [OUTPUTS.md](../../OUTPUTS.md), [README.md](../../README.md) |
| P1 | Audit register + verification report disk caveat | Done | 00, 03 — [audits/README.md](README.md) |
| P2 | ARCHITECTURE candidate flow (`analysis_subject` baseline) | Done | 04 — [ARCHITECTURE.md](../../ARCHITECTURE.md) |
| P2 | Agent rule: PDF rebuild not default for `site_api` review | Done | 04 — [.cursor/rules/portfolio_run_scope.mdc](../../.cursor/rules/portfolio_run_scope.mdc) |
| P2 | AGENTS / README: default run does not refresh `pdf files/` | Done | 03–04 — [AGENTS.md](../../AGENTS.md), [README.md](../../README.md) |
| P3 | Glossary + spec cross-links (Blocks 1–5 vs decision package; factory vs comparison) | Done | 05 — [GLOSSARY.md](../../GLOSSARY.md), specs, walkthroughs, [SPEC.md](../../SPEC.md) pointer |

**Follow-up ExecPlan:** [Core / Full Artifact and Documentation Confusion Remediation](../exec_plans/2026-05-23_core_full_artifact_documentation_confusion_plan.md) — **Completed** 2026-05-24.

**Still out of scope (unchanged):** product/code fixes (comparison registry filter, orchestrator manifest on every path, stale export cleanup on disk). Operators should continue to use §10 quick reference and runbook §0.1 / §8 before trusting rankings or PDFs.

**Verification:** `python scripts/verify_docs.py` — OK after each session; final closure Session 06.

---

## Related audits

- [2026-05-23 Blocks 1–5 actual algorithm walkthrough](2026-05-23_blocks_1_5_actual_algorithm_walkthrough.md)
- [2026-05-23 Blocks 1–5 manual algorithm walkthrough](2026-05-23_blocks_1_5_manual_algorithm_walkthrough.md)
- [2026-05-22 Blocks 1–5 verification report](2026-05-22_blocks_1_5_verification_report.md) — treat factory scope claims as **verify against disk**
- [2026-05-21 Blocks 1–5 deep audit snapshot](2026-05-21_blocks_1_5_deep_audit_snapshot.md)
