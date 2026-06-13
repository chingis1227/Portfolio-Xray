# Block 3.2 Stress Results MVP

**Status: Completed** (Session 08 closed 2026-05-27). Prerequisite: Block 3.1 Scenario Library **Done** ([stress_lab_layer_spec.md](../specs/stress_lab_layer_spec.md) §3.1; [scenario_library.py](../../src/scenario_library.py) canonical IDs). Evidence: [acceptance audit](../audits/2026-05-27_block_3_2_stress_results_acceptance_audit.md); closure pytest **75 passed**; live `stress_results_v1` on subject `stress_report.json`.

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document follows [PLANS.md](../../PLANS.md) from the repository root.

**Canonical specs (read order):**

- [docs/specs/stress_lab_layer_spec.md](../specs/stress_lab_layer_spec.md) — Block 3 boundary (rename §3.2 to Stress Results in Session 01)
- [docs/specs/stress_testing_spec.md](../specs/stress_testing_spec.md) — §12 scorecard/conclusions; add `stress_results_v1` in Session 01
- [docs/specs/scenario_library_spec.md](../specs/scenario_library_spec.md) — Block 3.1 sidecars
- [PRODUCT.md](../../PRODUCT.md) — add §4.3.2 in Session 01

## Purpose / Big Picture

After this migration, a portfolio-first operator running `python run_portfolio_review.py` on the current [config.yml](../../config.yml) reads `{output_dir_final}/analysis_subject/stress_report.json` and gets a **stable product-facing Block 3.2** that answers: *for each active stress scenario, what happened to the portfolio, what drove the loss, what offset it, and how confident is the evidence...* — without parsing raw `scenario_results` / `historical_results` rows or reintroducing client mandate pass/fail in Core MVP diagnostic mode.

Block 3.2 is delivered as **`stress_results_v1`** on `stress_report.json` (Stress Test Lab boundary — **not** `portfolio_xray.json`). Existing **`stress_conclusions`** (`stress_conclusions_v1`) remains the worst-case rollup for snapshot, comparison, and commentary backward compatibility.

**User-visible proof (Session 08 target):** open `Main portfolio/analysis_subject/stress_report.json` → `stress_results_v1` with 8 synthetic + 5 historical per-scenario diagnosis rows, `worst_synthetic` / `worst_historical`, English `diagnosis_summary_en` per scenario when data allows, and `loss_gate_mode: diagnostic` with no mandate `pass`/`loss_ok` on Block 3.2 product rows.

## Non-goals

- No new scenarios; no changes to Block 3.1 shock vectors or `HISTORICAL_EPISODES` / `SCENARIOS`.
- No client mandate comparison, `max_dd_limit` pass/fail, `DIAG_LOSS_*`, `DIAG_HIST_*`, or suitability gates inside Block 3.2 Core MVP output.
- No optimizer, candidate ranking, health score, or trading recommendations.
- No `portfolio_xray.json` product block unless explicitly promoted later.
- No PDF/HTML redesign in this wave (commentary may add a short pointer only).
- No LLM-generated narratives (template English from computed facts only).

## Progress

- [x] (2026-05-27) **Session 00 — ExecPlan foundation + field audit:** Created this ExecPlan; embedded code/spec field inventory; registered **Active** in [docs/exec_plans/README.md](README.md). No application code.
- [x] (2026-05-27) **Session 01 — Product contract (docs):** Renamed Block 3.2 to Stress Results in stress layer/spec docs; added normative `stress_results_v1` contract in stress testing spec §12.1; added PRODUCT §4.3.2; synced SPEC/OUTPUTS/TESTING/DECISIONS; `verify_docs.py` passed.
- [x] (2026-05-27) **Session 02 — Builder scaffold:** dedicated Block 3.2 builder module + empty-structure tests.
- [x] (2026-05-27) **Session 03 — Synthetic per-scenario rows + narratives:** 8 canonical synthetic product rows, factor drivers helper, `diagnosis_summary_en` templates, envelope `top3_loss_assets`/`top_factor_drivers` from worst row; 9 new contract tests (37 total passed).
- [x] (2026-05-27) **Session 04 — Historical per-scenario rows (paths → loss contribution).**
- [x] (2026-05-27) **Session 05 — Wire `run_stress` + `run_report` refresh after historical factor enrichment:** `attach_stress_results_v1` in `stress_results_block.py`; called from `run_stress`, `_empty_report`, `run_report.py` (post-enrichment/overlay), `run_optimization.py` (pre-export); 4 wiring tests added (55 total passed).
- [x] (2026-05-27) **Session 06 — Minimal commentary/snapshot mirror:** `_append_stress_results_v1_section` in `portfolio_commentary.py` (stress + portfolio commentary); compact `stress_results` envelope mirror in `snapshot.py` and `candidate_comparison.py`; downstream integration tests extended.
- [x] (2026-05-27) **Session 07 — Contract tests + regression bundle + CHANGELOG:** Extended `test_stress_diagnostic_mode.py`, `test_stress_scenario_coverage_contract.py`, and `test_stress_results_block_contract.py`; added Block 3.2 regression bundle + governance bundle entries in `TESTING.md`; `live_core_e2e` + offline MVP fixture require `stress_results_v1`; CHANGELOG entry.
- [x] (2026-05-27) **Session 08 — Live validation + acceptance audit + plan closure:** `run_portfolio_review.py --skip-candidates`; subject `stress_report.json` validated (8+5 rows, diagnostic mode, worst selectors); [acceptance audit](../audits/2026-05-27_block_3_2_stress_results_acceptance_audit.md); Block 3.2 pytest bundle **75 passed**.

