# Current Portfolio Stress Scorecard Specification

Status: diagnostic-only contract (Core MVP Block 3.4).

Stress Lab exposes two scorecard blocks on `stress_report.json`:

| Block | JSON key | Audience |
| --- | --- | --- |
| **Block 3.4 Core MVP** | `current_portfolio_stress_scorecard_v1` | Product-facing executive stress diagnosis for the **current** portfolio |
| **Legacy** | `stress_scorecard_v1` | Backward compatibility (mandate-mode semantics, `DIAG_*`, `pass` / `loss_ok`) |

Core MVP operators and new integrations must read **`current_portfolio_stress_scorecard_v1`** first.
Use `stress_scorecard_v1` only when `legacy_fallback_used` is `true` or when an explicit legacy
mandate path requires it.

Phase 2 institutional upgrade ruleset: **`current_portfolio_stress_scorecard_rules_v1_1`** (frozen
Session 01, 2026-05-29). MVP adapter shipped 2026-05-27; v1.1 fields roll out Sessions 02–11 per
[institutional upgrade plan](../exec_plans/2026-05-29_block_3_4_current_portfolio_stress_scorecard_institutional_upgrade_plan.md).

Baseline evidence: [Session 00 audit](../audits/2026-05-29_block_3_4_session_00_baseline_audit.md).

---

## Purpose

Block 3.4 is the **executive stress diagnosis layer** inside Stress Test Lab. It answers ten
product questions by **reading** Blocks 3.1–3.3 (and optional 2.4/2.6 context at attach time)—never
by re-running stress:

1. Where does the portfolio lose the most (worst synthetic loss vs worst historical episode)?
2. Which synthetic scenario is worst for the portfolio?
3. Which historical episode is worst for the portfolio?
4. Which assets hurt the most and which helped (loss contribution)?
5. Which assets concentrate risk under stress (RC_vol on the worst synthetic row)?
6. Which factor channels explain stress losses?
7. How much did helped assets offset losses from hurt assets (offset coverage)?
8. What is the main hedge gap (weakest protection area)?
9. What data is missing or weak for confident interpretation?
10. What compact diagnosis and downstream hooks should Problem Classification, Candidate Comparison,
   and AI Commentary consume?

### Hard boundaries

- **No** second stress engine, scenario recomputation, or mutation of `stress_results_v1` /
  `hedge_gap_analysis_v1`.
- **No** optimizer, candidate factory, or weight changes.
- **No** client mandate pass/fail, suitability gates, or `DIAG_*` language **inside**
  `current_portfolio_stress_scorecard_v1`.
- **No** legacy `hedge_gap_analysis` when `hedge_gap_analysis_v1` exists.
- **No** import of Block 3.4 from Block 2.4 / 2.6 (bridges are attach-time optional inputs only).
- **No** product wording such as “passes normally”, “passed stress”, or mandate-style pass/fail.

### Mandate boundary (summarize-only)

When `loss_gate_mode="mandate"`, Block 3.4 may **reference** mandate outcomes only if they already
exist on a **separate** legacy layer (`stress_scorecard_v1` under mandate semantics). Core MVP Block
3.4 must **not** compute or emit internal mandate pass/fail, `loss_ok`, `max_dd_limit`, or
`fail_reason_code`. Set `legacy_fallback_used=true` when downstream consumers had to read legacy
scorecard for mandate rollup (Session 02+).

### Product language (required)

| Use | Do not use |
| --- | --- |
| `relatively_resilient_scenarios` | “passes normally”, “passed scenario” |
| `less_damaging_scenarios` | “acceptable under stress” (mandate-adjacent) |
| `protection_status` (from Block 3.3 when cited) | “pass” / “fail” inside Block 3.4 |
| Loss severity, offset coverage, drawdown depth | Mandate-style pass/fail labels |

---

## Placement and wiring

