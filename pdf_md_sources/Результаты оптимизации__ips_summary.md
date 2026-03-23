# IPS Full Run Results Report

## Report Scope

- **Source:** `ips_summary.txt`
- **Document type:** **Run output summary**
- **Mandate context:** Aggressive profile, USD investor, 10-year horizon

## Mandate Parameters

| Parameter | Value |
|---|---|
| Target volatility (annual) | 17.0% |
| Max drawdown limit | 35.0% |
| Horizon | 10.0 years |
| Investor currency | USD |
| Client profile | Aggressive |

## Run Status

- **Primary status:** `CANDIDATE_RB_BREACH`
- **RC breaches:** none

## Final Portfolio Weights

| Asset | Weight |
|---|---:|
| VOO | 0.263 |
| ITA | 0.135 |
| SLV | 0.123 |
| SMH | 0.093 |
| COPX | 0.063 |
| URA | 0.044 |
| BIL | 0.025 |
| BBJP | 0.020 |
| GLD | 0.020 |
| QQQ | 0.020 |
| ROBO | 0.020 |
| VDC | 0.020 |
| VWO | 0.020 |
| ARMY.PA | 0.019 |
| BND | 0.019 |
| CIBR | 0.019 |
| SCHD | 0.019 |
| SCHP | 0.019 |
| VGK | 0.019 |
| VT | 0.019 |
| **Sum** | **0.999** |

## Risk Contribution by Block (actual | target)

| Block | Actual RC | Target RC | Gap |
|---|---:|---:|---:|
| Growth | 83.92% | 90.00% | -6.1 pp |
| Duration | 0.16% | 5.00% | -4.8 pp |
| Inflation | 15.92% | 5.00% | +10.9 pp |

## Stress Summary

| Item | Value |
|---|---|
| Status | FAIL_STRESS |
| Fail reason | FAIL_ROLE_EQUITY_SHOCK |
| Worst scenario loss | -31.89% |
| Failed scenario | equity_shock |

## Violations

- `RB_BREACH`: Growth = -6.08 | Duration = -4.84 | Inflation = 10.92
- `FAIL_STRESS`: fail_reason_code = FAIL_ROLE_EQUITY_SHOCK | worst_scenario_loss_pct = -0.3189 | failed_scenario = equity_shock

## Next Actions (from source)

- Re-run with wider corridor (e.g., 7pp) or minimally relax secondary weight caps.
- If RB breach persists, increase `k_block` in offending blocks.
- If Growth capacity constraints prevent target Growth weight, add satellites or relax max caps.
- Consider increasing liquidity, shortening duration, and reducing high growth/HY exposure.

## Status Reference (from source)

- `APPROVED`: Use weights as target; safe to execute.
- `CANDIDATE_RB_BREACH`: Use with caution; consider re-run or accept-and-monitor.
- `OK_FALLBACK`: Check RC breaches; use if mandate-compatible.
- `FAIL_STRESS`: Under strict stress gate, weights are not written.
- `FAIL_MAX_DD`: Weights are not written; adjust drawdown constraint/risk budget.
- `FAIL_DATA/RC/FEAS`: Weights are not written; follow corrective next actions.

## Conclusion / Key Takeaways

- Run output confirms a candidate portfolio with risk-budget mismatch and stress failure.
- Governance-ready interpretation should focus on block RC gaps and equity-shock resilience.
