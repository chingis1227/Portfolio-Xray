# Full Demo MVP Readiness Audit and Hardening

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`,
`Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This file follows `PLANS.md` from the repository root. It is self-contained so a future Codex
chat can resume from this file without relying on earlier conversation memory.

The next implementation chat must begin with Session 01 only. Session 00 is complete in this file.
If Session 01 succeeds, the implementer must stop at the end of Session 01 and leave later sessions
for later chats unless the user explicitly approves continuing. The Session 00 stop rule from the
originating request was: after Session 00 is fully complete, report
Legacy note normalized to English-only text.

## Purpose / Big Picture

Portfolio MRI / Portfolio X-Ray is a diagnosis-first investment decision-support system. The user
does not need another optimizer cockpit. The user needs to understand the current portfolio problem,
see one reasonable hypothesis tested, understand the trade-off, and know whether action is justified.

The purpose of this plan is to harden the already-implemented vertical MVP loop into a reliable,
understandable, demo-ready product path. The product story to prove is:

- I understand the portfolio problem.
- I tested one reasonable alternative.
- I see what improved and what worsened.
- I understand whether changing the portfolio is justified.

This plan must not add major new product features. It should only make the current path more reliable,
clearer, faster where safe, and more trustworthy. The final status may be `FULL_DEMO_MVP_READY` only
if the product story works across three demo portfolios without oral explanation from the developer.

## Progress

- [x] 2026-06-05 20:39+02:00: Session 00 started. Baseline commands collected current dirty tree,
  root `Main portfolio` outputs, and `Main portfolio/analysis_subject` outputs before writing this
  plan.
- [x] 2026-06-05 20:39+02:00: Session 00 recorded that the working tree was already heavily dirty
  before this plan file was added, including modified source, tests, docs, and untracked Blocks 5-9
  implementation files.
- [x] 2026-06-05 20:39+02:00: Session 00 confirmed the successful output chain already exists on disk:
  root `candidate_generation.json`, `current_vs_candidate.json`, `decision_verdict.json`,
  `ai_commentary_context.json`, and `analysis_subject/problem_classification.json`,
  `analysis_subject/candidate_launchpad.json`, `analysis_subject/portfolio_alternatives_builder.json`.
- [x] 2026-06-05 20:39+02:00: Session 00 wrote this ExecPlan file under `docs/exec_plans/`.
- [x] 2026-06-05 20:39+02:00: Session 00 updated `docs/exec_plans/README.md` so this plan is the
  active readiness hardening plan.
- [x] 2026-06-05: Session 00 ran `.\.venv\Scripts\python.exe scripts\verify_docs.py` after writing
  the plan and updating the register. Result: passed.
- [x] 2026-06-05 20:47+02:00: Session 01 completed. Product-critical tests for Block 6 Builder
  setup, Block 7 Candidate Generation, Block 8 Current vs Candidate, Block 9 Decision Verdict,
  Blocks 5-9 vertical flow, AI Commentary context, and docs validation were identified and run.
  All focused baseline checks passed: 45 Block 6 tests, 18 Candidate Generation tests, 12 Block 8
  tests, 16 Block 9 tests, 15 vertical/AI tests, and `scripts/verify_docs.py`.
- [x] 2026-06-05 23:02+02:00: Session 02 completed as a live acceptance attempt with blockers
  recorded. Three source-controlled demo configs were added under `config/demo_portfolios/`, and
  `--config` plumbing was added for the vertical demo path. Balanced and equity-heavy fixtures
  completed the fast vertical JSON chain, but Block 8 had unavailable candidate metrics, so the
  verdict was `evidence_insufficient`. The defensive/rates-sensitive fixture honestly stopped at a
  monitor-only / builder-blocked path before candidate generation. A standard-mode candidate attempt
  was tried to create fresh comparison snapshots, but it timed out after 904 seconds and was stopped.
- [x] 2026-06-05 23:22+02:00: Session 03 completed. Runtime entrypoints were clarified into diagnosis-only, generate-candidate, compare/verdict, full-demo, compatibility, and advanced/research categories. `run_portfolio_review.py --help` now works in a default Windows/CP1251 console without requiring `PYTHONIOENCODING=utf-8`, and its candidate flags now label `--candidates` as an explicit backend factory-id compatibility path rather than the canonical Builder-to-Block-7 product handoff.
- [x] 2026-06-05 23:29+02:00: Session 04 completed: Stale artifact hygiene and output freshness. Product-run freshness metadata was added to the Blocks 5-9 vertical artifact chain; Block 8 now refuses tombstoned/not-authoritative/inactive candidate_generation evidence; AI Commentary grounding ignores explicitly mismatched verdict run lineage instead of citing stale verdict evidence. Focused stale-artifact and adjacent vertical/AI tests passed, then docs verification passed.
- [x] 2026-06-05: Session 05 completed: FRED / factor matrix performance and reliability
  hardening. Existing factor-cache behavior from the dedicated FRED stabilization plan was verified
  with focused tests. The factor path now requests bounded-date FRED CSV data, uses a shorter
  factor-specific live-fetch budget before approved-cache fallback, and has an operator
  `scripts/warm_factor_cache.py` smoke. In the current environment, full factor cache is still not
  valid for the 2007-01-01..2026-06-05 demo range and live FRED is partially timing out, but the
  failure is now fast and explicit rather than a multi-minute hang.
- [x] 2026-06-05: Session 06 completed: Output quality audit. A written audit note was added at
  `docs/audits/2026-06-05_full_demo_mvp_output_quality_audit_session_06.md` and registered in
  `docs/audits/README.md`. The verdict remains `NOT_ACCEPTED_YET`: the outputs are truthful and do
  not overclaim, but balanced/equity-heavy cannot explain what improved or worsened because Block 8
  candidate metrics are unavailable, and defensive/rates-sensitive is an honest Builder-blocked case
  rather than a complete comparison/verdict demo.
- [x] 2026-06-05: Session 07 completed: AI Commentary grounding. The context now includes
  deterministic `client_explanation_draft` and `light_decision_journal` sections, admits missing
  or unavailable evidence instead of inventing metrics, and can cite blocked Builder status for
  monitor/data-quality cases. Focused AI/vertical/path and adjacent verdict/comparison tests passed.
- [x] 2026-06-05: Session 08 completed: Legacy path classification. Runtime banners, dry-run
  summaries, root legacy wrappers, README, runtime entrypoints, operator guide, and workflow
  spec now label explicit factory-id compatibility, advanced/research candidate factory, and
  legacy runner paths so they are not confused with the canonical Blocks 5-9 demo path.
- [x] 2026-06-06: Session 09 completed: Product demo package. A practical operator guide was added
  at `docs/demo/full_demo_mvp.md` and linked from README. It covers the three demo configs, canonical
  vertical commands, read order, expected outputs, verdict interpretation, and known limitations
  without presenting unavailable comparison metrics as product proof.
- [x] 2026-06-06: Session 10 completed: Final readiness gate. Focused product-critical tests, stale-artifact/runtime-label regressions, factor-cache check, existing three-demo-output inspection, and docs validation were run or classified. Final status is `DEMO_READY_WITH_LIMITATIONS`, not `FULL_DEMO_MVP_READY`, because balanced/equity-heavy still lack grounded improvement/worsening comparison metrics and the full-range FRED/factor cache gate is not demo-safe for fresh live reruns.
- [x] 2026-06-06: Session 11 completed: Three-portfolio vertical demo rerun after the FRED fix.
  The factor-cache check is now demo-safe (`cache_status: valid`, `missing_series: []`,
  `full_factor_matrix_available: true`, `demo_safe: true`) and all three standard vertical runs
  produced fresh Block 8 improvements/worsening. Final status remains
  `DEMO_READY_WITH_LIMITATIONS` because Block 7 still records failed candidate generation while
  Block 8 has comparison evidence, causing Block 9 and AI grounding to contradict the comparison.
- [x] 2026-06-06: Session 12 completed: Block 7-8-9 handoff consistency fix. Block 7 now reads
  `candidate_factory_run.json` from the same config-isolated output directory used by the factory,
  generated candidates require non-empty weights and `can_compare=true`, Block 8 blocks normal
  comparison when Block 7 is failed/infeasible or mismatched, Decision Verdict uses consistent
  Block 7/8 evidence, and AI Commentary flags future candidate/comparison contradictions. The three
  standard demo fixtures reran successfully with generated candidates, weights, available
  comparisons, consistent verdicts, no AI contradiction, demo-safe factor cache, focused tests, and
  docs validation. Final status is `FULL_DEMO_MVP_READY`.

## Surprises & Discoveries

- Observation: The repository was already dirty before this plan file was created.
  Evidence: Session 00 `git status --short` showed modified top-level docs such as `ARCHITECTURE.md`,
  `CHANGELOG.md`, `DECISIONS.md`, `OUTPUTS.md`, `PRODUCT.md`, `README.md`, `SPEC.md`, `TESTING.md`,
  `WORKFLOW.md`; modified runtime/source files such as `run_compare_variants.py`, `run_report.py`,
  `src/ai_commentary_context.py`, `src/current_vs_candidate.py`, `src/decision_verdict.py`,
  `src/portfolio_alternatives_builder.py`; and many untracked Blocks 5-9 files such as
  `scripts/run_blocks_5_to_9_vertical_flow.py`, `scripts/generate_candidate_from_builder_setup.py`,
  `src/candidate_generation.py`, and focused tests.

- Observation: The live vertical product chain already exists on disk from a prior run.
  Evidence: Session 00 found root `Main portfolio/candidate_generation.json`,
  `Main portfolio/current_vs_candidate.json`, `Main portfolio/decision_verdict.json`, and
  `Main portfolio/ai_commentary_context.json` with `LastWriteTime` 2026-06-05 around 20:02, plus
  `Main portfolio/analysis_subject/problem_classification.json`,
  `candidate_launchpad.json`, and `portfolio_alternatives_builder.json` with `LastWriteTime`
  2026-06-05 around 20:01.

- Observation: The known FRED / factor runtime issue must remain a readiness blocker until controlled.
  Evidence: The closed Blocks 5-9 vertical product loop plan records that the first live vertical
  command timed out after roughly 304 seconds, the diagnosis-only command completed in about 547
  seconds with FRED/factor timeout warnings and cached fallbacks, and the vertical flow completed
  only after allowing about 651 seconds.

