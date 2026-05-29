# Block 4 Diagnosis v2 Specification

This document owns the **V2** Problem Classification and Candidate Launchpad contracts for the diagnosis-first Portfolio MRI Evidence-to-Problem Translation Layer.

Target implementation package: `src/block_4/` (facade `build_block_4_diagnosis()` — Session 10+).

Taxonomy registry (Session 02): `src/block_4/problem_taxonomy.py` — `PROBLEM_REGISTRY`, `ACTION_PATH_REGISTRY`.

Evidence extraction (Session 03): `src/block_4/evidence_extraction.py` — `extract_evidence_signals()`, `EvidenceSignal`, `EvidenceExtractionResult`.

Problem scoring (Session 04): `src/block_4/problem_scoring.py` — `score_problems()`, `ProblemScoringResult`, `ProblemScoreRow`.

Severity and confidence (Session 05): `src/block_4/severity_confidence.py`, thresholds in `config/block_4_thresholds.yml` via `src/block_4/thresholds.py`.

Problem prioritization (Session 06): `src/block_4/problem_prioritization.py` — `prioritize_problems()`, `ProblemPrioritizationResult`, `RejectedProblemRow`.

Action path mapping (Session 07): `src/block_4/action_path_mapping.py` — `map_action_paths()`, `build_problem_row()`, `build_suggested_actions()`.

Launchpad cards (Session 08): `src/block_4/launchpad_cards.py` — `build_launchpad_cards()`, `build_candidate_launchpad_v2_document()`.

No-trade gate (Session 09): `src/block_4/no_trade_gate.py` — `evaluate_no_trade_gate()`, `build_diagnosis_summary()`.

Diagnosis facade (Session 10): `src/block_4/diagnosis_builder.py` — `build_block_4_diagnosis()`, `write_block_4_diagnosis_outputs()`.

Archetype fixtures (Session 11): `tests/block_4_fixtures.py`, `tests/fixtures/block_4/archetype_manifest.json`, `tests/test_block_4_v2_archetype_fixtures.py`.

Live product validation (Session 12): `scripts/validate_block_4_live.py` (`--refresh-diagnosis`); live E2E v2 gates in `src/live_core_e2e.py`; `tests/test_block_4_v2_live_validation.py`.

Documentation + operator guide + diagnostic journey (Session 13): SPEC/OUTPUTS/TESTING, [product_flow_operator_guide.md](../product_flow_operator_guide.md), `diagnostic_journey/view_model.py` v2 bridge fields.

Institutional closure (Session 14): V1 product validators removed; legacy builders frozen; [Session 14 audit](../audits/2026-05-29_block_4_v2_session_14_institutional_closure.md).

Current shipped implementation remains **V1** (`src/problem_classification.py`, `src/candidate_launchpad.py`). V2 replaces V1 logic without changing Blocks 2–3 formulas or Candidate Factory behavior.

Related:

- V1 Problem Classification: [problem_classification_spec.md](problem_classification_spec.md)
- V1 Candidate Launchpad: [candidate_launchpad_spec.md](candidate_launchpad_spec.md)
- Session 00 gap audit: [2026-05-29_block_4_v2_session_00_gap_audit.md](../audits/2026-05-29_block_4_v2_session_00_gap_audit.md)
- Migration decision: `DEC-2026-05-29-013`

Status: **implemented** (Sessions 02–14). Canonical product contract for Block 4 decision entry.

---

## 1. Scope and boundary

Block 4 v2 translates **read-only** evidence from Blocks 2–3 into:

- one **primary** portfolio problem;
- up to two **secondary** problems;
- **rejected** problem candidates with reasons;
- **suggested action paths** (hypotheses, not trades);
- **Launchpad cards** (methods to test, not portfolios);
- **no-trade / monitor** outcome when appropriate.

### Reads

| Artifact | Product blocks used (primary) |
| --- | --- |
| `portfolio_xray.json` | `block_2_1_asset_allocation` … `block_2_6_portfolio_weakness_map` |
| `stress_report.json` | `hedge_gap_analysis_v1`, `current_portfolio_stress_scorecard_v1` (+ documented legacy fallbacks) |

