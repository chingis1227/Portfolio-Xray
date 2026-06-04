# Blocks 3-5 Handoff Remediation — Live Readiness Fix

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`,
`Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document is maintained according to `PLANS.md` in the repository root. The purpose of this
plan is to remediate the final `NOT_READY` verdict from
`docs/audits/2026-06-04_blocks_3_5_handoff_session_08_final_readiness_verdict.md`.

## Purpose / Big Picture

The product handoff audited in Session 08 is:

    Stress evidence -> Investment diagnosis -> Testable Launchpad card -> Builder prefill

That chain is source-backed and mostly test-backed, but the current workspace cannot yet prove a
clean diagnosis-only live run. A diagnosis-only run means the current portfolio is diagnosed without
generating candidate portfolios, without comparing candidates, and without issuing a Decision
Verdict. After this remediation, operators should be able to run the diagnosis-only validation gate
and see `live core E2E validation: OK`, even after an earlier one-candidate run left candidate
artifacts on disk, provided that the required market data or an approved cached risk-free fallback is
available and disclosed.

The target final verdict for this plan is `READY_TO_MOVE_FORWARD` if all live/docs/tests are green.
If only a clearly external data-source limitation remains and all product contracts are clean, the
acceptable fallback verdict is `READY_WITH_MINOR_GAPS`.

## Progress

- [x] (2026-06-04) Session 01 completed: created this remediation ExecPlan, ran the requested
  baseline commands, and recorded the blocker table. No runtime logic, source behavior, tests, or
  product documentation were changed in this session.
- [x] (2026-06-05) Session 02 completed: diagnosis-only product-bundle hygiene now runs before
  shared market-data context preparation, so stale root candidate/compare artifacts are removed and
  `no_candidate_v1` tombstones are written before a FRED or market-data refresh failure can leave
  the workspace looking like a live candidate run.
- [x] (2026-06-05) Session 03 completed: diagnosis-only `analysis_subject` materialization can use
  an approved cached FRED `DTB3` risk-free series when the fresh risk-free fetch times out. The
  fallback is cache-only, provenance-visible, and covered by focused data-cache tests. The live
  review command advanced past the risk-free blocker but timed out later in shared factor/macro
  context, so final live completion remains for Session 04 or a follow-up live-data remediation.
- [x] (2026-06-05) Session 04 completed: fixed Stress Commentary legacy
  `hedge_gap_analysis.status = not_applicable` wording, ran the final readiness gate, and closed
  this ExecPlan with final verdict `READY_TO_MOVE_FORWARD`.

## Surprises & Discoveries

- Observation: The focused product-bundle hygiene and live-core validator unit tests already pass.
  Evidence: Session 01 baseline
  `.\.venv\Scripts\python.exe -m pytest tests/test_product_bundle_hygiene.py tests/test_live_core_e2e_validation.py -q`
  returned `10 passed`.

- Observation: The live diagnosis-only validator still sees a product-one-candidate workspace.
  Evidence: Session 01 baseline
  `.\.venv\Scripts\python.exe scripts\verify_live_core_e2e.py --profile diagnosis_only`
  reported `detected_profile=product_one_candidate` and failed because stale
  `candidate_factory_run.json`, `candidate_comparison_registry.json`, and non-tombstone
  compare/decision JSON remain at the output root.

- Observation: The allowed diagnosis-only refresh still cannot reach product-bundle hygiene because
  shared context preparation fails on live FRED `DTB3`.
  Evidence: Session 01 baseline
  `.\.venv\Scripts\python.exe run_portfolio_review.py --mode core --skip-candidates` failed while
  loading `FRED:DTB3`, ending with `TimeoutError: The read operation timed out`.

- Observation: The Stress Commentary failure is still a text-surface mismatch, not a proven JSON
  handoff failure.
  Evidence: Session 01 baseline
  `.\.venv\Scripts\python.exe -m pytest tests/test_stress_hedge_gap_contract.py tests/test_portfolio_commentary.py -q`
  returned `1 failed, 19 passed`; the failed test expected the phrase
  `Hedge gap: not applicable`.

