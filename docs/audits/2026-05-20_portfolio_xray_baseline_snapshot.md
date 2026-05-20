# Portfolio X-Ray Baseline Snapshot

Date: 2026-05-20

Purpose: fixed baseline for Portfolio X-Ray post-audit governance (Block 2, Phase 12).
Session: 10 (Baseline Snapshot & Wave Closure).
Policy for this closure chat: documentation and verification only — no threshold or X-Ray logic changes.

## Baseline commands

- `python run_report.py --materialize-analysis-subject` (refresh representative `analysis_subject` artifacts)
- `python -m pytest tests/test_portfolio_xray.py tests/test_portfolio_xray_threshold_registry.py tests/test_portfolio_xray_contract.py -q`
- `python tests/portfolio_xray_golden_inputs.py` (regenerate golden fixture only after intentional contract changes)
- `python scripts/verify_docs.py`

Full wave regression bundle (see [TESTING.md](../../TESTING.md)):

```bash
python -m pytest tests/test_portfolio_xray.py tests/test_portfolio_xray_threshold_registry.py tests/test_portfolio_xray_contract.py tests/test_portfolio_metrics_deepening.py tests/test_tail_risk.py tests/test_portfolio_commentary.py -q
python scripts/verify_docs.py
```

## Baseline artifacts to compare after each session

Representative portfolio-first subject folder (current config default):

- `{output_dir_final}/analysis_subject/portfolio_xray.json`
- `{output_dir_final}/analysis_subject/snapshot_3y.json`
- `{output_dir_final}/analysis_subject/snapshot_5y.json`
- `{output_dir_final}/analysis_subject/snapshot_10y.json`
- `{output_dir_final}/analysis_subject/stress_report.json`
- `{output_dir_final}/analysis_subject/results_csv/rc_vol_10y.csv`

Typical `output_dir_final` for Main/policy materialization: `Main portfolio/analysis_subject`.

## Baseline snapshot fingerprints (Session 10)

Captured after `python run_report.py --materialize-analysis-subject` on **2026-05-20**
(`analysis_end`: 2026-04-30; subject role: `user_current_portfolio`; `output_dir_final`:
`Main portfolio/analysis_subject`).

| Artifact | Size (bytes) | sha256 |
| --- | ---: | --- |
| `portfolio_xray.json` | 78025 | `9076638b5621a5fada8272207ce77a00f775a5557f0402d9fea473f69fadd853` |
| `snapshot_3y.json` | 58956 | `b39d8e67ed01876fe113a35ebe8448268be4adb50ab4a99c4ffdd17ca2015aaa` |
| `snapshot_5y.json` | 59074 | `b3dd4a3a79e12e726865e8b94b89114166c1eb151ca9e2af77dcafd0ef016366` |
| `snapshot_10y.json` | 60129 | `da14f0b5569c67db2762cff7f9085b66ca77135366e5f9c946add907f11109f4` |
| `stress_report.json` | 2045942 | `38d556f30243c141877fd02265d6a40ba8ff92dd310d3acb1ec585bd79b93a32` |
| `results_csv/rc_vol_10y.csv` | 94 | `5a2b27b54e8d3b96cf0df165e3f68816c589a1786def28969053e29e645aaf3a` |

Structural regression when artifacts are absent on disk: **golden contract tests**

- `tests/fixtures/portfolio_xray_golden_v2.json` — committed golden `portfolio_xray_v2` document
- `tests/portfolio_xray_golden_inputs.py` — stable builder inputs and regenerate entrypoint
- `tests/test_portfolio_xray_contract.py` — top-level/section contract, post-audit surface fingerprint, live-vs-golden equality

After intentional contract or pipeline changes, re-run materialization and update this table using the compare command in **Compare command template**.

## Baseline contract checklist

1. **Top-level:** `version` = `portfolio_xray_v2`; `diagnostic_only` = true; non-binding disclaimer; `thresholds` == runtime `XRAY_THRESHOLDS` (34 keys, spec §8).
2. **Sections:** all seven keys in `XRAY_SECTION_KEYS` with `status`, `data_sources_used`, `warnings`, `items`, `limitations`.
3. **Provenance (Sessions 03):** `risk_diagnostics`, `factor_exposure`, `risk_budget_view`, `weakness_map` expose `method`, `frequency`, `window`, `n_obs`, `benchmark` (risk budget omits `n_obs` per contract).
4. **Factor inference (Session 04):** `factor_exposure` items include `factor_regression_inference` for 5Y/10Y when `stress_report` provides `factor_regression_*` with HAC inference.
5. **Multi-window + TTR (Session 05):** `risk_diagnostics` includes `multi_window_metrics` when snapshot horizons exist; primary metrics expose `ttr_months` / `recovered` / `treynor` when available.
6. **Concentration (Session 07):** `asset_allocation` includes `weight_concentration` (top-1/top-3 sums, HHI on positive capital weights, `basis=capital_weights`).
7. **Volatility spike (Session 08):** `weakness_map` row `volatility_spike` uses `scenario_coverage.evidence_mode` = `factor_only` (Option B: `beta_vix`, historical `es_95`).
8. **Threshold registry (Session 02):** `tests/test_portfolio_xray_threshold_registry.py` locks spec/runtime parity.
9. **Golden contract (Session 09):** `contract_fingerprint` includes factor inference horizons `5Y`/`10Y`, weight concentration, multi-window panel, factor-only vol spike.
10. **Layer navigation (Session 06):** [portfolio_xray_layer_spec.md](../specs/portfolio_xray_layer_spec.md) maps Block 2.1–2.7 without chat history.