Legacy `sections.*` on X-Ray may be used **only** as fallback with `evidence_path: legacy_fallback`.

### Writes

| Artifact | Path | Schema |
| --- | --- | --- |
| Problem Classification | `{output_dir_final}/analysis_subject/problem_classification.json` | `problem_classification_v2` |
| Candidate Launchpad | `{output_dir_final}/analysis_subject/candidate_launchpad.json` | `candidate_launchpad_v2` |

Filenames are unchanged from V1 (six-file product bundle). No separate `block_4_diagnosis.json` in Core MVP unless a later session adds an optional index file.

### Does not

- compute new portfolio metrics;
- modify Blocks 2–3 builders or stress formulas;
- run Candidate Factory or optimizers;
- emit weights or rebalance instructions;
- write Selection Engine / Decision Verdict outcomes;
- let LLM prose alter diagnosis fields (`ai_commentary_context.json` may explain JSON only).

### Out of scope (downstream)

- Portfolio Alternatives Builder execution — [portfolio_alternatives_builder_spec.md](portfolio_alternatives_builder_spec.md)
- Candidate Factory 4.1–4.9 — [candidate_factory_layer_spec.md](candidate_factory_layer_spec.md)
- Current vs Candidate / Decision Verdict — Block 5 specs

---

## 2. Workflow placement

```text
Blocks 2–3 (portfolio_xray.json + stress_report.json)
  → Evidence extraction (Session 03)
  → Problem scoring (Session 04)
  → Severity + confidence (Session 05)
  → Prioritization (Session 06)
  → Action paths (Session 07)
  → Launchpad cards (Session 08)
  → No-trade gate (Session 09)
  → problem_classification.json (v2)
  → candidate_launchpad.json (v2)
```

Written from `run_report.py` when `not core_blocks_only` (same gate as V1). Absent on `run_core_diagnostics.py` (hygiene unchanged).

---

## 3. Problem Classification v2 contract

### 3.1 Top-level shape

```json
{
  "schema_version": "problem_classification_v2",
  "diagnostic_only": true,
  "diagnosis_mode": "current_portfolio_problem_classification",
  "ruleset_version": "block_4_v2_2026_06",
  "status": "ok",
  "generated_at": "2026-05-29T12:00:00Z",
  "analysis_end": "2026-04-30",
  "source_artifacts": {
    "portfolio_xray": "portfolio_xray.json",
    "stress_report": "stress_report.json"
  },
  "primary_problem": {},
  "secondary_problems": [],
  "rejected_problems": [],
  "suggested_actions": [],
  "no_trade_or_monitoring_view": {},
  "data_quality_warnings": [],
  "diagnostics_meta": {},
  "problems": [],
  "summary": {},
  "warnings": []
}
```

| Field | Required | Meaning |
| --- | --- | --- |
| `schema_version` | yes | Must be `problem_classification_v2`. |
| `diagnostic_only` | yes | Must be `true`. |
| `diagnosis_mode` | yes | Must be `current_portfolio_problem_classification`. |
| `ruleset_version` | yes | Bump when scoring/threshold logic changes (not on copy-only edits). Initial: `block_4_v2_2026_06`. |
| `status` | yes | `ok` \| `partial` \| `unavailable` — builder health, not portfolio pass/fail. |
| `primary_problem` | yes | Single `ProblemRow` object (see §3.2). |
| `secondary_problems` | yes | Array, **max 2** distinct `ProblemRow` objects. |
| `rejected_problems` | yes | Array (may be empty) of `RejectedProblemRow` (see §3.3). |
| `suggested_actions` | yes | Deduped action-path list (see §3.4). |
| `no_trade_or_monitoring_view` | yes | No-trade gate output (see §3.5). |
| `data_quality_warnings` | yes | Array of English strings (may be empty). |
| `diagnostics_meta` | yes | Pipeline metadata (see §3.6). |
| `problems` | yes | **Compatibility shim:** `[primary_problem] + secondary_problems` (max 3 rows). Same shape as V1 `problems[]` for readers not yet on v2. |
| `summary` | yes | See §3.7. |
| `warnings` | yes | Top-level pipeline warnings (may be empty). |

Optional provenance keys (when evaluated): `hedge_gap_source`, `stress_scorecard_source`, `weakness_map_source` — same semantics as V1.

