# Block 3.3 Hedge Gap Analysis MVP

**Status: Completed** (Sessions 00–08 closed 2026-05-27). Prerequisites: Block 3.1 Scenario Library **Done**; Block 3.2 Stress Results **Done** ([stress_results_v1](2026-05-27_block_3_2_stress_results_plan.md) closed 2026-05-27; [acceptance audit](../audits/2026-05-27_block_3_2_stress_results_acceptance_audit.md)).

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document follows [PLANS.md](../../PLANS.md) from the repository root.

**Canonical specs (read order):**

- [docs/specs/stress_lab_layer_spec.md](../specs/stress_lab_layer_spec.md) — renumber Core MVP blocks (3.3 = Hedge Gap; simulator/crisis replay → deferred)
- [docs/specs/hedge_gap_analysis_spec.md](../specs/hedge_gap_analysis_spec.md) — add v1 contribution-based contract in Session 01
- [docs/specs/stress_testing_spec.md](../specs/stress_testing_spec.md) — §12 hedge gap; link to Block 3.2
- [PRODUCT.md](../../PRODUCT.md) — add §4.3.3 in Session 01

## Purpose / Big Picture

After this migration, a portfolio-first operator running `python run_portfolio_review.py` on the current [config.yml](../../config.yml) reads `{output_dir_final}/analysis_subject/stress_report.json` and gets a **stable product-facing Block 3.3** that answers: *for each key market risk type, did assets that helped actually offset losses from assets that hurt in the mapped stress scenario, where is protection weak, and what is the main hedge gap?* — without pre-labeling holdings as hedge assets, without re-running the stress engine, and without client mandate pass/fail in Core MVP diagnostic mode.

Block 3.3 is delivered as **`hedge_gap_analysis_v1`** on `stress_report.json` (Stress Test Lab boundary — **not** `portfolio_xray.json`). It consumes **already calculated** stress evidence from Block 3.1 (`scenario_results[]`) and Block 3.2 (`stress_results_v1`). Legacy **`hedge_gap_analysis`** (`stress_scenario_hedge_evidence_v2`, taxonomy hedge labels) remains for backward compatibility; Core MVP operators read **`hedge_gap_analysis_v1`**.

**User-visible proof (Session 08 target):** open `Main portfolio/analysis_subject/stress_report.json` → `hedge_gap_analysis_v1` with seven `by_risk_type[]` rows (one per Core MVP risk type), `offset_coverage_ratio` where asset contributions allow, `summary.main_hedge_gap` / `weakest_protection_area`, English `diagnosis_summary_en` per risk type and overall, and `loss_gate_mode: diagnostic` with no mandate fields on Block 3.3 product rows.

## Non-goals

- No new scenarios; no changes to Block 3.1 shock vectors or `HISTORICAL_EPISODES` / `SCENARIOS`.
- No second stress engine or PnL recomputation (read evidence only).
- No taxonomy `risk_role` pre-labeling of hedge assets in Block 3.3 v1.
- No client mandate comparison, `max_dd_limit` pass/fail, `DIAG_*`, or suitability gates inside Block 3.3 Core MVP output.
- No optimizer, candidate ranking, health score, or trading recommendations.
- No `portfolio_xray.json` product block in this wave.
- No PDF/HTML redesign (commentary may add a short pointer only in Session 06).
- No LLM-generated narratives (template English from computed facts only).
- No retirement of legacy `hedge_gap_analysis` in this wave (deprecation deferred).
- Historical episode → risk-type mapping deferred (synthetic-only rows in v1).

## Progress