- Observation: Windows console encoding can affect runtime command clarity.
  Evidence: During planning exploration, `run_portfolio_review.py --help` raised a
  `UnicodeEncodeError` in a CP1251 console because help text contains a Unicode arrow. Running with
  `PYTHONIOENCODING=utf-8` printed help successfully. Session 03 should treat this as a runtime
  clarity issue for demos on Windows.

- Observation: Session 01 found all named product-critical baseline test files present; no missing
  test file or PowerShell wildcard issue blocked the focused baseline.
  Evidence: The test inventory found eight `test_block_6_*.py` files, four
  `test_candidate_generation_*.py` files, five Block 8 files, six Block 9 files, and the three
  vertical/AI files named in this plan.

- Observation: The offline product-critical baseline is green, but it does not prove live demo
  readiness across multiple portfolios.
  Evidence: Session 01 ran only focused pytest/doc checks and did not run live market-data commands
  or create the three demo fixtures planned for Session 02.

- Observation: Session 02 proved config-isolated demo runs can be launched, but it did not prove a
  complete human-understandable demo path.
  Evidence: `balanced.yml` and `equity_heavy.yml` completed
  `scripts/run_blocks_5_to_9_vertical_flow.py --config ... --method equal_weight --force-candidate`
  and wrote the required root JSON chain. In both cases `current_vs_candidate.json` marked the
  equal-weight comparison `status: unavailable`, with no `what_improved` or `what_worsened`, and
  `decision_verdict.json` returned `verdict_id: evidence_insufficient` / "Review missing or
  degraded evidence before acting." This is honest, but not demo-ready without explanation.

- Observation: The defensive/rates-sensitive fixture is a valid blocked case, not a completed
  candidate comparison.
  Evidence: `config/demo_portfolios/defensive_rates_sensitive.yml` produced
  `problem_classification.json`, `candidate_launchpad.json`, and
  `portfolio_alternatives_builder.json`, but the selected card was monitor-only and Builder returned
  `status: blocked`, `reason: data_quality_blocker`, `can_generate_candidate: false`. Root
  `candidate_generation.json`, `current_vs_candidate.json`, `decision_verdict.json`, and
  `ai_commentary_context.json` were therefore not written for this fixture.

- Observation: Fresh candidate comparison snapshots are still blocked by the known runtime/factor
  performance path.
  Evidence: changing the one-candidate backend delegation to `standard` mode and running balanced
  with `--factory-execution-mode standard` reached equal-weight weight files, then timed out after
  904 seconds before the vertical flow could write Block 8/9 outputs. The orphaned Python processes
  from that timed-out run were stopped manually. The vertical CLI now exposes
  `--factory-execution-mode` so future sessions can explicitly retry standard mode after Session 05
  hardens FRED/factor runtime behavior, while the default remains `fast`.

- Observation: Windows subprocess output decoding needed local hardening.
  Evidence: the first balanced live run completed, but background reader threads raised CP1251
  `UnicodeDecodeError` while reading captured subprocess output. Session 02 set captured subprocess
  decoding to UTF-8 with replacement in the vertical flow and candidate-generation helper.

- Observation: Session 03 found one remaining Windows `--help` blocker in `run_portfolio_review.py`.
  Evidence: running `run_portfolio_review.py --help` without `PYTHONIOENCODING` raised
  `UnicodeEncodeError` on a Unicode arrow in argparse help. The help text was changed to ASCII-safe
  wording and retested successfully in the same default PowerShell environment.

- Observation: The docs were mostly already aligned on the vertical demo script, but one anti-pattern
  still routed a one-hypothesis demo to `run_portfolio_review.py --candidates <id>`.
  Evidence: Session 03 changed that operator guidance so the canonical demo points to
  `scripts/run_blocks_5_to_9_vertical_flow.py --method <id>`, while `--candidates` remains an explicit
  backend factory-id compatibility path.

- Observation: Session 04 found the safest stale-artifact fix is metadata-plus-guards, not broad deletion.
  Evidence: vertical runs now stamp `portfolio_alternatives_builder.json`, `candidate_generation.json`,
  `candidate_comparison.json`, `current_vs_candidate.json`, `decision_verdict.json`, and
  `ai_commentary_context.json` with a shared optional `product_run.run_id`. Diagnosis-only tombstones
  remain `artifact_status: not_authoritative` and inactive; Block 8 rejects inactive candidate-generation
  evidence; AI Commentary drops mismatched verdict evidence and emits `artifact_lineage_mismatch:*`.

- Observation: Session 05 found that the checked-in FRED stabilization behavior was directionally
  correct but still too slow when no valid factor cache exists and live FRED times out.
  Evidence: `scripts/warm_factor_cache.py --check-only --start 2007-01-01 --end 2026-06-05`
  failed in 0.186s because cache coverage was missing/too short for the full demo range. Before the
  factor-specific live budget change, `scripts/warm_factor_cache.py --start 2007-01-01 --end
  2026-06-05` took 282.157s and every FRED-backed full-matrix series timed out or lacked valid
  approved cache.

- Observation: Session 05 made FRED/factor failure predictable, but did not create valid full-range
  factor cache in this environment.
  Evidence: after bounding the factor live-fetch budget, the same warm command failed in 45.355s
  instead of 282.157s. `BAMLH0A0HYM2` and `WEI` loaded live and wrote/updated cache, while `SP500`,
  `DFII10`, `T10YIE`, `BAA10Y`, `DTWEXBGS`, `VIXCLS`, and `DCOILWTICO` still timed out without
  valid full-range approved cache. Direct `build_factor_matrix('2007-01-01', '2026-06-05')` failed
  clearly in 7.431s on `DFII10` with `FactorDataUnavailableError`.

- Observation: Session 06 found that the existing demo outputs are truthful but not yet a complete
  human-understandable full-demo story.
  Evidence: balanced and equity-heavy both have clear Launchpad -> Builder -> Candidate Generation
  lineage for an Equal Weight reference test and a consistent `evidence_insufficient` verdict, but
  `current_vs_candidate.json` has comparison status `unavailable`, 12/12 unavailable dimensions, and
  empty `what_improved` / `what_worsened`. Defensive/rates-sensitive has a clear
  `weak_crisis_resilience` diagnosis and a Builder block (`reason: data_quality_blocker`,
  `can_generate_candidate: false`), but no root candidate/comparison/verdict artifacts.

- Observation: Session 08 found remaining confusion risk in labels rather than formulas.
  Evidence: docs already distinguished the vertical script from `run_portfolio_review.py --candidates`,
  but runtime banners and a test docstring still allowed future operators to read explicit candidate
  execution as the canonical demo path. Session 08 added explicit path-classification lines for
  compatibility and research paths, and legacy root wrappers now warn before delegating.

- Observation: Session 09 did not remove the remaining human-understandability blocker; it made it
  visible and operable.
  Evidence: `docs/demo/full_demo_mvp.md` documents that balanced and equity-heavy can still reach
  `evidence_insufficient` when Block 8 comparison metrics are unavailable, and that
  defensive/rates-sensitive can honestly stop at Builder with `reason: data_quality_blocker`.


- Observation: Session 10 confirmed the repo is demo-usable only with explicit limitations.
  Evidence: Focused product-critical tests passed, and the three demo output folders are explainable
  as two evidence-insufficient flows plus one Builder-blocked flow, but balanced/equity-heavy still
  have empty `what_improved` / `what_worsened` and defensive/rates-sensitive still has no
  post-candidate root artifact chain because Builder blocks generation.

- Observation: The factor/FRED gate is fast and explicit but not full-demo-ready for fresh live reruns.
  Evidence: `scripts/warm_factor_cache.py --check-only --start 2007-01-01 --end 2026-06-05`
  returned `EXIT_CODE=1` in about 3.247 seconds with named cache-coverage failures for required
  FRED-backed factor series.

- Observation: Session 11 confirmed the FRED/factor blocker is closed for this demo gate, but found
  a stricter product-chain blocker.
  Evidence: `scripts/warm_factor_cache.py --check-only --start 2007-01-01 --end 2026-06-05`
  returned `status: ok`, `source_used: cache_hit`, `cache_status: valid`, `missing_series: []`,
  `full_factor_matrix_available: true`, and `demo_safe: true`. The three standard vertical runs had
  no FRED/timeout warnings and refreshed fixture-specific product-bundle JSON. However,
  `candidate_generation.json` still says `generation_status: failed` / `weights: null`, while
  `current_vs_candidate.json` is `status: available` with meaningful `what_improved` and
  `what_worsened`. `decision_verdict.json` therefore remains `evidence_insufficient` for
  `candidate_generation_failed`, which contradicts the available comparison evidence.

- Observation: Session 12 found the contradiction was a config-output handoff bug, not an optimizer
  or factor-data problem.
  Evidence: `run_candidate_factory.py --config config/demo_portfolios/<fixture>.yml` wrote
  `candidate_factory_run.json` under each fixture's `output_dir_final`, while
  `scripts/generate_candidate_from_builder_setup.py` read the legacy default
  `Main portfolio/candidate_factory_run.json`. After resolving the default factory summary path from
  the same config used by the factory, all three demo `candidate_generation.json` artifacts changed
  from failed/null weights to generated/non-empty weights, and Block 8/9/AI became consistent.

## Decision Log

- Decision: This readiness plan is active and supersedes the previous "Active: none" pointer.
  Rationale: The user explicitly requested a checked-in plan and current/active registration before
  implementation work. The prior Blocks 5-9 plan is complete and remains historical evidence.
  Date/Author: 2026-06-05 / Codex.

- Decision: Session 00 is docs-only and must stop before Session 01.
  Rationale: The user explicitly required Plan Mode first, then Session 00 completion, a success
  report, and no Session 01 work in the same chat. This protects the baseline from being mixed with
  implementation changes.
  Date/Author: 2026-06-05 / Codex.

- Decision: `FULL_DEMO_MVP_READY` requires human-understandable results for all three demo portfolios.
  Rationale: Passing tests and writing JSON are insufficient if a user, advisor, or investor still
  needs the original developer to explain what happened.
  Date/Author: 2026-06-05 / Codex.

- Decision: Session 01 is accepted as a focused offline baseline, not a live readiness gate.
  Rationale: The session objective is to identify and run product-critical tests and classify
  failures. Since all focused checks passed, no product code change or failure classification was
  needed. Live multi-portfolio proof remains Session 02.
  Date/Author: 2026-06-05 / Codex.

- Decision: Session 02 should not declare the multi-portfolio demo path accepted.
  Rationale: Although two fixtures complete the fast JSON chain and the third blocks honestly, the
  two completed chains do not answer "what improved / what worsened" because candidate metrics are
  unavailable. The hard human-understandability gate therefore remains unmet.
  Date/Author: 2026-06-05 / Codex.

