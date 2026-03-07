"""
Web UI for Portfolio Config — run separately from main project.

Usage:
    pip install flask
    python config_ui/app.py

Then open http://localhost:5000 in browser.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

from flask import Flask, render_template, request, jsonify, send_file
import yaml

app = Flask(__name__)

# Path to main config
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "config.yml"

# Default values (aligned with config_schema; UI form uses benchmark_base_ticker, rf_source)
DEFAULTS = {
    "investor_currency": "USD",
    "initial_investable_amount": 1000,
    "liquidity_need": 0,
    "risk_free_source": None,
    "cash_proxy_ticker": None,
    "benchmark_base_ticker": "SPY",
    "beta_local_mapping": None,
    "allow_leverage": False,
    "allow_short_selling": False,
    "min_acceptable_return": None,
    "target_nominal_return_annual": None,
    "target_vol_annual": None,
    "target_max_drawdown_pct": None,
    "horizon_years": None,
    "rc_asset_cap_pct": None,
    "rc_block_targets": None,
    "max_single_security_weight_pct": None,
    "min_single_security_weight_pct": None,
    "windows_months": [36, 60, 120],
    "coverage_threshold": 0.90,
    "output_dir": "output",
}

CURRENCY_BENCHMARKS = {
    "USD": "SPY",
    "EUR": "VGK",
    "JPY": "EWJ",
    "CHF": "EWL",
}


def _normalize_loaded_config(raw: dict) -> dict:
    """Map canonical config keys to names used by the UI form (backward compatible)."""
    out = dict(raw)
    if out.get("benchmark_base_ticker") is None and out.get("base_benchmark_ticker") is not None:
        out["benchmark_base_ticker"] = out["base_benchmark_ticker"]
    if out.get("rf_source") is None and out.get("risk_free_source") is not None:
        out["rf_source"] = out["risk_free_source"]
    if out.get("local_benchmark_map") is None and out.get("beta_local_mapping") is not None:
        out["local_benchmark_map"] = out["beta_local_mapping"]
    return out


def load_current_config() -> dict:
    """Load current config.yml if exists. Supports canonical keys (base_benchmark_ticker, etc.)."""
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}
            return _normalize_loaded_config(raw)
    return {}


def parse_percent(val: str | None) -> float | None:
    """Parse percent string to decimal."""
    if not val or val.strip() == "":
        return None
    val = val.strip()
    if val.endswith("%"):
        return float(val[:-1]) / 100
    return float(val)


def parse_float(val: str | None) -> float | None:
    """Parse float string."""
    if not val or val.strip() == "":
        return None
    return float(val.strip())


def parse_int(val: str | None) -> int | None:
    """Parse int string."""
    if not val or val.strip() == "":
        return None
    return int(val.strip())


@app.route("/")
def index():
    """Main config form page."""
    current = load_current_config()
    
    # Merge with defaults
    config = {**DEFAULTS, **current}
    
    # Parse tickers and weights
    tickers = config.get("tickers", [])
    weights = config.get("weights", {})
    
    # Create ticker-weight pairs for template
    ticker_weights = []
    for t in tickers:
        w = weights.get(t, 0)
        ticker_weights.append({"ticker": t, "weight": w})
    
    return render_template(
        "config_form.html",
        config=config,
        ticker_weights=ticker_weights,
        currency_benchmarks=CURRENCY_BENCHMARKS,
    )


@app.route("/generate", methods=["POST"])
def generate_config():
    """Generate config.yml from form data."""
    data = request.form
    
    # Parse tickers and weights
    tickers = []
    weights = {}
    
    ticker_entries = data.getlist("ticker[]")
    weight_entries = data.getlist("weight[]")
    
    for t, w in zip(ticker_entries, weight_entries):
        t = t.strip().upper()
        if t:
            tickers.append(t)
            w_val = parse_percent(w)
            if w_val is not None:
                weights[t] = w_val
    
    # Build config dict
    config = {
        "investor_currency": data.get("investor_currency", "USD"),
        "initial_investable_amount": parse_float(data.get("initial_investable_amount")) or 1000,
        "liquidity_need": parse_float(data.get("liquidity_need")) or 0,
        "tickers": tickers,
        "weights": weights,
        "benchmark_base_ticker": data.get("benchmark_base_ticker", "SPY"),
        "allow_leverage": data.get("allow_leverage") == "true",
        "allow_short_selling": data.get("allow_short_selling") == "true",
        "min_acceptable_return": parse_percent(data.get("min_acceptable_return")),
        "target_nominal_return_annual": parse_percent(data.get("target_nominal_return_annual")),
        "target_vol_annual": parse_percent(data.get("target_vol_annual")),
        "target_max_drawdown_pct": parse_percent(data.get("target_max_drawdown_pct")),
        "horizon_years": parse_float(data.get("horizon_years")),
        "rc_asset_cap_pct": parse_percent(data.get("rc_asset_cap_pct")),
        "max_single_security_weight_pct": parse_percent(data.get("max_single_security_weight_pct")),
        "min_single_security_weight_pct": parse_percent(data.get("min_single_security_weight_pct")),
        "windows_months": [36, 60, 120],
        "coverage_threshold": parse_percent(data.get("coverage_threshold")) or 0.90,
        "output_dir": data.get("output_dir", "output"),
    }
    
    # Generate YAML content
    yaml_content = generate_yaml_with_comments(config)
    
    return jsonify({
        "success": True,
        "yaml": yaml_content,
    })


@app.route("/save", methods=["POST"])
def save_config():
    """Save config to config.yml file."""
    data = request.json
    yaml_content = data.get("yaml", "")
    
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        f.write(yaml_content)
    
    return jsonify({"success": True, "path": str(CONFIG_PATH)})


def generate_yaml_with_comments(config: dict) -> str:
    """Generate YAML with nice comments."""
    lines = []
    
    lines.append("# =============================================================================")
    lines.append("# Portfolio Metrics Standard — Main Configuration")
    lines.append("# Generated by Config UI")
    lines.append("# =============================================================================")
    lines.append("")
    
    lines.append("# =============================================================================")
    lines.append("# SECTION 1: CORE SETTINGS")
    lines.append("# =============================================================================")
    lines.append("")
    lines.append(f"investor_currency: {config['investor_currency']}")
    lines.append(f"initial_investable_amount: {config['initial_investable_amount']}")
    lines.append(f"liquidity_need: {config['liquidity_need']}")
    lines.append("")
    
    lines.append("# =============================================================================")
    lines.append("# SECTION 2: PORTFOLIO TICKERS AND WEIGHTS")
    lines.append("# =============================================================================")
    lines.append("")
    lines.append("tickers:")
    for t in config["tickers"]:
        lines.append(f"  - {t}")
    lines.append("")
    lines.append("weights:")
    for t, w in config["weights"].items():
        lines.append(f"  {t}: {w}")
    lines.append("")
    
    lines.append("# =============================================================================")
    lines.append("# SECTION 3: BENCHMARK AND RISK-FREE")
    lines.append("# =============================================================================")
    lines.append("")
    lines.append(f"benchmark_base_ticker: {config['benchmark_base_ticker']}")
    lines.append("")
    
    lines.append("# =============================================================================")
    lines.append("# SECTION 4: PORTFOLIO ASSUMPTIONS AND TARGETS")
    lines.append("# =============================================================================")
    lines.append("")
    lines.append(f"allow_leverage: {str(config['allow_leverage']).lower()}")
    lines.append(f"allow_short_selling: {str(config['allow_short_selling']).lower()}")
    lines.append(f"min_acceptable_return: {config['min_acceptable_return'] if config['min_acceptable_return'] is not None else 'null'}")
    lines.append(f"target_nominal_return_annual: {config['target_nominal_return_annual'] if config['target_nominal_return_annual'] is not None else 'null'}")
    lines.append(f"target_vol_annual: {config['target_vol_annual'] if config['target_vol_annual'] is not None else 'null'}")
    lines.append(f"target_max_drawdown_pct: {config['target_max_drawdown_pct'] if config['target_max_drawdown_pct'] is not None else 'null'}")
    lines.append(f"horizon_years: {config['horizon_years'] if config['horizon_years'] is not None else 'null'}")
    lines.append("")
    
    lines.append("# =============================================================================")
    lines.append("# SECTION 5: OPTIMIZATION CONSTRAINTS")
    lines.append("# =============================================================================")
    lines.append("")
    lines.append(f"rc_asset_cap_pct: {config['rc_asset_cap_pct'] if config['rc_asset_cap_pct'] is not None else 'null'}")
    lines.append("rc_block_targets: null")
    lines.append(f"max_single_security_weight_pct: {config['max_single_security_weight_pct'] if config['max_single_security_weight_pct'] is not None else 'null'}")
    lines.append(f"min_single_security_weight_pct: {config['min_single_security_weight_pct'] if config['min_single_security_weight_pct'] is not None else 'null'}")
    lines.append("")
    
    lines.append("# =============================================================================")
    lines.append("# SECTION 6: ANALYSIS SETTINGS")
    lines.append("# =============================================================================")
    lines.append("")
    lines.append(f"windows_months: {config['windows_months']}")
    lines.append(f"coverage_threshold: {config['coverage_threshold']}")
    lines.append(f"output_dir: {config['output_dir']}")
    
    return "\n".join(lines)


if __name__ == "__main__":
    print("=" * 60)
    print("Portfolio Config UI")
    print("=" * 60)
    print(f"Config file: {CONFIG_PATH}")
    print()
    print("Open in browser: http://localhost:5000")
    print("Press Ctrl+C to stop")
    print("=" * 60)
    app.run(debug=True, port=5000)
