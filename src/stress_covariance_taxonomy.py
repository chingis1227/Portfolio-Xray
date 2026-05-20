"""
Scenario-dependent stress covariance for RC_vol diagnostics (taxonomy_blend_v1).

Blends empirical monthly correlation with a block-structured target matrix keyed off
ETF/stock universe metadata. Does not affect scenario PnL (linear shock × betas).

See docs/docs/stress_testing_spec.md: synthetic stress covariance (taxonomy blend).
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import pandas as pd
import yaml

# Internal block ids (stable API for calibration tables)
BLOCK_EQ = "EQ"
BLOCK_CR = "CR"
BLOCK_ND = "ND"
BLOCK_TI = "TI"
BLOCK_CO = "CO"
BLOCK_CA = "CA"
BLOCK_GENERIC = "GENERIC"

# Diagnostic stress covariance taxonomy calibration (RC diagnostics only; not optimizer input).
STRESS_COV_CALIBRATION_VERSION = "calibrated_v1_assumptions"

LAMBDA_BLEND: dict[str, float] = {
    "equity_shock": 0.45,
    "credit_shock": 0.54,
    "liquidity_shock": 0.54,
    "recession_severe": 0.65,
    "rates_shock": 0.38,
    "inflation_stagflation": 0.44,
    "usd_shock": 0.42,
    "commodity_shock": 0.46,
}

RHO_DEFAULT_BETWEEN: dict[str, float] = {
    "equity_shock": 0.35,
    "credit_shock": 0.38,
    "liquidity_shock": 0.48,
    "recession_severe": 0.52,
    "rates_shock": 0.30,
    "inflation_stagflation": 0.36,
    "usd_shock": 0.34,
    "commodity_shock": 0.38,
}

# Within-block targets by scenario × block
RHO_WITHIN: dict[str, dict[str, float]] = {
    "equity_shock": {BLOCK_EQ: 0.86, BLOCK_CR: 0.74, BLOCK_ND: 0.62, BLOCK_TI: 0.64, BLOCK_CO: 0.72, BLOCK_CA: 0.18},
    "credit_shock": {BLOCK_EQ: 0.72, BLOCK_CR: 0.86, BLOCK_ND: 0.58, BLOCK_TI: 0.60, BLOCK_CO: 0.58, BLOCK_CA: 0.20},
    "liquidity_shock": {BLOCK_EQ: 0.88, BLOCK_CR: 0.86, BLOCK_ND: 0.70, BLOCK_TI: 0.72, BLOCK_CO: 0.78, BLOCK_CA: 0.22},
    "recession_severe": {BLOCK_EQ: 0.90, BLOCK_CR: 0.89, BLOCK_ND: 0.74, BLOCK_TI: 0.76, BLOCK_CO: 0.80, BLOCK_CA: 0.24},
    "rates_shock": {BLOCK_EQ: 0.58, BLOCK_CR: 0.56, BLOCK_ND: 0.78, BLOCK_TI: 0.76, BLOCK_CO: 0.52, BLOCK_CA: 0.16},
    "inflation_stagflation": {BLOCK_EQ: 0.68, BLOCK_CR: 0.63, BLOCK_ND: 0.66, BLOCK_TI: 0.72, BLOCK_CO: 0.74, BLOCK_CA: 0.18},
    "usd_shock": {BLOCK_EQ: 0.80, BLOCK_CR: 0.70, BLOCK_ND: 0.60, BLOCK_TI: 0.62, BLOCK_CO: 0.68, BLOCK_CA: 0.18},
    "commodity_shock": {BLOCK_EQ: 0.72, BLOCK_CR: 0.64, BLOCK_ND: 0.66, BLOCK_TI: 0.70, BLOCK_CO: 0.80, BLOCK_CA: 0.18},
}

# Explicit between-block overrides: canonical key = tuple(sorted((b1, b2)))
RHO_PAIR_OVERRIDES: dict[str, dict[tuple[str, str], float]] = {
    "equity_shock": {
        ("CR", "EQ"): 0.70,
        ("EQ", "ND"): -0.28,
        ("EQ", "TI"): -0.18,
        ("CO", "EQ"): 0.46,
        ("CR", "ND"): 0.40,
        ("ND", "TI"): 0.88,
        ("CO", "TI"): 0.42,
        ("CA", "CO"): 0.08,
        ("CA", "CR"): 0.08,
        ("CA", "EQ"): 0.08,
        ("CA", "ND"): 0.12,
        ("CA", "TI"): 0.12,
    },
    "credit_shock": {
        ("CR", "EQ"): 0.74,
        ("CR", "ND"): 0.48,
        ("ND", "TI"): 0.90,
        ("EQ", "ND"): 0.28,
        ("CO", "TI"): 0.38,
        ("CA", "CR"): 0.12,
        ("CA", "EQ"): 0.12,
    },
    "liquidity_shock": {
        ("CR", "EQ"): 0.82,
        ("EQ", "ND"): 0.48,
        ("CO", "EQ"): 0.62,
        ("CR", "ND"): 0.58,
        ("ND", "TI"): 0.86,
        ("CA", "CO"): 0.18,
        ("CA", "CR"): 0.18,
        ("CA", "EQ"): 0.18,
    },
    "recession_severe": {
        ("CR", "EQ"): 0.84,
        ("EQ", "ND"): 0.34,
        ("CO", "EQ"): 0.58,
        ("CR", "ND"): 0.60,
        ("ND", "TI"): 0.92,
        ("CO", "TI"): 0.50,
        ("CA", "CR"): 0.14,
        ("CA", "EQ"): 0.14,
    },
    "rates_shock": {
        ("ND", "TI"): 0.93,
        ("EQ", "ND"): -0.42,
        ("EQ", "TI"): -0.30,
        ("CR", "ND"): 0.52,
        ("CR", "EQ"): 0.35,
        ("CO", "TI"): 0.28,
        ("CO", "ND"): 0.12,
        ("CA", "CO"): 0.10,
        ("CA", "CR"): 0.10,
        ("CA", "EQ"): 0.10,
        ("CA", "ND"): 0.10,
        ("CA", "TI"): 0.10,
    },
    "inflation_stagflation": {
        ("ND", "TI"): 0.88,
        ("EQ", "ND"): -0.24,
        ("CR", "EQ"): -0.12,
        ("CO", "TI"): 0.64,
        ("CO", "EQ"): 0.44,
        ("CR", "ND"): 0.44,
        ("CO", "ND"): 0.22,
    },
    "usd_shock": {
        ("CR", "EQ"): 0.68,
        ("EQ", "ND"): -0.22,
        ("CO", "EQ"): -0.20,
        ("ND", "TI"): 0.86,
        ("CO", "TI"): 0.36,
        ("CA", "CO"): 0.10,
        ("CA", "CR"): 0.10,
        ("CA", "EQ"): 0.10,
    },
    "commodity_shock": {
        ("CO", "TI"): 0.68,
        ("CO", "EQ"): 0.52,
        ("CO", "ND"): 0.28,
        ("ND", "TI"): 0.86,
        ("EQ", "ND"): -0.18,
        ("CR", "EQ"): 0.38,
        ("CA", "CO"): 0.12,
    },
}

VOL_MULT_BLOCK: dict[str, dict[str, float]] = {
    "equity_shock": {BLOCK_EQ: 1.32, BLOCK_CR: 1.22, BLOCK_ND: 1.10, BLOCK_TI: 1.08, BLOCK_CO: 1.26, BLOCK_CA: 1.02},
    "credit_shock": {BLOCK_EQ: 1.18, BLOCK_CR: 1.48, BLOCK_ND: 1.14, BLOCK_TI: 1.10, BLOCK_CO: 1.14, BLOCK_CA: 1.03},
    "liquidity_shock": {BLOCK_EQ: 1.48, BLOCK_CR: 1.42, BLOCK_ND: 1.24, BLOCK_TI: 1.20, BLOCK_CO: 1.34, BLOCK_CA: 1.06},
    "recession_severe": {BLOCK_EQ: 1.55, BLOCK_CR: 1.50, BLOCK_ND: 1.30, BLOCK_TI: 1.26, BLOCK_CO: 1.40, BLOCK_CA: 1.08},
    "rates_shock": {BLOCK_EQ: 1.08, BLOCK_CR: 1.16, BLOCK_ND: 1.42, BLOCK_TI: 1.35, BLOCK_CO: 1.08, BLOCK_CA: 1.02},
    "inflation_stagflation": {BLOCK_EQ: 1.22, BLOCK_CR: 1.18, BLOCK_ND: 1.24, BLOCK_TI: 1.26, BLOCK_CO: 1.46, BLOCK_CA: 1.03},
    "usd_shock": {BLOCK_EQ: 1.20, BLOCK_CR: 1.16, BLOCK_ND: 1.12, BLOCK_TI: 1.10, BLOCK_CO: 1.30, BLOCK_CA: 1.02},
    "commodity_shock": {BLOCK_EQ: 1.18, BLOCK_CR: 1.14, BLOCK_ND: 1.16, BLOCK_TI: 1.18, BLOCK_CO: 1.52, BLOCK_CA: 1.03},
}

# Pairs echoed in stress output for calibration traceability (subset of RHO_PAIR_OVERRIDES).
KEY_RHO_TRACE_PAIRS: dict[str, list[tuple[str, str]]] = {
    "credit_shock": [("CR", "EQ")],
    "inflation_stagflation": [("CO", "TI")],
    "rates_shock": [("ND", "TI"), ("EQ", "ND")],
    "usd_shock": [("CO", "EQ")],
    "commodity_shock": [("CO", "TI"), ("CO", "EQ")],
}


def key_rho_overrides_used_for_scenario(scenario_id: str) -> dict[str, float]:
    """Compact trace: calibrated key between-block overrides present for `scenario_id`."""
    ov = RHO_PAIR_OVERRIDES.get(scenario_id) or {}
    out: dict[str, float] = {}
    for a, b in KEY_RHO_TRACE_PAIRS.get(scenario_id, []):
        k = _canonical_pair(a, b)
        if k in ov:
            out[f"{k[0]}_{k[1]}"] = round(float(ov[k]), 4)
    return out


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _canonical_pair(b1: str, b2: str) -> tuple[str, str]:
    return (b1, b2) if b1 <= b2 else (b2, b1)


@dataclass(frozen=True)
class TaxonomyResolution:
    ticker: str
    block: str
    source: str  # etf_universe | stock_universe | cash_proxy | unknown


def _normalize_ticker(t: str) -> str:
    return str(t).strip()


def _parse_universe_yaml(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    with path.open(encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    if isinstance(raw, list):
        return [x for x in raw if isinstance(x, dict)]
    return []


@lru_cache(maxsize=4)
def _load_combined_universe(
    etf_path: str,
    stock_path: str,
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    etf_records = _parse_universe_yaml(Path(etf_path))
    stock_records = _parse_universe_yaml(Path(stock_path))
    etf_by: dict[str, dict[str, Any]] = {}
    for row in etf_records:
        t = row.get("ticker")
        if t:
            etf_by[_normalize_ticker(str(t)).upper()] = row
    stock_by: dict[str, dict[str, Any]] = {}
    for row in stock_records:
        t = row.get("ticker")
        if t:
            stock_by[_normalize_ticker(str(t)).upper()] = row
    return etf_by, stock_by


def resolve_stress_asset_block(
    ticker: str,
    *,
    cash_proxy_ticker: str | None,
    etf_path: str | None = None,
    stock_path: str | None = None,
) -> TaxonomyResolution:
    """
    Map a portfolio ticker to a stress covariance block using ETF/stock universe rows.
    """
    t = _normalize_ticker(ticker)
    t_up = t.upper()
    cash_u = (cash_proxy_ticker or "").strip().upper()
    if cash_u and t_up == cash_u:
        return TaxonomyResolution(ticker=t, block=BLOCK_CA, source="cash_proxy")

    root = _project_root()
    ep = etf_path or str(root / "config" / "etf_universe.yml")
    sp = stock_path or str(root / "config" / "stock_universe.yml")
    etf_by, stock_by = _load_combined_universe(ep, sp)

    row = etf_by.get(t_up)
    if row is not None:
        return TaxonomyResolution(ticker=t, block=_block_from_etf_row(row, t_up), source="etf_universe")
    row2 = stock_by.get(t_up)
    if row2 is not None:
        return TaxonomyResolution(ticker=t, block=BLOCK_EQ, source="stock_universe")
    return TaxonomyResolution(ticker=t, block=BLOCK_EQ, source="unknown")


def _block_from_etf_row(row: Mapping[str, Any], t_up: str) -> str:
    asset_class = str(row.get("asset_class") or "").strip().lower()
    subtype = str(row.get("subtype") or "").strip().lower()
    main_rf = str(row.get("main_risk_factor") or "").strip().lower()
    credit_quality = str(row.get("credit_quality") or "").strip()
    risk_role = row.get("risk_role") or []
    if not isinstance(risk_role, (list, tuple)):
        risk_role = []
    risk_role_l = [str(x).strip().lower() for x in risk_role]

    if asset_class == "cash":
        return BLOCK_CA
    if asset_class == "commodity":
        return BLOCK_CO
    if asset_class in ("equity",):
        return BLOCK_EQ
    if asset_class == "alternative":
        st = subtype
        if st == "reit":
            return BLOCK_EQ
        if main_rf == "equity":
            return BLOCK_EQ
        if main_rf == "vix":
            return BLOCK_EQ
        if main_rf == "commodity":
            return BLOCK_CO
        return BLOCK_EQ
    if asset_class == "fixed_income":
        if subtype == "tips" or main_rf == "inflation":
            return BLOCK_TI
        if main_rf == "credit":
            return BLOCK_CR
        if subtype in (
            "high_yield",
            "corporate_ig",
            "em_debt",
            "bank_loan",
            "preferred",
            "floating_rate",
        ):
            return BLOCK_CR
        if credit_quality in ("HY", "EM_debt", "Junk"):
            return BLOCK_CR
        if subtype in ("t_bill", "ultra_short_bond") and "cash_like" in risk_role_l:
            return BLOCK_CA
        return BLOCK_ND
    return BLOCK_EQ


def build_target_correlation(
    blocks: list[str],
    scenario_id: str,
) -> np.ndarray:
    """Full n×n target correlation for ordered `blocks` (same order as cov columns)."""
    n = len(blocks)
    out = np.eye(n, dtype=float)
    sw = RHO_WITHIN.get(scenario_id) or {}
    dflt = RHO_DEFAULT_BETWEEN.get(scenario_id, 0.35)
    pairs = RHO_PAIR_OVERRIDES.get(scenario_id) or {}

    for i in range(n):
        for j in range(i + 1, n):
            bi, bj = blocks[i], blocks[j]
            if bi == bj:
                rho = float(sw.get(bi, sw.get(BLOCK_EQ, 0.65)))
            else:
                key = _canonical_pair(bi, bj)
                rho = float(pairs.get(key, dflt))
            out[i, j] = rho
            out[j, i] = rho
    np.fill_diagonal(out, 1.0)
    return out


def repair_correlation_matrix(corr: np.ndarray, *, eps: float = 1e-10) -> np.ndarray:
    """Symmetric PSD repair + unit diagonal."""
    c = (corr + corr.T) / 2.0
    w, v = np.linalg.eigh(c)
    w = np.maximum(w, eps)
    cn = (v * w) @ v.T
    d = np.sqrt(np.clip(np.diag(cn), eps, None))
    cn = cn / np.outer(d, d)
    np.fill_diagonal(cn, 1.0)
    return cn


def stress_covariance_taxonomy_blend(
    cov_base: pd.DataFrame,
    tickers: list[str],
    scenario_id: str,
    *,
    cash_proxy_ticker: str | None = None,
    etf_path: str | None = None,
    stock_path: str | None = None,
    lambda_blend: float | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """
    Return (stress_covariance, diagnostics).

    Blends Corr(cov_base) with block target correlation, then applies per-block
    volatility multipliers to the diagonal vols from cov_base.
    """
    tickers = list(tickers)
    n = len(tickers)
    if n == 0:
        return cov_base.copy(), {"error": "empty_tickers"}

    lam = float(lambda_blend if lambda_blend is not None else LAMBDA_BLEND.get(scenario_id, 0.45))
    vol_tab = VOL_MULT_BLOCK.get(scenario_id) or VOL_MULT_BLOCK["equity_shock"]

    resolutions = [
        resolve_stress_asset_block(t, cash_proxy_ticker=cash_proxy_ticker, etf_path=etf_path, stock_path=stock_path)
        for t in tickers
    ]
    blocks = [r.block for r in resolutions]
    missing = [r.ticker for r in resolutions if r.source == "unknown"]

    vals = cov_base.reindex(index=tickers, columns=tickers).values.astype(float)
    vol_base = np.sqrt(np.maximum(np.diag(vals), 1e-18))
    corr_base = np.eye(n, dtype=float)
    for i in range(n):
        for j in range(n):
            if vol_base[i] * vol_base[j] > 1e-18:
                corr_base[i, j] = vals[i, j] / (vol_base[i] * vol_base[j])
            else:
                corr_base[i, j] = 1.0 if i == j else 0.0
    np.fill_diagonal(corr_base, 1.0)

    c_target = build_target_correlation(blocks, scenario_id)
    c_blend = (1.0 - lam) * corr_base + lam * c_target
    c_blend = repair_correlation_matrix(c_blend)

    vol_mult = np.array(
        [float(vol_tab.get(blocks[i], vol_tab[BLOCK_EQ])) for i in range(n)],
        dtype=float,
    )
    vol_stress = vol_base * vol_mult
    cov_s = np.outer(vol_stress, vol_stress) * c_blend
    np.fill_diagonal(cov_s, vol_stress**2)

    df = pd.DataFrame(cov_s, index=tickers, columns=tickers)
    vol_mult_tab = {k: round(float(v), 4) for k, v in vol_tab.items()}
    diag = {
        "stress_cov_method": "taxonomy_blend_v1",
        "stress_cov_lambda": round(lam, 4),
        "stress_cov_calibration_version": STRESS_COV_CALIBRATION_VERSION,
        "taxonomy_coverage": {
            "missing_tickers": missing,
            "blocks_by_ticker": {tickers[i]: blocks[i] for i in range(n)},
        },
        "vol_mult_by_block": vol_mult_tab,
        "key_rho_overrides_used": key_rho_overrides_used_for_scenario(scenario_id),
    }
    return df, diag


__all__ = [
    "BLOCK_CA",
    "BLOCK_CO",
    "BLOCK_CR",
    "BLOCK_EQ",
    "BLOCK_GENERIC",
    "BLOCK_ND",
    "BLOCK_TI",
    "KEY_RHO_TRACE_PAIRS",
    "LAMBDA_BLEND",
    "RHO_DEFAULT_BETWEEN",
    "RHO_PAIR_OVERRIDES",
    "RHO_WITHIN",
    "STRESS_COV_CALIBRATION_VERSION",
    "VOL_MULT_BLOCK",
    "TaxonomyResolution",
    "build_target_correlation",
    "key_rho_overrides_used_for_scenario",
    "repair_correlation_matrix",
    "resolve_stress_asset_block",
    "stress_covariance_taxonomy_blend",
]
