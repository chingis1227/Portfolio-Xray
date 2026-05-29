# Block 2.4 Hidden Exposure — UI Pareto Layer Specification

Status: **Implemented** (presentation layer; backend `block_2_4_hidden_exposure` institutional v2 unchanged). Presenter: `src/block_2_4_hidden_exposure_ui.py`.

Related:

- Backend contract: [portfolio_xray_diagnostics_spec.md](portfolio_xray_diagnostics_spec.md) §2.4.1
- Institutional closure: [Session 13 audit](../audits/2026-05-29_block_2_4_session_13_institutional_closure.md)
- Visual tokens: [DESIGN.md](../../DESIGN.md) (severity colors, typography)

---

## 1. Purpose and boundary

### 1.1 What this spec owns

- **Hidden Risk Cards** — the default user-facing representation of Block 2.4 on Portfolio X-Ray / diagnosis screens.
- **Pareto view** — per alert, show only the minimum set an advisor or investor needs to understand *where* the hidden risk is, *why* the system flags it, *which holdings* matter, and *what to run next* in Stress Lab.
- **Mapping rules** from `portfolio_xray.json` → `block_2_4_hidden_exposure` → UI view models.
- **Prioritization** for top-3 vs full-six layouts, confidence caveats, and `Unavailable` handling.

### 1.2 What this spec does not own

- Scoring, thresholds, evidence generation, or Stress Lab execution (backend `src/block_2_4_hidden_exposure.py`).
- Changes to `block_2_4_hidden_exposure` JSON shape (frozen at institutional v2).
- Legacy `sections.hidden_risk_detector` (formatters / advanced diagnostics only).

### 1.3 Principle

| Layer | Role |
| --- | --- |
| **Backend** | Full diagnostic contract in `portfolio_xray.json` (machine-readable, audit-grade). |
| **UI Pareto** | Investment diagnosis cards; no raw metric dump, no JSON field names visible. |

---

## 2. UI view model (per card)

Each of the six alerts renders as one **Hidden Risk Card**.

### 2.1 Pareto fields (default — always visible)

| UI field | Type | Max | Source (see §4) |
| --- | --- | --- | --- |
| `card_id` | string | — | alert key |
| `card_title` | string | — | fixed label per alert |
| `risk_level` | enum | — | derived from `status` |
| `risk_level_label` | string | — | human label (§3.1) |
| `short_diagnosis` | string | 1 sentence | `explanation` + optional synthesis |
| `key_evidence` | array | **3–5** rows | ranked subset of `evidence` |
| `linked_assets` | array | **3** rows | `contributing_assets` |
| `next_tests` | array | **3** scenario labels | `next_tests` ids → labels |

### 2.2 Advanced / expandable (never in default card body)

| UI field | Backend source |
| --- | --- |
| `score` | `score` |
| `confidence` | `confidence` |
| `confidence_reason` | `confidence_reason` |
| `why_it_matters` | `why_it_matters` |
| `full_evidence` | `evidence[]` (all rows) |
| `limitations` | `limitations[]` |
| `data_quality_warnings` | `data_quality_warnings[]` |
| `insufficient_evidence_reasons` | `insufficient_evidence_reasons[]` |
| `calculation_notes` | `calculation_notes[]` |
| `confirmation_status` | `confirmation_status` |
| `thresholds_meta` | evidence row `threshold` objects |
| `signal_weights` | `diagnostics_meta.signal_weights` (if present) |
| `blocked_upstream_fields` | `diagnostics_meta.blocked_upstream_fields` |
| `ruleset` / `confidence_model` | `diagnostics_meta` |

### 2.3 Block-level chrome (above cards)

| UI field | Backend source |
| --- | --- |
| `section_title` | constant: "Hidden exposure" |
| `section_summary` | `summary` (one line) |
| `block_status_chip` | `status` (`ok` / `partial` / `unavailable`) — internal; user sees summary tone only |
| `top_cards` | first N cards from `top_hidden_risks` (default N=3) |

---

## 3. UI content contract — six cards

Fixed display order in **full view** (matches `ALERT_IDS`):

1. Hidden Equity Beta  
2. Duration Concentration  
3. Credit / Liquidity Risk  
4. Correlation Concentration  
5. Weak Hedge Behavior  
6. Tail Risk  

### 3.1 Risk level mapping

