"""
Core MVP historical stress replay — direct history only.

Stress Test Lab uses this module for per-position episode coverage and (from Session 2)
portfolio replay metadata. No ETF proxies, factor replay, or asset-class substitution.

Advanced/Legacy proxy waterfall: src/historical_stress_fallback.py (see core_mvp_historical_stress_replay_spec.md).
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml

from src.stress import HISTORICAL_EPISODES

CORE_MVP_HISTORICAL_STRESS_REPLAY_VERSION = "core_mvp_historical_stress_replay_v1"

DEFAULT_MIN_COVERAGE_RATIO = 0.45
MIN_EPISODE_OBSERVATIONS = 2

# Display labels aligned with src/stress_results_block.py _EPISODE_LABEL_OVERRIDES
CORE_MVP_HISTORICAL_SCENARIO_NAMES: dict[str, str] = {
    "dotcom": "dot-com bust",
    "2008": "2008 financial crisis",
    "2020": "COVID-19 shock",
    "2022": "2022 inflation shock",
    "banking_2023": "2023 banking stress",
}

CORE_MVP_HISTORICAL_SCENARIO_IDS: tuple[str, ...] = tuple(ep[0] for ep in HISTORICAL_EPISODES)

REPLAY_STATUS_FULL = "full_replay"
REPLAY_STATUS_PARTIAL = "partial_unavailable"
REPLAY_STATUS_UNAVAILABLE = "unavailable"

USER_NOTE_FULL_REPLAY_EN = (
    "Portfolio-level historical replay is available. "
    "All portfolio positions have usable direct data for this stress period."
)

USER_NOTE_PARTIAL_REPLAY_EN = (
    "This stress period cannot be fully replayed for the entire portfolio because some current "
    "positions did not exist or had no usable data at the time. Positions with usable direct "
    "history are shown separately. This is not a full replay of the current portfolio."
)

USER_NOTE_UNAVAILABLE_EN = (
    "This stress period cannot be replayed for the current portfolio: no positions have usable "
    "direct historical data in the episode window."
)

AVAILABLE_HISTORY_PARTIAL_CAVEAT_EN = (
    "These available-history assets can be reviewed separately, but this is not a full replay of "
    "the current portfolio."
)

LIMITATION_PARTIAL_EN = (
    "Full current-portfolio historical replay is not available for this stress period."
)

LIMITATION_UNAVAILABLE_EN = "No positions have usable direct history for this stress period."

_MAX_TICKERS_IN_DIAGNOSIS = 5


def _format_pct_for_text(value: float | int | None) -> str | None:
    if not isinstance(value, (int, float)) or not np.isfinite(float(value)):
        return None
    return f"{float(value) * 100:.1f}%"


def _ticker_list_phrase(positions: list[dict[str, Any]], *, key: str = "ticker") -> str | None:
    tickers: list[str] = []
    for row in positions:
        if not isinstance(row, dict):
            continue
        raw = row.get(key)
        if raw is None:
            continue
        tickers.append(str(raw).strip().upper())
    tickers = [t for t in tickers if t]
    if not tickers:
        return None
    shown = tickers[:_MAX_TICKERS_IN_DIAGNOSIS]
    if len(shown) == 1:
        return shown[0]
    if len(shown) == 2:
        return f"{shown[0]} and {shown[1]}"
    return f"{', '.join(shown[:-1])}, and {shown[-1]}"


def format_episode_diagnosis_summary_en(
    *,
    scenario_name: str,
    replay_status: str,
    direct_coverage_weight_pct: float,
    unavailable_weight_pct: float,
    unavailable_positions: list[dict[str, Any]],
    available_history_assets: dict[str, Any] | None,
    portfolio_loss_pct: float | None,
    drawdown_pct: float | None,
    user_note: str,
) -> str:
    """
    English episode narrative for Core MVP replay (coverage-first; no proxy language).
    """
    label = str(scenario_name or "historical stress period").strip()
    direct_text = f"{float(direct_coverage_weight_pct):.1f}%"
    unavail_text = f"{float(unavailable_weight_pct):.1f}%"

    if replay_status == REPLAY_STATUS_FULL:
        loss_text = _format_pct_for_text(portfolio_loss_pct)
        dd_text = _format_pct_for_text(drawdown_pct)
        if loss_text is not None and dd_text is not None:
            return (
                f"In the {label} stress period, direct history covers 100% of portfolio weight. "
                f"Portfolio return was {loss_text} with a peak drawdown of {dd_text}."
            )
        if loss_text is not None:
            return (
                f"In the {label} stress period, direct history covers 100% of portfolio weight. "
                f"Portfolio return was {loss_text}."
            )
        if dd_text is not None:
            return (
                f"In the {label} stress period, direct history covers 100% of portfolio weight. "
                f"Peak drawdown was {dd_text}."
            )
        return (
            f"In the {label} stress period, direct history covers 100% of portfolio weight. "
            f"{USER_NOTE_FULL_REPLAY_EN}"
        )

    coverage_opener = (
        f"In the {label} stress period, direct history covers {direct_text} of portfolio weight "
        f"({unavail_text} unavailable)."
    )
    parts = [coverage_opener.strip(), str(user_note).strip()]

    unavail_tickers = _ticker_list_phrase(unavailable_positions)
    if unavail_tickers:
        parts.append(f"Positions without usable direct history: {unavail_tickers}.")

    avail_block = available_history_assets if isinstance(available_history_assets, dict) else {}
    avail_positions = avail_block.get("positions")
    if isinstance(avail_positions, list) and avail_positions:
        avail_tickers = _ticker_list_phrase(avail_positions)
        if avail_tickers:
            parts.append(
                f"Positions with usable direct history (shown separately, not a full portfolio replay): "
                f"{avail_tickers}."
            )

    return " ".join(p for p in parts if p)


@dataclass(frozen=True)
class CoreMvpHistoricalReplayConfig:
    """Core MVP replay configuration (direct history only — no proxy fields)."""

    min_coverage_ratio: float = DEFAULT_MIN_COVERAGE_RATIO
    min_episode_observations: int = MIN_EPISODE_OBSERVATIONS


def default_core_mvp_replay_config() -> CoreMvpHistoricalReplayConfig:
    return CoreMvpHistoricalReplayConfig()


def historical_episode_windows() -> list[dict[str, str]]:
    """Episode registry for Core MVP replay (dates from src.stress.HISTORICAL_EPISODES)."""
    rows: list[dict[str, str]] = []
    for scenario_id, start, end in HISTORICAL_EPISODES:
        rows.append(
            {
                "scenario_id": scenario_id,
                "scenario_name": CORE_MVP_HISTORICAL_SCENARIO_NAMES.get(scenario_id, scenario_id),
                "episode_start": start,
                "episode_end": end,
            }
        )
    return rows


def episode_window_for_scenario(scenario_id: str) -> tuple[str, str] | None:
    for ep_id, start, end in HISTORICAL_EPISODES:
        if ep_id == scenario_id:
            return start, end
    return None


def _resolve_return_column(monthly_returns: pd.DataFrame, ticker: str) -> str | None:
    tu = str(ticker).strip().upper()
    for col in monthly_returns.columns:
        if str(col).strip().upper() == tu:
            return str(col)
    return None


def _normalized_monthly_index(monthly_returns: pd.DataFrame) -> pd.DataFrame:
    mr = monthly_returns.copy()
    mr.index = pd.to_datetime(mr.index).tz_localize(None)
    return mr


def _month_slice_valid_counts(
    monthly_returns: pd.DataFrame,
    ticker: str,
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> tuple[int, int]:
    col = _resolve_return_column(monthly_returns, ticker)
    if col is None:
        return 0, 0
    mr = _normalized_monthly_index(monthly_returns)
    window = mr.loc[start:end, col]
    n_expected = int(len(window))
    n_valid = int(window.notna().sum())
    return n_valid, max(n_expected, 0)


def _episode_return_series(
    monthly_returns: pd.DataFrame,
    ticker: str,
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> pd.Series:
    col = _resolve_return_column(monthly_returns, ticker)
    if col is None:
        return pd.Series(dtype=float)
    mr = _normalized_monthly_index(monthly_returns)
    return mr.loc[start:end, col].astype(float).dropna()


def compound_episode_simple_return(series: pd.Series) -> float | None:
    if series is None or len(series) < MIN_EPISODE_OBSERVATIONS:
        return None
    r = series.astype(float).values
    out = float(np.prod(1.0 + r) - 1.0)
    return out if np.isfinite(out) else None


def direct_history_coverage_ratio(
    monthly_returns: pd.DataFrame,
    ticker: str,
    episode_start: str,
    episode_end: str,
) -> float:
    """Share of expected monthly cells in the episode window with non-NaN returns for ticker."""
    start = pd.Timestamp(episode_start)
    end = pd.Timestamp(episode_end)
    n_valid, n_expected = _month_slice_valid_counts(monthly_returns, str(ticker).upper(), start, end)
    if n_expected <= 0:
        return 0.0
    return float(n_valid / n_expected)


def position_has_usable_direct_history(
    monthly_returns: pd.DataFrame,
    ticker: str,
    episode_start: str,
    episode_end: str,
    *,
    config: CoreMvpHistoricalReplayConfig | None = None,
) -> bool:
    """
    True when the position's own ticker has enough direct monthly history in the episode window.

    Core MVP: no proxies; unavailable when this returns False.
    """
    cfg = config or default_core_mvp_replay_config()
    if _resolve_return_column(monthly_returns, ticker) is None:
        return False
    start = pd.Timestamp(episode_start)
    end = pd.Timestamp(episode_end)
    n_valid, n_expected = _month_slice_valid_counts(monthly_returns, ticker, start, end)
    if n_valid < cfg.min_episode_observations:
        return False
    if n_expected <= 0:
        return False
    ratio = float(n_valid / n_expected)
    return ratio >= float(cfg.min_coverage_ratio) and np.isfinite(ratio)


def replay_status_from_weight_pcts(
    direct_coverage_weight_pct: float,
    unavailable_weight_pct: float,
) -> str:
    """Map weight coverage to Core MVP replay_status."""
    if unavailable_weight_pct <= 0.0 and direct_coverage_weight_pct > 0.0:
        return REPLAY_STATUS_FULL
    if unavailable_weight_pct >= 100.0 or direct_coverage_weight_pct <= 0.0:
        return REPLAY_STATUS_UNAVAILABLE
    return REPLAY_STATUS_PARTIAL


@lru_cache(maxsize=1)
def _universe_ticker_sets() -> tuple[frozenset[str], frozenset[str]]:
    root = Path(__file__).resolve().parents[1]
    etf: set[str] = set()
    stock: set[str] = set()
    for path, target in (
        (root / "config" / "etf_universe.yml", etf),
        (root / "config" / "stock_universe.yml", stock),
    ):
        if not path.is_file():
            continue
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            continue
        for row in data:
            if isinstance(row, dict) and isinstance(row.get("ticker"), str):
                target.add(row["ticker"].strip().upper())
    return frozenset(etf), frozenset(stock)


def resolve_instrument_type(ticker: str) -> str:
    """etf | stock | unknown — for unavailable_positions labeling only."""
    tu = str(ticker).strip().upper()
    etf_set, stock_set = _universe_ticker_sets()
    if tu in etf_set:
        return "etf"
    if tu in stock_set:
        return "stock"
    return "unknown"


def _risk_weight_vector(
    weights: dict[str, float],
    *,
    cash_proxy_ticker: str | None = None,
) -> dict[str, float]:
    cash_u = (cash_proxy_ticker or "").strip().upper()
    out: dict[str, float] = {}
    for t, w in weights.items():
        tu = str(t).strip().upper()
        if cash_u and tu == cash_u:
            continue
        fw = float(w)
        if fw > 0.0 and np.isfinite(fw):
            out[tu] = fw
    total = float(sum(out.values()))
    if total <= 0.0:
        return {}
    return {k: v / total for k, v in out.items()}


def _unavailable_reason_en(
    monthly_returns: pd.DataFrame,
    ticker: str,
    episode_start: str,
    episode_end: str,
    *,
    config: CoreMvpHistoricalReplayConfig | None = None,
) -> str:
    if _resolve_return_column(monthly_returns, ticker) is None:
        return "Ticker not present in aligned monthly returns panel for this run."
    if position_has_usable_direct_history(
        monthly_returns, ticker, episode_start, episode_end, config=config
    ):
        return "Direct history is available."
    cov = direct_history_coverage_ratio(monthly_returns, ticker, episode_start, episode_end)
    if cov <= 0.0:
        return "No usable direct monthly returns in the episode window (position may not have existed)."
    return (
        "Insufficient direct history coverage in the episode window "
        f"(coverage {cov:.1%} below required minimum)."
    )


def _portfolio_episode_metrics(
    monthly_returns: pd.DataFrame,
    risk_weights: dict[str, float],
    episode_start: str,
    episode_end: str,
) -> tuple[float | None, float | None, int]:
    """Aligned portfolio simple-return path: loss and max drawdown (ddof=1 not used on DD)."""
    col_by_ticker: dict[str, str] = {}
    for tu in risk_weights:
        col = _resolve_return_column(monthly_returns, tu)
        if col is not None:
            col_by_ticker[tu] = col
    if len(col_by_ticker) != len(risk_weights):
        return None, None, 0
    start = pd.Timestamp(episode_start)
    end = pd.Timestamp(episode_end)
    mr = _normalized_monthly_index(monthly_returns)
    cols = list(col_by_ticker.values())
    sub = mr.loc[start:end, cols].dropna(how="any")
    if len(sub) < MIN_EPISODE_OBSERVATIONS:
        return None, None, int(len(sub))
    w_vec = pd.Series(
        {col_by_ticker[tu]: risk_weights[tu] for tu in col_by_ticker},
        dtype=float,
    )
    port_ret = sub.dot(w_vec)
    port_eq = (1.0 + port_ret).cumprod()
    port_dd = port_eq / port_eq.cummax() - 1.0
    max_dd = float(port_dd.min())
    pnl = float(port_eq.iloc[-1] - 1.0) if len(port_eq) else None
    return (
        round(pnl, 4) if pnl is not None and np.isfinite(pnl) else None,
        round(max_dd, 4) if np.isfinite(max_dd) else None,
        int(len(sub)),
    )


def build_episode_replay(
    scenario_id: str,
    weights: dict[str, float],
    monthly_returns: pd.DataFrame,
    *,
    cash_proxy_ticker: str | None = None,
    config: CoreMvpHistoricalReplayConfig | None = None,
) -> dict[str, Any]:
    """Build one Core MVP historical episode replay row (direct history only)."""
    win = episode_window_for_scenario(scenario_id)
    scenario_name = CORE_MVP_HISTORICAL_SCENARIO_NAMES.get(scenario_id, scenario_id)
    if win is None:
        return {
            "scenario_id": scenario_id,
            "scenario_name": scenario_name,
            "replay_status": REPLAY_STATUS_UNAVAILABLE,
            "direct_coverage_weight_pct": 0.0,
            "unavailable_weight_pct": 100.0,
            "unavailable_positions": [],
            "available_history_assets": {
                "partial_replay_caveat_en": AVAILABLE_HISTORY_PARTIAL_CAVEAT_EN,
                "positions": [],
            },
            "portfolio_level_result_available": False,
            "user_note": USER_NOTE_UNAVAILABLE_EN,
            "limitation_summary": LIMITATION_UNAVAILABLE_EN,
            "diagnosis_summary_en": format_episode_diagnosis_summary_en(
                scenario_name=scenario_name,
                replay_status=REPLAY_STATUS_UNAVAILABLE,
                direct_coverage_weight_pct=0.0,
                unavailable_weight_pct=100.0,
                unavailable_positions=[],
                available_history_assets=None,
                portfolio_loss_pct=None,
                drawdown_pct=None,
                user_note=USER_NOTE_UNAVAILABLE_EN,
            ),
            "portfolio_loss_pct": None,
            "drawdown_pct": None,
            "episode_start": None,
            "episode_end": None,
        }

    episode_start, episode_end = win
    cfg = config or default_core_mvp_replay_config()
    risk_w = _risk_weight_vector(weights, cash_proxy_ticker=cash_proxy_ticker)
    if not risk_w:
        return {
            "scenario_id": scenario_id,
            "scenario_name": scenario_name,
            "episode_start": episode_start,
            "episode_end": episode_end,
            "replay_status": REPLAY_STATUS_UNAVAILABLE,
            "direct_coverage_weight_pct": 0.0,
            "unavailable_weight_pct": 100.0,
            "unavailable_positions": [],
            "available_history_assets": {
                "partial_replay_caveat_en": AVAILABLE_HISTORY_PARTIAL_CAVEAT_EN,
                "positions": [],
            },
            "portfolio_level_result_available": False,
            "user_note": USER_NOTE_UNAVAILABLE_EN,
            "limitation_summary": LIMITATION_UNAVAILABLE_EN,
            "diagnosis_summary_en": format_episode_diagnosis_summary_en(
                scenario_name=scenario_name,
                replay_status=REPLAY_STATUS_UNAVAILABLE,
                direct_coverage_weight_pct=0.0,
                unavailable_weight_pct=100.0,
                unavailable_positions=[],
                available_history_assets={
                    "partial_replay_caveat_en": AVAILABLE_HISTORY_PARTIAL_CAVEAT_EN,
                    "positions": [],
                },
                portfolio_loss_pct=None,
                drawdown_pct=None,
                user_note=USER_NOTE_UNAVAILABLE_EN,
            ),
            "portfolio_loss_pct": None,
            "drawdown_pct": None,
        }

    direct_w = 0.0
    unavailable_w = 0.0
    unavailable_positions: list[dict[str, Any]] = []
    available_positions: list[dict[str, Any]] = []

    for tu, w in risk_w.items():
        if position_has_usable_direct_history(
            monthly_returns, tu, episode_start, episode_end, config=cfg
        ):
            direct_w += w
            start_ts = pd.Timestamp(episode_start)
            end_ts = pd.Timestamp(episode_end)
            series = _episode_return_series(monthly_returns, tu, start_ts, end_ts)
            ep_ret = compound_episode_simple_return(series)
            available_positions.append(
                {
                    "ticker": tu,
                    "weight_pct": round(100.0 * w, 3),
                    "episode_return_pct": round(float(ep_ret), 4) if ep_ret is not None else None,
                    "method": "direct_history",
                }
            )
        else:
            unavailable_w += w
            unavailable_positions.append(
                {
                    "ticker": tu,
                    "instrument_type": resolve_instrument_type(tu),
                    "weight_pct": round(100.0 * w, 3),
                    "reason_en": _unavailable_reason_en(
                        monthly_returns, tu, episode_start, episode_end, config=cfg
                    ),
                }
            )

    direct_pct = round(100.0 * direct_w, 3)
    unavail_pct = round(100.0 * unavailable_w, 3)
    replay_status = replay_status_from_weight_pcts(direct_pct, unavail_pct)
    full_replay = replay_status == REPLAY_STATUS_FULL

    user_note = USER_NOTE_FULL_REPLAY_EN
    limitation_summary: str | None = None
    partial_caveat: str | None = None
    if replay_status == REPLAY_STATUS_PARTIAL:
        user_note = USER_NOTE_PARTIAL_REPLAY_EN
        limitation_summary = LIMITATION_PARTIAL_EN
        partial_caveat = AVAILABLE_HISTORY_PARTIAL_CAVEAT_EN
    elif replay_status == REPLAY_STATUS_UNAVAILABLE:
        user_note = USER_NOTE_UNAVAILABLE_EN
        limitation_summary = LIMITATION_UNAVAILABLE_EN
        partial_caveat = AVAILABLE_HISTORY_PARTIAL_CAVEAT_EN

    portfolio_loss_pct: float | None = None
    drawdown_pct: float | None = None
    if full_replay:
        portfolio_loss_pct, drawdown_pct, _ = _portfolio_episode_metrics(
            monthly_returns, risk_w, episode_start, episode_end
        )

    available_block: dict[str, Any] = {
        "partial_replay_caveat_en": partial_caveat,
        "positions": available_positions,
    }

    diagnosis_summary_en = format_episode_diagnosis_summary_en(
        scenario_name=scenario_name,
        replay_status=replay_status,
        direct_coverage_weight_pct=direct_pct,
        unavailable_weight_pct=unavail_pct,
        unavailable_positions=unavailable_positions,
        available_history_assets=available_block,
        portfolio_loss_pct=portfolio_loss_pct,
        drawdown_pct=drawdown_pct,
        user_note=user_note,
    )

    return {
        "scenario_id": scenario_id,
        "scenario_name": scenario_name,
        "episode_start": episode_start,
        "episode_end": episode_end,
        "replay_status": replay_status,
        "direct_coverage_weight_pct": direct_pct,
        "unavailable_weight_pct": unavail_pct,
        "unavailable_positions": unavailable_positions,
        "available_history_assets": available_block,
        "portfolio_level_result_available": full_replay,
        "user_note": user_note,
        "limitation_summary": limitation_summary,
        "diagnosis_summary_en": diagnosis_summary_en,
        "portfolio_loss_pct": portfolio_loss_pct,
        "drawdown_pct": drawdown_pct,
    }


def build_historical_stress_replay_v1(
    weights: dict[str, float],
    monthly_returns: pd.DataFrame,
    *,
    cash_proxy_ticker: str | None = None,
    config: CoreMvpHistoricalReplayConfig | None = None,
) -> dict[str, Any]:
    """Top-level Core MVP historical replay block for stress_report.json."""
    episodes = [
        build_episode_replay(
            scenario_id,
            weights,
            monthly_returns,
            cash_proxy_ticker=cash_proxy_ticker,
            config=config,
        )
        for scenario_id in CORE_MVP_HISTORICAL_SCENARIO_IDS
    ]
    return {
        "version": CORE_MVP_HISTORICAL_STRESS_REPLAY_VERSION,
        "policy": "direct_history_only",
        "episodes": episodes,
    }


def attach_core_mvp_historical_stress_replay_v1(
    stress_report: dict[str, Any],
    *,
    weights: dict[str, float],
    monthly_returns: pd.DataFrame,
    cash_proxy_ticker: str | None = None,
    config: CoreMvpHistoricalReplayConfig | None = None,
) -> None:
    """Attach ``historical_stress_replay_v1`` on *stress_report* (in-place)."""
    stress_report["historical_stress_replay_v1"] = build_historical_stress_replay_v1(
        weights,
        monthly_returns,
        cash_proxy_ticker=cash_proxy_ticker,
        config=config,
    )


def replay_episodes_by_scenario_id(
    historical_stress_replay_v1: dict[str, Any] | None,
) -> dict[str, dict[str, Any]]:
    if not isinstance(historical_stress_replay_v1, dict):
        return {}
    episodes = historical_stress_replay_v1.get("episodes")
    if not isinstance(episodes, list):
        return {}
    out: dict[str, dict[str, Any]] = {}
    for row in episodes:
        if isinstance(row, dict) and row.get("scenario_id"):
            out[str(row["scenario_id"])] = row
    return out


__all__ = [
    "CORE_MVP_HISTORICAL_SCENARIO_IDS",
    "CORE_MVP_HISTORICAL_SCENARIO_NAMES",
    "CORE_MVP_HISTORICAL_STRESS_REPLAY_VERSION",
    "CoreMvpHistoricalReplayConfig",
    "DEFAULT_MIN_COVERAGE_RATIO",
    "MIN_EPISODE_OBSERVATIONS",
    "REPLAY_STATUS_FULL",
    "REPLAY_STATUS_PARTIAL",
    "REPLAY_STATUS_UNAVAILABLE",
    "USER_NOTE_FULL_REPLAY_EN",
    "USER_NOTE_PARTIAL_REPLAY_EN",
    "USER_NOTE_UNAVAILABLE_EN",
    "AVAILABLE_HISTORY_PARTIAL_CAVEAT_EN",
    "LIMITATION_PARTIAL_EN",
    "LIMITATION_UNAVAILABLE_EN",
    "format_episode_diagnosis_summary_en",
    "attach_core_mvp_historical_stress_replay_v1",
    "build_episode_replay",
    "build_historical_stress_replay_v1",
    "replay_episodes_by_scenario_id",
    "compound_episode_simple_return",
    "default_core_mvp_replay_config",
    "direct_history_coverage_ratio",
    "episode_window_for_scenario",
    "historical_episode_windows",
    "position_has_usable_direct_history",
    "replay_status_from_weight_pcts",
    "resolve_instrument_type",
]
