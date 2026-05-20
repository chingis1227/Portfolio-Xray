# Proposal: Crypto and Volatility Synthetic Stress Scenarios

**Status:** Deferred (see [DEC-2026-05-20-002](../../DECISIONS.md))  
**Date:** 2026-05-20  
**Wave:** Block 3 Phase 13 — [Stress Lab Methodology Governance Plan](../exec_plans/2026-05-20_stress_lab_methodology_governance_plan.md) Session 08 (`RM-959`)  
**Methodology gap:** G8 — `crypto_shock` / `volatility_shock` absent from `run_stress`  
**Default for Session 08:** documentation and decision only — **no** `SCENARIOS` code changes

---

## 1. Executive summary

Portfolio X-Ray already surfaces **volatility spike** and **conditional crypto** risks in the
Weakness Map, but the diagnostic **stress suite** (`run_stress`) runs only **eight** synthetic
scenarios (seven fixed vectors plus calibrated `recession_severe`). There is no
`volatility_shock` or `crypto_shock` row in `stress_report.json.scenario_results`.

This proposal documents what adding those scenarios would require, compares options, and records
why implementation is **deferred** until product explicitly approves a spec change and a follow-up
implementation session.

**Recommendation (Session 08):**

| Scenario | Stress suite (`run_stress`) | X-Ray Weakness Map |
| --- | --- | --- |
| **Volatility** | **Defer** dedicated synthetic scenario | **Keep Option B** (factor-only: `beta_vix` + `es_95`) — already shipped (`RM-948`) |
| **Crypto** | **Defer** until a crypto factor channel is defined | **Keep** conditional `crypto_shock` weakness row (taxonomy / weights) |

---

## 2. Current state (evidence)

### 2.1 Stress suite (`src/stress.py`)

| Synthetic `scenario_id` | In `SCENARIOS` / `run_stress` | Notes |
| --- | --- | --- |
| `equity_shock` … `commodity_shock` | Yes (7 fixed) | Six-shock engine: `shock_eq`, `shock_rr`, `shock_credit`, `shock_inf`, `shock_usd`, `shock_cmd` |
| `recession_severe` | Yes (calibrated) | Worst of 2008/2020 weekly factor sums vs portfolio betas |
| `volatility_shock` / `vix_shock` | **No** | `beta_vix` exists in factor registry; **not** in `_SHOCK_TO_BETA` |
| `crypto_shock` | **No** | No `beta_crypto` / `shock_crypto` in production factor map |

Linear PnL uses `_SHOCK_TO_BETA` (six keys only). `simulate_custom_shock` normalizes the same six
`shock_*` keys; `shock_vix` / `shock_oil` are defined in `stress_factors.FACTOR_BETA_TO_SYNTHETIC_SHOCK_KEY`
but are **not** wired into `run_stress` portfolio PnL.

### 2.2 Portfolio X-Ray (`src/portfolio_xray.py`)

| Weakness key | Stress scenario mapping | Evidence mode |
| --- | --- | --- |
| `volatility_spike` | **None** (`WEAKNESS_FACTOR_ONLY_RISKS`) | `beta_vix` + tail `es_95`; `scenario_coverage.evidence_mode = factor_only` |
| `crypto_shock` | **None** | Emitted only when `asset_class=crypto` or `main_risk_factor=crypto_beta` |

`WEAKNESS_SCENARIO_MAP` links recession, inflation, rates, credit, liquidity, USD, equity crash,
and commodity shock to existing synthetic ids — not crypto or vol spike.

### 2.3 Related prior decision (Block 2)

[portfolio_xray_diagnostics_spec.md](../specs/portfolio_xray_diagnostics_spec.md) §2.7 documents
**Option B** for `volatility_spike`: factor-only diagnostics, no synthetic stress row. That decision
applies to **X-Ray**; this proposal addresses whether **Stress Lab** should add a matching synthetic
scenario (Option A for stress).

---

## 3. Volatility — options and recommendation