- Decision: Keep fast one-candidate generation as the default for now, but expose
  `--factory-execution-mode standard`.
  Rationale: `standard` is the likely path to fresh candidate metrics, but it timed out in the live
  balanced attempt before Session 05 performance hardening. Defaulting to standard now would make
  the vertical CLI fragile; hiding the option would make the blocker harder to retest.
  Date/Author: 2026-06-05 / Codex.

- Decision: Treat `run_portfolio_review.py --candidates <id>` as an explicit backend factory-id
  compatibility path, not the canonical full-demo command.
  Rationale: The staged product journey must visibly pass through Launchpad, Builder setup, Block 7
  Candidate Generation, Block 8 comparison, and Block 9 verdict. The vertical script is the command
  that proves that artifact loop.
  Date/Author: 2026-06-05 / Codex.

- Decision: Use `product_run` freshness metadata and reader guards for vertical output freshness.
  Rationale: Historical artifacts can be useful, so the readiness hardening should not broadly delete
  prior JSON. A shared run id lets readers verify that candidate generation, comparison, verdict, and
  AI Commentary grounding belong to the same vertical command.
  Date/Author: 2026-06-05 / Codex.

- Decision: Bound full factor-matrix FRED waits at the raw factor-series layer, not by adding an
  equity-only demo shortcut.
  Rationale: The product needs full factor evidence when it claims full factor diagnostics. If live
  FRED is unavailable and approved cache is invalid, the safer behavior is a fast explicit
  `FactorDataUnavailableError`, with operator warm/cache evidence, rather than a long hang or a
  silent downgrade to equity-only factor exposure.
  Date/Author: 2026-06-05 / Codex.

- Decision: Keep `run_portfolio_review.py --candidates <id>` callable but label it as an explicit
  factory-id compatibility path.
  Rationale: It remains useful for known backend ids and existing tests, but the current demo must
  prove the visible Launchpad -> Builder setup -> Block 7 -> compare -> verdict loop through
  `scripts/run_blocks_5_to_9_vertical_flow.py --method <id>`.
  Date/Author: 2026-06-05 / Codex.


- Decision: Final Session 10 status is `DEMO_READY_WITH_LIMITATIONS`, not `FULL_DEMO_MVP_READY` and
  not `NOT_READY_BLOCKED`.
  Rationale: The current repository state can support an honest limited demo with diagnosis, one
  reference-hypothesis attempt where allowed, evidence-insufficient safety behavior, and a clear
  Builder-blocked example. It cannot satisfy the hard full-ready gate because not all three demo
  portfolios can show grounded improvement/worsening trade-offs, and fresh full live reruns remain
  constrained by FRED/factor cache readiness.
  Date/Author: 2026-06-06 / Codex.

- Decision: Session 11 status remains `DEMO_READY_WITH_LIMITATIONS` rather than
  `FULL_DEMO_MVP_READY`.
  Rationale: The prior FRED/factor blocker is cleared and Block 8 now has meaningful trade-off
  evidence under standard mode, but a client still needs developer explanation because Block 7,
  Block 8, Block 9, and AI grounding do not tell one consistent story.
  Date/Author: 2026-06-06 / Codex.

- Decision: Session 12 status is `FULL_DEMO_MVP_READY`.
  Rationale: The Block 7/8/9/AI contradiction was fixed at the source-of-truth handoff, not hidden
  in the verdict. All three standard demo fixtures now have generated candidate weights, available
  Block 8 comparisons, consistent Decision Verdicts, no AI grounding contradiction, a demo-safe
  factor cache check, focused tests, and docs verification.
  Date/Author: 2026-06-06 / Codex.

## Outcomes & Retrospective


Session 10 outcome: final readiness gate completed with status `DEMO_READY_WITH_LIMITATIONS`. A
readiness audit was added at `docs/audits/2026-06-06_full_demo_mvp_readiness_gate_session_10.md`
and registered in `docs/audits/README.md`. The focused regression suite is green and the demo guide
can explain the current honest outcomes, but `FULL_DEMO_MVP_READY` remains blocked by unavailable
Block 8 improvement/worsening evidence for balanced/equity-heavy and by full-range FRED/factor cache
readiness for fresh live demo safety.

Session 11 outcome: post-FRED-fix three-portfolio rerun completed with status
`DEMO_READY_WITH_LIMITATIONS`. A new audit was added at
`docs/audits/2026-06-06_three_portfolio_vertical_demo_rerun_after_fred_fix.md` and registered in
`docs/audits/README.md`. The FRED/factor cache gate is now demo-safe and all three standard vertical
runs produce meaningful Block 8 comparison trade-offs. `FULL_DEMO_MVP_READY` remains blocked because
Block 7 marks candidate generation failed despite fresh successful factory evidence and available
Block 8 comparisons; Block 9 and AI grounding therefore produce an evidence-insufficient story that
contradicts the comparison.

Session 12 outcome: Block 7-8-9 handoff consistency fixed the final full-demo blocker and the final
readiness status is `FULL_DEMO_MVP_READY`. A follow-up audit was added at
`docs/audits/2026-06-06_block_7_8_9_handoff_consistency_fix.md` and registered in
`docs/audits/README.md`. The root cause was Block 7 reading the factory summary from legacy
`Main portfolio/` instead of the config-isolated demo output folder. After the fix, balanced,
equity-heavy, and defensive/rates-sensitive standard vertical runs all produce
`candidate_generation.generation_status: generated`, non-empty weights, `current_vs_candidate`
`comparison_status: available`, consistent material verdicts, and no AI Commentary
`pipeline_inconsistency`.

Session 00 outcome: the readiness hardening plan now exists as a tracked repository document and is
registered as active. Baseline state, existing output evidence, and the known FRED/factor runtime
risk are recorded. No runtime, optimizer, candidate generation, comparison, verdict, or factor code
was intentionally changed in Session 00.

Session 01 outcome: the product-critical offline test inventory is complete and green. The MVP path
has focused unit/contract coverage for Builder setup, Candidate Generation, Current vs Candidate,
Decision Verdict, vertical Blocks 5-9 orchestration, AI Commentary grounding, and documentation
links. No product blocker, test-expectation blocker, legacy-unrelated failure, or infrastructure
failure was observed in this baseline. The readiness plan is not yet live-demo-ready because Session
02 still must prove the vertical product loop across three portfolio fixtures.

Session 02 outcome: three source-controlled demo portfolio fixtures now exist and the vertical script
can run against an isolated config path. This is useful progress, but live acceptance is blocked:
balanced and equity-heavy complete the fast artifact chain but produce evidence-insufficient verdicts
because the selected equal-weight candidate has no fresh comparison metrics; defensive/rates-sensitive
honestly stops at a monitor-only Builder block before candidate generation. A standard-mode retry for
balanced timed out after 904 seconds, confirming that the Session 05 FRED/factor/runtime hardening is
product-critical before `FULL_DEMO_MVP_READY` can be considered.

Session 03 outcome: command architecture is clearer and safer for demos. The canonical full-demo
entrypoint is documented as `python scripts/run_blocks_5_to_9_vertical_flow.py --method equal_weight`;
`run_portfolio_review.py --candidates <id>` is now consistently labelled as an explicit backend
factory-id compatibility path. `run_portfolio_review.py --help` no longer requires UTF-8 environment
setup in default Windows PowerShell, and the dry-run still reports `product_diagnosis_only` with
`Candidates: disabled by default`.

Session 04 outcome: stale-artifact hygiene is now explicit for the vertical MVP chain. The
Blocks 5-9 vertical command stamps product-critical root artifacts with a shared `product_run.run_id`;
Block 8 refuses candidate-generation evidence that is tombstoned, not authoritative, or inactive;
AI Commentary grounding ignores a `decision_verdict.json` whose explicit run id differs from
`current_vs_candidate.json`. This does not solve Session 02's missing comparison metrics or Session
05's FRED/factor runtime blocker, but it prevents clean and repeated runs from silently treating old
vertical artifacts as current evidence when lineage metadata is present.

Session 05 outcome: FRED/factor behavior is now more predictable and demo-safe, but the environment
still lacks complete approved full-range factor cache. The existing cache policy and focused factor
tests were verified, FRED CSV fetches now request only the needed date range, full factor-matrix raw
FRED calls use a shorter factor-specific timeout/retry budget, and `scripts/warm_factor_cache.py`
provides a direct operator check/warm path. Current live evidence is a controlled blocker rather
than a silent degradation: full-range cache check fails immediately because cache coverage is
missing/too short; live warm-up still fails for several FRED series, but now in about 45 seconds
instead of about 282 seconds; direct `build_factor_matrix` fails clearly on `DFII10` in about
7 seconds instead of hanging for minutes. Session 06 may audit output quality, but `FULL_DEMO_MVP_READY`
still cannot be declared until factor/FRED cache availability and candidate comparison metrics are
acceptable for the three demo fixtures.

Session 06 outcome: output quality is audited and remains `NOT_ACCEPTED_YET` for the full demo gate.
The audit note
`docs/audits/2026-06-05_full_demo_mvp_output_quality_audit_session_06.md` records portfolio-by-
portfolio acceptance notes. Balanced and equity-heavy are honest evidence-insufficient runs: they
explain diagnosis, hypothesis, Equal Weight reference lineage, and missing evidence, but cannot
answer what improved or worsened because all Block 8 comparison dimensions are unavailable.
Defensive/rates-sensitive is understandable as a blocked monitor path, but it is not a complete
candidate comparison/verdict demo. The next useful work is Session 07 grounding/product-facing
summary hardening, not declaring readiness.

Session 07 outcome: AI Commentary grounding is stronger, but the full demo is still
`NOT_ACCEPTED_YET`. The context can now support a concise client-facing explanation through a
deterministic 5-10 sentence draft and a Light Decision Journal scaffold without calling an LLM. It
also cites `portfolio_alternatives_builder.json` when Builder is blocked, so the defensive/rates
fixture can be explained as a monitor/data-quality blocked path. This does not solve the Session 06
Block 8 metric gap: balanced and equity-heavy still honestly say improvement/worsening evidence is
unavailable until candidate comparison metrics exist.

## Context and Orientation

Portfolio MRI / Portfolio X-Ray is currently aligned around the "Diagnosis 2" product truth. The
current product is diagnosis-first, current-portfolio-first, and not optimizer-first.

The block names used in this plan are:

