# Core MVP Historical Stress Replay — Acceptance Audit (Session 07)

Date: 2026-05-28

Purpose: Close [Core MVP Historical Stress Replay ExecPlan](../exec_plans/2026-05-28_core_mvp_historical_stress_replay_plan.md) **Session 07** and record whether the direct-history-only replay contract is accepted on the portfolio-first diagnosis path.

Related:

- Normative spec: [core_mvp_historical_stress_replay_spec.md](../specs/core_mvp_historical_stress_replay_spec.md)
- Stress Lab layer: [stress_lab_layer_spec.md](../specs/stress_lab_layer_spec.md) §3.1.1, §3.2
- Decision: DEC-2026-05-28-001 (`DECISIONS.md`)
- Implementation: `src/core_mvp_historical_stress_replay.py`, `src/stress_results_block.py`, `run_report.py`
- Live gate: `scripts/verify_core_mvp_historical_stress_replay.py`

---

## 1. Executive Summary

| Question | Verdict |
| --- | --- |
| Is `historical_stress_replay_v1` on live portfolio-first diagnosis? | **Yes** — `run_portfolio_review.py --skip-candidates` refreshed `Main portfolio/analysis_subject/stress_report.json`. |
| Is policy `direct_history_only` with five canonical episodes? | **Yes** — dotcom, 2008, 2020, 2022, banking_2023 in registry order. |
| Are proxy product fields absent? | **Yes** — no `used_proxies` / `proxy_coverage_weight_pct` on replay or Block 3.2 historical rows. |
| Does Block 3.2 honor replay coverage for portfolio metrics? | **Yes** — loss/DD only when `portfolio_level_result_available`; dotcom/2008 cleared despite legacy paths. |
| Are English `user_note` / `diagnosis_summary_en` present on all episodes? | **Yes** — 5/5 replay episodes; partial/unavailable narratives in `data_trust_summary`. |
| Is the full ExecPlan accepted (Sessions 01–07)? | **Yes — 7/7** sessions complete (see §3). |

**Bottom line:** Core MVP historical stress replay is **complete**. Operators read honest per-episode coverage from `historical_stress_replay_v1` and merged Block 3.2 `historical_episodes[]` on subject `stress_report.json`. Early episodes (dotcom, 2008) correctly show **unavailable** full-book replay when the aligned monthly panel does not cover the episode window (2014+ book on this run), rather than implying full-portfolio precision.

---

## 2. Session Rollup (01–07)

| Session | Objective | Status | Primary evidence |
| --- | --- | --- | --- |
| 01 | Spec + config helpers; proxy map Advanced/Legacy | **Done** | `core_mvp_historical_stress_replay_spec.md`; `test_core_mvp_historical_stress_replay_config.py` |
| 02 | Replay engine cases A–D | **Done** | `build_historical_stress_replay_v1` |
| 03 | `run_report` wiring + Block 3.2 merge | **Done** | `test_stress_results_historical_replay_contract.py` |
| 04 | `user_note` / `diagnosis_summary_en` templates | **Done** | `format_episode_diagnosis_summary_en` |
| 05 | Contract tests A–D + merge | **Done** | `test_core_mvp_historical_stress_replay_contract.py` |
| 06 | Docs sync | **Done** | DEC-2026-05-28-001; layer + OUTPUTS + TESTING |
| 07 | Live proof + closure | **Done** | This document; live run §5 |

---

## 3. ExecPlan Acceptance Criteria

| # | Criterion | Result | Evidence |
| --- | --- | --- | --- |
| 1 | `historical_stress_replay_v1` on diagnostic subject run | **PASS** | Live `--skip-candidates`; §5.1 |
| 2 | `policy: direct_history_only`; five episodes canonical order | **PASS** | §5.1 |
| 3 | No forbidden proxy keys on replay / Block 3.2 rows | **PASS** | §5.2 |
| 4 | Portfolio metrics only when `portfolio_level_result_available` | **PASS** | §5.3 |
| 5 | Block 3.2 merges replay fields; non-full replay clears loss/DD | **PASS** | §5.3 |
| 6 | English copy on all episodes | **PASS** | §5.4 |
| 7 | `data_trust_summary` cites partial/unavailable replay | **PASS** | §5.5 |
| 8 | Closure pytest bundle | **PASS** | **35 passed** (Core MVP replay bundle) |
| 9 | Live gate script | **PASS** | `scripts/verify_core_mvp_historical_stress_replay.py` exit **0** |

**Core MVP Historical Stress Replay: ACCEPTED.**

---

## 4. Fixture-Locked Behavior (pytest)

Source: `tests/test_core_mvp_historical_stress_replay_config.py`, `tests/test_core_mvp_historical_stress_replay.py`, `tests/test_core_mvp_historical_stress_replay_contract.py`, `tests/test_stress_results_historical_replay_contract.py`.

| Check | Expected |
| --- | --- |
| Cases A–D | full / partial / unavailable replay; no proxy substitution |
| Block 3.2 merge | Replay fields copied; legacy `historical_results` PnL does not restore metrics when partial |
| Config | `min_coverage_ratio` 0.45; module does not import proxy fallback |