| Backend `alerts.*.status` | UI `risk_level` | UI `risk_level_label` | Visual severity (DESIGN.md) |
| --- | --- | --- | --- |
| `Low` | `low` | Low hidden risk | Teal / muted |
| `Medium` | `medium` | Medium hidden risk | Warning orange |
| `High` | `high` | High hidden risk | Danger red |
| `Unavailable` | `unavailable` | **Not enough data** | Neutral gray — **not** Low |

**Rules:**

- Never map `Unavailable` to Low or green success styling.
- When `confidence` is `low` and `status` is `Medium`, show optional chip **Indicative** on the card (Pareto), full `confidence_reason` in advanced.
- Backend already caps `High` when confidence is low; UI must not re-label Medium as High.

### 3.2 Short diagnosis (one sentence)

**Primary source:** trim `explanation` to one sentence (first sentence if multi-sentence).

**Optional enrichment** (only when `status` ≠ `Unavailable` and top scored evidence exists): append a concrete clause from the highest-priority evidence row (§5.2), e.g.  
*"Portfolio beta and equity factor exposure are both elevated versus thresholds."*

**Unavailable:** use fixed copy:  
*"We do not have enough aligned data to assess this hidden risk dimension."*  
Do not use `explanation` alone if `insufficient_evidence_reasons` is non-empty; prefer the first insufficient-evidence reason shortened to plain English.

### 3.3 Card-specific content hints (for copy / QA)

| `card_id` | `card_title` | Diagnosis theme (what user should understand) |
| --- | --- | --- |
| `hidden_equity_beta` | Hidden Equity Beta | Portfolio may behave more **equity-like** than allocation labels suggest. |
| `duration_concentration` | Duration Concentration | **Rate / duration** sensitivity may dominate despite mixed labels. |
| `credit_liquidity_risk` | Credit / Liquidity Risk | **Credit, carry, or liquidity** sleeves may act like risk-on risk. |
| `correlation_concentration` | Correlation Concentration | Holdings may **move together** (correlation, duplicates, currency). |
| `weak_hedge_behavior` | Weak Hedge Behavior | **Hedge-labeled** positions may not offset risk (preliminary until stress). |
| `tail_risk` | Tail Risk | **Tail losses / drawdowns** may be worse than headline volatility suggests. |

`why_it_matters` stays **advanced only** (investor education expander).

### 3.4 Weak hedge — special Pareto flags

| Backend | UI (Pareto) |
| --- | --- |
| `confirmation_status` = `preliminary` | Badge: **Preliminary** (before Stress Lab) |
| `confirmation_status` = `confirmed` | Badge: **Stress-checked** (Block 3 enrichment present) |
| `data_quality_warnings` contains `preliminary_without_stress_lab` | One-line note under diagnosis: *"Confirm in Stress Lab before treating hedges as effective."* |

Do not claim hedge failure in Pareto copy unless `confirmation_status` = `confirmed` **and** stress enrichment evidence supports it (advanced detail).

### 3.5 Key evidence row shape (UI)

Each Pareto evidence row:

```json
{
  "label": "Portfolio beta vs benchmark",
  "value_display": "0.85 (above moderate threshold)",
  "source_hint": "Portfolio metrics"
}
```

- `label`: humanized `metric` (§5.3), not snake_case in UI.
- `value_display`: formatted `value` + optional threshold context from `interpretation` (truncate technical threshold JSON).
- `source_hint`: map `source` → "Allocation" | "Portfolio metrics" | "Factor exposure" | "Stress cross-check" | "Taxonomy".

**Exclude from Pareto:** rows with `direction` = `missing` unless fewer than 3 non-missing rows exist (then show at most one missing-data line in advanced only).

### 3.6 Linked assets row shape (UI)

```json
{
  "ticker": "GLD",
  "weight_display": "9.0%",
  "role_label": "Commodity sleeve · equity-like behavior"
}
```

- `weight_display`: `weight_pct` × 100, one decimal, with `%`.
- `role_label`: combine `expected_role` + `behavior_flag` when present; else `expected_role` only.

Empty `contributing_assets`: omit linked-assets section; do not show "None".

### 3.7 Next tests (Stress Lab)

Backend `next_tests` holds scenario **ids**. UI shows **labels** (§5.4), max **3** ids in Pareto (preserve backend order).

---

## 4. Backend JSON → UI field mapping

### 4.1 Block envelope

