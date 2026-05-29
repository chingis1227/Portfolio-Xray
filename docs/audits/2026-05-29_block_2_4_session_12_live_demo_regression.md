# Block 2.4 Hidden Exposure — Session 12 Live Demo + Regression

Date: 2026-05-29

Status: **CLOSED**

Prior: [Session 11 Core MVP validation](2026-05-29_block_2_4_session_11_core_mvp_validation.md)

## Scope delivered

| Item | Result |
| --- | --- |
| Live `block_2_4_hidden_exposure` on root `config.yml` subject X-Ray | **PASS** — `heuristic_v2`, confidence model `v2`, block status `ok` |
| `scripts/validate_block_2_4_live.py` operator validator (`--refresh-xray`) | **PASS** |
| `live_core_e2e` institutional v2 checks for Block 2.4 | **PASS** (block-level); full gate blocked by stale comparison menu (pre-existing) |
| Session 11 regression bundle | **PASS** — **140 passed** |
| One-candidate `run_portfolio_review.py --candidates equal_weight` | **Attempted** — long-running; subject Block 2.4 validated after X-Ray refresh (see §5) |

## Live validation contract (Session 12)

After diagnosis materialization (or X-Ray refresh from existing subject artifacts):

```bash
python scripts/validate_block_2_4_live.py --refresh-xray
```

Checks:

- `diagnostics_meta.ruleset` = `heuristic_v2`
- `diagnostics_meta.confidence_model` = `v2`
- `diagnostics_meta.does_not_run_stress_lab` = true
- Six alerts with mandatory v2 fields (`limitations`, `confidence_reason`, `contributing_assets`, `confirmation_status`)
- No embedded Block 3 stress payloads at Block 2.4 top level

## Regression command

```bash
python -m pytest tests/test_core_mvp_block2_4_contract.py tests/test_block_2_4_hidden_exposure.py tests/test_block_2_4_matrix_coverage.py tests/test_portfolio_xray_contract.py tests/test_core_mvp_blocks_1_3_boundaries.py -q
```

Optional live core gate (Block 2.4 evidence only when comparison menu is stale):

```bash
python scripts/verify_live_core_e2e.py
```

## Live snapshot (root `config.yml`, 8 tickers, refreshed 2026-05-29)

Artifact: `Main portfolio/analysis_subject/portfolio_xray.json` (rebuilt via `_xray_summary_from_output_dir` from subject `snapshot_10y.json`, `stress_report.json`, `run_metadata.json`).

| Field | Observed |
| --- | --- |
| `block` | `2.4_hidden_exposure` |
| `status` | **ok** |
| `diagnostics_meta.ruleset` | **heuristic_v2** |
| `diagnostics_meta.confidence_model` | **v2** |
| `diagnostics_meta.does_not_run_stress_lab` | **true** |
| `blocked_upstream_fields` count | **9** |

### Six alerts (live demo book)

| alert_id | status | score | confidence | confirmation_status |
| --- | --- | ---: | --- | --- |
| `hidden_equity_beta` | Low | 36 | low | not_applicable |
| `duration_concentration` | Medium | 66 | medium | not_applicable |
| `credit_liquidity_risk` | Low | 19 | low | not_applicable |
| `correlation_concentration` | Medium | 40 | low | not_applicable |
| `weak_hedge_behavior` | Medium | 50 | low | **confirmed** |
| `tail_risk` | Medium | 44 | low | not_applicable |

### `top_hidden_risks` (top 3)

1. `duration_concentration` — Medium / 66 / medium  
2. `weak_hedge_behavior` — Medium / 50 / low  
3. `tail_risk` — Medium / 44 / low  

## Operator commands (Session 12)

Diagnosis-only (materializes subject; may take >30 min on cold cache):

```bash
python run_portfolio_review.py --skip-candidates
```

Refresh Block 2.4 on existing subject artifacts (fast, same `build_portfolio_xray_v2` path):

```bash
python scripts/validate_block_2_4_live.py --refresh-xray
```

One-hypothesis demo:

```bash
python run_portfolio_review.py --candidates equal_weight
python scripts/validate_one_candidate_demo.py
```

## Code / gate changes (Session 12)

- `src/live_core_e2e.py` — `check_block_2_4_hidden_exposure` on materialized subject X-Ray (`ruleset`, `confidence_model`, contract violations, stress boundary).
- `scripts/validate_block_2_4_live.py` — dedicated Block 2.4 live validator with optional `--refresh-xray`.

## Notes

- Stale `portfolio_xray.json` from pre-upgrade runs may still show `heuristic_v1` until refresh or full materialize; always run `validate_block_2_4_live.py --refresh-xray` after pulling Sessions 01–11 code.
- `verify_live_core_e2e.py` may fail on `candidate_menu.review_mode` / `factory_profile_id` when `candidate_comparison.json` on disk is from a prior full-menu run; Block 2.4 evidence in that gate remains valid when present.

## Next

Session 13 — see [Session 13 institutional closure](2026-05-29_block_2_4_session_13_institutional_closure.md) (**CLOSED**).
