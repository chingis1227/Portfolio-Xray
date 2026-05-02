# Portfolio Optimization вЂ” РµРґРёРЅР°СЏ С‚РѕС‡РєР° РІС…РѕРґР°

РЎРёСЃС‚РµРјР° СЃС‚СЂРѕРёС‚ РїРѕСЂС‚С„РµР»СЊ **РѕРґРЅРѕСЃС‚Р°РґРёР№РЅРѕР№** РѕРїС‚РёРјРёР·Р°С†РёРµР№ (РјР°РєСЃРёРјРёР·Р°С†РёСЏ РѕР¶РёРґР°РµРјРѕР№ РґРѕС…РѕРґРЅРѕСЃС‚Рё РїСЂРё РјСЏРіРєРёС… С†РµР»СЏС… РїРѕ РІРѕР»Р°С‚РёР»СЊРЅРѕСЃС‚Рё/РґРѕС…РѕРґРЅРѕСЃС‚Рё Рё РѕРіСЂР°РЅРёС‡РµРЅРёСЏС… РїРѕ **РІРµСЃСѓ**), Р·Р°С‚РµРј ProLiquidity Рё РґРёР°РіРЅРѕСЃС‚РёС‡РµСЃРєРёР№ СЃС‚СЂРµСЃСЃ. **RC_vol** СЃС‡РёС‚Р°РµС‚СЃСЏ Рё РїРѕРєР°Р·С‹РІР°РµС‚СЃСЏ РІ РѕС‚С‡С‘С‚Р°С…, РЅРѕ **РЅРµ** Р·Р°РґР°С‘С‚ Р¶С‘СЃС‚РєРёС… РѕРіСЂР°РЅРёС‡РµРЅРёР№ РѕРїС‚РёРјРёР·Р°С‚РѕСЂР°. Р’РµСЃР° РІС‹РґР°С‘С‚ С‚РѕР»СЊРєРѕ РѕРїС‚РёРјРёР·Р°С‚РѕСЂ; СЂСѓС‡РЅР°СЏ РїСЂР°РІРєР° РІРµСЃРѕРІ РІ РєРѕРЅС„РёРіРµ РЅРµ РґРѕРїСѓСЃРєР°РµС‚СЃСЏ (РёСЃРєР»СЋС‡РµРЅРёРµ вЂ” РїСЂРѕС‚РѕРєРѕР» В«View After OptimizationВ»).

---

## РџР°Р№РїР»Р°Р№РЅ

1. **РћРїС‚РёРјРёР·Р°С†РёСЏ**
   ```bash
   python run_optimization.py [--no-cache] [--write-config]
   ```
   Р§РёС‚Р°РµС‚ `config.yml` Рё РїСЂРё РЅРµРѕР±С…РѕРґРёРјРѕСЃС‚Рё **`config/client_profiles.yml`**; РїРѕРґС‚СЏРіРёРІР°РµС‚ СЂС‹РЅРѕС‡РЅС‹Рµ РґР°РЅРЅС‹Рµ; СЃС‡РёС‚Р°РµС‚ РєРѕРІР°СЂРёР°С†РёРё Рё **РѕРґРёРЅ** РїСЂРѕС…РѕРґ РѕРїС‚РёРјРёР·Р°С‚РѕСЂР° (`run_max_return_optimization`); ProLiquidity; РѕРїС†РёРѕРЅР°Р»СЊРЅРѕ dual-horizon (10Y + 5Y) РґР»СЏ `robustness_report.json`. РџРёС€РµС‚ РІРµСЃР° РІ **`portfolio_weights.yml`** Рё **`run_result.json`** РІ РєР°С‚Р°Р»РѕРі **`output_dir_final`** (РїРѕ СѓРјРѕР»С‡Р°РЅРёСЋ **Main portfolio**). РўРѕС‚ Р¶Рµ optimization run С‚РµРїРµСЂСЊ РїРёС€РµС‚ РІ `stress_report.json` РїРѕР»РЅС‹Р№ factor diagnostics block: factor betas/regressions, rolling beta stability, factor covariance, factor variance decomposition, historical factor attribution, Рё portfolio PCA. РџСЂРё РїСЂРѕРІР°Р»Рµ **РјР°РЅРґР°С‚Р° MaxDD** РІРµСЃР° РЅРµ Р·Р°РїРёСЃС‹РІР°СЋС‚СЃСЏ, РІС‹С…РѕРґ СЃ РѕС€РёР±РєРѕР№ (**FAIL_MANDATE**).

