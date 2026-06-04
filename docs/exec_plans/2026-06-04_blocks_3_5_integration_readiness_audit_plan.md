# Blocks 3-5 Integration Readiness Audit Plan

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`,
`Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document is maintained according to `PLANS.md` in the repository root.

## Purpose / Big Picture

This plan checks whether the current diagnosis-first product chain is ready for safe integration work from Block 3 Stress Lab through Block 4 diagnosis and Block 5 decision package. A user should be able to run the one-candidate product path and trust that Stress Lab evidence feeds Problem Classification / Candidate Launchpad, then Current vs Candidate and Decision Verdict, without accidentally using legacy optimizer-first or stale root artifacts as product truth.

Session 01 is intentionally a read-only readiness audit. It does not change formulas, schemas, runtime behavior, generated outputs, or candidate factory execution. Its observable outcome is a checked-in audit file plus focused contract tests proving that the existing integration seams are currently green.

## Progress

- [x] (2026-06-04) Session 01 completed as a read-only integration readiness audit. Evidence: `docs/audits/2026-06-04_blocks_3_5_integration_readiness_session_01.md`; focused contract bundle passed with `51 passed`; one-candidate dry-run showed the expected flow `Input -> X-Ray -> Stress -> Problem Classification -> Candidate Launchpad -> Current vs Candidate -> Decision Verdict`.
- [x] (2026-06-04) Session 02 completed as a controlled live-output validation with a qualified result. Evidence: `docs/audits/2026-06-04_blocks_3_5_integration_readiness_session_02.md`; full `run_portfolio_review.py --candidates equal_weight` could not refresh the subject because the live FRED risk-free dependency timed out after a `pandas_datareader` compatibility failure; direct `run_candidate_factory.py --candidates equal_weight --then-compare` reused the existing `equal_weight` snapshot, refreshed root compare/verdict/context JSON, and `scripts/verify_live_core_e2e.py --profile product_one_candidate` passed.
- [x] (2026-06-04) Session 03 completed as a fresh-refresh blocker recheck. Evidence: `docs/audits/2026-06-04_blocks_3_5_integration_readiness_session_03.md`; direct `fetch_fred_series("DTB3", ...)` and canonical `run_portfolio_review.py --candidates equal_weight` still failed on FRED timeout after the `pandas_datareader` compatibility error, while the existing `product_one_candidate` live validator still passed.
- [x] (2026-06-04) Session 03.1 completed as environment repair and dependency alignment. Evidence: `docs/audits/2026-06-04_blocks_3_5_integration_readiness_session_03_1.md`; `.venv` now has `pandas 2.1.4`, `numpy 1.26.4`, and `pandas_datareader 0.10.0`; `FredReader import ok`; canonical `run_portfolio_review.py --candidates equal_weight` was retried under the repaired venv and no longer showed the `deprecate_kwarg()` compatibility error, but still failed on live FRED `DTB3` timeout; existing `product_one_candidate` validator still passed.
- [x] (2026-06-04) Session 04 completed as a post-repair fresh-refresh blocker recheck. Evidence: `docs/audits/2026-06-04_blocks_3_5_integration_readiness_session_04.md`; the repaired environment persisted (`pandas 2.1.4`, `numpy 1.26.4`, `pandas_datareader 0.10.0`, `FredReader import ok`); direct FRED `DTB3` probe and canonical `run_portfolio_review.py --candidates equal_weight` still timed out on live FRED before fresh subject materialization; existing `product_one_candidate` validator still passed.

## Surprises & Discoveries

- Observation: The integration chain is already represented by focused validators and tests across Blocks 3, 4, and 5.
  Evidence: `scripts/core_mvp_validation_contract.py` exposes `check_problem_classification_v3`, `check_candidate_launchpad_v3`, `check_current_vs_candidate_v1`, and `check_decision_verdict_v1`; the Session 01 pytest bundle passed.

- Observation: The one-candidate dry-run now prints the full product flow including Blocks 4 and 5, without invoking legacy policy optimization.
  Evidence: `.\.venv\Scripts\python.exe run_portfolio_review.py --candidates equal_weight --dry-run` printed `Runtime mode: product_one_candidate`, `Workflow state: one_candidate`, and a candidate factory command with `--then-compare`.

- Observation: Session 01 did not refresh `Main portfolio/` or other generated outputs.
  Evidence: only dry-run and pytest commands were executed; no networked `run_portfolio_review.py --candidates equal_weight` live run was performed.

