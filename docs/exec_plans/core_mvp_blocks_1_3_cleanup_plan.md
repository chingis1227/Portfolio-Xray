# Core MVP Blocks 1-3 Cleanup Remediation Plan

## 1. Executive Summary

This plan cleans up legacy/client/mandate/pass-fail leaks around Core MVP Blocks 1-3 while preserving the already-clean product-facing contracts.

The cleanup matters because Core MVP Blocks 1-3 are portfolio-first diagnostics: they should analyze the current portfolio, not behave like a client mandate checker, suitability engine, optimizer, or recommendation system.

Must stay untouched:

- Real cash behavior: `Cash USD` / `CASH` remains real cash with 0% return, 0% volatility, no drawdown, no price download, and no `cash_proxy_ticker` substitution.
- Product-facing Block 2 keys: `block_2_1_asset_allocation` through `block_2_6_portfolio_weakness_map`.
- Product-facing Block 3 keys: `stress_results_v1`, `hedge_gap_analysis_v1`, `current_portfolio_stress_scorecard_v1`.
- Legacy mandate mode may remain only if isolated and gated away from portfolio-first diagnostic runs.
- Stale generated artifacts must not be edited or treated as source truth; they may only be used as evidence during live output verification.

Out of scope:

- Rewriting optimizer behavior.
- Removing advanced/generated artifacts such as Portfolio Health Score, Robustness Scorecard, Selection Engine, Action Plan, or Decision Journal.
- Editing stale generated artifacts just to make them look current.
- Changing formulas, stress scenarios, taxonomies, or real-cash methodology.
- Creating new Core MVP product blocks.

## 2. Remediation Principles

- Core MVP Blocks 1-3 are portfolio-first diagnostics.
- No client mandate, suitability, target return/vol/drawdown, liquidity, horizon, or pass/fail mandate logic should appear in product-facing Core MVP outputs.
- Legacy/advanced logic may remain only if clearly namespaced, gated, and not consumed by Core MVP UI/API.
- Real cash behavior must remain unchanged.
- Product-facing blocks 2.1-2.6 and Block 3 product keys must not be broken.
- No optimizer-first behavior should be reintroduced.
- Stale generated files are not source truth. Fix code, docs, comments, and tests; verify live regenerated outputs instead of hand-editing generated artifacts.

## 3. Session Plan

### Progress

- Session 1: completed in this thread. Added a clean Core MVP input contract while retaining legacy
  mandate/client/liquidity fields as legacy/advanced disclosure only.
- Session 2: completed. Marked X-Ray `legacy_summary` as non-product compatibility, removed the
  live `mandate_gate` verdict field, and corrected the Core MVP Block 2 comment to Blocks 2.1-2.6.
- Session 3: completed. Diagnostic-mode raw stress `scenario_results` and `historical_results` no
  longer emit mandate `pass`/`loss_ok`/`diagnostic_code(s)` fields; mandate mode remains gated.
- Session 4: completed. Added consolidated Core MVP boundary regression tests covering minimal
  input + real cash, Block 2 product surface, Block 3 diagnostic raw/product outputs, and gated
  legacy mandate stress mode.
- Session 5: completed. Aligned docs and source comments with the cleaned Core MVP boundaries:
  minimal Block 1 contract, Block 2 product blocks 2.1-2.6, diagnostic-mode Stress Lab raw-field
  behavior, and Scenario Library `scenario_library_meta` + sidecar `scenario_library.json` pattern.
  Generated artifacts were not hand-edited.
- Session 6: completed. Live portfolio-first run passed, fresh `analysis_subject` outputs were
  inspected, acceptance probe returned `LIVE_ACCEPTANCE_OK`, targeted Core MVP Blocks 1-3 suite
  passed (156 passed), docs verification passed, and the acceptance audit was written:
  [2026-05-27_core_mvp_blocks_1_3_cleanup_acceptance_audit.md](../audits/2026-05-27_core_mvp_blocks_1_3_cleanup_acceptance_audit.md).
  Full repository pytest was run and completed with 9 failures outside this cleanup acceptance
  surface; see the audit for the exact list.

### Session 1 - Protect Core MVP input surface

Objective: Separate the Core MVP input surface from legacy/advanced mandate assumptions.

Files likely touched:

- `src/analysis_setup.py`
- `src/input_assumptions.py`
- related input-layer tests

Exact tasks:

- Preserve existing runtime compatibility fields where needed, but clearly mark `resolved_mandate`, `client_profile`, target return/vol/drawdown, liquidity, portfolio value, and horizon as legacy/advanced.
- Ensure Core MVP-facing input surface exposes only tickers/instruments, weights/current_weights, and investor_currency.
- Ensure `input_surface` / `field_tiers` are the preferred Core MVP consumer surface.
- Avoid changing real cash handling or weight resolution.

Tests to add/update:

- Minimal config with `investor_currency`, `tickers`, `current_weights` resolves to `analysis_mode=analyze_current_weights`.
- Core MVP input surface does not require client profile, target return/vol/drawdown, liquidity, monthly expenses, portfolio value, or horizon.
- Real cash fixture still resolves correctly.

