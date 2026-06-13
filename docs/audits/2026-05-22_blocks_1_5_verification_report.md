# Blocks 1-5 Verification Report

Scope: only Blocks 1-5.

Excluded: Selection, Action Plan, Decision Package, Monitoring, Journal, UI, and later blocks.

Evidence basis: generated artifacts for the current 8-ticker portfolio only. No source-code behavior was treated as proof unless it produced an artifact listed below.

Checked artifacts:

- `Main portfolio/analysis_subject/run_metadata.json`
- `Main portfolio/analysis_subject/portfolio_xray.json`
- `Main portfolio/analysis_subject/stress_report.json`
- `Main portfolio/candidate_factory_run.json`
- `Main portfolio/candidate_comparison.json` for candidate readiness evidence only

Current portfolio evidenced in `run_metadata.json`:

- Tickers: `SPY`, `QQQ`, `GLD`, `SLV`, `BND`, `SCHD`, `SCHP`, `TLT`
- Weights: `SPY=0.10`, `QQQ=0.13`, `GLD=0.09`, `SLV=0.09`, `BND=0.16`, `SCHD=0.17`, `SCHP=0.13`, `TLT=0.13`
- Analysis end: `2026-04-30`

## 1. Can the system accept tickers and explicit weights...

- Status: YES
- Evidence: `Main portfolio/analysis_subject/run_metadata.json` -> `active_assumptions.analysis_subject.tickers`; `active_assumptions.analysis_subject.weights`; `analysis_setup.analysis_subject.weight_source="config.analysis_subject.weights"`.
- Problem if any: `input_assumptions.portfolio_input.current_weights_provided=false` can be confusing because the explicit weights are accepted through `analysis_subject.weights`, not the legacy `current_weights` field.
- Fix needed if any: Clarify the exported wording so legacy `current_weights` absence is not mistaken for missing `analysis_subject.weights`.

## 2. Does it validate weights correctly...

- Status: YES
- Evidence: `Main portfolio/analysis_subject/run_metadata.json` -> `analysis_setup.analysis_subject.weight_status.status="fully_invested"`; `weight_sum=1.0`; `cash_remainder=0.0`; `validation_result.status="valid"`; top-level `portfolio_valid=true`.
- Problem if any: The current generated artifacts prove the valid-weight path for this portfolio. They do not prove invalid-weight rejection cases.
- Fix needed if any: None for the current portfolio. Add a generated invalid-weight validation fixture only if broader validation proof is required.

## 3. Does it create a valid analysis_subject...

- Status: YES
- Evidence: `Main portfolio/analysis_subject/run_metadata.json` -> `analysis_setup.analysis_subject.id="analysis_subject"`; `type="current_portfolio"`; `resolution_status="resolved"`; `ticker_count=8`; `blocking_errors=[]`; `warnings=[]`.
- Problem if any: None for the current portfolio.
- Fix needed if any: None.

## 4. Does it resolve assumptions: currency, benchmark, risk profile, cash, risk-free rate, analysis_end...

- Status: YES
- Evidence: `Main portfolio/analysis_subject/run_metadata.json` -> `input_assumptions.currency_and_market.investor_currency="USD"`; `base_benchmark_ticker="SPY"`; `cash_proxy_ticker="BIL"`; `risk_free_source="FRED:DTB3"`; `mandate_and_constraints.client_profile="Balanced"`; `analysis_setup.analysis_portfolio.cash_handling.cash_proxy_weight=0.0`; `analysis_setup.resolved_assumptions.analysis_end="2026-04-30"`.
- Problem if any: `active_assumptions.rf_source=null` and `active_assumptions.cash_proxy_ticker=null` show raw config inputs, while resolved reporting fields show the applied defaults. This is acceptable but can confuse readers if both are shown together.
- Fix needed if any: Add a clearer "raw input vs resolved default" label in reporting if this is surfaced to users.

## 5. Does it calculate portfolio metrics: CAGR, volatility, Sharpe, Sortino, Max Drawdown, beta, VaR/ES if available...