- Blocks 1-3: Portfolio Evidence Engine. This includes input handling, Portfolio X-Ray, and Stress
  Test Lab.
- Block 4: Diagnosis Engine. This turns evidence into the main portfolio problem.
- Block 5: Hypothesis Launchpad. This proposes testable hypothesis cards.
- Block 6: Hypothesis Builder / Builder Setup. This configures one candidate setup. It is not a
  candidate and must not write candidate weights.
- Block 7: Candidate Generator. This attempts one selected candidate. The candidate is not a
  recommendation.
- Block 8: Trade-off Comparison. This compares current portfolio versus selected candidate. It is
  not a verdict.
- Block 9: Decision Verdict. This is where action, no-action, no-trade, or evidence-insufficient is
  evaluated.
- AI Commentary: deterministic grounding for client-ready explanation. It must not invent metrics
  or unsupported conclusions.

The canonical product chain is:

    Input portfolio
    -> Portfolio X-Ray
    -> Stress Test Lab
    -> Problem Classification
    -> Candidate Launchpad
    -> Portfolio Alternatives Builder
    -> Candidate Generation
    -> Current vs Candidate Comparison
    -> Decision Verdict
    -> AI Commentary / grounding
    -> Monitoring / What Changed

The successful output chain already observed on disk is:

- `Main portfolio/analysis_subject/problem_classification.json`
- `Main portfolio/analysis_subject/candidate_launchpad.json`
- `Main portfolio/analysis_subject/portfolio_alternatives_builder.json`
- `Main portfolio/candidate_generation.json`
- `Main portfolio/current_vs_candidate.json`
- `Main portfolio/decision_verdict.json`
- `Main portfolio/ai_commentary_context.json`

Product boundaries that must be preserved:

- Diagnosis-only must not create candidate weights.
- Builder setup is not a candidate.
- Candidate is not a recommendation.
- Reference benchmarks are diagnostic comparisons, not rebalance recommendations.
- Block 8 comparison is not a verdict.
- Block 9 verdict is where action or no-action is evaluated.
- AI Commentary grounds explanation; it does not invent metrics or make unsupported claims.
- No-trade is a valid outcome.
- Evidence-insufficient is a valid outcome.

Out of scope for this readiness plan:

- full PDF report design
- macro overlay
- multi-candidate arena
- advanced optimizer cockpit
- tax-aware optimization
- turnover-aware optimizer objective
- client risk profile / suitability module
- liquidity needs module
- full custom constraints UI
- assumption sensitivity mode
- Monte Carlo
- asset-level diagnostics
- new factor models
- new strategy research blocks
- full production UI

## Plan of Work

Session 00 creates this plan and registers it. Later sessions must follow the sequence below and
update this file as work proceeds.

### Session 01 - Product-critical test inventory and smoke baseline

Objective: create a clear test map for the current product-critical flow and run a focused baseline
test suite.

Scope: identify and run tests covering Block 6 Builder setup, Block 7 Candidate Generator, Block 8
Current vs Candidate, Block 9 Decision Verdict, AI Commentary context, Blocks 5-9 vertical flow, and
docs validation.

Files likely to inspect or change: `tests/`, this ExecPlan, and only trivial import/name fixes if a
baseline test cannot run.

Commands:

    $block6 = Get-ChildItem tests -Filter 'test_block_6_*.py' | ForEach-Object FullName
    .\.venv\Scripts\python.exe -m pytest $block6 -q
    $cg = Get-ChildItem tests -Filter 'test_candidate_generation_*.py' | ForEach-Object FullName
    .\.venv\Scripts\python.exe -m pytest $cg -q
    .\.venv\Scripts\python.exe -m pytest tests\test_current_vs_candidate.py tests\test_current_vs_candidate_comparison_contract.py tests\test_current_vs_candidate_success_criteria.py tests\test_current_vs_candidate_tradeoffs.py tests\test_block8_current_vs_candidate_boundary.py -q
    .\.venv\Scripts\python.exe -m pytest tests\test_decision_verdict.py tests\test_decision_verdict_contract.py tests\test_decision_verdict_evidence_insufficient.py tests\test_decision_verdict_failed_candidate.py tests\test_decision_verdict_no_trade.py tests\test_decision_verdict_rebalance_when_material.py -q
    .\.venv\Scripts\python.exe -m pytest tests\test_blocks_5_to_9_vertical_flow.py tests\test_reference_benchmark_vertical_flow.py tests\test_ai_commentary_context.py -q
    .\.venv\Scripts\python.exe scripts\verify_docs.py

Acceptance criteria: product-critical tests are identified; baseline pass/fail status is known; any
failures are classified as product blocker, test expectation update needed, legacy unrelated, or
infrastructure/performance; no unknown test status remains for the product-critical path.

Done when: this ExecPlan contains a clear baseline test report for the MVP path.

Risks and blockers: PowerShell does not pass literal pytest wildcards the same way Unix shells do, so
use PowerShell-expanded file lists. Existing unrelated dirty tests may fail for reasons outside this
readiness plan.

What not to touch: do not refactor product code unless a baseline test cannot even run due to a
trivial naming/import error; document before modifying.

### Session 02 - Multi-portfolio live acceptance fixtures

Objective: prove the vertical product loop works on multiple portfolio types, not only the current
demo portfolio.

Scope: create or identify three live/demo portfolio fixtures using existing supported instruments and
current project taxonomy. Use existing instruments from the current root config unless inspection
shows a better supported set. Required scenarios are balanced diversified, equity-heavy/concentrated,
and defensive/bond-heavy/rates-sensitive.

Files likely to inspect or change: fixture config files under a source-controlled demo config
directory such as `config/demo_portfolios/`; CLI config plumbing if the vertical script does not yet
support isolated config paths; this ExecPlan.

Commands, after config support exists if needed:

    .\.venv\Scripts\python.exe scripts\run_blocks_5_to_9_vertical_flow.py --config config\demo_portfolios\balanced.yml --method equal_weight
    .\.venv\Scripts\python.exe scripts\run_blocks_5_to_9_vertical_flow.py --config config\demo_portfolios\equity_heavy.yml --method equal_weight
    .\.venv\Scripts\python.exe scripts\run_blocks_5_to_9_vertical_flow.py --config config\demo_portfolios\defensive_rates_sensitive.yml --method equal_weight

Required JSON outputs for each portfolio:

- `problem_classification.json`
- `candidate_launchpad.json`
- `portfolio_alternatives_builder.json`
- `candidate_generation.json`
- `current_vs_candidate.json`
- `decision_verdict.json`
- `ai_commentary_context.json`

Required human-readable result for each portfolio:

- primary diagnosis
- hypothesis tested
- candidate method
- what improved
- what worsened
- verdict
- whether this is understandable without developer explanation, with a yes/no and reason

Acceptance criteria: all three portfolios complete or produce honest blocked/evidence-insufficient
outputs with clear reasons; one candidate is generated or an honest failed/infeasible path is
recorded; no candidate zoo is created; no stale artifacts contaminate the run; verdict is valid and
explainable; AI Commentary grounding exists; each output chain is coherent enough to summarize in
plain English.

Done when: three portfolio fixtures complete the vertical product flow or produce honest
blocked/evidence-insufficient outputs, and each has the required human-readable result.

Risks and blockers: current vertical script may not support `--config`; candidate factory output
folders may be shared unless fixture output directories and config fingerprints are isolated.

What not to touch: do not add new analytics or optimizers to make a fixture pass. If a portfolio
exposes a real limitation, document it.

### Session 03 - Runtime command architecture and product entrypoints

Objective: make runtime modes understandable and aligned with the staged user journey: user enters a
portfolio, system runs diagnosis, user sees problems/hypotheses, user chooses a test, system generates
candidate, system compares and gives verdict.

Scope: audit and document diagnosis-only, full product review, explicit candidate run, vertical demo
script, legacy runners, and advanced/research paths. Define a clean command taxonomy for
diagnosis-only, generate-candidate, compare-and-verdict, and full-demo. Fix or document Windows
encoding issues that make command help unreadable.

Files likely to inspect or change: `run_portfolio_review.py`, `run_core_diagnostics.py`,
`scripts/run_blocks_5_to_9_vertical_flow.py`, `scripts/generate_candidate_from_builder_setup.py`,
`run_compare_variants.py`, `docs/runtime_entrypoints.md`, `README.md`, and
`docs/product_flow_operator_guide.md`.

Commands:

    $env:PYTHONIOENCODING='utf-8'
    .\.venv\Scripts\python.exe run_portfolio_review.py --help
    .\.venv\Scripts\python.exe run_portfolio_review.py --dry-run
    .\.venv\Scripts\python.exe scripts\run_blocks_5_to_9_vertical_flow.py --help
    .\.venv\Scripts\python.exe scripts\verify_docs.py

Acceptance criteria: runtime entrypoints are documented clearly; compatibility paths such as
`run_portfolio_review.py --candidates equal_weight` are labelled as explicit/legacy or compatibility
paths, not canonical Block 6 to Block 7 flow; diagnosis-only does not create authoritative
candidate/comparison/verdict artifacts; full-demo path is available for demo/testing.

Done when: a developer can read docs and understand exactly which command to run for diagnosis-only,
candidate generation, comparison/verdict, and demo.

Risks and blockers: old docs may still name legacy candidate generation as the recommended demo path.

What not to touch: do not delete legacy runners unless already documented as safe to remove.

### Session 04 - Stale artifact hygiene and output freshness

Objective: prevent stale JSON outputs from contaminating product runs.

Scope: audit and harden output hygiene for diagnosis-only, builder setup, candidate generation,
current vs candidate, decision verdict, and AI Commentary context.

Files likely to inspect or change: `src/product_bundle_hygiene.py`,
`scripts/run_blocks_5_to_9_vertical_flow.py`, `src/candidate_generation.py`,
`src/current_vs_candidate.py`, `src/decision_verdict.py`, `src/ai_commentary_context.py`, and
artifact-path helpers.

Required behavior: diagnosis-only runs must not leave authoritative fresh candidate/comparison/verdict
files unless they are explicitly marked as tombstone, not generated, stale, or inactive. Vertical flow
runs must create fresh artifacts with enough metadata to determine whether they belong to the same
run.

Suggested tests:

    tests/test_product_artifact_hygiene.py
    tests/test_no_stale_candidate_generation.py
    tests/test_no_stale_verdict_in_ai_context.py

Acceptance criteria: product-critical outputs include enough metadata to determine whether they belong
to the same run; no stale candidate is used for comparison; no stale verdict is used for AI
Commentary; tests cover no-stale-artifact behavior.

