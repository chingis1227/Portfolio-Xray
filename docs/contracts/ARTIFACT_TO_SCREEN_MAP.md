# Artifact-to-Screen Map

Status: **canonical artifact-to-screen contract** for Portfolio MRI Core MVP screens, frontend adapters, run-local review state, and documentation alignment.

Scope: maps backend/runtime artifacts to frontend routes, presentation adapters, user-facing meaning, lifecycle state, stale-data risk, and lineage rules. This contract does not define formulas, stress scenarios, optimizer methods, JSON schemas, visual design, or test implementation details. Field-level and formula-level authority stays with the owning specs listed below.

This contract exists to prevent product-code-design drift. Future changes that add, rename, remove, reinterpret, or newly surface an artifact in Core MVP UI must update this file and the owning source-of-truth documents in the same change.


## Session 10 adapter boundary

Core MVP screens consume display models produced by frontend/FastAPI adapters, not raw generated
artifacts directly. Diagnosis interpretation Session 10 makes the active frontend state adapters
prefer FastAPI public display envelopes (`DiagnosisSummary`, candidate/hypothesis summaries,
downstream `evidence_chain_context`, verdict evidence lists, and report preview context) before
falling back to same-run artifacts. This map still defines which artifacts may feed each adapter, but
parsing raw `reviewResult.outputs.*` belongs in adapter code, compatibility proxies, tests, or
operator/debug views only.

## Session 12 review isolation boundary

Diagnosis interpretation Session 12 adds a public-envelope lineage check at the frontend FastAPI
bridge boundary. Recovery, Builder, Candidate, Comparison, Verdict, and Report compatibility routes
must reject a FastAPI response when its `lineage` or top-level identifiers point to a different
`review_id`, selected Launchpad card, candidate, comparison, or verdict than the active frontend
request. A matching local file under `runs/frontend_review_*` is not enough after a mismatch; the
route must fail before trusting downstream artifacts.

## Source-of-truth order

Use this document for artifact-to-screen routing and UI interpretation. Use lower-level sources for behavior details:

- `docs/contracts/PRODUCT_FLOW_CONTRACT.md` for canonical product step order and product boundaries.
- `docs/contracts/STAGED_REVIEW_STATE_CONTRACT.md` for the implemented staged web execution state,
  `review_state_v1`, canonical stage names, staged status semantics, and compact Supabase boundary.
- `RULES.md`, `WORKFLOW.md`, and `SPEC.md` for repository discipline and current implementation contract.
- `OUTPUTS.md` for generated output folders, product-bundle boundaries, and generated-vs-source rules.
- `docs/runtime_artifact_contract.md` for which artifacts are required, tombstoned, absent, optional, or stale by runtime mode.
- `docs/product_flow_operator_guide.md` for operator read order and product-bundle path rules.
- `../../frontend/README.md` for run-local frontend review folders and active browser state rules.
- `docs/contracts/FASTAPI_SCREEN_MAPPING.json` for the machine-readable FastAPI operation,
  response-field, and screen-route governance map.
- `docs/specs/portfolio_review_workflow_spec.md` for diagnosis-first workflow and `analysis_subject` boundaries.
- `docs/specs/input_assumptions_spec.md` for input and `analysis_setup` semantics.
- `docs/specs/portfolio_xray_diagnostics_spec.md` and `docs/specs/portfolio_xray_layer_spec.md` for Portfolio Diagnosis artifacts.
- `docs/specs/stress_lab_layer_spec.md`, `docs/specs/stress_testing_spec.md`, `docs/specs/hedge_gap_analysis_spec.md`, and `docs/specs/current_portfolio_stress_scorecard_spec.md` for Stress Test Lab artifacts.
- `docs/specs/client_fit_check_spec.md` and `docs/specs/client_fit_questionnaire_spec.md` for Client Fit V1 artifacts.
- `docs/specs/problem_classification_spec.md`, `docs/specs/candidate_launchpad_spec.md`, and `docs/specs/block_4_diagnosis_v3_spec.md` for Problem Classification and Launchpad artifacts.
- `docs/specs/portfolio_alternatives_builder_spec.md`, `docs/specs/builder_prefill_spec.md`, `docs/specs/candidate_setup_spec.md`, and `docs/specs/candidate_generation_spec.md` for Builder and candidate-generation artifacts.
- `docs/specs/current_vs_candidate_spec.md` for Current vs Candidate artifacts.
- `docs/specs/decision_verdict_spec.md` and `docs/specs/selection_engine_spec.md` for Decision Verdict and legacy selection evidence.
- `docs/specs/ai_commentary_grounding_spec.md` for grounded commentary context.
- `docs/specs/light_monitoring_summary_spec.md` and `docs/specs/monitoring_spec.md` for What Changed and monitoring artifacts.
- `docs/design/portfolio_mri_design_system.md` and future `docs/contracts/DESIGN_SYSTEM_CONTRACT.md` for visual hierarchy once surfaced.
- `docs/contracts/DOC_SYNC_CONTRACT.md` for documentation impact routing and final-response doc-sync reporting.