- [x] (2026-05-27) **Session 00 — ExecPlan foundation + field audit:** Created this ExecPlan; embedded legacy vs v1 field inventory; registered **Active** in [docs/exec_plans/README.md](README.md). No application code.
- [x] (2026-05-27) **Session 01 — Product contract (docs):** Renumbered Stress Lab Core MVP (3.3 Hedge Gap, 3.4 Scorecard); deferred simulator/crisis replay; normative `hedge_gap_analysis_v1` in specs; PRODUCT §4.3.3; synced SPEC/OUTPUTS/TESTING/DECISIONS/CHANGELOG; `verify_docs.py` passed.
- [x] (2026-05-27) **Session 02 — Builder scaffold:** `src/hedge_gap_analysis_block.py` + empty-structure tests.
- [x] (2026-05-27) **Session 03 — Per-risk rows + offset_coverage_ratio:** Seven risk types; hurt/helped from signed `pnl_by_asset_pct`; ratio math.
- [x] (2026-05-27) **Session 04 — Summary + narratives:** `main_hedge_gap`, weakest/strongest protection, template `diagnosis_summary_en`.
- [x] (2026-05-27) **Session 05 — Wire `run_stress` + `run_report` refresh:** `attach_hedge_gap_analysis_v1` after `attach_stress_results_v1`.
- [x] (2026-05-27) **Session 06 — Minimal commentary/snapshot mirror:** Pointer in `portfolio_commentary.py`; compact snapshot mirror; `live_core_e2e` key.
- [x] (2026-05-27) **Session 07 — Contract tests + regression bundle + CHANGELOG:** `test_hedge_gap_analysis_v1_contract.py` extended; diagnostic-mode hedge-gap coverage; Block 3.3 regression bundle in TESTING.md; CHANGELOG entry for Session 07.
- [x] (2026-05-27) **Session 08 — Live validation + acceptance audit + plan closure:** `run_portfolio_review.py --skip-candidates`; acceptance audit `docs/audits/2026-05-27_block_3_3_hedge_gap_acceptance_audit.md`; closure pytest; mark **Completed**.

## Surprises & Discoveries

### Session 00 — Field audit (legacy vs v1; source / derive / unavailable)

**Observation:** Contribution-based hedge diagnosis data **already exists** on every synthetic `scenario_results[]` row as `pnl_by_asset_pct`. Block 3.2 copies it into `stress_results_v1.synthetic_scenarios[].loss_contribution` but only populates `assets_helped` on the **worst** synthetic row. Block 3.3 must read **per linked scenario** (all seven mapped synthetics), not only the global worst.

**Observation:** Legacy `hedge_gap_analysis` (`stress_scenario_hedge_evidence_v2` in [src/stress.py](../../src/stress.py) ~L1011–1311) uses taxonomy `risk_role` labels (`crisis_hedge`, `defensive`, `inflation_hedge`, `tail_hedge`) and flags gap when hedge-labeled tickers have non-positive PnL in a loss scenario. That is **not** the product definition for Block 3.3. Portfolios without hedge labels often get `status: not_applicable` on legacy block while v1 can still diagnose offset coverage from contributions.

**Observation:** [stress_lab_layer_spec.md](../specs/stress_lab_layer_spec.md) currently numbers Hedge Gap as §3.5 and What Happens If as §3.3. Product brief and user decision require renumbering: **Core MVP 3.3 = Hedge Gap**, **3.4 = Scorecard**; simulator and crisis replay → advanced/deferred (code remains).

#### A. Block 3.1 / 3.2 linkage (must not invent IDs)

| Product need | Source | Action for Block 3.3 |
| --- | --- | --- |
| Synthetic scenario set (8) | `SYNTHETIC_SCENARIO_IDS` in [src/scenario_library.py](../../src/scenario_library.py) | Seven risk types map 1:1 to seven synthetics; `recession_severe` excluded from v1 rows (see Decision Log) |
| Per-scenario asset PnL | `scenario_results[].pnl_by_asset_pct` | Primary evidence for hurt/helped split |
| Per-scenario portfolio loss | `scenario_results[].portfolio_pnl_pct` or Block 3.2 `portfolio_loss_pct` | Product `portfolio_loss_pct` on each risk row |
| Block 3.2 mirror | `stress_results_v1.synthetic_scenarios[]` | Preferred read path: `loss_contribution.pnl_by_asset_pct`; fallback to `scenario_results` |
| Scenario library meta | `stress_results_v1.scenario_library` | Copy synthetic_ids for linkage tests |
| Contract tests | [tests/test_stress_scenario_coverage_contract.py](../../tests/test_stress_scenario_coverage_contract.py), [tests/test_stress_results_block_contract.py](../../tests/test_stress_results_block_contract.py) | Reuse in Session 07 |