- Artifact: `stress_report.json` (Stress Test Lab — **not** `portfolio_xray.json`).
- Built **after** `attach_stress_results_v1` and `attach_hedge_gap_analysis_v1` on the same report dict.
- `loss_gate_mode` copied from top-level report (`diagnostic` for Core MVP portfolio-first runs).

Module: `src/current_portfolio_stress_scorecard_block.py`

- `BLOCK_3_4_VERSION = "current_portfolio_stress_scorecard_v1"`
- `RULESET_VERSION = "current_portfolio_stress_scorecard_rules_v1_1"` (implementation Session 02+)

Wiring: `src/stress.py` (`run_stress`, `_empty_report`), `run_report.py`, `run_optimization.py`,
portfolio-first materialization paths.

Optional attach (Session 07+): `attach_current_portfolio_stress_scorecard_v1(..., portfolio_xray=...)`
may pass Block 2.4 / 2.6 dicts for `pre_stress_confirmation_summary` without circular imports.

---

## Evidence inputs (read-only)

| Source block | JSON key | What Block 3.4 reads |
| --- | --- | --- |
| 3.1 | `scenario_results[]`, `historical_results[]` | Indirectly via 3.2 rows only (no direct re-walk in v1.1) |
| 3.2 | `stress_results_v1` | `envelope.worst_synthetic`, `envelope.worst_historical`, `synthetic_scenarios[]`, `historical_episodes[]`, `scenario_library`, conclusions warnings |
| 3.3 | `hedge_gap_analysis_v1` | `summary.main_hedge_gap`, `by_risk_type[]`, `protection_profile`, offset metrics |
| Trust | `data_trust_summary`, `stress_conclusions` | `user_summary_lines`, `data_quality_warnings`, `helped_factors_worst_scenario` |
| Legacy (fallback only) | `stress_scorecard_v1` | Never for Core MVP fields; may set `legacy_fallback_used` when consumers require it |

Do **not** use Block 3.2 global `assets_helped` on the worst synthetic row as the only helped list
when per-scenario maps exist on envelope / synthetic rows.

### Worst-scenario rules (frozen — do not mix metrics)

Ownership: Block 3.2 envelope. Block 3.4 **copies** selectors; it does not recompute.

| Selector | Rule | Block 3.4 field |
| --- | --- | --- |
| Worst synthetic | Minimum synthetic `portfolio_pnl_pct` (same as `portfolio_loss_pct` on envelope) | `worst_synthetic_scenario` |
| Worst historical | Minimum historical `max_dd` (drawdown), **not** synthetic PnL | `worst_historical_scenario` |

Never rank historical episodes by synthetic PnL alone for “worst historical”. Never rank synthetic
scenarios by historical drawdown.

---

## Top-level block shape

`stress_report.json.current_portfolio_stress_scorecard_v1`:

### Product metadata (v1.1 — Session 02+)

| Field | Type / values | Derive rule |
| --- | --- | --- |
| `version` | `current_portfolio_stress_scorecard_v1` | Constant |
| `block` | `"3.4"` | Constant |
| `ruleset_version` | `current_portfolio_stress_scorecard_rules_v1_1` | Constant until scoring/diagnosis logic changes |
| `block_status` | `ok` \| `partial` \| `unavailable` | See § Block status |
| `scorecard_scope` | `current_portfolio_diagnostic` | Constant for Core MVP |
| `source_blocks_used` | string[] | Subset of `stress_results_v1`, `hedge_gap_analysis_v1`, `stress_conclusions`, `data_trust_summary`; add `portfolio_xray` only when 2.4/2.6 bridges run |
| `stress_coverage` | object | See § Stress coverage |
| `legacy_fallback_used` | boolean | `true` iff any downstream-facing field was satisfied from `stress_scorecard_v1` (default `false`) |
| `limitations` | string[] | English limitation lines (RC unavailable, partial historical, etc.) |
| `loss_gate_mode` | `diagnostic` \| `mandate` | Copy from report |

#### `block_status`