## Core routing principle

A backend artifact is not automatically a Core MVP screen. Core MVP UI should show product meaning, not raw files. The adapter layer translates artifacts into user-facing states such as diagnosis, stress evidence, hypothesis card, setup-only candidate test, comparison trade-off, decision verdict, grounded report preview, or deferred monitoring.

The current MVP canonical new-user frontend route chain is:

```text
/
-> /onboarding/sign-in
-> /onboarding/name
-> /onboarding/investor-type
-> /onboarding/loading
-> /portfolio-input
-> /diagnosis
-> /evidence
-> /client-fit
-> /hypothesis
-> /comparison
-> /verdict
-> /report
```

Returning signed-in users with completed onboarding and saved workspace, portfolio, draft, or review
history may branch from sign-in/loading to `/workspace`. `/workspace` restores compact account
context and review history only; it is not a calculation stage and must not treat compact history as
fresh run-local evidence unless the current FastAPI backend confirms same-run lineage.

Local preview may start at `/onboarding/name?dev_bypass=1` while email sign-in is being stabilized.
`/onboarding/goals` is a compatibility-only redirect to `/onboarding/investor-type`. `/client-profile`
remains an advanced/manual Client Fit editor, not the primary route start. `/sandbox/components`,
developer provenance panels, and legacy/debug helpers are operator review surfaces and must not
promote backend artifacts into Core MVP screen truth.

There is no current `/candidate`, `/monitoring`, `/what-changed`, optimizer-arena, action-plan, decision-journal, macro-dashboard, or PDF-product route. `/hypothesis` intentionally owns Launchpad, Builder setup, and the candidate-generation action/status for the MVP; generated candidate weights and current-vs-candidate display belong on `/comparison`. Monitoring / What Changed is a backend product projection and deferred UI layer.

Client Fit V1 is active in the web journey through onboarding plus a dedicated display route. `client_fit_check.json` can be generated under `analysis_subject/` and feeds bounded display/test criteria in adapters. Primary UI consumes compact Client Fit request/display models, not raw generated artifacts. Backend/CLI paths remain compatible with missing Client Fit and may produce `not_provided`; the standard web journey requires Client Fit context from onboarding before diagnosis.

The staged web path adds `review_state.json` as the active run-local progress source for
`runs/frontend_review_*` reviews. `review_state.json` does not replace canonical calculation
artifacts; it records stage status, current stage, safe errors, provider status, and allowed artifact
references for the active web run. The detailed contract is
`docs/contracts/STAGED_REVIEW_STATE_CONTRACT.md`.

## Runtime locations and trust boundaries

### Portfolio-first output folders

| Location | Trust rule | UI use |
| --- | --- | --- |
| `{output_dir_final}/analysis_subject/` | Authoritative for the diagnosed current portfolio after `run_portfolio_review.py` or frontend diagnosis bridge. Read this before root artifacts. | Input recovery, Diagnosis, Stress Lab, Problem Classification bridge, Hypothesis, Builder setup. |
| `{output_dir_final}/` root | Authoritative only for post-candidate product-bundle artifacts generated in the same active workflow, or for explicitly targeted legacy/policy workflows. | Candidate status, Comparison, Verdict, Report, optional What Changed when lineage is current. |
| `runs/frontend_review_<timestamp>_<id>/` | Authoritative for the active frontend vertical demo. Later API stages must use the same `reviewId`. | Live UI state, recovery, active candidate/comparison/verdict/report gates. |
| `runs/frontend_review_<timestamp>_<id>/review_state.json` | Authoritative progress state for the staged web path. It is valid only for its own `reviewId` and does not override artifact-level lineage rules. | Progress screen, partial-result unlocks, refresh recovery, compact Supabase stage summaries. |
| Root legacy policy files such as root `portfolio_xray.json`, `stress_report.json`, `run_result.json`, `portfolio_weights.yml` | Not authoritative for portfolio-first subject unless the task explicitly targets legacy policy. | Do not use as Core MVP primary screen evidence. |
| CSV/TXT/HTML/PNG/PDF/Markdown sidecars and `pdf files/` | Generated exports that may be stale under default `site_api`. | Do not use as active UI truth unless the user explicitly targets export/report artifacts. |