2. **РћС‚С‡С‘С‚**
   ```bash
   python run_report.py [--no-cache] [--clear-cache] [--backtest-mode dynamic_nan_safe]
   ```
   Р‘РµСЂС‘С‚ РІРµСЃР° РёР· `config.yml` РёР»Рё РёР· **`portfolio_weights.yml`** РІ `output_dir_final`; СЃС‡РёС‚Р°РµС‚ РјРµС‚СЂРёРєРё РїРѕ РѕРєРЅР°Рј 3Y/5Y/10Y, RC_vol, СЃС‚СЂРµСЃСЃ, СЃРЅРёРјРєРё. РџРёС€РµС‚ CSV РІ `output_dir_csv` (С‡Р°СЃС‚Рѕ **`results_csv/`**), JSON Рё HTML/text РѕС‚С‡С‘С‚С‹ РІ **`output_dir_final`**.
  Factor regression outputs in `stress_report.json` include R2, adjusted R2, `idiosyncratic_risk = 1 - R2`, multicollinearity, serial correlation, Breusch-Pagan heteroskedasticity, HAC/Newey-West inference diagnostics for 5Y/10Y weekly OLS windows, and diagnostic-only `factor_betas_stability` for rolling beta sign/magnitude/specification/OOS stability.
  Production factor beta outputs use the base factor contract: `equity`, `real_rates`, `inflation`, `credit`, `usd`, `commodity`, `vix`, and `us_growth`. `commodity` is the production сырьевой factor.
  Extended diagnostic/stress analytics use the base factors plus `oil`. `oil` is diagnostic/stress only: `beta_oil` is deprecated and removed from new production beta, stability, OOS, adjusted overlay, and base variance-decomposition outputs. Read Oil exposure from `stress_report.json.diagnostic_oil_beta` or stress-layer metrics.
  `stress_report.json.factor_betas_kalman` adds diagnostic-only time-varying Kalman beta estimates on the extended weekly factor registry. Reported Kalman betas are capped at `|beta| <= 3.0`, preserve raw latest filtered values, flag Kalman-vs-5Y divergence, classify state uncertainty, and export `kalman_factor_betas_weekly.csv` plus `kalman_factor_betas_latest.csv` in `results_csv/`. These diagnostics do not change weights, mandate gates, or raw OLS beta outputs.
  `stress_report.json` also carries a diagnostic-only stability-adjusted beta overlay: `factor_betas_adjusted`, `synthetic_factor_pnl_adjusted`, `factor_beta_shock_oos_adjusted`, and `raw_vs_adjusted_pnl_signal`. The overlay shrinks unstable 5Y betas toward 10Y anchors, flags strong 5Y-vs-10Y divergence, and logs where raw-vs-adjusted factor-model PnL differs materially. These fields do not change optimizer behavior, mandate gates, or the primary raw beta outputs, and production adjusted betas exclude Oil.
  Historical stress rows in `stress_report.json` include model-based factor attribution when factor data is available: 5Y beta times realized episode factor shock, top factor drivers, largest negative factor, model PnL, and model error versus realized episode PnL. The same rows can now carry parallel adjusted-beta attribution fields with `_adjusted` suffixes. This is an explainability diagnostic, not a pure realized causal decomposition.
   Factor covariance analytics in `stress_report.json.factor_covariance` keep `base`, `stress_empirical`, and `stress_overlay` separate. `base` and `stress_empirical` are data-driven; `stress_overlay` is hypothetical and exports explicit overlay deltas. The same block includes diagnostic-only `forecast_quality`, a 5Y weekly covariance vs next-1Y realized factor-risk backtest. Related CSV artifacts include factor covariance/correlation matrices, factor RC, overlay deltas, covariance stability checks, and `factor_covariance_forecast_quality.csv` in `results_csv/`.
   Macro regime diagnostics in `stress_report.json.macro_regime_diagnostics` use `internal_market_proxy_v1`: rolling weekly `us_growth` z-score for `growth_score` and average rolling z-score of available `inflation` and `commodity` for `inflation_pressure_score`. The block labels `goldilocks`, `reflation`, `stagflation`, and `recession_disinflation`, reports confidence/transition warnings, regime factor betas/covariance/RC with `base_10y` fallback metadata, and exports `macro_regime_labels_weekly.csv`, `macro_regime_factor_betas.csv`, `macro_regime_factor_covariance.csv`, and `macro_regime_factor_rc.csv`. It is diagnostic-only and is not a full macroeconomic regime model.
   Factor variance decomposition in `stress_report.json.factor_variance_decomposition` uses 5Y weekly base-factor OLS rows only (`variance_scale=weekly`) to split total portfolio variance into signed net factor shares, gross factor concentration, risk adders, hedgers, neutral factors, and residual risk. It includes an R2 cross-check against `b' Sigma_f b / Var(portfolio)`, local warning codes, residual severity, and exports `results_csv/factor_variance_decomposition_5y.csv`.
   Portfolio PCA diagnostics in `stress_report.json.portfolio_pca` use 5Y weekly adjusted-close returns for current positive-weight portfolio assets. The block reports raw and factor-residual PCA, each as covariance PCA (`risk_dominance`) and correlation PCA (`structure`), plus PC1 stability, effective number of bets, PC1 factor correlations, and CSV exports: `portfolio_pca_summary_5y.csv`, `portfolio_pca_components_5y.csv`, `portfolio_pca_rolling_pc1.csv`, and `portfolio_pca_pc1_factor_correlations.csv`.