| Value | Rule |
| --- | --- |
| `ok` | Worst synthetic **and** worst historical available; hedge gap v1 present with `block_status` ∈ `{ok, partial}`; no fatal trust block |
| `partial` | Scorecard built but any of: hedge gap missing/unavailable, partial historical coverage, RC unavailable, or non-empty `data_quality_warnings` |
| `unavailable` | Empty builder / missing `stress_results_v1` envelope |

`block_status` is derived from stress evidence (3.1–3.3) **only**. Missing Block 2.4 / 2.6 bridges
must **not** downgrade `block_status` below what stress data supports.

#### `stress_coverage`

| Field | Rule |
| --- | --- |
| `n_synthetic_available` | Count of `stress_results_v1.synthetic_scenarios[]` with `availability == available` |
| `n_synthetic_total` | Length of synthetic list or scenario library synthetic count |
| `n_historical_available` | Count of historical episodes with usable `max_dd` |
| `n_historical_total` | Length of historical episode list |
| `fraction_synthetic_available` | `n_synthetic_available / n_synthetic_total` when total > 0, else `null` |
| `fraction_historical_available` | Same for historical |

### Worst scenario summaries (MVP — implemented)

| Field | Rule |
| --- | --- |
| `scenario_library` | Copy from `stress_results_v1.scenario_library` or `hedge_gap_analysis_v1.scenario_library` |
| `worst_synthetic_scenario` | `{availability, scenario_id, portfolio_loss_pct}` from `envelope.worst_synthetic` |
| `worst_historical_scenario` | `{availability, episode, portfolio_loss_pct, drawdown_pct}` from `envelope.worst_historical` |
| `portfolio_loss_summary` | Synthetic PnL + historical `pnl_real_episode` |
| `historical_drawdown_summary` | `max_dd` from worst historical |

### Loss and risk contribution (MVP + v1.1 aliases)

| Field | Session | Rule |
| --- | --- | --- |
| `top_loss_contributors` | MVP | Worst synthetic / historical `top3_loss_assets` |
| `loss_contribution_summary` | 04 | Same content as `top_loss_contributors` plus `loss_concentration_top3_share` when computable |
| `top_risk_contributors` | MVP | RC_vol Top1/Top3 from worst synthetic row in `synthetic_scenarios[]` |
| `risk_contribution_summary` | 04 | Same as `top_risk_contributors` plus `rc_overlap_with_loss_contributors` flag |

Loss contribution and RC_vol are **separate** concepts: PnL hurt/help vs covariance-based risk share
under the worst synthetic scenario.

### Factor, assets, hedge gap (MVP + v1.1)

| Field | Session | Rule |
| --- | --- | --- |
| `factor_stress_attribution_summary` | MVP | `top_factor_drivers` from worst synthetic; `helped_factors` from `stress_conclusions` |
| `assets_helped_hurt_summary` | MVP | Worst synthetic helped/hurt; `hedge_gap_main_area` from main gap row |
| `offset_coverage_summary` | MVP | Main gap offset ratio and contrib terms from Block 3.3 |
| `main_hedge_gap` | MVP | Weakest/strongest area + nested `main_hedge_gap` from Block 3.3 summary |
| `hedge_gap_summary` | 05 | Compact: `main_hedge_gap_scenario_id`, `main_hedge_gap_risk_type`, `offset_coverage_ratio`, `protection_profile`, `hedge_gap_block_status`, `hedge_gap_ruleset_version` |
| `hedge_gap_ruleset_version` | MVP (optional meta) | Copy from `hedge_gap_analysis_v1.ruleset_version` when present |
| `hedge_gap_block_status` | MVP (optional meta) | Copy from `hedge_gap_analysis_v1.block_status` when present |
| `protection_profile` | MVP (optional meta) | Copy from Block 3.3 summary when present |

`hedge_gap_summary.main_hedge_gap_scenario_id` **must** equal
`hedge_gap_analysis_v1.summary.main_hedge_gap.linked_scenario_id` when main gap exists.

