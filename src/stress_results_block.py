"""Block 3.2 Stress Results builder — stress_results_v1.

Builds the product-facing Block 3.2 layer on top of the raw stress engine
evidence rows (scenario_results, historical_results, historical_episode_paths).

This module is intentionally free of direct circular imports with src.stress:
it consumes plain dicts produced by run_stress, not live stress-engine objects.

Session 02 (scaffold): envelope + empty per-scenario arrays.
Session 03: synthetic per-scenario rows + diagnosis_summary_en templates.
Session 04 adds: historical per-scenario rows + loss-contribution derivation.
Session 05: attach_stress_results_v1 wired from run_stress, run_report (post-enrichment), run_optimization.
"""
from __future__ import annotations

from typing import Any

from src.scenario_library import (
    HISTORICAL_SCENARIO_IDS,
    SCENARIO_LIBRARY_VERSION,
    SYNTHETIC_SCENARIO_IDS,
)
from src.stress_factors import get_factor_display_name

BLOCK_3_2_VERSION = "stress_results_v1"
_DIAGNOSIS_METHOD = "template_v1"

_LOSS_GATE_MODE_DIAGNOSTIC = "diagnostic"
_LOSS_GATE_MODE_MANDATE = "mandate"

_FACTOR_SHORT_TO_BETA: dict[str, str] = {
    "eq": "beta_eq",
    "rr": "beta_rr",
    "credit": "beta_credit",
    "inf": "beta_inf",
    "usd": "beta_usd",
    "cmd": "beta_cmd",
}

_SCENARIO_LABEL_OVERRIDES: dict[str, str] = {
    "equity_shock": "equity shock",
    "credit_shock": "credit shock",
    "rates_shock": "rates shock",
    "inflation_stagflation": "inflation / stagflation",
    "liquidity_shock": "liquidity shock",
    "usd_shock": "USD shock",
    "commodity_shock": "commodity shock",
    "recession_severe": "severe recession",
}

_EPISODE_LABEL_OVERRIDES: dict[str, str] = {
    "dotcom": "dot-com bust",
    "2008": "2008 financial crisis",
    "2020": "COVID-19 shock",
    "2022": "2022 inflation shock",
    "banking_2023": "2023 banking stress",
}

_HISTORICAL_RC_NOT_APPLICABLE_REASON = (
    "stressed_covariance_risk_contribution_is_synthetic_only"
)


