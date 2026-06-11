# Presentation Language Rules

Status: **canonical presentation-language contract** for Portfolio MRI / Portfolio X-Ray Core MVP primary UI, frontend presentation adapters, report preview copy, and future QA scans.

Scope: forbidden backend/internal terms, approved user-facing replacements, display-label responsibilities, safe state wording, and `rg` scan commands. This document is documentation-only for Session 4. It does not change runtime behavior, backend schemas, `frontend/lib/displayLabels.ts`, frontend components, generated artifacts, formulas, or visual design tokens.

This contract exists to prevent product-code-design drift. The backend may keep precise artifact names, JSON keys, enum ids, and file paths; primary user-facing screens must translate those details into plain decision-support language.

## Source-of-truth order

Use this document for copy and terminology boundaries. Use these related contracts for context:

- `docs/contracts/PRODUCT_FLOW_CONTRACT.md` for product order and global boundaries.
- `docs/contracts/ARTIFACT_TO_SCREEN_MAP.md` for artifact routing, lineage, stale-data rules, and adapter ownership.
- `docs/contracts/SCREEN_CONTRACTS.md` for screen-level roles, must-show rules, empty states, CTAs, and screen-specific forbidden terms.
- `docs/specs/frontend_screen_contracts.md` as prior alignment context, not the active Session 4 destination.
- `frontend/lib/displayLabels.ts` as the current implementation layer that normalizes labels. This session does not edit that file.
- `docs/contracts/DESIGN_SYSTEM_CONTRACT.md`, `docs/contracts/QA_CONTRACT.md`, and `docs/contracts/DOC_SYNC_CONTRACT.md` for visual, QA, and documentation-sync enforcement.

## Language principle

Primary UI must answer the user's question, not expose how the product is wired internally. Use words such as diagnosis, evidence, stress test, hypothesis, test setup, generated test candidate, trade-off, verdict, grounded explanation, limitation, and monitoring note. Avoid backend vocabulary such as artifact, JSON, factory, raw ids, folder names, booleans, schema keys, and operator run-state labels.

Technical language is allowed only in clearly developer/operator surfaces, docs, logs, API errors, or appendices that are not primary UI. If a term appears in a screen hero, primary card, CTA, empty state, badge, or report summary, it must follow this contract.

## Product safety boundaries

These boundaries apply to every replacement below:

1. A candidate is a **diagnostic test candidate**, not a recommendation, a winner, a best portfolio, or a trade order.
2. A Builder setup is **setup only** until the user explicitly generates one candidate attempt.
3. A comparison is **trade-off evidence**, not a verdict.
4. A Decision Verdict is **non-binding decision support**, not a trading instruction, suitability approval, or tax recommendation.
5. AI Commentary / report language explains **grounded evidence**. It must not say that AI decided, invented evidence, or created unsupported recommendations.
6. Backend/artifact/JSON names must not appear in primary UI. The UI may say supporting evidence, current review data, or grounded source summary instead.
7. Missing, partial, blocked, stale, generated, unavailable, and sample states are valid product states. Do not hide them and do not convert them into raw errors.

## Forbidden terms and approved replacements

Use this table for primary UI copy, user-visible labels, report preview text, badges, empty states, CTA labels, and card copy.