- Observation: Session 02 proved the one-candidate product validator can pass on the current workspace after candidate factory / compare materialization, but did not prove a fresh subject Stress Lab refresh.
  Evidence: `verify_live_core_e2e.py --profile product_one_candidate` returned `ok=True`; `Main portfolio/analysis_subject/stress_report.json` still had an older mtime than the Session 02 compare artifacts because the subject materialization step failed on FRED.

- Observation: Direct candidate factory materialization stayed within one requested candidate but reused an existing snapshot rather than rebuilding it.
  Evidence: `Main portfolio/candidate_factory_run.json` recorded `factory_profile_id: explicit_list`, `run_status: full_success`, and one step `equal_weight` with `status: skipped_existing`.

- Observation: Session 03 reconfirmed that the fresh-refresh blocker is still external FRED risk-free access, not Blocks 3-5 product-contract wiring.
  Evidence: direct `fetch_fred_series("DTB3", ...)` returned `TimeoutError`; `run_portfolio_review.py --candidates equal_weight` reached `product_one_candidate` mode and then failed while loading `FRED:DTB3`; `verify_live_core_e2e.py --profile product_one_candidate` still returned OK on the existing bundle.

- Observation: Session 03.1 cleared the local pandas/pandas-datareader compatibility blocker but did not clear live FRED access.
  Evidence: after `pip install "pandas<2.2" "pandas-datareader==0.10.0"`, the venv reported `pandas 2.1.4`, `numpy 1.26.4`, `pandas_datareader 0.10.0`, and `FredReader import ok`; the canonical one-candidate command no longer emitted `TypeError: deprecate_kwarg()`, but still timed out on FRED `DTB3`.

- Observation: Session 04 reconfirmed that the remaining fresh-refresh blocker is live FRED network access after the environment repair persisted.
  Evidence: the Session 04 probe reported Python 3.12.13, `pandas 2.1.4`, `numpy 1.26.4`, `pandas_datareader 0.10.0`, and `FredReader import ok`; direct `fetch_fred_series("DTB3", ...)` returned `TimeoutError`; canonical `run_portfolio_review.py --candidates equal_weight` reached `product_one_candidate` mode and failed while loading `FRED:DTB3`; `verify_live_core_e2e.py --profile product_one_candidate` still returned OK on the existing bundle.

## Decision Log

- Decision: Treat Session 01 as documentation and verification only.
  Rationale: The user requested only Session 01. A live candidate run or code change could mutate generated outputs and would exceed a readiness-audit boundary.
  Date/Author: 2026-06-04 / Codex.

- Decision: Use a focused cross-block contract bundle instead of full pytest for Session 01.
  Rationale: The audit question is integration readiness across Blocks 3-5, so the relevant proof is downstream stress integration, Block 4 contracts, Block 5 contracts, and AI grounding context rather than unrelated repository-wide tests.
  Date/Author: 2026-06-04 / Codex.

- Decision: Record Session 02 as `QUALIFIED_LIVE_VALIDATION`, not as a full fresh-output closure.
  Rationale: The product-one-candidate validator passed after factory/compare materialization, but the canonical full command failed before subject refresh due to a network/dependency issue outside the Blocks 3-5 integration contracts.
  Date/Author: 2026-06-04 / Codex.

- Decision: Record Session 03 as `BLOCKER_RECONFIRMED_CURRENT_BUNDLE_VALID`, not as fresh-output closure.
  Rationale: The user asked for Session 03 only. The canonical one-candidate command still failed before fresh subject materialization, but the existing materialized bundle remained validator-clean. No formulas, schemas, or implementation behavior were changed.
  Date/Author: 2026-06-04 / Codex.

- Decision: Record Session 04 as `FRED_NETWORK_BLOCKER_RECONFIRMED_AFTER_ENV_REPAIR`, not as fresh-output closure and not as a data-layer fallback implementation.
  Rationale: The repaired environment persisted and the failure is now consistently live FRED timeout. Silently bypassing FRED or changing risk-free fallback behavior would affect the data layer and must be handled as a separate spec-governed implementation task.
  Date/Author: 2026-06-04 / Codex.

## Outcomes & Retrospective

Session 01 found the Blocks 3-5 integration seams ready for a targeted live validation session. The code-level contract chain is present and focused tests pass.