**РџРѕСЂСЏРґРѕРє:** СЃРЅР°С‡Р°Р»Р° `run_optimization.py`, Р·Р°С‚РµРј `run_report.py`. РРЅР°С‡Рµ РѕС‚С‡С‘С‚ Р±СѓРґРµС‚ Р±РµР· Р°РєС‚СѓР°Р»СЊРЅС‹С… РІРµСЃРѕРІ.

---

## РљРѕРЅС„РёРіСѓСЂР°С†РёСЏ

| Р¤Р°Р№Р» | РќР°Р·РЅР°С‡РµРЅРёРµ |
|------|------------|
| **config.yml** | РћСЃРЅРѕРІРЅС‹Рµ РЅР°СЃС‚СЂРѕР№РєРё: С‚РёРєРµСЂС‹, РІР°Р»СЋС‚Р°, РїСЂРѕС„РёР»СЊ, Р»РёРєРІРёРґРЅРѕСЃС‚СЊ, cash_policy, target_vol, target_max_drawdown_pct, РѕРєРЅР°, `output_dir_final`. Р’РµСЃР° РІ РєРѕРЅС„РёРі РЅРµ РІРІРѕРґСЏС‚СЃСЏ вЂ” РѕРЅРё СЂРµР·СѓР»СЊС‚Р°С‚ РѕРїС‚РёРјРёР·Р°С†РёРё. |
| **config/client_profiles.yml** | РЁР°Р±Р»РѕРЅС‹ РїРѕ РїСЂРѕС„РёР»СЏРј (ultra_conservative вЂ¦ aggressive): С†РµР»РµРІР°СЏ РІРѕР»Р°С‚РёР»СЊРЅРѕСЃС‚СЊ, MaxDD, С†РµР»РµРІР°СЏ РЅРѕРјРёРЅР°Р»СЊРЅР°СЏ РґРѕС…РѕРґРЅРѕСЃС‚СЊ Рё РґСЂ. РџСЂРё `client_profile` РІ `config.yml` РЅРµРґРѕСЃС‚Р°СЋС‰РёРµ РїРѕР»СЏ РїРѕРґСЃС‚Р°РІР»СЏСЋС‚СЃСЏ РёР· РїСЂРѕС„РёР»СЏ. |
| **assets.yml** | РњРµС‚Р°РґР°РЅРЅС‹Рµ Р°РєС‚РёРІРѕРІ (РЅР°РїСЂРёРјРµСЂ РІР°Р»СЋС‚Р°). РћРїС†РёРѕРЅР°Р»СЊРЅРѕ. |