## Surprises & Discoveries

### Session 00 — Field audit (source / derive / unavailable)

**Observation:** Block 3.2 product concepts are **mostly already computed** in `run_stress` evidence rows; the gap is a **unified per-scenario product layer** and **historical asset loss contribution** (not on `historical_results` rows today).

**Observation:** Spec title §3.2 is still 「Stress Conclusions」 while product brief names **Stress Results**; implementation will add `stress_results_v1` and keep `stress_conclusions` as worst-case rollup.

#### A. Block 3.1 linkage (must not invent IDs)

| Product need | Source | Action for Block 3.2 |
| --- | --- | --- |
| Synthetic scenario set (8) | `SYNTHETIC_SCENARIO_IDS` in [src/scenario_library.py](../../src/scenario_library.py) | Copy into `stress_results_v1.scenario_library.synthetic_ids`; iterate `scenario_results` in this order |
| Historical scenario set (5) | `HISTORICAL_SCENARIO_IDS` in `scenario_library.py` | Copy into `scenario_library.historical_ids`; iterate `historical_results` in this order |
| Registry in stress engine | `SCENARIOS` + `recession_severe` merge, `HISTORICAL_EPISODES` in [src/stress.py](../../src/stress.py) | Evidence only; IDs must match library tuples |
| Sidecar metadata | `scenario_library_meta` on `stress_report.json` from [run_report.py](../../run_report.py) | Optional cross-check; not required to build Block 3.2 |
| Contract tests | [tests/test_stress_scenario_coverage_contract.py](../../tests/test_stress_scenario_coverage_contract.py) | Reuse in Session 07 |

#### B. Product concept → field mapping (per scenario)

| # | Product concept | Synthetic | Historical |
| --- | --- | --- | --- |
| 1 | Portfolio loss | **Source:** `scenario_results[].portfolio_pnl_pct` → product `portfolio_loss_pct` | **Source:** `historical_results[].pnl_real_episode` → `portfolio_loss_pct` |
| 2 | Drawdown | **N/A** (`drawdown_pct: null`, `availability: not_applicable`) | **Source:** `historical_results[].max_dd` → `drawdown_pct` |
| 3 | Loss contribution | **Source:** `top3_loss_assets`, `pnl_by_asset_pct` on same row | **Derive:** join `historical_episode_paths[].asset_pnl_contrib_episode` + `top_loss_assets_episode` by `episode`; build `pnl_by_asset_pct` map and `top3_loss_assets`. **Unavailable** when episode path missing or `n_obs < 2` (no contrib block) — `reason_en: insufficient_episode_data` |
| 4 | Asset risk contribution | **Source:** `top1_rc_asset`, `top1_rc_pct`, `top3_rc_assets`, `top3_rc_sum_pct` | **Unavailable:** `not_applicable` — stressed covariance RC is synthetic-only ([stress_testing_spec.md](../specs/stress_testing_spec.md) §2.2); historical uses realized monthly path |
| 5 | Factor stress attribution | **Source:** `pnl_by_factor_pct`; **derive** `top_factor_drivers` (reuse `_worst_scenario_factor_drivers` pattern in `stress.py`) | **Source (full report):** `historical_results[].pnl_by_factor_pct` after [enrich_historical_results_with_factor_attribution](../../src/stress_factors.py) in `run_report.py`. **Unavailable** on `run_stress`-only paths until enrichment — `reason_en: factor_attribution_requires_report_enrichment` |
| 6 | Worst scenario (envelope) | **Derive:** `min(portfolio_pnl_pct)` over `scenario_results` — already in `run_stress` (~L1751–1756) and `stress_conclusions.worst_synthetic_scenario` | **Derive:** `min(max_dd)` via `_select_worst_historical_row` (~L887–892) — **not** `min(pnl_real_episode)` |
| 7 | Assets hurt / helped | **Hurt:** top negative from `pnl_by_asset_pct` / `top3_loss_assets`. **Helped:** positive `pnl_by_asset_pct` tickers; **product rule:** populate `helped_assets_worst_synthetic` at envelope + `assets_helped` on **worst synthetic row only** (mirror `helped_assets` built ~L1758–1766) | **Hurt:** from derived loss contribution. **Helped:** list positive contrib tickers when data exists; no global 「worst historical helped」 in product brief |

