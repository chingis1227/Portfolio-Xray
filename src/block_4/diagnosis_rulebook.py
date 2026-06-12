"""Read-only loader and parity validator for the Block 4 diagnosis rulebook.

The rulebook is parity evidence for the current Python registry.  This module
must not replace ``PROBLEM_REGISTRY`` or ``ACTION_PATH_REGISTRY`` in runtime
diagnosis selection until a later accepted spec promotes the YAML to an active
source.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from src.block_4.problem_taxonomy import (
    ACTION_PATH_REGISTRY,
    PROBLEM_REGISTRY,
    ROOT_CAUSE_ELEVATION_RULES,
)

RULEBOOK_SCHEMA_VERSION = "diagnosis_rulebook_schema_v1"
DEFAULT_RULEBOOK_PATH = Path(__file__).resolve().parents[2] / "config" / "diagnosis_rulebook.yml"
DEFAULT_THRESHOLD_PATH = Path(__file__).resolve().parents[2] / "config" / "block_4_thresholds.yml"
REPO_ROOT = Path(__file__).resolve().parents[2]

REQUIRED_TOP_LEVEL_KEYS = (
    "schema_version",
    "ruleset_version",
    "status",
    "threshold_source",
    "runtime_parity_source",
    "allowed_roles",
    "action_paths",
    "problems",
    "prioritization_rules",
    "governance",
)
REQUIRED_ACTION_PATH_KEYS = (
    "label_en",
    "goal_label",
    "candidate_method_ids",
    "launchpad_description_en",
    "decision_boundary_en",
    "source_refs",
)
REQUIRED_PROBLEM_KEYS = (
    "label_en",
    "legacy_ids",
    "role",
    "eligible_as_primary",
    "suppress_launchpad_methods",
    "technical_definition_en",
    "portfolio_manager_interpretation_en",
    "professional_rationale_en",
    "evidence",
    "threshold_refs",
    "action_paths",
    "launchpad",
    "false_positive_notes_en",
    "false_negative_notes_en",
    "when_not_primary_en",
    "do_not_overreact_en",
    "hypothesis_tests",
    "success_criteria",
    "downstream_comparison_focus_en",
    "narrative_templates",
    "source_refs",
)
REQUIRED_EVIDENCE_KEYS = (
    "required_signals",
    "supporting_signals",
    "contrary_signals",
    "missing_evidence_policy_en",
    "source_artifacts",
)
REQUIRED_LAUNCHPAD_KEYS = (
    "card_title_en",
    "what_this_tests_en",
    "tradeoff_en",
    "skip_when_en",
    "default_candidate_method_ids",
)
REQUIRED_GOVERNANCE_CHECKS = {
    "problem_ids_match_python_registry",
    "action_paths_match_python_registry",
    "roles_match_python_registry",
    "signals_exist_in_registry_or_extractor",
    "threshold_refs_exist_in_threshold_source",
    "no_numeric_activation_thresholds_in_rulebook",
    "launchpad_methods_match_python_registry",
    "source_refs_exist",
    "no_recommendation_language",
}
ALLOWED_ROLES = ("root_cause", "symptom", "outcome")
_PROHIBITED_RECOMMENDATION_PHRASES = (
    "must rebalance",
    "should rebalance",
    "recommend rebalancing",
    "recommended rebalance",
    "buy ",
    "sell ",
)


class DiagnosisRulebookValidationError(ValueError):
    """Raised when callers require a valid diagnosis rulebook."""


@dataclass(frozen=True)
class DiagnosisRulebookValidationResult:
    """Validation result with explicit errors instead of hidden side effects."""

    path: Path
    valid: bool
    checks_passed: tuple[str, ...]
    errors: tuple[str, ...]
    warnings: tuple[str, ...] = ()

    def raise_for_errors(self) -> None:
        if self.errors:
            joined = "\n".join(f"- {item}" for item in self.errors)
            raise DiagnosisRulebookValidationError(
                f"Diagnosis rulebook validation failed for {self.path}:\n{joined}"
            )


def load_diagnosis_rulebook(path: Path | str | None = None) -> dict[str, Any]:
    """Load the diagnosis rulebook YAML as a mapping.

    Loading is intentionally read-only.  It does not mutate Block 4 registries
    or generated artifacts.
    """

    target = Path(path) if path is not None else DEFAULT_RULEBOOK_PATH
    with target.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise DiagnosisRulebookValidationError(f"Diagnosis rulebook must be a mapping: {target}")
    return data


def validate_diagnosis_rulebook(
    path: Path | str | None = None,
    *,
    threshold_path: Path | str | None = None,
    repo_root: Path | str | None = None,
) -> DiagnosisRulebookValidationResult:
    """Validate schema and parity with the current Block 4 Python registry."""

    target = Path(path) if path is not None else DEFAULT_RULEBOOK_PATH
    thresholds = Path(threshold_path) if threshold_path is not None else DEFAULT_THRESHOLD_PATH
    root = Path(repo_root) if repo_root is not None else REPO_ROOT
    errors: list[str] = []
    warnings: list[str] = []
    checks: list[str] = []

    try:
        data = load_diagnosis_rulebook(target)
    except Exception as exc:  # noqa: BLE001 - validation should report parse failures.
        return DiagnosisRulebookValidationResult(
            path=target,
            valid=False,
            checks_passed=(),
            errors=(str(exc),),
        )

    _validate_top_level(data, errors, checks)
    action_paths = _mapping(data.get("action_paths"))
    problems = _mapping(data.get("problems"))
    governance = _mapping(data.get("governance"))
    threshold_data = _load_yaml_mapping(thresholds, errors, f"threshold source {thresholds}")
    valid_threshold_refs = _leaf_paths(threshold_data)
    known_signals = _known_registry_signals()

    _validate_action_paths(action_paths, errors, checks)
    _validate_problems(problems, known_signals, valid_threshold_refs, root, errors, checks)
    _validate_prioritization_rules(data.get("prioritization_rules"), problems, errors, checks)
    _validate_governance(governance, errors, checks)
    _validate_source_refs(data, root, errors, checks)
    _validate_no_numeric_activation_thresholds(data, errors, checks)
    _validate_no_recommendation_language(data, errors, checks)
    _validate_parity(action_paths, problems, data.get("prioritization_rules"), errors, checks)

    if data.get("status") != "parity":
        warnings.append("Session 03 expects rulebook status to remain 'parity'.")

    return DiagnosisRulebookValidationResult(
        path=target,
        valid=not errors,
        checks_passed=tuple(dict.fromkeys(checks)),
        errors=tuple(errors),
        warnings=tuple(warnings),
    )


def assert_valid_diagnosis_rulebook(path: Path | str | None = None) -> DiagnosisRulebookValidationResult:
    """Validate the rulebook and raise with a concise error list if invalid."""

    result = validate_diagnosis_rulebook(path)
    result.raise_for_errors()
    return result


def _validate_top_level(data: dict[str, Any], errors: list[str], checks: list[str]) -> None:
    for key in REQUIRED_TOP_LEVEL_KEYS:
        if key not in data:
            errors.append(f"Missing top-level key: {key}")
    if data.get("schema_version") != RULEBOOK_SCHEMA_VERSION:
        errors.append(f"schema_version must be {RULEBOOK_SCHEMA_VERSION!r}")
    if data.get("threshold_source") != "config/block_4_thresholds.yml":
        errors.append("threshold_source must be 'config/block_4_thresholds.yml'")
    if tuple(data.get("allowed_roles") or ()) != ALLOWED_ROLES:
        errors.append(f"allowed_roles must be {ALLOWED_ROLES!r}")
    checks.append("top_level_schema_valid")


def _validate_action_paths(
    action_paths: dict[str, Any],
    errors: list[str],
    checks: list[str],
) -> None:
    if not action_paths:
        errors.append("action_paths must be a non-empty mapping")
        return
    for action_id, entry in action_paths.items():
        row = _mapping(entry)
        for key in REQUIRED_ACTION_PATH_KEYS:
            if key not in row:
                errors.append(f"action_paths.{action_id} missing key: {key}")
        if list(row.get("candidate_method_ids") or []) != list(dict.fromkeys(row.get("candidate_method_ids") or [])):
            errors.append(f"action_paths.{action_id}.candidate_method_ids contains duplicates")
    checks.append("action_path_schema_valid")


def _validate_problems(
    problems: dict[str, Any],
    known_signals: set[str],
    valid_threshold_refs: set[str],
    repo_root: Path,
    errors: list[str],
    checks: list[str],
) -> None:
    if not problems:
        errors.append("problems must be a non-empty mapping")
        return
    allowed_artifacts = _allowed_artifacts(problems)
    for problem_id, entry in problems.items():
        row = _mapping(entry)
        for key in REQUIRED_PROBLEM_KEYS:
            if key not in row:
                errors.append(f"problems.{problem_id} missing key: {key}")
        if row.get("role") not in ALLOWED_ROLES:
            errors.append(f"problems.{problem_id}.role is not allowed: {row.get('role')!r}")
        evidence = _mapping(row.get("evidence"))
        for key in REQUIRED_EVIDENCE_KEYS:
            if key not in evidence:
                errors.append(f"problems.{problem_id}.evidence missing key: {key}")
        launchpad = _mapping(row.get("launchpad"))
        for key in REQUIRED_LAUNCHPAD_KEYS:
            if key not in launchpad:
                errors.append(f"problems.{problem_id}.launchpad missing key: {key}")
        _validate_problem_action_paths(problem_id, row, errors)
        _validate_problem_hypotheses(problem_id, row, errors)
        _validate_problem_success_criteria(problem_id, row, errors)
        for signal in _list(evidence.get("required_signals")) + _list(evidence.get("supporting_signals")) + _list(
            evidence.get("contrary_signals")
        ):
            if signal not in known_signals:
                errors.append(f"problems.{problem_id} references unknown evidence signal: {signal}")
        for ref in _list(row.get("threshold_refs")):
            if ref not in valid_threshold_refs:
                errors.append(f"problems.{problem_id} references missing threshold path: {ref}")
        for artifact in _list(evidence.get("source_artifacts")):
            if artifact not in allowed_artifacts:
                errors.append(f"problems.{problem_id} references ungoverned artifact: {artifact}")
        for source_ref in _list(row.get("source_refs")):
            if not _source_ref_exists(source_ref, repo_root):
                errors.append(f"problems.{problem_id} source_ref does not exist: {source_ref}")
    checks.extend(
        [
            "signals_exist_in_registry_or_extractor",
            "threshold_refs_exist_in_threshold_source",
            "source_refs_exist",
        ]
    )


def _validate_problem_action_paths(problem_id: str, row: dict[str, Any], errors: list[str]) -> None:
    action_paths = _mapping(row.get("action_paths"))
    primary = action_paths.get("primary_action_path_id")
    if primary not in ACTION_PATH_REGISTRY:
        errors.append(f"problems.{problem_id}.action_paths.primary_action_path_id is unknown: {primary}")
    for secondary in _list(action_paths.get("secondary_action_path_ids")):
        if secondary not in ACTION_PATH_REGISTRY:
            errors.append(f"problems.{problem_id}.action_paths.secondary_action_path_ids has unknown id: {secondary}")


def _validate_problem_hypotheses(problem_id: str, row: dict[str, Any], errors: list[str]) -> None:
    success_ids = {str(item.get("criterion_id")) for item in _list_of_mappings(row.get("success_criteria"))}
    for item in _list_of_mappings(row.get("hypothesis_tests")):
        test_id = item.get("test_id")
        preferred_path = item.get("preferred_action_path_id")
        if preferred_path not in ACTION_PATH_REGISTRY:
            errors.append(f"problems.{problem_id}.hypothesis_tests.{test_id} preferred action path is unknown")
            continue
        allowed_methods = set(ACTION_PATH_REGISTRY[preferred_path].candidate_method_ids)
        for method_id in _list(item.get("suggested_method_ids")):
            if method_id not in allowed_methods:
                errors.append(
                    f"problems.{problem_id}.hypothesis_tests.{test_id} method {method_id!r} "
                    f"is not allowed for action path {preferred_path!r}"
                )
        for criterion_id in _list(item.get("success_criteria_refs")):
            if criterion_id not in success_ids:
                errors.append(
                    f"problems.{problem_id}.hypothesis_tests.{test_id} references unknown success criterion "
                    f"{criterion_id!r}"
                )


def _validate_problem_success_criteria(problem_id: str, row: dict[str, Any], errors: list[str]) -> None:
    allowed_directions = {"lower_is_better", "higher_is_better", "non_deterioration", "resolved"}
    seen: set[str] = set()
    for item in _list_of_mappings(row.get("success_criteria")):
        criterion_id = str(item.get("criterion_id") or "")
        if not criterion_id:
            errors.append(f"problems.{problem_id}.success_criteria has blank criterion_id")
        if criterion_id in seen:
            errors.append(f"problems.{problem_id}.success_criteria duplicates criterion_id {criterion_id!r}")
        seen.add(criterion_id)
        if item.get("direction") not in allowed_directions:
            errors.append(f"problems.{problem_id}.success_criteria.{criterion_id} has invalid direction")


def _validate_prioritization_rules(
    rules: Any,
    problems: dict[str, Any],
    errors: list[str],
    checks: list[str],
) -> None:
    rows = _list_of_mappings(rules)
    if not rows:
        errors.append("prioritization_rules must be a non-empty list")
        return
    for row in rows:
        rule_id = row.get("rule_id")
        if row.get("prefer_primary") not in problems:
            errors.append(f"prioritization_rules.{rule_id}.prefer_primary is unknown")
        for problem_id in _list(row.get("demote_when_present")):
            if problem_id not in problems:
                errors.append(f"prioritization_rules.{rule_id}.demote_when_present has unknown id: {problem_id}")
        if "requires_stress_confirmation" not in row:
            errors.append(f"prioritization_rules.{rule_id} missing requires_stress_confirmation")
        if "requires_signals" not in row:
            errors.append(f"prioritization_rules.{rule_id} missing requires_signals")
    checks.append("prioritization_rules_schema_valid")


def _validate_governance(governance: dict[str, Any], errors: list[str], checks: list[str]) -> None:
    if not governance:
        errors.append("governance must be a non-empty mapping")
        return
    checks_required = set(_list(governance.get("required_validation_checks")))
    missing = REQUIRED_GOVERNANCE_CHECKS - checks_required
    if missing:
        errors.append(f"governance.required_validation_checks missing: {sorted(missing)}")
    checks.append("governance_schema_valid")


def _validate_source_refs(data: dict[str, Any], repo_root: Path, errors: list[str], checks: list[str]) -> None:
    parity_source = _mapping(data.get("runtime_parity_source"))
    for key, source_ref in parity_source.items():
        if not _source_ref_exists(str(source_ref), repo_root):
            errors.append(f"runtime_parity_source.{key} does not exist: {source_ref}")
    for action_id, entry in _mapping(data.get("action_paths")).items():
        for source_ref in _list(_mapping(entry).get("source_refs")):
            if not _source_ref_exists(source_ref, repo_root):
                errors.append(f"action_paths.{action_id} source_ref does not exist: {source_ref}")
    checks.append("source_refs_exist")


def _validate_no_recommendation_language(data: dict[str, Any], errors: list[str], checks: list[str]) -> None:
    text = yaml.safe_dump(data, allow_unicode=True, sort_keys=True).lower()
    for phrase in _PROHIBITED_RECOMMENDATION_PHRASES:
        if phrase in text:
            errors.append(f"Rulebook contains prohibited recommendation phrase: {phrase!r}")
    checks.append("no_recommendation_language")


def _validate_no_numeric_activation_thresholds(
    data: dict[str, Any],
    errors: list[str],
    checks: list[str],
) -> None:
    """Reject numeric scalars so threshold values cannot drift into the rulebook."""

    for path, value in _walk_scalars(data):
        if isinstance(value, bool):
            continue
        if isinstance(value, int | float):
            errors.append(
                "Rulebook must reference threshold paths instead of storing numeric values; "
                f"found numeric scalar at {path}"
            )
    checks.append("no_numeric_activation_thresholds_in_rulebook")


def _validate_parity(
    action_paths: dict[str, Any],
    problems: dict[str, Any],
    prioritization_rules: Any,
    errors: list[str],
    checks: list[str],
) -> None:
    if set(action_paths) != set(ACTION_PATH_REGISTRY):
        errors.append(
            "action path ids do not match Python registry: "
            f"yaml={sorted(action_paths)} python={sorted(ACTION_PATH_REGISTRY)}"
        )
    else:
        checks.append("action_paths_match_python_registry")

    if set(problems) != set(PROBLEM_REGISTRY):
        errors.append(
            "problem ids do not match Python registry: "
            f"yaml={sorted(problems)} python={sorted(PROBLEM_REGISTRY)}"
        )
    else:
        checks.append("problem_ids_match_python_registry")

    for action_id, defn in ACTION_PATH_REGISTRY.items():
        row = _mapping(action_paths.get(action_id))
        _expect_equal(row.get("label_en"), defn.label_en, f"action_paths.{action_id}.label_en", errors)
        _expect_equal(row.get("goal_label"), defn.goal_label, f"action_paths.{action_id}.goal_label", errors)
        _expect_equal(
            tuple(_list(row.get("candidate_method_ids"))),
            tuple(defn.candidate_method_ids),
            f"action_paths.{action_id}.candidate_method_ids",
            errors,
        )
        _expect_equal(
            row.get("launchpad_description_en"),
            defn.launchpad_description_en,
            f"action_paths.{action_id}.launchpad_description_en",
            errors,
        )

    for problem_id, defn in PROBLEM_REGISTRY.items():
        row = _mapping(problems.get(problem_id))
        evidence = _mapping(row.get("evidence"))
        launchpad = _mapping(row.get("launchpad"))
        action_paths_row = _mapping(row.get("action_paths"))
        _expect_equal(row.get("label_en"), defn.label_en, f"problems.{problem_id}.label_en", errors)
        _expect_equal(row.get("role"), defn.diagnosis_role, f"problems.{problem_id}.role", errors)
        _expect_equal(
            row.get("eligible_as_primary"),
            defn.eligible_as_primary,
            f"problems.{problem_id}.eligible_as_primary",
            errors,
        )
        _expect_equal(
            row.get("suppress_launchpad_methods"),
            defn.suppress_launchpad_methods,
            f"problems.{problem_id}.suppress_launchpad_methods",
            errors,
        )
        _expect_equal(
            tuple(_list(evidence.get("required_signals"))),
            tuple(defn.required_evidence_signals),
            f"problems.{problem_id}.evidence.required_signals",
            errors,
        )
        _expect_equal(
            tuple(_list(evidence.get("supporting_signals"))),
            tuple(defn.supporting_evidence_signals),
            f"problems.{problem_id}.evidence.supporting_signals",
            errors,
        )
        _expect_equal(
            tuple(_list(evidence.get("contrary_signals"))),
            tuple(defn.negative_evidence_signals),
            f"problems.{problem_id}.evidence.contrary_signals",
            errors,
        )
        _expect_equal(
            action_paths_row.get("primary_action_path_id"),
            defn.primary_action_path_id,
            f"problems.{problem_id}.action_paths.primary_action_path_id",
            errors,
        )
        _expect_equal(
            tuple(_list(action_paths_row.get("secondary_action_path_ids"))),
            tuple(defn.secondary_action_path_ids),
            f"problems.{problem_id}.action_paths.secondary_action_path_ids",
            errors,
        )
        _expect_equal(
            tuple(_list(launchpad.get("default_candidate_method_ids"))),
            tuple(defn.default_candidate_method_ids),
            f"problems.{problem_id}.launchpad.default_candidate_method_ids",
            errors,
        )
        _expect_equal(
            launchpad.get("card_title_en"),
            defn.launchpad_card_title_en,
            f"problems.{problem_id}.launchpad.card_title_en",
            errors,
        )
        _expect_equal(
            launchpad.get("what_this_tests_en"),
            defn.launchpad_what_this_tests_en,
            f"problems.{problem_id}.launchpad.what_this_tests_en",
            errors,
        )
        _expect_equal(
            launchpad.get("tradeoff_en"),
            defn.launchpad_tradeoff_en,
            f"problems.{problem_id}.launchpad.tradeoff_en",
            errors,
        )
        _expect_equal(
            launchpad.get("skip_when_en"),
            defn.launchpad_skip_when_en,
            f"problems.{problem_id}.launchpad.skip_when_en",
            errors,
        )
        _expect_equal(row.get("do_not_overreact_en"), defn.do_not_overreact_reason_en, f"problems.{problem_id}.do_not_overreact_en", errors)
        _expect_equal(row.get("when_not_primary_en"), defn.when_not_to_select_as_primary_en, f"problems.{problem_id}.when_not_primary_en", errors)
        _expect_equal(
            _list(row.get("false_positive_notes_en")),
            [defn.common_false_positive_en],
            f"problems.{problem_id}.false_positive_notes_en",
            errors,
        )
        _expect_equal(
            _list(row.get("false_negative_notes_en")),
            [defn.common_false_negative_en],
            f"problems.{problem_id}.false_negative_notes_en",
            errors,
        )
        _expect_equal(
            row.get("downstream_comparison_focus_en"),
            defn.downstream_comparison_focus_en,
            f"problems.{problem_id}.downstream_comparison_focus_en",
            errors,
        )
        if defn.diagnosis_subtypes:
            _expect_equal(
                tuple(_list(row.get("subtypes"))),
                tuple(defn.diagnosis_subtypes),
                f"problems.{problem_id}.subtypes",
                errors,
            )

    current_rules = {_mapping(rule).get("rule_id"): _mapping(rule) for rule in ROOT_CAUSE_ELEVATION_RULES}
    yaml_rules = {_mapping(rule).get("rule_id"): _mapping(rule) for rule in _list(prioritization_rules)}
    if set(yaml_rules) != set(current_rules):
        errors.append(
            "prioritization rule ids do not match ROOT_CAUSE_ELEVATION_RULES: "
            f"yaml={sorted(yaml_rules)} python={sorted(current_rules)}"
        )
    for rule_id, current in current_rules.items():
        row = yaml_rules.get(rule_id, {})
        _expect_equal(row.get("prefer_primary"), current.get("prefer_primary"), f"prioritization_rules.{rule_id}.prefer_primary", errors)
        _expect_equal(
            tuple(_list(row.get("demote_when_present"))),
            tuple(current.get("demote_when_present") or ()),
            f"prioritization_rules.{rule_id}.demote_when_present",
            errors,
        )
        _expect_equal(
            bool(row.get("requires_stress_confirmation")),
            bool(current.get("requires_stress_confirmation", False)),
            f"prioritization_rules.{rule_id}.requires_stress_confirmation",
            errors,
        )
        expected_signals = (current["requires_signal"],) if current.get("requires_signal") else ()
        _expect_equal(
            tuple(_list(row.get("requires_signals"))),
            expected_signals,
            f"prioritization_rules.{rule_id}.requires_signals",
            errors,
        )
    checks.extend(["roles_match_python_registry", "launchpad_methods_match_python_registry"])


def _load_yaml_mapping(path: Path, errors: list[str], label: str) -> dict[str, Any]:
    if not path.is_file():
        errors.append(f"Missing {label}")
        return {}
    try:
        with path.open(encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
    except Exception as exc:  # noqa: BLE001 - report validation input failures.
        errors.append(f"Could not parse {label}: {exc}")
        return {}
    if not isinstance(data, dict):
        errors.append(f"{label} must be a mapping")
        return {}
    return data


def _leaf_paths(data: Any, prefix: str = "") -> set[str]:
    if not isinstance(data, dict):
        return {prefix} if prefix else set()
    out: set[str] = set()
    for key, value in data.items():
        child = f"{prefix}.{key}" if prefix else str(key)
        if isinstance(value, dict):
            out.update(_leaf_paths(value, child))
        else:
            out.add(child)
    return out


def _known_registry_signals() -> set[str]:
    signals: set[str] = set()
    for defn in PROBLEM_REGISTRY.values():
        signals.update(defn.required_evidence_signals)
        signals.update(defn.supporting_evidence_signals)
        signals.update(defn.negative_evidence_signals)
    return signals


def _allowed_artifacts(problems: dict[str, Any]) -> set[str]:
    artifacts = {"portfolio_xray.json", "stress_report.json", "current_vs_candidate.json"}
    for row in problems.values():
        evidence = _mapping(_mapping(row).get("evidence"))
        artifacts.update(_list(evidence.get("source_artifacts")))
    return artifacts


def _source_ref_exists(source_ref: str, repo_root: Path) -> bool:
    path_part = source_ref.split("::", 1)[0].split("#", 1)[0]
    if not path_part:
        return False
    return (repo_root / path_part).exists()


def _expect_equal(actual: Any, expected: Any, label: str, errors: list[str]) -> None:
    if actual != expected:
        errors.append(f"{label} mismatch: yaml={actual!r} python={expected!r}")


def _walk_scalars(value: Any, prefix: str = "$") -> list[tuple[str, Any]]:
    if isinstance(value, dict):
        out: list[tuple[str, Any]] = []
        for key, child in value.items():
            out.extend(_walk_scalars(child, f"{prefix}.{key}"))
        return out
    if isinstance(value, list):
        out = []
        for idx, child in enumerate(value):
            out.extend(_walk_scalars(child, f"{prefix}[{idx}]"))
        return out
    return [(prefix, value)]


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _list_of_mappings(value: Any) -> list[dict[str, Any]]:
    return [item for item in _list(value) if isinstance(item, dict)]
