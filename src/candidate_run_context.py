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
    get_mar_from_config,
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
from src.metrics_asset import asset_metrics_one_window
from src.returns_frequency import (
    normalize_returns_frequency,
    per_period_eff_from_annual_simple,
    periods_per_year as periods_per_year_for,
)
from src.risk_contrib import cov_matrix_monthly
from src.robust_mv_lambda_resolve import resolve_robust_mv_lambda_for_baseline
from src.stress import (
    PreparedSyntheticStressInputs,
    build_prepared_synthetic_stress_inputs,
    prepared_synthetic_stress_usable,
)
from src.stress_factors import (
    FACTOR_COLUMN_ORDER,
    FACTOR_WEEKS_10Y,
    FACTOR_WEEKS_5Y,
    PortfolioFactorWeeklyFrames,
    build_factor_matrix,
    build_portfolio_factor_weekly_frames,
    compute_asset_factor_betas_from_daily_returns,
    portfolio_factor_betas,
    weekly_factor_frames_cover_tickers,
)
from src.utils import coverage_ratio, logger
from src.windows import slice_window, truncate_to_analysis_end

SCHEMA_VERSION = "candidate_run_context_v5"
REVIEW_RUN_CONTEXT_SCHEMA = "review_run_context_v1"
_REVIEW_MACRO_PANEL_MEMORY_CACHE: dict[tuple[str, int], tuple[pd.DataFrame, dict[str, Any]]] = {}


def clear_review_macro_panel_memory_cache() -> None:
    """Clear process-local review macro panel cache; primarily useful for tests."""

    _REVIEW_MACRO_PANEL_MEMORY_CACHE.clear()


def _copy_macro_panel_cache_value(value: tuple[pd.DataFrame, dict[str, Any]]) -> tuple[pd.DataFrame, dict[str, Any]]:
    panel, meta = value
    copied_panel = panel.copy(deep=True)
    copied_panel.attrs = dict(getattr(panel, "attrs", {}) or {})
    return copied_panel, dict(meta or {})

# Re-export for factory/report callers
FactoryWeeklyFactorFrames = PortfolioFactorWeeklyFrames


@dataclass(frozen=True)
class FactoryFactorStressInputs:
    """
    Factor and scenario inputs invariant across candidates in one factory run.

    Asset-level betas are still aggregated per candidate weights inside the report pipeline.
    """

    daily_asset_returns_for_betas: pd.DataFrame
    cash_returns_daily: pd.Series
    asset_betas_5y_universe: pd.DataFrame
    asset_betas_10y_universe: pd.DataFrame
    asset_betas_5y_extended_universe: pd.DataFrame
    asset_betas_10y_extended_universe: pd.DataFrame
    recession_factor_returns: pd.DataFrame
    scenario_episode_factor_returns: pd.DataFrame
    beta_source: str | None
    beta_setup_reasons: tuple[str, ...] = ()
    weekly_factor_frames: PortfolioFactorWeeklyFrames | None = None


@dataclass(frozen=True)
class FactoryInvariantMetrics:
    """
    Asset metrics, return correlations, and stress base covariance for one factory run.

    Computed on ``report_tickers`` (full config universe + cash proxy). Candidate reports
    slice or reindex; RC_vol and portfolio-level metrics remain per candidate.
    """

    asset_metrics_all: tuple[list[dict], ...]
    correlation_by_window: dict[int, pd.DataFrame]
    stress_cov_base: pd.DataFrame
    stress_cov_asset_cols: tuple[str, ...]
    windows_months: tuple[int, ...]
    universe_tickers: tuple[str, ...]


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
    invariant_metrics: FactoryInvariantMetrics | None = None
    prepared_synthetic_stress: PreparedSyntheticStressInputs | None = None
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