#### C. Existing `scenario_results[]` row fields (synthetic evidence — do not recompute PnL)

Generated in `run_stress` (~L1529–1564):

| Field | In evidence today | Include in Block 3.2 product row |
| --- | --- | --- |
| `scenario_id` | Yes | Yes (`scenario_id`) |
| `portfolio_pnl_pct` | Yes | Yes (`portfolio_loss_pct`) |
| `pnl_by_asset_pct` | Yes | Yes (under `loss_contribution`) |
| `top3_loss_assets` | Yes | Yes |
| `pnl_by_factor_pct` | Yes | Yes (under `factor_attribution`) |
| `top1_rc_asset`, `top1_rc_pct`, `top3_rc_assets`, `top3_rc_sum_pct` | Yes | Yes (under `risk_contribution`) |
| `pass`, `loss_ok`, `diagnostic_codes` | Yes (null in diagnostic mode) | **Omit** from Block 3.2 in `loss_gate_mode=diagnostic` |
| `shock_vector`, `synthetic_assumptions`, stress cov metadata | Yes | Optional `evidence_refs` only; not required for MVP narrative |

#### D. Existing `historical_results[]` row fields

Generated in `run_stress` (~L1624–1638):

| Field | In evidence today | Block 3.2 |
| --- | --- | --- |
| `episode` | Yes | Yes |
| `pnl_real_episode` | Yes | `portfolio_loss_pct` |
| `max_dd` | Yes | `drawdown_pct` |
| `pass`, `diagnostic_code` | Yes (mandate only) | Omit in diagnostic mode |
| `data_quality`, `coverage_ratio`, `n_obs` | Yes | Copy for trust disclosure |
| `return_method`, `proxy_used` | Yes | Copy (primary path realized-only) |
| `pnl_by_asset_pct`, `top3_loss_assets` | **No** | Derive from paths (see B.3) |
| `pnl_by_factor_pct` | **No** until `run_report` enrichment | Copy when present |

Post-enrichment fields on `historical_results` ([stress_factors.py](../../src/stress_factors.py) ~L3105–3180): `pnl_by_factor_pct`, `top_factor_drivers`, `historical_factor_attribution`, `factor_model_pnl_pct`, `factor_model_error_pct`, etc.

#### E. `historical_episode_paths[]` (crisis replay — loss contribution source)

Built in `run_stress` (~L1651–1666):

| Field | Use in Block 3.2 |
| --- | --- |
| `episode` | Join key to `historical_results` |
| `asset_pnl_contrib_episode` | **Primary** source for historical `pnl_by_asset_pct` (static-weight monthly sum; `_episode_asset_pnl_contrib` ~L641–651) |
| `top_loss_assets_episode` | Cross-check / fallback for `top3_loss_assets` |
| `rows`, recovery fields | Not duplicated in Block 3.2 (Block 3.4 crisis replay) |

#### F. Existing rollup blocks (keep; Block 3.2 complements)

| JSON key | Role | Relationship to Block 3.2 |
| --- | --- | --- |
| `stress_conclusions` | Worst synthetic/historical + helped assets/factors + hedge mirror | Subset; worst IDs must match `stress_results_v1.worst_*` |
| `stress_scorecard_v1` | Abbreviated per-scenario table + suite status | Parallel; scorecard omits `pnl_by_factor_pct` and narratives |
| `scenario_results` / `historical_results` | Full evidence | Source of truth for numbers; Block 3.2 is adapter + narrative |