РџСЂРёРјРµСЂ РїРѕР»РЅРѕРіРѕ РєРѕРЅС„РёРіР°: **config.yml.example**.

---

## Р”РѕРєСѓРјРµРЅС‚Р°С†РёСЏ (РёСЃС‚РѕС‡РЅРёРєРё РёСЃС‚РёРЅС‹)

- **РџРѕР»РёС‚РёРєР° Рё РјРµС‚СЂРёРєРё**
  - [Portfolio Construction Policy](docs/portfolio_construction_policy.md) вЂ” РѕРґРЅРѕСЃС‚Р°РґРёР№РЅС‹Р№ РѕРїС‚РёРјРёР·Р°С‚РѕСЂ, RC_vol РєР°Рє РґРёР°РіРЅРѕСЃС‚РёРєР°, mandate, СЃС‚СЂРµСЃСЃ РєР°Рє РґРёР°РіРЅРѕСЃС‚РёРєР°.
  - [Metrics Specification](metrics_specification.md) вЂ” С„РѕСЂРјСѓР»С‹ РјРµС‚СЂРёРє, РѕРєРЅР°, ddof=1, RC_vol, FX.
  - [PROJECT_RULES.md](PROJECT_RULES.md) вЂ” СЃС‚Р°РЅРґР°СЂС‚ С‡Р°СЃС‚РѕС‚С‹, РґР°С‚, Р±РµРЅС‡РјР°СЂРєРѕРІ.

- **Р”Р°РЅРЅС‹Рµ Рё Р±СЌРєС‚РµСЃС‚**
  - [Data policy, NaN, young ETFs](docs/data_policy_nan_young_etfs.md) вЂ” join policy, РїРµСЂРµСЂР°СЃРїСЂРµРґРµР»РµРЅРёРµ NaN СЃСЂРµРґРё СЂРёСЃРє-Р°РєС‚РёРІРѕРІ, РґРѕР»СЏ `w_miss` РЅР° РєСЌС€-РїСЂРѕРєСЃРё.

- **РћРїС‚РёРјРёР·Р°С†РёСЏ Рё РѕРіСЂР°РЅРёС‡РµРЅРёСЏ**
  - [Optimization specs (РѕРіР»Р°РІР»РµРЅРёРµ)](docs/docs/README.md) вЂ” ProLiquidity, View After Optimization.
  - [Feasibility constraints](docs/docs/feasibility_constraints_spec.md) вЂ” Р»РёРјРёС‚С‹ РІРµСЃРѕРІ РїРѕ **N** (Рё РёСЃС‚РѕСЂРёС‡РµСЃРєР°СЏ СЃРїСЂР°РІРєР° РїРѕ СѓРґР°Р»С‘РЅРЅРѕРјСѓ RC-cap).
  - [Optimization run checks](docs/optimization_run_checks.md) вЂ” С‚РѕС‡РєРё РѕС‚РєР°Р·Р°, СЃРµС‚СЊ, РїСЂРѕС‚РёРІРѕСЂРµС‡РёСЏ РїР°СЂР°РјРµС‚СЂРѕРІ.