- Observation: Early diagnosis-only hygiene is now covered by a focused regression test that
  simulates shared-context failure before report materialization.
  Evidence: Session 02
  `.\.venv\Scripts\python.exe -m pytest tests/test_product_bundle_hygiene.py tests/test_live_core_e2e_validation.py -q`
  returned `11 passed`.

- Observation: The live diagnosis-only gate becomes clean after the early hygiene hook runs, even
  though FRED still times out before full materialization completes.
  Evidence: Session 02 `.\.venv\Scripts\python.exe run_portfolio_review.py --mode core --skip-candidates`
  still exited `1` on `FRED:DTB3` timeout, but logged
  `Early diagnosis-only product bundle hygiene (tombstone=no_candidate_v1, removed=3 stale files)`.
  The subsequent
  `.\.venv\Scripts\python.exe scripts\verify_live_core_e2e.py --profile diagnosis_only`
  returned `live core E2E validation: OK`.

- Observation: The risk-free timeout blocker is now remediated with explicit fallback metadata.
  Evidence: Session 03
  `.\.venv\Scripts\python.exe -m pytest tests/test_data_cache_key.py tests/test_product_bundle_integration.py -q`
  returned `8 passed`. A live retry created a current monthly cache with
  `risk_free_fallback_used: true`, `risk_free_fallback_reason: fred_timeout_cached_rf`, and
  `risk_free_source_used: approved_cached_risk_free_series` in `cache/monthly/v_d5593f9be828/meta.json`.

- Observation: The canonical live review command no longer stops at risk-free loading, but it did
  not complete inside this session's command budget.
  Evidence: Session 03 `.\.venv\Scripts\python.exe run_portfolio_review.py --mode core --skip-candidates`
  timed out after 304 seconds. A direct logged retry of
  `.\.venv\Scripts\python.exe -u run_report.py --materialize-analysis-subject --output-profile site_api --review-mode core --use-review-run-context`
  timed out after 124 seconds after logging `Return panel cache found; loading...`,
  `Return panel cache was created with approved cached risk-free fallback...`, and
  `Daily cache found for tail-risk panel; loading...`. This indicates the remaining live blocker is
  later shared factor/macro context work, not the FRED `DTB3` risk-free fetch fixed in Session 03.

- Observation: The Stress Commentary wording mismatch is fixed without reintroducing legacy hedge
  gap phrasing when `hedge_gap_analysis_v1` evidence exists.
  Evidence: Session 04
  `.\.venv\Scripts\python.exe -m pytest tests/test_stress_hedge_gap_contract.py tests/test_portfolio_commentary.py -q`
  returned `20 passed`.

- Observation: The final live/docs readiness gate is clean.
  Evidence: Session 04 `.\.venv\Scripts\python.exe scripts\validate_block_4_live.py --refresh-diagnosis`
  returned `Block 4 v3 live validation: OK`;
  `.\.venv\Scripts\python.exe scripts\verify_live_core_e2e.py --profile diagnosis_only` returned
  `live core E2E validation: OK`; and
  `.\.venv\Scripts\python.exe scripts\verify_docs.py` returned `docs verification: OK`.

## Decision Log

- Decision: Keep this remediation plan limited to live readiness, artifact hygiene, approved
  risk-free fallback disclosure, and Stress Commentary wording.
  Rationale: The Session 08 audit did not prove a broken optimizer, candidate-generation,
  Decision Verdict, PDF, AI-generation, or portfolio-weight formula. Touching those areas would
  expand risk beyond the observed blockers.
  Date/Author: 2026-06-04 / Codex.

- Decision: Treat silent risk-free fallback as forbidden.
  Rationale: A cached risk-free series can make a live run operationally resilient, but using cache
  instead of fresh FRED changes data provenance. Operators and downstream artifacts must see that
  fallback happened through metadata and warnings.
  Date/Author: 2026-06-04 / Codex.