#### B. Block 3.3 risk type → scenario mapping (v1 — frozen for implementation)

| `risk_type` | `linked_scenario_id` | `scenario_type` |
| --- | --- | --- |
| `equity_crash_protection` | `equity_shock` | `synthetic` |
| `rates_up_shock_protection` | `rates_shock` | `synthetic` |
| `stagflation_protection` | `inflation_stagflation` | `synthetic` |
| `liquidity_shock_protection` | `liquidity_shock` | `synthetic` |
| `usd_spike_protection` | `usd_shock` | `synthetic` |
| `credit_shock_protection` | `credit_shock` | `synthetic` |
| `commodity_inflation_shock_protection` | `commodity_shock` | `synthetic` |

Registry constant (planned): `BLOCK_3_3_RISK_SCENARIO_MAP` in `src/hedge_gap_analysis_block.py`. Do **not** reuse legacy `HEDGE_GAP_SCENARIO_BY_RISK` weakness bucket ids (`recession`, `inflation`, …) as product `risk_type` strings.

#### C. Product field → source mapping (per risk row)

| Product field | Source / derive | Unavailable when |
| --- | --- | --- |
| `risk_type` | Fixed map key | — |
| `linked_scenario_id` | Map value | — |
| `linked_episode` | `null` (v1 synthetic-only) | — |
| `scenario_type` | `"synthetic"` | — |
| `portfolio_loss_pct` | Linked `scenario_results` or Block 3.2 row | Scenario row missing |
| `assets_hurt` | Tickers with `pnl_by_asset_pct < 0`, sorted most negative first; shape `{ticker, pnl_pct}` | No `pnl_by_asset_pct` dict |
| `assets_helped` | Tickers with `pnl_by_asset_pct > 0`, sorted largest positive first | Same |
| `gross_loss_from_assets_hurt` | `sum(abs(pnl_pct))` over hurt assets | No hurt assets |
| `positive_contribution_from_assets_helped` | `sum(pnl_pct)` over helped assets | No helped assets (ratio may still be 0) |
| `offset_coverage_ratio` | `positive_contribution / gross_loss` when `gross_loss > 0` | `gross_loss == 0` or missing contrib → `null` + reason |
| `loss_concentration` | `top3_share_of_gross_loss`: sum of abs top-3 hurt / `gross_loss` | `gross_loss` unavailable |
| `data_availability` | `available` \| `insufficient_data` \| `unavailable` | See reason codes in spec Session 01 |
| `diagnosis_summary_en` | Template from computed fields | Missing portfolio loss |

**Formula (product):** `offset_coverage_ratio = positive_contribution_from_assets_helped / gross_loss_from_assets_hurt` (example: hurt gross 12%, helped +2.5% → ratio ≈ 0.208 → report as 21% in narrative).

#### D. Overall summary fields

| Field | Derive rule |
| --- | --- |
| `main_hedge_gap` | Among rows with numeric `offset_coverage_ratio`: minimum ratio (weakest offset); tie-break by more negative `portfolio_loss_pct` |
| `weakest_protection_area` | `risk_type` of `main_hedge_gap` |
| `strongest_protection_area` | Maximum `offset_coverage_ratio` when ≥2 rows have ratio; else `null` |
| `diagnosis_summary_en` | Portfolio-level template (main gap + contrast vs stronger areas) |
| `data_quality_warnings` | Missing contrib, scenario missing, all ratios unavailable, etc. |

#### E. Legacy `hedge_gap_analysis` (keep; do not extend for v1)

Present on every `run_stress` output ([src/stress.py](../../src/stress.py) ~L1768, ~L1819):

