# Block 2.6 Portfolio Weakness Map — UI Pareto Layer Specification

Status: **Target / UX contract** (presentation layer only; backend `block_2_6_portfolio_weakness_map` **`heuristic_v2`** is **implemented**).

Related:

- Backend contract: [portfolio_xray_diagnostics_spec.md](portfolio_xray_diagnostics_spec.md) §2.6.1
- Institutional closure: [heuristic_v2 acceptance audit](../audits/2026-05-29_block_2_6_weakness_map_heuristic_v2_acceptance_audit.md)
- Decision: `DEC-2026-05-29-001`
- Visual tokens: [DESIGN.md](../../DESIGN.md) (severity colors, typography)

---

## 1. Purpose and boundary

### 1.1 What this spec owns

- **Weakness Cards** — default user-facing representation of Block 2.6 on Portfolio X-Ray / diagnosis screens.
- **Pareto view** — per risk type, show only what an advisor needs to understand *which* vulnerability is flagged, *why* the severity band was chosen, *which holdings* matter, and *which Stress Lab scenarios* to run next.
- **Mapping rules** from `portfolio_xray.json` → `block_2_6_portfolio_weakness_map` → UI view models.
- **Prioritization** for top-N vs full-eight layouts, confidence caveats, and `Unavailable` handling.

### 1.2 What this spec does not own

- Scoring, rule tables, evidence generation, or Stress Lab execution (`src/block_2_6_portfolio_weakness_map.py`).
- Changes to `block_2_6_portfolio_weakness_map` JSON shape (frozen at `heuristic_v2` for this release).
- Legacy `sections.weakness_map` (stress-coupled; formatters / advanced diagnostics only).

### 1.3 Principle

| Layer | Role |
| --- | --- |
| **Backend** | Full diagnostic contract in `portfolio_xray.json` (machine-readable, audit-grade). |
| **UI Pareto** | Investment diagnosis cards; no raw metric dump, no JSON field names, **no scenario PnL**. |

---

## 2. UI view model (per card)

Each of the eight canonical risk types renders as one **Weakness Card**.

### 2.1 Pareto fields (default — always visible)

| UI field | Type | Max | Source (see §4) |
| --- | --- | --- | --- |
| `card_id` | string | — | `risk_type` (canonical Stress Lab id) |
| `card_title` | string | — | `risk_title` |
| `risk_level` | enum | — | derived from `severity` |
| `risk_level_label` | string | — | human label (§3.1) |
| `short_diagnosis` | string | 1–2 sentences | `short_diagnosis` |
| `why_status` | string | 1–2 sentences | `why_status` (expandable or inline) |
| `key_evidence` | array | **3–5** rows | `key_evidence[]` |
| `linked_assets` | array | **3** rows | `linked_assets[]` |
| `next_tests` | array | **3** labels | `next_tests` ids → Stress Lab labels |

### 2.2 Advanced / expandable (never in default card body)

| UI field | Backend source |
| --- | --- |
| `score` | `score_0_100` |
| `confidence` | `confidence` |
| `confidence_reason` | `confidence_reason` |
| `why_it_matters` | `why_it_matters` |
| `full_evidence` | `evidence[]` |
| `limitations` | `limitations[]` |
| `data_quality_warnings` | `data_quality_warnings[]` |
| `signal_scores` | `signal_scores` (optional backend diagnostics) |
| `legacy_risk_aliases` | `metadata.legacy_risk_aliases` (read-only migration aid) |

### 2.3 Block-level chrome (above cards)

| UI field | Backend source |
| --- | --- |
| `section_title` | constant: "Portfolio weakness map" |
| `section_summary` | `summary` |
| `block_status_chip` | `status` (`ok` / `partial` / `unavailable`) — tone only for users |
| `next_tests_global` | `next_tests_global` (deduped scenario ids) |
| `pre_stress_disclaimer` | constant: scores are hypotheses; run Stress Lab for losses |

---

## 3. Severity and confidence presentation

### 3.1 Severity labels

| Backend `severity` | UI `risk_level_label` |
| --- | --- |
| `Low` | Low vulnerability |
| `Medium` | Medium vulnerability |
| `High` | High vulnerability |
| `Unavailable` | Insufficient evidence |

Do not show raw `score_0_100` in the default card; optional in advanced panel.

### 3.2 Confidence caveats

When `confidence` is `low` or `unavailable`, show `confidence_reason` in a subdued callout. When `severity` is `Unavailable`, hide score and emphasize `limitations[0]` plus suggested `next_tests`.

### 3.3 Prioritization

Default sort for top-N (N=3) cards:

1. `severity` rank: High → Medium → Low → Unavailable
2. `score_0_100` descending (nulls last)
3. Stable tie-break: canonical `RISK_TYPES` order

Full-eight view uses canonical order (`equity_shock` … `recession_severe`).

---

## 4. Backend → UI mapping

| UI field | JSON path |
| --- | --- |
| Block root | `portfolio_xray.json` → `block_2_6_portfolio_weakness_map` |
| Cards array | `.risk_types[]` |
| Global next tests | `.next_tests_global[]` |
| Ruleset badge (advanced) | `.metadata.rule_version` (`heuristic_v2`) |

**Do not read** `sections.weakness_map` for product UI after v2 migration.

### 4.1 Scenario id → label

Map `next_tests` entries using Stress Lab scenario display names from [stress_lab_layer_spec.md](stress_lab_layer_spec.md) §3.1.2. `risk_type` on the card equals the primary scenario id for that vulnerability family.

---

## 5. Acceptance criteria (UI)

- [ ] Eight cards max; no `volatility_spike` card from product block.
- [ ] Default card shows `short_diagnosis`, 3–5 `key_evidence` bullets, up to 3 `linked_assets`, and at least one `next_tests` label.
- [ ] No scenario PnL, pass/fail, or `stress_report` field names in visible UI copy.
- [ ] `Unavailable` rows never imply a numeric score.
- [ ] Legacy weakness ids only via advanced alias panel, not as primary card ids.

---

## 6. Mock data note

Use `tests/fixtures/portfolio_xray_golden_v2.json` → `block_2_6_portfolio_weakness_map` for static mocks. Regenerate via `python tests/portfolio_xray_golden_inputs.py` when the backend contract changes.
