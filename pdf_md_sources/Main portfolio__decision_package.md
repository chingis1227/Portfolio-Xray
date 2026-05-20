---
title: "Decision Package Summary"
date: "Decision package summary as of 2026-04-30"
documentclass: article
geometry: "left=18mm, right=18mm, top=24mm, bottom=20mm, head=20pt, foot=20pt, footskip=40pt"
fontsize: 10pt
---


Analysis end: 2026-04-30 Investor currency: USD



This summary projects existing decision JSON artifacts. It is not trade advice and does not execute orders.



Comparison highlights

----------------------------------------

Candidate menu

 Intended menu: default_v1 (16/16 candidates scored).

 Product reference menu: default_v1 (16/16 scored).



 Starting portfolio: Current Portfolio: CAGR 9.9%, vol 9.6%, max DD -19.8%, stress Diagnostic review



Robustness scorecard

----------------------------------------

 Favored profile not scored in robustness scorecard.



Portfolio health score

----------------------------------------

 Favored profile not scored in health score.



Selection

----------------------------------------

 Status: Favored profile selected for further review.

 Favored profile: Risk Parity Portfolio

 Favored profile: Risk Parity Portfolio for this comparison.

 Versus starting portfolio: Material benefit versus Current Portfolio may warrant review.



Trade-offs

----------------------------------------

 Comparing Current Portfolio to Risk Parity Portfolio: 6 improving dimension(s), 2 worsening dimension(s).

 Comparing Current Portfolio to Risk Parity Portfolio: 6 improving dimension(s), 2 worsening dimension(s). Improvements include: risk_vol, drawdown, stress_worst_loss, stress_overall. Trade-offs include: return_cagr, risk_adjusted_sharpe. Estimated weight turnover (half-sum) is 17.9%. This summary is diagnostic only and does not instruct trading.

 Turnover (half-sum): 17.9%



Model risk

----------------------------------------

 Overall severity: low

 Model-risk flags are present but none are high severity.



Assumption sensitivity

----------------------------------------

 Stability: stable

 Favored stable rate (Tier A): 100.0%

 Risk Parity Portfolio remained favored in 8 of 8 selection-weight variants (100%). Selection weights are stable, but single-metric window leaders sometimes differ.



Pareto / dominance

----------------------------------------

 Efficient set: 16 profile(s); dominated: 2.

 16 candidate(s) are on the Pareto-efficient set; 2 are dominated on return, risk, drawdown, and stress when applicable. The selection favorite (Risk Parity Portfolio) is not dominated on the evaluated metrics.



Regret analysis

----------------------------------------

 Status: partial

 Favored worst regret: 0.177 (recession_severe).

 Under the favored profile (Risk Parity Portfolio), worst stress regret versus the best available candidate is 17.7% in scenario recession_severe.



Action plan

----------------------------------------

 Status: trades_for_review

 Turnover (half-sum): 17.9%

 Portfolio-first review uses analysis_subject as the baseline; legacy current-vs-policy status is compatibility-only for this run.

 For review (not execution instructions):

 BND buy Δw=0.064 (6.4%)

 GLD buy Δw=0.02 (2.0%)

 QQQ sell Δw=-0.052 (-5.2%)

 SCHD sell Δw=-0.067 (-6.7%)

 SCHP buy Δw=0.096 (9.6%)

 ... and 3 more in action_plan.json



Monitoring — What Changed

----------------------------------------

 Diff status: no_prior_snapshot

 This is the first stored monitoring snapshot for analysis ending 2026-04-30. No prior snapshot is available for comparison. Future runs will show What Changed when a previous snapshot exists under monitoring/latest/.



Decision journal

----------------------------------------

 Generated decision record: see decision_journal.json, journal/latest/, and journal/history/.



Artifact index

----------------------------------------

 candidate_comparison.json

 robustness_scorecard.json

 portfolio_health_score.json

 selection_decision.json

 tradeoff_explanation.json

 model_risk_diagnostics.json

 assumption_sensitivity.json

 pareto_dominance.json

 regret_analysis.json

 action_plan.json

 monitoring_diff.json

 decision_journal.json