- Status: YES
- Evidence: `Main portfolio/analysis_subject/portfolio_xray.json` -> `sections.risk_diagnostics.items[type="portfolio_metrics"]` has `cagr=0.099`, `vol_annual=0.096`, `sharpe=0.799`, `sortino=1.286`, `beta_portfolio=0.513`, `max_drawdown=-0.198`; `sections.risk_diagnostics.items[type="tail_risk"]` has `metric_available=true`, `var_95=-0.009`, `var_99=-0.016`, `es_95=-0.014`, `es_99=-0.025`.
- Problem if any: None for the current portfolio.
- Fix needed if any: None.

## 6. Does it show allocation breakdown...

- Status: YES
- Evidence: `Main portfolio/analysis_subject/portfolio_xray.json` -> `sections.asset_allocation.status="available"`; `items[type="holding"]` for all 8 tickers; `items[type="breakdown"]` for `asset_class`, `region`, `currency_exposure`, `sector`, `risk_role`, `main_risk_factor`, and `risk_bucket`.
- Problem if any: None for the current portfolio.
- Fix needed if any: None.

## 7. Does it show risk contribution...

- Status: YES
- Evidence: `Main portfolio/analysis_subject/portfolio_xray.json` -> `sections.risk_budget_view.status="available"`; `sections.risk_budget_view.items[type="asset_risk_budget"]` for all 8 tickers; `legacy_summary.risk_contribution_summary.top_rc_contributors` lists `SCHD=0.195`, `QQQ=0.193`, `SLV=0.185`.
- Problem if any: Risk contribution is diagnostic-only; the artifact says `RC_vol` does not act as an optimizer gate or recommendation rule.
- Fix needed if any: None for Blocks 1-5. Keep the diagnostic-only label visible.

## 8. Does it show factor exposure...

- Status: PARTIAL
- Evidence: `Main portfolio/analysis_subject/portfolio_xray.json` -> `sections.factor_exposure.status="partial"`; `items[0].beta_key="beta_eq"` with `beta_5y=0.4794` and `beta_10y=0.4633`. `Main portfolio/analysis_subject/stress_report.json` -> `factor_diagnostics_meta.factor_beta_keys=["beta_eq"]`.
- Problem if any: Only equity beta is exposed. The factor section is explicitly partial and `stress_report.factor_regression_5y` is empty.
- Fix needed if any: Emit the missing factor regression inference panels and broader factor exposures, or keep labeling the section as partial when only `beta_eq` is available.

## 9. Does it clearly explain if factor exposure is partial or missing...

- Status: YES
- Evidence: `Main portfolio/analysis_subject/portfolio_xray.json` -> `sections.factor_exposure.status="partial"`; `sections.factor_exposure.warnings=["factor regression inference panels missing from stress_report"]`; `data_trust_signals.user_summary_lines` includes `factor regression inference panels missing from stress_report`.
- Problem if any: The explanation exists, but it is terse. It says what is missing, not what factor set was expected.
- Fix needed if any: Add a short expected-vs-available factor list for user-facing reports.

## 10. Does it run historical stress scenarios...

- Status: PARTIAL
- Evidence: `Main portfolio/analysis_subject/stress_report.json` -> `historical_results` includes five episodes: `dotcom`, `2008`, `2020`, `2022`, `banking_2023`. Reliable computed episodes are `2020` (`pnl_real_episode=-0.0078`, `n_obs=3`), `2022` (`pnl_real_episode=-0.1629`, `n_obs=12`), and `banking_2023` (`pnl_real_episode=0.0072`, `n_obs=4`).
- Problem if any: `dotcom` and `2008` are present but not computed as realized historical PnL because `data_quality="insufficient_data"` and `n_obs=0`.
- Fix needed if any: None if the intended behavior is realized-only historical stress with disclosure. If the product requires old episodes for all portfolios, add a governed proxy/fallback path to the primary historical stress artifact.

## 11. Does it clearly explain if old historical scenarios like dotcom/2008 cannot be computed...