- Decision: Stop after Session 01 in this run.
  Rationale: The user explicitly instructed that once Session 01 is fully complete, the agent should
  report completion and stop.
  Date/Author: 2026-06-04 / Codex.

- Decision: Apply diagnosis-only/root cleanup immediately after resolving the output directories,
  before shared market-data context preparation and before `run_portfolio_report_for_weights`.
  Rationale: This is the earliest safe point where `output_dir_final` and `analysis_subject/` are
  known. It preserves the existing `no_candidate_v1` contract and avoids changing optimizer,
  candidate, Decision Verdict, PDF, AI, or portfolio-weight logic.
  Date/Author: 2026-06-05 / Codex.

- Decision: Scope the risk-free cached fallback to diagnosis-only `analysis_subject`
  materialization and the review context it prepares, instead of enabling it for all candidate
  factory or legacy report runs by default.
  Rationale: Session 03 is a live-readiness remediation for the diagnosis-only gate. Keeping the
  fallback opt-in at the orchestrator boundary avoids changing optimizer, candidate, or policy
  data behavior outside the observed blocker.
  Date/Author: 2026-06-05 / Codex.

- Decision: Approve cached risk-free fallback only when cache metadata matches `rf_source`,
  `investor_currency`, and `returns_frequency`, and cached observations cover the
  analysis-effective end date.
  Rationale: The risk-free series is independent from portfolio tickers, but using a wrong source,
  currency, frequency, or stale series would silently change assumptions. These criteria keep the
  run operational while preserving traceable data provenance.
  Date/Author: 2026-06-05 / Codex.

## Outcomes & Retrospective

Session 01 established the remediation baseline and confirmed that the final `NOT_READY` status was
caused by three concrete issues: stale root candidate artifacts, FRED timeout before diagnosis-only
hygiene could complete, and one Stress Commentary wording failure. No implementation changes were
made in Session 01.

Session 02 fixed the stale-root-artifact blocker. `run_report.run_materialize_analysis_subject_report`
now applies diagnosis-only tombstones before shared context preparation, and applies core Blocks
1-3 pruning early for the core-only scope. The FRED timeout remains a Session 03 blocker, and the
Stress Commentary wording mismatch remains a Session 04 blocker.

Session 02 verification:

    .\.venv\Scripts\python.exe -m pytest tests/test_product_bundle_hygiene.py tests/test_live_core_e2e_validation.py -q
    11 passed

    .\.venv\Scripts\python.exe run_portfolio_review.py --mode core --skip-candidates
    exit=1, still blocked by FRED:DTB3 timeout after early hygiene

    .\.venv\Scripts\python.exe scripts\verify_live_core_e2e.py --profile diagnosis_only
    live core E2E validation: OK

Session 03 fixed the FRED `DTB3` risk-free timeout blocker without making the fallback silent.
`src.data_loader.load_monthly_data_shared` now accepts an opt-in
`allow_risk_free_cached_fallback` flag. `run_report.run_materialize_analysis_subject_report` enables
that flag only for diagnosis-only `analysis_subject` materialization and its shared review context.
When FRED times out, the loader searches monthly cache folders for an approved cached risk-free
series with matching `rf_source`, `investor_currency`, `returns_frequency`, and analysis-end
coverage. If one exists, the run uses it and writes `risk_free_fallback_used: true`,
`risk_free_fallback_reason: fred_timeout_cached_rf`, provenance, and warnings into data results,
monthly cache metadata, `data_policy.json`, and `run_metadata.json.derived_assumptions`. If no
approved cache exists, the run fails clearly.

Session 03 verification:

    .\.venv\Scripts\python.exe -m pytest tests/test_data_cache_key.py tests/test_product_bundle_integration.py -q
    8 passed

    .\.venv\Scripts\python.exe run_portfolio_review.py --mode core --skip-candidates
    timed out after 304 seconds; risk-free fallback created cache/monthly/v_d5593f9be828/meta.json
    with risk_free_fallback_used=true, but the command later stalled in shared factor/macro context
    after loading the fallback-created return panel cache.