@dataclass
class ReviewRunContext:
    """
    Shared review-run context for portfolio-first ``core_fast`` orchestration.

    Wraps one ``CandidateRunContext`` (monthly/daily/factor weekly frames) and
    reserves slots for review-wide caches filled in later Wave 2 sessions.
    """

    factory_context: CandidateRunContext
    macro_panel: pd.DataFrame | None = None
    macro_panel_meta: dict[str, Any] | None = None
    schema_version: str = REVIEW_RUN_CONTEXT_SCHEMA

    @property
    def cfg(self) -> PortfolioConfig:
        return self.factory_context.cfg

    @property
    def project_root(self) -> Path:
        return self.factory_context.project_root

    @property
    def monthly_data(self) -> MonthlyDataResult:
        return self.factory_context.monthly_data

    @property
    def monthly_returns(self) -> pd.DataFrame:
        return self.factory_context.monthly_returns

    @property
    def analysis_end_str(self) -> str:
        return self.factory_context.analysis_end_str

    @property
    def analysis_end(self) -> pd.Timestamp:
        return self.factory_context.analysis_end

    @property
    def factor_stress(self) -> FactoryFactorStressInputs | None:
        return self.factory_context.factor_stress

    @property
    def invariant_metrics(self) -> FactoryInvariantMetrics | None:
        return self.factory_context.invariant_metrics

    @property
    def prepared_synthetic_stress(self) -> PreparedSyntheticStressInputs | None:
        return self.factory_context.prepared_synthetic_stress

    @property
    def weekly_factor_frames(self) -> PortfolioFactorWeeklyFrames | None:
        fs = self.factory_context.factor_stress
        return fs.weekly_factor_frames if fs is not None else None

    @property
    def weekly_asset_returns(self) -> pd.DataFrame | None:
        frames = self.weekly_factor_frames
        if frames is None or frames.asset_weekly.empty:
            return None
        return frames.asset_weekly

    @property
    def no_cache(self) -> bool:
        return self.factory_context.no_cache