- Status: YES
- Evidence: `Main portfolio/analysis_subject/stress_report.json` -> `data_trust_summary.episode_flags[episode="dotcom"].plain_english` and `episode_flags[episode="2008"].plain_english` state insufficient aligned realized history and unavailable primary historical episode PnL/replay. `data_trust_summary.promoted_warnings` repeats both limitations.
- Problem if any: None for current Blocks 1-5 evidence.
- Fix needed if any: None.

## 12. Does it run synthetic stress scenarios...

- Status: YES
- Evidence: `Main portfolio/analysis_subject/stress_report.json` -> `scenario_results` contains eight synthetic scenarios: `equity_shock`, `credit_shock`, `rates_shock`, `inflation_stagflation`, `liquidity_shock`, `usd_shock`, `commodity_shock`, `recession_severe`. Each row has `portfolio_pnl_pct`, `pass`, `shock_vector`, `pnl_by_asset_pct`, and `synthetic_assumptions.beta_coverage_ratio=1.0`.
- Problem if any: None for the current portfolio.
- Fix needed if any: None.

## 13. Does it show worst stress scenario and loss drivers...

- Status: YES
- Evidence: `Main portfolio/analysis_subject/stress_report.json` -> `worst_scenario_loss_pct=-0.1918`; `stress_conclusions.worst_synthetic_scenario.scenario_id="equity_shock"`; `stress_conclusions.top_loss_assets_worst_scenario=["QQQ","SCHD","SPY"]`; `stress_conclusions.top_factor_drivers_worst_scenario[0].factor="Equity"`; `scenario_results[scenario_id="equity_shock"].pnl_by_asset_pct` gives per-asset loss contributions.
- Problem if any: None for the current portfolio.
- Fix needed if any: None.

## 14. Does it generate a candidate portfolio menu...

- Status: YES
- Evidence: `Main portfolio/candidate_comparison.json` -> `candidate_menu.product_menu_profile_id="default_v1"`; `product_menu_size=16`; `intended_menu_size=16`; `product_menu_status_counts.available=16`; `candidates` contains candidate rows. `Main portfolio/candidate_factory_run.json` -> `summary.total=16`.
- Problem if any: None for the current full-mode artifact.
- Fix needed if any: None.

## 15. Does it separate core vs full candidate modes clearly...

- Status: PARTIAL
- Evidence: `Main portfolio/candidate_comparison.json` -> `candidate_menu.review_mode="full"`; `refresh_command_core="python run_portfolio_review.py --mode core"`; `refresh_command_full="python run_portfolio_review.py --mode full --no-skip-existing"`.
- Problem if any: The artifact shows the current mode and both refresh commands, but it does not include a clear core candidate list vs full candidate list or per-mode status counts.
- Fix needed if any: Add explicit `core_menu` and `full_menu` sections, or add per-candidate mode membership fields to `candidate_menu`.

## 16. Does it generate optimizer-backed candidates in full mode...

- Status: YES
- Evidence: `Main portfolio/candidate_comparison.json` -> `candidate_menu.review_mode="full"` and optimizer-backed candidates with `status="available"` and `construction_disclosure.optimization_readiness.overall_status="ready"` include `maximum_diversification`, `maximum_diversification_uncapped`, `minimum_cvar_constrained`, `minimum_cvar_uncapped`, `minimum_variance`, `minimum_variance_advanced`, `minimum_variance_uncapped`, `robust_mv_constrained`, `robust_mv_uncapped`, and `robust_scenario`. `Main portfolio/candidate_factory_run.json` -> corresponding `steps[*].status="succeeded"` and `freshness_status="fresh"`.
- Problem if any: None for the current full-mode artifact.
- Fix needed if any: None.

## 17. Does it show whether candidates were rebuilt, skipped, stale, failed, or fresh...

- Status: YES
- Evidence: `Main portfolio/candidate_factory_run.json` -> `summary.succeeded=16`; `summary.failed=0`; `summary.skipped_existing=0`; `summary.skipped_dependency=0`; `summary.rebuilt_stale=0`; each `steps[*]` row has `status="succeeded"` and `freshness_status="fresh"`.
- Problem if any: The current run has no skipped/stale/failed examples, so the artifact proves the fields exist and that this run was fresh, not every branch of behavior.
- Fix needed if any: None for this run. Add a small stale/skip fixture only if the demo must show those alternate states.