Session 02 then proved that the current workspace can hold a validator-clean `product_one_candidate` bundle after candidate factory / compare materialization. The remaining unproven area is a fully fresh subject refresh through `run_portfolio_review.py --candidates equal_weight`, because that command was blocked before Block 3 refresh by the live FRED risk-free dependency.

Session 03 rechecked that remaining unproven area and found the same blocker still active. The existing product-one-candidate bundle remains valid, but a fully fresh subject Stress Lab refresh is still not proven.

Session 03.1 repaired the local Python environment so dependency versions match the project constraints, then reran the same fresh-refresh validation. The import-time compatibility blocker is cleared; live FRED `DTB3` timeout remains the blocker for fresh subject refresh.

Session 04 rechecked the same fresh-refresh path after the environment repair and found the same external FRED timeout. The existing product-one-candidate bundle remains valid, but fresh subject materialization is still not proven.

## Context and Orientation

The repository root is `D:\Рабочий стол\КУРСОР ТУЛА ДИАГНОСТИКА`. The current product is diagnosis-first and current-portfolio-first. Portfolio-first subject artifacts live under `{output_dir_final}/analysis_subject/`, usually `Main portfolio/analysis_subject/`.

Block 3 means Stress Lab product evidence on `analysis_subject/stress_report.json`. The key product fields are `stress_results_v1`, `hedge_gap_analysis_v1`, and `current_portfolio_stress_scorecard_v1`.

Block 4 means diagnosis outputs under `analysis_subject/`: `problem_classification.json` with schema `problem_classification_v3`, and `candidate_launchpad.json` with schema `candidate_launchpad_v3`.

Block 5 means post-compare root artifacts: `current_vs_candidate.json` with schema `current_vs_candidate_v1`, and `decision_verdict.json` with schema `decision_verdict_v1`. These are authoritative only after a compare run such as `python run_portfolio_review.py --candidates equal_weight`; diagnosis-only runs use `no_candidate_v1` tombstones for root compare/verdict files.

Important files:

- `src/stress_results_block.py`, `src/hedge_gap_analysis_block.py`, and `src/current_portfolio_stress_scorecard_block.py` build Block 3 product adapters.
- `src/problem_classification.py` and `src/block_4/diagnosis_builder.py` build and write Block 4 diagnosis artifacts.
- `src/candidate_comparison.py` writes comparison outputs and includes Block 3 peer slices such as `hedge_gap_comparison` and `stress_scorecard_comparison`.
- `src/current_vs_candidate.py` and `src/decision_verdict.py` build Block 5 product adapters.
- `src/ai_commentary_context.py` builds grounding context after the decision package and includes Block 3 context when available.
- `scripts/core_mvp_validation_contract.py` owns product-contract validators used by tests and live E2E validation.

## Plan of Work

Session 01 records the existing state and does not modify behavior. It verifies the integration seams using focused tests, confirms the dry-run flow for one explicit candidate, and writes a concise audit file with readiness verdict, evidence, and remaining risk.

If a future Session 02 is requested, it should run a fresh product-one-candidate live validation in a controlled output directory or with explicit approval to refresh generated outputs. It should then inspect `analysis_subject/stress_report.json`, `analysis_subject/problem_classification.json`, `analysis_subject/candidate_launchpad.json`, root `current_vs_candidate.json`, root `decision_verdict.json`, and `ai_commentary_context.json`, and record whether all live artifacts satisfy their validators.

Session 02 was requested and executed on 2026-06-04. It did not change implementation behavior. It attempted the canonical one-candidate command first, then used direct factory/compare materialization after the canonical command hit a live FRED dependency timeout.

## Concrete Steps

All commands are run from:

    D:\Рабочий стол\КУРСОР ТУЛА ДИАГНОСТИКА

Use the repository virtual environment:

    .\.venv\Scripts\python.exe

Session 01 commands executed:

    .\.venv\Scripts\python.exe -m pytest tests/test_stress_downstream_integration.py tests/test_problem_classification.py tests/test_candidate_launchpad.py tests/test_block_4_decision_entry_contract.py tests/test_block_5_decision_compare_contract.py tests/test_current_vs_candidate.py tests/test_decision_verdict.py tests/test_ai_commentary_context.py -q

Expected and observed result:

    51 passed

Dry-run command executed:

    .\.venv\Scripts\python.exe run_portfolio_review.py --candidates equal_weight --dry-run

