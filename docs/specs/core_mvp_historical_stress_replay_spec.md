# Core MVP Historical Stress Replay

**Status:** Implemented and accepted (Sessions 1–7). Live proof: [acceptance audit](../audits/2026-05-28_core_mvp_historical_stress_replay_acceptance_audit.md); gate `scripts/verify_core_mvp_historical_stress_replay.py`.

**Product boundary:** Core MVP Stress Test Lab historical replay uses **direct historical data only**. It does not substitute missing positions with ETF proxies, factor replay, asset-class proxies, index proxies, or stock-to-stock / stock-to-ETF replacements.

**Not Core MVP (Advanced / Legacy):** Per-asset proxy waterfall in `src/historical_stress_fallback.py` and mappings in `config/historical_stress_proxy_map.yml` are for robust scenario optimization and normalized scenario library consumers only. Those paths must not populate user-facing Core MVP Stress Lab outputs (`historical_stress_replay_v1`, Block 3.2 historical rows on portfolio-first subject runs).

**Related specs:** [stress_lab_layer_spec.md](stress_lab_layer_spec.md) (Block 3), [stress_testing_spec.md](stress_testing_spec.md) (episode registry), [crisis_replay_spec.md](crisis_replay_spec.md) (monthly path export). Primary `run_stress` `historical_results` remain legacy realized portfolio monthly (`DEC-2026-05-20-001`); Core MVP replay is a separate honest-coverage layer.

---

## 1. Policy rules

1. **Direct history first.** A position is included only when its own ticker has usable monthly simple returns in the episode window (see §2).
2. **No proxies in Core MVP.** Do not use ETF proxies, approved proxy replay, factor replay, asset-class proxy, index proxy, company-to-company proxy, or sector ETF proxy for individual stocks.
3. **Full portfolio replay** only when **every** risk position (cash proxy excluded per stress conventions) has usable direct history for that episode.
4. **Partial replay.** If any position is unavailable, do not present portfolio-level loss or drawdown as a full current-portfolio replay. Show unavailable positions, `unavailable_weight_pct`, and `available_history_assets` separately.
5. **Available-history assets** may be listed for positions with direct data, but copy must state this is **not** a full replay of the current portfolio when `replay_status` is not `full_replay`.

---

## 2. Direct history usability

**Episode windows** match `HISTORICAL_EPISODES` in `src/stress.py` (single source; re-exported by `src/core_mvp_historical_stress_replay.py`).

| `scenario_id` | `episode_start` | `episode_end` | `scenario_name` (display) |
| --- | --- | --- | --- |
| `dotcom` | 2000-03-01 | 2002-10-31 | dot-com bust |
| `2008` | 2007-10-01 | 2009-03-31 | 2008 financial crisis |
| `2020` | 2020-02-01 | 2020-04-30 | COVID-19 shock |
| `2022` | 2021-11-01 | 2022-10-31 | 2022 inflation shock |
| `banking_2023` | 2023-02-01 | 2023-05-31 | 2023 banking stress |

**Minimum coverage ratio (`min_coverage_ratio`):** `0.45` — aligned with the direct-history tier in legacy fallback math. A position has usable direct history when:

- the ticker column exists in the aligned monthly returns panel;
- at least **2** non-NaN monthly observations fall in `[episode_start, episode_end]`; and
- `n_valid / n_expected >= min_coverage_ratio` for that window.

**Configuration:** `CoreMvpHistoricalReplayConfig` in `src/core_mvp_historical_stress_replay.py` exposes only `min_coverage_ratio` (default `0.45`). Core MVP code must **not** load `config/historical_stress_proxy_map.yml`.

---

## 3. Replay status and output contract (target)

Each episode in `historical_stress_replay_v1.episodes[]` (and mirrored Block 3.2 fields) uses:

| Field | Values / notes |
| --- | --- |
| `scenario_id` | Canonical id from table §2 |
| `scenario_name` | English display label |
| `replay_status` | `full_replay` \| `partial_unavailable` \| `unavailable` |
| `direct_coverage_weight_pct` | 0–100 |
| `unavailable_weight_pct` | 0–100 |
| `unavailable_positions` | List of `{ticker, instrument_type, reason_en}` |
| `available_history_assets` | Positions with direct history; partial caveat when not full replay |
| `portfolio_level_result_available` | `true` only when all risk weight has direct history |
| `user_note` | English user-facing explanation (spec wording in §3) |
| `diagnosis_summary_en` | English narrative: coverage %, replay status, portfolio metrics when full, unavailable/available tickers when partial |
| `limitation_summary` | One-line limitation when not full replay |
| `portfolio_loss_pct` / `drawdown_pct` | Only when `portfolio_level_result_available` is true |

**Forbidden on Core MVP paths:** `used_proxies`, `proxy_coverage_weight_pct`, `proxy_assisted_replay`, `approved_etf_proxies`, any proxy mapping usage.

### Status rules

- **`full_replay`:** `unavailable_weight_pct == 0`.
- **`partial_unavailable`:** `0 < unavailable_weight_pct < 100` and at least one position has direct history.
- **`unavailable`:** no position has usable direct history, or the episode window cannot be evaluated.

### User-facing wording (partial / not full replay)

> This stress period cannot be fully replayed for the entire portfolio because some current positions did not exist or had no usable data at the time. Positions with usable direct history are shown separately. This is not a full replay of the current portfolio.

### User-facing wording (full replay)

> Portfolio-level historical replay is available. All portfolio positions have usable direct data for this stress period.

---

## 4. Code map

| Module / file | Role |
| --- | --- |
| `src/core_mvp_historical_stress_replay.py` | Config, coverage helpers, `build_episode_replay`, `build_historical_stress_replay_v1` |
| `src/stress.py` | `HISTORICAL_EPISODES` registry (dates) |
| `config/historical_stress_proxy_map.yml` | **Advanced / Legacy only** — not read by Core MVP module |

**Top-level JSON block:** `stress_report.json` → `historical_stress_replay_v1` with `version`, `policy: direct_history_only`, and `episodes[]`. Populated on portfolio-first diagnostic runs (`analysis_mode=analyze_current_weights`) before `stress_results_v1` is built. Block 3.2 `historical_episodes[]` copies the replay fields per episode.

---

## 5. Acceptance

**Session 1:** Spec, `min_coverage_ratio` 0.45, proxy map labeled Advanced/Legacy.

**Session 2:** `build_historical_stress_replay_v1` returns per-episode rows with required fields; portfolio metrics only when `portfolio_level_result_available`; tests `test_core_mvp_historical_stress_replay.py` (cases A–D).

**Session 5:** Parametrized contract tests cases A–D on replay rows and Block 3.2 merge (`tests/test_core_mvp_historical_stress_replay_contract.py`); partial replay must not restore portfolio metrics from legacy `historical_results`.

**Session 6:** Docs sync — `stress_lab_layer_spec.md` §3.1.1/§3.2, `stress_testing_spec.md` §9.4, `OUTPUTS.md`, `DECISIONS.md` (DEC-2026-05-28-001), `TESTING.md`.

**Session 7:** Live `run_portfolio_review.py --skip-candidates` on root `config.yml`; acceptance audit; pytest bundle **35 passed**; `scripts/verify_core_mvp_historical_stress_replay.py` exit 0.