#### G. Core MVP diagnostic boundary (already implemented)

| Check | Evidence |
| --- | --- |
| `loss_gate_mode=diagnostic` when `analysis_mode=analyze_current_weights` | [run_report.py](../../run_report.py) ~L1081–1103 |
| Row `pass`/`loss_ok` null; no `DIAG_*` suite status | [tests/test_stress_diagnostic_mode.py](../../tests/test_stress_diagnostic_mode.py) |
| Block 3.2 must not reintroduce mandate fields | Session 07 contract test |

#### H. Gap list (Session 00 → implementation backlog)

| ID | Gap | Priority | Session |
| --- | --- | --- | --- |
| G1 | No `stress_results_v1` key on `stress_report.json` | P0 | 02–05 |
| G2 | Spec §3.2 titled 「Conclusions」not 「Results」 | P0 | 01 |
| G3 | No per-scenario product rows for all 13 scenarios | P0 | 03–04 |
| G4 | Historical loss contribution only on episode paths | P0 | 04 |
| G5 | Historical factor only after `run_report` enrichment | P1 | 05 (rebuild Block 3.2 post-enrichment) |
| G6 | No `diagnosis_summary_en` template | P1 | 03–04 |
| G7 | `TESTING.md` / `live_core_e2e` do not list `stress_results_v1` | P2 | 01, 07 |
| G8 | Commentary does not surface Block 3.2 | P2 | 06 **Done** |

## Decision Log

- Decision: Deliver Block 3.2 as **`stress_results_v1`** on `stress_report.json`, not on `portfolio_xray.json`.
  Rationale: Stress Lab product boundary; Block 3.1 has no X-Ray key either.
  Date/Author: 2026-05-27 / Session 00.

- Decision: Keep **`stress_conclusions`** unchanged as worst-case rollup; do not rename JSON key.
  Rationale: Downstream consumers (`snapshot.py`, `candidate_comparison.py`, commentary) already depend on it.
  Date/Author: 2026-05-27 / Session 00.

- Decision: Historical **risk contribution under stress** is `not_applicable` in Block 3.2 product rows.
  Rationale: RC fields are computed from stressed covariance in synthetic engine only; inventing historical RC would violate stress spec.
  Date/Author: 2026-05-27 / Session 00.

- Decision: Historical **loss contribution** is **derived** from `historical_episode_paths`, not added to `historical_results` evidence rows in this wave.
  Rationale: Avoid duplicating evidence layer; paths already hold `asset_pnl_contrib_episode`.
  Date/Author: 2026-05-27 / Session 00.

- Decision: Rebuild `stress_results_v1` in `run_report.py` after `enrich_historical_results_with_factor_attribution`.
  Rationale: Historical `pnl_by_factor_pct` does not exist at `run_stress` return time.
  Date/Author: 2026-05-27 / Session 00.

- Decision: **`helped_assets`** populated only for worst synthetic scenario (envelope + that row), per product brief.
  Rationale: User definition §7; avoids implying offsetting assets in every shock.
  Date/Author: 2026-05-27 / Session 00.

## Outcomes & Retrospective

**Session 00 (2026-05-27):** ExecPlan created with full field audit (sections A–H above). Registered **Active** in exec plan README. No application code. Next: Session 01 product contract in specs.

**Session 01 (2026-05-27):** Documentation contract baseline landed for Block 3.2 Stress Results. Specs now define `stress_results_v1` as the product-facing Block 3.2 contract on `stress_report.json`, while `stress_conclusions` remains compatibility rollup. PRODUCT/SPEC/OUTPUTS/TESTING/DECISIONS synchronized; no runtime code changes yet.

**Session 02 (2026-05-27):** Builder scaffold delivered. `src/stress_results_block.py` created with `build_stress_results_v1`, `empty_stress_results_v1`, envelope helpers, and worst-scenario selectors (priority to `stress_conclusions`, fallback to min-scan). 28 contract tests in `tests/test_stress_results_block_contract.py` — all passed. No circular imports with `src/stress.py`. Per-scenario rows (`synthetic_scenarios`, `historical_episodes`) are empty lists pending Session 03–04.