### Frontend adapter sources

| Adapter/source file | Current responsibility | Contract boundary |
| --- | --- | --- |
| `frontend/lib/reviewState.tsx` | Active review state, compact summaries, lineage gates, localStorage cleanup, journey flags, and presentation mapping for diagnosis, evidence, Builder, candidate, comparison, and verdict summaries. | May map artifacts to product states; must not turn raw filenames, raw enum ids, booleans, or stale downstream artifacts into primary UI copy. Session 8 may split adapter responsibilities, but this file is the current concentration point. |
| `frontend/lib/siteExplanationPresenter.ts` | Presentation boundary for `site_explanation_bundle.json` on public explanation cards. | Converts backend explanation-bundle rows into public display labels and keeps raw schema/source provenance out of default UI. Developer provenance is allowed only through an explicit opt-in debug display. |
| `frontend/lib/displayLabels.ts` | Shared normalization for raw labels, method IDs, scenario IDs, backend terms, and unknown values. | Must convert backend/internal vocabulary into approved user-facing labels and hide path-like artifact filenames in normal copy. |
| `frontend/lib/journey.ts` | Route list and unlock flags. | Must preserve Core MVP order and must not introduce hidden candidate/monitoring routes without contract updates. |
| `frontend/lib/types.ts` | Shared lightweight UI types. | Must represent product-facing concepts, not backend schema copies. |
| `frontend/app/api/portfolio/*` routes | Run-local bridges for diagnose, recover, Builder prepare, candidate generation, comparison, verdict, and report. | Must preserve `reviewId` lineage and sanitize recovery so stale downstream artifacts are not trusted as current. |

## Core artifact-to-screen map