---

## 5. Live Verification (Session 07, root `config.yml`)

Commands (repository root):

```bash
python run_portfolio_review.py --skip-candidates
python -m pytest tests/test_core_mvp_historical_stress_replay_config.py tests/test_core_mvp_historical_stress_replay.py tests/test_core_mvp_historical_stress_replay_contract.py tests/test_stress_results_historical_replay_contract.py -q
python scripts/verify_core_mvp_historical_stress_replay.py
python scripts/verify_docs.py
```

| Check | Result |
| --- | --- |
| Diagnosis-only review | Exit **0**; `product_diagnosis_only`; `analysis_subject` materialized |
| Closure pytest bundle | **35 passed** |
| Live gate script | **OK** |
| `verify_docs.py` | **OK** |

Artifact: `Main portfolio/analysis_subject/stress_report.json` (refreshed **2026-05-28**).

Monthly panel on this run: **2014-06 → 2026-04** (8-ticker Core MVP demo book). Episode windows before 2014 have no aligned monthly cells, so dotcom and 2008 replay as **unavailable** for all risk positions — expected honest behavior, not a proxy fill.

### 5.1 Top-level replay block (`historical_stress_replay_v1`)

| Field | Observed |
| --- | --- |
| `version` | `core_mvp_historical_stress_replay_v1` |
| `policy` | `direct_history_only` |
| `historical_stress_replay_v1_error` | absent |
| Episode count | **5** (canonical order) |

### 5.2 Per-episode replay (`episodes[]`)

| scenario_id | replay_status | direct % | unavail % | portfolio_level | portfolio_loss_pct | drawdown_pct | unavailable (sample) |
| --- | --- | ---: | ---: | --- | ---: | ---: | --- |
| dotcom | unavailable | 0.0 | 100.0 | false | — | — | all 8 risk tickers |
| 2008 | unavailable | 0.0 | 100.0 | false | — | — | all 8 risk tickers |
| 2020 | full_replay | 100.0 | 0.0 | true | -0.0078 | -0.0526 | — |
| 2022 | full_replay | 100.0 | 0.0 | true | -0.1629 | -0.1976 | — |
| banking_2023 | full_replay | 100.0 | 0.0 | true | 0.0072 | -0.0103 | — |

Forbidden keys (`used_proxies`, `proxy_coverage_weight_pct`, …): **absent** on all replay rows.

### 5.3 Block 3.2 merge (`stress_results_v1.historical_episodes[]`)

| episode | replay_status | availability | portfolio_loss_pct | Matches replay loss? |
| --- | --- | --- | ---: | --- |
| dotcom | unavailable | unavailable | — | cleared (replay unavailable) |
| 2008 | unavailable | unavailable | — | cleared |
| 2020 | full_replay | available | -0.0078 | yes |
| 2022 | full_replay | available | -0.1629 | yes |
| banking_2023 | full_replay | available | 0.0072 | yes |

Legacy `historical_results` for dotcom/2008: `pnl_real_episode` and `max_dd` **null** (`insufficient_data`) — aligned with replay, not contradictory full-book loss.

### 5.4 English copy

| episode | `user_note` | `diagnosis_summary_en` |
| --- | --- | --- |
| dotcom | yes | yes (coverage + unavailable narrative) |
| 2008 | yes | yes |
| 2020 | yes | yes (includes return/drawdown on full replay) |
| 2022 | yes | yes |
| banking_2023 | yes | yes |

### 5.5 Trust summary

`data_trust_summary.user_summary_lines` includes **Historical replay (dotcom)** and **Historical replay (2008)** lines sourced from replay `diagnosis_summary_en` (partial/unavailable episodes).

`loss_gate_mode` on report and Block 3.2: **diagnostic**. Mandate keys absent on Block 3.2 historical product rows.

---

## 6. Out of Scope / Deferred

| Item | Status |
| --- | --- |
| Per-asset proxy waterfall on Core MVP Stress Lab UI | Advanced/Legacy only (`historical_stress_fallback`, `historical_stress_proxy_map.yml`) |
| Replacing primary `run_stress` `historical_results` with replay engine | Deferred (DEC-2026-05-20-001 realized path unchanged) |
| Longer monthly history download in lightweight subject profile | Operator may use full report path for deeper episode coverage; replay reflects aligned panel honestly |

---

## 7. Operator Checklist

1. Run diagnosis: `python run_portfolio_review.py --skip-candidates`
2. Open `{output_dir_final}/analysis_subject/stress_report.json` → `historical_stress_replay_v1` and `stress_results_v1.historical_episodes`
3. Read `replay_status`, coverage %, and `diagnosis_summary_en` per episode; do not treat partial/unavailable rows as full-book replay
4. Check `data_trust_summary.user_summary_lines` for historical replay warnings
5. Regression: TESTING.md Core MVP historical replay bundle; live gate `python scripts/verify_core_mvp_historical_stress_replay.py`

---

**Closure:** ExecPlan [2026-05-28_core_mvp_historical_stress_replay_plan.md](../exec_plans/2026-05-28_core_mvp_historical_stress_replay_plan.md) marked **Completed** 2026-05-28.