**Session 03 (2026-05-27):** Synthetic per-scenario product rows implemented in `src/stress_results_block.py`: canonical order over `SYNTHETIC_SCENARIO_IDS`, `loss_contribution` / `factor_attribution` / `risk_contribution` sub-blocks, `_synthetic_factor_drivers` (mirrors `stress.py` without import), English `diagnosis_summary_en` template, `assets_helped` only on worst synthetic row, envelope enriched from built rows. `historical_episodes` remains `[]` until Session 04. `python -m pytest tests/test_stress_results_block_contract.py -q` → 37 passed. Wiring into `run_stress` deferred to Session 05.

**Session 04 (2026-05-27):** Historical per-episode product rows in `src/stress_results_block.py`: join `historical_episode_paths` for `asset_pnl_contrib_episode` → `loss_contribution`; factor copy when `pnl_by_factor_pct` present else `factor_attribution_requires_report_enrichment`; RC `not_applicable`; `assets_helped` from positive contrib; English `diagnosis_summary_en` historical template; envelope `worst_historical.top3_loss_assets` from built rows. 14 new contract tests; `python -m pytest tests/test_stress_results_block_contract.py -q` → 51 passed. Wiring deferred to Session 05.

**Session 05 (2026-05-27):** Wired Block 3.2 onto `stress_report.json`: `attach_stress_results_v1` rebuilds in-place from evidence rows; `run_stress` and `_empty_report` always emit `stress_results_v1`; `run_report.py` refreshes after historical factor enrichment and adjusted overlay; `run_optimization.py` refreshes before `export_stress_report`. Four integration tests in `tests/test_stress_results_block_contract.py`; 55 passed.

**Session 06 (2026-05-27):** Minimal downstream mirror: `_append_stress_results_v1_section` surfaces Block 3.2 envelope and worst-case `diagnosis_summary_en` in `stress_commentary.txt` and `commentary.txt`; `snapshot_10y.json` `stress_suite_results.stress_results` carries compact envelope; `candidate_comparison` merges `stress_results` from snapshot or `stress_report.json`. `tests/test_stress_downstream_integration.py` extended.

**Session 07 (2026-05-27):** Regression closure — extended diagnostic-mode, scenario-coverage, and Block 3.2 contract tests; `TESTING.md` Stress Lab governance bundle + dedicated Block 3.2 bundle; `live_core_e2e` and offline MVP fixture require `stress_results_v1`; CHANGELOG. No application logic changes.

**Session 08 (2026-05-27):** Live proof and plan closure — `python run_portfolio_review.py --skip-candidates` on root `config.yml`; `Main portfolio/analysis_subject/stress_report.json` contains `stress_results_v1` (8 synthetic + 5 historical, `loss_gate_mode: diagnostic`, envelope worst synthetic `recession_severe` / worst historical `2022` aligned with `stress_conclusions`); [acceptance audit](../audits/2026-05-27_block_3_2_stress_results_acceptance_audit.md); Block 3.2 pytest bundle **75 passed**; ExecPlan **Completed**.

## Context and Orientation

Portfolio MRI Core MVP flow: Input → Portfolio X-Ray → **Stress Test Lab** → Problem Classification → candidates. Block 3 lives on **`stress_report.json`** under each portfolio output folder (primary: `Main portfolio/analysis_subject/stress_report.json`).

Stress pipeline today:

```text
monthly returns + weekly betas + config
  -> run_stress (src/stress.py)
       -> scenario_results[] (8 synthetic)
       -> historical_results[] (5)
       -> historical_episode_paths[] (crisis replay)
       -> stress_scorecard_v1, stress_conclusions, hedge_gap_analysis
  -> run_report.py (full path)
       -> enrich_historical_results_with_factor_attribution
       -> scenario_library.json sidecars
       -> stress_commentary.txt
```

**Loss gate mode:** `diagnostic` (Core MVP portfolio-first) vs `mandate` (legacy policy). Block 3.2 reports facts and interpretation only; mandate pass/fail stays off product rows in diagnostic mode.

**Worst scenario rules (must match existing code):**

- Worst synthetic: minimum `portfolio_pnl_pct`.
- Worst historical: minimum `max_dd` among rows with computed drawdown.

## Plan of Work

### Session 01 — Docs only

Update [stress_lab_layer_spec.md](../specs/stress_lab_layer_spec.md) §3.2 title and tables; add `stress_results_v1` to core blocks table. Extend [stress_testing_spec.md](../specs/stress_testing_spec.md) §12 with normative JSON contract. Add PRODUCT §4.3.2. Touch SPEC.md, OUTPUTS.md, TESTING.md, DECISIONS.md. Run `python scripts/verify_docs.py`.