### 3.2 `ProblemRow` (primary and secondary)

```json
{
  "problem_id": "weak_crisis_resilience",
  "problem_id_legacy": "weak_crisis_resilience",
  "label_en": "Weak crisis resilience",
  "severity": "high",
  "confidence": "high",
  "short_diagnosis_en": "Large stress losses with limited internal offset.",
  "why_it_matters_en": "Severe scenarios dominate downside; internal hedges did not materially offset losses.",
  "evidence_refs": [],
  "negative_evidence_refs": [],
  "suggested_action_path_id": "improve_crisis_resilience",
  "secondary_action_path_ids": ["reduce_drawdown_risk"],
  "candidate_method_suggestions": [
    {
      "candidate_method_id": "minimum_cvar_constrained",
      "rationale_en": "Tests tail-loss reduction under stress-aware construction."
    }
  ],
  "do_not_overreact_reason_en": "Elevated equity beta is secondary; stress losses drive the primary diagnosis.",
  "risk_of_misinterpretation_en": "Do not treat low normal-period volatility as crisis safety.",
  "reasonable_paths_to_test": ["Improve crisis resilience", "Reduce drawdown"],
  "scoring": {
    "raw_score": 0.78,
    "decision_score": 0.85,
    "stress_confirmation": "confirmed",
    "materiality": "high"
  }
}
```

| Field | Required | Meaning |
| --- | --- | --- |
| `problem_id` | yes | Stable id from §4.1. |
| `problem_id_legacy` | optional | V1 alias when renamed (e.g. `high_drawdown_risk` for `high_drawdown`). |
| `label_en` | yes | Client-facing English label. |
| `severity` | yes | `low` \| `medium` \| `high` \| `unavailable`. |
| `confidence` | yes | `low` \| `medium` \| `high`. |
| `short_diagnosis_en` | yes | One-sentence headline. |
| `why_it_matters_en` | yes | Short decision relevance (2–3 sentences max in product UI). |
| `evidence_refs` | yes | Non-empty array of `EvidenceRef` (§3.8). |
| `negative_evidence_refs` | yes | Array (may be empty) of contradicting `EvidenceRef`. |
| `suggested_action_path_id` | yes | Primary action path id from §4.2. |
| `secondary_action_path_ids` | yes | Array (may be empty) of additional path ids. |
| `candidate_method_suggestions` | yes | Array (may be empty for monitor/no-act problems). |
| `do_not_overreact_reason_en` | optional | When severity is high but context warrants caution. |
| `risk_of_misinterpretation_en` | optional | Common misread guardrail. |
| `reasonable_paths_to_test` | yes | **V1 shim:** human goal strings for Launchpad (same as V1 field). |
| `scoring` | yes | Audit metadata (not shown as KPI in client PDF). |

**Compatibility shim for `problems[]` rows:** When mirrored into `problems[]`, each row must also include V1-shaped fields:

- `label` = `label_en`
- `evidence` = compact copy of `evidence_refs` (may omit `normalized_score` if absent)
- `reasonable_paths_to_test` unchanged

### 3.3 `RejectedProblemRow`

```json
{
  "problem_id": "high_volatility",
  "reject_reason_code": "stress_not_confirmed_below_materiality",
  "reject_reason_en": "Volatility is elevated but stress losses are not material and confirmation is weak.",
  "top_evidence_refs": []
}
```

### 3.4 `suggested_actions[]`

```json
{
  "action_path_id": "improve_crisis_resilience",
  "label_en": "Improve crisis resilience",
  "source_problem_ids": ["weak_crisis_resilience"],
  "priority": 1
}
```

Deduped across primary + secondary. `priority` starts at 1 for the primary problem's action path.

### 3.5 `no_trade_or_monitoring_view`

```json
{
  "outcome": "proceed_to_launchpad",
  "headline_en": "Stress-confirmed crisis weakness warrants testing a defensive hypothesis.",
  "reasons": ["Primary confidence is high", "Worst synthetic loss exceeds materiality floor"],
  "recommended_next_step": "select_launchpad_card",
  "launchpad_suppressed": false
}
```