Done when: a clean run and a repeated run cannot accidentally use old candidate/comparison/verdict
artifacts.

Risks and blockers: historical run artifacts can be useful, so prefer active/inactive marking or
scoped output directories over broad deletion.

What not to touch: do not remove useful historical artifacts unless there is already an archive/run-id
system.

### Session 05 - FRED / factor matrix performance and reliability hardening

Objective: reduce demo fragility caused by FRED / factor matrix timeouts without weakening investment
diagnostics.

Scope: audit existing FRED / factor cache and fallback behavior. Start from the already checked-in
plan `docs/exec_plans/2026-06-05_full_factor_matrix_fred_dependency_stabilization.md` and verify
whether its implemented behavior is sufficient for this readiness gate.

Non-negotiable boundary: do not add an equity-only shortcut; do not silently degrade factor exposure;
do not fake factor data; do not bypass full factor matrix in the product diagnostic path unless
explicitly in a degraded mode with clear warnings.

Files likely to inspect or change: `src/data_fred.py`, `src/stress_factors.py`,
`src/data_loader.py`, `src/candidate_run_context.py`, factor tests, and optionally a warm-cache script
if no safe operator path exists.

Commands: run diagnosis once cold and record timing; run diagnosis again warm and record timing;
inspect factor diagnostics metadata; run focused factor/cache tests; run docs verification.

Acceptance criteria: repeated run after cache warm-up is materially faster or at least not blocked by
FRED timeout; if FRED times out, approved cache is used where valid; if no valid cache exists, the
system fails honestly or marks factor evidence unavailable; warnings are visible in product metadata;
Factor Exposure and Stress Lab remain logically intact.

Done when: FRED/factor behavior is predictable, documented, and demo-safe without sacrificing
diagnostic integrity.

Risks and blockers: live FRED and market data behavior is unstable and may require longer command
timeouts.

What not to touch: do not change factor model formulas unless required for a bug and separately
justified.

### Session 06 - Output quality audit

Objective: verify that the product outputs answer the user's real questions, not just that JSON files
exist.

Scope: for each of the three Session 02 fixtures, read the full output chain and create an audit of
diagnosis clarity, hypothesis clarity, candidate lineage, comparison clarity, verdict clarity,
no-trade/evidence-insufficient rationale, client-ready explanation readiness, confusing backend
leakage, missing evidence, overstated claims, and under-explained trade-offs.

Files likely to inspect or change: this ExecPlan and optionally an audit note under `docs/audits/` if
the evidence is too long for the plan.

Acceptance criteria: for each portfolio, a human can explain the result in 5-7 sentences; verdict is
consistent with comparison; AI Commentary grounding contains enough evidence to write a client-ready
summary; no output says or implies "best portfolio" without justification; no output presents
reference benchmark as recommendation; no output hides data quality or model limitations.

Done when: there is a written product acceptance note for each portfolio and a list of concrete
output-quality improvements if needed.

Risks and blockers: outputs may be technically correct but still too backend-oriented for a
non-developer.

What not to touch: do not rewrite the whole commentary engine yet. First audit whether the data is
enough.

### Session 07 - AI Commentary grounding

Objective: ensure AI Commentary can produce a client-ready explanation from deterministic outputs
without hallucination.

Scope: inspect `ai_commentary_context.json`, `src/ai_commentary_context.py`, existing commentary
templates if any, and grounding fields from Blocks 1-9.

Required commentary topics: portfolio diagnosis, key problems, hidden exposures, stress behavior,
suggested hypothesis, selected candidate logic if candidate exists, current vs candidate comparison,
what improved, what worsened, turnover / transaction cost impact, Decision Verdict, no-trade
rationale if applicable, evidence-insufficient rationale if applicable, next review trigger, and a
Light Decision Journal covering date, current portfolio, selected candidate, untested/rejected
alternatives, key assumptions, decision verdict, accepted trade-offs, and next review trigger.

Acceptance criteria: AI Commentary context is fully grounded in existing outputs; it does not invent
metrics; it can support a concise client-ready explanation; it preserves uncertainty and data-quality
limitations; it includes no-trade and evidence-insufficient rationale where relevant.

Optional only if low-risk: create a deterministic commentary preview generator that does not call an
LLM and uses context fields to produce a plain-language draft.

Done when: for each demo portfolio, AI Commentary context can support a clear 5-10 sentence
advisor/client explanation.

Risks and blockers: the context may contain enough evidence but lack client-facing ordering or field
names.

What not to touch: do not add live LLM generation or prompt chains unless the repo already has that
and it is explicitly in scope.

### Session 08 - Legacy path classification

Objective: stop legacy runtime paths and advanced research code from confusing the current product
MVP.

Scope: classify existing paths into current product path, explicit candidate compatibility path,
advanced research path, legacy runner, and deprecated/do-not-use.

Files likely to inspect or change: root scripts, `legacy/runners/`, candidate factory calls,
optimizer-related scripts, and docs references to old candidate zoo / health score / robustness /
macro / action plan / old selection engine.

Required outcome: do not necessarily delete code. Create clear labels and docs. If safe, add runtime
warnings for legacy explicit candidate paths that say the path uses explicit legacy candidate
generation and is not the canonical Block 6 to Block 7 product handoff.

Acceptance criteria: README and runtime docs identify canonical product path; legacy paths are not
described as current Core MVP; advanced/research paths are preserved but hidden/deferred; product path
does not accidentally use candidate zoo; full demo path uses the new canonical product loop.

Done when: a new developer or future AI agent cannot confuse legacy candidate generation with the
current product path.

Risks and blockers: root wrappers remain for compatibility and can still be discovered by search.

What not to touch: do not delete working legacy code unless explicitly safe and covered by tests.

### Session 09 - Product demo package

Objective: create a demo package that makes the product understandable without developer narration.

Scope: create or update a planned demo document, expected target path docs/demo/full_demo_mvp.md,
or equivalent with sample run instructions,
expected outputs, known limitations, a one-page explanation of the product flow, three demo portfolio
descriptions, and an interpretation guide for verdicts.

Acceptance criteria: the demo docs allow someone to run and understand the vertical MVP without asking
the original developer. The demo explains what the product does and does not do, why
evidence-insufficient can be valid, why no-trade can be valid, why candidate is not automatically a
recommendation, how to run the vertical flow, where outputs are written, and how to read the outputs.

Done when: there is a clear demo document and it matches actual runtime behavior.

Risks and blockers: marketing copy can overpromise; keep the document practical and product-facing.

What not to touch: do not design a full PDF report or marketing package.

### Session 10 - Final readiness gate

Objective: run final acceptance checks and decide whether the project can be marked
`FULL_DEMO_MVP_READY`, `DEMO_READY_WITH_LIMITATIONS`, or `NOT_READY_BLOCKED`.

Required checks:

- focused tests pass or blockers are classified
- docs validation passes
- at least three portfolio live runs complete or produce honest blocked/evidence-insufficient outputs
- required output chain exists for successful vertical flows
- each portfolio has the required human-readable summary
- output freshness / no-stale-artifact behavior is verified
- FRED/factor behavior is documented and demo-safe
- runtime commands are clear
- legacy paths are labelled
- AI Commentary grounding is client-ready enough for a demo
- no forced rebalance when evidence is insufficient
- no reference benchmark treated as recommendation
- no candidate zoo in default product path

Hard gate: `FULL_DEMO_MVP_READY` must not be declared if any of the three demo portfolios requires
oral developer explanation to understand the result.

Suggested final commands:

    $block6 = Get-ChildItem tests -Filter 'test_block_6_*.py' | ForEach-Object FullName
    .\.venv\Scripts\python.exe -m pytest $block6 -q
    $cg = Get-ChildItem tests -Filter 'test_candidate_generation_*.py' | ForEach-Object FullName
    .\.venv\Scripts\python.exe -m pytest $cg -q
    .\.venv\Scripts\python.exe -m pytest tests\test_current_vs_candidate.py tests\test_current_vs_candidate_comparison_contract.py tests\test_current_vs_candidate_success_criteria.py tests\test_current_vs_candidate_tradeoffs.py tests\test_block8_current_vs_candidate_boundary.py -q
    .\.venv\Scripts\python.exe -m pytest tests\test_decision_verdict.py tests\test_decision_verdict_contract.py tests\test_decision_verdict_evidence_insufficient.py tests\test_decision_verdict_failed_candidate.py tests\test_decision_verdict_no_trade.py tests\test_decision_verdict_rebalance_when_material.py -q
    .\.venv\Scripts\python.exe -m pytest tests\test_blocks_5_to_9_vertical_flow.py tests\test_reference_benchmark_vertical_flow.py tests\test_ai_commentary_context.py -q
    .\.venv\Scripts\python.exe scripts\verify_docs.py
    .\.venv\Scripts\python.exe scripts\run_blocks_5_to_9_vertical_flow.py --method equal_weight

Add the actual multi-portfolio commands once Session 02 fixture support exists.

Done when: the repo has a written readiness result, test evidence, demo evidence, human-readable
portfolio summaries, and a clear final status.

Risks and blockers: tests passing alone is not enough. The product story must be understandable.

What not to touch: do not broaden scope into deferred features.

## Concrete Steps

All commands assume the working directory is:

    D:\Desktop\CURSOR TULA DIAGNOSTICS

Session 00 commands actually run:

    git status --short
    Get-ChildItem -LiteralPath 'Main portfolio' -Force | Select-Object Mode,Length,LastWriteTime,Name
    Get-ChildItem -LiteralPath 'Main portfolio\analysis_subject' -Force | Select-Object Mode,Length,LastWriteTime,Name
    Get-Date -Format 'yyyy-MM-ddTHH:mm:ssK'
    .\.venv\Scripts\python.exe scripts\verify_docs.py

Session 00 observed that the working tree had many existing modified and untracked files before this
plan was added. The only intended Session 00 changes are this plan file and `docs/exec_plans/README.md`.