Commands to run:

```bash
python -m pytest tests/test_mvp_input_defaults.py tests/test_input_layer_mvp_regression.py tests/test_real_cash.py
```

Acceptance criteria:

- Core MVP input remains minimal.
- Legacy mandate/client fields are not presented as Core MVP required fields.
- Real cash tests pass unchanged.

Rollback / safety notes:

- If downstream code depends on `resolved_mandate`, do not remove it; namespace/disclose it as legacy/advanced instead.

Must NOT change:

- Real cash detection/injection.
- Weight normalization semantics.
- Optimizer profile behavior.
- Generated artifacts.

### Session 2 - Isolate legacy X-Ray summary contamination

Objective: Prevent Core MVP consumers from treating `legacy_summary` or `mandate_gate` as product-facing Block 2 output.

Files likely touched:

- `src/portfolio_xray.py`
- `src/product_bundle_paths.py` if consumer guidance needs tightening
- Block 2 tests

Exact tasks:

- Remove, rename, or clearly namespace mandate/pass-fail wording in `legacy_summary` so it cannot be confused with Core MVP product verdict.
- Ensure product consumers are directed to `block_2_1_asset_allocation` through `block_2_6_portfolio_weakness_map`.
- Update stale comments that mention Blocks 2.1-2.5 to Blocks 2.1-2.6.
- Preserve legacy sections for compatibility, but mark them non-product-facing.

Commands to run:

```bash
python -m pytest tests/test_block_2_1_pipeline_integration.py tests/test_block_2_2_pipeline_integration.py tests/test_block_2_3_factor_exposure.py tests/test_block_2_4_hidden_exposure.py tests/test_block_2_5_pipeline_integration.py tests/test_block_2_6_portfolio_weakness_map.py
```

Acceptance criteria:

- Blocks 2.1-2.6 remain present and unchanged in intent.
- Core MVP product consumers can ignore legacy sections safely.
- No mandate/pass-fail language appears in product-facing Block 2 contracts.

Must NOT change:

- Block 2.1-2.6 schemas except for contamination cleanup.
- Legacy section shape unless tests and docs are updated deliberately.
- Stale generated `portfolio_xray.json` files by hand.

### Session 3 - Clean diagnostic-mode stress raw fields

Objective: Stop diagnostic-mode stress evidence from leaking active pass/fail/DIAG mandate fields.

Files likely touched:

- `src/stress.py`
- `src/stress_results_block.py` only if tests reveal dependency
- Block 3 tests

Exact tasks:

- In `loss_gate_mode="diagnostic"`, remove or suppress `pass`, `loss_ok`, `diagnostic_codes`, and `diagnostic_code` from raw `scenario_results` / `historical_results`, or namespace them as legacy-null evidence if removal breaks compatibility.
- Keep `loss_gate_mode="mandate"` behavior intact and explicitly gated.
- Confirm `max_dd_limit` remains `None` in Core MVP diagnostic runs.
- Do not alter scenario PnL, historical drawdown, factor attribution, hedge gap, or scorecard calculations.

Commands to run:

```bash
python -m pytest tests/test_stress_results_block_contract.py tests/test_hedge_gap_analysis_v1_contract.py tests/test_current_portfolio_stress_scorecard_v1_contract.py tests/test_stress_mandate_pass.py
```

Acceptance criteria:

- Portfolio-first diagnostic stress does not look like a pass/fail mandate engine.
- Legacy mandate mode remains isolated.
- Block 3 product outputs remain schema-compatible.

Must NOT change:

- Scenario library IDs.
- Stress scenario formulas.
- Hedge gap contribution math.
- Current Portfolio Stress Scorecard product schema except contamination removal if needed.
- Generated `stress_report.json` files by hand.

### Session 4 - Add regression tests for Core MVP boundaries

Objective: Add explicit boundary tests proving Blocks 1-3 stay clean.

Exact tasks:

- Add a consolidated Core MVP contamination regression test using minimal current-portfolio config.
- Assert product-facing Block 1 surface excludes client/mandate/suitability requirements.
- Assert Block 2 product keys exclude mandate/pass/fail/suitability/rebalance/candidate language.
- Assert Block 3 product keys exclude `DIAG_*`, `pass`, `loss_ok`, `max_dd_limit`, `client_profile`, and suitability.
- Include real cash fixture coverage.

Acceptance criteria:

- Tests fail if client/mandate/pass-fail fields reappear in Core MVP product outputs.
- Tests prove real cash still works.
- Tests prove legacy mode is gated away from portfolio-first runs.

Must NOT change:

- Production behavior except to fix boundary failures exposed by tests.
- Stale generated artifacts.

### Session 5 - Documentation and comment alignment

Objective: Align docs and code comments with actual Core MVP architecture.

Exact tasks:

- Document that Block 1 Core MVP input is minimal and legacy mandate fields are advanced/legacy only.
- Clarify `portfolio_xray.json` product surface is Blocks 2.1-2.6, not `legacy_summary`.
- Clarify Block 3 lives in `stress_report.json`.
- Clarify Scenario Library pattern: `scenario_library_meta` plus sidecar `scenario_library.json`, not top-level `scenario_library_v1`.
- Update stale comments/docs that say Blocks 2.1-2.5.
- Record cleanup decisions and any compatibility compromises.
- Do not edit stale generated artifacts as documentation substitutes.

Acceptance criteria:

- Docs no longer imply client mandate fields are part of Core MVP input.
- Docs match chosen diagnostic-mode raw-field behavior.
- Scenario Library placement is unambiguous.
- No stale 2.1-2.5 comments remain where 2.1-2.6 is intended.

Must NOT change:

- Product scope beyond audit findings.
- Archived docs except if explicitly marked as traceability-only.
- Generated output files.

### Session 6 - Final live run and acceptance audit

Objective: Prove the cleanup works in the live/demo portfolio-first path and close the plan.

Exact tasks:

- Run portfolio-first diagnostic path.
- Inspect freshly produced live outputs under the current portfolio-first output location.
- Confirm `analysis_subject/portfolio_xray.json` has Block 2 product keys 2.1-2.6.
- Confirm `analysis_subject/stress_report.json` has Block 3 product keys.
- Confirm Core MVP product outputs do not expose active client mandate/pass-fail/suitability/DIAG logic.
- Confirm real cash fixture or live cash test still passes.
- Mark plan completed with outcomes and any remaining legacy/advanced exceptions.
- If stale generated artifacts still exist elsewhere, mention them as stale generated outputs only; do not edit them as source truth.

Commands to run:

```bash
python run_portfolio_review.py --skip-candidates
python -m pytest
```

Acceptance criteria:

- Live portfolio-first run completes.
- Fresh `analysis_subject/portfolio_xray.json` has clean Blocks 2.1-2.6.
- Fresh `analysis_subject/stress_report.json` has clean `stress_results_v1`, `hedge_gap_analysis_v1`, and `current_portfolio_stress_scorecard_v1`.
- No real cash regression.
- No optimizer-first behavior reintroduced.
- Acceptance audit is written.

Must NOT change:

- Candidate factory, optimizer, or decision package behavior except incidental compatibility documentation.
- Generated artifacts manually.

## 4. Test Strategy

Tests should prove:

- Minimal input remains minimal: `investor_currency`, tickers/instruments, and weights/current_weights are enough for Core MVP.
- Real cash still works: no price series required, 0% return, 0% volatility behavior preserved, no `cash_proxy_ticker` substitution.
- Block 2.1-2.6 still output expected product keys in `portfolio_xray.json`.
- Block 2 product blocks do not depend on client mandate, suitability, target return/vol/drawdown, liquidity, horizon, optimizer, candidate generation, or rebalance recommendation logic.
- Block 3 product outputs do not expose pass/fail mandate logic.
- Diagnostic mode does not leak active `DIAG_*`, `pass`, or `loss_ok` fields into Core MVP product outputs.
- Legacy mandate mode, if kept, remains gated and does not affect portfolio-first diagnostic runs.
- Generated outputs are verified only through fresh live runs, not hand-edited as source truth.

## 5. Acceptance Checklist

- [x] Block 1 Core MVP input surface is clean and minimal.
- [x] Block 1 legacy/client/mandate fields are isolated or clearly advanced/legacy.
- [x] Real cash behavior unchanged.
- [x] Block 2.1-2.6 product keys still exist.
- [x] Block 2 product outputs are diagnostic-only.
- [x] `legacy_summary` / `mandate_gate` cannot be mistaken for Core MVP product output.
- [x] Block 3 product keys still exist in `stress_report.json`.
- [x] Diagnostic-mode stress does not expose active pass/fail mandate or `DIAG_*` product logic.
- [x] Legacy mandate mode remains isolated and gated.
- [x] Scenario Library docs match `scenario_library_meta` + sidecar `scenario_library.json`.
- [x] Stale 2.1-2.5 comments/docs corrected to 2.1-2.6.
- [x] Targeted tests pass.
- [x] Live portfolio-first run passes.
- [x] No stale generated artifact was hand-edited or used as source truth.
- [x] No product JSON key regression.
- [x] No optimizer-first behavior reintroduced.

Note: full repository `python -m pytest` was executed during Session 6 and is not globally green in the current repo state (`9 failed, 1171 passed, 2 skipped`). Those failures are listed in the acceptance audit and are outside the Core MVP Blocks 1-3 cleanup acceptance surface.

## 6. Implementation Protocol

When implementation begins, execute this plan session by session. If the user says 'start the plan' or 'begin the plan', perform only Session 1 unless explicitly instructed otherwise. After each session, stop, summarize changes, report tests, and wait for the next instruction. Do not jump to the next session automatically.

## Planned sessions summary

1. Protect Core MVP input surface.
2. Isolate legacy X-Ray summary contamination.
3. Clean diagnostic-mode stress raw fields.
4. Add Core MVP boundary regression tests.
5. Align documentation and comments; do not edit generated artifacts as source truth.
6. Run final live output verification and close the cleanup plan.