def build_stress_results_v1(
    *,
    scenario_results: list[dict[str, Any]],
    historical_results: list[dict[str, Any]],
    historical_episode_paths: list[dict[str, Any]],
    stress_conclusions: dict[str, Any],
    loss_gate_mode: str,
    helped_assets_worst_synthetic: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build the Block 3.2 product layer from stress engine evidence dicts."""
    gate_mode = _normalize_gate_mode(loss_gate_mode)

    worst_synthetic = _select_worst_synthetic(scenario_results, stress_conclusions)
    worst_historical = _select_worst_historical(historical_results, stress_conclusions)
    worst_synthetic_id = (
        worst_synthetic.get("scenario_id") if isinstance(worst_synthetic, dict) else None
    )

    helped_assets = helped_assets_worst_synthetic
    if helped_assets is None and isinstance(worst_synthetic, dict):
        helped_assets = _derive_helped_assets_from_row(worst_synthetic)
    helped_assets = helped_assets or []

    synthetic_scenarios = _build_synthetic_scenarios(
        scenario_results,
        worst_synthetic_id=worst_synthetic_id,
        helped_assets_worst=helped_assets,
    )
    historical_episodes = _build_historical_episodes(
        historical_results,
        historical_episode_paths,
    )
    envelope = _build_envelope(
        worst_synthetic=worst_synthetic,
        worst_historical=worst_historical,
        helped_assets_worst_synthetic=helped_assets,
        synthetic_scenarios=synthetic_scenarios,
        historical_episodes=historical_episodes,
    )

    return {
        "version": BLOCK_3_2_VERSION,
        "loss_gate_mode": gate_mode,
        "diagnosis_method": _DIAGNOSIS_METHOD,
        "scenario_library": {
            "version": SCENARIO_LIBRARY_VERSION,
            "synthetic_ids": list(SYNTHETIC_SCENARIO_IDS),
            "historical_ids": list(HISTORICAL_SCENARIO_IDS),
        },
        "envelope": envelope,
        "synthetic_scenarios": synthetic_scenarios,
        "historical_episodes": historical_episodes,
    }


def attach_stress_results_v1(stress_report: dict[str, Any]) -> None:
    """Rebuild ``stress_results_v1`` on *stress_report* from current evidence rows (in-place)."""
    conclusions = stress_report.get("stress_conclusions")
    if not isinstance(conclusions, dict):
        conclusions = {}
    helped = conclusions.get("helped_assets_worst_scenario")
    stress_report["stress_results_v1"] = build_stress_results_v1(
        scenario_results=list(stress_report.get("scenario_results") or []),
        historical_results=list(stress_report.get("historical_results") or []),
        historical_episode_paths=list(stress_report.get("historical_episode_paths") or []),
        stress_conclusions=conclusions,
        loss_gate_mode=str(stress_report.get("loss_gate_mode") or _LOSS_GATE_MODE_MANDATE),
        helped_assets_worst_synthetic=helped if isinstance(helped, list) else None,
    )


def empty_stress_results_v1(
    reason: str = "no_data",
    *,
    loss_gate_mode: str = _LOSS_GATE_MODE_DIAGNOSTIC,
) -> dict[str, Any]:
    """Return a valid but empty stress_results_v1 block."""
    gate_mode = _normalize_gate_mode(loss_gate_mode)
    return {
        "version": BLOCK_3_2_VERSION,
        "loss_gate_mode": gate_mode,
        "diagnosis_method": _DIAGNOSIS_METHOD,
        "scenario_library": {
            "version": SCENARIO_LIBRARY_VERSION,
            "synthetic_ids": list(SYNTHETIC_SCENARIO_IDS),
            "historical_ids": list(HISTORICAL_SCENARIO_IDS),
        },
        "envelope": _empty_envelope(),
        "synthetic_scenarios": [],
        "historical_episodes": [],
        "error": reason,
    }


def _build_synthetic_scenarios(
    scenario_results: list[dict[str, Any]],
    *,
    worst_synthetic_id: str | None,
    helped_assets_worst: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    by_id = {
        str(row.get("scenario_id")): row
        for row in scenario_results
        if row.get("scenario_id") is not None
    }
    rows: list[dict[str, Any]] = []
    for scenario_id in SYNTHETIC_SCENARIO_IDS:
        evidence = by_id.get(scenario_id)
        is_worst = scenario_id == worst_synthetic_id
        rows.append(
            _build_synthetic_scenario_row(
                scenario_id,
                evidence,
                assets_helped=helped_assets_worst if is_worst else [],
            )
        )
    return rows


def _build_synthetic_scenario_row(
    scenario_id: str,
    evidence: dict[str, Any] | None,
    *,
    assets_helped: list[dict[str, Any]],
) -> dict[str, Any]:
    if not isinstance(evidence, dict):
        return _unavailable_synthetic_row(scenario_id)

    portfolio_loss = evidence.get("portfolio_pnl_pct")
    loss_contribution = _build_loss_contribution_synthetic(evidence)
    factor_attribution = _build_factor_attribution_synthetic(evidence)
    risk_contribution = _build_risk_contribution_synthetic(evidence)

    return {
        "scenario_id": scenario_id,
        "portfolio_loss_pct": portfolio_loss,
        "drawdown_pct": None,
        "availability": "available",
        "loss_contribution": loss_contribution,
        "factor_attribution": factor_attribution,
        "risk_contribution": risk_contribution,
        "assets_helped": list(assets_helped),
        "diagnosis_summary_en": _format_diagnosis_summary_en_synthetic(
            scenario_id=scenario_id,
            portfolio_loss_pct=portfolio_loss,
            top_factor_drivers=factor_attribution.get("top_factor_drivers") or [],
            top3_loss_assets=loss_contribution.get("top3_loss_assets") or [],
            assets_helped=assets_helped,
        ),
    }


def _unavailable_synthetic_row(scenario_id: str) -> dict[str, Any]:
    reason = "scenario_evidence_missing"
    unavailable = {"availability": "unavailable", "reason_en": reason}
    return {
        "scenario_id": scenario_id,
        "portfolio_loss_pct": None,
        "drawdown_pct": None,
        "availability": "unavailable",
        "reason_en": reason,
        "loss_contribution": dict(unavailable),
        "factor_attribution": dict(unavailable),
        "risk_contribution": {
            "availability": "not_applicable",
            "reason_en": reason,
        },
        "assets_helped": [],
        "diagnosis_summary_en": None,
    }


def _build_loss_contribution_synthetic(evidence: dict[str, Any]) -> dict[str, Any]:
    pnl_by_asset = evidence.get("pnl_by_asset_pct")
    top3 = evidence.get("top3_loss_assets")
    if not isinstance(pnl_by_asset, dict):
        pnl_by_asset = {}
    if not isinstance(top3, list):
        top3 = []

    assets_hurt = _normalize_top_loss_assets(top3)
    if not assets_hurt and pnl_by_asset:
        negatives = sorted(
            (
                (str(ticker), float(pnl))
                for ticker, pnl in pnl_by_asset.items()
                if isinstance(pnl, (int, float)) and float(pnl) < 0
            ),
            key=lambda item: (item[1], item[0]),
        )[:3]
        assets_hurt = [{"ticker": t, "pnl_pct": round(v, 4)} for t, v in negatives]

    if not pnl_by_asset and not assets_hurt:
        return {
            "availability": "unavailable",
            "reason_en": "asset_loss_contribution_missing",
            "pnl_by_asset_pct": {},
            "top3_loss_assets": [],
            "assets_hurt": [],
        }

    return {
        "availability": "available",
        "pnl_by_asset_pct": dict(pnl_by_asset),
        "top3_loss_assets": assets_hurt,
        "assets_hurt": assets_hurt,
    }


def _build_factor_attribution_synthetic(evidence: dict[str, Any]) -> dict[str, Any]:
    pnl_by_factor = evidence.get("pnl_by_factor_pct")
    if not isinstance(pnl_by_factor, dict) or not pnl_by_factor:
        return {
            "availability": "unavailable",
            "reason_en": "factor_attribution_missing",
            "pnl_by_factor_pct": {},
            "top_factor_drivers": [],
            "helped_factors": [],
        }

    top_loss, helped = _synthetic_factor_drivers(evidence)
    return {
        "availability": "available",
        "pnl_by_factor_pct": dict(pnl_by_factor),
        "top_factor_drivers": top_loss,
        "helped_factors": helped,
    }


def _build_risk_contribution_synthetic(evidence: dict[str, Any]) -> dict[str, Any]:
    top1_asset = evidence.get("top1_rc_asset")
    top1_pct = evidence.get("top1_rc_pct")
    top3_assets = evidence.get("top3_rc_assets")
    top3_sum = evidence.get("top3_rc_sum_pct")
    if top1_asset is None and not top3_assets:
        return {
            "availability": "unavailable",
            "reason_en": "risk_contribution_missing",
        }

    return {
        "availability": "available",
        "top1_rc_asset": top1_asset,
        "top1_rc_pct": top1_pct,
        "top3_rc_assets": list(top3_assets) if isinstance(top3_assets, list) else top3_assets,
        "top3_rc_sum_pct": top3_sum,
    }


def _synthetic_factor_drivers(
    scenario_row: dict[str, Any] | None,
    *,
    limit: int = 3,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Top loss and helping factor channels from a synthetic scenario row."""
    if not isinstance(scenario_row, dict):
        return [], []
    pnl_by_factor = scenario_row.get("pnl_by_factor_pct")
    if not isinstance(pnl_by_factor, dict) or not pnl_by_factor:
        return [], []
    return _factor_drivers_from_pnl_by_factor(pnl_by_factor, limit=limit)


def _derive_helped_assets_from_row(scenario_row: dict[str, Any]) -> list[dict[str, Any]]:
    by_asset = scenario_row.get("pnl_by_asset_pct") or {}
    if not isinstance(by_asset, dict):
        return []
    positive = sorted(
        (
            (str(ticker), float(pnl))
            for ticker, pnl in by_asset.items()
            if isinstance(pnl, (int, float)) and float(pnl) > 0
        ),
        key=lambda item: (-item[1], item[0]),
    )[:3]
    return [{"ticker": ticker, "pnl_pct": round(pnl, 4)} for ticker, pnl in positive]


def _normalize_top_loss_assets(top3: list[Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for item in top3:
        if not isinstance(item, dict):
            continue
        ticker = item.get("ticker")
        pnl = item.get("pnl_pct")
        if ticker is None or not isinstance(pnl, (int, float)):
            continue
        out.append({"ticker": str(ticker), "pnl_pct": round(float(pnl), 4)})
    return out


def _scenario_label_en(scenario_id: str) -> str:
    return _SCENARIO_LABEL_OVERRIDES.get(scenario_id, scenario_id.replace("_", " "))


def _format_pct_for_text(value: float | int | None) -> str | None:
    if not isinstance(value, (int, float)):
        return None
    return f"{float(value) * 100:.1f}%"


def _format_diagnosis_summary_en_synthetic(
    *,
    scenario_id: str,
    portfolio_loss_pct: Any,
    top_factor_drivers: list[dict[str, Any]],
    top3_loss_assets: list[dict[str, Any]],
    assets_helped: list[dict[str, Any]],
) -> str | None:
    loss_text = _format_pct_for_text(portfolio_loss_pct)
    if loss_text is None:
        return None

    label = _scenario_label_en(scenario_id)
    parts = [f"Under the {label} scenario, the portfolio would lose {loss_text}."]

    factor_names = [
        str(row.get("factor") or row.get("factor_short"))
        for row in top_factor_drivers[:3]
        if row.get("factor") or row.get("factor_short")
    ]
    if factor_names:
        if len(factor_names) == 1:
            factor_clause = f"{factor_names[0]} is the largest modeled loss driver"
        else:
            factor_clause = (
                f"{', '.join(factor_names[:-1])} and {factor_names[-1]} "
                "are the largest modeled loss drivers"
            )
        parts.append(f"Factor attribution points to {factor_clause}.")

    hurt_tickers = [str(row.get("ticker")) for row in top3_loss_assets[:3] if row.get("ticker")]
    if hurt_tickers:
        if len(hurt_tickers) == 1:
            asset_clause = f"{hurt_tickers[0]} contributes most at the asset level"
        else:
            asset_clause = (
                f"{', '.join(hurt_tickers[:-1])} and {hurt_tickers[-1]} "
                "contribute most at the asset level"
            )
        parts.append(f"{asset_clause}.")

    helped_tickers = [str(row.get("ticker")) for row in assets_helped[:3] if row.get("ticker")]
    if helped_tickers:
        if len(helped_tickers) == 1:
            offset_clause = f"{helped_tickers[0]} partially offsets the decline"
        else:
            offset_clause = (
                f"{', '.join(helped_tickers[:-1])} and {helped_tickers[-1]} "
                "partially offset the decline"
            )
        parts.append(f"{offset_clause}.")

    return " ".join(parts)


def _build_historical_episodes(
    historical_results: list[dict[str, Any]],
    historical_episode_paths: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    by_episode = {
        str(row.get("episode")): row
        for row in historical_results
        if row.get("episode") is not None
    }
    paths_by_episode = {
        str(path.get("episode")): path
        for path in historical_episode_paths
        if isinstance(path, dict) and path.get("episode") is not None
    }
    rows: list[dict[str, Any]] = []
    for episode_id in HISTORICAL_SCENARIO_IDS:
        evidence = by_episode.get(episode_id)
        path = paths_by_episode.get(episode_id)
        rows.append(
            _build_historical_episode_row(
                episode_id,
                evidence,
                path,
            )
        )
    return rows


def _build_historical_episode_row(
    episode_id: str,
    evidence: dict[str, Any] | None,
    path: dict[str, Any] | None,
) -> dict[str, Any]:
    if not isinstance(evidence, dict):
        return _unavailable_historical_row(episode_id, reason="episode_evidence_missing")

    portfolio_loss = evidence.get("pnl_real_episode")
    drawdown = evidence.get("max_dd")
    loss_contribution = _build_loss_contribution_historical(evidence, path)
    factor_attribution = _build_factor_attribution_historical(evidence)
    assets_helped = _derive_helped_assets_from_contrib(
        loss_contribution.get("pnl_by_asset_pct") or {}
    )

    row_available = portfolio_loss is not None or drawdown is not None
    return {
        "episode": episode_id,
        "portfolio_loss_pct": portfolio_loss,
        "drawdown_pct": drawdown,
        "availability": "available" if row_available else "unavailable",
        "reason_en": None if row_available else "episode_metrics_missing",
        "data_quality": evidence.get("data_quality"),
        "coverage_ratio": evidence.get("coverage_ratio"),
        "n_obs": evidence.get("n_obs"),
        "return_method": evidence.get("return_method"),
        "proxy_used": evidence.get("proxy_used"),
        "loss_contribution": loss_contribution,
        "factor_attribution": factor_attribution,
        "risk_contribution": {
            "availability": "not_applicable",
            "reason_en": _HISTORICAL_RC_NOT_APPLICABLE_REASON,
        },
        "assets_helped": assets_helped,
        "diagnosis_summary_en": _format_diagnosis_summary_en_historical(
            episode_id=episode_id,
            portfolio_loss_pct=portfolio_loss,
            drawdown_pct=drawdown,
            top_factor_drivers=factor_attribution.get("top_factor_drivers") or [],
            top3_loss_assets=loss_contribution.get("top3_loss_assets") or [],
            assets_helped=assets_helped,
        ),
    }


def _unavailable_historical_row(episode_id: str, *, reason: str) -> dict[str, Any]:
    unavailable = {"availability": "unavailable", "reason_en": reason}
    return {
        "episode": episode_id,
        "portfolio_loss_pct": None,
        "drawdown_pct": None,
        "availability": "unavailable",
        "reason_en": reason,
        "data_quality": None,
        "coverage_ratio": None,
        "n_obs": None,
        "return_method": None,
        "proxy_used": None,
        "loss_contribution": dict(unavailable),
        "factor_attribution": dict(unavailable),
        "risk_contribution": {
            "availability": "not_applicable",
            "reason_en": _HISTORICAL_RC_NOT_APPLICABLE_REASON,
        },
        "assets_helped": [],
        "diagnosis_summary_en": None,
    }


def _build_loss_contribution_historical(
    evidence: dict[str, Any],
    path: dict[str, Any] | None,
) -> dict[str, Any]:
    n_obs = evidence.get("n_obs")
    if not isinstance(path, dict):
        return {
            "availability": "unavailable",
            "reason_en": "insufficient_episode_data",
            "pnl_by_asset_pct": {},
            "top3_loss_assets": [],
            "assets_hurt": [],
        }
    if isinstance(n_obs, (int, float)) and int(n_obs) < 2:
        return {
            "availability": "unavailable",
            "reason_en": "insufficient_episode_data",
            "pnl_by_asset_pct": {},
            "top3_loss_assets": [],
            "assets_hurt": [],
        }

    contrib = path.get("asset_pnl_contrib_episode")
    if not isinstance(contrib, dict) or not contrib:
        return {
            "availability": "unavailable",
            "reason_en": "insufficient_episode_data",
            "pnl_by_asset_pct": {},
            "top3_loss_assets": [],
            "assets_hurt": [],
        }

    pnl_by_asset = {str(ticker): float(pnl) for ticker, pnl in contrib.items()}
    top3 = _top3_loss_assets_from_contrib(pnl_by_asset, path)
    assets_hurt = _normalize_top_loss_assets(top3)

    return {
        "availability": "available",
        "pnl_by_asset_pct": pnl_by_asset,
        "top3_loss_assets": assets_hurt,
        "assets_hurt": assets_hurt,
    }


def _top3_loss_assets_from_contrib(
    pnl_by_asset: dict[str, float],
    path: dict[str, Any],
) -> list[dict[str, Any]]:
    path_top = path.get("top_loss_assets_episode")
    if isinstance(path_top, list) and path_top:
        out: list[dict[str, Any]] = []
        for ticker in path_top[:3]:
            ticker_s = str(ticker)
            pnl = pnl_by_asset.get(ticker_s)
            if isinstance(pnl, (int, float)):
                out.append({"ticker": ticker_s, "pnl_pct": round(float(pnl), 4)})
        if out:
            return out

    negatives = sorted(
        (
            (str(ticker), float(pnl))
            for ticker, pnl in pnl_by_asset.items()
            if float(pnl) < 0
        ),
        key=lambda item: (item[1], item[0]),
    )[:3]
    return [{"ticker": t, "pnl_pct": round(v, 4)} for t, v in negatives]


def _derive_helped_assets_from_contrib(pnl_by_asset: dict[str, Any]) -> list[dict[str, Any]]:
    if not isinstance(pnl_by_asset, dict) or not pnl_by_asset:
        return []
    positive = sorted(
        (
            (str(ticker), float(pnl))
            for ticker, pnl in pnl_by_asset.items()
            if isinstance(pnl, (int, float)) and float(pnl) > 0
        ),
        key=lambda item: (-item[1], item[0]),
    )[:3]
    return [{"ticker": ticker, "pnl_pct": round(pnl, 4)} for ticker, pnl in positive]


def _build_factor_attribution_historical(evidence: dict[str, Any]) -> dict[str, Any]:
    pnl_by_factor = evidence.get("pnl_by_factor_pct")
    if not isinstance(pnl_by_factor, dict) or not pnl_by_factor:
        return {
            "availability": "unavailable",
            "reason_en": "factor_attribution_requires_report_enrichment",
            "pnl_by_factor_pct": {},
            "top_factor_drivers": [],
            "helped_factors": [],
        }

    top_loss, helped = _factor_drivers_from_pnl_by_factor(pnl_by_factor)
    return {
        "availability": "available",
        "pnl_by_factor_pct": dict(pnl_by_factor),
        "top_factor_drivers": top_loss,
        "helped_factors": helped,
    }


def _factor_driver_row_from_key(factor_key: str, pnl_pct: float) -> dict[str, Any]:
    beta_key = factor_key if factor_key.startswith("beta_") else _FACTOR_SHORT_TO_BETA.get(factor_key)
    factor_short = factor_key
    if beta_key and beta_key.startswith("beta_"):
        factor_short = beta_key.replace("beta_", "", 1)
    return {
        "factor_short": factor_short,
        "beta_key": beta_key,
        "factor": get_factor_display_name(beta_key) if beta_key else factor_key,
        "pnl_pct": round(float(pnl_pct), 4),
        "abs_pnl_pct": round(abs(float(pnl_pct)), 4),
        "direction": "loss" if pnl_pct < 0 else "gain" if pnl_pct > 0 else "flat",
    }


def _factor_drivers_from_pnl_by_factor(
    pnl_by_factor: dict[str, Any],
    *,
    limit: int = 3,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    negatives: list[dict[str, Any]] = []
    positives: list[dict[str, Any]] = []
    for factor_key, raw_pnl in pnl_by_factor.items():
        if not isinstance(raw_pnl, (int, float)):
            continue
        pnl = float(raw_pnl)
        row = _factor_driver_row_from_key(str(factor_key), pnl)
        if pnl < 0:
            negatives.append(row)
        elif pnl > 0:
            positives.append(row)

    negatives.sort(key=lambda row: (float(row["pnl_pct"]), str(row.get("factor_short") or "")))
    positives.sort(key=lambda row: (-float(row["pnl_pct"]), str(row.get("factor_short") or "")))

    top_loss = negatives[:limit]
    helped = positives[:limit]
    for idx, row in enumerate(top_loss, start=1):
        row["rank"] = idx
    for idx, row in enumerate(helped, start=1):
        row["rank"] = idx
    return top_loss, helped


def _episode_label_en(episode_id: str) -> str:
    return _EPISODE_LABEL_OVERRIDES.get(episode_id, episode_id.replace("_", " "))


def _format_diagnosis_summary_en_historical(
    *,
    episode_id: str,
    portfolio_loss_pct: Any,
    drawdown_pct: Any,
    top_factor_drivers: list[dict[str, Any]],
    top3_loss_assets: list[dict[str, Any]],
    assets_helped: list[dict[str, Any]],
) -> str | None:
    loss_text = _format_pct_for_text(portfolio_loss_pct)
    dd_text = _format_pct_for_text(drawdown_pct)
    if loss_text is None and dd_text is None:
        return None

    label = _episode_label_en(episode_id)
    if loss_text is not None and dd_text is not None:
        opener = (
            f"In a {label}-like episode, the portfolio return was {loss_text} "
            f"with a peak drawdown of {dd_text}."
        )
    elif loss_text is not None:
        opener = f"In a {label}-like episode, the portfolio return was {loss_text}."
    else:
        opener = f"In a {label}-like episode, the peak drawdown was {dd_text}."

    parts = [opener]

    factor_names = [
        str(row.get("factor") or row.get("factor_short"))
        for row in top_factor_drivers[:3]
        if row.get("factor") or row.get("factor_short")
    ]
    if factor_names:
        if len(factor_names) == 1:
            factor_clause = f"{factor_names[0]} is the largest modeled loss driver"
        else:
            factor_clause = (
                f"{', '.join(factor_names[:-1])} and {factor_names[-1]} "
                "are the largest modeled loss drivers"
            )
        parts.append(f"Model factor attribution points to {factor_clause}.")

    hurt_tickers = [str(row.get("ticker")) for row in top3_loss_assets[:3] if row.get("ticker")]
    if hurt_tickers:
        if len(hurt_tickers) == 1:
            asset_clause = f"{hurt_tickers[0]} contributed most to the realized loss"
        else:
            asset_clause = (
                f"{', '.join(hurt_tickers[:-1])} and {hurt_tickers[-1]} "
                "contributed most to the realized loss"
            )
        parts.append(f"{asset_clause}.")

    helped_tickers = [str(row.get("ticker")) for row in assets_helped[:3] if row.get("ticker")]
    if helped_tickers:
        if len(helped_tickers) == 1:
            offset_clause = f"{helped_tickers[0]} offset part of the decline"
        else:
            offset_clause = (
                f"{', '.join(helped_tickers[:-1])} and {helped_tickers[-1]} "
                "offset part of the decline"
            )
        parts.append(f"{offset_clause}.")

    return " ".join(parts)


def _build_envelope(
    *,
    worst_synthetic: dict[str, Any] | None,
    worst_historical: dict[str, Any] | None,
    helped_assets_worst_synthetic: list[dict[str, Any]],
    synthetic_scenarios: list[dict[str, Any]] | None = None,
    historical_episodes: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if worst_synthetic:
        ws_id = worst_synthetic.get("scenario_id")
        ws_loss = worst_synthetic.get("portfolio_pnl_pct")
    else:
        ws_id = None
        ws_loss = None

    if worst_historical:
        wh_id = worst_historical.get("episode")
        wh_dd = worst_historical.get("max_dd")
        wh_loss = worst_historical.get("pnl_real_episode")
    else:
        wh_id = None
        wh_dd = None
        wh_loss = None

    ws_top3: list[dict[str, Any]] = []
    ws_top_factors: list[dict[str, Any]] = []
    if synthetic_scenarios and ws_id:
        for row in synthetic_scenarios:
            if row.get("scenario_id") == ws_id:
                lc = row.get("loss_contribution") or {}
                fa = row.get("factor_attribution") or {}
                ws_top3 = list(lc.get("top3_loss_assets") or [])
                ws_top_factors = list(fa.get("top_factor_drivers") or [])
                break
    elif isinstance(worst_synthetic, dict):
        ws_top3 = _normalize_top_loss_assets(worst_synthetic.get("top3_loss_assets") or [])
        ws_top_factors, _ = _synthetic_factor_drivers(worst_synthetic)

    wh_top3: list[dict[str, Any]] = []
    if historical_episodes and wh_id:
        for row in historical_episodes:
            if row.get("episode") == wh_id:
                lc = row.get("loss_contribution") or {}
                wh_top3 = list(lc.get("top3_loss_assets") or [])
                break

    return {
        "worst_synthetic": {
            "scenario_id": ws_id,
            "portfolio_loss_pct": ws_loss,
            "top3_loss_assets": ws_top3,
            "top_factor_drivers": ws_top_factors,
            "helped_assets": helped_assets_worst_synthetic,
        },
        "worst_historical": {
            "episode": wh_id,
            "portfolio_loss_pct": wh_loss,
            "drawdown_pct": wh_dd,
            "top3_loss_assets": wh_top3,
        },
    }


def _empty_envelope() -> dict[str, Any]:
    return {
        "worst_synthetic": {
            "scenario_id": None,
            "portfolio_loss_pct": None,
            "top3_loss_assets": [],
            "top_factor_drivers": [],
            "helped_assets": [],
        },
        "worst_historical": {
            "episode": None,
            "portfolio_loss_pct": None,
            "drawdown_pct": None,
            "top3_loss_assets": [],
        },
    }


def _select_worst_synthetic(
    scenario_results: list[dict[str, Any]],
    stress_conclusions: dict[str, Any],
) -> dict[str, Any] | None:
    worst_id = (
        stress_conclusions.get("worst_synthetic_scenario", {}).get("scenario_id")
        if stress_conclusions
        else None
    )
    if worst_id:
        for row in scenario_results:
            if row.get("scenario_id") == worst_id:
                return row

    candidates = [r for r in scenario_results if r.get("portfolio_pnl_pct") is not None]
    if not candidates:
        return None
    return min(candidates, key=lambda r: r["portfolio_pnl_pct"])


def _select_worst_historical(
    historical_results: list[dict[str, Any]],
    stress_conclusions: dict[str, Any],
) -> dict[str, Any] | None:
    worst_id = (
        stress_conclusions.get("worst_historical_episode", {}).get("episode")
        if stress_conclusions
        else None
    )
    if worst_id:
        for row in historical_results:
            if row.get("episode") == worst_id:
                return row

    candidates = [r for r in historical_results if r.get("max_dd") is not None]
    if not candidates:
        return None
    return min(candidates, key=lambda r: r["max_dd"])


def _normalize_gate_mode(mode: str) -> str:
    if mode == _LOSS_GATE_MODE_DIAGNOSTIC:
        return _LOSS_GATE_MODE_DIAGNOSTIC
    return _LOSS_GATE_MODE_MANDATE
