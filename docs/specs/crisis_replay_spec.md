# Crisis Replay Specification

Status: diagnostic-only contract for historical episode path outputs.

Version: **crisis_replay_v2** (portfolio path + recovery + static asset attribution).

## Purpose

Provide month-by-month replay evidence for historical stress episodes instead of aggregate-only fields,
plus episode-level recovery timing and static-weight asset loss attribution.

## Inputs

- monthly portfolio returns in episode windows (aligned inner join across assets)
- fixed portfolio weights for the analyzed subject (not renormalized within episode)
- canonical historical episode list from `src/stress.py::HISTORICAL_EPISODES`

## Output contract

### In `stress_report.json`

`historical_episode_paths`: list of episode blocks (one per episode with sufficient data):

| Field | Description |
| --- | --- |
| `replay_version` | `crisis_replay_v2` |
| `episode`, `episode_start`, `episode_end` | Episode identity and calendar window |
| `n_obs`, `n_expected_obs`, `coverage_ratio`, `data_quality` | Same semantics as `historical_results` |
| `time_to_recovery_months` | Months from max-DD peak to first post-trough month equity ≥ prior peak; `null` if not recovered in-window |
| `recovered` | Whether recovery occurred within the episode window |
| `asset_pnl_contrib_episode` | Map `ticker →` additive static-weight sum of `w_i * r_i,t` over episode months |
| `top_loss_assets_episode` | Up to three tickers with lowest `asset_pnl_contrib_episode` values |
| `rows` | Month-by-month portfolio path (see below) |

**Recovery** follows [metrics_specification.md](metrics_specification.md) §6.9 via
`src/metrics_asset.py::time_to_recovery` on episode portfolio monthly returns.

**Asset attribution** is additive (sum of weighted monthly returns), not compounded asset equity.
The sum of `asset_pnl_contrib_episode` values equals the sum of monthly `portfolio_return` over the
episode (which may differ from compounded `pnl_real_episode` in `historical_results`).

`rows` (list):

- `date`
- `portfolio_return`
- `equity`
- `drawdown`

Episodes with insufficient data (`n_obs < 2` or null `max_dd`) do not appear in
`historical_episode_paths`; quality metadata remains on `historical_results` only.

### CSV exports

Per episode under `results_csv/`:

| File | Content |
| --- | --- |
| `crisis_replay_{episode}.csv` | One row per `historical_episode_paths[*].rows` entry |
| `crisis_replay_{episode}_asset_contrib.csv` | `ticker`, `episode_pnl_contrib` from `asset_pnl_contrib_episode` |

## Acceptance rules

- Path max drawdown must match the aggregate historical `max_dd` for the same episode.
- CSV row count for `crisis_replay_{episode}.csv` must equal `n_obs`.
- `time_to_recovery_months` / `recovered` must be consistent with `time_to_recovery` on the same
  episode portfolio return series used to build `rows`.
- Sum of `asset_pnl_contrib_episode` values must equal the sum of `portfolio_return` in `rows`
  (within rounding tolerance).
- Episodes with insufficient data must still emit quality metadata in `historical_results`.
