# Product Flow MVP Demo Audit — Portfolio MRI

Date: 2026-05-26

Purpose: Controlled **live** backend demo audit for the diagnosis-first product journey with **one** factory hypothesis (`equal_weight`). This run is independent evidence from the Session 07 baseline snapshot and the 2026-05-25 validation audit closure.

Related:

- [Product-Flow Validation Audit](2026-05-25_product_flow_validation_audit.md) (closure context)
- [Product Flow Demo Baseline Snapshot](2026-05-25_product_flow_demo_baseline_snapshot.md) (prior disk evidence)
- [Product flow operator guide](../product_flow_operator_guide.md)

---

## 1. Executive Summary

| Question | Answer |
| --- | --- |
| Did the product flow run successfully... | **Yes (CLI exit 0).** Subject materialization, factory step, and compare/decision package completed in ~81 s. |
| Can this be demoed today... | **Partially.** The **diagnosis → problems → launchpad → six JSON bundle** story is demoable. The **“we tested Equal Weight and here is the verdict”** story is **not** honest on this disk without operator fixes. |
| What worked... | End-to-end orchestration; fresh subject X-Ray/stress; `problem_classification` + `candidate_launchpad` in sidecar; all six product JSON files present with stable `schema_version`; grounded `ai_commentary_context`; monitoring baseline written. |
| What failed... | **Compare/selection ignored the CLI hypothesis:** `current_vs_candidate.json` and `decision_verdict.json` feature **`risk_parity`**, not `equal_weight`, because compare ranked **12 stale variant folders** on disk. Factory only **reused** EW snapshot (`skipped_existing`). Root `output_manifest.json` is factory-only (no product-bundle index). |
| Strongest product output... | **`analysis_subject/problem_classification.json`** + **`candidate_launchpad.json`** — readable problems, evidence refs, launchpad cards tied to stress/X-Ray. |
| Still confusing / not product-ready... | Verdict layer contradicts `--candidates equal_weight`; `view_mode: one_candidate` with `selected_candidate_ids: ["risk_parity"]`; 23k-line `candidate_comparison.json` vs thin product bundle; internal codes (`DIAG_*`) still in technical JSON; no LLM commentary output (grounding only). |

**Bottom line:** Backend **can** run the flow and emit the six-file bundle, but **this run is not a clean Equal Weight demo** — it is a **bundle-contract + diagnosis demo** with a **stale multi-candidate verdict**. Do not tell stakeholders “Equal Weight won” from this run.

---

## 2. Command Run

| Field | Value |
| --- | --- |
| Exact command | `python run_portfolio_review.py --candidates equal_weight` |
| Working directory | Repository root (`D:\Desktop\CURSOR TULA DIAGNOSTICS`) |
| Exit code | **0** |
| Wall-clock duration | **~81.5 s** (`RUNTIME_SECONDS=81.4774805`) |
| Network / data access | **Required and used.** Monthly return cache loaded (9 tickers); daily cache for tail-risk; yfinance fallbacks and FRED risk-free (USD). Many non-fatal Yahoo “possibly delisted” warnings on long historical factor windows. |
| Workflow state (log) | `one_candidate` (`candidate_count=1`, `source=candidate_ids`) |
| Review mode | `core` (factory profile `explicit_list`) |
| PDF | Not refreshed (`site_api`; no `--with-pdf`) |

### Warnings / errors (non-fatal unless noted)

| Item | Severity | Detail |
| --- | --- | --- |
| Config placeholders | INFO | `max_single_security_weight_pct`, `min_single_security_weight_pct` awaiting user input |
| Yahoo historical factor pulls | Noise | Repeated failed downloads for DBC/GLD/SLV/BND/SCHD/SCHP/TLT on pre-inception windows |
| Factor beta overlay | INFO | Material raw-vs-adjusted PnL on `commodity_shock` / `recession_severe` historical episodes |
| Subject stress | Diagnostic | `DIAG_ATTENTION` / `DIAG_LOSS_RECESSION_SEVERE` on `recession_severe` |
| Factory | INFO | `equal_weight` → `skipped_existing` (reused fresh `equal-weight portfolio/snapshot_10y.json`) |
| Monitoring | Warning | `what_changed_summary.json` warns `monitoring_diff:prior_same_analysis_end_ignored` |

No run-stopping exception observed.

---

## 3. Product Flow Evidence