| Field | Required | Values |
| --- | --- | --- |
| `outcome` | yes | `proceed_to_launchpad` \| `monitor` \| `do_not_act_yet` |
| `headline_en` | yes | Single user-facing sentence. |
| `reasons` | yes | Array of English strings (may be empty when outcome is proceed). |
| `recommended_next_step` | yes | `select_launchpad_card` \| `monitor_quarterly` \| `rerun_diagnostics` \| `resolve_data` |
| `launchpad_suppressed` | yes | When `true`, cards limited to monitor / review / data-quality goals. |

### 3.6 `diagnostics_meta`

| Field | Required | Meaning |
| --- | --- | --- |
| `hedge_gap_source` | optional | `hedge_gap_analysis_v1` or legacy path id. |
| `stress_scorecard_source` | optional | `current_portfolio_stress_scorecard_v1` or legacy path id. |
| `weakness_map_source` | optional | `block_2_6_portfolio_weakness_map` when present. |
| `evidence_signal_count` | yes | Count of extracted signals (Session 03+). |
| `problems_evaluated` | yes | Count of taxonomy ids evaluated (15). |
| `problems_activated` | yes | Count before prioritization cut. |
| `legacy_sections_fallback_used` | optional | `true` if any evidence used legacy `sections.*`. |

### 3.7 `summary`

| Field | Required | Meaning |
| --- | --- | --- |
| `primary_problem_id` | yes | Must equal `primary_problem.problem_id`. |
| `n_secondary` | yes | `len(secondary_problems)`. |
| `n_rejected` | yes | `len(rejected_problems)`. |
| `n_problems` | yes | `1 + n_secondary` (must equal `len(problems)`). |
| `current_portfolio_acceptable` | yes | `true` iff primary is `current_portfolio_acceptable`. |
| `no_trade_outcome` | yes | Copy of `no_trade_or_monitoring_view.outcome`. |

### 3.8 `EvidenceRef`

```json
{
  "evidence_id": "ev_3_3_offset_coverage_main",
  "source_block": "block_3_3_hedge_gap_analysis",
  "source_artifact": "stress_report.json",
  "signal": "offset_coverage_ratio",
  "value": 0.21,
  "normalized_score": 0.79,
  "severity": "high",
  "confidence": "high",
  "interpretation_en": "Only 21% of losses from hurt assets were offset by assets that helped.",
  "why_relevant_to_problem_en": "Supports weak_hedge_behavior and weak_crisis_resilience.",
  "linked_assets": ["TLT", "GLD"],
  "limitation_en": null,
  "evidence_path": "primary"
}
```

| Field | Required | Meaning |
| --- | --- | --- |
| `evidence_id` | yes | Stable id unique within the problem row. |
| `source_block` | yes | Product block id (e.g. `block_2_2_portfolio_metrics`, `block_3_3_hedge_gap_analysis`). |
| `source_artifact` | yes | `portfolio_xray.json` or `stress_report.json`. |
| `signal` | yes | Machine signal name (see Session 00 audit matrix). |
| `value` | optional | Scalar or small object; JSON-serializable. |
| `normalized_score` | optional | 0–1 contribution strength when scoring supplies it. |
| `severity` | optional | Signal-level severity band. |
| `confidence` | optional | Signal-level confidence band. |
| `interpretation_en` | yes | Plain English, no JSON field names visible to client. |
| `why_relevant_to_problem_en` | yes | Link to problem id(s). |
| `linked_assets` | optional | Ticker list when applicable. |
| `limitation_en` | optional | Stale data, fallback path, or pre-stress-only caveat. |
| `evidence_path` | yes | `primary` \| `legacy_fallback` \| `pre_stress_only` |

Every `ProblemRow` must have **≥1** `evidence_refs` entry with `evidence_path != pre_stress_only` **or** an explicit `limitation_en` on all refs when diagnosis is pre-stress-only.

---

## 4. Controlled vocabularies

### 4.1 Problem ids (`problem_id`)