Session 01 commands actually run:

    Get-ChildItem tests -Filter 'test_block_6_*.py' | Sort-Object Name
    Get-ChildItem tests -Filter 'test_candidate_generation_*.py' | Sort-Object Name
    .\.venv\Scripts\python.exe -m pytest $block6 -q
    .\.venv\Scripts\python.exe -m pytest $cg -q
    .\.venv\Scripts\python.exe -m pytest tests\test_current_vs_candidate.py tests\test_current_vs_candidate_comparison_contract.py tests\test_current_vs_candidate_success_criteria.py tests\test_current_vs_candidate_tradeoffs.py tests\test_block8_current_vs_candidate_boundary.py -q
    .\.venv\Scripts\python.exe -m pytest tests\test_decision_verdict.py tests\test_decision_verdict_contract.py tests\test_decision_verdict_evidence_insufficient.py tests\test_decision_verdict_failed_candidate.py tests\test_decision_verdict_no_trade.py tests\test_decision_verdict_rebalance_when_material.py -q
    .\.venv\Scripts\python.exe -m pytest tests\test_blocks_5_to_9_vertical_flow.py tests\test_reference_benchmark_vertical_flow.py tests\test_ai_commentary_context.py -q
    .\.venv\Scripts\python.exe scripts\verify_docs.py

Session 01 actual results:

    Block 6 Builder setup tests: 45 passed in 1.65s.
    Candidate Generation tests: 18 passed in 0.60s.
    Block 8 Current vs Candidate tests: 12 passed in 3.57s.
    Block 9 Decision Verdict tests: 16 passed in 0.77s.
    Blocks 5-9 vertical flow and AI Commentary tests: 15 passed in 6.79s.
    Documentation verification: docs verification: OK.

Session 02 source/config changes:

    config/demo_portfolios/balanced.yml
    config/demo_portfolios/equity_heavy.yml
    config/demo_portfolios/defensive_rates_sensitive.yml
    run_report.py --config
    run_portfolio_review.py --config
    run_compare_variants.py --config
    scripts/run_blocks_5_to_9_vertical_flow.py --config / --factory-execution-mode
    scripts/generate_candidate_from_builder_setup.py --config / --factory-execution-mode
    src/portfolio_review_workflow.py config propagation to subprocess steps

Session 02 commands actually run:

    .\.venv\Scripts\python.exe run_portfolio_review.py --config config\demo_portfolios\balanced.yml --skip-candidates --skip-compare --dry-run
    .\.venv\Scripts\python.exe run_portfolio_review.py --config config\demo_portfolios\equity_heavy.yml --skip-candidates --skip-compare --dry-run
    .\.venv\Scripts\python.exe run_portfolio_review.py --config config\demo_portfolios\defensive_rates_sensitive.yml --skip-candidates --skip-compare --dry-run
    .\.venv\Scripts\python.exe scripts\run_blocks_5_to_9_vertical_flow.py --config config\demo_portfolios\balanced.yml --method equal_weight --force-candidate
    .\.venv\Scripts\python.exe scripts\run_blocks_5_to_9_vertical_flow.py --config config\demo_portfolios\equity_heavy.yml --method equal_weight --force-candidate
    .\.venv\Scripts\python.exe scripts\run_blocks_5_to_9_vertical_flow.py --config config\demo_portfolios\defensive_rates_sensitive.yml --method equal_weight --force-candidate
    .\.venv\Scripts\python.exe scripts\run_blocks_5_to_9_vertical_flow.py --config config\demo_portfolios\balanced.yml --method equal_weight --force-candidate --factory-execution-mode standard
    .\.venv\Scripts\python.exe -m pytest tests\test_blocks_5_to_9_vertical_flow.py tests\test_candidate_generation_from_builder_setup.py tests\test_block_6_product_runtime_wiring.py -q
    .\.venv\Scripts\python.exe scripts\verify_docs.py

Session 02 actual results:

    Config dry-runs: all three demo configs loaded and planned isolated output directories under output/demo_portfolios/.
    Balanced fast vertical run: completed in 701.9s first run; completed again in 652.4s after the standard-mode timeout cleanup. Required root JSON chain exists, but comparison status is unavailable and verdict is evidence_insufficient.
    Equity-heavy fast vertical run: completed in 682.2s. Required root JSON chain exists, but comparison status is unavailable and verdict is evidence_insufficient.
    Defensive/rates-sensitive fast vertical run: failed honestly in 582.4s with builder_setup_not_generatable:blocked_by_data_quality:data_quality_blocker. Analysis-subject diagnosis, Launchpad, and Builder JSON exist; candidate/comparison/verdict/root AI context do not.
    Balanced standard vertical retry: timed out after 904s after writing equal-weight weight-side artifacts but before completing Block 8/9. Orphaned Python processes from this timed-out run were stopped.
    Focused tests after code changes: 6 passed in 2.35s.
    Documentation verification after code changes: docs verification: OK.

Session 03 source/docs changes:

    run_portfolio_review.py help text for --with-candidates, --candidate-profile, --candidates, and --execution-mode
    docs/runtime_entrypoints.md command taxonomy and Windows console encoding note
    README.md runtime command taxonomy and annotated command examples
    docs/product_flow_operator_guide.md staged operator commands and anti-pattern correction

Session 03 commands actually run:

    Remove-Item Env:PYTHONIOENCODING -ErrorAction SilentlyContinue; .\.venv\Scripts\python.exe run_portfolio_review.py --help
    Remove-Item Env:PYTHONIOENCODING -ErrorAction SilentlyContinue; .\.venv\Scripts\python.exe scripts\run_blocks_5_to_9_vertical_flow.py --help
    $env:PYTHONIOENCODING='utf-8'; .\.venv\Scripts\python.exe run_portfolio_review.py --dry-run
    .\.venv\Scripts\python.exe scripts\verify_docs.py

Session 03 actual results:

    `run_portfolio_review.py --help`: passed in default Windows/CP1251 console after removing non-ASCII argparse glyphs.
    `scripts/run_blocks_5_to_9_vertical_flow.py --help`: passed in default Windows/CP1251 console.
    `run_portfolio_review.py --dry-run`: passed; printed `Mode: product_diagnosis_workflow`, `Runtime mode: product_diagnosis_only`, `Workflow state: diagnosis_only`, and `Candidates: disabled by default`.
    Documentation verification: docs verification: OK.

Session 04 source/docs changes:

    src/product_bundle_hygiene.py product_run metadata helpers and diagnosis-only tombstone metadata
    scripts/run_blocks_5_to_9_vertical_flow.py shared vertical product_run stamping
    src/candidate_comparison.py Block 8 stale/inactive candidate_generation guard
    src/ai_commentary_context.py product_run mismatch guard for stale verdict evidence
    tests/test_no_stale_candidate_generation.py
    tests/test_no_stale_verdict_in_ai_context.py
    OUTPUTS.md, TESTING.md, DECISIONS.md, CHANGELOG.md, current-vs-candidate / candidate-generation / AI-grounding specs

Session 04 commands actually run:

    .\.venv\Scripts\python.exe -m pytest tests\test_product_bundle_hygiene.py tests\test_no_stale_candidate_generation.py tests\test_no_stale_verdict_in_ai_context.py tests\test_blocks_5_to_9_vertical_flow.py tests\test_ai_commentary_context.py -q
    .\.venv\Scripts\python.exe scripts\verify_docs.py

Session 04 actual results:

    Focused stale-artifact, hygiene, vertical-flow, and AI-grounding tests: 24 passed in 11.90s after fixing one missing Mapping import.
    Documentation verification: docs verification: OK.

Session 05 source/docs changes:

    src/data_fred.py pushes requested start/end into the FRED CSV URL via `cosd` / `coed`.
    src/stress_factors.py uses a factor-specific bounded live FRED budget before approved-cache fallback.
    scripts/warm_factor_cache.py adds an operator smoke to validate or warm raw FRED factor cache.
    tests/test_factor_matrix_builders.py covers date-bounded CSV URLs and factor-specific FRED timeout budget.
    DATA.md, TESTING.md, DECISIONS.md, CHANGELOG.md, and this ExecPlan document the behavior.

Session 05 commands actually run:

    .\.venv\Scripts\python.exe -m pytest tests\test_factor_matrix_builders.py tests\test_data_cache_key.py tests\test_factor_diagnostics_wiring.py tests\test_product_bundle_integration.py -q
    .\.venv\Scripts\python.exe scripts\warm_factor_cache.py --help
    .\.venv\Scripts\python.exe scripts\warm_factor_cache.py --check-only --start 2007-01-01 --end 2026-06-05
    .\.venv\Scripts\python.exe scripts\warm_factor_cache.py --start 2007-01-01 --end 2026-06-05
    .\.venv\Scripts\python.exe -m pytest tests\test_factor_matrix_builders.py -q
    .\.venv\Scripts\python.exe scripts\warm_factor_cache.py --start 2007-01-01 --end 2026-06-05
    python - <<direct build_factor_matrix smoke equivalent>>

Session 05 actual results before final docs verification:

    Focused factor/cache tests before implementation: 21 passed in 24.53s.
    Focused factor/cache tests after date-bounded URL and warm-cache script: 22 passed in 19.08s.
    `warm_factor_cache.py --help`: passed.
    Cache-only full-range check: failed honestly in 0.186s because `cache/factors/` did not contain approved full-range cache for all required FRED-backed series.
    Live warm before factor-specific budget change: failed in 282.157s; every required full-range FRED-backed series timed out or lacked valid approved cache.
    Focused factor builder tests after factor-specific budget change: 13 passed in 5.33s.
    Live warm after factor-specific budget change: failed in 45.355s; `BAMLH0A0HYM2` and `WEI` loaded live, while `SP500`, `DFII10`, `T10YIE`, `BAA10Y`, `DTWEXBGS`, `VIXCLS`, and `DCOILWTICO` still timed out without valid approved full-range cache.
    Direct `build_factor_matrix('2007-01-01', '2026-06-05')`: failed clearly in 7.431s with `FactorDataUnavailableError` for `DFII10`; no equity-only shortcut was used.
    Final focused factor/cache tests: 23 passed in 16.01s.
    Documentation verification: docs verification: OK.

Session 06 source/docs changes:

    docs/audits/2026-06-05_full_demo_mvp_output_quality_audit_session_06.md
    docs/audits/README.md
    docs/exec_plans/2026-06-05_full_demo_mvp_readiness_audit_and_hardening_plan.md

Session 06 commands actually run:

    Python JSON inspection scripts over:
      output/demo_portfolios/balanced/final/
      output/demo_portfolios/equity_heavy/final/
      output/demo_portfolios/defensive_rates_sensitive/final/
    .\.venv\Scripts\python.exe scripts\verify_docs.py

Session 06 actual results:

    Output quality audit note written and registered.
    Balanced: diagnosis/hypothesis/candidate lineage/verdict are clear, but Block 8 comparison is
    unavailable and cannot explain improvement/worsening.
    Equity-heavy: same result as balanced; honest `evidence_insufficient`, not a demo-ready
    trade-off explanation.
    Defensive/rates-sensitive: diagnosis and Builder block are clear, but there is no candidate,
    comparison, or verdict artifact, so it is a blocked-case story only.
    Documentation verification: docs verification: OK.

