# Two-Stage RiskPortfolio Optimization (canonical)

This document is the **source of truth** for the **default** primary RiskPortfolio optimization in `run_optimization.py`. It aligns with **docs/portfolio_construction_policy.md** (§2.2 risk budget, §2.4 RC caps, §2.6 optimization).

For the **legacy** single-pass optimizer, see **§ Legacy single-stage** below.

---

## 1. Purpose

Split the numerical problem into:

1. **Architecture of risk** — find a **coherent risk skeleton** across Growth / Duration / Inflation (RC structure + diversification within the penalty), and select a **concrete RB target triple** via the same RB-search order as policy (midpoint → range → expanded).
2. **Return and mandate alignment** — starting from that skeleton, **maximize expected return** (estimated \(\mu\)) while staying near the skeleton and applying **soft** mandate-style targets (vol and nominal return) as penalties, not as hard relaxations of mandate gates.

Mandate **Max Drawdown** and **stress** behaviour are unchanged: they run **after** weights are produced, as defined in **portfolio_construction_policy.md** and **docs/docs/stress_testing_spec.md**.

---

## 2. When it runs

| Entry | Behaviour |
|--------|-----------|
| `python run_optimization.py` (no extra flags) | **Two-stage** primary window (default). |
| `python run_optimization.py --single-stage` | **Legacy** one-pass RB search + default `max_return` objective. |

Other flags (`--no-cache`, `--no-report`, `--profile`, `--config`, `--write-config`) compose normally.

---

## 3. Stage 1 — `risk_skeleton`

**Implementation:** `run_risk_budget_optimization(..., objective_mode=risk_skeleton, ...)`.

**Intent:**

- Penalize **RC cap violations** (same penalty machinery as elsewhere; strength from `rc_cap_penalty_lambda` in config).
- Add **concentration penalty** on block RC: \(\lambda_{\text{skel}} \times \sum_b \mathrm{RC\_vol}_b^2\) (Herfindahl-style on **block** RC shares), controlled by **`risk_skeleton_concentration_lambda`** (default `10.0` in schema; `0` = RC-cap penalty only).

**Risk budget selection:**

- **`rc_block_targets`** from profile/config is the starting point.
- **`rb_target_ranges`** and **RB search** (simplex + expanded fallback) follow **portfolio_construction_policy.md** §2.2 — same order as single-stage.
- The chosen target is echoed in the optimizer **status string** as  
  `RB_TARGET_USED: g/d/i` (Growth / Duration / Inflation shares).

**Output:** feasible weights \(w^{(1)}\) and status line used to parse **`RB_TARGET_USED`** for stage 2.

---

## 4. Stage 2 — `max_return` from skeleton + soft IPS

**Implementation:** second call to `run_risk_budget_optimization` with:

| Setting | Meaning |
|--------|---------|
| `rc_block_targets` | Parsed **`RB_TARGET_USED`** from stage 1; if parsing fails, fallback to config `rc_block_targets`. |
| `rb_target_ranges` | **`None`** — no second RB search. |
| `rb_search_enabled` | **`False`** — fix the triple from stage 1. |
| `objective_mode` | **`max_return`** |
| `warm_start_weights` | \(w^{(1)}\) from stage 1 |
| `skeleton_tracking_lambda` | **10.0** (code constant `_TWO_STAGE_SKEL_TRACK_LAMBDA`) — penalty for drifting away from \(w^{(1)}\). |
| `soft_target_vol_annual` / `soft_target_return_annual` | From config (`target_vol_annual`, `target_nominal_return_annual`) when set. |
| `soft_vol_penalty_lambda` / `soft_return_penalty_lambda` | From **`optimization_soft_vol_penalty_lambda`** / **`optimization_soft_return_penalty_lambda`**. If either is **≤ 0**, runtime substitutes **12** (vol) and **8** (return) so soft terms are active. |

**`risk_skeleton_concentration_lambda`** is passed through for consistency with the solver signature; stage 2 objective is **`max_return`** (not `risk_skeleton`).

---

## 5. After stage 2 (unchanged pipeline)

Order matches **portfolio_construction_policy.md** § Production workflow:

1. **RC post-processing** — `enforce_rc_caps_postprocess` (strict vs permissive per `rc_policy_mode`).
2. **Block RC logging** — realized RC by block on the primary window.
3. **Robustness (optional)** — secondary **5Y** optimization for `robustness_report.json` uses the **legacy single-pass** call (RB search + default `max_return`) for horizon comparison — **not** a second two-stage loop (faster; diagnostic).
4. **ProLiquidity**, tail overlay, **mandate** historical MaxDD, **stress**, **`run_result.json`**, **`portfolio_weights.yml`**.

---

## 6. Config fields (reference)

| Field | Role in two-stage |
|-------|-------------------|
| `rc_cap_penalty_lambda` | Both stages |
| `risk_skeleton_concentration_lambda` | Stage 1 skeleton concentration |
| `target_vol_annual`, `target_nominal_return_annual` | Soft targets for stage 2 (optional) |
| `optimization_soft_vol_penalty_lambda`, `optimization_soft_return_penalty_lambda` | Strength of soft penalties; **0 or unset → 12 / 8** at runtime for stage 2 |
| `rc_block_targets`, `rc_block_target_ranges` | Stage 1 only (ranges drive RB search) |

---

## 7. Legacy single-stage

**Flag:** `--single-stage`

**Behaviour:** one call to `run_risk_budget_optimization` with default **`max_return`**, **`rb_target_ranges`** and RB search as today, **no** warm start from `risk_skeleton`.

Use for **reproducing older runs**, A/B tests, or debugging. Production policy treats **two-stage** as the default architecture.

---

## 8. Related documents

- **docs/portfolio_construction_policy.md** — rule hierarchy, RB corridor, production gates.
- **docs/production_workflow.md** — status codes and what blocks weights.
- **docs/data_policy_nan_young_etfs.md** — dual covariance / young ETF path (unchanged; applies before optimization).
- **docs/docs/feasibility_constraints_spec.md** — RC caps, weight caps.
- **research/two_stage_optimization_experiment.py** — offline experiments; does not write production weights.