| `problem_id` | `label_en` (default) |
| --- | --- |
| `high_volatility` | High volatility |
| `high_drawdown` | High drawdown |
| `high_equity_beta` | High equity beta |
| `high_concentration` | High concentration |
| `poor_diversification` | Poor diversification |
| `weak_hedge_behavior` | Weak hedge behavior |
| `poor_rates_up_behavior` | Poor rates-up behavior |
| `weak_crisis_resilience` | Weak crisis resilience |
| `high_tail_risk` | High tail risk |
| `credit_liquidity_fragility` | Credit / liquidity fragility |
| `duration_rates_vulnerability` | Duration / rates vulnerability |
| `low_return_risk_efficiency` | Low return / risk efficiency |
| `current_portfolio_acceptable` | Current portfolio already acceptable |
| `evidence_insufficient_data_quality` | Evidence quality requires review |
| `evidence_insufficient_conflicting_signals` | Conflicting evidence — do not act yet |

Legacy V1 id mapping:

| V1 | V2 |
| --- | --- |
| `high_drawdown_risk` | `high_drawdown` |
| `data_review_required` | `evidence_insufficient_data_quality` |

### 4.2 Action path ids (`action_path_id`)

| `action_path_id` | Human label (`label_en`) |
| --- | --- |
| `reduce_volatility` | Reduce volatility |
| `reduce_drawdown_risk` | Reduce drawdown |
| `improve_diversification` | Improve diversification |
| `reduce_concentration` | Reduce concentration |
| `improve_crisis_resilience` | Improve crisis resilience |
| `reduce_equity_beta` | Reduce equity beta |
| `reduce_duration_rates_sensitivity` | Reduce duration / rates sensitivity |
| `improve_hedge_behavior` | Improve hedge behavior |
| `reduce_tail_risk` | Reduce tail risk |
| `reduce_credit_liquidity_risk` | Reduce credit / liquidity risk |
| `improve_return_risk_balance` | Improve return / risk balance |
| `compare_against_simple_benchmark` | Compare against simple benchmark |
| `keep_current_portfolio_and_monitor` | Keep current portfolio and monitor |
| `test_another_candidate` | Test another candidate |
| `evidence_insufficient_do_not_act_yet` | Do not act yet — resolve evidence first |

`reasonable_paths_to_test` strings remain the **human goal labels** in the right column for Launchpad compatibility.

### 4.3 Scoring enums

| Field | Values |
| --- | --- |
| `scoring.stress_confirmation` | `confirmed` \| `contradicted` \| `pre_stress_only` \| `unavailable` |
| `scoring.materiality` | `high` \| `medium` \| `low` \| `none` |

---

## 5. Candidate Launchpad v2 contract

### 5.1 Top-level shape

```json
{
  "schema_version": "candidate_launchpad_v2",
  "diagnostic_only": true,
  "ruleset_version": "block_4_v2_2026_06",
  "generated_at": "2026-05-29T12:00:00Z",
  "analysis_end": "2026-04-30",
  "source_artifacts": {
    "problem_classification": "problem_classification.json"
  },
  "launchpad_outcome": "proceed_to_launchpad",
  "cards": [],
  "summary": {},
  "warnings": []
}
```

| Field | Required | Meaning |
| --- | --- | --- |
| `schema_version` | yes | Must be `candidate_launchpad_v2`. |
| `ruleset_version` | yes | Must match PC v2 ruleset when built in same run. |
| `launchpad_outcome` | yes | Copy of `no_trade_or_monitoring_view.outcome` from PC v2. |
| `cards` | yes | Non-empty unless `status=unavailable` on PC (then single monitor card allowed). |

### 5.2 Card row (`cards[]`)

V2 cards **extend** V1 card fields (all V1 fields remain required for shim readers).

