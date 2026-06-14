# Legacy / research / advanced runners

Scripts in this directory are **not** part of the current Core MVP product runtime.

## Active Core MVP entrypoints (repository root)

| Command | Scope |
| --- | --- |
| `python run_core_diagnostics.py` | Blocks 1-3: Input, Portfolio Diagnosis, Stress Test Lab |
| `python run_portfolio_review.py` | Full diagnosis-first product workflow (candidates off by default) |
| `python run_portfolio_review.py --candidates equal_weight` | Full workflow + one explicit candidate through Decision Verdict |

## This folder

- Optimizer zoo (`run_equal_weight.py`, `run_risk_parity.py`, robust/min-var builders, etc.)
- Legacy policy workflow (`run_optimization.py`, `run_mvp_workflow.py`)
- Variant utilities (`run_stress_variant.py`, `run_rebalance.py`, `run_view_after_optimization.py`)
- EW/RP-only comparison (`run_compare_ew_rp.py`)

Root-level `run_<name>.py` files with the same basename are **thin deprecation wrappers** that
delegate here so existing automation and `run_candidate_factory.py` entry commands keep working.

## Internal engines (still at repo root)

- `run_report.py` — metrics/stress/materialization engine (prefer `run_core_diagnostics.py` or `run_portfolio_review.py` at the CLI)
- `run_candidate_factory.py` — candidate batch builder (explicit `--with-candidates` / `--candidates` only)
- `run_compare_variants.py` — comparison writer (invoked by factory `--then-compare` or explicit compare)

See [docs/runtime_entrypoints.md](../../docs/runtime_entrypoints.md) for the full matrix.