| Artifact | Producer / default location | Consumer screen(s) | Adapter / state source | User-facing meaning | Current issue / risk | Required contract |
| --- | --- | --- | --- | --- | --- | --- |
| `run_metadata.json` and `analysis_setup` / `input_assumptions` | Portfolio-first materialization under `analysis_subject/`; frontend run-local diagnosis result under `runs/frontend_review_*`. | `/portfolio-input`, `/diagnosis`, report context. | `frontend/lib/reviewState.tsx`; diagnosis API result; recovery API. | What portfolio was diagnosed, with currency, analysis window, weights source, and resolved system assumptions. | Raw `analysis_subject`, `analysis_setup`, `cash_proxy_ticker`, or review-folder language can feel like operator/debug copy. | Use for assumptions and recovery only. Primary UI says current portfolio, reporting currency, analysis window, and data assumptions. Do not expose root legacy policy weights as user input. |
| `portfolio_xray.json` | Report/materialization pipeline; preferred path `analysis_subject/portfolio_xray.json`. | `/diagnosis`; supporting context in `/evidence`, `/hypothesis`, `/report`. | `reviewState.tsx` compact Diagnosis/diagnosis builders; Diagnosis components. | Portfolio Diagnosis evidence: what the current portfolio owns, where concentration/risk/factor/hidden exposure lives, and pre-stress weakness hypotheses. | Adapter logic is concentrated in `reviewState.tsx`; root legacy copies may be mistaken for subject truth; product blocks vs legacy `sections.*` can be mixed. | Prefer product blocks 2.1-2.6. Use legacy sections only as compatibility fallback. UI must translate block IDs into plain section names and never recommend a rebalance from Diagnosis alone. |
| `stress_report.json` | Stress/report pipeline; preferred path `analysis_subject/stress_report.json`. | `/evidence`; supporting context in `/diagnosis`, `/hypothesis`, `/report`. | `frontend/components/evidence/stressLabModel.ts`; `displayLabels.ts`; `reviewState.tsx` evidence summary. | Stress Test Lab evidence: how the current portfolio behaves under historical and synthetic stress, helped/hurt contributors, hedge gaps, and limitations. | Route is `/evidence` while product label is Stress Lab; raw scenario IDs and mandate pass/fail fields can leak if adapters regress. | Present as Stress Test Lab, not generic backend evidence. Translate scenario IDs and status codes. Do not expose Core MVP mandate pass/fail, `DIAG_*`, `loss_ok`, or raw row diagnostics as product conclusions. |
| `client_fit_check.json` | `src/client_fit.py` via report/materialization pipeline; preferred path `analysis_subject/client_fit_check.json`. | `/client-fit`; Problem Classification bridge; `/hypothesis`, `/comparison`, `/verdict`, `/report`. | FastAPI public `client_fit` display summary; `frontend/lib/reviewState.tsx`; `frontend/app/client-fit/page.tsx`; `frontend/components/client-fit/ClientFitContextCard.tsx`; Block 4 evidence extraction; Launchpad/Builder adapters; Current vs Candidate target comparison; Verdict context. | Client Fit V1 evidence: non-binding comparison of portfolio return, volatility, drawdown, stress loss, and horizon context against the provided profile. | Can be over-read as suitability approval, hidden optimizer constraints, a structural-issue override, or a final verdict. | Keep separate from diagnostic quality and verdict. Use only bounded status/target rows and source-quality context. Do not expose raw artifact names, convert targets into optimizer mandates, issue trade advice, claim approval, or let a fit result hide material objective diagnosis. |
| `problem_classification.json` | `write_block_4_diagnosis_outputs` in `run_report.py` / `src/block_4/diagnosis_builder.py`; `analysis_subject/problem_classification.json`. | `/diagnosis` bridge, `/hypothesis`, `/report`. | `reviewState.tsx` compact problem fields; `/hypothesis/page.tsx` mapping; future screen contract. | Main portfolio diagnosis: top problem, evidence, confidence, materiality, actionability, and next diagnostic step. | It is a product step but has no dedicated MVP route; can be underplayed or exposed as raw diagnosis IDs. | Surface as a bridge from Diagnosis/Stress into Hypothesis. It cannot build candidates, decide action, or force a rebalance. Missing classification is a partial-evidence state, not permission to invent a problem. |
| `candidate_launchpad.json` | `write_block_4_diagnosis_outputs` in `run_report.py`; `analysis_subject/candidate_launchpad.json`. | `/hypothesis`; report context. | `reviewState.tsx` compact launchpad fields; `/hypothesis/page.tsx`; `HypothesisCard`; `displayLabels.ts`. | Hypothesis cards: possible diagnosis-linked tests, success criteria, trade-off to watch, skip rule, and decision boundary. | Raw card/method fields and optimizer-zoo language can make cards look like recommendations or disabled backend methods. | Cards are tests, not portfolios. Show only contextual MVP test paths. Monitor/data-quality cards must not auto-generate candidates. Translate method IDs and hide raw `card_type`, `source_card_id`, and booleans. |
| `portfolio_alternatives_builder.json` | `src/portfolio_alternatives_builder.py` and frontend Builder prepare bridge; `analysis_subject/portfolio_alternatives_builder.json` or active run-local folder. | `/hypothesis` merged Builder/Candidate stage; report context. | `reviewState.tsx` `compactBuilderSetup` and `recordBuilderSetup`; API `POST /api/portfolio/builder/prepare`. | Candidate test setup: selected hypothesis, method, constraints, success criteria, Client Fit target criteria when available, trade-off, skip rule, and generation readiness. | Setup can look like a technical config panel, be over-read as generated weights, or accidentally turn Client Fit targets into optimizer mandates. | Builder is setup-only. It must not create weights, compare portfolios, issue a verdict, or map Client Fit target return/vol/drawdown/horizon into hidden optimizer objectives, constraints, mandate gates, factory commands, or analysis windows. Primary UI must say ready to test / blocked / monitor, not raw validation status or `CandidateSetup` internals. |
| `candidate_generation.json` | `src/candidate_generation.py`, `scripts/generate_candidate_from_builder_setup.py`, vertical Blocks 5-9 script, or frontend candidate API; root or active run-local folder. | `/hypothesis` generation action/status, `/comparison` candidate allocation and gate, `/verdict` and `/report` context. | `reviewState.tsx` `recordCandidateGeneration`; API `POST /api/portfolio/candidate/generate`. | One generated diagnostic test candidate, or a failed/infeasible attempt with reason. | Stale attempts from old runs can unlock comparison; candidate can be misread as recommendation; showing weights in Hypothesis can make setup look like the comparison result. | Candidate generation must be explicit and linked to the active Builder setup/review. A generated candidate is not recommended, not ranked, and not a trade. Generated weights are reviewed against the current portfolio on `/comparison`. Failed/infeasible/missing candidates block comparison or route to evidence-insufficient language. |
| `current_vs_candidate.json` | `src/current_vs_candidate.py` or Block 8 writer in `src/candidate_comparison.py`; root or active run-local folder after compare. | `/comparison`; `/verdict`; `/report`. | `reviewState.tsx` `recordComparisonResult`; `frontend/app/comparison/page.tsx`; comparison components; API `POST /api/portfolio/comparison/generate`. | Current-vs-candidate trade-off: what improved, worsened, stayed similar, is unavailable, how current/candidate values compare with Client Fit targets when available, and whether materiality supports decision review. If full candidate snapshots are missing but the same-run generated candidate has weights, the adapter may expose degraded weight-only concentration/turnover evidence instead of an opaque unavailable row. | Missing metrics may be shown as fake conclusions; stale comparison can be trusted after a different candidate; raw `view_mode` / selected IDs can leak; Client Fit target rows can be mistaken for a verdict; weight-only fallback can be over-read as full performance/stress evidence. | Only a current, scoped, same-candidate comparison unlocks Verdict. UI must separate no candidate, not comparable, partial metrics, weight-only degraded evidence, complete comparison, target-reference rows, and stale/ignored states. Do not crown a winner or issue a verdict here. |
| `decision_verdict.json` | `src/decision_verdict.py`; root or active run-local folder after Block 9 / verdict API. | `/verdict`; `/report`; optional monitoring summary. | `reviewState.tsx` `recordVerdictResult`; `VerdictPanel`; API `POST /api/portfolio/verdict/generate`. | Non-binding decision-support verdict: keep current/no-trade, no material rebalance, rebalance review, test another, candidate failed/infeasible, or evidence insufficient. | Backend verdict IDs and legacy selection statuses can leak; action wording can sound like trade advice. | Verdict must preserve no-trade and evidence-insufficient as valid outcomes. It must say decision support only, not trade instruction, suitability approval, tax advice, or best portfolio. Stale/mismatched verdicts must be ignored. |
| `ai_commentary_context.json` | `src/ai_commentary_context.py`; `analysis_subject/` for diagnosis-phase context and root/run-local after compare. | `/report`; optional supporting context in `/verdict`. | `frontend/app/report/page.tsx`; report API `POST /api/portfolio/report/generate`; future report adapter. | Grounded explanation inputs: deterministic evidence references and safe narrative scaffolding. | UI can expose prototype/operator phrases such as `AI Commentary context`, `does_not_call_llm`, source artifact names, or `No PDF generation`. | Use only as grounding. Do not claim an LLM decided or generated unsupported conclusions. Primary UI says grounded report preview / explanation inputs and marks missing evidence clearly. |
| `what_changed_summary.json` | `src/light_monitoring_summary.py`; root or product-bundle path after compare/monitoring when prior evidence exists. | No current route; optional `/report` note only. | No active frontend screen; future Monitoring adapter. | Light What Changed summary: changes since prior review and retest/watch triggers. | Backend artifact exists but no MVP UI route; omission can look accidental; report may imply full monitoring product. | Treat as Deferred / Monitoring layer. If absent, say no comparable prior review or no monitoring evidence. If present, show only a short grounded note until a Monitoring route is approved. |
| `output_manifest.json` | Output policy/report/factory/review writers; `analysis_subject/output_manifest.json` and/or root output manifest. | All screens as discovery/support, not hero content. | Backend API results; `reviewState.tsx` compact `outputPaths`; recovery API. | Machine-readable index for generated paths, product-bundle discovery, output profile, and artifact categories. | Raw paths can leak into UI; stale sidecar/PDF assumptions can mislead. | Use for path resolution and QA, not primary user copy. UI must not show manifest keys as product labels. Manifest does not override same-run lineage checks. |
| `review_result.json` | Frontend bridge `scripts/run_review_from_payload.py`; active `runs/frontend_review_*` folder. | `/portfolio-input` recovery and all run-local screens through active review state. | `frontend/app/api/portfolio/review/recover/route.ts`; `reviewState.tsx` compact storage. | Run-local envelope for frontend diagnosis/recovery. FastAPI recovery may include bounded current-portfolio `artifact_payloads` so the frontend can rebuild compact Diagnosis and Stress evidence summaries without storing the full raw result in browser storage. | Browser storage or recovery can accidentally trust stale downstream candidate/comparison/verdict artifacts. | Store compact summaries only in browser. Recovery restores diagnosis/evidence/launchpad/builder only and must clear candidate/comparison/verdict/report readiness unless same-run stage APIs regenerate or verify them. |
| `review_state.json` | Staged backend wrapper under the active `runs/frontend_review_*` folder. | Progress state across `/portfolio-input`, `/diagnosis`, `/evidence`, `/client-fit`, `/hypothesis`, `/comparison`, `/verdict`, and `/report`. | FastAPI `GET /api/v1/reviews/{review_id}/status`; frontend staged polling/refresh recovery; optional compact Supabase rows. | Web execution state: overall status, current stage, per-stage readiness, provider status, safe errors, and allowed artifact references. | Could be misread as a replacement for canonical artifacts or as permission to trust stale downstream files. | Use only as progress and routing state. Artifact contents and downstream unlocks still require same-run and same-candidate lineage. Do not expose raw file paths or stage ids as primary user copy. |

