# View After Optimization — Protocol (tactical tilt)

**Policy link.** This document defines the **only permitted exception** to the rule "No manual weight adjustments" in [portfolio_construction_policy.md](../portfolio_construction_policy.md). Tilts may be applied to the Policy portfolio **only** through this protocol. Final weights are never edited by hand; changes are deterministic and reported for audit.

---

## 0) Baseline

1. Build the Policy portfolio per `portfolio_construction_policy.md` (optimization, ProLiquidity, RC post-process, mandate).
2. Baseline weights come from `portfolio_weights.yml` / config or the last optimization output.
3. Optional: pass baseline stress summary from `run_result.json` for reporting context only.

---

## 1) PM inputs

1. **Asset** `X`: ticker to increase (must be in the baseline weight set / universe).
2. **Δchoice:** tilt size from the menu **{+1%, +2%, +5%}** of total portfolio weight (implemented in code as auto-shrink **5% → 2% → 1%** if gates fail).

There is **no** separate "HEDGE" vs "TACTICAL" mode and **no** hedge-benefit or tail-overlay logic in the implementation.

---

## 2) Funding (current implementation)

- Funding sells from **other** positions in **descending RC** order (subject to `min_single_security_weight_pct`).
- Weights are renormalized to sum to 1 after the tilt.

(Legacy spec text about block-aware donors, RB corridors, and stress **PASS** gates is **removed**; the code does not implement those rules.)

---

## 3) Gates (per attempted Δ, in order)

1. **Weights:** each held name within min/max single-name bounds; total weight = 1.
2. **Vol:** estimated annual vol of tilted portfolio ≤ `1.5 × target_vol_annual` when a target vol is set.
3. **Max drawdown:** on the aligned return window, portfolio max DD not worse than `target_max_drawdown_pct` when set.
4. **RC caps:** per-asset RC vs caps from config (same machinery as main optimization path).
5. **Stress:** `run_stress` is run for diagnostics only (`stress_diagnostic_status` / codes in the report); it **does not** accept or reject the tilt in code.

If any gate fails, the next smaller Δ from the menu is tried. If all fail → **TILT_REJECTED**.

---

## 4) Outcome statuses

- **TILT_ACCEPTED** — a Δ passed all gates.
- **TILT_REJECTED** — no feasible Δ.

`TILT_NO_BENEFIT` and hedge-specific fields are **not** produced by the current implementation.

---

## 5) Report (`view_execution_report.json`)

Minimum fields (see `src/view_after_optimization.py`):

- `baseline_weights`, optional `baseline_stress` summary
- `request`: `asset`, `delta_choice`
- `execution_delta`, `funding_donors_sold`
- `outcome_status`, `rb_status` (placeholder `N_A`), `broken_gate`, `key_metric_values`
- `tilted_weights`, `tilted_stress_summary`

---

## 6) CLI

`python run_view_after_optimization.py --asset TICKER --delta {1|2|5}`  
Optional: `--weights-file`, `--run-result-file`, `--output`, `--no-cache`.