| Legacy field | v1 equivalent? | Notes |
| --- | --- | --- |
| `method` | `version` + `diagnosis_method` | v2 vs v1 |
| `hedge_label_risk_roles`, `hedge_assets_considered` | **No** | Taxonomy-only |
| `worst_scenario_id` (global min PnL) | Partial | v1 evaluates per risk type, not one global worst |
| `hedge_assets_negative_in_worst_scenario` | **No** | Replaced by contribution-based hurt/helped |
| `by_risk_type[]` with `gap_detected` / hedge-negative | **Replaced** | New row shape (offset ratio, not label gap) |
| `status`, `stress_conclusions.hedge_gap_status` | Legacy only in Session 05 | v1 summary does not copy mandate semantics |

Tests: [tests/test_stress_hedge_gap_contract.py](../../tests/test_stress_hedge_gap_contract.py) — must stay green unchanged in Session 07.

#### F. Existing Block 3.2 fields usable for linkage (no recompute)

From [src/stress_results_block.py](../../src/stress_results_block.py):

| Block 3.2 path | Use in Block 3.3 |
| --- | --- |
| `synthetic_scenarios[].scenario_id` | Join key |
| `synthetic_scenarios[].portfolio_loss_pct` | Cross-check |
| `synthetic_scenarios[].loss_contribution.pnl_by_asset_pct` | Primary hurt/helped input |
| `synthetic_scenarios[].loss_contribution.assets_hurt` | Top-3 hurt only; v1 needs **all** negatives from full map |
| `synthetic_scenarios[].assets_helped` | Only on worst synthetic row — **do not** rely on this for per-risk rows |
| `envelope.worst_synthetic` | Informational; not the v1 per-risk selector |

#### G. Core MVP diagnostic boundary

| Check | Evidence |
| --- | --- |
| `loss_gate_mode=diagnostic` on portfolio-first path | [run_report.py](../../run_report.py); Block 3.2 live audit |
| Block 3.3 must omit mandate fields | Session 07 contract test (mirror Block 3.2 pattern) |
| No pass/fail on hedge effectiveness | Product brief; not a suitability checker |

#### H. Gap list (Session 00 → implementation backlog)

| ID | Gap | Priority | Session |
| --- | --- | --- | --- |
| G1 | No `hedge_gap_analysis_v1` on `stress_report.json` | P0 | 02–05 |
| G2 | Stress Lab spec numbering conflicts with product 3.3 | P0 | 01 |
| G3 | No contribution-based offset_coverage_ratio | P0 | 03 |
| G4 | Legacy hedge block `not_applicable` without taxonomy labels | P1 | 03 (v1 fixes product gap) |
| G5 | Block 3.2 `assets_helped` only on worst synthetic | P1 | 03 (read `pnl_by_asset_pct` per scenario) |
| G6 | No `main_hedge_gap` / per-risk English diagnosis | P1 | 04 |
| G7 | `TESTING.md` / `live_core_e2e` lack `hedge_gap_analysis_v1` | P2 | 01, 07 |
| G8 | Commentary references legacy hedge gap only | P2 | 06 |
| G9 | `recession_severe` not in seven risk types | P2 | 01 DECISIONS (document exclusion) |

## Decision Log

- Decision: Deliver Block 3.3 as **`hedge_gap_analysis_v1`** on `stress_report.json`, not on `portfolio_xray.json`.
  Rationale: Stress Lab product boundary; follows Block 3.2 placement.
  Date/Author: 2026-05-27 / Session 00.

- Decision: **Keep legacy `hedge_gap_analysis`** unchanged; do not remove or repurpose in this wave.
  Rationale: `stress_conclusions.hedge_gap_status`, snapshot, and [tests/test_stress_hedge_gap_contract.py](../../tests/test_stress_hedge_gap_contract.py) depend on v2 contract.
  Date/Author: 2026-05-27 / Session 00.

- Decision: Hedge effectiveness is determined by **signed scenario asset contribution**, not taxonomy `risk_role`.
  Rationale: Product brief explicitly forbids pre-labeling hedge assets.
  Date/Author: 2026-05-27 / Session 00.