| Backend path | UI field | Notes |
| --- | --- | --- |
| `block_2_4_hidden_exposure.block_id` | — | Internal only |
| `block_2_4_hidden_exposure.block_name` | `section_title` alt | Prefer fixed "Hidden exposure" for product |
| `block_2_4_hidden_exposure.status` | `block_status_chip` | Do not show raw `partial`/`ok` to client; use `summary` tone |
| `block_2_4_hidden_exposure.summary` | `section_summary` | |
| `block_2_4_hidden_exposure.top_hidden_risks[]` | drives `top_cards` order | Match `alert_id` + `status` + `score` |
| `block_2_4_hidden_exposure.data_quality_warnings` | advanced block warnings | |
| `block_2_4_hidden_exposure.diagnostics_meta` | advanced diagnostics drawer | |

### 4.2 Per alert (`alerts.<alert_id>`)

| Backend path | UI Pareto field | UI advanced field |
| --- | --- | --- |
| `status` | `risk_level`, `risk_level_label` | — |
| `explanation` | `short_diagnosis` (primary) | — |
| `evidence[]` | `key_evidence` (subset) | `full_evidence` |
| `contributing_assets[]` | `linked_assets` | — |
| `next_tests[]` | `next_tests` (labeled) | full list in advanced |
| `score` | — | `score` |
| `confidence` | optional `Indicative` chip if `low` | `confidence` |
| `confidence_reason` | — | `confidence_reason` |
| `why_it_matters` | — | `why_it_matters` |
| `limitations[]` | — | `limitations` |
| `data_quality_warnings[]` | weak-hedge one-liner only | full list |
| `insufficient_evidence_reasons[]` | shapes Unavailable copy | advanced |
| `calculation_notes[]` | — | advanced |
| `confirmation_status` | weak-hedge badges only | `confirmation_status` |

### 4.3 Alert id → card id

| Backend `alert_id` | UI `card_id` | UI `card_title` |
| --- | --- | --- |
| `hidden_equity_beta` | `hidden_equity_beta` | Hidden Equity Beta |
| `duration_concentration` | `duration_concentration` | Duration Concentration |
| `credit_liquidity_risk` | `credit_liquidity_risk` | Credit / Liquidity Risk |
| `correlation_concentration` | `correlation_concentration` | Correlation Concentration |
| `weak_hedge_behavior` | `weak_hedge_behavior` | Weak Hedge Behavior |
| `tail_risk` | `tail_risk` | Tail Risk |

---

## 5. Prioritization rules

### 5.1 Section layout: top 3 vs full 6

| Mode | Rule |
| --- | --- |
| **Default (Pareto section)** | Show cards for `top_hidden_risks` in list order (max **3**). If `top_hidden_risks` empty, take top 3 alerts by `score` descending among non-`Unavailable`. |
| **Full view** | Expand to all **6** cards in `ALERT_IDS` order. |
| **Unavailable alerts** | Include in full view with `unavailable` styling; exclude from default top-3 unless fewer than 3 evaluable alerts exist. |

### 5.2 Key evidence ranking (per alert, pick 3–5)

Apply in order; stop at 5 rows:

1. **Scored signals first** — metrics that participate in `heuristic_v2` score for that alert (see per-alert priority lists below).
2. **Severity** — prefer `direction` = `above_threshold` or `conflicting` over `present` over `below_threshold`; skip `missing` in Pareto.
3. **Magnitude** — among numeric values, prefer larger deviation vs threshold when encoded in `interpretation`.
4. **Informational tie-break** — factor variance, PCA cross-ref, stress cross-ref only after scored rows exhausted.

**Per-alert scored-metric priority (first pass):**

| Alert | Priority order (scored / high-signal first) |
| --- | --- |
| `hidden_equity_beta` | `beta_portfolio`, `downside_beta`, `beta_eq`, `rolling_correlation`, `equity_weight`, `risk_on_weight` |
| `duration_concentration` | `fixed_income_weight`, `rates_or_duration_weight`, `beta_rr`, `beta_inf` |
| `credit_liquidity_risk` | `beta_credit`, `credit_liquidity_weight`, `risk_on_or_carry_weight`, `downside_beta` |
| `correlation_concentration` | `highest_pair_correlation`, `duplicate_exposure_weight`, `dominant_main_risk_factor_weight`, `avg_pairwise_correlation`, `lowest_pair_correlation` |
| `weak_hedge_behavior` | `hedge_labeled_weight`, `equity_or_credit_beta`, `downside_beta`, `rolling_correlation` |
| `tail_risk` | `es_95`, `es_99`, `max_drawdown`, `var_95`, `var_99`, `downside_deviation`, `pct_time_underwater`, `downside_beta` |

