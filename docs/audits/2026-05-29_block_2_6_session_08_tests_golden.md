# Block 2.6 Portfolio Weakness Map — Session 08 Tests + Golden + Live Validation

Date: 2026-05-29

Status: **CLOSED**

Prior: Session 07 downstream SSOT (ExecPlan progress).

Plan: [2026-05-29_block_2_6_weakness_map_heuristic_v2_plan.md](../exec_plans/2026-05-29_block_2_6_weakness_map_heuristic_v2_plan.md)

## Scope delivered

| Item | Result |
| --- | --- |
| `assert_block_2_6_product_contract` + expanded unit tests | **PASS** |
| Per-risk parametrized evidence surface (8 canonical ids) | **PASS** |
| `tests/test_block_2_6_stress_boundary.py` (import isolation, forbidden keys, score invariance) | **PASS** |
| Golden `block_2_6` surface test in `test_portfolio_xray_contract.py` | **PASS** |
| Golden fixture regen (`portfolio_xray_golden_v2.json`) | **PASS** |
| Live `run_portfolio_review.py --skip-candidates` Block 2.6 validation | **PASS** |

## Regression command

```bash
python -m pytest tests/test_block_2_6_portfolio_weakness_map.py tests/test_block_2_6_stress_boundary.py tests/test_portfolio_xray_contract.py tests/test_problem_classification.py -q
```

Regenerate golden after intentional contract changes:

```bash
python tests/portfolio_xray_golden_inputs.py
python -m pytest tests/test_portfolio_xray_contract.py -q
```

**Session 08 closure:** **39 passed** (2026-05-29).

## Live verification (root `config.yml`, analysis_subject)

Path: `Main portfolio/analysis_subject/portfolio_xray.json`

| Check | Observed |
| --- | --- |
| `metadata.rule_version` | `heuristic_v2` |
| `len(risk_types)` | 8 |
| Canonical `risk_type` order | Matches `SYNTHETIC_SCENARIO_IDS` |
| `usd_shock` | **Medium** (score 55) — scored, not placeholder-only |
| `recession_severe` | **Unavailable** (`score_0_100` null) — insufficient evaluable signal coverage on this subject |
| Stress boundary | No `stress_report` / scenario PnL fields inside product block |

## Next

Session 09 — see [heuristic_v2 acceptance audit](2026-05-29_block_2_6_weakness_map_heuristic_v2_acceptance_audit.md) (**CLOSED**); ExecPlan **Completed**.
