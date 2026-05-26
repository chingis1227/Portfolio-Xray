# Block 2.2 Drawdown Structure Wiring — Bugfix Note

Date: 2026-05-26

Related: [Block 2.2 acceptance audit](2026-05-26_block_2_2_portfolio_metrics_acceptance_audit.md) (Session 08 deferred item §6).

## Problem

`run_report.py` stores `drawdown_structure` inside `snapshot["analytics"]["drawdown_structure"]`.
`_xray_summary_from_output_dir` passed only `snapshot.get("drawdown_structure")` (top-level) into
`build_block_2_2_portfolio_metrics`, so extended drawdown fields were **null** on live runs despite
data being computed.

## Fix

`src/block_2_2_portfolio_metrics.py` — `build_block_2_2_portfolio_metrics` now resolves drawdown as:

1. Non-empty top-level `drawdown_structure` argument (precedence), else
2. `portfolio_analytics["drawdown_structure"]` (live lightweight path).

No snapshot schema change.

## Verification

| Check | Result |
| --- | --- |
| `tests/test_block_2_2_portfolio_metrics.py` | **6 passed** (3 new tests) |
| Regression bundle (2.1 + 2.2 + bundle/runtime) | **37 passed** |
| Live `--skip-candidates` / `--candidates equal_weight` | exit **0** |
| `validate_one_candidate_demo.py` | **PASS** (8 checks) |

### Live before / after (`config.yml`, `drawdown_diagnostics`)

| Field | Before fix | After fix |
| --- | ---: | ---: |
| `max_drawdown` | -0.198 | -0.198 |
| `ttr_months` | 27.0 | 27.0 |
| `pct_time_underwater` | null | **0.567** |
| `count_drawdowns_gt_5` | null | **4** |
| `count_drawdowns_gt_10` | null | **1** |
| `count_drawdowns_gt_20` | null | **0** |
| `recovery_median` | null | **1.0** |
| `recovery_p90` | null | **4.0** |
| `longest_underwater` | null | **26** |
| `drawdown_depth` | null | **-0.198** |
| `drawdown_length` | null | **27** |
| `recovery_months` | null | **18** |

`count_drawdowns_gt_20` = **0** is a valid populated value (no >20% drawdown episodes in 10Y window).