### Session 02 — Block 3.2 builder module

Implement `build_stress_results_v1(stress_report: dict) -> dict` with envelope + empty arrays; unit tests for structure.

### Session 03 — Synthetic rows

Map each `scenario_results` row; factor drivers helper; `diagnosis_summary_en` template (loss %, top factors, hurt assets).

### Session 04 — Historical rows

Join paths; loss contribution derive; factor copy when present; historical narrative template.

### Session 05 — Wire-up

Call builder at end of `run_stress`; rebuild in `run_report.py` after historical enrichment; extend `_empty_report`.

### Session 06 — Downstream (minimal)

Optional lines in `portfolio_commentary.py`; optional snapshot mirror if comparison needs it.

### Session 07 — Tests

New Block 3.2 contract test module; extend diagnostic mode test; regression bundle; CHANGELOG.

### Session 08 — Live proof

`python run_portfolio_review.py`; inspect subject `stress_report.json`; write Session 08 acceptance audit in `docs/audits/`; mark plan **Completed**.

## Concrete Steps

Session 00 (complete):

    # From repository root — documentation only
    # Confirm canonical IDs unchanged:
    python -c "from src.scenario_library import SYNTHETIC_SCENARIO_IDS, HISTORICAL_SCENARIO_IDS; print(len(SYNTHETIC_SCENARIO_IDS), len(HISTORICAL_SCENARIO_IDS))"

Expected: `8 5`.

Session 01 (next):

    python scripts/verify_docs.py

Session 07 (target):

    python -m pytest <block_3_2_contract_test_module> -q
    python -m pytest tests/test_stress_diagnostic_mode.py tests/test_stress_scorecard_contract.py tests/test_stress_scenario_coverage_contract.py -q

Session 08 (target):

    python run_portfolio_review.py --skip-candidates

## Validation and Acceptance

**Session 00 acceptance:** This ExecPlan exists at `docs/exec_plans/2026-05-27_block_3_2_stress_results_plan.md`; field audit in `Surprises & Discoveries`; README **Active** pointer updated. No pytest required.

**Final acceptance (Session 08):** Subject `stress_report.json` contains `stress_results_v1` with 8+5 scenarios, correct worst selectors, diagnostic mode without mandate fields on Block 3.2 rows, and English summaries where data exists.

## Idempotence and Recovery

Sessions 01–08 are additive. Re-running `run_portfolio_review.py` overwrites `stress_report.json`. No migrations. If Session 05 wiring breaks tests, revert `run_stress` call and keep builder tested in isolation until fixed.

## Artifacts and Notes

Canonical scenario IDs (Block 3.1 — frozen):

**Synthetic:** `equity_shock`, `credit_shock`, `rates_shock`, `inflation_stagflation`, `liquidity_shock`, `usd_shock`, `commodity_shock`, `recession_severe`.

**Historical:** `dotcom`, `2008`, `2020`, `2022`, `banking_2023`.

Example product narrative (template target — Session 03–04; numbers illustrative only):

    In a 2008-like episode, the portfolio return was -24.6% with a peak drawdown of -31.2%.
    Model factor attribution points to equity and credit channels as the largest loss drivers;
    treasury holdings offset part of the decline.

## Interfaces and Dependencies

Planned module: dedicated Block 3.2 builder (Session 02).

    BLOCK_3_2_VERSION = "stress_results_v1"

    def build_stress_results_v1(
        *,
        scenario_results: list[dict[str, Any]],
        historical_results: list[dict[str, Any]],
        historical_episode_paths: list[dict[str, Any]],
        stress_conclusions: dict[str, Any],
        loss_gate_mode: str,
        helped_assets_worst_synthetic: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        ...

Imports: `SYNTHETIC_SCENARIO_IDS`, `HISTORICAL_SCENARIO_IDS`, `SCENARIO_LIBRARY_VERSION` from `src.scenario_library`; reuse `_worst_scenario_factor_drivers` / `_select_worst_historical_row` from `src.stress` or duplicate minimal selection logic in the block module to avoid circular imports (decide in Session 02).

Wire points:

- [src/stress.py](../../src/stress.py) — `run_stress` return dict and `_empty_report`
- [run_report.py](../../run_report.py) — after historical factor enrichment (~L1865+)

Tests: dedicated Block 3.2 contract test module (Session 02+).