| Forbidden / internal phrase | Approved user-facing wording | Notes |
| --- | --- | --- |
| `backend`, `real backend review`, `api`, `raw output`, `raw outputs` | supporting data; review evidence; analysis engine | Avoid implementation-layer language in primary UI. |
| `artifact`, `source artifact`, `artifacts` | supporting evidence; source evidence; review output | Artifact names are implementer vocabulary. |
| `JSON`, `valid JSON`, raw request JSON | request format; input format; review data | API routes may return technical errors; primary UI should translate them. |
| `analysis_subject` | current portfolio; diagnosed portfolio | Keep `analysis_subject/` for docs/operators only. |
| `frontend_review_*`, `Review ID`, `reviewId`, run folder path | current review; saved review; review reference | If an operator ID must be shown, put it in diagnostics, not hero copy. |
| `output_manifest.json`, `outputs.*`, `outputPaths` | output index; available review files; supporting output list | Do not make manifests user-visible proof. |
| `portfolio_xray.json` | Portfolio X-Ray evidence | Screen label remains Portfolio X-Ray. |
| `stress_report.json` | Stress Test Lab evidence; stress-test evidence | Prefer product label `Stress Test Lab`. |
| `problem_classification.json` | main portfolio diagnosis; diagnosis bridge | Do not expose diagnosis ids as labels. |
| `candidate_launchpad.json` | hypothesis cards; test paths | Launchpad is implementer/product-step language, not necessarily primary copy. |
| `portfolio_alternatives_builder.json` | candidate test setup; selected test setup | Setup does not mean generated weights. |
| `candidate_generation.json`, `candidate_generation` | generated test candidate; candidate-generation result | Candidate generation is explicit user-triggered test creation. |
| `current_vs_candidate.json` | Current vs Candidate Comparison; trade-off comparison | Do not crown a winner here. |
| `decision_verdict.json` | Decision Verdict; decision-support verdict | Verdict is non-binding. |
| `ai_commentary_context.json`, `AI Commentary context` | grounded explanation inputs; grounded report preview | Do not imply the LLM decided. |
| `what_changed_summary.json`, `monitoring_diff.json` | What Changed summary; monitoring note | Current Monitoring route is deferred. |
| `candidate_comparison.json`, `selection_decision.json` | supporting comparison evidence; translated verdict evidence | Never surface as the main product answer. |
| `schema_version`, `artifact_status`, `source_artifacts`, `field_path`, `backend_audit` | evidence version/detail/source summary | Usually omit from primary UI entirely. |
| `view_mode`, `diagnosis_only`, `one_candidate`, `shortlist` | review mode; no active candidate; one test candidate; candidate list | Do not expose enum ids. |
| `generation_status`, `validation_status`, `can_generate_candidate`, `candidate_generation_allowed` | setup status; ready to test; blocked; unavailable | Translate raw booleans and statuses. |
| `card_type`, `source_card_id`, `source_diagnosis_id`, `source_builder_setup_id` | test type; diagnosis source; selected test path | IDs belong in diagnostics only. |
| `selected_candidate_ids`, `requested_candidate_ids`, raw candidate folder names | selected test candidate; candidate used for comparison | Do not show folder names as labels. |
| `baseline_or_candidate_metric_missing`, `no_available_comparison_metrics` | candidate metric unavailable; comparison metrics unavailable | Keep unavailable state visible. |
| `stale_downstream_artifact_ignored`, `stale downstream` | previous result ignored because it is outdated | Explain stale lineage plainly. |
| `tombstone` | intentionally unavailable for this review; no active candidate yet | Tombstone means lifecycle state, not failure. |
| `factory`, `candidate_factory_run.json`, `skipped_existing` | candidate builder; reused previous candidate evidence; generation provenance | Avoid factory-step tables in primary UI. |
| `optimizer arena`, `optimizer zoo`, full method catalog | available test paths; suggested method | Core MVP is not a multi-candidate optimizer arena. |
| raw method ids such as `equal_weight`, `risk_parity`, `minimum_variance`, `minimum_cvar`, `hrp` | Equal Weight, Risk Parity, Minimum Variance, Minimum CVaR, Hierarchical Risk Parity | Show methods only when contextually relevant. |
| raw scenario ids such as `recession_severe`, `equity_shock`, `rates_shock`, `inflation_stagflation` | Severe recession; Equity sell-off; Interest-rate shock; Inflation / stagflation | Translate scenario ids and keep evidence quality visible. |
| `DIAG_*`, `loss_ok`, `loss_gate_mode`, `fail_reason_code`, `diagnostic_code` | stress limitation; stress flag; reason to review | Do not show legacy mandate semantics as Core MVP outcomes. |
| raw booleans `true`, `false` | Available; Not available; Yes; No; Ready; Blocked | Choose wording by product state, not literal boolean. |
| `null`, `undefined`, raw `n/a`, `not available yet` as table filler | Not available; Not evaluated; Evidence unavailable; Not enough evidence yet | Avoid fake rows or placeholder-looking conclusions. |
| `disabled` | Not ready yet; unavailable for this review; blocked by missing evidence | Do not make unsupported paths look like broken buttons. |
| `source problem`, `selected hypothesis`, `setup preview` | diagnosis source; selected test path; test setup preview | Keep hypothesis/test wording consistent. |
| `candidate generation readiness` | ready to generate a test candidate; blocked; not ready | State what the user can do next. |
| `No PDF generation` | preview only; export deferred; PDF export is not part of this review | Do not present missing export support as product failure. |
| `implementation order` | rebalance instruction, only when explicitly supported; otherwise omit | Current report must not create implementation orders. |
| `Backend does not expose` | not available in this review; not enough evidence returned | Avoid blaming backend in user copy. |
| `no comparison or verdict was generated` | comparison and verdict are not ready for this review | Explain what is missing and how to proceed. |
| `selected_candidate`, `selected candidate` as verdict outcome | rebalance review; selected test candidate | Never imply automatic execution. |
| `best portfolio`, `winner`, `recommended portfolio`, `must rebalance`, `trade now`, `execute`, `buy`, `sell` | candidate test; improved/worsened trade-off; rebalance review; keep current; no-trade | Trading/advice language is forbidden. |
| `tax advice`, `client suitability approved`, `guaranteed improvement` | decision-support only; not tax/suitability advice; evidence-based scenario result | Preserve compliance boundary. |
| `Decision Journal` as a completed Core MVP screen, `Action Engine`, `Action Plan` as primary route | generated support artifact; future/backlog; optional supporting context | Do not promote advanced/legacy artifacts into Core MVP. |

