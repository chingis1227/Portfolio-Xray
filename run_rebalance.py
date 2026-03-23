"""
Compute rebalance trades: current positions → target weights (from portfolio_weights.yml).

Usage:
  python run_rebalance.py --current current_positions.yml [--target path] [--nav NAV] [--threshold 2] [--min-trade 0.5]

If --threshold is set and max |Δweight| is below threshold (%), prints "Rebalance not needed" and exits.
Otherwise prints list of trades (ticker, direction, delta_weight, delta_pct, optional delta_amount).
"""
from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from src.config import load_config, WEIGHTS_FILENAME
from src.rebalance import Trade, compute_trades


def _load_weights(path: Path) -> dict[str, float]:
    if not path.is_file():
        return {}
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return {str(k): float(v) for k, v in data.items() if isinstance(k, str) and isinstance(v, (int, float))}


def main() -> None:
    parser = argparse.ArgumentParser(description="Rebalance: current positions → target weights → trades")
    parser.add_argument("--current", required=True, help="Path to YAML file: ticker → current weight (fraction)")
    parser.add_argument("--target", default=None, help="Path to target weights YAML (default: output_dir_final/portfolio_weights.yml)")
    parser.add_argument("--nav", type=float, default=None, help="Portfolio NAV (for delta_amount in trades)")
    parser.add_argument("--threshold", type=float, default=None, help="If max |Δweight|% < threshold, output 'Rebalance not needed'")
    parser.add_argument("--min-trade", type=float, default=None, help="Do not list trades with |Δweight|%% smaller than this")
    args = parser.parse_args()

    current_path = Path(args.current)
    current_weights = _load_weights(current_path)
    if not current_weights:
        print("No current weights loaded from %s" % current_path)
        return

    if args.target:
        target_path = Path(args.target)
    else:
        cfg = load_config()
        out_final = cfg.get("output_dir_final") or "Результаты оптимизации"
        base = Path(__file__).resolve().parent
        target_path = base / out_final / WEIGHTS_FILENAME
    target_weights = _load_weights(target_path)
    if not target_weights:
        print("No target weights loaded from %s" % target_path)
        return

    trades, needed = compute_trades(
        current_weights,
        target_weights,
        nav=args.nav,
        threshold_pct=args.threshold,
        min_trade_pct=args.min_trade,
    )

    if not needed:
        print("Rebalance not needed (within threshold).")
        return

    if not trades:
        print("No trades (all within min-trade or zero delta).")
        return

    print("Trades:")
    for t in trades:
        line = "  %s %s  Δw=%.4f (%.2f%%)" % (t.ticker, t.direction, t.delta_weight, t.delta_pct)
        if t.delta_amount is not None:
            line += "  amount=%.2f" % t.delta_amount
        print(line)


if __name__ == "__main__":
    main()