## Technical, advanced, legacy, and deferred artifacts

| Artifact | Status | Screen policy | Contract |
| --- | --- | --- | --- |
| `candidate_comparison.json` | Technical comparison evidence and batch/research registry depending on mode. | May support `/comparison` adapter, but not a Core MVP multi-candidate arena. | For one-candidate UI, use product-scoped evidence only and prefer `current_vs_candidate.json` for user-facing comparison. Read `candidate_menu` before interpreting batch rankings. |
| `candidate_comparison_registry.json` | Optional advanced full registry when product-scoped comparison is written separately. | No Core MVP screen. | Drill-down / audit only. Never unlock Verdict or present rankings in MVP journey. |
| `selection_decision.json` | Legacy/technical selection evidence; may inform Verdict. | Supporting evidence behind `/verdict`, not primary screen language. | Translate through `decision_verdict.json` when possible. Do not expose Selection Engine vocabulary as the Core MVP answer. |
| `candidate_factory_run.json` and `candidate_factory_manifest.json` | Factory orchestration and provenance. | No primary Core MVP screen; support candidate-generation QA and run-mode checks. | Use to detect profile/mode/reuse/stale evidence. Do not show factory step tables as user-facing hypothesis options. |
| Per-candidate folders and candidate manifests | Generated candidate report artifacts. | No Core MVP navigation. | Use only when same-run selected candidate is proven current. Do not scan disk and infer a candidate for the active UI. |
| `monitoring_diff.json` | Advanced/backend monitoring evidence. | Deferred Monitoring layer; optional support for What Changed/report. | Use only if `what_changed_summary.json` or future Monitoring contract maps it. Do not create scheduler/alert/trading semantics. |
| `portfolio_health_score.json`, `robustness_scorecard.json`, `assumption_sensitivity.json`, `pareto_dominance.json`, `regret_analysis.json`, `model_risk_diagnostics.json`, `tradeoff_explanation.json` | Advanced/research evidence. | No Core MVP hero or route. | May be drill-down/support in future advanced surfaces only after contract update. Do not present as the main product answer. |
| `action_plan.json`, `decision_journal.json`, `decision_package_summary.json` | Generated support / advanced decision records. | No full Action Plan or Decision Journal route in Core MVP. | May support report/verdict wording only if translated and bounded. Do not imply trade execution or completed journal product. |
| Root `run_result.json`, `portfolio_weights.yml`, root legacy `portfolio_xray.json`, root legacy `stress_report.json`, `current_vs_policy_status.json`, `portfolio_comparison.json`, `ew_rp_comparison.json` | Legacy policy compatibility. | No portfolio-first Core MVP primary screen. | Use only for explicit legacy-policy tasks. Never override `analysis_subject` for the current portfolio. |
| CSV/TXT/HTML/PNG/PDF/Markdown sidecars, `pdf files/`, `pdf_md_sources/`, `results_csv/`, `cache/` | Generated/export/cache artifacts. | Not active UI truth under default site/API runs. | Treat as stale unless explicitly generated in the active task. Do not commit routine refreshes unless requested. |