## Golden contract checklist result (Session 10, captured)

Verified via `tests/test_portfolio_xray_contract.py` (`test_golden_post_audit_surface_items`, `test_live_build_matches_golden_document`):

- `factor_inference_horizons`: `5Y`, `10Y`
- `has_weight_concentration`: true
- `has_multi_window_metrics`: true
- `volatility_spike_evidence_mode`: `factor_only`
- `primary_archetype`: present in golden fingerprint

## Compare command template (after materialization refresh)

```bash
python -c "from pathlib import Path; import hashlib; base=Path('Main portfolio/analysis_subject'); files=['portfolio_xray.json','snapshot_3y.json','snapshot_5y.json','snapshot_10y.json','stress_report.json','results_csv/rc_vol_10y.csv']; print('\n'.join(f'{f}|{(base/f).stat().st_size if (base/f).exists() else \"missing\"}|{hashlib.sha256((base/f).read_bytes()).hexdigest() if (base/f).exists() else \"\"}' for f in files))"
```

## Known gaps at baseline (Phase 12 closure status)

| Gap ID | Topic | Status after Sessions 01–10 |
| --- | --- | --- |
| G1 | Thresholds code-only | **Closed** — spec §8 + drift tests (`RM-942`) |
| G2 | Section provenance metadata | **Closed** — sections 2.2/2.3/2.6/2.7 (`RM-943`) |
| G3 | Factor inference not in X-Ray | **Closed** — read-only panel (`RM-944`) |
| G4 | Single-window metrics | **Closed** — `multi_window_metrics` (`RM-945`) |
| G5 | TTR not exposed | **Closed** — primary risk metrics (`RM-945`) |
| G6 | No HHI / concentration | **Closed** — `weight_concentration` (`RM-947`) |
| G7 | No factor/drawdown/ES risk budget | **Deferred** — not in Phase 12 scope |
| G8 | volatility_spike scenario gap | **Closed** — Option B factor-only (`RM-948`) |
| G9 | Stale KNOWN_ISSUES / ROADMAP | **Closed** — Session 01 (`RM-941`) |
| G10 | No X-Ray baseline snapshot | **Closed** — this file (`RM-950`) |
| G11 | No portfolio_xray_layer_spec.md | **Closed** — layer spec (`RM-946`) |

## Session 10 wave closure (2026-05-20)

Scope: baseline artifact checklist, final verification, and documentation pack (no new X-Ray heuristics).

### Verification commands (passed)

- Portfolio X-Ray governance bundle: **40 passed**
  (`tests/test_portfolio_xray.py`, `tests/test_portfolio_xray_threshold_registry.py`, `tests/test_portfolio_xray_contract.py`).
- `python scripts/verify_docs.py`: **OK**

### Baseline hash note

Fingerprints in **Baseline snapshot fingerprints** refreshed on **2026-05-20** after
`python run_report.py --materialize-analysis-subject` (`stress_report.status` = `DIAG_ATTENTION`;
`portfolio_xray.json` present under `Main portfolio/analysis_subject/`).

### Documentation pack

- This baseline snapshot audit (`docs/audits/2026-05-20_portfolio_xray_baseline_snapshot.md`).
- [TESTING.md](../../TESTING.md): wave bundle and golden refresh commands.
- [docs/exec_plans/README.md](../exec_plans/README.md): post-audit roadmap marked **Completed**.
- [CHANGELOG.md](../../CHANGELOG.md): Phase 12 Sessions 00–10 summary.
- [Portfolio X-Ray Methodology Map](2026-05-20_portfolio_xray_methodology_map.md): G10 closed; wave marked historical input.

### Wave status

Portfolio X-Ray post-audit roadmap **Sessions 00–10: complete**. Phase 12 (`RM-940`–`RM-950`) exit condition met: methodology map and layer spec in repo; spec-owned thresholds; provenance on applicable sections; golden contract tests; registers aligned with runtime.