### 3.1 Option A — Add `volatility_shock` (or `vix_shock`) to `run_stress`

**Intent:** Align Weakness Map `volatility_spike` with a named `scenario_results` row for PnL,
RC diagnostics, scorecard, and hedge-gap mapping.

**Proposed shock vector (illustrative — not calibrated):**

| Key | Illustrative value | Rationale |
| --- | --- | --- |
| `shock_vix` | +0.30 to +0.50 (30–50% VIX level move) | VIX is already a weekly factor (`FRED:VIXCLS`); shock on **level change** or **return** must be defined explicitly |
| Cross terms | e.g. `shock_eq = -0.10`, `shock_credit = +0.02` | Mild risk-off consistency with `liquidity_shock` |
| `vol_mult` | 1.40–1.60 | Elevated vol blocks in `taxonomy_blend_v1` |
| `stress_cov` | `True` | RC Top1/Top3 under stressed covariance |

**Engine prerequisites (breaking scope if done wrong):**

1. Extend `_SHOCK_TO_BETA` with `("shock_vix", "beta_vix")` (and asset-level beta column coverage).
2. Update `_portfolio_factor_pnl_pct`, `_scenario_return_per_asset`, `shock_vector_from_scenario`,
   `simulate_custom_shock` normalization, and stress spec §2 scenario table.
3. Add `volatility_shock` → `volatility_spike` in `WEAKNESS_SCENARIO_MAP` and
   `HEDGE_GAP_SCENARIOS_BY_RISK` (hedge gap v2 alignment).
4. Extend `scenario_library` / robust optimization eligibility only if product agrees (separate decision).
5. Contract tests: scenario count, PnL equivalence, scorecard row, X-Ray `scenarios_present` for vol row.

**Risks:**

- **Double counting:** X-Ray already flags high `beta_vix` and `es_95`; a large fixed VIX shock may
  overstate “vol vulnerability” relative to other scenarios.
- **Unit ambiguity:** VIX factor returns vs level shocks must match the weekly regression definition
  in `stress_factors.py` (same alignment as existing betas).
- **Suite inflation:** Ninth synthetic scenario changes worst-synthetic selection, commentary, and
  baseline snapshots — requires Session 10 integration and Session 11 baseline refresh.

### 3.2 Option B — No synthetic vol scenario (status quo for stress)

**Intent:** Volatility risk is visible via factor betas, tail metrics, and historical episodes
(e.g. 2020, 2022) without a dedicated factor shock row.

**Already implemented:** X-Ray `volatility_spike` factor-only contract (`RM-948`).

**Stress Lab behavior:** Unchanged eight-scenario suite; `liquidity_shock` and `equity_shock` partially
proxy broad risk-off vol compression.

### 3.3 Volatility recommendation

**Defer Option A** for Stress Lab. **Retain Option B** for X-Ray and stress suite.

Revisit when: (a) product requires vol spike PnL next to other named scenarios in IPS/PDF, or
(b) hedge-gap / weakness map reports persistent `scenarios_missing` confusion for vol (user research).

---

## 4. Crypto — options and recommendation

### 4.1 Problem statement

Crypto exposure is identified in taxonomy (`asset_class=crypto`, `main_risk_factor=crypto_beta`) and
in the Weakness Map, but the **six-factor stress engine has no crypto channel**. Applying
`shock_eq = -0.40` to crypto ETFs via equity beta proxy misstates idiosyncratic crypto drawdowns.

### 4.2 Option A — Dedicated `crypto_shock` synthetic scenario

**Proposed approach (high level):**

| Element | Proposal |
| --- | --- |
| Scenario id | `crypto_shock` |
| Shock | New `shock_crypto` mapped to new factor `crypto` / `beta_crypto` (weekly return series TBD: e.g. BTC proxy ETF) |
| Conditional run | **Only when** portfolio crypto weight ≥ threshold (e.g. 1% or 5%) or any crypto taxonomy row — mirror X-Ray emission rule |
| Cross terms | Minimal: optional mild `shock_eq` for correlated risk assets |
| RC | `stress_cov=True` with crypto block in taxonomy (may require new block code in `stress_covariance_taxonomy.py`) |