## Screen-by-screen artifact ownership

| Screen | Primary artifacts | Supporting artifacts | Must not use as primary truth |
| --- | --- | --- | --- |
| `/onboarding/*` | Bounded Client Fit profile request object created from intake. | Sign-in state, name, five-question intake, setup progress. | Portfolio diagnostics, generated artifacts, optimizer constraints, suitability approval. |
| `/workspace` | Compact workspace state and compact review history only. | Saved portfolios, active draft/review pointer, immutable compact review summaries, archive markers. | Raw generated artifacts, automatic recalculation, or treating compact history as fresh same-run evidence. |
| `/onboarding/goals` | No artifact ownership; compatibility redirect to current intake. | Safe redirect/fallback copy. | Goal artifact semantics, journey step ownership, generated outputs. |
| `/client-profile` | Advanced/manual Client Fit profile request object. | Preset metadata and editable target rows. | Treating this as the primary journey start, suitability approval, optimizer constraints. |
| `/sandbox/components` | No runtime artifact ownership. | Sample component states and local UI review fixtures. | Backend review actions, generated-output truth, or public journey status. |
| `/portfolio-input` | User input; bounded Client Fit profile request; run-local `review_result.json`; `analysis_setup` / `input_assumptions` after diagnosis. | Instrument universe; recovery metadata. | `portfolio_weights.yml`, root legacy `run_result.json`, optimizer targets, full constraints UI. |
| `/diagnosis` | `analysis_subject/portfolio_xray.json`; compact `analysis_subject/problem_classification.json` bridge. | `run_metadata.json`; data limitations; stress cross-references only where already cited. | Root legacy diagnosis; health score as main answer; candidate/comparison/verdict artifacts. |
| `/evidence` | `analysis_subject/stress_report.json`. | `portfolio_xray.json` and `problem_classification.json` for bridge context; scenario library sidecars. | Root legacy stress files; mandate pass/fail as Core MVP outcome; candidate comparison. |
| `/client-fit` | Bounded FastAPI/adapter `client_fit` display summary derived from `client_fit_check.json`. | Client Profile input summary; Stress/diagnosis evidence already generated for the active review. | Raw `client_fit_check.json`, suitability approval, optimizer mandates, verdict/action language. |
| `/hypothesis` | `problem_classification.json`, `candidate_launchpad.json`, `portfolio_alternatives_builder.json`, same-run `candidate_generation.json` status after explicit action. | Bounded Client Fit display summary as separate context; `run_metadata.json`; candidate factory provenance only for safety checks. | Full optimizer menu, generated weights as primary content, Client Fit target mandates, unrelated candidate folders, stale candidate attempts, verdict artifacts. |
| `/comparison` | Same-run `candidate_generation.json`; same-run `current_vs_candidate.json`. | Current portfolio input weights, bounded Client Fit display summary and target-reference context; product-scoped `candidate_comparison.json` behind adapter; output manifest paths. | Batch rankings, stale downstream comparison, selection verdict, suitability approval, fake metric rows. |
| `/verdict` | Same-run `decision_verdict.json`; same-run `current_vs_candidate.json`; same-run `candidate_generation.json`. | Bounded Client Fit display summary as one verdict input; `selection_decision.json` only as translated backend evidence; optional action context as support. | Trading instruction, best-portfolio ranking, stale verdict, full action plan, Client Fit pass as structural-issue override. |
| `/report` | `ai_commentary_context.json`, `decision_verdict.json`, `current_vs_candidate.json`, diagnosis/stress/hypothesis artifacts through grounding references. | `what_changed_summary.json` as short deferred-monitoring note when available. | Ungrounded prose, raw artifact package, PDF status as primary product result, full Decision Journal. |
| Deferred Monitoring / What Changed | Future route: `what_changed_summary.json`. | `monitoring_diff.json`, verdict/problem/comparison context. | Scheduler, broker alert, automatic rebalance trigger, trade instruction. |