| Field | Required | Meaning |
| --- | --- | --- |
| `card_id` | yes | Stable id (`launchpad_NN_<slug>`). |
| `title` | yes | Short card title (may equal goal). |
| `goal` | yes | Human goal label (V1 compatible). |
| `description` | yes | Plain English (V1). |
| `source_problem_id` | yes | Must exist in PC `primary_problem` or `secondary_problems`. |
| `source_problem_label` | yes | Copy of `label_en`. |
| `rationale` | yes | `{severity, confidence, evidence}` — V1 shape; `evidence` may mirror top `evidence_refs`. |
| `suggested_methods` | yes | `[{candidate_method_id}]` — V1 shape. |
| `generates_portfolio` | yes | Must be `false`. |
| `requires_user_action` | yes | V1 semantics. |
| `why_this_path_en` | yes | Why this hypothesis follows from the diagnosis. |
| `what_this_tests_en` | yes | What the user would learn from running the test. |
| `default_method` | optional | One `candidate_method_id` from `suggested_methods`; required when `suggested_methods` non-empty. |
| `simple_constraints` | yes | Array of English constraint hints (may be empty; not applied in V1 builder). |
| `expected_tradeoff_to_check_en` | yes | e.g. lower tail loss vs lower expected return. |
| `not_a_recommendation_disclaimer_en` | yes | Fixed product disclaimer string (see §5.4). |
| `when_to_skip_this_test_en` | yes | Explicit skip conditions. |
| `priority_rank` | yes | Integer ≥ 1; lower = higher priority. |

**Card count:** max **4** cards per run (primary path + secondaries + optional benchmark compare). Monitor-only runs may emit 1–2 cards when `launchpad_suppressed=true`.

### 5.3 `summary`

| Field | Required | Meaning |
| --- | --- | --- |
| `n_cards` | yes | `len(cards)`. |
| `primary_card_id` | yes | Must equal `cards[0].card_id`. |
| `has_portfolio_generating_options` | yes | `true` if any card has non-empty `suggested_methods`. |
| `has_keep_current_option` | yes | V1 semantics. |
| `launchpad_outcome` | yes | Duplicate of top-level `launchpad_outcome`. |

### 5.4 Standard disclaimer string

`not_a_recommendation_disclaimer_en` must equal (or start with):

> This card suggests a hypothesis to test, not a buy or sell instruction.

### 5.5 Method allowlist

`suggested_methods[].candidate_method_id` and `default_method` must be in the Launchpad allowlist (same set as V1 `LAUNCHPAD_KNOWN_METHOD_IDS` in `scripts/core_mvp_validation_contract.py`, extended only via spec + DEC).

---

## 6. Cross-artifact handoff (v2)

1. `candidate_launchpad.json` `analysis_end` must match `problem_classification.json`.
2. Every card `source_problem_id` (when not null) must appear in PC v2 `primary_problem.problem_id` or `secondary_problems[].problem_id`.
3. `launchpad_outcome` must equal PC `summary.no_trade_outcome`.
4. `source_artifacts.problem_classification` must be `problem_classification.json`.
5. When PC `primary_problem.problem_id` is `current_portfolio_acceptable` or evidence-insufficient ids, cards must not suggest builder methods except benchmark compare when explicitly allowed.

---

## 7. V1 compatibility (DEC-2026-05-29-013, closed Session 14)

**Frozen (Session 14):**

- Product validators: **v2 only** — `check_problem_classification_v2`, `check_candidate_launchpad_v2`, `check_block_4_v2_diagnosis_handoff` in `scripts/core_mvp_validation_contract.py`.
- Live E2E: v2 gates since Session 12; v1 validators **removed** Session 14.
- JSON shim retained: flat `problems[]` mirror with severity `medium` → `moderate` for legacy readers.
- Legacy builders `src/problem_classification.py` / `src/candidate_launchpad.py` remain for unit tests only; not used in `run_report.py`.

---

## 8. Verification

Contract-only tests (Session 01):

```text
python -m pytest tests/test_block_4_v2_contract.py -q
```

Full Block 4 bundle (during migration):

```text
python -m pytest tests/test_block_4_v2_contract.py tests/test_block_4_decision_entry_contract.py -q
```

Implementation tests (Session 11+):

```text
python -m pytest tests/test_block_4_v2_*.py tests/test_block_4_decision_entry_contract.py -q
```

Live E2E (Session 12+):

```text
python scripts/validate_block_4_live.py --refresh-diagnosis
python scripts/verify_live_core_e2e.py --profile diagnosis_only
```

---

## 9. Change policy

- Bump `ruleset_version` when scoring weights, thresholds in `config/block_4_thresholds.yml`, or prioritization rules change.
- Bump `schema_version` only on breaking JSON shape changes (requires DEC + migration note).
- Problem id or action-path id additions require §4 update + taxonomy module + contract tests in the same change.