- Decision: Seven product risk types map 1:1 to seven synthetic scenarios; **`recession_severe` excluded** from Block 3.3 v1 rows.
  Rationale: Product brief lists seven protection areas; `recession_severe` is a composite calibrated scenario without a separate product risk type in v1.
  Date/Author: 2026-05-27 / Session 00.

- Decision: Renumber Stress Lab Core MVP docs to **3.1 Scenario Library, 3.2 Stress Results, 3.3 Hedge Gap, 3.4 Scorecard**; move What Happens If simulator and Crisis Replay to **advanced/deferred**.
  Rationale: User confirmation; simulator is not Core MVP; hedge gap directly follows stress results.
  Date/Author: 2026-05-27 / Session 00.

- Decision: Wire `attach_hedge_gap_analysis_v1` **after** `attach_stress_results_v1` in `run_stress` and `run_report.py`.
  Rationale: v1 reads Block 3.2 product rows when available; rebuild order matches Block 3.2 pattern.
  Date/Author: 2026-05-27 / Session 00.

- Decision: Historical episodes are **out of scope** for v1 `by_risk_type[]` rows (`linked_episode: null`, `scenario_type: synthetic` only).
  Rationale: No canonical episode→risk-type map in product brief; avoid inventing mappings.
  Date/Author: 2026-05-27 / Session 00.

## Outcomes & Retrospective

**Session 00 (2026-05-27):** ExecPlan created with full field audit (sections A–H above). Registered **Active** in [docs/exec_plans/README.md](README.md). No application code. Next: Session 01 product contract and Stress Lab doc renumbering.

**Session 01 (2026-05-27):** Documentation contract baseline for Block 3.3 Hedge Gap Analysis. Specs define `hedge_gap_analysis_v1` as the Core MVP product block on `stress_report.json`; Stress Lab layer renumbered (3.3 Hedge Gap, 3.4 Scorecard; simulator/crisis replay deferred); legacy `hedge_gap_analysis` documented separately. PRODUCT §4.3.3, SPEC/OUTPUTS/TESTING/DECISIONS (`DEC-2026-05-27-002`), CHANGELOG synchronized. No application code. Next: Session 02 builder scaffold.

**Session 02 (2026-05-27):** Builder scaffold delivered. `src/hedge_gap_analysis_block.py` with `BLOCK_3_3_RISK_SCENARIO_MAP` (7 entries), `build_hedge_gap_analysis_v1`, `empty_hedge_gap_analysis_v1`, `attach_hedge_gap_analysis_v1` stub; seven unavailable placeholder rows per map key. `tests/test_hedge_gap_analysis_v1_contract.py` — structure/registry/attach/empty tests. No `src.stress` import; not wired into `run_stress` until Session 05. Next: Session 03 per-risk hurt/helped + `offset_coverage_ratio`.

**Session 03 (2026-05-27):** Per-risk rows implemented: hurt/helped split from `pnl_by_asset_pct` (Block 3.2 preferred, Block 3.1 fallback), `gross_loss_from_assets_hurt`, `positive_contribution_from_assets_helped`, `offset_coverage_ratio`, `loss_concentration.top3_share_of_gross_loss`, `data_availability` reason codes. Summary still empty (Session 04). Contract tests for ratio math, sorting, concentration, edge cases. Not wired into `run_stress` until Session 05. Next: Session 04 summary + `diagnosis_summary_en`.

**Session 04 (2026-05-27):** Summary object: `main_hedge_gap` (compact weakest row), `weakest_protection_area`, `strongest_protection_area` (when ≥2 ratios), `data_quality_warnings`, portfolio `diagnosis_summary_en`. Per-risk English templates when `data_availability=available`. Contract tests for selection, tie-break, narratives, warnings. Not wired into `run_stress` until Session 05. Next: Session 05 wire-up.