## Context and Orientation

The repository root is `D:\Рабочий стол\КУРСОР ТУЛА ДИАГНОСТИКА`. Use Windows PowerShell commands
from that directory. Use `.\.venv\Scripts\python.exe` as the Python interpreter.

The current product is diagnosis-first. In this plan, "diagnosis-only" means current portfolio
diagnostics are materialized under `Main portfolio/analysis_subject/`, while root-level candidate
factory, candidate comparison, current-vs-candidate, and decision verdict artifacts must not look
like current live candidate output. For diagnosis-only runs, stale post-candidate root JSON must be
removed or overwritten with `no_candidate_v1` tombstones.

The main files for later sessions are:

- `src/product_bundle_hygiene.py`, which defines `apply_diagnosis_only_product_bundle_hygiene`.
- `run_report.py`, whose `run_materialize_analysis_subject_report` currently applies
  diagnosis-only hygiene only after `run_portfolio_report_for_weights` completes.
- `src/data_loader.py` and `src/data_fred.py`, which load risk-free data from sources such as
  `FRED:DTB3`.
- `src/portfolio_commentary.py`, which writes stress commentary text.
- `tests/test_product_bundle_hygiene.py`, `tests/test_live_core_e2e_validation.py`,
  `tests/test_data_cache_key.py`, `tests/test_product_bundle_integration.py`,
  `tests/test_stress_hedge_gap_contract.py`, and `tests/test_portfolio_commentary.py`.

## Plan of Work

Session 01 creates this ExecPlan and captures baseline evidence only. It does not change runtime
logic.

Session 02 should make diagnosis-only product-bundle hygiene robust against partial run failures.
The implementer should ensure stale root candidate and comparison artifacts are removed and
diagnosis-only tombstones are written before a market-data or FRED failure can leave the workspace
looking like a live candidate run. The exact implementation should stay minimal and should preserve
the existing `no_candidate_v1` contract.

Session 03 should make diagnosis-only refresh resilient to temporary FRED risk-free failures when an
approved cached risk-free series exists. The fallback must be explicit. If cache is used instead of
fresh FRED, metadata and warnings must include a machine-readable flag such as
`risk_free_fallback_used: true`, a reason such as `risk_free_fallback_reason:
fred_timeout_cached_rf`, and an operator-facing warning. If no approved cached risk-free series is
available, the command must fail clearly rather than fabricate success.

Session 04 should fix the Stress Commentary wording mismatch. Minimal legacy or old-style
`hedge_gap_analysis.status = not_applicable` commentary must include the human-readable phrase
`Hedge gap: not applicable`, while full `hedge_gap_analysis_v1` commentary must remain v1-first and
must not reintroduce the old legacy phrase when v1 evidence exists. The session then runs the final
readiness gate and updates this ExecPlan with the final verdict.

## Concrete Steps

All commands run from:

    D:\Рабочий стол\КУРСОР ТУЛА ДИАГНОСТИКА

Session 01 baseline commands already run:

    .\.venv\Scripts\python.exe scripts\verify_live_core_e2e.py --profile diagnosis_only
    .\.venv\Scripts\python.exe run_portfolio_review.py --mode core --skip-candidates
    .\.venv\Scripts\python.exe -m pytest tests/test_product_bundle_hygiene.py tests/test_live_core_e2e_validation.py -q
    .\.venv\Scripts\python.exe -m pytest tests/test_stress_hedge_gap_contract.py tests/test_portfolio_commentary.py -q

Observed Session 01 results:

    verify_live_core_e2e.py --profile diagnosis_only: exit=1
    run_portfolio_review.py --mode core --skip-candidates: exit=1
    test_product_bundle_hygiene.py + test_live_core_e2e_validation.py: 10 passed
    test_stress_hedge_gap_contract.py + test_portfolio_commentary.py: 1 failed, 19 passed