| Step | Status | Primary output file(s) | What the user would learn | Gap |
| --- | --- | --- | --- | --- |
| Current portfolio input | **pass** | `config.yml` → `analysis_subject/run_metadata.json` | 8-ticker USD current book; weights from `analysis_subject`; role `user_current_portfolio` | No UI; legacy policy trees still on disk elsewhere |
| Portfolio X-Ray | **pass** | `analysis_subject/portfolio_xray.json` | Allocation: ~42% fixed income, 40% equity, 18% commodity; top weight SCHD 17%; concentration flagged | Large technical JSON; not a single KPI card |
| Stress Test Lab | **pass** | `analysis_subject/stress_report.json`, `analysis_subject/snapshot_10y.json` | Worst synthetic loss **-22.2%** (`recession_severe`); status `DIAG_ATTENTION` | Codes not client-ready; file very large |
| Problem Classification | **pass** | `analysis_subject/problem_classification.json` | 3 problems; primary **weak crisis resilience** (high severity); current not acceptable | Some evidence `summary: null`; confidence often low |
| Candidate Launchpad | **pass** | `analysis_subject/candidate_launchpad.json` | 4 cards linking problems to test paths; EW listed under concentration/diversification cards | Cards do not auto-run factory; `requires_user_action: true` |
| Equal Weight candidate generation | **partial** | `candidate_factory_run.json`, `equal-weight portfolio/snapshot_10y.json` | EW exists at 12.5% per asset; factory step succeeded via reuse | **No rebuild** this run; compare did not select EW for product-facing compare |
| Current vs Candidate Comparison | **fail** (demo intent) | `current_vs_candidate.json` | Side-by-side deltas vs **Risk Parity**, not Equal Weight | **`selected_candidate_ids`: `["risk_parity"]`** despite CLI |
| Decision Verdict | **partial** | `decision_verdict.json` | `rebalance_to_selected_candidate` for **Risk Parity**; no-trade evaluated, not applied | Misaligned with `--candidates equal_weight` |
| AI Commentary grounding | **pass** | `ai_commentary_context.json` | Strict allow-list, forbidden claims, evidence refs to diagnosis + verdict | **No generated prose**; cites RP verdict not EW hypothesis |
| Monitoring / What Changed | **partial** | `what_changed_summary.json`, `monitoring_diff.json` | First baseline stored; rebalance trigger true | No prior period diff; warning on same analysis end |

---

## 4. Six Product JSON Bundle Check

| # | File | Exists | Path | `schema_version` | Key fields (sample) | Useful for product UI... | Understandable to advisor/investor... |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Problem Classification | **yes** | `Main portfolio/analysis_subject/problem_classification.json` | `problem_classification_v1` | `problems[]`, `summary.primary_problem_id`, `current_portfolio_acceptable: false` | **Yes** — card list + severity | **Yes** — plain labels; evidence paths are technical |
| 2 | Candidate Launchpad | **yes** | `Main portfolio/analysis_subject/candidate_launchpad.json` | `candidate_launchpad_v1` | `cards[]`, `suggested_methods`, `summary.n_cards: 4` | **Yes** — next-step menu | **Yes** — goals readable; method ids need UI mapping |
| 3 | Current vs Candidate | **yes** | `Main portfolio/current_vs_candidate.json` | `current_vs_candidate_v1` | `view_mode: one_candidate`, dimensions cagr/vol/max_drawdown/sharpe/worst_stress_loss | **Yes** — delta table | **Yes** — if UI labels dimensions; **wrong candidate for this demo** |
| 4 | Decision Verdict | **yes** | `Main portfolio/decision_verdict.json` | `decision_verdict_v1` | `verdict_id: rebalance_to_selected_candidate`, `selected_candidate_id: risk_parity`, `confidence: medium` | **Yes** — product verdict object | **Mostly** — action is “for review”, not execution |
| 5 | AI Commentary context | **yes** | `Main portfolio/ai_commentary_context.json` | `ai_commentary_context_v1` | `allowed_source_artifacts`, `evidence_references`, `guardrails` | **Yes** — LLM prep | **N/A** — not consumer-facing prose |
| 6 | What Changed | **yes** | `Main portfolio/what_changed_summary.json` | `what_changed_summary_v1` | `headline`, `what_changed_lines[]`, `retest_triggers` | **Yes** — monitoring feed | **Yes** on first run (baseline message) |

**Bundle checklist:** **PASS (6/6 files + schema versions).**  
**Demo narrative checklist:** **FAIL** for Equal Weight as the compared/selected hypothesis.

---

## 5. Verdict Quality Review

### What verdict did the system produce...

