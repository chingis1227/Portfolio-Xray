# Robust Mean–Variance baseline portfolios (uncapped + constrained)

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`,
`Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

## Purpose

Introduce optional **Robust Mean–Variance** baselines as **statistical benchmarks**, not replacements for `run_optimization.py`. The construction estimates weights from a mean–variance optimum on **stabilized inputs**: James–Stein shrinkage for expected returns; Ledoit–Wolf or OAS shrinkage for covariance; and an internal risk-aversion **λ** on monthly portfolio variance governing the trade-off between shrunk expected return and variance. **Clients choose IPS risk limits, not λ:** mandate-aligned λ selection belongs in `run_robust_mv_lambda_calibration.py`, which evaluates a λ grid against volatility, mandate maximum drawdown, diagnostic synthetic stress loss alignment (where configured), concentration caps (where configured), and related YAML constraints.

**Interpretation.** Treat Robust MV outputs (including calibrated λ runs) as: (1) a **return-aware statistical benchmark**; (2) a **sanity check** versus the policy optimizer pipeline; (3) a **comparison point** versus Equal Weight, Equal Weight by asset class, Risk Parity, HRP, Minimum Variance, Maximum Diversification, and Minimum CVaR. These paths **do not** apply ProLiquidity, mandate blocking as an optimizer layer, or RC caps as optimization targets.

Normative variant wording is mirrored in `portfolio_variants.ROBUST_MV_VARIANT_SUMMARY` and exported with baseline metadata (`robust_mv_variant_role`, `robust_mv_variant_summary`).

**Operator entrypoints (baseline weights + reports).**

    python run_robust_mean_variance_uncapped.py
    python run_robust_mean_variance_constrained.py

**IPS-aligned λ calibration (constrained path; grid vs mandate diagnostics).**

    python run_robust_mv_lambda_calibration.py

## Definitions

**Monthly panel.** Same synchronous monthly simple returns used elsewhere for baseline covariance: inner join over eligible assets in the configured window ending at `analysis_end`.

**Shrunk μ.** Per-asset sample mean over time, then James–Stein positive-part shrinkage toward the mean of those sample means (details and formula in `src/robust_mv.py`). For fewer than three assets, shrinkage intensity is zero.

**Shrunk Σ.** `sklearn.covariance.LedoitWolf` or `sklearn.covariance.OAS` fit on the panel; matrix symmetrized; PSD repair via eigenvalue clipping (`repair_covariance_psd`).

**λ (`robust_mv_lambda`).** Non-negative risk aversion on **monthly** portfolio variance `w′Σw`. When λ = 0, the objective reduces to maximizing `μ′w` on the feasible set (still uses shrunk μ only).

**Uncapped variant.** Bounds `(0, 1)` per asset, `sum(w)=1`. No config min/max weights, no feasibility basket cap, no Young per-ticker caps.

**Constrained variant.** Same `_build_bounds` as constrained minimum-variance / maximum-diversification / minimum CVaR: feasibility cap, `min_single_security_weight_pct`, `max_single_security_weight_pct`, and Young per-ticker caps when `young_etf_optimization_policy.enabled` is true. Σ for the objective remains LW/OAS on the synchronous panel; the dual Young covariance path is used **only** to derive caps, not to replace Σ in the objective.

## Milestones (story)

**Milestone A — Core math.** Implement `src/robust_mv.py`: James–Stein helper, covariance helper, PSD status labeling, and `solve_robust_mean_variance` with SLSQP (minimize `λ w′Σw − μ′w`). Acceptance: unit tests pass on synthetic data.

**Milestone B — Builders.** Add `build_robust_mean_variance_uncapped` and `build_robust_mean_variance_constrained` in `src/portfolio_variants.py`, metadata export list (including exported variant interpretation fields), and diagnostics (`raw_mu`, `shrunk_mu`, `shrinkage_intensity`, `objective_value`, `concentration_metrics`, etc.). Acceptance: builders return `OK` or `APPROXIMATE` on synthetic panels.

**Milestone C — Config and CLI.** Extend `PortfolioConfig` and `validate_config` with `robust_mv_lambda`, `robust_mv_covariance_method`, `robust_mv_mu_shrinkage_method`. Add root scripts mirroring other baselines (weights.json, baseline_weights_metadata.json, summary.json/txt, report + PDF rebuild hook). Acceptance: `load_validated_config()` accepts defaults; scripts run without import errors.

**Milestone D — λ calibration.** Add `run_robust_mv_lambda_calibration.py` + `src/robust_mv_calibration.py` to map IPS limits to a λ grid on the constrained path (read-only stress/mandate diagnostics); document that λ is internal.

**Milestone E — Documentation.** Update `AGENTS.md`, `SPEC.md`, `config.yml.example`, PDF rebuild list in `src/pdf_reports.py`, and keep this ExecPlan current.

## Validation

From the repository root:

    python -m pytest tests/test_robust_mean_variance.py -q

Optional smoke on real config (requires data/network/cache):

    python run_robust_mean_variance_uncapped.py
    python run_robust_mean_variance_constrained.py
    python run_robust_mv_lambda_calibration.py

## Progress

- [x] Milestone A — `src/robust_mv.py` implemented.
- [x] Milestone B — `portfolio_variants` builders and metadata export (including variant interpretation export keys).
- [x] Milestone C — config schema, CLI scripts, PDF suite entries.
- [x] Milestone D — λ calibration (`run_robust_mv_lambda_calibration.py`, `src/robust_mv_calibration.py`).
- [x] Milestone E — AGENTS / SPEC / `config.yml.example` / ExecPlan documentation alignment.

## Surprises & Discoveries

- Constrained Robust MV intentionally uses LW/OAS Σ on the inner-join panel while Young policy affects bounds only, so the objective matches the product spec without mixing dual-merged Σ into the mean–variance kernel.

## Decision Log

- **Σ vs dual Young merge:** Use LW/OAS on the synchronous eligible panel for both variants; derive Young caps via `build_dual_covariance_and_mu` diagnostics only on the constrained path.
- **λ default:** `robust_mv_lambda = 0` means no variance penalty; optimizer maximizes shrunk expected return subject to constraints.
- **λ vs IPS:** Treat λ as an internal knob; map IPS limits to λ via `run_robust_mv_lambda_calibration.py` instead of asking clients to set λ directly.

## Outcomes & Retrospective

Delivered baseline entrypoints, shared math module, schema defaults, PDF rebuild integration for commentary/stress/weights when outputs exist, mandate-aligned λ calibration tooling (`analysis_robust_mv_lambda_calibration/`), exported interpretation metadata (`robust_mv_variant_role`, `robust_mv_variant_summary`), and pytest coverage for shrinkage, PSD covariance, solver behavior, constraint caps, and calibration helpers.
