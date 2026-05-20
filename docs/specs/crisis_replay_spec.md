# Crisis Replay Specification

Status: diagnostic-only contract for historical episode path outputs.

## Purpose

Provide month-by-month replay evidence for historical stress episodes instead of aggregate-only fields.

## Inputs

- monthly portfolio returns in episode windows
- fixed portfolio weights for the analyzed subject
- canonical historical episode list from `src/stress.py::HISTORICAL_EPISODES`

## Output contract

### In `stress_report.json`

`historical_episode_paths`: list of episode blocks:

- `episode`, `episode_start`, `episode_end`
- `n_obs`, `n_expected_obs`, `coverage_ratio`, `data_quality`
- `rows`: list of:
  - `date`
  - `portfolio_return`
  - `equity`
  - `drawdown`

### CSV exports

Per episode CSV under `results_csv/`:

- `crisis_replay_{episode}.csv`

Each row mirrors `historical_episode_paths[*].rows`.

## Acceptance rules

- Path max drawdown must match the aggregate historical `max_dd` for the same episode.
- CSV row count must equal `n_obs`.
- Episodes with insufficient data must still emit quality metadata in `historical_results`.