## Lineage and stale-data rules

1. **Same current portfolio first.** Diagnosis artifacts must belong to the submitted current portfolio under `analysis_subject/` or the active `runs/frontend_review_*` folder.
2. **Same `reviewId` in frontend.** Recovery, Builder prepare, candidate generation, comparison, verdict, and report API calls must use the active review lineage and must reject mismatched FastAPI response lineage. Next.js compatibility route handlers must not read downstream run-local JSON files in Edge/deployed runtimes; they should pass explicit lineage ids to FastAPI and consume FastAPI public response payloads or another deployment-safe artifact access path.
3. **Same selected hypothesis.** Builder setup must link to the selected Launchpad card. Selecting a different card clears downstream candidate, comparison, verdict, and report readiness.
4. **Same generated candidate.** Comparison must scope `selected_candidate_ids` / comparison rows to the generated candidate for the active setup. Verdict must review that same candidate or valid no-candidate/evidence-insufficient state.
5. **Tombstones are states, not failures.** Diagnosis-only `no_candidate_v1` comparison/verdict tombstones mean no active candidate exists; they must not be shown as broken output.
6. **Stale downstream artifacts are ignored.** If a file exists on disk but the current runtime mode would not regenerate it, the UI must not trust it as current evidence.
7. **Manifest helps discovery, not trust by itself.** `output_manifest.json` paths must still pass same-run, same-candidate, and stage-order checks.
8. **Generated exports are not UI truth.** PDFs, CSVs, TXT, HTML, PNG, and Markdown sidecars are stale unless explicitly refreshed in the active task.
9. **Missing/partial evidence is visible.** Adapters must present unavailable, partial, limited, blocked, stale/ignored, and evidence-insufficient states separately.
10. **No raw artifact names in primary copy.** Artifact filenames in this contract are implementer vocabulary. User-facing UI uses product labels.
11. **Explanation provenance is opt-in debug data.** `site_explanation_bundle.json` keeps exact
    `source_refs` for audit, but public explanation cards must use the frontend presenter boundary
    and hide raw schema names, artifact filenames, and field paths unless a developer-only
    provenance display is explicitly enabled.