def coerce_factory_run_context(
    run_context: CandidateRunContext | ReviewRunContext | None,
) -> CandidateRunContext | None:
    """Normalize review or factory context for report/factory entrypoints."""
    if run_context is None:
        return None
    if isinstance(run_context, ReviewRunContext):
        return run_context.factory_context
    return run_context


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
    asset_betas_5y_extended = pd.DataFrame()
    asset_betas_10y_extended = pd.DataFrame()
    cash_returns_daily = pd.Series(dtype=float)
    recession_factor_returns = pd.DataFrame()
    scenario_episode_factor_returns = pd.DataFrame()

    try:
        daily_asset_returns, cash_returns_daily = load_daily_asset_returns_shared(
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
            asset_betas_5y_extended = compute_asset_factor_betas_from_daily_returns(
                daily_asset_returns,
                analysis_end_str,
                FACTOR_WEEKS_5Y,
                factor_columns=FACTOR_COLUMN_ORDER,
                asset_tickers=beta_tickers,
                equity_factor_ticker=benchmark_base_ticker,
            )
            asset_betas_10y_extended = compute_asset_factor_betas_from_daily_returns(
                daily_asset_returns,
                analysis_end_str,
                FACTOR_WEEKS_10Y,
                factor_columns=FACTOR_COLUMN_ORDER,
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
        cash_returns_daily = pd.Series(dtype=float)

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

    weekly_factor_frames: PortfolioFactorWeeklyFrames | None = None
    if not daily_asset_returns.empty:
        weekly_factor_frames = build_portfolio_factor_weekly_frames(
            daily_returns=daily_asset_returns,
            analysis_end_str=analysis_end_str,
            universe_tickers=beta_tickers,
        )

    if daily_asset_returns.empty and not beta_setup_reasons:
        return None

    return FactoryFactorStressInputs(
        daily_asset_returns_for_betas=daily_asset_returns,
        cash_returns_daily=cash_returns_daily,
        asset_betas_5y_universe=asset_betas_5y,
        asset_betas_10y_universe=asset_betas_10y,
        asset_betas_5y_extended_universe=asset_betas_5y_extended,
        asset_betas_10y_extended_universe=asset_betas_10y_extended,
        recession_factor_returns=recession_factor_returns,
        scenario_episode_factor_returns=scenario_episode_factor_returns,
        weekly_factor_frames=weekly_factor_frames,
        beta_source=beta_source,
        beta_setup_reasons=tuple(beta_setup_reasons),
    )


def weekly_factor_frames_for_candidate(
    factory_inputs: FactoryFactorStressInputs,
    *,
    tickers: list[str],
) -> PortfolioFactorWeeklyFrames | None:
    """Return shared weekly R/X when the factory panel covers this candidate's tickers."""
    frames = factory_inputs.weekly_factor_frames
    if not weekly_factor_frames_cover_tickers(frames, tickers):
        return None
    return frames


def build_factory_invariant_metrics(
    *,
    cfg: PortfolioConfig,
    monthly_data: MonthlyDataResult,
    local_benchmark_map: dict[str, str],
    report_tickers: list[str],
) -> FactoryInvariantMetrics | None:
    """
    Precompute universe asset metrics, correlation matrices, and monthly cov_base for stress.
    """
    windows_months = tuple(cfg.windows_months or ())
    if not windows_months or not report_tickers:
        return None

    analysis_end = monthly_data.analysis_end
    analysis_end_ts = pd.Timestamp(monthly_data.analysis_end_str)
    monthly_returns = truncate_to_analysis_end(monthly_data.monthly_returns, analysis_end)
    monthly_log_returns = truncate_to_analysis_end(
        monthly_data.monthly_log_returns, analysis_end
    )
    rf_monthly = truncate_to_analysis_end(monthly_data.rf_monthly, analysis_end)
    benchmark_returns = truncate_to_analysis_end(
        monthly_data.benchmark_returns, analysis_end
    )
    benchmark_base_ticker = cfg.benchmark_base_ticker

    returns_frequency = normalize_returns_frequency(monthly_data.returns_frequency)
    ppy = periods_per_year_for(returns_frequency)
    mar_annual = get_mar_from_config(cfg)
    mar_period = (
        per_period_eff_from_annual_simple(float(mar_annual), returns_frequency)
        if mar_annual is not None
        else None
    )
    coverage_threshold = getattr(cfg, "coverage_threshold", 0.90) or 0.90

    asset_metrics_all: list[list[dict]] = []
    for wm in windows_months:
        rows: list[dict] = []
        for ticker in report_tickers:
            r_simple = monthly_returns.get(ticker)
            r_log = monthly_log_returns.get(ticker)
            if r_simple is None or r_log is None:
                continue
            if coverage_ratio(r_simple, analysis_end_ts, wm) < coverage_threshold:
                continue
            local_bench_ticker = local_benchmark_map.get(ticker)
            local_bench_returns = None
            if local_bench_ticker and local_bench_ticker != benchmark_base_ticker:
                local_bench_returns = monthly_returns.get(local_bench_ticker)
            row = asset_metrics_one_window(
                ticker,
                r_simple,
                r_log,
                rf_monthly,
                benchmark_returns,
                analysis_end,
                wm,
                mar=mar_period,
                local_benchmark_returns=local_bench_returns,
                periods_per_year=ppy,
            )
            rows.append(row)
        asset_metrics_all.append(rows)

    asset_cols = [t for t in report_tickers if t in monthly_returns.columns]
    correlation_by_window: dict[int, pd.DataFrame] = {}
    for wm in windows_months:
        if not asset_cols:
            continue
        returns_slice = slice_window(monthly_returns[asset_cols], analysis_end, wm)
        returns_slice = returns_slice.dropna(how="all")
        if returns_slice.empty or len(returns_slice) < 2:
            continue
        correlation_by_window[wm] = returns_slice.corr()

    stress_cov_base = pd.DataFrame()
    stress_cov_asset_cols: list[str] = []
    if asset_cols:
        returns_sub = monthly_returns[asset_cols].dropna(how="all")
        if len(returns_sub) >= 2:
            stress_cov_base = cov_matrix_monthly(returns_sub, ddof=1)
            stress_cov_asset_cols = list(stress_cov_base.columns)

    return FactoryInvariantMetrics(
        asset_metrics_all=tuple(asset_metrics_all),
        correlation_by_window=correlation_by_window,
        stress_cov_base=stress_cov_base,
        stress_cov_asset_cols=tuple(stress_cov_asset_cols),
        windows_months=windows_months,
        universe_tickers=tuple(report_tickers),
    )


def invariant_metrics_usable_for_report(
    invariant: FactoryInvariantMetrics | None,
    *,
    tickers: list[str],
    windows_months: list[int] | tuple[int, ...],
) -> bool:
    """True when precomputed invariant blocks can be sliced for this candidate report."""
    if invariant is None:
        return False
    if tuple(windows_months) != invariant.windows_months:
        return False
    ticker_set = set(tickers)
    return ticker_set.issubset(set(invariant.universe_tickers))


def slice_asset_metrics_for_tickers(
    asset_metrics_all: tuple[list[dict], ...],
    tickers: list[str],
) -> list[list[dict]]:
    """Filter precomputed universe asset metrics to the tickers used in one report."""
    ticker_set = set(tickers)
    return [
        [row for row in window_rows if row.get("ticker") in ticker_set]
        for window_rows in asset_metrics_all
    ]


def prepare_candidate_run_context(
    cfg: PortfolioConfig,
    *,
    project_root: Path,
    no_cache: bool = False,
    preload_factor_stress: bool = True,
    preload_invariant_metrics: bool = True,
    allow_risk_free_cached_fallback: bool = False,
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
        allow_risk_free_cached_fallback=allow_risk_free_cached_fallback,
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
    invariant_metrics = None
    if preload_invariant_metrics:
        invariant_metrics = build_factory_invariant_metrics(
            cfg=cfg,
            monthly_data=monthly_data,
            local_benchmark_map=local_benchmark_map,
            report_tickers=report_tickers,
        )
    prepared_synthetic_stress = None
    if factor_stress is not None and invariant_metrics is not None:
        stress_cov_method = str(getattr(cfg, "stress_cov_method", None) or "taxonomy_blend_v1")
        asset_cols = [
            t
            for t in invariant_metrics.stress_cov_asset_cols
            if t in invariant_metrics.stress_cov_base.columns
        ]
        if not asset_cols:
            asset_cols = [t for t in report_tickers if t in invariant_metrics.stress_cov_base.columns]
        if asset_cols and not factor_stress.asset_betas_5y_universe.empty:
            prepared_synthetic_stress = build_prepared_synthetic_stress_inputs(
                asset_cols=asset_cols,
                asset_betas=factor_stress.asset_betas_5y_universe,
                cov_base=invariant_metrics.stress_cov_base,
                cash_proxy_ticker=cash_proxy_ticker,
                stress_cov_method=stress_cov_method,
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
        invariant_metrics=invariant_metrics,
        prepared_synthetic_stress=prepared_synthetic_stress,
        no_cache=no_cache,
    )


def macro_panel_fetch_window(
    analysis_end_str: str,
    *,
    months_back: int = 420,
) -> tuple[str, str]:
    """Date window for ``fetch_macro_indicators`` aligned with macro_two_axis production path."""
    end_ts = pd.Timestamp(analysis_end_str)
    panel_start = (end_ts - pd.DateOffset(months=int(months_back) + 12)).strftime("%Y-%m-%d")
    panel_end = (end_ts + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    return panel_start, panel_end


def load_review_macro_panel(
    analysis_end_str: str,
    *,
    months_back: int = 420,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Fetch the monthly macro indicator panel once per review run."""
    from src.stress_factors_macro import fetch_macro_indicators

    cache_key = (str(analysis_end_str), int(months_back))
    cached = _REVIEW_MACRO_PANEL_MEMORY_CACHE.get(cache_key)
    if cached is not None:
        return _copy_macro_panel_cache_value(cached)
    panel_start, panel_end = macro_panel_fetch_window(
        analysis_end_str,
        months_back=months_back,
    )
    panel, meta = fetch_macro_indicators(panel_start, panel_end)
    _REVIEW_MACRO_PANEL_MEMORY_CACHE[cache_key] = _copy_macro_panel_cache_value((panel, meta))
    return panel, meta


def prepare_review_run_context(
    cfg: PortfolioConfig,
    *,
    project_root: Path,
    no_cache: bool = False,
    allow_risk_free_cached_fallback: bool = False,
) -> ReviewRunContext:
    """
    Load shared monthly/daily panels, weekly factor frames, and macro indicator panel
    once per review run.
    """
    factory_context = prepare_candidate_run_context(
        cfg,
        project_root=project_root,
        no_cache=no_cache,
        preload_factor_stress=True,
        preload_invariant_metrics=True,
        allow_risk_free_cached_fallback=allow_risk_free_cached_fallback,
    )
    macro_panel: pd.DataFrame | None = None
    macro_panel_meta: dict[str, Any] | None = None
    try:
        macro_panel, macro_panel_meta = load_review_macro_panel(
            factory_context.analysis_end_str,
        )
    except Exception as exc:
        logger.warning("Review context: macro panel preload failed: %s", exc)
        macro_panel_meta = {"preload_error": str(exc)}
    return ReviewRunContext(
        factory_context=factory_context,
        macro_panel=macro_panel,
        macro_panel_meta=macro_panel_meta,
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


def extended_diagnostic_betas_for_candidate(
    factory_inputs: FactoryFactorStressInputs,
    *,
    weights: dict[str, float],
    beta_tickers: list[str],
    benchmark_base_ticker: str,
    analysis_end_str: str,
) -> tuple[dict[str, float], dict[str, float]]:
    """
    Portfolio-level extended-factor diagnostic betas from precomputed universe panels.
    """
    if (
        not factory_inputs.asset_betas_5y_extended_universe.empty
        and not factory_inputs.asset_betas_10y_extended_universe.empty
    ):
        b5 = factory_inputs.asset_betas_5y_extended_universe.reindex(beta_tickers).dropna(how="all")
        b10 = factory_inputs.asset_betas_10y_extended_universe.reindex(beta_tickers).dropna(how="all")
        if not b5.empty and not b10.empty:
            return (
                portfolio_factor_betas(weights, b5),
                portfolio_factor_betas(weights, b10),
            )

    daily = factory_inputs.daily_asset_returns_for_betas
    if daily.empty:
        return {}, {}
    b5 = compute_asset_factor_betas_from_daily_returns(
        daily,
        analysis_end_str,
        FACTOR_WEEKS_5Y,
        factor_columns=FACTOR_COLUMN_ORDER,
        asset_tickers=beta_tickers,
        equity_factor_ticker=benchmark_base_ticker,
    )
    b10 = compute_asset_factor_betas_from_daily_returns(
        daily,
        analysis_end_str,
        FACTOR_WEEKS_10Y,
        factor_columns=FACTOR_COLUMN_ORDER,
        asset_tickers=beta_tickers,
        equity_factor_ticker=benchmark_base_ticker,
    )
    return portfolio_factor_betas(weights, b5), portfolio_factor_betas(weights, b10)


def daily_panel_for_candidate_report(
    factory_inputs: FactoryFactorStressInputs,
    *,
    tickers: list[str],
    cash_proxy_ticker: str,
) -> tuple[pd.DataFrame, pd.Series] | None:
    """
    Slice the factory daily return panel for one candidate report (tail-risk block).
    """
    daily = factory_inputs.daily_asset_returns_for_betas
    if daily is None or daily.empty:
        return None
    needed = list(dict.fromkeys(list(tickers) + [cash_proxy_ticker]))
    missing = [t for t in needed if t not in daily.columns]
    if missing:
        return None
    cols = [t for t in needed if t in daily.columns]
    sub = daily.loc[:, cols]
    cash = factory_inputs.cash_returns_daily
    if cash is None or cash.empty:
        cash = pd.Series(0.0, index=sub.index)
    else:
        cash = cash.reindex(sub.index).fillna(0.0)
    return sub, cash