Second pass (informational, max 2 rows): dominant factor share, hedge gap summary, PCA cross-ref, currency flags — only if fewer than 3 scored rows available.

### 5.3 Metric → label (examples)

| `metric` | UI `label` |
| --- | --- |
| `beta_portfolio` | Portfolio beta vs benchmark |
| `downside_beta` | Downside beta |
| `beta_eq` | Equity factor beta (5Y) |
| `equity_weight` | Equity allocation weight |
| `highest_pair_correlation` | Highest pairwise correlation |
| `duplicate_exposure_weight` | Duplicate exposure overlap |
| `max_drawdown` | Maximum drawdown |
| `hedge_labeled_weight` | Hedge-labeled weight |
| `hedge_gap_summary` | Stress hedge gap (summary) |

### 5.4 Scenario id → UI label (next_tests)

| Scenario id | UI label |
| --- | --- |
| `equity_shock` | Equity shock |
| `rates_shock` | Rates shock |
| `inflation_stagflation` | Inflation / stagflation |
| `credit_shock` | Credit spread shock |
| `liquidity_shock` | Liquidity shock |
| `recession_severe` | Severe recession |
| `commodity_shock` | Commodity shock |
| `usd_shock` | USD shock |
| `volatility_spike` | Volatility spike |

Unknown ids: title-case id with underscores replaced by spaces.

### 5.5 High status + low confidence

| Condition | Pareto behavior |
| --- | --- |
| `status` = `High` and `confidence` = `low` | Should not occur (backend caps High). If seen in stale JSON, display **Medium** + **Indicative**. |
| `status` = `Medium` and `confidence` = `low` | Show **Indicative** chip; do not use alarm-red High styling. |
| `status` = `Unavailable` | Gray card, **Not enough data**; no linked assets; next_tests may still show if backend populated. |

---

## 6. Mock examples (Pareto view models)

Illustrative UI payloads (not backend JSON). Values inspired by live demo book (8-ticker USD).

### 6.1 Hidden Equity Beta

```json
{
  "card_id": "hidden_equity_beta",
  "card_title": "Hidden Equity Beta",
  "risk_level": "low",
  "risk_level_label": "Low hidden risk",
  "short_diagnosis": "The portfolio still shows moderate equity-like market sensitivity, but it is below the threshold for a strong hidden beta alert.",
  "key_evidence": [
    {
      "label": "Portfolio beta vs benchmark",
      "value_display": "0.80 — within low band",
      "source_hint": "Portfolio metrics"
    },
    {
      "label": "Equity factor beta (5Y)",
      "value_display": "0.72 — elevated vs factor threshold",
      "source_hint": "Factor exposure"
    },
    {
      "label": "Equity allocation weight",
      "value_display": "23% of portfolio",
      "source_hint": "Allocation"
    }
  ],
  "linked_assets": [
    { "ticker": "QQQ", "weight_display": "13.0%", "role_label": "US equity growth" },
    { "ticker": "SPY", "weight_display": "10.0%", "role_label": "US equity core" },
    { "ticker": "SCHD", "weight_display": "17.0%", "role_label": "Dividend equity" }
  ],
  "next_tests": [
    { "scenario_id": "equity_shock", "label": "Equity shock" },
    { "scenario_id": "recession_severe", "label": "Severe recession" },
    { "scenario_id": "liquidity_shock", "label": "Liquidity shock" }
  ]
}
```

### 6.2 Correlation Concentration

