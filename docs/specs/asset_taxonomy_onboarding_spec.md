# Asset Taxonomy Onboarding Specification

## Purpose

One-time onboarding of new tickers into Portfolio MRI taxonomy so Portfolio X-Ray, synthetic Stress Lab PnL, and synthetic stress **risk contribution (RC)** stay consistent as the universe scales.

This is **not** run on every portfolio analysis. Operators or the taxonomy agent run it when adding instruments to `config/etf_universe.yml` or `config/stock_universe.yml`.

## Boundaries

| In scope | Out of scope |
| --- | --- |
| ETF/stock universe rows and validation | Optimizer universe selection or weights |
| Stress block mapping (EQ/CR/ND/TI/CO/CA) for RC | Changing synthetic `SCENARIOS` or `VOL_MULT_BLOCK` |
| Onboarding report JSON | New stress blocks without architecture decision |
| Confidence / `needs_review` in **report only** | Factor beta estimation (separate portfolio run) |

Canonical schemas: [etf_universe_spec.md](etf_universe_spec.md), [stock_universe_spec.md](stock_universe_spec.md).  
Stress RC behavior: [stress_testing_spec.md](stress_testing_spec.md) §2.2.  
Taxonomy map: [taxonomy_spec.md](taxonomy_spec.md).

## Two readiness layers

| Layer | Question | Depends on |
| --- | --- | --- |
| **Synthetic PnL** | How much loss/gain under factor shocks... | Weekly factor betas × shocks × weights; prices for beta estimation |
| **Synthetic RC** | Who dominates stressed variance (Top1/Top3)... | Taxonomy → stress block; `taxonomy_blend_v1` vol/correlation tables |

Volatility multipliers and stressed correlations **do not** change synthetic PnL.

## Universe routing

| Instrument | File |
| --- | --- |
| ETF, fund-like, bond/commodity/cash ETF, alternatives | `config/etf_universe.yml` |
| Individual common stock (e.g. S&P 500 name) | `config/stock_universe.yml` |

Stocks in `stock_universe.yml` always map to stress block **EQ** for RC.

## Fields that drive stress RC vs X-Ray only

Implementation: `resolve_stress_asset_block()` in `src/stress_covariance_taxonomy.py`.

| Field | Drives stress block (RC) | Used heavily in X-Ray |
| --- | --- | --- |
| `asset_class` | **Yes** | Yes |
| `subtype` | **Yes** (FI, cash, alternatives) | Yes |
| `main_risk_factor` | **Yes** (FI, alternative) | Yes |
| `credit_quality` | **Yes** (FI → CR) | Diagnostic |
| `risk_role` | **Yes** only `cash_like` + bill subtypes → CA | Yes |
| `sector`, `region`, `thematic_*` | No | Yes |
| `risk_role` (risk_on, defensive, …) | No for block | Yes |
| `secondary_risk_factors` | No | Yes |

Unknown ticker (not in either universe) → block **EQ**, `stress_block_source=unknown`, `silent_default_eq=true`.

## Stress block reference

| Block | Meaning | Typical YAML signals |
| --- | --- | --- |
| EQ | Equity / equity-like | `asset_class: equity`; most `alternative`; stocks |
| CR | Credit / spread | HY, IG corporate, EM debt, bank loan; `main_risk_factor: credit` |
| ND | Nominal duration | Treasuries, aggregate when duration-dominant |
| TI | Inflation-linked | `subtype: tips`, `main_risk_factor: inflation` |
| CO | Commodities | `asset_class: commodity`, commodity alternatives |
| CA | Cash-like | `asset_class: cash`; bill + `cash_like` in `risk_role`; config cash proxy |

## Classification confidence (report-only)

Emitted by `scripts/taxonomy_onboard_report.py` / `src/taxonomy_stress_blocks.py`; **not** stored in universe YAML in V1.

| Level | When |
| --- | --- |
| **high** | Listed in universe; block consistent with asset_class/subtype/main_rf; not hybrid/crypto/leveraged |
| **medium** | REIT, aggregate bond, alternative/multi-asset/covered call; documented hybrid in notes recommended |
| **low** | Missing from universe; crypto; leveraged/inverse; block/tag mismatch warnings |

`needs_review=true` when confidence is medium or low, or any warning is raised.

`classification_method` in agent workflow: `manual` | `rule_based` | `inferred` | `issuer` | `llm_assisted` (document in PR/notes, not YAML enum in V1).

## Onboarding report schema (`taxonomy_onboard_report_v1`)

```json
{
  "version": "taxonomy_onboard_report_v1",
  "tickers": ["VOO"],
  "cash_proxy_ticker": "BIL",
  "per_ticker": [{
    "ticker": "VOO",
    "universe_source": "etf_universe",
    "taxonomy_row_present": true,
    "taxonomy": { "asset_class": "equity", "subtype": "broad_market", "main_risk_factor": "equity" },
    "stress_block": "EQ",
    "stress_block_source": "etf_universe",
    "silent_default_eq": false,
    "classification_confidence": "high",
    "needs_review": false,
    "warnings": [],
    "xray_ready": true,
    "rc_ready": true,
    "pnl_ready_hint": "..."
  }],
  "validators": { "etf_universe": { "status": "PASS" }, "stock_universe": { "status": "PASS" } },
  "summary": { "count": 1, "rc_ready_count": 1, "silent_default_eq_count": 0 }
}
```

## Operator commands

After editing universe YAML:

```bash
python run_etf_universe.py validate
python run_stock_universe.py validate
python run_etf_universe.py check-config --config config.yml
python scripts/taxonomy_onboard_report.py --tickers VOO,HYG,NEWETF --format text
```

Confirm synthetic PnL after adding to portfolio:

```bash
python run_portfolio_review.py
```

Inspect `stress_report.json` → `synthetic_assumptions`, `taxonomy_coverage.blocks_by_ticker`, factor beta coverage.

## Hybrid assets

Document secondary risks in `notes`. Examples: REIT (EQ block, rates in betas); preferred (often CR); convertibles; covered call; multi-asset; leveraged/inverse; crypto.

Do not add a seventh stress block without updating `stress_testing_spec.md` and `stress_covariance_taxonomy.py`.

## Cursor agent

Use **asset-taxonomy-stress-classification** (`.cursor/agents/asset-taxonomy-stress-classification-agent.md`) for guided onboarding.