Session 02 should run:

    .\.venv\Scripts\python.exe -m pytest tests/test_product_bundle_hygiene.py tests/test_live_core_e2e_validation.py -q
    .\.venv\Scripts\python.exe scripts\verify_live_core_e2e.py --profile diagnosis_only

Session 03 should run:

    .\.venv\Scripts\python.exe -m pytest tests/test_data_cache_key.py tests/test_product_bundle_integration.py -q
    .\.venv\Scripts\python.exe run_portfolio_review.py --mode core --skip-candidates

Observed Session 03 results:

    tests/test_data_cache_key.py tests/test_product_bundle_integration.py: 8 passed
    run_portfolio_review.py --mode core --skip-candidates: timed out after 304 seconds after the
    risk-free fallback created/used a current monthly cache. The remaining stall occurred later in
    shared factor/macro context and is not the FRED DTB3 risk-free blocker fixed in this session.

Session 04 fixed the remaining Stress Commentary text-surface blocker. Minimal legacy
`hedge_gap_analysis.status = not_applicable` commentary now includes the phrase
`Hedge gap: not applicable`, while the v1-primary commentary path remains preferred and does not
emit the old legacy phrase when `hedge_gap_analysis_v1` evidence is available.

Session 04 verification:

    .\.venv\Scripts\python.exe -m pytest tests/test_stress_hedge_gap_contract.py tests/test_portfolio_commentary.py -q
    20 passed

    .\.venv\Scripts\python.exe scripts\validate_block_4_live.py --refresh-diagnosis
    Block 4 v3 live validation: OK

    .\.venv\Scripts\python.exe scripts\verify_live_core_e2e.py --profile diagnosis_only
    live core E2E validation: OK

    .\.venv\Scripts\python.exe scripts\verify_docs.py
    docs verification: OK

Final verdict: `READY_TO_MOVE_FORWARD`.

Session 04 should run:

    .\.venv\Scripts\python.exe -m pytest tests/test_stress_hedge_gap_contract.py tests/test_portfolio_commentary.py -q
    .\.venv\Scripts\python.exe scripts\validate_block_4_live.py --refresh-diagnosis
    .\.venv\Scripts\python.exe scripts\verify_live_core_e2e.py --profile diagnosis_only
    .\.venv\Scripts\python.exe scripts\verify_docs.py

For wildcard pytest groups on Windows PowerShell, expand file lists instead of passing literal
globs:

    $block4 = Get-ChildItem -LiteralPath tests -Filter 'test_block_4_*.py' | ForEach-Object { $_.FullName }
    .\.venv\Scripts\python.exe -m pytest @block4 -q
    $stress = @(Get-ChildItem -LiteralPath tests -Filter 'test_stress_*.py' | ForEach-Object { $_.FullName }) + @(Get-ChildItem -LiteralPath tests -Filter 'test_hedge_gap*.py' | ForEach-Object { $_.FullName })
    .\.venv\Scripts\python.exe -m pytest @stress -q

## Validation and Acceptance

The plan is accepted only when the final diagnosis-only live gate is clean, documentation verifies,
and the focused test groups pass. The expected final success transcript includes:

    Block 4 v3 live validation: OK
    live core E2E validation: OK
    docs verification: OK

The blocker table from Session 01 is:

| Blocker | Root cause | Product impact | Fix session |
| --- | --- | --- | --- |
| Stale root candidate/compare artifacts | A previous candidate or product-one-candidate run left root artifacts such as `candidate_factory_run.json`, `candidate_comparison_registry.json`, and non-tombstone compare/decision JSON. Diagnosis-only hygiene exists but is not applied early enough when refresh fails before materialization completes. | `verify_live_core_e2e.py --profile diagnosis_only` detects `product_one_candidate` and fails, so the workspace cannot prove a clean diagnosis-only handoff. | Session 02 |
| FRED `DTB3` timeout | `run_portfolio_review.py --mode core --skip-candidates` prepares shared monthly data and calls `fetch_fred_series("DTB3", ...)`; both pandas-datareader and CSV fallback timed out during Session 01. | Diagnosis-only refresh exits before writing fresh subject artifacts and before applying reliable root tombstones, leaving stale candidate artifacts visible. | Session 03 |
| Stress Commentary wording failure | Minimal legacy `hedge_gap_analysis.status = not_applicable` commentary no longer includes the phrase expected by `test_stress_commentary_states_hedge_gap_not_applicable`. | Stress/Hedge Gap coverage is not fully green; the issue is text-surface wording, not a proven JSON handoff break. | Session 04 |