## 18. Does it show optimizer readiness and methodology/quality metadata...

- Status: YES
- Evidence: `Main portfolio/candidate_comparison.json` -> optimizer-backed candidate rows contain `construction_disclosure.optimization_readiness.overall_status="ready"`, `fair_comparison_ready=true`, `optimizer_methodology`, and `optimizer_quality.optimization_quality_status="clean_solve"`. `Main portfolio/candidate_factory_run.json` -> optimizer steps expose `optimization_status_source`, `optimization_quality_status`, `optimization_quality_family`, `optimizer_fallback_used`, and sometimes `optimizer_solver_status`.
- Problem if any: Some benchmark-like candidates have `optimization_quality_status="unknown"` or partial disclosure, but the optimizer-backed candidates needed for Block 5 readiness show clean metadata.
- Fix needed if any: None for optimizer-backed candidates. Optionally standardize benchmark disclosure so all menu rows use the same readiness vocabulary.

## 19. Does it prepare candidates for later comparison/backtest/stress evaluation...

- Status: YES
- Evidence: `Main portfolio/candidate_comparison.json` -> optimizer-backed candidate `construction_disclosure.optimization_readiness.required_checks` includes present `weights`, `snapshot_10y`, `stress_summary`, `construction_disclosure`, `optimizer_quality`, and `freshness`; candidate rows include `metrics`, `stress.scenarios`, `stress.historical_episodes`, `drawdown`, `diversification`, `weight_concentration`, and `source_files`. `Main portfolio/candidate_factory_run.json` -> `comparison_outputs.candidate_comparison_json` points to the comparison artifact.
- Problem if any: This verifies preparation and readiness only. It does not evaluate Selection, Action Plan, Decision Package, Monitoring, Journal, or UI.
- Fix needed if any: None for Blocks 1-5.

## 20. Can Blocks 1-5 alone be shown as a reliable MVP diagnostic-and-optimization demo...

**Disk caveat (snapshot at write time):** claims in this section about factory scope (e.g. a
**16-candidate** / `default_v1` run) describe evidence **at the time this report was written**, not
guaranteed current disk state. Before demo or audit reuse, open
`{output_dir_final}/candidate_factory_run.json` and confirm `factory_profile_id`, `steps[]`, and
`execution_summary.reused_existing`. A routine **`core_v1`** review leaves a six-step factory record
while `candidate_comparison.json` may still list optimizer rows reused from earlier **`default_v1`**
runs — read `candidate_menu` before treating comparison as full-menu proof.

- Status: PARTIAL
- Evidence: Positive evidence is present in `run_metadata.json` for resolved 8-ticker inputs and assumptions, `portfolio_xray.json` for diagnostics, `stress_report.json` for synthetic stress and partial historical stress, `candidate_factory_run.json` for a fresh 16-candidate factory run *(snapshot at write time; re-verify `factory_profile_id` on disk)*, and `candidate_comparison.json` for full-mode candidate readiness. Limiting evidence is also explicit: `portfolio_xray.sections.factor_exposure.status="partial"`, `stress_report.data_trust_summary.overall_trust="low"`, `historical_results` cannot compute `dotcom` or `2008`, and `candidate_menu` does not fully separate core vs full candidate membership.
- Problem if any: Blocks 1-5 can support a credible MVP diagnostic-and-optimization demo only if the demo clearly states the limitations: factor exposure is partial, old historical stress episodes are unavailable for this current portfolio, and core/full menu separation is not fully explicit in the artifacts.
- Fix needed if any: Before calling it fully reliable as a standalone MVP demo, add fuller factor coverage or clearer factor-missing disclosure, add explicit core/full menu membership, and decide whether old historical stress should remain realized-only with disclosure or get a governed fallback in the primary historical stress artifact.
