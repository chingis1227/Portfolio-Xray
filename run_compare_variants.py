from __future__ import annotations

"""
Compare Policy vs Equal-Weight vs Risk-Parity vs Robust Scenario portfolios in a single summary file.

This script assumes that:
- Policy portfolio report has been generated into output_dir_final (config.yml).
- Equal-Weight baseline exists in project root folder "equal-weight portfolio".
- Risk-Parity baseline exists in project root folder "risk parity portfolio".
- Robust scenario variant exists in project root folder "robust scenario portfolio" (optional).

It builds a machine-readable JSON and a concise TXT table with:
- CAGR
- Volatility
- Max Drawdown
- Sharpe / Sortino
- Beta vs benchmark
- Correlation with benchmark
- Stress-test status
- Client-fit (MaxDD gate pass/fail)
"""

import json
from pathlib import Path

from src.config import load_validated_config
from src.utils import setup_logging, logger


def _load_variant_summary(root: Path, subdir: str | None, label: str) -> dict:
    if subdir:
        base = root / subdir
    else:
        base = root
    # Prefer snapshot_10y.json if available, else fall back to run_metadata / summary.json
    snap_10y = base / "snapshot_10y.json"
    summary_json = base / "summary.json"
    run_meta = base / "run_metadata.json"

    metrics = {}
    stress_status = None
    client_fit = None

    if snap_10y.exists():
        try:
            with open(snap_10y, encoding="utf-8") as f:
                data = json.load(f)
            m = data.get("metrics") or {}
            metrics = {
                "cagr": m.get("cagr"),
                "vol_annual": m.get("vol_annual"),
                "max_drawdown": m.get("max_drawdown"),
                "sharpe": m.get("sharpe"),
                "sortino": m.get("sortino"),
                "beta_portfolio": m.get("beta_portfolio"),
            }
            stress = data.get("stress_suite_results") or {}
            stress_status = stress.get("overall")
        except Exception as e:
            logger.warning(f"Не удалось прочитать {snap_10y} для {label}: {e}")

    if run_meta.exists():
        try:
            with open(run_meta, encoding="utf-8") as f:
                meta = json.load(f)
            client_fit = bool(meta.get("portfolio_valid", True))
        except Exception:
            pass

    # For Equal-Weight / Risk-Parity we may also have their own summary.json
    if summary_json.exists():
        try:
            with open(summary_json, encoding="utf-8") as f:
                s = json.load(f)
            if not metrics and s.get("metrics_10y"):
                m = s["metrics_10y"]
                metrics = {
                    "cagr": m.get("cagr"),
                    "vol_annual": m.get("vol_annual"),
                    "max_drawdown": m.get("max_drawdown"),
                    "sharpe": m.get("sharpe"),
                    "sortino": m.get("sortino"),
                    "beta_portfolio": m.get("beta_portfolio"),
                }
            if stress_status is None:
                stress_status = s.get("stress_status")
            if client_fit is None and "portfolio_valid" in s:
                client_fit = bool(s.get("portfolio_valid"))
        except Exception:
            pass

    return {
        "label": label,
        "metrics": metrics,
        "stress_status": stress_status,
        "client_fit": client_fit,
    }


def main() -> None:
    setup_logging()
    cfg = load_validated_config()
    root = Path(getattr(cfg, "output_dir_final", "Main portfolio"))
    project_root = Path(__file__).resolve().parent

    policy = _load_variant_summary(root, None, "Policy Portfolio")
    eq = _load_variant_summary(project_root, "equal-weight portfolio", "Equal-Weight Portfolio")
    rp = _load_variant_summary(project_root, "risk parity portfolio", "Risk Parity Portfolio")
    robust = _load_variant_summary(project_root, "robust scenario portfolio", "Robust Scenario Portfolio")

    comparison = {
        "policy": policy,
        "equal_weight": eq,
        "risk_parity": rp,
        "robust_scenario": robust,
    }

    out_json = root / "portfolio_comparison.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(comparison, f, indent=2, ensure_ascii=False)

    # Human-readable TXT table
    def _fmt(v, pct=False):
        if v is None:
            return "—"
        try:
            if pct:
                return f"{v:.1%}"
            return f"{v:.3f}"
        except Exception:
            return str(v)

    lines = [
        "Policy vs Equal-Weight vs Risk-Parity vs Robust Scenario",
        "=" * 70,
        "",
        "Columns:   CAGR | Vol | MaxDD | Sharpe | Sortino | Beta | Stress | Client-fit",
        "",
    ]
    for item in (policy, eq, rp, robust):
        m = item["metrics"] or {}
        line = (
            f"{item['label']:<22} "
            f"{_fmt(m.get('cagr'), pct=True):>8}  "
            f"{_fmt(m.get('vol_annual'), pct=True):>8}  "
            f"{_fmt(m.get('max_drawdown'), pct=True):>8}  "
            f"{_fmt(m.get('sharpe')):>7}  "
            f"{_fmt(m.get('sortino')):>7}  "
            f"{_fmt(m.get('beta_portfolio')):>7}  "
            f"{(item['stress_status'] or 'N/A'):>8}  "
            f"{('PASS' if item['client_fit'] else 'FAIL') if item['client_fit'] is not None else '—':>6}"
        )
        lines.append(line)

    out_txt = root / "portfolio_comparison.txt"
    with open(out_txt, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Comparison written to {out_json} and {out_txt}")


if __name__ == "__main__":
    main()

