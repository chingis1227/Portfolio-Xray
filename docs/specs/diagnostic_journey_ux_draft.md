# Diagnostic Journey UX Draft (Blocks 1–3)

Status: **UX draft / prototype** — information architecture and guided flow for Core MVP Blocks 1–3. Visual styling follows [DESIGN.md](../../DESIGN.md) (Revolut-inspired tokens). Interactive prototype: `diagnostic_journey/` (Flask, port 5006).

## Product intent

Portfolio MRI is **diagnosis-first**. Blocks 1–3 must read as **one guided diagnostic report**, not three disconnected analytics screens or an optimizer cockpit.

```text
Portfolio Setup (Block 1)
  → Portfolio X-Ray (Block 2)
  → Stress Test Lab (Block 3)
  → Problem bridge preview (Block 4 entry only)
```

## Non-goals (this draft)

- No optimizer-first UI, “best portfolio”, or auto-generated candidates
- No Health Score, Robustness Scorecard, Macro Dashboard, Pareto, Regret, full backtest, tax-aware optimizer, or rebalancing advisor in this surface
- No trading-terminal aesthetics (dense heatmaps, alarm-red dashboards, prediction language)

## Page map

| Section | ID | Primary JSON sources | Ends with |
| --- | --- | --- | --- |
| 1 Portfolio Setup | `#setup` | `run_metadata.json`, `input_assumptions` (via run_metadata), weights from `analysis_setup` | CTA: Run Portfolio X-Ray |
| 2 Portfolio X-Ray | `#xray` | `portfolio_xray.json` (`block_2_1` … `block_2_6`) | CTA: Run Stress Test Lab |
| 3 Stress Test Lab | `#stress` | `stress_report.json` (`stress_results_v1`, `hedge_gap_analysis_v1`, `current_portfolio_stress_scorecard_v1`) | CTA: View suggested improvement paths |
| 4 Problem bridge | `#bridge` | `problem_classification.json` (`problem_classification_v3`), `candidate_launchpad.json` (`candidate_launchpad_v3`); else deterministic fallback from stress/X-Ray | CTA: Open Candidate Launchpad (disabled until wired) |

## Block 2 information hierarchy

| Sub-section | User question | Top-level (always visible) | Drill-down (`<details>`) |
| --- | --- | --- | --- |
| 2.0 Executive diagnosis | What matters overall? | 5–7 plain-language findings | — |
| 2.1 What you own | What do I really hold? | Composition KPIs + one diagnosis | Allocation breakdowns, concentration flags |
| 2.2 How it behaved | How did it perform? | CAGR, vol, Sharpe, MDD, beta, underwater | Tail metrics, correlation pairs, warnings |
| 2.3 Factor drivers | What moves it? | Top 3 factors + interpretation | Regression stats in JSON only (by design) |
| 2.4 Hidden risks | What looks diversified but isn’t? | Alert cards (level, diagnosis, evidence, next tests) | Scores, limitations |
| 2.5 Who creates risk | Where is risk vs capital? | Top RC contributor, top-3 share, gap | Full RC table |
| 2.6 Weakness map | What to stress-test? | High / Medium / Low buckets | Scores, full evidence |

**Copy rule:** Block 2.6 is **pre-stress hypothesis**; Block 3 confirms or refutes via `pre_stress_confirmation_summary` on the stress scorecard.

## Block 3 information hierarchy

| Sub-section | User question | Top-level | Drill-down |
| --- | --- | --- | --- |
| 3.0 Stress diagnosis | Where does it break? | Worst scenario, loss, hurt/helped, hedge gap, one-line diagnosis | — |
| 3.1 Scenario overview | Which scenarios hurt most? | Sorted damaging vs less damaging | Full tables, historical limits |
| 3.2 Assets hurt/helped | Who drove the loss? | Top hurt/helped in worst scenario | Per-scenario attribution |
| 3.3 Hedge gap | Is there internal offset? | Gap label, coverage ratio, protection status | Per-scenario hedge rows |
| 3.4 Stress scorecard | What next for decisions? | Main weakness, confirmed/not confirmed X-Ray risks, failure mode | Full scorecard JSON |

**Language:** Use *hurt*, *helped*, *did not materially help* — not *hedge* unless scenario evidence supports offset.

## Global UX rules (enforced in prototype)

1. Top-level: headline + short diagnosis + ≤5 evidence bullets + next step  
2. Investment language over raw quant labels (e.g. variance risk, not `RC_vol` in primary copy)  
3. Confidence: High / Moderate / Weak evidence / Unavailable / Data insufficient  
4. Scenario framing: “tests how the portfolio might behave under defined assumptions” — not forecasts  
5. Every section has a practical CTA or scroll target to the next step  

## Data boundaries

- UI **must not invent** metrics; missing fields show safe placeholders (`—`, “Data unavailable”).  
- `portfolio_xray.json` and `stress_report.json` under `{output_dir_final}/analysis_subject/` are the primary contracts.  
- Block 4 artifacts use v2 schemas when present; bridge reads `primary_problem`, `no_trade_or_monitoring_view`, and Launchpad `suggested_methods` / `why_this_path_en` / `what_this_tests_en`.  

## Running the prototype

```bash
pip install flask pyyaml
python diagnostic_journey/app.py
```

Open `http://localhost:5006` after a core diagnostics or portfolio review run that materializes `analysis_subject/`.

## Acceptance checklist

See task acceptance criteria in product brief; prototype implements navigation, section order, executive-first X-Ray, stress summary-first Lab, RC vs stress loss separation (copy), and hypothesis-only bridge cards.

## Related specs

- [portfolio_xray_diagnostics_spec.md](portfolio_xray_diagnostics_spec.md) — Block 2 contracts  
- [stress_testing_spec.md](stress_testing_spec.md) — Block 3 contracts  
- [input_assumptions_spec.md](input_assumptions_spec.md) — Block 1 assumptions  
- [runtime_artifact_contract.md](../runtime_artifact_contract.md) — artifact paths  