**Session 05 (2026-05-27):** Wired Block 3.3 onto `stress_report.json`: `attach_hedge_gap_analysis_v1` rebuilds in-place after `attach_stress_results_v1`; `run_stress`, `_empty_report`, `run_report.py` (post-enrichment), and `run_optimization.py` (pre-export) emit `hedge_gap_analysis_v1`. Four wiring tests in `tests/test_hedge_gap_analysis_v1_contract.py`. Legacy `hedge_gap_analysis` unchanged. Next: Session 06 commentary/snapshot mirror.
**Session 06 (2026-05-27):** Minimal downstream integration: `portfolio_commentary.py` pointer to Block 3.3; compact mirror on `snapshot_10y.json` for `stress_suite_results`; `live_core_e2e` updated to assert `hedge_gap_analysis_v1` presence on subject artifacts. Next: Session 07 tests and CHANGELOG.
**Session 07 (2026-05-27):** Contract tests and regression bundle: `tests/test_hedge_gap_analysis_v1_contract.py` extended; diagnostic-mode stress bundle in TESTING.md; CHANGELOG entry for Block 3.3. Plan ready for Session 08 live validation.
**Session 08 (2026-05-27):** Live portfolio-first diagnosis run (`python run_portfolio_review.py --skip-candidates`) refreshed `Main portfolio/analysis_subject/stress_report.json` with `hedge_gap_analysis_v1` present, seven risk-type rows, numeric `offset_coverage_ratio` where contributions are available, summary fields populated, and `loss_gate_mode=diagnostic`. Closure pytest bundle (Block 3.3 + Stress Lab tests) passed; acceptance audit recorded in `docs/audits/2026-05-27_block_3_3_hedge_gap_acceptance_audit.md`. Plan marked **Completed**.

## Context and Orientation

Portfolio MRI Core MVP flow: Input → Portfolio X-Ray → **Stress Test Lab** → Problem Classification → candidates.

**Core MVP Stress Lab product blocks (target numbering after Session 01):**

```text
3.1 Scenario Library
3.2 Stress Results          (stress_results_v1 — Done)
3.3 Hedge Gap Analysis      (hedge_gap_analysis_v1 — this plan)
3.4 Current Portfolio Stress Scorecard
```

**Deferred / advanced (not Core MVP product blocks):** What Happens If custom shock simulator API; Crisis Replay month-by-month paths (code remains in `src/stress.py` / `historical_episode_paths`).

Stress pipeline today:

```text
monthly returns + weekly betas + config
  -> run_stress (src/stress.py)
       -> scenario_results[] (8 synthetic)
       -> historical_results[] (5)
       -> stress_scorecard_v1, stress_conclusions, hedge_gap_analysis (legacy)
       -> attach_stress_results_v1
  -> run_report.py (full path)
       -> enrich_historical_results_with_factor_attribution
       -> attach_stress_results_v1 (refresh)
       -> [planned] attach_hedge_gap_analysis_v1
```

Primary artifact: `{output_dir_final}/analysis_subject/stress_report.json`.

**Loss gate mode:** `diagnostic` (Core MVP) — Block 3.3 reports offset facts and hedge-gap interpretation only.

## Plan of Work

### Session 01 — Docs only

Renumber [stress_lab_layer_spec.md](../specs/stress_lab_layer_spec.md). Extend [hedge_gap_analysis_spec.md](../specs/hedge_gap_analysis_spec.md) with v1 contract. Add `hedge_gap_analysis_v1` to [stress_testing_spec.md](../specs/stress_testing_spec.md). Add PRODUCT §4.3.3. Touch SPEC.md, OUTPUTS.md, TESTING.md, DECISIONS.md, CHANGELOG.md (Session 01 entry). Run `python scripts/verify_docs.py`.

### Session 02 — Block 3.3 builder module

Create `src/hedge_gap_analysis_block.py` with `build_hedge_gap_analysis_v1`, `empty_hedge_gap_analysis_v1`, `attach_hedge_gap_analysis_v1` stub; no circular import from `src.stress`.

### Session 03 — Per-risk rows + ratio

Implement hurt/helped extraction and `offset_coverage_ratio` / `loss_concentration` for seven risk types.

### Session 04 — Summary + narratives

Implement `summary` object and English templates.

### Session 05 — Wire-up

Call `attach_hedge_gap_analysis_v1` after `attach_stress_results_v1` in `run_stress`, `_empty_report`, `run_report.py`, `run_optimization.py`.