### Resilience language (v1.1 — Session 06)

| Field | Rule |
| --- | --- |
| `relatively_resilient_scenarios` | Up to **3** synthetic scenarios with `portfolio_pnl_pct >= 0`, sorted by `portfolio_pnl_pct` descending; empty list if none |
| `less_damaging_scenarios` | Up to **3** synthetic scenarios with `portfolio_pnl_pct` **strictly greater** than worst synthetic `portfolio_loss_pct`, sorted descending; excludes ids already listed as relatively resilient |

Each entry: `{scenario_id, portfolio_pnl_pct, availability: "available"}`.

### Stress diagnosis (v1.1 — Session 06)

`stress_diagnosis` object:

| Field | Rule |
| --- | --- |
| `headline` | One-line English executive headline (non-empty when `block_status` ∈ `{ok, partial}`) |
| `diagnosis_summary_en` | Short paragraph; may mirror legacy `diagnosis_summary_en` during alias period |
| `diagnosis_confidence` | `high` \| `medium` \| `low` \| `unavailable` — see below |
| `confidence_reason` | Machine-readable code |
| `confidence_reason_en` | English explanation |
| `key_findings` | Up to 5 bullet strings (worst syn, worst hist, main gap, factor driver, DQ) |

#### `diagnosis_confidence`

| Value | Rule |
| --- | --- |
| `high` | `block_status == ok`; hedge gap v1 `block_status == ok`; `stress_coverage.fraction_synthetic_available >= 0.75`; ≤1 material DQ warning |
| `medium` | `block_status == ok` or `partial` with worst syn+hist available but partial historical fraction &lt; 0.75 or 2–4 DQ warnings |
| `low` | `block_status == partial` with missing RC or hedge gap partial/unavailable, or &gt;4 DQ warnings |
| `unavailable` | `block_status == unavailable` or both worst selectors unavailable |

Weak coverage or data quality must **not** be narrated at `high` confidence.

Legacy top-level `diagnosis_summary_en` (MVP) remains for one release as an alias; prefer
`stress_diagnosis.diagnosis_summary_en` for new consumers.

### Pre-stress confirmation (v1.1 — Session 07)

`pre_stress_confirmation_summary` — optional bridges; scorecard **always runs** if stress blocks exist.

| Sub-block | When present | When absent |
| --- | --- | --- |
| `hidden_exposure` | Block 2.4 dict passed at attach | `{status: "not_applicable", reason_en: "block_2_4_not_attached"}` |
| `weakness_map` | Block 2.6 dict passed at attach | `{status: "not_applicable", reason_en: "block_2_6_not_attached"}` |
| `aggregate_confirmation` | Both bridges evaluated | `unavailable` if neither attached |

Each sub-block may copy confirmation rows from `hedge_gap_analysis_v1.hidden_exposure_confirmation` /
`weakness_map_confirmation` when already populated by Portfolio X-Ray wire-time bridges; do not
recompute offset math in Block 3.4.

Statuses: `confirmed` \| `partially_confirmed` \| `not_confirmed` \| `preliminary` \| `unavailable` \|
`not_applicable`.

### Downstream hooks (v1.1 — Sessions 08–10)

| Field | Session | Purpose |
| --- | --- | --- |
| `problem_classification_signals` | 08 | Compact machine hints: `stress_severity`, `main_gap_risk_type`, `worst_synthetic_id`, `worst_historical_episode`, `diagnosis_confidence` |
| `candidate_comparison_targets` | 09 | Stress slice ids for CC: `worst_synthetic_scenario_id`, `main_hedge_gap_scenario_id`, `compare_offset_coverage` |
| `ai_commentary_context` | 10 | Nested grounding: headline, confidence, forbidden to duplicate legacy `overall_status` |
| `next_decision_uses[]` | 06 | Non-empty when `block_status` ∈ `{ok, partial}`; see § Next decision uses |