## Approved state language

### Empty states

Use empty states to tell the user what is missing and what to do next.

- No portfolio input: "Add holdings and weights to start the diagnosis."
- No diagnosis yet: "Run diagnosis to create Portfolio X-Ray and Stress Test Lab evidence."
- No stress evidence: "Stress evidence is unavailable for this review. Continue only with disclosed limitations."
- No hypothesis cards: "No testable hypothesis is available from the current evidence."
- No candidate: "Generate one test candidate before comparing."
- No verdict: "Complete a current comparison before asking for a verdict."
- No report: "Generate a grounded report preview after the verdict is available."

### Blocked states

Blocked states must name the blocker without raw backend vocabulary.

- Data quality blocker: "The review needs cleaner data before this test is reliable."
- Setup blocked: "This test setup is not ready to generate a candidate."
- Candidate failed / infeasible: "The selected test candidate could not be built from the available evidence."
- Comparison blocked: "The current portfolio and candidate cannot be compared yet."
- Verdict blocked: "There is not enough current comparison evidence for a verdict."

### Generated states

Generated means a product artifact or candidate attempt exists; it does not mean recommended.

- Candidate generated: "A diagnostic test candidate was generated for comparison."
- Comparison generated: "The current portfolio and test candidate were compared."
- Verdict generated: "A non-binding decision-support verdict is available."
- Report generated: "A grounded report preview is available."

### Unavailable / partial states

Unavailable and partial states must be specific and not look like bugs.

- "Evidence unavailable for this review."
- "This metric was not evaluated."
- "Only partial evidence is available; conclusions are limited."
- "Previous result ignored because it is outdated."
- "No comparable prior review is available yet."

Avoid raw `n/a`, blank cells, or generic "disabled" labels in primary cards and tables.

### Sample / demo states

Sample mode must be transparent and must not be confused with a real user review.

- Use: "Sample review"; "Demo data"; "Example portfolio"; "Sample evidence".
- Do not use: raw `frontend_review_sample` as the main label, fake review ids, or unstated sample data.
- If sample mode is active, major screens should disclose it near the top or in a persistent context label.

## Display-label layer responsibilities

`frontend/lib/displayLabels.ts` is the current shared normalization layer. Session 4 does **not** edit it, but future implementation work must use these responsibilities:

1. Convert raw artifact filenames, JSON keys, enum ids, method ids, scenario ids, and booleans into approved product labels.
2. Hide path-like values, generated-output folder names, and raw run ids from normal copy.
3. Normalize unknown values to state-specific labels such as Not available, Not evaluated, Evidence unavailable, or Not enough evidence yet.
4. Preserve approved product names and acronyms: Portfolio MRI, Portfolio X-Ray, Stress Test Lab, Current vs Candidate Comparison, Decision Verdict, AI Commentary, USD, US, CAGR, VaR, ES, VIX.
5. Keep candidate language as diagnostic-test language. Do not map a generated candidate to recommendation, winner, or trade instruction.
6. Keep verdict language non-binding. `selected_candidate`-style backend ids should become review language, not execution language.
7. Keep AI/report language grounded. `ai_commentary_context`-style terms should become grounded explanation inputs or report preview.
8. Treat `displayLabels.ts` as a translation boundary, not a place to change backend behavior, schemas, route unlock rules, or calculations.

Future code changes that alter `displayLabels.ts` must update this contract or state why no language-contract change is needed.

## Screen-specific language routing

- `/portfolio-input`: current portfolio, holdings, weights, reporting currency, assumptions. Do not show config/runtime ids as primary copy.
- `/diagnosis`: Portfolio X-Ray, current portfolio diagnosis, concentration, factor exposure, hidden exposure, weakness map, data limitations. Do not recommend action.
- `/evidence`: Stress Test Lab, stress evidence, helped/hurt contributors, hedge gap, limitations. Do not expose raw scenario ids or legacy mandate pass/fail fields.
- `/hypothesis`: diagnosis recap, hypothesis cards, selected test path, test setup, ready/blocked, generated test candidate. Candidate is not recommendation.
- `/comparison`: current vs candidate trade-off, improved/worsened/similar/unavailable, materiality for review. Comparison is not verdict.
- `/verdict`: keep current / no-trade, no material rebalance, rebalance review, test another hypothesis, candidate failed/infeasible, evidence insufficient. Verdict is not trading instruction.
- `/report`: grounded report preview, evidence used, limitations, decision-support boundary, optional What Changed note. Report does not invent conclusions or present export/PDF absence as product failure.
- Monitoring / What Changed: deferred UI layer. If mentioned, use first review, no comparable prior review, no material change, changed, retest suggested, or monitoring unavailable.