```json
{
  "card_id": "correlation_concentration",
  "card_title": "Correlation Concentration",
  "risk_level": "medium",
  "risk_level_label": "Medium hidden risk",
  "short_diagnosis": "Several holdings still move together, so diversification may be weaker than the number of tickers suggests.",
  "key_evidence": [
    {
      "label": "Highest pairwise correlation",
      "value_display": "0.78 (GLD–QQQ) — above moderate threshold",
      "source_hint": "Portfolio metrics"
    },
    {
      "label": "Average pairwise correlation",
      "value_display": "0.61 — elevated",
      "source_hint": "Portfolio metrics"
    },
    {
      "label": "Dominant risk-factor bucket",
      "value_display": "Equity-linked factors dominate overlap",
      "source_hint": "Allocation"
    }
  ],
  "linked_assets": [
    { "ticker": "GLD", "weight_display": "9.0%", "role_label": "Commodity · equity-like correlation" },
    { "ticker": "SLV", "weight_display": "9.0%", "role_label": "Precious metals" },
    { "ticker": "QQQ", "weight_display": "13.0%", "role_label": "US equity growth" }
  ],
  "next_tests": [
    { "scenario_id": "equity_shock", "label": "Equity shock" },
    { "scenario_id": "recession_severe", "label": "Severe recession" },
    { "scenario_id": "liquidity_shock", "label": "Liquidity shock" }
  ],
  "indicative_only": true
}
```

### 6.3 Tail Risk

```json
{
  "card_id": "tail_risk",
  "card_title": "Tail Risk",
  "risk_level": "medium",
  "risk_level_label": "Medium hidden risk",
  "short_diagnosis": "Tail and drawdown metrics show meaningful stress-period loss potential despite moderate headline volatility.",
  "key_evidence": [
    {
      "label": "Expected shortfall (95%)",
      "value_display": "−1.4% monthly — above tail threshold",
      "source_hint": "Portfolio metrics"
    },
    {
      "label": "Maximum drawdown",
      "value_display": "−19.8% — persistent underwater episodes",
      "source_hint": "Portfolio metrics"
    },
    {
      "label": "Time underwater",
      "value_display": "57% of window below prior peak",
      "source_hint": "Portfolio metrics"
    },
    {
      "label": "Volatility instability",
      "value_display": "Vol-of-vol 0.03 — monitoring signal",
      "source_hint": "Portfolio metrics"
    }
  ],
  "linked_assets": [
    { "ticker": "SLV", "weight_display": "9.0%", "role_label": "High-volatility sleeve" },
    { "ticker": "QQQ", "weight_display": "13.0%", "role_label": "Growth equity" },
    { "ticker": "TLT", "weight_display": "13.0%", "role_label": "Long duration" }
  ],
  "next_tests": [
    { "scenario_id": "recession_severe", "label": "Severe recession" },
    { "scenario_id": "equity_shock", "label": "Equity shock" },
    { "scenario_id": "liquidity_shock", "label": "Liquidity shock" }
  ],
  "indicative_only": true
}
```

---

## 7. Implementation placement

- `src/block_2_4_hidden_exposure_ui.py` — `build_hidden_risk_cards_pareto(block_2_4: dict) -> dict` (`hidden_risk_cards_pareto_v1`).
- API/site layer consumes Pareto view model; never exposes raw `evidence[].threshold` objects on default screen.
- Unit tests: `tests/test_block_2_4_hidden_exposure_ui.py` (golden Block 2.4 from `tests/fixtures/portfolio_xray_golden_v2.json`).

No change to `build_block_2_4_hidden_exposure` required for this layer.

---

## 8. Acceptance criteria

The UI Pareto layer is **ready for implementation review** when:

| # | Criterion | Verification |
| --- | --- | --- |
| A1 | Default screen shows **≤3** Hidden Risk Cards from `top_hidden_risks`, each with exactly 5 Pareto elements (risk level, diagnosis, ≤5 evidence, ≤3 assets, next tests). | UX review / Storybook |
| A2 | Full view shows **6** cards in fixed order; `Unavailable` cards use **Not enough data**, not Low. | UX review |
| A3 | No raw JSON keys (`beta_portfolio`, `heuristic_v2`, `blocked_upstream_fields`) in default UI. | Copy audit |
| A4 | `score`, full `evidence`, `limitations`, and `diagnostics_meta` appear only behind expand / advanced. | UX review |
| A5 | Weak hedge shows **Preliminary** or **Stress-checked** badge per `confirmation_status`. | Fixture with/without stress enrichment |
| A6 | Next tests link to Stress Lab scenario ids with human labels (§5.4). | Click-through to Stress Lab |
| A7 | **30-second comprehension test:** two non-specialist reviewers can answer: (1) where is the main hidden risk, (2) why the system flags it, (3) which tickers matter, (4) which stress scenarios to run next — using only Pareto cards on a real `portfolio_xray.json`. | Moderated session (n≥2) |

---

## 9. Revision history

| Date | Change |
| --- | --- |
| 2026-05-29 | Initial UI Pareto contract (post institutional v2 closure). |
