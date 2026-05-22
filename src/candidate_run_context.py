"""
Shared run context for Candidate Portfolio Factory (orchestration only).

One ``load_monthly_data_shared`` and invariant factor/scenario inputs per factory run.
Does not change formulas, optimizers, or stress scenario definitions.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from src.config import (
    load_assets_metadata,
    portfolio_total_tickers,
    resolve_cash_and_rf,
    resolve_local_benchmarks,
)
from src.config_schema import PortfolioConfig
from src.data_loader import (
    MonthlyDataResult,
    load_daily_asset_returns_shared,
    load_monthly_data_shared,
)
from src.robust_mv_lambda_resolve import resolve_robust_mv_lambda_for_baseline
from src.stress_factors import (
    FACTOR_WEEKS_10Y,
    FACTOR_WEEKS_5Y,
    build_factor_matrix,
    compute_asset_factor_betas_from_daily_returns,
)
from src.utils import logger

SCHEMA_VERSION = "candidate_run_context_v1"


@dataclass(frozen=True)
class FactoryFactorStressInputs:
    """
    Factor and scenario inputs invariant across candidates in one factory run.

    Asset-level betas are still aggregated per candidate weights inside the report pipeline.
    """

    daily_asset_returns_for_betas: pd.DataFrame
    asset_betas_5y_universe: pd.DataFrame
    asset_betas_10y_universe: pd.DataFrame
    recession_factor_returns: pd.DataFrame
    scenario_episode_factor_returns: pd.DataFrame
    beta_source: str | None
    beta_setup_reasons: tuple[str, ...] = ()


@dataclass
class CandidateRunContext:
    """Shared data and factor cache for one factory execution (fast / standard modes)."""

    cfg: PortfolioConfig
    project_root: Path
    monthly_data: MonthlyDataResult
    assets_meta: dict[str, dict[str, Any]]
    cash_proxy_ticker: str
    rf_source: str
    local_benchmark_map: dict[str, str]
    report_tickers: list[str]
    primary_window: int
    robust_mv_lambda: float | None = None
    robust_mv_lambda_resolution: str | None = None
    factor_stress: FactoryFactorStressInputs | None = None
    no_cache: bool = False
    schema_version: str = SCHEMA_VERSION

    @property
    def monthly_returns(self) -> pd.DataFrame:
        return self.monthly_data.monthly_returns

    @property
    def analysis_end_str(self) -> str:
        return self.monthly_data.analysis_end_str

    @property
    def analysis_end(self) -> pd.Timestamp:
        return self.monthly_data.analysis_end


def build_factory_factor_stress_inputs(
    *,
    cfg: PortfolioConfig,
    monthly_data: MonthlyDataResult,
    assets_meta: dict[str, dict[str, Any]],
    cash_proxy_ticker: str,
    local_benchmark_map: dict[str, str],
    report_tickers: list[str],
    no_cache: bool = False,
) -> FactoryFactorStressInputs | None:
    """
    Preload daily returns and factor matrices shared by all candidate reports in a factory run.
    """
    analysis_end_str = monthly_data.analysis_end_str
    benchmark_base_ticker = cfg.benchmark_base_ticker
    beta_tickers = list(report_tickers)
    beta_daily_tickers = list(
        dict.fromkeys(list(beta_tickers) + [benchmark_base_ticker])
    )
    beta_setup_reasons: list[str] = []
    beta_source: str | None = None
    asset_betas_5y = pd.DataFrame()
    asset_betas_10y = pd.DataFrame()
    recession_factor_returns = pd.DataFrame()
    scenario_episode_factor_returns = pd.DataFrame()

    try:
        daily_asset_returns, _cash = load_daily_asset_returns_shared(
            tickers=beta_daily_tickers,
            benchmark_base_ticker=benchmark_base_ticker,
            cash_proxy_ticker=cash_proxy_ticker,
            investor_currency=cfg.investor_currency,
            windows_months=cfg.windows_months,
            assets_meta=assets_meta,
            daily_cache_key=monthly_data.daily_cache_key,
            analysis_end=monthly_data.analysis_end,
            no_cache=no_cache,
            local_benchmark_map=local_benchmark_map,
            data_provider=getattr(cfg, "market_data_provider", None),
        )
        if daily_asset_returns.empty:
            beta_setup_reasons.append("cached_daily_returns_empty")
            daily_asset_returns = pd.DataFrame()
        else:
            asset_betas_5y = compute_asset_factor_betas_from_daily_returns(
                daily_asset_returns,
                analysis_end_str,
                FACTOR_WEEKS_5Y,
                asset_tickers=beta_tickers,
                equity_factor_ticker=benchmark_base_ticker,
            )
            asset_betas_10y = compute_asset_factor_betas_from_daily_returns(
                daily_asset_returns,
                analysis_end_str,
                FACTOR_WEEKS_10Y,
                asset_tickers=beta_tickers,
                equity_factor_ticker=benchmark_base_ticker,
            )
            if not asset_betas_5y.empty:
                beta_source = "cached_daily_returns_weekly_ols"
            else:
                beta_setup_reasons.append("cached_daily_returns_weekly_ols_no_aligned_betas")
    except Exception as exc:
        beta_setup_reasons.append(f"cached_daily_returns_weekly_ols_error:{exc}")
        daily_asset_returns = pd.DataFrame()

    try:
        recession_factor_returns = build_factor_matrix("2007-01-01", analysis_end_str)
    except Exception as exc:
        logger.warning(
            "Factory shared context: recession factor calibration failed: %s",
            exc,
        )
    try:
        scenario_episode_factor_returns = build_factor_matrix(
            "1990-01-01",
            analysis_end_str,
            require_complete_rows=False,
        )
    except Exception as exc:
        logger.warning(
            "Factory shared context: long-window factor matrix failed: %s",
            exc,
        )

    if daily_asset_returns.empty and not beta_setup_reasons:
        return None

    return FactoryFactorStressInputs(
        daily_asset_returns_for_betas=daily_asset_returns,
        asset_betas_5y_universe=asset_betas_5y,
        asset_betas_10y_universe=asset_betas_10y,
        recession_factor_returns=recession_factor_returns,
        scenario_episode_factor_returns=scenario_episode_factor_returns,
        beta_source=beta_source,
        beta_setup_reasons=tuple(beta_setup_reasons),
    )


def prepare_candidate_run_context(
    cfg: PortfolioConfig,
    *,
    project_root: Path,
    no_cache: bool = False,
    preload_factor_stress: bool = True,
) -> CandidateRunContext:
    """
    Load monthly panel once and optionally build invariant factor/scenario inputs.
    """
    assets_meta = load_assets_metadata()
    cash_proxy_ticker, rf_source = resolve_cash_and_rf(cfg)
    local_benchmark_map = resolve_local_benchmarks(
        cfg.tickers,
        cfg.local_benchmark_map or {},
        base_benchmark=cfg.benchmark_base_ticker,
    )
    monthly_data = load_monthly_data_shared(
        tickers=cfg.tickers,
        benchmark_base_ticker=cfg.benchmark_base_ticker,
        cash_proxy_ticker=cash_proxy_ticker,
        rf_source=rf_source,
        investor_currency=cfg.investor_currency,
        windows_months=cfg.windows_months,
        assets_meta=assets_meta,
        no_cache=no_cache,
        local_benchmark_map=local_benchmark_map,
        returns_frequency=getattr(cfg, "returns_frequency", None),
        data_provider=getattr(cfg, "market_data_provider", None),
    )
    primary_window = cfg.windows_months[-1] if cfg.windows_months else 120
    lam, lam_src = resolve_robust_mv_lambda_for_baseline(
        project_root=project_root,
        cli_lambda=None,
    )
    uniform = {t: 1.0 / len(cfg.tickers) for t in cfg.tickers} if cfg.tickers else {}
    report_tickers = portfolio_total_tickers(
        cfg.tickers,
        uniform,
        cash_proxy_ticker,
    )
    factor_stress = None
    if preload_factor_stress:
        factor_stress = build_factory_factor_stress_inputs(
            cfg=cfg,
            monthly_data=monthly_data,
            assets_meta=assets_meta,
            cash_proxy_ticker=cash_proxy_ticker,
            local_benchmark_map=local_benchmark_map,
            report_tickers=report_tickers,
            no_cache=no_cache,
        )
    return CandidateRunContext(
        cfg=cfg,
        project_root=project_root,
        monthly_data=monthly_data,
        assets_meta=assets_meta,
        cash_proxy_ticker=cash_proxy_ticker,
        rf_source=rf_source,
        local_benchmark_map=local_benchmark_map,
        report_tickers=report_tickers,
        primary_window=primary_window,
        robust_mv_lambda=lam,
        robust_mv_lambda_resolution=lam_src,
        factor_stress=factor_stress,
        no_cache=no_cache,
    )


def asset_betas_for_candidate_weights(
    factory_inputs: FactoryFactorStressInputs,
    *,
    beta_tickers: list[str],
    benchmark_base_ticker: str,
    analysis_end_str: str,
) -> tuple[pd.DataFrame, pd.DataFrame, str | None]:
    """
    Slice universe asset betas to the tickers used for one candidate report.
    """
    if (
        not factory_inputs.asset_betas_5y_universe.empty
        and not factory_inputs.asset_betas_10y_universe.empty
    ):
        b5 = factory_inputs.asset_betas_5y_universe.reindex(beta_tickers).dropna(how="all")
        b10 = factory_inputs.asset_betas_10y_universe.reindex(beta_tickers).dropna(how="all")
        if not b5.empty:
            return b5, b10, factory_inputs.beta_source

    daily = factory_inputs.daily_asset_returns_for_betas
    if daily.empty:
        return pd.DataFrame(), pd.DataFrame(), None
    b5 = compute_asset_factor_betas_from_daily_returns(
        daily,
        analysis_end_str,
        FACTOR_WEEKS_5Y,
        asset_tickers=beta_tickers,
        equity_factor_ticker=benchmark_base_ticker,
    )
    b10 = compute_asset_factor_betas_from_daily_returns(
        daily,
        analysis_end_str,
        FACTOR_WEEKS_10Y,
        asset_tickers=beta_tickers,
        equity_factor_ticker=benchmark_base_ticker,
    )
    source = factory_inputs.beta_source
    if not b5.empty and source is None:
        source = "cached_daily_returns_weekly_ols"
    return b5, b10, source