Expected and observed proof points:

    Mode: product_one_candidate
    Flow: Input -> X-Ray -> Stress -> Problem Classification -> Candidate Launchpad -> Current vs Candidate -> Decision Verdict
    Workflow state: one_candidate
    run_candidate_factory.py --candidates equal_weight --execution-mode standard --output-profile site_api --then-compare

Session 02 commands executed:

    .\.venv\Scripts\python.exe -m ensurepip --upgrade
    .\.venv\Scripts\python.exe -m pip install setuptools
    .\.venv\Scripts\python.exe run_portfolio_review.py --candidates equal_weight
    .\.venv\Scripts\python.exe scripts\verify_live_core_e2e.py --profile product_one_candidate
    .\.venv\Scripts\python.exe run_candidate_factory.py --candidates equal_weight --then-compare
    .\.venv\Scripts\python.exe scripts\verify_live_core_e2e.py --profile product_one_candidate

Session 02 observed results:

    run_portfolio_review.py --candidates equal_weight: failed during subject materialization on FRED risk-free loading.
    verify before factory materialization: failed as diagnosis_only; missing candidate_factory_run.json.
    run_candidate_factory.py --candidates equal_weight --then-compare: full_success with equal_weight skipped_existing.
    verify after factory materialization: live core E2E validation OK for product_one_candidate.

Session 03 commands executed:

    @'
    from src.data_fred import fetch_fred_series
    try:
        s = fetch_fred_series('DTB3','2026-01-01','2026-06-04')
        print('ok', len(s), s.tail().to_dict())
    except Exception as e:
        print('ERR', type(e).__name__, e)
    '@ | .\.venv\Scripts\python.exe -
    .\.venv\Scripts\python.exe run_portfolio_review.py --candidates equal_weight
    .\.venv\Scripts\python.exe scripts\verify_live_core_e2e.py --profile product_one_candidate

Session 03 observed results:

    fetch_fred_series("DTB3", ...): failed with TimeoutError.
    run_portfolio_review.py --candidates equal_weight: failed during subject materialization on FRED risk-free loading after entering product_one_candidate mode.
    verify existing materialized bundle: live core E2E validation OK for product_one_candidate.

Session 03.1 commands executed:

    .\.venv\Scripts\python.exe -m pip install "pandas<2.2" "pandas-datareader==0.10.0"

    # compatibility check: pandas/numpy/pandas_datareader versions plus FredReader import
    # FRED probe, canonical one-candidate retry, and product_one_candidate validator

Session 03.1 observed results:

    pip install: downgraded pandas from 3.0.2 to 2.1.4 and numpy from 2.4.4 to 1.26.4.
    compatibility check: pandas 2.1.4, numpy 1.26.4, pandas_datareader 0.10.0, FredReader import ok.
    fetch_fred_series("DTB3", ...): no import-time compatibility error; still failed with TimeoutError.
    run_portfolio_review.py --candidates equal_weight: entered product_one_candidate mode under the repaired venv; no deprecate_kwarg compatibility error; still failed during FRED risk-free loading on ReadTimeout/TimeoutError.
    verify existing materialized bundle: live core E2E validation OK for product_one_candidate.

Session 04 commands executed:

    # environment compatibility plus direct FRED probe
    .\.venv\Scripts\python.exe run_portfolio_review.py --candidates equal_weight
    .\.venv\Scripts\python.exe scriptserify_live_core_e2e.py --profile product_one_candidate

Session 04 observed results:

    compatibility check: Python 3.12.13, pandas 2.1.4, numpy 1.26.4, pandas_datareader 0.10.0, FredReader import ok.
    fetch_fred_series("DTB3", ...): still failed with TimeoutError.
    run_portfolio_review.py --candidates equal_weight: reached product_one_candidate mode and then failed during FRED risk-free loading on ReadTimeout/TimeoutError before fresh subject materialization.
    verify existing materialized bundle: live core E2E validation OK for product_one_candidate.

## Validation and Acceptance

Session 01 is accepted when the audit file exists, the focused pytest bundle passes, the one-candidate dry-run shows the product flow through Decision Verdict, and no code behavior or generated portfolio outputs were changed.

Session 01 does not prove that the current on-disk `Main portfolio/` artifacts are fresh. That proof belongs to a later live-output session.