**Engine prerequisites:**

1. New `FactorDefinition` with `stress_participates=True` and data source policy in `data_policy_spec.md`.
2. Extend `_SHOCK_TO_BETA`, asset beta estimation, and `portfolio_betas` export on `stress_report.json`.
3. Conditional scenario execution in `run_stress` (skip row with `status=skipped_no_exposure` vs omit row — must be spec-defined).
4. `WEAKNESS_SCENARIO_MAP`: `crypto_shock` → `crypto_shock` weakness key.
5. Historical calibration optional (e.g. 2022 crypto drawdown window) — separate from fixed shock.

**Risks:**

- **Data policy:** Young crypto ETFs, stale ticks, and FX must follow `data_policy_spec.md`.
- **Mandate boundary:** Conditional scenarios complicate “worst synthetic” and scorecard comparability across portfolios.
- **Universe coverage:** Many policy portfolios have **zero** crypto; conditional logic must not look like missing data (same lesson as hedge `not_applicable`).

### 4.3 Option B — Proxy via equity shock only (rejected)

Map `crypto_shock` weakness to `equity_shock` for stress PnL. **Rejected:** overstates correlation,
hides crypto-specific tail risk, and contradicts taxonomy `crypto_beta`.

### 4.4 Option C — X-Ray only (status quo)

Keep crypto vulnerability in Weakness Map and factor/taxonomy evidence; no `run_stress` row.

### 4.5 Crypto recommendation

**Defer Option A.** **Retain Option C** until a crypto factor series, taxonomy block, and conditional
execution contract are accepted in `stress_testing_spec.md` and `DECISIONS.md`.

---

## 5. If implementation is approved later

Use a **dedicated implementation session** (not bundled with governance doc-only sessions). Minimum
deliverables:

| # | Deliverable |
| --- | --- |
| 1 | Update [stress_testing_spec.md](../specs/stress_testing_spec.md) §2 (mandatory or conditional scenarios) |
| 2 | `src/stress.py` — `SCENARIOS`, `_SHOCK_TO_BETA`, suffix map, optional conditional runner |
| 3 | `src/portfolio_xray.py` — `WEAKNESS_SCENARIO_MAP` / factor-only flags |
| 4 | `src/stress_covariance_taxonomy.py` — vol_mult / blocks if new blocks added |
| 5 | Contract tests: scenario count, conditional skip, X-Ray coverage, simulator alignment |
| 6 | Session 10-style downstream: scorecard, commentary, snapshot, comparison |
| 7 | Baseline snapshot + CHANGELOG + supersede this proposal status |

**Non-goals (unchanged):** no new mandate gates; no silent threshold changes; no optimizer weight changes.

---

## 6. Acceptance criteria (Session 08 — documentation only)

- [x] Reviewable proposal persisted under `docs/proposals/`.
- [x] DECISIONS entry records **defer** for both scenarios in `run_stress`.
- [x] Methodology map G8 closed as **spec-only / deferred**.
- [x] `stress_testing_spec.md` cross-references deferred scenarios (§2.3).
- [x] No change to `src/stress.py::SCENARIOS` in Session 08.

---

## 7. References

- [Stress Lab Methodology Map](../audits/2026-05-20_stress_lab_methodology_map.md) — G8, P4
- [stress_lab_layer_spec.md](../specs/stress_lab_layer_spec.md) — §3.1 synthetic block
- [portfolio_xray_diagnostics_spec.md](../specs/portfolio_xray_diagnostics_spec.md) — §2.7 vol Option B, crypto conditional
- [stress_testing_spec.md](../specs/stress_testing_spec.md) — §2 mandatory scenarios, §2.3 deferred
- [scenario_library_spec.md](../specs/scenario_library_spec.md) — library ids vs run_stress ids