## Future `rg` scan commands

Run these from the repository root. These commands are intentionally targeted at frontend primary UI and adapters; docs and tests may contain forbidden terms as contract evidence.

### Primary UI forbidden-term scan

    rg -n "backend|artifact|JSON|valid JSON|source problem|selected hypothesis|setup preview|run-local|candidate generation readiness|not available yet|disabled|true|false|n/a|outputs\\.|stale downstream|baseline_or_candidate|no comparison or verdict was generated|factory|candidate_generation|implementation order|source artifact|Backend does not expose|No PDF generation|AI Commentary context|best portfolio|must rebalance|trade now|execute|buy|sell" frontend/app frontend/components

Expected result: no matches in screen hero copy, primary cards, CTAs, empty states, or report summaries. If matches are in API routes or developer-only diagnostics, inspect manually and document why they are outside primary UI.

### Adapter leakage scan

    rg -n "portfolio_xray\\.json|stress_report\\.json|problem_classification\\.json|candidate_launchpad\\.json|portfolio_alternatives_builder\\.json|candidate_generation\\.json|current_vs_candidate\\.json|decision_verdict\\.json|ai_commentary_context\\.json|what_changed_summary\\.json|selection_decision\\.json|output_manifest\\.json|run_result\\.json|portfolio_weights\\.yml|Review ID|frontend_review_|analysis_subject|valid JSON|tombstone|skipped_existing|optimizer arena|Selection Engine|Action Engine" frontend/app frontend/components frontend/lib

Expected result: raw terms should be absent from primary screen copy. Matches in `frontend/lib/displayLabels.ts` are allowed only when they are replacement rules. Matches in API routes are allowed only for request validation or operator errors, not primary UI strings.

### Advice/execution scan

    rg -n "recommended portfolio|best portfolio|winner|must rebalance|trade now|execute trade|buy|sell|guaranteed improvement|tax advice|client suitability approved|implementation order" frontend/app frontend/components frontend/lib

Expected result: no primary UI wording that turns diagnostics into trading advice. Boundary notes may mention what the product does **not** do.

### State placeholder scan

    rg -n "\\bn/a\\b|\\bnull\\b|\\bundefined\\b|\\btrue\\b|\\bfalse\\b|disabled|not available yet" frontend/app frontend/components

Expected result: no raw placeholders in user-facing copy. Code booleans and React props may match; inspect manually and do not treat implementation syntax as copy leakage.

### Contract evidence scan

    rg -n "Presentation Language Rules|candidate is not|verdict is not|grounded explanation|backend/artifact/JSON|displayLabels|forbidden" docs/contracts

Expected result: this contract and related contracts reference the language boundaries.

## Acceptance checklist for future language changes

- [ ] User-facing copy uses product language, not backend vocabulary.
- [ ] Candidate wording remains diagnostic-test wording and never recommendation/trade wording.
- [ ] Verdict wording remains non-binding decision support.
- [ ] AI/report wording explains grounded evidence only.
- [ ] Backend/artifact/JSON/file/path names are absent from primary UI.
- [ ] Empty, blocked, generated, unavailable, partial, stale, evidence-insufficient, and sample states have distinct labels.
- [ ] `displayLabels.ts` changes, if any, align with this contract.
- [ ] `PRODUCT_FLOW_CONTRACT.md`, `ARTIFACT_TO_SCREEN_MAP.md`, and `SCREEN_CONTRACTS.md` remain consistent with any language change.
- [ ] Targeted `rg` scans were run or explicitly waived with a reason.

## Validation for this contract

Session 4 is documentation-only. Minimum checks after editing this file:

    rg -n "backend|artifact|JSON|source problem|selected hypothesis|setup preview|run-local|candidate generation readiness|not available yet|disabled|true|false|n/a|outputs\\.|stale downstream|baseline_or_candidate|no comparison or verdict was generated|factory|candidate_generation|implementation order|source artifact|Backend does not expose" frontend/app frontend/components frontend/lib docs/contracts docs/specs/frontend_screen_contracts.md
    rg -n "portfolio_xray\\.json|stress_report\\.json|problem_classification\\.json|candidate_launchpad\\.json|portfolio_alternatives_builder\\.json|candidate_generation\\.json|current_vs_candidate\\.json|decision_verdict\\.json|ai_commentary_context\\.json|what_changed_summary\\.json|Review ID|frontend_review_|valid JSON|best portfolio|must rebalance|trade now|AI Commentary context|No PDF generation" frontend/app frontend/components frontend/lib docs/contracts docs/specs/frontend_screen_contracts.md
    git diff --check

The `rg` scans above are evidence-gathering scans for Session 4. They may return matches in existing code or contracts; those matches are not fixed in this docs-only session. Implementation cleanup belongs to later sessions.
