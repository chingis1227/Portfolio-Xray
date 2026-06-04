"""Block 4 v3 controlled diagnosis and action-path taxonomy.

Single source of truth for problem ids, action paths, Launchpad goal labels,
and candidate method hints. Scoring and evidence extraction consume this registry;
they must not invent parallel problem labels.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

# ---------------------------------------------------------------------------
# Action paths
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ActionPathDefinition:
    action_path_id: str
    label_en: str
    goal_label: str
    candidate_method_ids: tuple[str, ...]
    launchpad_description_en: str


ACTION_PATH_REGISTRY: dict[str, ActionPathDefinition] = {
    "reduce_volatility": ActionPathDefinition(
        action_path_id="reduce_volatility",
        label_en="Reduce volatility",
        goal_label="Reduce volatility",
        candidate_method_ids=("minimum_variance", "risk_parity", "equal_weight"),
        launchpad_description_en=(
            "Test whether a lower-volatility construction improves the diagnosed risk profile."
        ),
    ),
    "reduce_drawdown_risk": ActionPathDefinition(
        action_path_id="reduce_drawdown_risk",
        label_en="Reduce drawdown",
        goal_label="Reduce drawdown",
        candidate_method_ids=("minimum_variance", "minimum_cvar_constrained", "risk_parity"),
        launchpad_description_en=(
            "Test whether downside-risk-focused candidates reduce drawdown exposure."
        ),
    ),
    "improve_diversification": ActionPathDefinition(
        action_path_id="improve_diversification",
        label_en="Improve diversification",
        goal_label="Improve diversification",
        candidate_method_ids=(
            "equal_weight",
            "equal_weight_by_asset_class",
            "maximum_diversification",
        ),
        launchpad_description_en=(
            "Test whether simpler diversified benchmarks improve concentration and balance."
        ),
    ),
    "reduce_concentration": ActionPathDefinition(
        action_path_id="reduce_concentration",
        label_en="Reduce concentration",
        goal_label="Reduce concentration",
        candidate_method_ids=("equal_weight", "equal_weight_by_asset_class", "risk_budget_by_asset"),
        launchpad_description_en=(
            "Test whether caps or equalized exposures reduce dominant holdings."
        ),
    ),
    "improve_crisis_resilience": ActionPathDefinition(
        action_path_id="improve_crisis_resilience",
        label_en="Improve crisis resilience",
        goal_label="Improve crisis resilience",
        candidate_method_ids=(
            "minimum_cvar_constrained",
            "robust_mv_constrained",
            "robust_scenario",
        ),
        launchpad_description_en=(
            "Test whether stress-aware candidates improve weak crisis or hedge behavior."
        ),
    ),
    "reduce_equity_beta": ActionPathDefinition(
        action_path_id="reduce_equity_beta",
        label_en="Reduce equity beta",
        goal_label="Reduce equity beta",
        candidate_method_ids=("minimum_variance", "risk_parity", "robust_mv_constrained"),
        launchpad_description_en=(
            "Test whether lower market-beta constructions reduce equity shock sensitivity."
        ),
    ),
    "reduce_duration_rates_sensitivity": ActionPathDefinition(
        action_path_id="reduce_duration_rates_sensitivity",
        label_en="Reduce duration / rates sensitivity",
        goal_label="Reduce duration / rates sensitivity",
        candidate_method_ids=("robust_mv_constrained", "minimum_cvar_constrained"),
        launchpad_description_en=(
            "Test whether duration-aware or defensive candidates improve rates-up behavior."
        ),
    ),
    "improve_hedge_behavior": ActionPathDefinition(
        action_path_id="improve_hedge_behavior",
        label_en="Improve hedge behavior",
        goal_label="Improve hedge behavior",
        candidate_method_ids=("minimum_cvar_constrained", "robust_mv_constrained"),
        launchpad_description_en=(
            "Test whether internal offset improves when stress losses occur."
        ),
    ),
    "reduce_tail_risk": ActionPathDefinition(
        action_path_id="reduce_tail_risk",
        label_en="Reduce tail risk",
        goal_label="Reduce tail risk",
        candidate_method_ids=("minimum_cvar_constrained", "robust_mv_constrained"),
        launchpad_description_en=(
            "Test whether tail-risk-aware candidates reduce VaR/ES-style downside."
        ),
    ),
    "reduce_credit_liquidity_risk": ActionPathDefinition(
        action_path_id="reduce_credit_liquidity_risk",
        label_en="Reduce credit / liquidity risk",
        goal_label="Reduce credit / liquidity risk",
        candidate_method_ids=("minimum_cvar_constrained", "robust_mv_constrained"),
        launchpad_description_en=(
            "Test whether defensive candidates reduce credit and liquidity fragility."
        ),
    ),
    "improve_return_risk_balance": ActionPathDefinition(
        action_path_id="improve_return_risk_balance",
        label_en="Improve return / risk balance",
        goal_label="Improve return/risk balance",
        candidate_method_ids=("maximum_diversification", "robust_mv_constrained"),
        launchpad_description_en=(
            "Test whether diversified return/risk methods improve efficiency."
        ),
    ),
    "compare_against_simple_benchmark": ActionPathDefinition(
        action_path_id="compare_against_simple_benchmark",
        label_en="Compare against simple benchmark",
        goal_label="Compare against simple benchmark",
        candidate_method_ids=("equal_weight", "risk_parity"),
        launchpad_description_en=(
            "Compare the diagnosed portfolio with transparent benchmark candidates."
        ),
    ),
    "keep_current_portfolio_and_monitor": ActionPathDefinition(
        action_path_id="keep_current_portfolio_and_monitor",
        label_en="Keep current portfolio and monitor",
        goal_label="Keep current portfolio and monitor",
        candidate_method_ids=(),
        launchpad_description_en=(
            "Do not generate a candidate yet; track changes and warnings."
        ),
    ),
    "test_another_candidate": ActionPathDefinition(
        action_path_id="test_another_candidate",
        label_en="Test another candidate",
        goal_label="Test another candidate",
        candidate_method_ids=(),
        launchpad_description_en=(
            "Explore an alternative hypothesis after reviewing the current diagnosis."
        ),
    ),
    "evidence_insufficient_do_not_act_yet": ActionPathDefinition(
        action_path_id="evidence_insufficient_do_not_act_yet",
        label_en="Do not act yet — evidence does not justify action",
        goal_label="Do not act yet",
        candidate_method_ids=(),
        launchpad_description_en=(
            "Do not rebalance from this diagnosis alone; resolve bad data or monitor mixed evidence first."
        ),
    ),
}


# ---------------------------------------------------------------------------
# Problem definitions
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ProblemDefinition:
    problem_id: str
    label_en: str
    problem_id_legacy: str | None
    technical_definition_en: str
    portfolio_manager_interpretation_en: str
    required_evidence_signals: tuple[str, ...]
    supporting_evidence_signals: tuple[str, ...]
    negative_evidence_signals: tuple[str, ...]
    primary_action_path_id: str
    secondary_action_path_ids: tuple[str, ...]
    default_candidate_method_ids: tuple[str, ...]
    launchpad_card_title_en: str
    launchpad_what_this_tests_en: str
    launchpad_tradeoff_en: str
    launchpad_skip_when_en: str
    do_not_overreact_reason_en: str
    when_not_to_select_as_primary_en: str
    common_false_positive_en: str
    common_false_negative_en: str
    downstream_comparison_focus_en: str
    eligible_as_primary: bool = True
    suppress_launchpad_methods: bool = False
    diagnosis_role: str = "root_cause"
    diagnosis_subtypes: tuple[str, ...] = ()


def _methods_for(*action_ids: str) -> tuple[str, ...]:
    seen: set[str] = set()
    out: list[str] = []
    for aid in action_ids:
        path = ACTION_PATH_REGISTRY.get(aid)
        if path is None:
            continue
        for mid in path.candidate_method_ids:
            if mid not in seen:
                seen.add(mid)
                out.append(mid)
    return tuple(out)


PROBLEM_REGISTRY: dict[str, ProblemDefinition] = {
    "high_volatility": ProblemDefinition(
        problem_id="high_volatility",
        label_en="High volatility",
        problem_id_legacy=None,
        technical_definition_en=(
            "Annualized portfolio volatility exceeds the materiality band on Block 2.2 "
            "and is not fully explained by a stress-confirmed crisis narrative alone."
        ),
        portfolio_manager_interpretation_en=(
            "The portfolio swings more than the investor's risk budget may tolerate in normal periods. "
            "Volatility alone does not prove a bad portfolio — it must be weighed against return and stress behavior."
        ),
        required_evidence_signals=("vol_annual",),
        supporting_evidence_signals=("rolling_volatility", "block_2_6_equity_shock"),
        negative_evidence_signals=("low_stress_loss_with_high_vol",),
        primary_action_path_id="reduce_volatility",
        secondary_action_path_ids=("compare_against_simple_benchmark",),
        default_candidate_method_ids=_methods_for("reduce_volatility"),
        launchpad_card_title_en="Reduce Volatility",
        launchpad_what_this_tests_en=(
            "Whether a lower-volatility construction improves the risk profile without unacceptable return loss."
        ),
        launchpad_tradeoff_en="Lower volatility vs lower expected return and possible turnover.",
        launchpad_skip_when_en="Skip if volatility is only mildly above benchmark and stress losses are immaterial.",
        do_not_overreact_reason_en=(
            "High volatility with strong crisis resilience may be an acceptable growth posture."
        ),
        when_not_to_select_as_primary_en=(
            "When stress-confirmed crisis weakness is material and volatility is only moderately elevated."
        ),
        common_false_positive_en="Short-window vol spike after a single risk-on month.",
        common_false_negative_en="Vol masked by cash sleeve or stale monthly window.",
        downstream_comparison_focus_en="Compare vol, max drawdown, and turnover vs current.",
        diagnosis_role="symptom",
    ),
    "high_drawdown": ProblemDefinition(
        problem_id="high_drawdown",
        label_en="High drawdown",
        problem_id_legacy="high_drawdown_risk",
        technical_definition_en=(
            "Historical or stress-aligned drawdown magnitude exceeds materiality on Block 2.2 or "
            "Block 3.4 worst historical scenario."
        ),
        portfolio_manager_interpretation_en=(
            "The portfolio has experienced or would experience deep peak-to-trough losses. "
            "Drawdown path matters for investor behavior and recovery time."
        ),
        required_evidence_signals=("max_drawdown",),
        supporting_evidence_signals=(
            "worst_historical_scenario",
            "time_underwater",
            "block_2_6_recession_severe",
        ),
        negative_evidence_signals=("drawdown_recovered_quickly",),
        primary_action_path_id="reduce_drawdown_risk",
        secondary_action_path_ids=("improve_crisis_resilience",),
        default_candidate_method_ids=_methods_for("reduce_drawdown_risk", "improve_crisis_resilience"),
        launchpad_card_title_en="Reduce Drawdown Risk",
        launchpad_what_this_tests_en=(
            "Whether downside-focused candidates reduce peak-to-trough loss versus current weights."
        ),
        launchpad_tradeoff_en="Lower drawdown vs lower expected return.",
        launchpad_skip_when_en="Skip if drawdown is historical only and current risk structure materially changed.",
        do_not_overreact_reason_en=(
            "A recovered drawdown with improved diversification may not require action."
        ),
        when_not_to_select_as_primary_en=(
            "When weak crisis resilience with larger stress losses is stress-confirmed."
        ),
        common_false_positive_en="Young ETF history with one short crash window.",
        common_false_negative_en="Drawdown diluted by recent rally without fixing tail structure.",
        downstream_comparison_focus_en="Compare max drawdown, recovery time, and stress replay loss.",
        diagnosis_role="symptom",
    ),
    "high_equity_beta": ProblemDefinition(
        problem_id="high_equity_beta",
        label_en="High equity beta",
        problem_id_legacy=None,
        technical_definition_en=(
            "Portfolio beta to the equity factor or benchmark exceeds the high band on Blocks 2.2/2.3 "
            "or hidden equity beta alert is elevated on Block 2.4."
        ),
        portfolio_manager_interpretation_en=(
            "The portfolio behaves like equities even when labels suggest balance. "
            "Equity beta is a symptom; crisis stress confirms whether it is decision-relevant."
        ),
        required_evidence_signals=("beta_portfolio", "beta_eq"),
        supporting_evidence_signals=("hidden_equity_beta", "block_2_6_equity_shock"),
        negative_evidence_signals=("stress_loss_immaterial", "strong_hedge_offset"),
        primary_action_path_id="reduce_equity_beta",
        secondary_action_path_ids=("improve_crisis_resilience",),
        default_candidate_method_ids=_methods_for("reduce_equity_beta", "improve_crisis_resilience"),
        launchpad_card_title_en="Reduce Equity Beta",
        launchpad_what_this_tests_en=(
            "Whether lower market-beta constructions reduce equity shock sensitivity."
        ),
        launchpad_tradeoff_en="Lower beta vs lower upside participation in rallies.",
        launchpad_skip_when_en="Skip when beta is high but stress losses are immaterial and hedges offset.",
        do_not_overreact_reason_en=(
            "High beta is expected for growth mandates; stress confirmation distinguishes risk from posture."
        ),
        when_not_to_select_as_primary_en=(
            "When stress-confirmed weak crisis resilience explains losses better than beta alone."
        ),
        common_false_positive_en="Beta high due to mixed asset labels but correlated equity proxies.",
        common_false_negative_en="Low beta with hidden equity-like drawdown correlation.",
        downstream_comparison_focus_en="Compare beta, stress equity shock loss, and crisis scenarios.",
        diagnosis_role="symptom",
    ),
    "high_concentration": ProblemDefinition(
        problem_id="high_concentration",
        label_en="High concentration",
        problem_id_legacy=None,
        technical_definition_en=(
            "Top-1 or top-3 capital weights or RC concentration flags exceed Block 2.1/2.5 thresholds."
        ),
        portfolio_manager_interpretation_en=(
            "A few holdings dominate capital or risk budget. Concentration amplifies idiosyncratic and factor shocks."
        ),
        required_evidence_signals=("top1_weight_pct", "top3_weight_pct"),
        supporting_evidence_signals=("rc_top1_share", "concentration_flags"),
        negative_evidence_signals=("broad_equal_weights",),
        primary_action_path_id="reduce_concentration",
        secondary_action_path_ids=("improve_diversification",),
        default_candidate_method_ids=_methods_for("reduce_concentration", "improve_diversification"),
        launchpad_card_title_en="Reduce Concentration",
        launchpad_what_this_tests_en=(
            "Whether equalized or capped exposures reduce dominant holding risk."
        ),
        launchpad_tradeoff_en="Less concentration vs potential return from best ideas.",
        launchpad_skip_when_en="Skip when top weight is intentional mandate expression and risk is acceptable.",
        do_not_overreact_reason_en=(
            "Moderate top holding in a liquid core may be acceptable if RC is balanced."
        ),
        when_not_to_select_as_primary_en=(
            "When poor diversification from correlated clones is the root issue, not single-name weight."
        ),
        common_false_positive_en="Many small lines that sum to one dominant factor exposure.",
        common_false_negative_en="Low weights but risk-parity imbalance in RC top share.",
        downstream_comparison_focus_en="Compare top weights, RC top3 share, and stress loss contributors.",
        diagnosis_subtypes=(
            "capital_concentration",
            "risk_contribution_concentration",
            "factor_concentration",
            "regional_concentration",
            "currency_concentration",
            "duplicate_exposure_concentration",
        ),
    ),
    "poor_diversification": ProblemDefinition(
        problem_id="poor_diversification",
        label_en="Poor diversification",
        problem_id_legacy=None,
        technical_definition_en=(
            "Duplicate exposure, correlation concentration, or weak breadth flags on Blocks 2.1/2.4/2.5 "
            "indicate pseudo-diversification."
        ),
        portfolio_manager_interpretation_en=(
            "The portfolio looks diversified by count but behaves like a narrower bet. "
            "Diversification quality matters more than line-item count."
        ),
        required_evidence_signals=("duplicate_exposure", "correlation_concentration"),
        supporting_evidence_signals=(
            "avg_pairwise_correlation",
            "block_2_6_liquidity_shock",
        ),
        negative_evidence_signals=("low_correlation_breadth",),
        primary_action_path_id="improve_diversification",
        secondary_action_path_ids=("compare_against_simple_benchmark",),
        default_candidate_method_ids=_methods_for("improve_diversification"),
        launchpad_card_title_en="Improve Diversification",
        launchpad_what_this_tests_en=(
            "Whether transparent diversified benchmarks reduce hidden overlap."
        ),
        launchpad_tradeoff_en="Broader diversification vs complexity and turnover.",
        launchpad_skip_when_en="Skip when overlap is cosmetic and stress behavior is acceptable.",
        do_not_overreact_reason_en=(
            "Intentional factor tilts can look like poor diversification by correlation alone."
        ),
        when_not_to_select_as_primary_en=(
            "When a single dominant weight is the clearer issue (prefer high_concentration)."
        ),
        common_false_positive_en="Correlated equity ETFs labeled as different sleeves.",
        common_false_negative_en="Uncorrelated assets with shared macro factor loadings.",
        downstream_comparison_focus_en="Compare correlation matrix, RC breadth, and stress attribution.",
    ),
    "weak_hedge_behavior": ProblemDefinition(
        problem_id="weak_hedge_behavior",
        label_en="Weak hedge behavior",
        problem_id_legacy=None,
        technical_definition_en=(
            "Block 3.3 offset coverage shows hurt assets are not offset by assets that helped in stress; "
            "Block 2.4 weak_hedge_behavior alert may pre-flag."
        ),
        portfolio_manager_interpretation_en=(
            "Hedge-labeled assets did not actually offset losses in stress. "
            "Hedge quality must be observed in scenario PnL, not assumed from labels."
        ),
        required_evidence_signals=("offset_coverage_ratio", "protection_status"),
        supporting_evidence_signals=("weak_hedge_behavior_alert", "main_hedge_gap"),
        negative_evidence_signals=("strong_offset_coverage",),
        primary_action_path_id="improve_hedge_behavior",
        secondary_action_path_ids=("improve_crisis_resilience",),
        default_candidate_method_ids=_methods_for("improve_hedge_behavior", "improve_crisis_resilience"),
        launchpad_card_title_en="Improve Hedge Behavior",
        launchpad_what_this_tests_en=(
            "Whether stress-aware candidates improve internal offset when the portfolio loses money."
        ),
        launchpad_tradeoff_en="Better stress offset vs return drag from defensive sleeves.",
        launchpad_skip_when_en="Skip when offset coverage is adequate despite weak labels.",
        do_not_overreact_reason_en=(
            "Partial protection may be acceptable if worst-case loss is still within tolerance."
        ),
        when_not_to_select_as_primary_en=(
            "When weak crisis resilience with larger absolute loss is stress-confirmed as root cause."
        ),
        common_false_positive_en="Gold/bonds present but did not contribute positively in the scenario.",
        common_false_negative_en="Offset exists in one scenario but fails in worst synthetic case.",
        downstream_comparison_focus_en="Compare offset coverage and assets helped/hurt in stress replay.",
    ),
    "poor_rates_up_behavior": ProblemDefinition(
        problem_id="poor_rates_up_behavior",
        label_en="Poor rates-up behavior",
        problem_id_legacy=None,
        technical_definition_en=(
            "Block 2.6 rates_shock hypothesis is elevated and/or rates-up stress loss is material "
            "with adverse factor rates sensitivity."
        ),
        portfolio_manager_interpretation_en=(
            "The portfolio is vulnerable when yields rise. Duration and rate-sensitive sleeves drive the risk."
        ),
        required_evidence_signals=("block_2_6_rates_shock", "rates_scenario_loss"),
        supporting_evidence_signals=("beta_rr", "rates_shock_stress"),
        negative_evidence_signals=("rates_hedge_present",),
        primary_action_path_id="reduce_duration_rates_sensitivity",
        secondary_action_path_ids=("reduce_drawdown_risk",),
        default_candidate_method_ids=_methods_for("reduce_duration_rates_sensitivity"),
        launchpad_card_title_en="Reduce Rates-Up Sensitivity",
        launchpad_what_this_tests_en=(
            "Whether duration-aware candidates improve behavior in rates-up stress."
        ),
        launchpad_tradeoff_en="Less rates sensitivity vs income and carry from long duration.",
        launchpad_skip_when_en="Skip when rates exposure is small relative to total risk budget.",
        do_not_overreact_reason_en=(
            "Moderate duration in a balanced book may be intentional liability matching."
        ),
        when_not_to_select_as_primary_en=(
            "When duration concentration (structural) is the clearer diagnosis."
        ),
        common_false_positive_en="Short rate shock with immaterial portfolio loss.",
        common_false_negative_en="Rates risk hidden inside balanced fund proxies.",
        downstream_comparison_focus_en="Compare rates shock scenario loss and factor rates beta.",
        diagnosis_role="symptom",
    ),
    "weak_crisis_resilience": ProblemDefinition(
        problem_id="weak_crisis_resilience",
        label_en="Weak crisis resilience",
        problem_id_legacy=None,
        technical_definition_en=(
            "Worst synthetic or historical stress loss on Block 3.4 exceeds materiality and/or "
            "mandate diagnostic status indicates stress attention."
        ),
        portfolio_manager_interpretation_en=(
            "Severe scenarios dominate downside. This is the institutional headline when stress confirms large losses."
        ),
        required_evidence_signals=("worst_synthetic_scenario", "worst_historical_scenario"),
        supporting_evidence_signals=(
            "offset_coverage_ratio",
            "block_2_6_recession_severe",
            "stress_diagnosis",
        ),
        negative_evidence_signals=("immaterial_stress_loss",),
        primary_action_path_id="improve_crisis_resilience",
        secondary_action_path_ids=("reduce_drawdown_risk",),
        default_candidate_method_ids=_methods_for("improve_crisis_resilience"),
        launchpad_card_title_en="Improve Crisis Resilience",
        launchpad_what_this_tests_en=(
            "Whether tail-loss-aware candidates reduce behavior in severe stress scenarios."
        ),
        launchpad_tradeoff_en="Lower tail loss vs lower expected return and higher turnover.",
        launchpad_skip_when_en="Skip if worst stress loss is above -8% and hedge offset is strong.",
        do_not_overreact_reason_en=(
            "Elevated equity beta may be secondary when stress losses are the confirmed concern."
        ),
        when_not_to_select_as_primary_en=(
            "When evidence is pre-stress only without stress confirmation and confidence is low."
        ),
        common_false_positive_en="One synthetic scenario dominates without historical support.",
        common_false_negative_en="Average metrics OK but tail scenario loss is severe.",
        downstream_comparison_focus_en="Compare worst synthetic/historical loss and crisis scenario set.",
    ),
    "high_tail_risk": ProblemDefinition(
        problem_id="high_tail_risk",
        label_en="High tail risk",
        problem_id_legacy=None,
        technical_definition_en=(
            "VaR/ES or tail-risk alert on Block 2.2/2.4 exceeds high band; may co-occur with stress tail losses."
        ),
        portfolio_manager_interpretation_en=(
            "Left-tail outcomes are fat relative to normal volatility. Tail risk differs from average vol."
        ),
        required_evidence_signals=("es_95", "tail_risk_alert"),
        supporting_evidence_signals=("var_95", "downside_beta", "worst_synthetic_scenario"),
        negative_evidence_signals=("vol_low_tail_high_only_pre_stress",),
        primary_action_path_id="reduce_tail_risk",
        secondary_action_path_ids=("improve_crisis_resilience",),
        default_candidate_method_ids=_methods_for("reduce_tail_risk", "improve_crisis_resilience"),
        launchpad_card_title_en="Reduce Tail Risk",
        launchpad_what_this_tests_en=(
            "Whether CVaR-aware candidates reduce extreme downside outcomes."
        ),
        launchpad_tradeoff_en="Lower tail risk vs upside convexity.",
        launchpad_skip_when_en="Skip when tail metrics are elevated but stress losses are not material.",
        do_not_overreact_reason_en=(
            "Tail metrics can be noisy on short histories; prefer stress-confirmed loss when available."
        ),
        when_not_to_select_as_primary_en=(
            "When weak crisis resilience already captures confirmed severe stress loss."
        ),
        common_false_positive_en="ES spike from one outlier month.",
        common_false_negative_en="Normal vol masking fat tails in mixed book.",
        downstream_comparison_focus_en="Compare ES/VaR and worst stress scenarios.",
        diagnosis_role="symptom",
    ),
    "credit_liquidity_fragility": ProblemDefinition(
        problem_id="credit_liquidity_fragility",
        label_en="Credit / liquidity fragility",
        problem_id_legacy=None,
        technical_definition_en=(
            "Block 2.4 credit/liquidity alert or Block 2.6 credit/liquidity shock hypothesis elevated; "
            "credit stress loss may confirm."
        ),
        portfolio_manager_interpretation_en=(
            "Carry and credit-like exposures may fail in spread or liquidity stress. "
            "Illiquidity amplifies drawdowns when investors need to sell."
        ),
        required_evidence_signals=("credit_liquidity_risk_alert", "block_2_6_credit_shock"),
        supporting_evidence_signals=("beta_credit", "liquidity_shock_stress"),
        negative_evidence_signals=("minimal_credit_weight",),
        primary_action_path_id="reduce_credit_liquidity_risk",
        secondary_action_path_ids=("improve_crisis_resilience",),
        default_candidate_method_ids=_methods_for("reduce_credit_liquidity_risk"),
        launchpad_card_title_en="Reduce Credit / Liquidity Risk",
        launchpad_what_this_tests_en=(
            "Whether defensive candidates reduce spread and liquidity stress sensitivity."
        ),
        launchpad_tradeoff_en="Less credit/carry vs income yield.",
        launchpad_skip_when_en="Skip when credit sleeve is tiny and stress loss is immaterial.",
        do_not_overreact_reason_en=(
            "Investment-grade aggregate exposure may be acceptable with strong liquidity profile."
        ),
        when_not_to_select_as_primary_en=(
            "When general crisis resilience without credit specificity is stress-confirmed."
        ),
        common_false_positive_en="HY label on diversified bond fund with modest weight.",
        common_false_negative_en="Liquidity risk in private or thin ETFs not flagged.",
        downstream_comparison_focus_en="Compare credit shock and liquidity shock scenario losses.",
    ),
    "duration_rates_vulnerability": ProblemDefinition(
        problem_id="duration_rates_vulnerability",
        label_en="Duration / rates vulnerability",
        problem_id_legacy=None,
        technical_definition_en=(
            "Block 2.4 duration concentration alert high or fixed-income/rates weight concentrated "
            "with elevated rates factor beta."
        ),
        portfolio_manager_interpretation_en=(
            "Structural duration exposure dominates risk. Rates-up episodes can overwhelm diversifiers."
        ),
        required_evidence_signals=("duration_concentration_alert", "fixed_income_weight"),
        supporting_evidence_signals=("beta_rr", "block_2_6_rates_shock"),
        negative_evidence_signals=("short_duration_book",),
        primary_action_path_id="reduce_duration_rates_sensitivity",
        secondary_action_path_ids=("reduce_tail_risk",),
        default_candidate_method_ids=_methods_for("reduce_duration_rates_sensitivity"),
        launchpad_card_title_en="Reduce Duration Vulnerability",
        launchpad_what_this_tests_en=(
            "Whether duration-aware construction reduces rates shock sensitivity."
        ),
        launchpad_tradeoff_en="Less duration risk vs yield and liability hedge benefits.",
        launchpad_skip_when_en="Skip when duration is intentional and rates stress loss is mild.",
        do_not_overreact_reason_en=(
            "Long Treasuries may be deliberate hedges even when duration alert is elevated."
        ),
        when_not_to_select_as_primary_en=(
            "When poor_rates_up_behavior with confirmed stress loss is clearer."
        ),
        common_false_positive_en="Duration alert from one small ETF line.",
        common_false_negative_en="Duration spread across funds with same factor exposure.",
        downstream_comparison_focus_en="Compare rates shock loss and duration-related factor betas.",
    ),
    "low_return_risk_efficiency": ProblemDefinition(
        problem_id="low_return_risk_efficiency",
        label_en="Low return / risk efficiency",
        problem_id_legacy=None,
        technical_definition_en=(
            "Sharpe/Sortino on Block 2.2 below materiality band relative to internal benchmark context; "
            "not a mandate failure by itself."
        ),
        portfolio_manager_interpretation_en=(
            "The portfolio may be taking risk without commensurate return. "
            "Efficiency problems justify exploration, not automatic rejection of the current book."
        ),
        required_evidence_signals=("sharpe", "sortino"),
        supporting_evidence_signals=("vol_annual", "cagr"),
        negative_evidence_signals=("high_stress_resilience_with_low_sharpe",),
        primary_action_path_id="improve_return_risk_balance",
        secondary_action_path_ids=("compare_against_simple_benchmark",),
        default_candidate_method_ids=_methods_for("improve_return_risk_balance"),
        launchpad_card_title_en="Improve Return / Risk Balance",
        launchpad_what_this_tests_en=(
            "Whether alternative constructions improve Sharpe-like efficiency versus current."
        ),
        launchpad_tradeoff_en="Higher efficiency vs tracking active views or constraints.",
        launchpad_skip_when_en="Skip when return/risk is acceptable and stress behavior is strong.",
        do_not_overreact_reason_en=(
            "Low Sharpe in a defensive post-crisis window may reflect regime, not construction flaw."
        ),
        when_not_to_select_as_primary_en=(
            "When stress-confirmed crisis or concentration issues are more decision-relevant."
        ),
        common_false_positive_en="Short window Sharpe after one bad month.",
        common_false_negative_en="High return from concentrated bet masking poor risk-adjusted profile.",
        downstream_comparison_focus_en="Compare Sharpe, vol, and return vs benchmark candidates.",
        diagnosis_role="symptom",
    ),
    "current_portfolio_acceptable": ProblemDefinition(
        problem_id="current_portfolio_acceptable",
        label_en="Acceptable portfolio; benchmark test available",
        problem_id_legacy=None,
        technical_definition_en=(
            "No material problem exceeds activation threshold after scoring and materiality gates."
        ),
        portfolio_manager_interpretation_en=(
            "No confirmed problem requires an immediate rebalance. Monitoring is valid, and a simple reference comparison can test whether the current allocation is materially better than transparent alternatives."
        ),
        required_evidence_signals=("no_material_problem",),
        supporting_evidence_signals=(),
        negative_evidence_signals=(),
        primary_action_path_id="compare_against_simple_benchmark",
        secondary_action_path_ids=("keep_current_portfolio_and_monitor",),
        default_candidate_method_ids=(),
        launchpad_card_title_en="Compare Against Simple References",
        launchpad_what_this_tests_en=(
            "Whether the current allocation is materially better than Equal Weight and Risk Parity references."
        ),
        launchpad_tradeoff_en="Diagnostic clarity vs time spent testing alternatives when no issue is material.",
        launchpad_skip_when_en="Skip if the user only wants monitoring and no reference comparison.",
        do_not_overreact_reason_en=(
            "Absence of a flagged problem does not guarantee future safety; monitoring remains appropriate."
        ),
        when_not_to_select_as_primary_en="N/A - this is the acceptable-portfolio outcome.",
        common_false_positive_en="Thresholds too loose missing mild issues.",
        common_false_negative_en="Over-triggering on cosmetic metric breaches.",
        downstream_comparison_focus_en="Reference comparison only; do not imply a rebalance.",
        suppress_launchpad_methods=True,
        diagnosis_role="outcome",
    ),
    "evidence_insufficient_data_quality": ProblemDefinition(
        problem_id="evidence_insufficient_data_quality",
        label_en="Evidence quality requires review",
        problem_id_legacy="data_review_required",
        technical_definition_en=(
            "Multiple Block 2 sections partial/unavailable, stress blocks missing, or data_trust signals fail."
        ),
        portfolio_manager_interpretation_en=(
            "Diagnosis cannot be trusted yet. Fix data before candidate testing or allocation changes."
        ),
        required_evidence_signals=("data_trust_failure", "partial_sections"),
        supporting_evidence_signals=("stress_block_unavailable",),
        negative_evidence_signals=(),
        primary_action_path_id="evidence_insufficient_do_not_act_yet",
        secondary_action_path_ids=("keep_current_portfolio_and_monitor",),
        default_candidate_method_ids=(),
        launchpad_card_title_en="Review Data Quality",
        launchpad_what_this_tests_en=(
            "Resolve missing history, stale inputs, or unavailable stress blocks before acting."
        ),
        launchpad_tradeoff_en="Waiting for clean evidence vs urgency to act.",
        launchpad_skip_when_en="N/A — act only after data review.",
        do_not_overreact_reason_en=(
            "Incomplete ETF history is common; do not infer problems from missing windows."
        ),
        when_not_to_select_as_primary_en=(
            "When partial data still supports a stress-confirmed primary with high confidence."
        ),
        common_false_positive_en="One young ticker blocking unrelated diagnoses.",
        common_false_negative_en="Silent stale cache treated as OK.",
        downstream_comparison_focus_en="Defer comparison until data_quality_warnings cleared.",
        suppress_launchpad_methods=True,
        diagnosis_role="outcome",
    ),
    "mixed_evidence_no_action": ProblemDefinition(
        problem_id="mixed_evidence_no_action",
        label_en="Mixed evidence - reference test available",
        problem_id_legacy=None,
        technical_definition_en=(
            "Usable diagnostic evidence contains tensions, but no dominant actionable root-cause diagnosis "
            "is confirmed strongly enough to justify a rebalance."
        ),
        portfolio_manager_interpretation_en=(
            "The current evidence does not justify forcing a trade. The right next diagnostic step is to "
            "avoid an immediate rebalance while comparing against simple benchmark references."
        ),
        required_evidence_signals=("conflicting_signal_bundle",),
        supporting_evidence_signals=(),
        negative_evidence_signals=(),
        primary_action_path_id="compare_against_simple_benchmark",
        secondary_action_path_ids=("keep_current_portfolio_and_monitor",),
        default_candidate_method_ids=(),
        launchpad_card_title_en="Compare Against Simple References",
        launchpad_what_this_tests_en=(
            "Whether the current allocation is materially better than Equal Weight and Risk Parity despite mixed evidence."
        ),
        launchpad_tradeoff_en="Avoiding unnecessary turnover vs checking whether simple references expose a real weakness.",
        launchpad_skip_when_en="Skip rebalance interpretation; use this only as a diagnostic benchmark test.",
        do_not_overreact_reason_en=(
            "Mixed evidence is a warning, not proof that the portfolio is broken."
        ),
        when_not_to_select_as_primary_en=(
            "When one root-cause signal family dominates after prioritization rules."
        ),
        common_false_positive_en="Mild tension between pre-stress and stress paths treated as a major conflict.",
        common_false_negative_en="Treating mixed evidence as multiple separate action problems.",
        downstream_comparison_focus_en="Reference comparison only; do not imply a rebalance.",
        suppress_launchpad_methods=True,
        diagnosis_role="outcome",
    ),
}


# ---------------------------------------------------------------------------
# Block 2.6 → problem mapping (v3 ids)
# ---------------------------------------------------------------------------

BLOCK_2_6_RISK_TYPE_TO_PROBLEM_IDS_V3: dict[str, tuple[str, ...]] = {
    "equity_shock": ("high_equity_beta", "weak_crisis_resilience"),
    "credit_shock": ("weak_crisis_resilience", "credit_liquidity_fragility"),
    "rates_shock": ("poor_rates_up_behavior", "duration_rates_vulnerability", "high_drawdown"),
    "inflation_stagflation": ("weak_crisis_resilience",),
    "liquidity_shock": ("poor_diversification", "weak_crisis_resilience", "credit_liquidity_fragility"),
    "usd_shock": ("weak_crisis_resilience",),
    "commodity_shock": ("weak_crisis_resilience",),
    "recession_severe": ("weak_crisis_resilience", "high_drawdown"),
}


# ---------------------------------------------------------------------------
# Legacy V1 id mapping
# ---------------------------------------------------------------------------

PROBLEM_ID_V1_TO_V2: dict[str, str] = {
    "high_drawdown_risk": "high_drawdown",
    "data_review_required": "evidence_insufficient_data_quality",
}

PROBLEM_ID_V2_TO_V1: dict[str, str] = {
    v2: v1 for v1, v2 in PROBLEM_ID_V1_TO_V2.items()
}


# ---------------------------------------------------------------------------
# Root-cause elevation hints (Session 06 consumes)
# ---------------------------------------------------------------------------

ROOT_CAUSE_ELEVATION_RULES: tuple[dict[str, Any], ...] = (
    {
        "rule_id": "crisis_over_equity_beta",
        "prefer_primary": "weak_crisis_resilience",
        "demote_when_present": ("high_equity_beta",),
        "requires_stress_confirmation": True,
    },
    {
        "rule_id": "crisis_over_volatility",
        "prefer_primary": "weak_crisis_resilience",
        "demote_when_present": ("high_volatility", "high_drawdown"),
        "requires_stress_confirmation": True,
    },
    {
        "rule_id": "concentration_over_diversification",
        "prefer_primary": "high_concentration",
        "demote_when_present": ("poor_diversification",),
        "requires_signal": "top1_weight_pct",
    },
    {
        "rule_id": "duration_over_rates_behavior",
        "prefer_primary": "duration_rates_vulnerability",
        "demote_when_present": ("poor_rates_up_behavior",),
        "requires_signal": "duration_concentration_alert",
    },
    {
        "rule_id": "hedge_gap_over_labeled_hedge",
        "prefer_primary": "weak_crisis_resilience",
        "demote_when_present": ("weak_hedge_behavior",),
        "requires_stress_confirmation": True,
    },
)


# ---------------------------------------------------------------------------
# Accessors
# ---------------------------------------------------------------------------


def all_problem_ids() -> tuple[str, ...]:
    return tuple(PROBLEM_REGISTRY.keys())


def problem_ids_by_role(role: str) -> tuple[str, ...]:
    """Return canonical problem ids for a diagnosis role."""
    return tuple(
        pid
        for pid, defn in PROBLEM_REGISTRY.items()
        if defn.diagnosis_role == role
    )


def root_cause_problem_ids() -> tuple[str, ...]:
    return problem_ids_by_role("root_cause")


def symptom_problem_ids() -> tuple[str, ...]:
    return problem_ids_by_role("symptom")


def outcome_problem_ids() -> tuple[str, ...]:
    return problem_ids_by_role("outcome")


def is_root_cause_problem(problem_id: str) -> bool:
    defn = PROBLEM_REGISTRY.get(problem_id)
    return defn is not None and defn.diagnosis_role == "root_cause"


def is_symptom_problem(problem_id: str) -> bool:
    defn = PROBLEM_REGISTRY.get(problem_id)
    return defn is not None and defn.diagnosis_role == "symptom"


def is_outcome_problem(problem_id: str) -> bool:
    defn = PROBLEM_REGISTRY.get(problem_id)
    return defn is not None and defn.diagnosis_role == "outcome"


def all_action_path_ids() -> tuple[str, ...]:
    return tuple(ACTION_PATH_REGISTRY.keys())


def get_problem_definition(problem_id: str) -> ProblemDefinition | None:
    return PROBLEM_REGISTRY.get(problem_id)


def get_action_path(action_path_id: str) -> ActionPathDefinition | None:
    return ACTION_PATH_REGISTRY.get(action_path_id)


def resolve_problem_id_v2(raw_id: str) -> str:
    """Map V1 legacy ids to V2 canonical ids."""
    return PROBLEM_ID_V1_TO_V2.get(raw_id, raw_id)


def reasonable_paths_for_problem(problem_id: str) -> tuple[str, ...]:
    """Human goal labels for Launchpad / V1 shim."""
    defn = PROBLEM_REGISTRY.get(problem_id)
    if defn is None:
        return ()
    paths: list[str] = []
    primary = ACTION_PATH_REGISTRY.get(defn.primary_action_path_id)
    if primary is not None:
        paths.append(primary.goal_label)
    for sid in defn.secondary_action_path_ids:
        secondary = ACTION_PATH_REGISTRY.get(sid)
        if secondary is not None and secondary.goal_label not in paths:
            paths.append(secondary.goal_label)
    return tuple(paths)


def method_suggestions_for_problem(problem_id: str) -> tuple[dict[str, str], ...]:
    """Default candidate method suggestions with rationale stub for JSON export."""
    defn = PROBLEM_REGISTRY.get(problem_id)
    if defn is None or defn.suppress_launchpad_methods:
        return ()
    out: list[dict[str, str]] = []
    for mid in defn.default_candidate_method_ids:
        out.append(
            {
                "candidate_method_id": mid,
                "rationale_en": f"Suggested test method for {defn.label_en}.",
            }
        )
    return tuple(out)