## Artifact lifecycle by runtime mode

| Runtime mode | Required diagnosis artifacts | Candidate/comparison/verdict state | UI interpretation |
| --- | --- | --- | --- |
| `python run_core_diagnostics.py` | `analysis_subject/run_metadata.json`, `portfolio_xray.json`, `stress_report.json`, snapshots, subject manifest. | Problem/Launchpad/Builder and post-candidate artifacts are absent. | Blocks 1-3 only. UI can show Input, Diagnosis, Stress evidence, and limitations; no Hypothesis generation or Verdict. |
| `python run_portfolio_review.py` default diagnosis-only | `analysis_subject/run_metadata.json`, `portfolio_xray.json`, `stress_report.json`, `problem_classification.json`, `candidate_launchpad.json`, `portfolio_alternatives_builder.json` where available, `ai_commentary_context.json` diagnosis phase. | Root compare/verdict may be diagnosis-only tombstones; no live generated candidate. | Diagnosis, Stress, and Hypothesis setup are available. Candidate generation/comparison/verdict remain unavailable until explicit action. |
| `python scripts/run_blocks_5_to_9_vertical_flow.py --method <id>` | Uses existing diagnosis/Builder context and writes/refreshes product-bundle artifacts. | `candidate_generation.json`, `current_vs_candidate.json`, `decision_verdict.json`, `ai_commentary_context.json`, optional `what_changed_summary.json`. | Canonical one-hypothesis product demo chain. UI can show candidate, comparison, verdict, and report only if same-run lineage is current. |
| `python run_portfolio_review.py --candidates <id>` | Same diagnosis artifacts plus explicit factory-id compatibility path. | Candidate/comparison/verdict artifacts scoped to selected id when current. | Allowed backend compatibility path, not the canonical visible Builder-to-Block-7 proof. UI language still treats candidate as a diagnostic test. |
| `python run_portfolio_review.py --with-candidates` or `--mode full` | Diagnosis artifacts plus batch/research candidate evidence. | Full menu/registry may exist. | Advanced/research mode. Do not convert this into Core MVP optimizer arena without new contract work. |
| Frontend `runs/frontend_review_*` vertical flow | Run-local diagnosis, Launchpad, Builder setup, and later stage result files. | Stage APIs write `candidate_generation_result.json`, `current_vs_candidate_result.json`, `decision_verdict_result.json`, and report result envelopes while preserving product artifacts. | Active browser truth for manual QA. Recovery is read-only and clears stale downstream readiness. |

## Acceptance checklist for future changes

- [ ] Every newly surfaced artifact has a producer, path, consumer screen, adapter, user-facing meaning, and lifecycle state in this contract.
- [ ] Every newly surfaced FastAPI operation or public response `data` field is listed in
  `docs/contracts/FASTAPI_SCREEN_MAPPING.json`, and generated frontend API types are current.
- [ ] The change preserves `analysis_subject/` as the portfolio-first current-subject source.
- [ ] Frontend routes consume artifacts through adapters, not raw JSON copy.
- [ ] Same-review, same-selected-card, same-candidate, and same-stage-order lineage is enforced before unlocking downstream screens.
- [ ] Diagnosis-only tombstones, missing artifacts, partial evidence, stale evidence, and generated export staleness have distinct user-facing states.
- [ ] No raw artifact filenames, raw JSON keys, booleans, backend status IDs, or path strings appear in primary UI.
- [ ] Monitoring / What Changed remains deferred unless a route decision and screen contract promote it.
- [ ] Advanced/legacy artifacts remain supporting evidence only unless the product-flow contract and screen contracts are updated.
- [ ] Documentation impact was checked against `OUTPUTS.md`, `../../frontend/README.md`, `docs/runtime_artifact_contract.md`, relevant `docs/specs/*`, and contract docs.

## Validation for this contract

This session is documentation-only. Minimum checks after editing this contract:

```text
git diff --check
```

Recommended evidence-gathering checks when this contract is applied to code:

```text
rg -n "portfolio_xray|stress_report|problem_classification|candidate_launchpad|portfolio_alternatives_builder|candidate_generation|current_vs_candidate|decision_verdict|ai_commentary_context|what_changed_summary|output_manifest" frontend
rg -n "reviewId|selectedCardId|candidateId|candidate_generation|current_vs_candidate|decision_verdict" frontend/lib/reviewState.tsx frontend/app/api/portfolio
```

Frontend implementation sessions must also use the checks required by `TESTING.md`, `../../frontend/README.md`, `AGENTS.md`, and the relevant screen contract.