## Idempotence and Recovery

The pytest commands are safe to repeat. `scripts/verify_live_core_e2e.py` is read-only.
`run_portfolio_review.py --mode core --skip-candidates` may refresh generated artifacts under
`Main portfolio/`; those generated artifacts are not source of truth and should not be committed
unless explicitly requested. If FRED remains unavailable during Session 03 or Session 04, record
whether an approved cached risk-free fallback was used and whether metadata disclosed it. Do not
delete or revert unrelated user changes.

## Artifacts and Notes

Session 01 terminal evidence, abbreviated:

    detected_profile=product_one_candidate
    ok=False
    ERROR: diagnosis_only must not retain candidate_factory_run.json
    ERROR: candidate_comparison.json must carry no_candidate_v1 tombstone on diagnosis_only
    ERROR: current_vs_candidate.json must carry no_candidate_v1 tombstone on diagnosis_only
    ERROR: decision_verdict.json must carry no_candidate_v1 tombstone on diagnosis_only
    ERROR: diagnosis_only must not retain candidate_comparison_registry.json

    run_portfolio_review.py --mode core --skip-candidates
    Runtime mode: product_diagnosis_only
    Workflow state: diagnosis_only
    Step failed with exit code 1.
    INFO: Loading risk-free rate from FRED:DTB3...
    TimeoutError: The read operation timed out

    tests/test_product_bundle_hygiene.py tests/test_live_core_e2e_validation.py
    10 passed

    tests/test_stress_hedge_gap_contract.py tests/test_portfolio_commentary.py
    FAILED tests/test_stress_hedge_gap_contract.py::test_stress_commentary_states_hedge_gap_not_applicable
    AssertionError: assert 'Hedge gap: not applicable' in generated stress commentary text
    1 failed, 19 passed

## Interfaces and Dependencies

The stable interfaces for this work are:

- `src.product_bundle_hygiene.apply_diagnosis_only_product_bundle_hygiene(output_dir_final,
  analysis_end=None, investor_currency="USD")`, which must keep writing `no_candidate_v1`
  tombstones for diagnosis-only runs.
- `run_report.run_materialize_analysis_subject_report`, which orchestrates analysis-subject
  materialization and currently controls when hygiene is applied.
- `src.data_loader.load_monthly_data_shared`, which builds or loads return panels and risk-free
  series. Session 03 added `allow_risk_free_cached_fallback=False`; diagnosis-only
  materialization passes `True`, while candidate and legacy paths keep the default.
- `src.data_fred.fetch_fred_series`, which fetches FRED data and may raise external timeout errors.
- `src.portfolio_commentary.write_stress_commentary`, which writes the text checked by the failing
  Stress Commentary test.

Do not change optimizer, candidate generation, Decision Verdict formulas, PDF generation,
AI-generation, or portfolio weights in this remediation plan.

Revision note, 2026-06-04: Created Session 01 remediation ExecPlan from the user's approved
four-session plan. Added baseline results and the required `Blocker / Root cause / Product impact /
Fix session` table. Runtime logic was not changed.

Revision note, 2026-06-05: Completed Session 03 risk-free cached fallback. Updated progress,
decisions, evidence, outcomes, and interfaces. Recorded that the canonical live review command now
passes the risk-free blocker but still timed out later in shared factor/macro context.

Revision note, 2026-06-05: Completed Session 04 Stress Commentary wording fix and final readiness
gate. Final verdict is `READY_TO_MOVE_FORWARD`.
