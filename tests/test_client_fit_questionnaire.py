from src.client_fit import QUESTION_IDS, load_questionnaire, suggest_preset_from_answers, validate_questionnaire


def test_questionnaire_validates_canonical_v1_shape_without_liquidity():
    result = validate_questionnaire()

    assert result.ok, result.errors
    questionnaire = load_questionnaire()
    assert questionnaire["liquidity_in_scope"] is False
    assert [question["id"] for question in questionnaire["questions"]] == list(QUESTION_IDS)
    joined_ids = " ".join(question["id"] for question in questionnaire["questions"])
    assert "liquidity" not in joined_ids.lower()


def test_questionnaire_suggests_balanced_profile_and_extracts_targets():
    suggestion = suggest_preset_from_answers(
        {
            "main_objective": "balanced_growth_and_risk",
            "target_return_expectation": "return_5_7",
            "investment_horizon": "years_6_10",
            "max_temporary_loss": "loss_20",
            "reaction_to_20_decline": "hold",
            "comfortable_yearly_fluctuation": "fluctuation_8_12",
            "investment_experience": "some_experience",
            "profile_confirmation": "use_suggested_profile",
        }
    )

    assert suggestion["suggested_preset_id"] == "balanced"
    assert suggestion["source"] == "questionnaire"
    assert suggestion["source_quality"] == "medium"
    assert suggestion["extracted_targets"]["target_return_range"] == {"min": 0.05, "max": 0.07}
    assert suggestion["extracted_targets"]["target_vol_range"] == {"min": 0.08, "max": 0.12}
    assert suggestion["extracted_targets"]["target_max_drawdown_pct"] == -0.20
    assert suggestion["extracted_targets"]["horizon_years"] == 7
