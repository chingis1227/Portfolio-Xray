"""
Web UI for Portfolio Config — run separately from main project.

Usage:
    pip install flask
    python config_ui/app.py

Then open http://localhost:5000 in browser.

Flow: set parameters in the form → Save config.yml (writes to config.yml) →
optionally Run optimization (runs run_optimization.py using current config).
Same config file and same code as when running from the command line.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Ensure project root is on path for src.client_profiles
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import subprocess

from flask import Flask, render_template, request, jsonify, send_file
import yaml

from src.client_profiles import apply_profile_to_config
from src.config import WEIGHTS_FILENAME, load_blocks_universe
from src.config_schema import ConfigValidationError, validate_config

app = Flask(__name__)

CONFIG_PATH = PROJECT_ROOT / "config.yml"

# Default values (aligned with config_schema; UI form uses benchmark_base_ticker, rf_source)
DEFAULTS = {
    "investor_currency": "USD",
    "initial_investable_amount": 1000,
    "liquidity_need": 0,
    "liquidity_need_months": 0,
    "monthly_expenses": 0,
    "portfolio_value": None,
    "cash_policy": "allowed_for_scaling",
    "client_profile": None,
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
    "N_rc": 3,
    "growth_core_candidates": ["VOO", "VT", "VTI"],
    "donor_shift_mode": "proportional",
    "blocks": {"Growth": [], "Growth_HY": ["JNK", "HYG"], "Growth_EM_debt": [], "Duration": [], "Inflation": []},
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
    if out.get("max_single_security_weight_pct") is None and out.get("max_single_asset_weight_pct") is not None:
        out["max_single_security_weight_pct"] = out["max_single_asset_weight_pct"]
    if out.get("min_single_security_weight_pct") is None and out.get("min_single_asset_weight_pct") is not None:
        out["min_single_security_weight_pct"] = out["min_single_asset_weight_pct"]
    if "blocks" not in out or not isinstance(out.get("blocks"), dict):
        out["blocks"] = {"Growth": [], "Growth_HY": [], "Growth_EM_debt": [], "Duration": [], "Inflation": []}
    if out["blocks"].get("Growth_HY") is None:
        out["blocks"]["Growth_HY"] = []
    if out["blocks"].get("Growth_EM_debt") is None:
        out["blocks"]["Growth_EM_debt"] = []
    return out


def load_current_config() -> dict:
    """Load current config.yml if exists. If config has no weights, load from portfolio_weights.yml."""
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}
        if not raw.get("weights"):
            weights_path = PROJECT_ROOT / WEIGHTS_FILENAME
            if weights_path.is_file():
                with open(weights_path, encoding="utf-8") as wf:
                    file_weights = yaml.safe_load(wf) or {}
                if isinstance(file_weights, dict):
                    raw["weights"] = {k: v for k, v in file_weights.items() if isinstance(v, (int, float))}
        return _normalize_loaded_config(raw)
    return {}


def load_client_profiles_reminder() -> list[dict]:
    """Load client_profiles.yml and return a short list for the reminder table (name, metrics, block ranges)."""
    path = PROJECT_ROOT / "config" / "client_profiles.yml"
    if not path.is_file():
        return []
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    profiles = data.get("profiles") or {}
    out = []
    for pid, p in profiles.items():
        if not isinstance(p, dict):
            continue
        rb = p.get("risk_budget") or {}
        def _r(spec, key="min_pct", key2="max_pct"):
            if not isinstance(spec, dict):
                return "—"
            a, b = spec.get(key), spec.get(key2)
            if a is not None and b is not None:
                return f"{a}–{b}%"
            return "—"
        out.append({
            "id": pid,
            "name": p.get("name", pid.replace("_", " ").title()),
            "return_range": _r(p.get("target_return_annual")),
            "vol_range": _r(p.get("target_vol_annual")),
            "max_dd": str(p.get("max_drawdown_pct", "—")),
            "growth_range": _r(rb.get("Growth")),
            "duration_range": _r(rb.get("Duration")),
            "inflation_range": _r(rb.get("Inflation")),
        })
    return out


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
    # Apply profile defaults (target return, vol, max_dd, rc_block_targets) so form shows profile midpoints
    current = apply_profile_to_config(current)
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
    
    client_profiles_reminder = load_client_profiles_reminder()
    return render_template(
        "config_form.html",
        config=config,
        ticker_weights=ticker_weights,
        currency_benchmarks=CURRENCY_BENCHMARKS,
        client_profiles_reminder=client_profiles_reminder,
    )


def _parse_growth_core_candidates(val: str | None) -> list[str]:
    """Parse comma-separated tickers to list."""
    if not val or not val.strip():
        return ["VOO", "VT"]
    return [t.strip().upper() for t in val.split(",") if t.strip()]


@app.route("/generate", methods=["POST"])
def generate_config():
    """Generate config.yml from form data."""
    data = request.form
    current = load_current_config()
    
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
        "liquidity_need_months": (parse_float(data.get("liquidity_need_months")) or 0),
        "monthly_expenses": parse_float(data.get("monthly_expenses")) if data.get("monthly_expenses") not in (None, "") else 0,
        "portfolio_value": parse_float(data.get("portfolio_value")) if data.get("portfolio_value") not in (None, "") else None,
        "cash_policy": data.get("cash_policy", "allowed_for_scaling") or "allowed_for_scaling",
        "client_profile": data.get("client_profile") or None,
        "tickers": tickers,
        "weights": weights,
        "benchmark_base_ticker": data.get("benchmark_base_ticker", "SPY"),
        "risk_free_source": data.get("risk_free_source") or current.get("risk_free_source") or current.get("rf_source"),
        "cash_proxy_ticker": data.get("cash_proxy_ticker") or current.get("cash_proxy_ticker"),
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
        "N_rc": parse_int(data.get("N_rc")) if data.get("N_rc") not in (None, "") else 3,
        "growth_core_candidates": _parse_growth_core_candidates(data.get("growth_core_candidates")),
        "donor_shift_mode": data.get("donor_shift_mode", "proportional") or "proportional",
        "windows_months": [36, 60, 120],
        "coverage_threshold": parse_percent(data.get("coverage_threshold")) or 0.90,
        "output_dir": data.get("output_dir", "output"),
    }
    config["blocks"] = current.get("blocks") or {"Growth": [], "Duration": [], "Inflation": []}
    
    # Generate YAML content
    yaml_content = generate_yaml_with_comments(config)
    
    return jsonify({
        "success": True,
        "yaml": yaml_content,
    })


@app.route("/save", methods=["POST"])
def save_config():
    """Save config to config.yml file. Validates with same rules as run_report/run_optimization."""
    data = request.json
    yaml_content = data.get("yaml", "")

    try:
        parsed = yaml.safe_load(yaml_content) or {}
    except yaml.YAMLError as e:
        return jsonify({"success": False, "error": f"Неверный YAML: {e}"})

    parsed = apply_profile_to_config(parsed)
    blocks_universe = load_blocks_universe(config_path=CONFIG_PATH)
    try:
        validate_config(parsed, blocks_universe=blocks_universe)
    except ConfigValidationError as e:
        return jsonify({"success": False, "error": str(e)})

    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        f.write(yaml_content)

    return jsonify({"success": True, "path": str(CONFIG_PATH)})


# Timeout for optimization run (seconds)
OPTIMIZATION_TIMEOUT = 600


@app.route("/run-optimization", methods=["POST"])
def run_optimization():
    """
    Run portfolio optimization using current config.yml.
    Expects config to be already saved. Returns stdout/stderr and exit code.
    """
    run_script = PROJECT_ROOT / "run_optimization.py"
    if not run_script.is_file():
        return jsonify({
            "success": False,
            "error": "run_optimization.py not found in project root",
            "stdout": "",
            "stderr": "",
            "exit_code": -1,
        })

    try:
        result = subprocess.run(
            [sys.executable, str(run_script)],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=OPTIMIZATION_TIMEOUT,
            env={**os.environ},
        )
        return jsonify({
            "success": result.returncode == 0,
            "stdout": result.stdout or "",
            "stderr": result.stderr or "",
            "exit_code": result.returncode,
        })
    except subprocess.TimeoutExpired:
        return jsonify({
            "success": False,
            "error": f"Optimization timed out after {OPTIMIZATION_TIMEOUT} seconds",
            "stdout": "",
            "stderr": "",
            "exit_code": -1,
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "stdout": "",
            "stderr": "",
            "exit_code": -1,
        })


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
    lines.append(f"liquidity_need: {config.get('liquidity_need', 0)}")
    lines.append("")
    lines.append("# ---------- Liquidity (life floor); target_vol_annual used for vol scaling ----------")
    lines.append(f"liquidity_need_months: {config.get('liquidity_need_months', 0)}")
    lines.append(f"monthly_expenses: {config.get('monthly_expenses', 0)}")
    pv = config.get("portfolio_value")
    lines.append(f"portfolio_value: {pv if pv is not None else 'null'}")
    lines.append("# cash_policy: allowed_for_scaling | required_floor | prohibited")
    lines.append(f"cash_policy: {config.get('cash_policy', 'allowed_for_scaling')}")
    lines.append("")
    
    lines.append("# =============================================================================")
    lines.append("# SECTION 2: PORTFOLIO TICKERS AND WEIGHTS")
    lines.append("# =============================================================================")
    lines.append("")
    lines.append("tickers:")
    for t in config["tickers"]:
        lines.append(f"  - {t}")
    blocks = config.get("blocks") or {"Growth": [], "Growth_HY": [], "Growth_EM_debt": [], "Duration": [], "Inflation": []}
    lines.append("blocks:")
    for block_name in ("Growth", "Growth_HY", "Growth_EM_debt", "Duration", "Inflation"):
        tickers_in_block = blocks.get(block_name, [])
        lines.append(f"  {block_name}: {tickers_in_block}")
    lines.append("")
    if config.get("weights"):
        lines.append("weights:")
        for t, w in config["weights"].items():
            lines.append(f"  {t}: {w}")
    else:
        lines.append("weights: {}")
    lines.append("")
    
    lines.append("# =============================================================================")
    lines.append("# SECTION 3: BENCHMARK AND RISK-FREE (cash_proxy_ticker from currency if not set)")
    lines.append("# =============================================================================")
    lines.append("")
    if config.get("risk_free_source"):
        lines.append(f"risk_free_source: {config['risk_free_source']}")
    if config.get("cash_proxy_ticker"):
        lines.append(f"cash_proxy_ticker: {config['cash_proxy_ticker']}")
    lines.append(f"base_benchmark_ticker: {config['benchmark_base_ticker']}")
    lines.append("")
    
    lines.append("# =============================================================================")
    lines.append("# SECTION 4: PORTFOLIO ASSUMPTIONS AND TARGETS")
    lines.append("# =============================================================================")
    lines.append("# client_profile: optional. ultra_conservative | conservative | balanced | growth | aggressive")
    lines.append(f"client_profile: {config.get('client_profile') if config.get('client_profile') else 'null'}")
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
    lines.append("# Alpha-shift (when cash_policy = prohibited and vol > target_vol_annual)")
    lines.append(f"N_rc: {config.get('N_rc', 3)}")
    lines.append(f"growth_core_candidates: {config.get('growth_core_candidates', ['VOO', 'VT'])}")
    lines.append(f"donor_shift_mode: {config.get('donor_shift_mode', 'proportional')}")
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