### Data quality (MVP)

| Field | Rule |
| --- | --- |
| `data_quality_warnings` | De-duplicated merge: `data_trust_summary.user_summary_lines`, Block 3.3 summary warnings, `stress_conclusions.data_quality_warnings`, historical partial count |

---

## `next_decision_uses[]` (frozen)

Replace singular `next_decision_use`. Array of stable machine tokens (English labels in docs only):

| Token | Consumer |
| --- | --- |
| `problem_classification` | `problem_classification.py` stress problems |
| `candidate_comparison` | Stress sidecar / hedge gap compare targets |
| `ai_commentary` | `ai_commentary_context.json` stress refs |
| `monitoring` | What-changed / stress drift (future) |

Emit all applicable tokens when `block_status` ∈ `{ok, partial}`; emit `[]` when `unavailable`.

---

## Forbidden keys and phrases

### Forbidden keys (anywhere under `current_portfolio_stress_scorecard_v1`)

`pass`, `loss_ok`, `max_dd_limit`, `diagnostic_codes`, `primary_diagnostic_code`,
`fail_reason_code`, `failed_scenario`, `failed_test`, `overall_status` (legacy scorecard field).

Contract tests must walk nested dicts (MVP: `tests/test_current_portfolio_stress_scorecard_v1_contract.py`).

### Forbidden English phrases (Session 06+ scan)

Case-insensitive substring scan on all string values under the block:

- `passes normally`
- `passed stress`
- `failed stress` (mandate-adjacent inside 3.4)

---

## Backward compatibility (one release)

Per decision UPG-34-03:

- Keep all MVP keys listed in § Worst scenario summaries through § Data quality.
- Add v1.1 keys alongside; do not remove MVP keys until Session 13 acceptance.
- `top_loss_contributors` / `loss_contribution_summary` and `top_risk_contributors` /
  `risk_contribution_summary` must remain consistent when both exist.
- Do not remove `stress_scorecard_v1` from the report.

---

## Implementation status matrix

| Area | MVP (2026-05-27) | v1.1 target session |
| --- | --- | --- |
| Adapter over 3.2/3.3 | Shipped | — |
| Product metadata | Partial (`version`, `block` only) | 02 |
| `stress_coverage` | — | 03 (shipped 2026-05-29) |
| Loss/risk summary names + concentration | Partial | 04 (shipped 2026-05-29) |
| `hedge_gap_summary` | Partial (`main_hedge_gap` only) | 05 (shipped 2026-05-29) |
| `stress_diagnosis` + resilience lists | — | 06 (shipped 2026-05-29) |
| `pre_stress_confirmation_summary` | — | 07 (shipped 2026-05-29) |
| Downstream signals | `problem_classification_signals` (08); `candidate_comparison_targets` (09); AI pending | 10 |
| Snapshot / validator / live gates | — | 11 |

---

## Tests

| Bundle | Path |
| --- | --- |
| Block 3.4 contract | `tests/test_current_portfolio_stress_scorecard_v1_contract.py` |
| Downstream (after migration) | `tests/test_problem_classification.py`, `tests/test_ai_commentary_context.py`, `tests/test_stress_downstream_integration.py`, `tests/test_live_core_e2e_validation.py` |

Layer index: [stress_lab_layer_spec.md](stress_lab_layer_spec.md) §3.4.

---

## Related specs

- [stress_testing_spec.md](stress_testing_spec.md) — scenarios and evidence fields
- [hedge_gap_analysis_spec.md](hedge_gap_analysis_spec.md) — Block 3.3 offset coverage
- [problem_classification_spec.md](problem_classification_spec.md) — downstream consumer (Session 08)
- [candidate_comparison_spec.md](candidate_comparison_spec.md) — downstream consumer (Session 09)
- [ai_commentary_grounding_spec.md](ai_commentary_grounding_spec.md) — downstream consumer (Session 10)
