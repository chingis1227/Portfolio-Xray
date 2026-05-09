# Maximum Diversification baseline (constrained long-only)

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`,
`Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

Repository norms: [`PLANS.md`](../../PLANS.md) from the repo root.

## Purpose / Big Picture

Add a standalone **maximum diversification** baseline that maximizes the **diversification ratio** \(DR = (\sigma^{\top} w) / \sqrt{w^{\top}\Sigma w}\) on the same **monthly** covariance path and **same box bounds** as **minimum_variance_constrained** (`src.optimization._build_bounds`), with \(\sum_i w_i = 1\) and long-only feasibility. Users run `python run_maximum_diversification.py` and get a **`maximum diversification portfolio/`** folder with weights, baseline metadata including **diversification_ratio**, and the usual metrics/stress/report pipeline via `run_portfolio_report_for_weights`.

## Progress

- [x] (2026-05-08) ExecPlan authored; implementation milestones completed in code (`src/portfolio_variants.py`, `run_maximum_diversification.py`, tests, docs, PDF suite hook).
- [x] (2026-05-08) Solver: SLSQP on \(-DR\) with analytic Jacobian; fallback attempts match MV resilience pattern.

## Surprises & Discoveries

- Observation: Maximizing \(DR\) is not a convex program; **SLSQP** may converge to **local** maxima depending on \(\Sigma\) and bounds.
  Evidence: Accepted for baseline parity with other nonlinear variant scripts; mitigation uses the same feasible **inverse-volatility** scaling start as Minimum Variance (`_minimum_variance_slsqp`-style \(x_0\)).

## Decision Log

- Decision: Keep **maximum diversification** out of **`run_optimization.py`** policy `objective_mode`; expose only as an explicit baseline script (`run_maximum_diversification.py`).
  Rationale: Aligns with “separate optimization layer” product ask; avoids changing mandate / max-return product path. Date: 2026-05-08.

- Decision: Solve **\( \max DR \)** by minimizing **\(-DR\)** using **SciPy SLSQP** with **explicit gradient** \(\nabla DR = \sigma/\mathrm{den} - (\Sigma w)(\sigma^{\top}w)/\mathrm{den}^3\), \(\mathrm{den}=\sqrt{w^{\top}\Sigma w}\).
  Rationale: Fast, deterministic, consistent with `_minimum_variance_slsqp`; second SLSQP pass without Jacobian if the first stagnates.

- Decision: Report diagnostics **dimensionless \(DR\)** on **monthly** \(\Sigma\); annualizing scales numerator and \(\sqrt{\text{variance}}\) by \(\sqrt{12}\) equally, leaving **\(DR\) unchanged**.
  Rationale: Document user interpretation without extra annualized DR confusion.

## Outcomes & Retrospective

Delivers **`maximum_diversification_constrained`** in `baseline_weights_metadata.json`, folder **`maximum diversification portfolio/`**, **`python -m pytest tests/test_maximum_diversification_baseline.py`** green, **`AGENTS.md` / `SPEC.md`** updated. Optional triplet **`run_compare_variants.py`** extension remains out of scope for v1.

## Context and Orientation

- **Variants module:** [`src/portfolio_variants.py`](../../src/portfolio_variants.py) builds Equal-Weight, Risk Parity, Minimum Variance, and Maximum Diversification baselines outside policy caps.
- **Bounds:** [`src.optimization._build_bounds`](../../src/optimization.py) — same feasibility/config min/max/Young caps as constrained MV when dual covariance is on.
- **Covariance reuse:** **`_eligible_universe_from_returns`**, **`_mv_covariance_for_eligible`**, PSD repair identical to **`build_minimum_variance_constrained`**.
- **Reporting entry:** **`run_report.run_portfolio_report_for_weights`** from [`run_report.py`](../../run_report.py`).
- **PDF suite:** [`src/pdf_reports.py`](../../src/pdf_reports.py) **`rebuild_all_pdfs`** iterates **`mv_dirs` tuple list** pattern for commentary/stress/weights PDFs.

## Plan of Work

1. Extend **`portfolio_variants`**: constants, **`maximum_diversification_baseline_metadata_export`**, **`_maximum_diversification_slsqp`**, **`_finalize_md_weights`**, **`build_maximum_diversification_constrained`**.
2. Add **`run_maximum_diversification.py`** mirroring **`run_minimum_variance.py`** outputs and **`maximum_diversification_metadata`** snapshot field names.
3. Add **`tests/test_maximum_diversification_baseline.py`**: feasibility, bounds, \(\sum w \approx 1\), **`DR(w^\*) ≥ DR(w^{EW})\)** on the same repaired monthly covariance slice.
4. Wire **PDF**: `_PDF_HEADER_LEFT` keys + **`mv_dirs`** (or successor list) entry for **`maximum diversification portfolio`** folder.
5. Document **`AGENTS.md`**, **`SPEC.md`** “Expected Product Behavior”.

## Concrete Steps

From repository root (`c:\...\exp-pf-arch-v2-dc9c2cc6` or user worktree):

    python -m pytest tests/test_maximum_diversification_baseline.py -q

Then with valid `config.yml` and network data as needed:

    python run_maximum_diversification.py

Expect **`maximum diversification portfolio/weights.json`**, **`baseline_weights_metadata.json`** with **`optimizer_name`** = **`maximum_diversification_constrained`** and **`diversification_ratio`**.

Rebuild PDF suite if Pandoc toolchain present:

    python rebuild_pdf_reports.py

(or rely on **`try_rebuild_pdfs_after_variant`** at end of **`run_maximum_diversification.py`**).

## Validation and Acceptance

- **Unit tests**: `pytest tests/test_maximum_diversification_baseline.py` — all passed; import smoke **`import run_maximum_diversification`**.
- **Behavior**: Constrained optimum has **greater or equal diversification ratio** than equal weights on **identical \(\Sigma\) estimate** used in the assertion (repair + window slice), within numeric tolerance \(\sim 10^{-6}\).

## Idempotence and Recovery

Scripts overwrite outputs in **`maximum diversification portfolio/`** deterministically given the same inputs. Safe to re-run after failed partial write; partial runs leave stale files only if interrupted mid-write — re-run clears.

## Artifacts and Notes

- Diagnostics include **`solver_success`**, **`diversification_ratio`**, **`portfolio_variance`** (monthly), **`annualized_volatility`** (for comparison with MV outputs).

## Interfaces and Dependencies

- **Public builder**

      def build_maximum_diversification_constrained(
          cfg: PortfolioConfig,
          monthly_returns: pd.DataFrame,
          analysis_end: str,
          window_months: int,
      ) -> BaselineWeightsResult

- **`BaselineWeightsResult`**: unchanged dataclass **`weights`, `status`, `diagnostics`**.

- **Dependencies**: **`numpy`**, **`scipy.optimize.minimize`** (method **`SLSQP`**), **`pandas`** — consistent with **`portfolio_variants`**.

Revision note (2026-05-08): Initial v1 authored after implementation roadmap approval.