- **`decision_verdict.json`:** `verdict_id` = `rebalance_to_selected_candidate`; label “Rebalance to selected candidate for review”; `selected_candidate_id` = **`risk_parity`** (Risk Parity Portfolio); `recommended_action` = review implementation plan; `action_plan.json` → `action_status: trades_for_review`.
- **`selection_decision.json`:** `decision_status: selected_candidate`; `favored_candidate_id: risk_parity`; composite score **67.15** vs **equal_weight 59.5** (rank **7** of 12); `no_trade.materiality_pass: true` (health +10, robustness +10, turnover 17.9%, drawdown improvement 1.6 pp).
- **`current_vs_candidate.json`:** 10y deltas vs current — Risk Parity **improves** vol (-1.5 pp), max drawdown (+1.6 pp less negative), worst stress loss (+6.8 pp); **worsens** CAGR (-2.1 pp) and Sharpe (-0.11).

### Economically / intuitively reasonable...

- **For Risk Parity vs current:** Plausible trade-off (lower vol/stress loss, give up return/Sharpe). Materiality flag consistent with modest drawdown/stress improvement.
- **For the stated demo (Equal Weight):** **Not represented** in product-facing compare/verdict. EW 10y metrics vs current (from `candidate_comparison.json`): CAGR **10.6%** vs **9.9%**, vol **10.3%** vs **9.6%**, max DD similar (**-19.7%** vs **-19.8%**), Sharpe slightly higher (**0.819** vs **0.799**), but EW **worse** on `recession_severe` stress (**-26.2%** vs **-22.2%**). A concentration-focused hypothesis does not obviously fix the **primary** classified problem (weak crisis resilience).

### Trade-offs explained...

- **Partial.** `current_vs_candidate` has dimension directions; `selection_decision.rationale` is thin (one bullet). Full trade-offs live in `tradeoff_explanation.json` (technical package), not in the six-file bundle.

### Avoids “best portfolio” framing...

- **Mostly yes** in verdict copy (“for review”, guardrails, `diagnostic_only` on several artifacts). **No** at selection layer — “Highest composite selection score” language still ranks a **winner** among many disk candidates.

### Supports no-trade / rebalance / test another / insufficient evidence...

| Logic | Supported... | Evidence |
| --- | --- | --- |
| No-trade | **Evaluated, not chosen** | `no_trade.applies: false`, materiality_pass true |
| Rebalance / review | **Yes** | `rebalance_to_selected_candidate` |
| Test another candidate | **Implicit only** | Launchpad cards + rejected list in journal; **not** wired to CLI-selected id |
| Evidence insufficient | **Weak** | Low confidence on some problems; verdict `confidence: medium` with empty `confidence_limitations` |

---

## 6. Client-Ready Interpretation

*Based only on artifacts from this run (analysis end **2026-04-30**).*

### What is inside the current portfolio...

Eight USD ETFs: largest weights **SCHD 17%**, **BND 16%**, **QQQ / SCHP / TLT 13%** each, **SPY 10%**, **GLD / SLV 9%** each (subject snapshot / `action_plan` baseline). X-Ray breakdown: **~42% fixed income**, **~40% equity**, **~18% commodity**; US region **~82%**.

### Where is the main risk...

Problem classification primary: **weak crisis resilience** (high severity). Stress: **`recession_severe`** synthetic loss **~-22%**, overall **`DIAG_ATTENTION`**. Risk contribution emphasis: **QQQ, SCHD, SLV** among top contributors (subject snapshot log).

### What did Equal Weight improve... (metrics only — not selected)

Versus current on **10y** window in `candidate_comparison.json`: **higher CAGR** (10.6% vs 9.9%), **similar max drawdown**, **slightly higher Sharpe**; **higher vol** (10.3% vs 9.6%). Stress: **worse** severe recession loss (**~-26%** vs **~-22%**).

### What got worse... (vs current, for **Risk Parity** — what the verdict actually used)

**Lower return and Sharpe**; **better** vol, max drawdown, and worst stress loss in `current_vs_candidate.json`.

### Is action justified...

System says **review rebalance toward Risk Parity** (`trades_for_review`), **not** auto-execution. For the **Equal Weight** hypothesis the operator requested, the system **did not** surface EW as the selected comparison — **no product verdict for EW** in `current_vs_candidate` / `decision_verdict`.

### What should be monitored...

`what_changed_summary`: first monitoring baseline; **retest triggers** `rebalance_trigger`, `monitoring_warning`. Track decision status, favored id, and future diff once a prior snapshot exists under `monitoring/latest/`.

---

## 7. Product Readiness Score

