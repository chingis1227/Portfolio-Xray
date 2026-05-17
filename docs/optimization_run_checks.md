# Full Optimization Run Checks

This note lists the main checks and failure points for a full optimization run.

## 1. Execution Order And Failure Points

### 1.1 Configuration Load (`load_validated_config`)

| Check | Failure | Action |
| --- | --- | --- |
| `config.yml` is missing | `FileNotFoundError` | Create `config.yml` from `config.yml.example`. |
| Required fields are empty | `ConfigValidationError: Missing or empty required config fields: [...]` | Fill `tickers`, `investor_currency`, and the other schema-required fields. |
| Numeric or percentage fields are invalid | `ConfigValidationError` naming the field | Convert values to the format expected by `validate_config`. |
| `client_profile` is set but not found in `client_profiles.yml` | Profile values are not applied | Use one of: `ultra_conservative`, `conservative`, `balanced`, `growth`, `aggressive`; IDs are normalized to lowercase. |
| `investor_currency` is not USD/EUR and `cash_proxy_ticker` or `risk_free_source` is missing | `ConfigValidationError` requiring explicit settings | Set the cash proxy and risk-free source explicitly for the investor currency. |

### 1.2 Client Profile (`client_profiles.yml`)

Profiles fill target return, volatility, drawdown, and liquidity defaults when configured.

### 1.3 Data Loading (`load_monthly_data_shared`)

This step performs network requests. Without network access, or when an API is blocked, the script may fail or wait for timeouts.

| Source | Used for | Possible failure or behavior |
| --- | --- | --- |
| **Yahoo Finance (yfinance)** | Prices for assets, benchmark, cash proxy, and FX | Timeout, empty ticker series, or exception from `yf.download`. |
| **FRED** (`pandas_datareader`) | `risk_free_source` such as `FRED:DTB3` | `ImportError` if missing, API exception, or empty `rf_monthly`. |
| **ECB ESTR** (`api.estr.dev`) | `risk_free_source` such as `ECB:ESTR` for EUR | `URLError`, timeout, or blocked network request. |

There is no VPN or tunnel setup in code. For firewall or regional blocks, use an external VPN or proxy (`HTTP_PROXY` / `HTTPS_PROXY`) if the libraries honor it.

### 1.4 Optimization (`run_max_return_optimization` in `run_optimization.py`)

The historical function name is kept for compatibility. The current policy is a single-stage expected-return maximization with penalties for target volatility and target return deviations, plus weight constraints. See `docs/specs/portfolio_construction_policy.md` and `docs/specs/feasibility_constraints_spec.md`. `RC_vol` is not an optimizer constraint.

| Situation | Result | Action |
| --- | --- | --- |
| Optimizer does not converge or data fails | See logs and `run_result.json` (`FAIL_DATA`, etc.) | Check min/max weights, ticker universe, data coverage, and covariance. |
| Optimizer fallback branch (`OK_FALLBACK`) | `run_result.json` has `OK_FALLBACK` in `optimization_status` | Review optimizer messages; `rc_breaches` is reserved and empty. |

### 1.5 ProLiquidity And Alpha-Shift

| Condition | Failure | Action |
| --- | --- | --- |
| `cash_policy = prohibited`, volatility is above target, and alpha-shift cannot reach target vol | ProLiquidity message / `SystemExit` | Allow cash (`allowed_for_scaling`), raise `target_vol_annual`, or add lower-volatility assets. |
| Donor set is empty for alpha-shift | `Donor set empty for alpha shift` | Ensure the risk portfolio has positive-weight names with non-zero RC, or increase `N_rc`. |

## 2. Network Notes

- VPN is not configured in code.
- Outgoing requests are made by `src/data_yf.py` (Yahoo), `src/data_fred.py` (FRED), and `src/data_ecb.py` (ESTR).
- When network issues occur, check browser/curl access, VPN/proxy settings, and `FRED_API_KEY` for FRED rate limits.

## 3. Parameter Conflicts

| Parameter A | Parameter B | Conflict | Recommendation |
| --- | --- | --- | --- |
| **investor_currency: JPY/CHF** | Missing `cash_proxy_ticker` / `risk_free_source` | Validation error | Set cash and risk-free source explicitly. |
| **cash_policy: prohibited** | Low **target_vol_annual** and high-volatility universe | Target volatility may be unreachable | Allow cash or adjust targets/universe. |
| **client_profile: Growth** in config | YAML key is **`growth`** | OK: profile ID is normalized to lowercase | Keep profile keys lowercase in `client_profiles.yml`. |
| **weights** in config | Policy is "weights come from optimization" | Manual weights may be overwritten by a run | Run optimization first, then run the report. |

## 4. Script Dependencies

- **run_optimization.py** reads `config.yml` and `config/client_profiles.yml`, downloads data, and writes `portfolio_weights.yml`, `run_result.json`, stress outputs, and snapshots to `output_dir_final`. The optimization-path `stress_report.json` includes factor betas/regressions, beta stability, factor covariance, factor variance decomposition, historical factor attribution, and portfolio PCA.
- **run_report.py** reads `config.yml` and, when weights are absent from config, reads `portfolio_weights.yml` from `output_dir_final`.

Order: run `python run_optimization.py`, then `python run_report.py` when needed. Add `--no-cache` when data should be refreshed.

## 5. Current Policy Notes

1. Weights are system outputs; do not require final weights manually in `config.yml`.
2. `RC_vol` / Top1 / Top3 in stress are diagnostics only in reports and JSON. They do not block weight writing and do not define config thresholds.
3. Full-overlap historical MaxDD is the main hard gate for weight writing, alongside `FAIL_DATA`. Stress remains `DIAG_*` and does not block weights when the mandate passes.
4. Default `backtest_mode` is `dynamic_nan_safe`; see `docs/specs/data_policy_spec.md`.
5. Dual-horizon robustness compares 10Y vs 5Y weights and per-asset RC when enabled; flags are written in `robustness_report.json`.

## 6. Pre-Run Checklist

1. `config.yml`: required fields are present; non-USD portfolios have explicit cash and risk-free settings.
2. `client_profile`, if used, exists in `client_profiles.yml`.
3. Network access: Yahoo, FRED, and for EUR portfolios `api.estr.dev`.
4. Dependencies: `pandas-datareader` for FRED.
5. After optimization: confirm `portfolio_weights.yml` and `run_result.json`; then run `run_report.py`.

If something fails, use the console output and tables above. Status details are in `docs/specs/production_workflow.md`.