Session 07 source/docs changes:

    src/ai_commentary_context.py
    src/product_bundle_paths.py
    src/candidate_comparison.py
    scripts/run_blocks_5_to_9_vertical_flow.py
    tests/test_ai_commentary_context.py
    docs/specs/ai_commentary_grounding_spec.md
    CHANGELOG.md
    docs/exec_plans/2026-06-05_full_demo_mvp_readiness_audit_and_hardening_plan.md

Session 07 commands actually run:

    .\.venv\Scripts\python.exe -m pytest tests\test_ai_commentary_context.py -q
    .\.venv\Scripts\python.exe -m pytest tests\test_ai_commentary_context.py tests\test_product_bundle_paths.py tests\test_blocks_5_to_9_vertical_flow.py -q
    .\.venv\Scripts\python.exe -m pytest tests\test_decision_verdict.py tests\test_current_vs_candidate.py -q
    Python in-memory context rebuild over existing demo outputs:
      output/demo_portfolios/balanced/final/
      output/demo_portfolios/equity_heavy/final/
      output/demo_portfolios/defensive_rates_sensitive/final/
    .\.venv\Scripts\python.exe scripts\verify_docs.py

Session 07 actual results before final docs verification:

    AI Commentary focused tests: 14 passed in 5.45s.
    AI Commentary + product bundle paths + vertical flow tests: 37 passed in 7.42s.
    Adjacent verdict/current-vs-candidate tests: 10 passed in 0.28s.
    In-memory context rebuild: all three demo portfolios produced 10 deterministic explanation
    sentences; balanced/equity-heavy remained post-compare with unavailable improvement/worsening
    evidence, while defensive/rates-sensitive remained diagnosis-only with blocked Builder status.
    Documentation verification: docs verification: OK.
    The context now exposes deterministic client explanation sentences and a Light Decision Journal
    scaffold. Missing comparison metrics remain explicitly unavailable rather than being invented.


Session 08 outcome: legacy and advanced runtime paths are now explicitly classified at the places
future operators are most likely to see first. `run_portfolio_review.py --candidates <id>` still
builds a one-candidate compatibility plan, but the banner and dry-run summary say it is an
explicit factory-id compatibility path. Research/batch paths say they are not the Core MVP demo
story. Root legacy runner wrappers print a warning before delegating to `legacy/runners/`. Docs
now point the canonical full-demo proof to `scripts/run_blocks_5_to_9_vertical_flow.py --method
<id>`. No legacy code was deleted.

Session 08 source/docs changes:

    src/runtime_entrypoint_labels.py
    src/portfolio_review_workflow.py
    run_candidate_factory.py
    run_compare_variants.py
    root legacy runner wrappers (`run_optimization.py`, optimizer/candidate wrappers, etc.)
    tests/test_portfolio_review_workflow.py
    tests/test_runtime_entrypoint_labels.py
    tests/test_legacy_runner_wrappers.py
    README.md
    docs/runtime_entrypoints.md
    docs/product_flow_operator_guide.md
    docs/specs/portfolio_review_workflow_spec.md
    CHANGELOG.md
    docs/exec_plans/2026-06-05_full_demo_mvp_readiness_audit_and_hardening_plan.md

Session 08 commands actually run:

    .\.venv\Scripts\python.exe -m pytest tests\test_portfolio_review_workflow.py tests\test_runtime_entrypoint_labels.py tests\test_legacy_runner_wrappers.py -q
    Remove-Item Env:PYTHONIOENCODING -ErrorAction SilentlyContinue; .\.venv\Scripts\python.exe run_portfolio_review.py --candidates equal_weight --dry-run
    Remove-Item Env:PYTHONIOENCODING -ErrorAction SilentlyContinue; .\.venv\Scripts\python.exe run_portfolio_review.py --with-candidates --dry-run
    Remove-Item Env:PYTHONIOENCODING -ErrorAction SilentlyContinue; .\.venv\Scripts\python.exe run_candidate_factory.py --help
    Remove-Item Env:PYTHONIOENCODING -ErrorAction SilentlyContinue; .\.venv\Scripts\python.exe run_compare_variants.py --help
    .\.venv\Scripts\python.exe scripts\verify_docs.py

Session 08 actual results:

    Focused path-classification tests: 35 passed in 6.09s after the final help-text patch.
    `run_portfolio_review.py --candidates equal_weight --dry-run`: passed and printed the
    explicit factory-id compatibility path classification plus the canonical vertical script.
    `run_portfolio_review.py --with-candidates --dry-run`: passed and printed the
    advanced/research path classification.
    `run_candidate_factory.py --help`: passed and points product demos to the vertical script.
    `run_compare_variants.py --help`: passed and labels default compare as advanced/backend
    support, with `--block8-only --candidate <id>` as the technical vertical boundary.
    Documentation verification: docs verification: OK.

Session 09 outcome: the repo now has a practical Core MVP demo guide that a future operator can use
without oral developer narration. The guide intentionally does not declare the product fully ready:
it explains the current successful/partial/blocked states for the three demo fixtures, how to run
the canonical vertical script, where every product-bundle artifact is written, how to interpret
`evidence_insufficient` and no-trade style outcomes, and why a generated candidate is not a
recommendation.

Session 09 source/docs changes:

    docs/demo/full_demo_mvp.md
    README.md
    CHANGELOG.md
    docs/exec_plans/2026-06-05_full_demo_mvp_readiness_audit_and_hardening_plan.md

Session 09 commands actually run:

    .\.venv\Scripts\python.exe scripts\run_blocks_5_to_9_vertical_flow.py --help
    Python JSON inspection script over:
      output/demo_portfolios/balanced/final/
      output/demo_portfolios/equity_heavy/final/
      output/demo_portfolios/defensive_rates_sensitive/final/
    .\.venv\Scripts\python.exe scripts\verify_docs.py

Session 09 actual results:

    Vertical CLI help passed and confirmed the canonical one-candidate demo command options.
    Existing generated demo outputs matched the documented current limitations: balanced and
    equity-heavy have diagnosis/Builder/candidate/verdict chains but remain evidence-insufficient
    when comparison metrics are unavailable; defensive/rates-sensitive has diagnosis and blocked
    Builder evidence but no post-candidate root artifact chain.
    Documentation verification: docs verification: OK.

Session 02 human-readable acceptance summary:

    Balanced diversified:
    - Primary diagnosis: mixed_evidence_no_action; no dominant actionable problem is confirmed.
    - Hypothesis tested: compare against a simple equal-weight reference benchmark.
    - Candidate method: equal_weight.
    - What improved: not available; Block 8 has no candidate metric values.
    - What worsened: not available; Block 8 has no candidate metric values.
    - Verdict: evidence_insufficient; review missing or degraded evidence before acting.
    - Understandable without developer explanation: no, because the chain writes JSON but does not explain improvements/worsening.

    Equity-heavy/concentrated:
    - Primary diagnosis: mixed_evidence_no_action; no dominant actionable problem is confirmed.
    - Hypothesis tested: compare against a simple equal-weight reference benchmark.
    - Candidate method: equal_weight.
    - What improved: not available; Block 8 has no candidate metric values.
    - What worsened: not available; Block 8 has no candidate metric values.
    - Verdict: evidence_insufficient; review missing or degraded evidence before acting.
    - Understandable without developer explanation: no, because the result cannot answer the trade-off question.

    Defensive/bond-heavy/rates-sensitive:
    - Primary diagnosis: weak_crisis_resilience; worst synthetic stress loss is reported as -40.0%.
    - Hypothesis tested: none as a generated portfolio; Launchpad selected keep-current-and-monitor.
    - Candidate method: none; Builder blocked candidate generation.
    - What improved: not applicable.
    - What worsened: not applicable.
    - Verdict: no Block 9 verdict was written because no candidate was generated.
    - Understandable without developer explanation: no for demo acceptance; yes only as an internal honest blocked-case.


Session 10 source/docs changes:

    docs/audits/2026-06-06_full_demo_mvp_readiness_gate_session_10.md
    docs/audits/README.md
    CHANGELOG.md
    docs/exec_plans/2026-06-05_full_demo_mvp_readiness_audit_and_hardening_plan.md

Session 10 commands actually run:

    $block6 = Get-ChildItem tests -Filter 'test_block_6_*.py' | ForEach-Object FullName
    .\.venv\Scripts\python.exe -m pytest $block6 -q
    $cg = Get-ChildItem tests -Filter 'test_candidate_generation_*.py' | ForEach-Object FullName
    .\.venv\Scripts\python.exe -m pytest $cg -q
    .\.venv\Scripts\python.exe -m pytest tests\test_current_vs_candidate.py tests\test_current_vs_candidate_comparison_contract.py tests\test_current_vs_candidate_success_criteria.py tests\test_current_vs_candidate_tradeoffs.py tests\test_block8_current_vs_candidate_boundary.py -q
    .\.venv\Scripts\python.exe -m pytest tests\test_decision_verdict.py tests\test_decision_verdict_contract.py tests\test_decision_verdict_evidence_insufficient.py tests\test_decision_verdict_failed_candidate.py tests\test_decision_verdict_no_trade.py tests\test_decision_verdict_rebalance_when_material.py -q
    .\.venv\Scripts\python.exe -m pytest tests\test_blocks_5_to_9_vertical_flow.py tests\test_reference_benchmark_vertical_flow.py tests\test_ai_commentary_context.py -q
    .\.venv\Scripts\python.exe -m pytest tests\test_no_stale_candidate_generation.py tests\test_no_stale_verdict_in_ai_context.py tests\test_product_bundle_paths.py tests\test_runtime_entrypoint_labels.py tests\test_legacy_runner_wrappers.py tests\test_portfolio_review_workflow.py -q
    .\.venv\Scripts\python.exe scripts\warm_factor_cache.py --check-only --start 2007-01-01 --end 2026-06-05
    Python JSON inspection script over output/demo_portfolios/balanced/final/, output/demo_portfolios/equity_heavy/final/, and output/demo_portfolios/defensive_rates_sensitive/final/
    .\.venv\Scripts\python.exe scripts\verify_docs.py