| Dimension | Score | Brief rationale |
| --- | ---: | --- |
| Backend flow readiness | **78** | Single command completes; caches work; diagnosis + factory + compare run. Compare scope not constrained to CLI candidate id. |
| Product output clarity | **62** | Six JSON schemas are clear; `one_candidate` view contradicts 12-candidate selection; manifest does not index bundle. |
| Advisor report usefulness | **58** | Diagnosis/launchpad strong; verdict/compare misleading for one-hypothesis demo without disk hygiene. |
| Data / output reliability | **72** | Reproducible with cache; noisy Yahoo warnings; EW snapshot reused (2026-05-22 timestamp) not rebuilt. |
| Demo readiness | **52** | Show diagnosis + bundle existence; **hide** EW-as-winner narrative; fix compare scope before external demo. |

**Overall demo readiness (equal weight story): ~52/100.**  
**Overall backend capability (any successful run): ~72/100.**

---

## 8. Problems Found

### Critical

1. **`--candidates equal_weight` does not drive `current_vs_candidate` / `decision_verdict` selected id** — product-facing layer shows **`risk_parity`** while factory only touched EW (`skipped_existing`). Breaks the documented one-hypothesis demo narrative.

### High

2. **Compare ranks all stale variant folders (12 candidates)** — selection favors highest on-disk score, not factory invocation set.  
3. **`output_manifest.json` after run lists only factory paths** — missing six `product_bundle_*` keys; API/discovery must hardcode paths or read OUTPUTS.md.  
4. **`view_mode: one_candidate` with wrong `selected_candidate_ids`** — UI would mislabel the comparison.

### Medium

5. **`candidate_comparison.json` is huge (~23k lines)** — poor default API payload for product UI.  
6. **Primary problem is crisis resilience; EW worsens severe recession stress** — launchpad suggests EW for concentration, not crisis — advisor may find narrative inconsistent without explanation.  
7. **Monitoring first-run only** — `what_changed` is baseline text, not true delta storytelling.

### Low

8. Yahoo historical download noise in logs.  
9. Config fields still “awaiting user input”.  
10. Legacy duplicate `portfolio_xray.json` / `stress_report.json` at `Main portfolio/` root (older) vs fresh sidecar — consumer path confusion.

---

## 9. Next Fixes

1. **Constrain compare/selection to factory-requested candidate id(s)** when `--candidates` is set — write `current_vs_candidate` and `decision_verdict` for **equal_weight**, not best-of-disk.  
2. **Prune or isolate variant output dirs** for demo runs (documented operator script or `--output-isolation` flag).  
3. **Merge compare manifest into `output_manifest.json`** after `--then-compare` (product bundle path index).  
4. **Emit slim `current_vs_candidate` payload** (or separate API view) without shipping full `candidate_comparison.json`.  
5. **Align launchpad primary card with CLI hypothesis** or add explicit “requested_hypothesis_id” on verdict for UI labeling.

*Out of scope for this audit: LLM commentary (`RM-ARCH-010`), new optimizers, UI.*

---

## 10. Final Verdict

| Question | Answer |
| --- | --- |
| Can I show this to someone as a backend demo... | **Yes for diagnosis + JSON contract; no for end-to-end Equal Weight decision story without caveats.** |
| What should I show... | `problem_classification.json`, `candidate_launchpad.json`, subject `portfolio_xray.json` + `stress_report.json` (excerpts), six-file bundle checklist, `ai_commentary_context.json` guardrails, offline test gate reference. |
| What should I hide... | `decision_verdict` / `current_vs_candidate` **as “the Equal Weight result”**; full `candidate_comparison.json`; raw `DIAG_*` codes in client views; stale multi-candidate ranking. |
| What must be fixed before UI/API... | Compare scope tied to requested candidates; manifest bundle index; single canonical paths under `analysis_subject/`; slim compare API; optional fresh isolated output root per demo. |

---

## Appendix: Supporting technical artifacts (this run)

| Artifact | Present | Notes |
| --- | --- | --- |
| `analysis_subject/portfolio_xray.json` | yes | `portfolio_xray_v2`, regenerated 2026-05-26 |
| `analysis_subject/stress_report.json` | yes | `DIAG_ATTENTION`, large file |
| `candidate_comparison.json` | yes | Includes `equal_weight` row; 12 candidates |
| `selection_decision.json` | yes | Favors `risk_parity`; EW rank 7 |
| `output_manifest.json` | yes | `run_kind: candidate_factory` only |
| `monitoring_diff.json` | yes | `diff_status: no_prior_snapshot` |
| `decision_journal.json` | yes | Records RP favored; EW rejected |

---

## Audit metadata

| Field | Value |
| --- | --- |
| Auditor | Controlled demo audit (agent, 2026-05-26) |
| Source code changed by audit | **No** |
| Documentation changed | **This file only** |
| Git staging | **None** |