Session 02 is accepted as a qualified live validation when the Session 02 audit file exists, the canonical command failure is recorded with its blocker, direct factory/compare materialization is recorded, and `scripts/verify_live_core_e2e.py --profile product_one_candidate` passes after materialization. It is not accepted as proof of a fully fresh subject Stress Lab refresh.

Session 03 is accepted as a blocker recheck when the Session 03 audit file exists, the direct FRED probe and canonical command result are recorded, and the existing `product_one_candidate` validator result is recorded. It is not accepted as proof of a fully fresh subject Stress Lab refresh.

Session 03.1 is accepted because the environment matches project constraints, the FRED loader executes without the import-time compatibility error, and the canonical one-candidate refresh was retried under the repaired venv. The session does not prove fresh subject refresh because live FRED `DTB3` still timed out.

Session 04 is accepted as a post-repair blocker recheck when the Session 04 audit file exists, the environment/FRED probe and canonical command result are recorded, and the existing `product_one_candidate` validator result is recorded. It is not accepted as proof of a fully fresh subject Stress Lab refresh.

## Idempotence and Recovery

Session 01 is safe to repeat. The pytest command is read-only. The dry-run command does not run builders or write candidate artifacts. The audit and plan files can be edited idempotently as long as their evidence remains accurate.

If a later live validation mutates generated outputs unintentionally, do not commit generated folders unless the user explicitly asks for generated artifact refresh. Follow `OUTPUTS.md` generated-output boundaries.

## Artifacts and Notes

Session 01 produced:

- `docs/exec_plans/2026-06-04_blocks_3_5_integration_readiness_audit_plan.md`
- `docs/audits/2026-06-04_blocks_3_5_integration_readiness_session_01.md`

No implementation files were changed.

Session 02 produced:

- `docs/audits/2026-06-04_blocks_3_5_integration_readiness_session_02.md`
- refreshed generated root JSON under `Main portfolio/` through candidate factory / compare materialization, including `candidate_factory_run.json`, `candidate_comparison.json`, `current_vs_candidate.json`, `decision_verdict.json`, and `ai_commentary_context.json`

No implementation files were changed.

Session 03 produced:

- `docs/audits/2026-06-04_blocks_3_5_integration_readiness_session_03.md`

No implementation files were changed.

Session 03.1 produced:

- `docs/audits/2026-06-04_blocks_3_5_integration_readiness_session_03_1.md`

No implementation files were changed.

Session 04 produced:

- `docs/audits/2026-06-04_blocks_3_5_integration_readiness_session_04.md`

No implementation files were changed.

## Interfaces and Dependencies

The plan depends only on local Python tests and existing repository validators. It does not require web access or market-data downloads in Session 01.

Stable validation interfaces for later sessions:

- `scripts.core_mvp_validation_contract.check_problem_classification_v3`
- `scripts.core_mvp_validation_contract.check_candidate_launchpad_v3`
- `scripts.core_mvp_validation_contract.check_current_vs_candidate_v1`
- `scripts.core_mvp_validation_contract.check_decision_verdict_v1`
- `src.live_core_e2e.validate_live_core_artifacts`

Revision note, 2026-06-04: Created this ExecPlan and completed Session 01 only because the user asked for "Blocks 3-5 Integration Readiness Audit Plan" Session 01 only.

Revision note, 2026-06-04 Session 02: The user then requested Session 02 only. Completed a qualified live validation: canonical subject refresh was blocked by FRED, direct factory/compare materialization passed the product-one-candidate live validator.

Revision note, 2026-06-04 Session 03: The user then requested Session 03 only. Rechecked the fresh one-candidate refresh blocker; FRED `DTB3` loading still timed out, and the existing product-one-candidate bundle still passed live validation.

Revision note, 2026-06-04 Session 03.1: User requested a separate follow-up session for environment repair. Plan now reserves Session 03.1 for venv/dependency alignment before the next fresh-refresh retry.

Revision note, 2026-06-04 Session 03.1 closure: Repaired `.venv` dependency drift (`pandas 2.1.4`, `numpy 1.26.4`, `pandas_datareader 0.10.0`) and confirmed `FredReader import ok`; canonical one-candidate refresh was retried and is now blocked only by live FRED `DTB3` timeout, while the existing product-one-candidate bundle still validates.

Revision note, 2026-06-04 Session 04: User requested Session 04. Rechecked the post-repair fresh one-candidate refresh path; environment alignment persisted, FRED `DTB3` still timed out, and the existing product-one-candidate bundle still validated.