### Session 06 — Downstream (minimal)

`_append_hedge_gap_analysis_v1_section` in `portfolio_commentary.py`; snapshot compact mirror; `live_core_e2e` require key.

### Session 07 — Tests

New `tests/test_hedge_gap_analysis_v1_contract.py`; extend diagnostic mode; TESTING.md bundle; CHANGELOG.

### Session 08 — Live proof

`python run_portfolio_review.py --skip-candidates`; write acceptance audit `docs/audits/2026-05-27_block_3_3_hedge_gap_acceptance_audit.md`; mark plan **Completed**.

## Concrete Steps

Session 00 (complete):

    # From repository root — documentation only
    python -c "from src.scenario_library import SYNTHETIC_SCENARIO_IDS; print(list(SYNTHETIC_SCENARIO_IDS))"

Expected: eight synthetic IDs including `recession_severe`.

Session 01 (next):

    python scripts/verify_docs.py

Session 07 (target):

    python -m pytest tests/test_hedge_gap_analysis_v1_contract.py tests/test_stress_results_block_contract.py tests/test_stress_scenario_coverage_contract.py tests/test_stress_diagnostic_mode.py tests/test_stress_hedge_gap_contract.py tests/test_stress_downstream_integration.py -q

Session 08 (target):

    python run_portfolio_review.py --skip-candidates

## Validation and Acceptance

**Session 00 acceptance:** This ExecPlan exists at `docs/exec_plans/2026-05-27_block_3_3_hedge_gap_analysis_plan.md`; field audit in `Surprises & Discoveries`; README **Active** pointer updated. No pytest required.

**Final acceptance (Session 08):** Subject `stress_report.json` contains `hedge_gap_analysis_v1` with seven risk rows (or explicit unavailable reasons), correct `offset_coverage_ratio` math, `summary.main_hedge_gap` when data supports it, linkage to `stress_results_v1`, diagnostic mode without mandate fields on v1, legacy `hedge_gap_analysis` still present; closure pytest bundle green.

## Idempotence and Recovery

Sessions 01–08 are additive. Re-running `run_portfolio_review.py` overwrites `stress_report.json`. No migrations. If Session 05 wiring breaks tests, revert attach call and keep builder tested in isolation.

## Artifacts and Notes

Example product narrative (template target — Session 04; numbers illustrative):

    The main hedge gap is inflation/rates shock, not normal equity volatility. The portfolio has
    some protection in equity crash scenarios, but remains vulnerable when equities and bonds
    decline together. In the inflation_stagflation scenario, assets that helped offset only a small
    part of losses from assets that hurt.

Example ratio (Session 03):

    gross_loss_from_assets_hurt = 0.12
    positive_contribution_from_assets_helped = 0.025
    offset_coverage_ratio = 0.025 / 0.12 ≈ 0.208 (21% in prose)

## Interfaces and Dependencies

Planned module: `src/hedge_gap_analysis_block.py` (Session 02).

    BLOCK_3_3_VERSION = "hedge_gap_analysis_v1"

    BLOCK_3_3_RISK_SCENARIO_MAP: dict[str, str]  # risk_type -> scenario_id (7 entries)

    def build_hedge_gap_analysis_v1(
        *,
        stress_results_v1: dict[str, Any],
        scenario_results: list[dict[str, Any]],
        loss_gate_mode: str,
    ) -> dict[str, Any]:
        ...

    def attach_hedge_gap_analysis_v1(stress_report: dict[str, Any]) -> None:
        ...

Imports: `SYNTHETIC_SCENARIO_IDS`, `SCENARIO_LIBRARY_VERSION` from `src.scenario_library`; read `stress_results_v1` from same `stress_report` dict. No import from `src.stress` (mirror Block 3.2 isolation).

Wire points:

- [src/stress.py](../../src/stress.py) — after `attach_stress_results_v1` in `run_stress` and `_empty_report`
- [run_report.py](../../run_report.py) — after `attach_stress_results_v1` refresh
- [run_optimization.py](../../run_optimization.py) — before stress export if applicable