Session 10 actual results before final docs verification:

    Block 6 Builder setup tests: 45 passed in 4.46s.
    Candidate Generation tests: 18 passed in 0.46s.
    Block 8 Current vs Candidate tests: 12 passed in 2.97s.
    Block 9 Decision Verdict tests: 16 passed in 0.76s.
    Blocks 5-9 vertical flow and AI Commentary tests: 16 passed in 7.96s.
    Stale-artifact / runtime-label / workflow checks: 61 passed in 11.39s.
    Factor cache check-only gate: failed honestly with EXIT_CODE=1 in about 3.247s due missing or insufficient full-range FRED-backed factor cache.
    Existing demo output inspection: balanced and equity-heavy have required root chains but remain evidence-insufficient with no improvement/worsening evidence; defensive/rates-sensitive has diagnosis/Launchpad/Builder evidence and correctly stops before candidate generation with `data_quality_blocker`.
    Final status recorded: `DEMO_READY_WITH_LIMITATIONS`.
    Documentation verification: docs verification: OK.

## Validation and Acceptance

Session 00 validation is documentation validation only:

    .\.venv\Scripts\python.exe scripts\verify_docs.py

Expected result:

    docs verification: OK

Session 01 validation is the focused product-critical offline baseline. Expected and actual result:
all listed pytest groups pass and docs verification reports `docs verification: OK`. This proves the
offline test inventory for the MVP path is known and green. It does not prove live data reliability,
multi-portfolio demo behavior, stale-artifact hygiene, FRED/factor runtime stability, or final
human-understandability; those remain assigned to later sessions.

Session 02 validation added three config-isolated live fixtures and ran the vertical CLI against them.
Expected result was a coherent three-portfolio live acceptance set. Actual result is
`NOT_ACCEPTED_YET`: two fixtures complete fast-mode JSON chains but cannot answer improvements /
worsening because candidate metrics are unavailable, and one fixture blocks before candidate
generation. This is a valid blocker discovery, not demo readiness.

Session 06 validation is documentation/audit validation. The existing generated output chain was
read, a written audit note was created, and `scripts/verify_docs.py` passed. Actual result remains
`NOT_ACCEPTED_YET` for human-understandability because two fixtures lack grounded improvement /
worsening evidence and one fixture is Builder-blocked before candidate comparison.

Full-plan acceptance requires all Session 10 checks and the hard human-understandability gate. Do not
declare `FULL_DEMO_MVP_READY` just because tests pass. Declare it only if the user can see what the
portfolio problem is, what was tested, what candidate was generated, what improved, what worsened,
whether action is justified, and what to monitor next.


Session 10 final validation completed the full-plan readiness gate. Actual result is
`DEMO_READY_WITH_LIMITATIONS`. The repository must not be labelled `FULL_DEMO_MVP_READY` yet because
the hard human-understandability gate is not fully met for all three demo portfolios: two flows still
lack grounded improvement/worsening evidence, and one flow is a correct Builder-blocked case rather
than a complete candidate comparison. The detailed written result is
[docs/audits/2026-06-06_full_demo_mvp_readiness_gate_session_10.md](../audits/2026-06-06_full_demo_mvp_readiness_gate_session_10.md).

## Idempotence and Recovery

Session 00 is safe to rerun. If the plan file already exists, update its living sections rather than
creating a duplicate. If `docs/exec_plans/README.md` already points to this plan, do not add a second
active pointer.

For later sessions, avoid destructive cleanup of generated output directories unless the session
explicitly targets output hygiene and preserves useful history through tombstones, inactive markers,
or scoped run directories.

If live data commands fail because FRED, Yahoo Finance, IBKR fallback, or another source is
unavailable, record the failure as an infrastructure/performance blocker unless the product code
silently hides the limitation. Do not fake successful factor data.

## Artifacts and Notes

Session 00 baseline key output files:

    Main portfolio/analysis_subject/problem_classification.json
    Main portfolio/analysis_subject/candidate_launchpad.json
    Main portfolio/analysis_subject/portfolio_alternatives_builder.json
    Main portfolio/candidate_generation.json
    Main portfolio/current_vs_candidate.json
    Main portfolio/decision_verdict.json
    Main portfolio/ai_commentary_context.json

Session 00 baseline known runtime issue:

    Diagnosis-only can take around nine minutes because of FRED / factor timeout warnings.
    A prior first vertical run hit a five-minute tool timeout, and a later longer-budget run completed.
    This is not acceptable for polished demo readiness until controlled, cached, documented, or
    honestly surfaced.

Session 01 baseline test inventory:

    Block 6 Builder setup:
    - tests/test_block_6_builder_prefill_contract.py
    - tests/test_block_6_builder_validation.py
    - tests/test_block_6_candidate_setup_contract.py
    - tests/test_block_6_launchpad_to_builder_prefill.py
    - tests/test_block_6_mvp_methods_modes_presets.py
    - tests/test_block_6_parameter_builder_simple_mode.py
    - tests/test_block_6_product_runtime_wiring.py
    - tests/test_block_6_strategy_selector.py

    Block 7 Candidate Generation:
    - tests/test_candidate_generation_failed_infeasible.py
    - tests/test_candidate_generation_from_builder_setup.py
    - tests/test_candidate_generation_method_mapping.py
    - tests/test_candidate_generation_no_recommendation_boundary.py

    Block 8 Current vs Candidate:
    - tests/test_current_vs_candidate.py
    - tests/test_current_vs_candidate_comparison_contract.py
    - tests/test_current_vs_candidate_success_criteria.py
    - tests/test_current_vs_candidate_tradeoffs.py
    - tests/test_block8_current_vs_candidate_boundary.py

    Block 9 Decision Verdict:
    - tests/test_decision_verdict.py
    - tests/test_decision_verdict_contract.py
    - tests/test_decision_verdict_evidence_insufficient.py
    - tests/test_decision_verdict_failed_candidate.py
    - tests/test_decision_verdict_no_trade.py
    - tests/test_decision_verdict_rebalance_when_material.py

    Vertical flow and AI Commentary:
    - tests/test_blocks_5_to_9_vertical_flow.py
    - tests/test_reference_benchmark_vertical_flow.py
    - tests/test_ai_commentary_context.py

Session 01 baseline classification:

    Product blocker: none observed.
    Test expectation update needed: none observed.
    Legacy unrelated failure: none observed.
    Infrastructure/performance blocker: none observed in the offline baseline.
    Unknown product-critical test status: none for the files listed above.

Session 02 demo fixtures:

    config/demo_portfolios/balanced.yml
    config/demo_portfolios/equity_heavy.yml
    config/demo_portfolios/defensive_rates_sensitive.yml

Session 02 output locations:

    output/demo_portfolios/balanced/final/
    output/demo_portfolios/equity_heavy/final/
    output/demo_portfolios/defensive_rates_sensitive/final/

Session 02 blocker classification:

    Product blocker: candidate comparison metrics are unavailable in fast one-candidate vertical runs,
    so the result cannot explain what improved or worsened.
    Infrastructure/performance blocker: standard one-candidate mode, which should create fresh
    comparison snapshots, timed out after 904 seconds on the balanced fixture.
    Honest blocked product path: defensive/rates-sensitive selected monitor-only and Builder blocked
    candidate generation with data_quality_blocker.
    Test expectation update needed: none observed in the focused tests run after code changes.
    Legacy unrelated failure: none observed.

## Interfaces and Dependencies

The primary runtime commands in scope are:

- `python run_core_diagnostics.py` for Blocks 1-3 only.
- `python run_portfolio_review.py` for current portfolio diagnosis / product-bundle generation.
- `python scripts/run_blocks_5_to_9_vertical_flow.py --method equal_weight` for the current vertical
  demo path.
- `python scripts/generate_candidate_from_builder_setup.py` for Block 7 one-attempt candidate
  generation from Builder setup.
- `python run_compare_variants.py --block8-only --candidate ID` for the Block 8 comparison boundary.

The current product artifacts in scope are:

- `problem_classification.json`
- `candidate_launchpad.json`
- `portfolio_alternatives_builder.json`
- `candidate_generation.json`
- `current_vs_candidate.json`
- `decision_verdict.json`
- `ai_commentary_context.json`

The plan may add safe `--config` plumbing for demo fixtures if Session 02 discovers it is missing.
That plumbing must preserve existing default behavior when no `--config` is provided.

Revision note, 2026-06-05: Initial Session 00 version created from the user-approved readiness plan.
It adds the required three-portfolio human-readable summary gate and the rule that
`FULL_DEMO_MVP_READY` cannot be declared if any demo portfolio needs oral developer explanation.

Revision note, 2026-06-05 Session 01: Added the product-critical offline test inventory and baseline
results. The session is complete and green, but it intentionally does not advance into Session 02.

Revision note, 2026-06-05 Session 03: Added command taxonomy evidence, Windows help hardening,
and the decision that the vertical Blocks 5-9 script is the canonical full-demo command while
`run_portfolio_review.py --candidates <id>` is an explicit factory-id compatibility path.

Revision note, 2026-06-05 Session 04: Added product-run freshness metadata and stale-artifact
guards for the vertical MVP chain. Block 8 now refuses inactive/not-authoritative candidate-generation
evidence, and AI Commentary grounding ignores explicitly mismatched verdict lineage.

Revision note, 2026-06-05 Session 07: Added deterministic AI Commentary client explanation and
Light Decision Journal grounding, including Builder-blocked evidence. This improves explanation
readiness but does not remove the remaining Block 8 comparison-metric blocker.

Revision note, 2026-06-05 Session 08: Added legacy/compatibility/research path classification
to runtime banners, dry-run summaries, root legacy wrapper warnings, and operator docs.


Revision note, 2026-06-06 Session 10: Completed the final readiness gate and recorded status
`DEMO_READY_WITH_LIMITATIONS`. Focused tests and docs validation passed, but full demo readiness
remains blocked by unavailable grounded comparison trade-offs and by full-range FRED/factor cache
readiness for fresh live runs.

Revision note, 2026-06-06 Session 11: Re-ran the three demo fixtures after the FRED/factor cache fix.
The FRED gate is now demo-safe and standard-mode Block 8 comparisons contain meaningful
improvements/worsening, but readiness remains `DEMO_READY_WITH_LIMITATIONS` because Block 7 records
failed candidate generation and Block 9/AI grounding contradict the available comparison evidence.

Revision note, 2026-06-06 Session 12: Fixed the Block 7 factory-output ingestion path and added
Block 7/8/9/AI consistency guards. The three standard demo fixtures now have generated candidates
with weights, available comparisons, consistent verdicts, no AI contradiction, and demo-safe factor
cache evidence. Final readiness status is `FULL_DEMO_MVP_READY`.