- **РЎС‚СЂРµСЃСЃ Рё View After Optimization**
  - [Stress testing spec](docs/docs/stress_testing_spec.md) вЂ” СЃС†РµРЅР°СЂРёРё, Loss, RC Top1вЂ“Top3 (С‡РёСЃР»Р°), РёСЃС‚РѕСЂРёС‡РµСЃРєРёРµ СЌРїРёР·РѕРґС‹, РєРѕРґС‹ **DIAG_***.
  - [View After Optimization](docs/docs/view_after_optimization_spec.md) вЂ” СЂР°Р·СЂРµС€С‘РЅРЅС‹Р№ В«С‚РёР»СЊС‚В» РїРѕСЃР»Рµ РѕРїС‚РёРјРёР·Р°С†РёРё.

- **РџСЂРѕРґР°РєС€РµРЅ**
  - [Production workflow](docs/production_workflow.md) вЂ” С‡С‚Рѕ Р±Р»РѕРєРёСЂСѓРµС‚ Р·Р°РїРёСЃСЊ РІРµСЃРѕРІ, СЃС‚Р°С‚СѓСЃС‹ **APPROVED** / **OK_FALLBACK**.

---

## Р”РѕРїРѕР»РЅРёС‚РµР»СЊРЅРѕ

- **View After Optimization:** РѕС‚РґРµР»СЊРЅС‹Р№ СЃРєСЂРёРїС‚ `run_view_after_optimization.py` (СЃРј. СЃРїРµРєСѓ РІС‹С€Рµ).
- **РњР°РЅРґР°С‚ MaxDD:** РїСЂРё Р·Р°РґР°РЅРЅРѕРј `target_max_drawdown_pct` Р·Р°РїРёСЃСЊ РІРµСЃРѕРІ Р±Р»РѕРєРёСЂСѓРµС‚ С‚РѕР»СЊРєРѕ **СЂРµР°Р»РёР·РѕРІР°РЅРЅР°СЏ РїСЂРѕСЃР°РґРєР° РЅР° РїРѕР»РЅРѕР№ РїРµСЂРµСЃРµРєР°СЋС‰РµР№СЃСЏ РјРµСЃСЏС‡РЅРѕР№ РёСЃС‚РѕСЂРёРё** (СЃРј. `run_result.json`, `mandate_check`, **FAIL_MANDATE**). РЎС†РµРЅР°СЂРЅС‹Р№ СЃС‚СЂРµСЃСЃ вЂ” **РґРёР°РіРЅРѕСЃС‚РёРєР°** (**DIAG_***), РЅРµ Р±Р»РѕРєРёСЂСѓРµС‚ РІС‹РїСѓСЃРє РІРµСЃРѕРІ.

---

## ETF Universe Taxonomy

`config/etf_universe.yml` is the curated ETF classification source of truth. In V1 it validates and annotates the active `config.yml` ticker list; it does not change optimizer membership, optimizer eligibility, or portfolio weights.

Useful commands:

```bash
python run_etf_universe.py validate
python run_etf_universe.py check-config --config config.yml
python run_etf_universe.py export --format csv
python run_etf_universe.py export --format json
python run_etf_universe.py list --asset-class equity
python run_etf_universe.py list --risk-factor real_rates
python run_etf_universe.py enrich-yahoo
```

CSV/JSON exports are generated artifacts under `results_csv/`. Optimization and report runs write `etf_universe_validation.json` under `output_dir_final` when the universe file exists. See `docs/etf_universe_spec.md`.

`config/stock_universe.yml` is a separate stock classification source of truth for the current S&P 500 constituent set. In V1 it is CLI-only, validates and exports stock metadata, and can check an explicit stock config, but it does not integrate into optimization/report runs or change portfolio weights.

```bash
python run_stock_universe.py validate
python run_stock_universe.py check-config --config path/to/stock_config.yml
python run_stock_universe.py export --format csv
python run_stock_universe.py export --format json
python run_stock_universe.py list --sector "Information Technology"
python run_stock_universe.py list --industry "Biotechnology"
python run_stock_universe.py list --risk-factor us_growth
```

See `docs/stock_universe_spec.md`.
