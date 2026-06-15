from __future__ import annotations

import argparse
import json
import os
import re
import secrets
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.review_runtime.staged_diagnosis_service import run_staged_diagnosis_service

from src.portfolio_alternatives_builder import (  # noqa: E402
    PORTFOLIO_ALTERNATIVES_BUILDER_FILENAME,
    build_portfolio_alternatives_builder_document,
    build_simple_builder_parameters,
    builder_prefill_to_candidate_setup,
    launchpad_card_to_builder_prefill,
    validate_builder_setup,
)
from src.candidate_comparison import (  # noqa: E402
    write_block8_current_vs_candidate_only_outputs,
)
from src.config import load_validated_config  # noqa: E402
from src.current_vs_candidate import CURRENT_VS_CANDIDATE_FILENAME  # noqa: E402
from src.decision_verdict import (  # noqa: E402
    DECISION_VERDICT_FILENAME,
    write_decision_verdict_outputs,
)
from src.ai_commentary_context import (  # noqa: E402
    AI_COMMENTARY_CONTEXT_FILENAME,
    write_ai_commentary_context_outputs,
)
from src.site_explanation_bundle import (  # noqa: E402
    SITE_EXPLANATION_BUNDLE_FILENAME,
    write_site_explanation_bundle_outputs,
)
from scripts.generate_candidate_from_builder_setup import (  # noqa: E402
    generate_candidate_from_builder_setup,
)

DEFAULT_TIMEOUT_SECONDS = 15 * 60
WEIGHT_TOLERANCE = 0.01
MODE_CORE_ONLY = "core_only"
MODE_DIAGNOSIS_PLUS_PROBLEM = "diagnosis_plus_problem"
SUPPORTED_MODES = (MODE_CORE_ONLY, MODE_DIAGNOSIS_PLUS_PROBLEM)
CLIENT_FIT_PROFILE_IDS = {
    "ultra_conservative",
    "conservative",
    "balanced",
    "growth",
    "aggressive",
}
CLIENT_FIT_SOURCES = {"questionnaire", "preset_override", "manual_override", "imported", "missing"}
CLIENT_FIT_SOURCE_QUALITIES = {"high", "medium", "low", "missing"}


class PayloadValidationError(ValueError):
    """Raised when the frontend payload cannot be mapped to a safe review config."""


class BuilderSelectionError(ValueError):
    """Raised when a selected Launchpad card cannot safely become Builder setup."""


class CandidateBridgeError(ValueError):
    """Raised when the selected Builder setup cannot safely generate one candidate."""


class ComparisonBridgeError(ValueError):
    """Raised when the selected generated candidate cannot safely be compared."""


class VerdictBridgeError(ValueError):
    """Raised when a run-local verdict cannot safely be built for one candidate."""


class ReportBridgeError(ValueError):
    """Raised when a run-local report commentary context cannot safely be built."""


def _read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        raise PayloadValidationError(f"Payload is not valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise PayloadValidationError("Payload root must be a JSON object.")
    return data


def _positive_weight(value: Any, *, row_number: int) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise PayloadValidationError(f"holding[{row_number}].weight must be a number.")
    weight = float(value)
    if weight <= 0:
        raise PayloadValidationError(f"holding[{row_number}].weight must be greater than 0.")
    return weight


def _client_fit_range(value: Any, *, field_name: str) -> dict[str, float] | None:
    if value is None:
        return None
    if not isinstance(value, dict):
        raise PayloadValidationError(f"client_fit.{field_name} must be an object.")
    low = value.get("min")
    high = value.get("max")
    if (
        isinstance(low, bool)
        or isinstance(high, bool)
        or not isinstance(low, (int, float))
        or not isinstance(high, (int, float))
    ):
        raise PayloadValidationError(f"client_fit.{field_name}.min and max must be numbers.")
    low_f = float(low)
    high_f = float(high)
    if not (0 <= low_f < high_f <= 1):
        raise PayloadValidationError(f"client_fit.{field_name} must satisfy 0 <= min < max <= 1.")
    return {"min": low_f, "max": high_f}


def normalize_client_fit(raw: Any) -> dict[str, Any] | None:
    """Validate and normalize optional Client Fit V1 request context.

    This preserves the full profile for future Client Fit artifacts and maps a
    few compatible fields into the run config. It does not run Client Fit checks
    or change diagnosis behavior.
    """

    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise PayloadValidationError("client_fit must be an object when provided.")

    source = str(raw.get("source") or "").strip().lower()
    source_quality = str(raw.get("source_quality") or "").strip().lower()
    if source not in CLIENT_FIT_SOURCES:
        raise PayloadValidationError("client_fit.source is invalid.")
    if source_quality not in CLIENT_FIT_SOURCE_QUALITIES:
        raise PayloadValidationError("client_fit.source_quality is invalid.")

    normalized: dict[str, Any] = {
        "source": source,
        "source_quality": source_quality,
    }
    reason = raw.get("source_quality_reason")
    if reason is not None:
        if not isinstance(reason, str):
            raise PayloadValidationError("client_fit.source_quality_reason must be a string.")
        normalized["source_quality_reason"] = reason.strip()[:240]

    if source == "missing" or source_quality == "missing":
        if source != "missing" or source_quality != "missing":
            raise PayloadValidationError(
                "missing Client Fit profile requires source and source_quality to both be missing."
            )
        blocked_fields = (
            "preset_id",
            "horizon_years",
            "target_return_range",
            "target_vol_range",
            "target_max_drawdown_pct",
        )
        if any(raw.get(field) is not None for field in blocked_fields):
            raise PayloadValidationError("missing Client Fit profile must not include target fields.")
        return normalized

    preset_id = raw.get("preset_id")
    if preset_id is not None:
        if not isinstance(preset_id, str) or preset_id.strip() not in CLIENT_FIT_PROFILE_IDS:
            raise PayloadValidationError("client_fit.preset_id is invalid.")
        normalized["preset_id"] = preset_id.strip()

    horizon_years = raw.get("horizon_years")
    if horizon_years is not None:
        if (
            isinstance(horizon_years, bool)
            or not isinstance(horizon_years, (int, float))
            or float(horizon_years) <= 0
        ):
            raise PayloadValidationError("client_fit.horizon_years must be a positive number.")
        normalized["horizon_years"] = float(horizon_years)

    return_range = _client_fit_range(raw.get("target_return_range"), field_name="target_return_range")
    if return_range is not None:
        normalized["target_return_range"] = return_range
    vol_range = _client_fit_range(raw.get("target_vol_range"), field_name="target_vol_range")
    if vol_range is not None:
        normalized["target_vol_range"] = vol_range

    max_drawdown = raw.get("target_max_drawdown_pct")
    if max_drawdown is not None:
        if (
            isinstance(max_drawdown, bool)
            or not isinstance(max_drawdown, (int, float))
            or not (-1 <= float(max_drawdown) <= 0)
        ):
            raise PayloadValidationError(
                "client_fit.target_max_drawdown_pct must be a decimal from -1 to 0."
            )
        normalized["target_max_drawdown_pct"] = float(max_drawdown)

    has_complete_targets = all(
        key in normalized
        for key in ("horizon_years", "target_return_range", "target_vol_range", "target_max_drawdown_pct")
    )
    if "preset_id" not in normalized and not has_complete_targets:
        raise PayloadValidationError("client_fit requires preset_id or complete manual targets.")
    return normalized


def normalize_payload(payload: dict[str, Any]) -> dict[str, Any]:
    investor_currency = payload.get("investor_currency")
    if not isinstance(investor_currency, str) or not investor_currency.strip():
        raise PayloadValidationError("investor_currency is required.")
    investor_currency = investor_currency.strip().upper()

    holdings = payload.get("holdings")
    if not isinstance(holdings, list):
        raise PayloadValidationError("holdings must be a list.")
    if len(holdings) < 2:
        raise PayloadValidationError("holdings must have at least 2 rows.")

    tickers: list[str] = []
    current_weights: dict[str, float] = {}
    normalized_holdings: list[dict[str, Any]] = []
    total_weight = 0.0

    for idx, row in enumerate(holdings):
        if not isinstance(row, dict):
            raise PayloadValidationError(f"holding[{idx}] must be an object.")

        holding_type = row.get("type")
        if not isinstance(holding_type, str) or not holding_type.strip():
            raise PayloadValidationError(f"holding[{idx}].type is required.")
        holding_type = holding_type.strip().lower()

        frontend_weight = _positive_weight(row.get("weight"), row_number=idx)
        total_weight += frontend_weight

        if holding_type == "instrument":
            ticker = row.get("ticker")
            if not isinstance(ticker, str) or not ticker.strip():
                raise PayloadValidationError(f"holding[{idx}] instrument row requires ticker.")
            label = ticker.strip().upper()
            normalized_row = {
                "type": "instrument",
                "ticker": label,
                "weight": frontend_weight,
                "config_weight": frontend_weight / 100.0,
            }
        elif holding_type == "cash":
            currency = row.get("currency")
            if not isinstance(currency, str) or not currency.strip():
                raise PayloadValidationError(f"holding[{idx}] cash row requires currency.")
            cash_currency = currency.strip().upper()
            label = f"Cash {cash_currency}"
            normalized_row = {
                "type": "cash",
                "currency": cash_currency,
                "ticker": label,
                "weight": frontend_weight,
                "config_weight": frontend_weight / 100.0,
            }
        else:
            raise PayloadValidationError(
                f"Unsupported holding type '{holding_type}' at holding[{idx}]."
            )

        if label in current_weights:
            raise PayloadValidationError(f"Duplicate holding label '{label}' is not supported.")

        tickers.append(label)
        current_weights[label] = frontend_weight / 100.0
        normalized_holdings.append(normalized_row)

    if abs(total_weight - 100.0) > WEIGHT_TOLERANCE:
        raise PayloadValidationError(
            f"Total weights must equal 100 within {WEIGHT_TOLERANCE} tolerance; got {total_weight}."
        )

    normalized_client_fit = normalize_client_fit(payload.get("client_fit"))

    return {
        "investor_currency": investor_currency,
        "holdings": normalized_holdings,
        "tickers": tickers,
        "current_weights": current_weights,
        "total_weight": total_weight,
        "client_fit": normalized_client_fit,
    }


def _range_midpoint(range_value: Any) -> float | None:
    if not isinstance(range_value, dict):
        return None
    low = range_value.get("min")
    high = range_value.get("max")
    if (
        isinstance(low, (int, float))
        and not isinstance(low, bool)
        and isinstance(high, (int, float))
        and not isinstance(high, bool)
    ):
        return (float(low) + float(high)) / 2.0
    return None


def build_input_config(normalized: dict[str, Any], run_dir: Path) -> dict[str, Any]:
    try:
        run_dir_for_config = run_dir.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        run_dir_for_config = str(run_dir)
    config = {
        "investor_currency": normalized["investor_currency"],
        "tickers": normalized["tickers"],
        "current_weights": normalized["current_weights"],
        "output_dir": f"{run_dir_for_config}/csv",
        "output_dir_final": run_dir_for_config,
        "returns_frequency": "monthly",
        "market_data_provider": "ibkr_yfinance_fallback",
    }
    client_fit = normalized.get("client_fit")
    if isinstance(client_fit, dict):
        config["client_fit"] = dict(client_fit)
        if client_fit.get("preset_id"):
            config["client_profile"] = client_fit["preset_id"]
        if client_fit.get("horizon_years") is not None:
            config["horizon_years"] = client_fit["horizon_years"]
        return_midpoint = _range_midpoint(client_fit.get("target_return_range"))
        if return_midpoint is not None:
            config["target_nominal_return_annual"] = return_midpoint
        vol_midpoint = _range_midpoint(client_fit.get("target_vol_range"))
        if vol_midpoint is not None:
            config["target_vol_annual"] = vol_midpoint
        if client_fit.get("target_max_drawdown_pct") is not None:
            config["target_max_drawdown_pct"] = client_fit["target_max_drawdown_pct"]
    return config


def create_run_dir(base_dir: Path = PROJECT_ROOT / "runs") -> tuple[str, Path]:
    unique = f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}_{secrets.token_urlsafe(16)}"
    review_id = f"frontend_review_{unique}"
    run_dir = base_dir / review_id
    run_dir.mkdir(parents=True, exist_ok=False)
    return review_id, run_dir


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def tail_text(text: str, *, max_chars: int = 4000) -> str:
    if len(text) <= max_chars:
        return text
    return text[-max_chars:]


def scrub_failure_text(text: object, *, max_chars: int = 4000) -> str:
    """Prepare backend failure text for user-facing API responses.

    Keep the actionable reason, but hide local filesystem paths and Python
    tracebacks. Full details remain in server logs, not client JSON.
    """

    if text is None:
        return ""
    value = tail_text(str(text), max_chars=max_chars)
    root = str(PROJECT_ROOT)
    value = value.replace(root, "[project]").replace(root.replace("\\", "/"), "[project]")
    value = re.sub(r"Traceback \(most recent call last\):[\s\S]*", "Backend failure details were captured safely.", value)
    value = re.sub(r'File "[^"]+", line \d+(...:, in [^\r\n]+)...', "Backend file reference hidden.", value)
    value = re.sub(r"[A-Za-z]:[\\/][^\s'\")<>]+", "[path]", value)
    value = re.sub(r"/(...:Users|home|var|tmp|mnt)/[^\s'\")<>]+", "[path]", value)
    return value.strip()


def failure_details_code(exc: BaseException) -> str:
    if isinstance(exc, PayloadValidationError):
        return "input_validation_error"
    if isinstance(exc, subprocess.TimeoutExpired):
        return "backend_timeout"
    if isinstance(exc, FileNotFoundError):
        return "missing_backend_output"
    if isinstance(exc, (BuilderSelectionError, CandidateBridgeError, ComparisonBridgeError, VerdictBridgeError, ReportBridgeError)):
        return "review_lineage_or_stage_error"
    return "backend_error"


def display_path(path: Path) -> str:
    try:
        return path.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return str(path)


def safe_review_run_dir(review_id: str, *, base_dir: Path = PROJECT_ROOT / "runs") -> Path:
    """Resolve a frontend review id to its run directory without path traversal."""

    if not isinstance(review_id, str) or not review_id.strip():
        raise BuilderSelectionError("review_id is required.")
    normalized = review_id.strip()
    if not normalized.startswith("frontend_review_"):
        raise BuilderSelectionError("review_id must be a frontend_review_* id.")
    if normalized != Path(normalized).name:
        raise BuilderSelectionError("review_id must not contain path separators.")

    base = base_dir.resolve()
    run_dir = (base / normalized).resolve()
    try:
        run_dir.relative_to(base)
    except ValueError as exc:
        raise BuilderSelectionError("review_id resolves outside the runs directory.") from exc
    if not run_dir.is_dir():
        raise BuilderSelectionError(f"Review run was not found: {normalized}.")
    return run_dir


def _selected_card_from_launchpad(launchpad: dict[str, Any], selected_card_id: str) -> dict[str, Any]:
    cards = launchpad.get("cards")
    if not isinstance(cards, list):
        raise BuilderSelectionError("candidate_launchpad.cards must be a list.")
    for card in cards:
        if isinstance(card, dict) and str(card.get("card_id") or "") == selected_card_id:
            return card
    raise BuilderSelectionError(f"Selected Launchpad card was not found: {selected_card_id}.")


def _assert_selected_builder_lineage(builder_doc: dict[str, Any], selected_card_id: str) -> None:
    """Refuse stale or mismatched Builder setup before Block 7 can use it."""

    checks: dict[str, Any] = {
        "portfolio_alternatives_builder.selected_card_id": builder_doc.get("selected_card_id"),
    }
    prefill = builder_doc.get("builder_prefill")
    if isinstance(prefill, dict):
        checks["builder_prefill.source_card_id"] = prefill.get("source_card_id")
    else:
        checks["builder_prefill"] = None

    candidate_setup = builder_doc.get("candidate_setup")
    if isinstance(candidate_setup, dict):
        checks["candidate_setup.source_card_id"] = candidate_setup.get("source_card_id")
    else:
        checks["candidate_setup"] = None

    mismatches = [
        f"{field}={value!r}"
        for field, value in checks.items()
        if value != selected_card_id
    ]
    if mismatches:
        raise BuilderSelectionError(
            "Selected Builder setup does not match the frontend-selected Launchpad card: "
            + "; ".join(mismatches)
        )

    if builder_doc.get("can_generate_candidate") is not True:
        reason = builder_doc.get("reason") or (builder_doc.get("validation") or {}).get(
            "validation_status"
        )
        raise BuilderSelectionError(
            f"Selected Builder setup cannot generate a candidate: {reason or 'unknown_reason'}."
        )


def _assert_candidate_generation_lineage(
    candidate_generation: dict[str, Any],
    *,
    selected_card_id: str,
) -> None:
    """Refuse stale or mismatched Candidate Generation output."""

    candidate = candidate_generation.get("candidate")
    source_builder = candidate_generation.get("source_builder_setup")
    handoff = candidate_generation.get("handoff_to_comparison")
    if not isinstance(candidate, dict):
        raise CandidateBridgeError("candidate_generation.candidate must be an object.")
    if not isinstance(source_builder, dict):
        raise CandidateBridgeError("candidate_generation.source_builder_setup must be an object.")
    if not isinstance(handoff, dict):
        raise CandidateBridgeError("candidate_generation.handoff_to_comparison must be an object.")

    checks: dict[str, Any] = {
        "candidate.source_card_id": candidate.get("source_card_id"),
        "source_builder_setup.source_card_id": source_builder.get("source_card_id"),
    }
    mismatches = [
        f"{field}={value!r}"
        for field, value in checks.items()
        if value != selected_card_id
    ]
    if mismatches:
        raise CandidateBridgeError(
            "Candidate Generation output does not match the selected Launchpad card: "
            + "; ".join(mismatches)
        )

    candidate_id = candidate.get("candidate_id")
    if not isinstance(candidate_id, str) or not candidate_id.strip():
        raise CandidateBridgeError("candidate_generation.candidate.candidate_id is required.")
    if handoff.get("candidate_id") != candidate_id:
        raise CandidateBridgeError(
            "candidate_generation handoff candidate_id does not match candidate.candidate_id."
        )
    if candidate.get("is_rebalance_recommendation") is not False:
        raise CandidateBridgeError("Candidate Generation must not create a rebalance recommendation.")

    guardrails = candidate_generation.get("guardrails")
    if not isinstance(guardrails, dict) or guardrails.get("creates_exactly_one_candidate_attempt") is not True:
        raise CandidateBridgeError("Candidate Generation must create exactly one candidate attempt.")


def _assert_factory_run_scoped_to_one_candidate(factory_run_path: Path, candidate_id: str) -> None:
    """If the factory summary exists, it must contain only the selected candidate."""

    if not factory_run_path.is_file():
        return
    factory_doc = _read_json(factory_run_path)
    steps = factory_doc.get("steps")
    if not isinstance(steps, list):
        raise CandidateBridgeError("candidate_factory_run.steps must be a list.")
    step_candidate_ids = {
        str(step.get("candidate_id") or "")
        for step in steps
        if isinstance(step, dict) and str(step.get("candidate_id") or "").strip()
    }
    if step_candidate_ids != {candidate_id}:
        raise CandidateBridgeError(
            "candidate_factory_run is not scoped to exactly one selected candidate: "
            + ", ".join(sorted(step_candidate_ids or {"<none>"}))
        )


def generate_selected_candidate(
    *,
    review_id: str,
    selected_card_id: str,
    base_dir: Path = PROJECT_ROOT / "runs",
    force: bool = False,
    factory_execution_mode: str = "fast",
    generator: Any = generate_candidate_from_builder_setup,
) -> dict[str, Any]:
    """Generate one run-local Block 7 candidate from the selected Builder setup."""

    if not isinstance(selected_card_id, str) or not selected_card_id.strip():
        raise CandidateBridgeError("selected_card_id is required.")
    selected_card_id = selected_card_id.strip()
    run_dir = safe_review_run_dir(review_id, base_dir=base_dir)
    analysis_subject = run_dir / "analysis_subject"
    builder_path = analysis_subject / PORTFOLIO_ALTERNATIVES_BUILDER_FILENAME
    input_config_path = run_dir / "input.yml"
    output_path = run_dir / "candidate_generation.json"
    factory_run_path = run_dir / "candidate_factory_run.json"

    if not builder_path.is_file():
        raise CandidateBridgeError("portfolio_alternatives_builder.json was not found for this review.")
    if not input_config_path.is_file():
        raise CandidateBridgeError("input.yml was not found for this review.")

    builder_doc = _read_json(builder_path)
    _assert_selected_builder_lineage(builder_doc, selected_card_id)

    candidate_generation = generator(
        builder_input=builder_path,
        output_path=output_path,
        project_root=PROJECT_ROOT,
        run_factory=True,
        force=force,
        factory_run_json=factory_run_path,
        config_path=input_config_path,
        factory_execution_mode=factory_execution_mode,
    )
    if not isinstance(candidate_generation, dict):
        raise CandidateBridgeError("Candidate Generation did not return a JSON object.")

    _assert_candidate_generation_lineage(
        candidate_generation,
        selected_card_id=selected_card_id,
    )
    candidate_id = str((candidate_generation.get("candidate") or {}).get("candidate_id") or "")
    _assert_factory_run_scoped_to_one_candidate(factory_run_path, candidate_id)

    generation_status = str(candidate_generation.get("generation_status") or "")
    stage_status = "completed" if generation_status == "generated" else "failed"
    return {
        "review_id": review_id,
        "status": stage_status,
        "stage": "candidate_generation",
        "selected_card_id": selected_card_id,
        "candidate_id": candidate_id,
        "generation_status": generation_status,
        "can_compare": bool(
            (candidate_generation.get("handoff_to_comparison") or {}).get("can_compare")
        ),
        "path": display_path(output_path),
        "candidate_generation": candidate_generation,
    }


def compare_selected_candidate(
    *,
    review_id: str,
    selected_card_id: str,
    base_dir: Path = PROJECT_ROOT / "runs",
    config_loader: Any = load_validated_config,
    comparison_writer: Any = write_block8_current_vs_candidate_only_outputs,
) -> dict[str, Any]:
    """Write run-local Block 8 comparison for exactly one selected generated candidate."""

    if not isinstance(selected_card_id, str) or not selected_card_id.strip():
        raise ComparisonBridgeError("selected_card_id is required.")
    selected_card_id = selected_card_id.strip()
    run_dir = safe_review_run_dir(review_id, base_dir=base_dir)
    input_config_path = run_dir / "input.yml"
    candidate_generation_path = run_dir / "candidate_generation.json"
    factory_run_path = run_dir / "candidate_factory_run.json"

    if not input_config_path.is_file():
        raise ComparisonBridgeError("input.yml was not found for this review.")
    if not candidate_generation_path.is_file():
        raise ComparisonBridgeError("candidate_generation.json was not found for this review.")

    candidate_generation = _read_json(candidate_generation_path)
    _assert_candidate_generation_lineage(
        candidate_generation,
        selected_card_id=selected_card_id,
    )
    candidate_id = str((candidate_generation.get("candidate") or {}).get("candidate_id") or "")
    if not candidate_id:
        raise ComparisonBridgeError("candidate_generation.candidate.candidate_id is required.")

    _assert_factory_run_scoped_to_one_candidate(factory_run_path, candidate_id)
    factory_run = _read_json(factory_run_path) if factory_run_path.is_file() else None
    cfg = config_loader(input_config_path)
    paths = comparison_writer(
        cfg,
        project_root=PROJECT_ROOT,
        candidate_ids=[candidate_id],
        candidate_generation=candidate_generation,
        factory_run=factory_run,
    )

    comparison_path = paths.get("candidate_comparison_json")
    current_vs_path = paths.get("current_vs_candidate_json")
    if comparison_path is None or not Path(comparison_path).is_file():
        raise ComparisonBridgeError("candidate_comparison.json was not created for this review.")
    if current_vs_path is None or not Path(current_vs_path).is_file():
        raise ComparisonBridgeError(f"{CURRENT_VS_CANDIDATE_FILENAME} was not created for this review.")

    comparison = _read_json(Path(comparison_path))
    current_vs_candidate = _read_json(Path(current_vs_path))
    selected_candidate_ids = current_vs_candidate.get("selected_candidate_ids")
    if selected_candidate_ids != [candidate_id]:
        raise ComparisonBridgeError(
            "current_vs_candidate.selected_candidate_ids does not match the selected generated candidate."
        )
    site_bundle_path, site_bundle = write_run_site_explanation_bundle(run_dir, review_id=review_id)

    return {
        "review_id": review_id,
        "status": "completed",
        "stage": "current_vs_candidate",
        "selected_card_id": selected_card_id,
        "candidate_id": candidate_id,
        "comparison_status": current_vs_candidate.get("comparison_status"),
        "view_mode": current_vs_candidate.get("view_mode"),
        "paths": {
            "candidate_comparison": display_path(Path(comparison_path)),
            "current_vs_candidate": display_path(Path(current_vs_path)),
            "site_explanation_bundle": display_path(site_bundle_path),
        },
        "candidate_comparison": comparison,
        "current_vs_candidate": current_vs_candidate,
        "site_explanation_bundle": site_bundle,
    }


def write_selected_candidate_verdict(
    *,
    review_id: str,
    selected_card_id: str,
    base_dir: Path = PROJECT_ROOT / "runs",
    verdict_writer: Any = write_decision_verdict_outputs,
) -> dict[str, Any]:
    """Write run-local Block 9 verdict for exactly one selected generated candidate."""

    if not isinstance(selected_card_id, str) or not selected_card_id.strip():
        raise VerdictBridgeError("selected_card_id is required.")
    selected_card_id = selected_card_id.strip()
    run_dir = safe_review_run_dir(review_id, base_dir=base_dir)
    candidate_generation_path = run_dir / "candidate_generation.json"
    current_vs_path = run_dir / CURRENT_VS_CANDIDATE_FILENAME
    factory_run_path = run_dir / "candidate_factory_run.json"
    analysis_subject = run_dir / "analysis_subject"

    if not candidate_generation_path.is_file():
        raise VerdictBridgeError("candidate_generation.json was not found for this review.")

    candidate_generation = _read_json(candidate_generation_path)
    _assert_candidate_generation_lineage(
        candidate_generation,
        selected_card_id=selected_card_id,
    )
    candidate_id = str((candidate_generation.get("candidate") or {}).get("candidate_id") or "")
    if not candidate_id:
        raise VerdictBridgeError("candidate_generation.candidate.candidate_id is required.")
    _assert_factory_run_scoped_to_one_candidate(factory_run_path, candidate_id)

    current_vs_candidate = _read_json(current_vs_path) if current_vs_path.is_file() else None
    if current_vs_candidate is not None:
        selected_candidate_ids = current_vs_candidate.get("selected_candidate_ids")
        if selected_candidate_ids not in ([candidate_id], []):
            raise VerdictBridgeError(
                "current_vs_candidate.selected_candidate_ids does not match the selected generated candidate."
            )
        comparisons = current_vs_candidate.get("comparisons")
        comparison_candidate_ids = (
            {
                str(row.get("candidate_id") or "")
                for row in comparisons
                if isinstance(row, dict) and str(row.get("candidate_id") or "").strip()
            }
            if isinstance(comparisons, list)
            else set()
        )
        if comparison_candidate_ids and comparison_candidate_ids != {candidate_id}:
            raise VerdictBridgeError(
                "current_vs_candidate.comparisons are not scoped to the selected generated candidate."
            )
    elif str(candidate_generation.get("generation_status") or "") == "generated":
        raise VerdictBridgeError(f"{CURRENT_VS_CANDIDATE_FILENAME} was not found for this review.")

    paths = verdict_writer(
        output_dir=run_dir,
        selection=None,
        candidate_generation=candidate_generation,
        current_vs_candidate=current_vs_candidate,
        client_fit_check=_read_optional_json(analysis_subject / "client_fit_check.json"),
        problem_classification=_read_optional_json(analysis_subject / "problem_classification.json"),
    )
    verdict_path = paths.get("decision_verdict_json")
    if verdict_path is None or not Path(verdict_path).is_file():
        raise VerdictBridgeError(f"{DECISION_VERDICT_FILENAME} was not created for this review.")

    verdict = _read_json(Path(verdict_path))
    reviewed_candidate_id = verdict.get("reviewed_candidate_id") or verdict.get("selected_candidate_id")
    if reviewed_candidate_id != candidate_id:
        raise VerdictBridgeError(
            "decision_verdict reviewed candidate does not match the selected generated candidate."
        )
    if verdict.get("guardrails", {}).get("does_not_execute_trades") is not True:
        raise VerdictBridgeError("decision_verdict must preserve the does_not_execute_trades guardrail.")
    site_bundle_path, site_bundle = write_run_site_explanation_bundle(run_dir, review_id=review_id)

    result = {
        "review_id": review_id,
        "status": "completed",
        "stage": "decision_verdict",
        "selected_card_id": selected_card_id,
        "candidate_id": candidate_id,
        "verdict_id": verdict.get("verdict_id"),
        "selection_decision_status": verdict.get("selection_decision_status"),
        "confidence": verdict.get("confidence"),
        "path": display_path(Path(verdict_path)),
        "decision_verdict": verdict,
        "site_explanation_bundle_path": display_path(site_bundle_path),
        "site_explanation_bundle": site_bundle,
    }
    return result


def _read_optional_json(path: Path) -> dict[str, Any] | None:
    return _read_json(path) if path.is_file() else None


def write_run_site_explanation_bundle(run_dir: Path, *, review_id: str) -> tuple[Path, dict[str, Any]]:
    """Refresh the run-local screen-copy hierarchy from deterministic review artifacts."""

    analysis_subject = run_dir / "analysis_subject"
    paths = write_site_explanation_bundle_outputs(
        output_dir=run_dir,
        review_id=review_id,
        portfolio_xray=_read_optional_json(analysis_subject / "portfolio_xray.json"),
        stress_report=_read_optional_json(analysis_subject / "stress_report.json"),
        client_fit_check=_read_optional_json(analysis_subject / "client_fit_check.json"),
        problem_classification=_read_optional_json(analysis_subject / "problem_classification.json"),
        candidate_launchpad=_read_optional_json(analysis_subject / "candidate_launchpad.json"),
        portfolio_alternatives_builder=_read_optional_json(
            analysis_subject / PORTFOLIO_ALTERNATIVES_BUILDER_FILENAME
        ),
        candidate_generation=_read_optional_json(run_dir / "candidate_generation.json"),
        candidate_comparison=_read_optional_json(run_dir / "candidate_comparison.json"),
        current_vs_candidate=_read_optional_json(run_dir / CURRENT_VS_CANDIDATE_FILENAME),
        decision_verdict=_read_optional_json(run_dir / DECISION_VERDICT_FILENAME),
        ai_commentary_context=_read_optional_json(run_dir / AI_COMMENTARY_CONTEXT_FILENAME),
        what_changed_summary=_read_optional_json(run_dir / "what_changed_summary.json"),
        monitoring_diff=_read_optional_json(run_dir / "monitoring_diff.json"),
    )
    bundle_path = paths["site_explanation_bundle_json"]
    return bundle_path, _read_json(bundle_path)


def _assert_current_vs_candidate_scope(
    current_vs_candidate: dict[str, Any] | None,
    *,
    candidate_id: str,
    required: bool,
) -> None:
    if current_vs_candidate is None:
        if required:
            raise ReportBridgeError(f"{CURRENT_VS_CANDIDATE_FILENAME} was not found for this review.")
        return

    selected_candidate_ids = current_vs_candidate.get("selected_candidate_ids")
    if selected_candidate_ids not in ([candidate_id], []):
        raise ReportBridgeError(
            "current_vs_candidate.selected_candidate_ids does not match the selected generated candidate."
        )
    comparisons = current_vs_candidate.get("comparisons")
    comparison_candidate_ids = (
        {
            str(row.get("candidate_id") or "")
            for row in comparisons
            if isinstance(row, dict) and str(row.get("candidate_id") or "").strip()
        }
        if isinstance(comparisons, list)
        else set()
    )
    if comparison_candidate_ids and comparison_candidate_ids != {candidate_id}:
        raise ReportBridgeError(
            "current_vs_candidate.comparisons are not scoped to the selected generated candidate."
        )


def _assert_decision_verdict_scope(
    decision_verdict: dict[str, Any],
    *,
    candidate_id: str,
) -> None:
    reviewed_candidate_id = decision_verdict.get("reviewed_candidate_id") or decision_verdict.get(
        "selected_candidate_id"
    )
    if reviewed_candidate_id != candidate_id:
        raise ReportBridgeError(
            "decision_verdict reviewed candidate does not match the selected generated candidate."
        )
    if decision_verdict.get("guardrails", {}).get("does_not_execute_trades") is not True:
        raise ReportBridgeError("decision_verdict must preserve the does_not_execute_trades guardrail.")


def write_selected_report_context(
    *,
    review_id: str,
    selected_card_id: str,
    base_dir: Path = PROJECT_ROOT / "runs",
    context_writer: Any = write_ai_commentary_context_outputs,
) -> dict[str, Any]:
    """Write run-local grounded AI Commentary context for the active selected candidate."""

    if not isinstance(selected_card_id, str) or not selected_card_id.strip():
        raise ReportBridgeError("selected_card_id is required.")
    selected_card_id = selected_card_id.strip()
    run_dir = safe_review_run_dir(review_id, base_dir=base_dir)
    analysis_subject = run_dir / "analysis_subject"

    candidate_generation_path = run_dir / "candidate_generation.json"
    factory_run_path = run_dir / "candidate_factory_run.json"
    current_vs_path = run_dir / CURRENT_VS_CANDIDATE_FILENAME
    decision_verdict_path = run_dir / DECISION_VERDICT_FILENAME

    if not candidate_generation_path.is_file():
        raise ReportBridgeError("candidate_generation.json was not found for this review.")
    if not decision_verdict_path.is_file():
        raise ReportBridgeError(f"{DECISION_VERDICT_FILENAME} was not found for this review.")

    candidate_generation = _read_json(candidate_generation_path)
    _assert_candidate_generation_lineage(
        candidate_generation,
        selected_card_id=selected_card_id,
    )
    candidate_id = str((candidate_generation.get("candidate") or {}).get("candidate_id") or "")
    if not candidate_id:
        raise ReportBridgeError("candidate_generation.candidate.candidate_id is required.")
    _assert_factory_run_scoped_to_one_candidate(factory_run_path, candidate_id)

    current_vs_candidate = _read_optional_json(current_vs_path)
    generation_status = str(candidate_generation.get("generation_status") or "")
    _assert_current_vs_candidate_scope(
        current_vs_candidate,
        candidate_id=candidate_id,
        required=generation_status == "generated",
    )

    decision_verdict = _read_json(decision_verdict_path)
    _assert_decision_verdict_scope(decision_verdict, candidate_id=candidate_id)

    paths = context_writer(
        output_dir=run_dir,
        comparison=_read_optional_json(run_dir / "candidate_comparison.json"),
        current_vs_candidate=current_vs_candidate,
        selection=None,
        decision_verdict=decision_verdict,
        action=None,
        problem_classification=_read_optional_json(analysis_subject / "problem_classification.json"),
        candidate_launchpad=_read_optional_json(analysis_subject / "candidate_launchpad.json"),
        portfolio_alternatives_builder=_read_optional_json(
            analysis_subject / PORTFOLIO_ALTERNATIVES_BUILDER_FILENAME
        ),
        candidate_generation=candidate_generation,
        monitoring_diff=_read_optional_json(run_dir / "monitoring_diff.json"),
        portfolio_xray=_read_optional_json(analysis_subject / "portfolio_xray.json"),
        stress_report=_read_optional_json(analysis_subject / "stress_report.json"),
        client_fit_check=_read_optional_json(analysis_subject / "client_fit_check.json"),
    )

    ai_context_path = paths.get("ai_commentary_context_json")
    if ai_context_path is None or not Path(ai_context_path).is_file():
        raise ReportBridgeError(f"{AI_COMMENTARY_CONTEXT_FILENAME} was not created for this review.")
    ai_context = _read_json(Path(ai_context_path))
    if ai_context.get("guardrails", {}).get("does_not_execute_trades") is not True:
        raise ReportBridgeError("ai_commentary_context must preserve the does_not_execute_trades guardrail.")
    if ai_context.get("grounding_phase") != "post_compare":
        raise ReportBridgeError("ai_commentary_context must be a post-compare grounded report context.")
    site_bundle_path, site_bundle = write_run_site_explanation_bundle(run_dir, review_id=review_id)

    return {
        "review_id": review_id,
        "status": "completed",
        "stage": "report_commentary",
        "selected_card_id": selected_card_id,
        "candidate_id": candidate_id,
        "path": display_path(Path(ai_context_path)),
        "ai_commentary_context": ai_context,
        "site_explanation_bundle_path": display_path(site_bundle_path),
        "site_explanation_bundle": site_bundle,
    }


def prepare_selected_builder_setup(
    *,
    review_id: str,
    selected_card_id: str,
    base_dir: Path = PROJECT_ROOT / "runs",
    method: str | None = None,
    constraint_preset: str | None = None,
    mode: str | None = None,
    min_asset_weight: float | None = None,
    max_asset_weight: float | None = None,
) -> dict[str, Any]:
    """Build a run-local Builder artifact for exactly one selected Launchpad card.

    This is Session 02 backend handoff only. It does not generate candidates, does not
    call the candidate factory, and does not write weights, comparison, or verdict files.
    """

    if not isinstance(selected_card_id, str) or not selected_card_id.strip():
        raise BuilderSelectionError("selected_card_id is required.")
    selected_card_id = selected_card_id.strip()
    run_dir = safe_review_run_dir(review_id, base_dir=base_dir)
    analysis_subject = run_dir / "analysis_subject"
    launchpad_path = analysis_subject / "candidate_launchpad.json"
    problem_path = analysis_subject / "problem_classification.json"
    client_fit_path = analysis_subject / "client_fit_check.json"
    if not launchpad_path.is_file():
        raise BuilderSelectionError("candidate_launchpad.json was not found for this review.")

    launchpad = _read_json(launchpad_path)
    problem = _read_json(problem_path) if problem_path.is_file() else {}
    client_fit_check = _read_json(client_fit_path) if client_fit_path.is_file() else None
    card = _selected_card_from_launchpad(launchpad, selected_card_id)
    next_step = problem.get("next_diagnostic_step") if isinstance(problem, dict) else None
    next_step = next_step if isinstance(next_step, dict) else None

    prefill = launchpad_card_to_builder_prefill(
        card,
        next_diagnostic_step=next_step,
        client_fit_check=client_fit_check,
    )
    overrides: dict[str, Any] = {}
    if method is not None:
        overrides["method"] = method
    if constraint_preset is not None:
        overrides["constraint_preset"] = constraint_preset
    if mode is not None:
        overrides["mode"] = mode
    if min_asset_weight is not None:
        overrides["min_asset_weight"] = min_asset_weight
    if max_asset_weight is not None:
        overrides["max_asset_weight"] = max_asset_weight

    setup = build_simple_builder_parameters(prefill, overrides=overrides or None)
    validation = validate_builder_setup(setup)
    candidate_setup = builder_prefill_to_candidate_setup(prefill, edits=overrides or None)
    if candidate_setup is None:
        reason = validation.get("validation_status") or "builder_validation_failed"
        errors = ", ".join(str(row) for row in validation.get("validation_errors") or [])
        raise BuilderSelectionError(
            f"Selected Builder setup is not generatable: {reason}"
            + (f" ({errors})" if errors else "")
        )

    builder_doc = build_portfolio_alternatives_builder_document(
        prefill,
        candidate_setup,
        validation,
    )
    _assert_selected_builder_lineage(builder_doc, selected_card_id)

    builder_path = analysis_subject / PORTFOLIO_ALTERNATIVES_BUILDER_FILENAME
    write_json(builder_path, builder_doc)
    return {
        "review_id": review_id,
        "status": "completed",
        "stage": "builder_setup",
        "selected_card_id": selected_card_id,
        "can_generate_candidate": True,
        "path": display_path(builder_path),
        "portfolio_alternatives_builder": builder_doc,
    }


def expected_output_paths(run_dir: Path, *, mode: str) -> dict[str, Path]:
    analysis_subject = run_dir / "analysis_subject"
    paths = {
        "run_dir": run_dir,
        "portfolio_xray": analysis_subject / "portfolio_xray.json",
        "stress_report": analysis_subject / "stress_report.json",
        "run_metadata": analysis_subject / "run_metadata.json",
        "output_manifest": analysis_subject / "output_manifest.json",
        "site_explanation_bundle": analysis_subject / SITE_EXPLANATION_BUNDLE_FILENAME,
    }
    if mode == MODE_DIAGNOSIS_PLUS_PROBLEM:
        paths.update(
            {
                "problem_classification": analysis_subject / "problem_classification.json",
                "candidate_launchpad": analysis_subject / "candidate_launchpad.json",
                "portfolio_alternatives_builder": analysis_subject
                / "portfolio_alternatives_builder.json",
                "ai_commentary_context": analysis_subject / "ai_commentary_context.json",
            }
        )
    return paths


def read_outputs(paths: dict[str, Path], *, mode: str) -> dict[str, Any]:
    outputs: dict[str, Any] = {}
    required_keys = [
        "portfolio_xray",
        "stress_report",
        "run_metadata",
        "output_manifest",
        "site_explanation_bundle",
    ]
    if mode == MODE_DIAGNOSIS_PLUS_PROBLEM:
        required_keys.extend(
            ["problem_classification", "candidate_launchpad", "portfolio_alternatives_builder"]
        )

    for key in required_keys:
        path = paths[key]
        if not path.is_file():
            raise FileNotFoundError(f"Expected output file was not created: {path}")
        outputs[key] = json.loads(path.read_text(encoding="utf-8"))

    if mode == MODE_DIAGNOSIS_PLUS_PROBLEM:
        ai_context_path = paths["ai_commentary_context"]
        if ai_context_path.is_file():
            outputs["debug_context"] = {
                "ai_commentary_context": {
                    "kind": "grounding_debug_context",
                    "data": json.loads(ai_context_path.read_text(encoding="utf-8")),
                }
            }
    return outputs


def build_backend_command(config_path: Path, *, mode: str) -> list[str]:
    config_arg = display_path(config_path.resolve())
    if mode == MODE_CORE_ONLY:
        return [
            sys.executable,
            "run_report.py",
            "--materialize-analysis-subject",
            "--core-diagnostics-only",
            "--output-profile",
            "site_api",
            "--review-mode",
            "core",
            "--config",
            config_arg,
            "--no-review-run-context",
        ]
    if mode == MODE_DIAGNOSIS_PLUS_PROBLEM:
        return [
            sys.executable,
            "run_portfolio_review.py",
            "--config",
            config_arg,
            "--skip-candidates",
            "--output-profile",
            "site_api",
        ]
    raise ValueError(f"Unsupported bridge mode: {mode}")


def backend_failure_looks_like_transient_market_data_empty(completed: subprocess.CompletedProcess[str]) -> bool:
    """Detect a transient empty market-data panel that is worth retrying once.

    The normal frontend/FastAPI path depends on live provider data on a cold cache.
    yfinance/IBKR fallback can occasionally return an empty batch for all tickers
    while a repeat request succeeds and writes the same canonical artifacts. This
    retry does not change formulas or accept partial results; it only repeats the
    same backend command once before surfacing a failure to the UI.
    """

    combined = f"{completed.stdout or ''}\n{completed.stderr or ''}".lower()
    return (
        completed.returncode != 0
        and "market data produced no usable prices" in combined
        and "market data produced an empty panel" in combined
    )


def run_backend(
    config_path: Path, *, mode: str = MODE_CORE_ONLY, timeout_seconds: int
) -> subprocess.CompletedProcess[str]:
    cmd = build_backend_command(config_path, mode=mode)
    return subprocess.run(
        cmd,
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        timeout=timeout_seconds,
        check=False,
    )


def _direct_staged_backend_enabled(mode: str) -> bool:
    runtime = os.environ.get("PMRI_STAGED_REVIEW_RUNTIME", "direct").strip().lower()
    return runtime not in {"subprocess", "legacy"} and mode in {
        MODE_CORE_ONLY,
        MODE_DIAGNOSIS_PLUS_PROBLEM,
    }


def run_backend_for_payload(
    config_path: Path, *, mode: str = MODE_CORE_ONLY, timeout_seconds: int
) -> subprocess.CompletedProcess[str]:
    if _direct_staged_backend_enabled(mode):
        return run_staged_diagnosis_service(
            config_path,
            mode=mode,
            project_root=PROJECT_ROOT,
        )
    return run_backend(config_path, mode=mode, timeout_seconds=timeout_seconds)


def backend_failure_source(completed: subprocess.CompletedProcess[str], config_path: Path, *, mode: str) -> str:
    args = list(completed.args) if isinstance(completed.args, (list, tuple)) else []
    if args and str(args[0]) == "direct_staged_diagnosis_service":
        return "direct staged diagnosis service"
    return build_backend_command(config_path, mode=mode)[1]


def build_success_result(
    *,
    review_id: str,
    mode: str,
    normalized: dict[str, Any],
    paths: dict[str, Path],
    outputs: dict[str, Any],
) -> dict[str, Any]:
    return {
        "review_id": review_id,
        "status": "completed",
        "mode": mode,
        "portfolio_input": normalized,
        "paths": {key: display_path(path) for key, path in paths.items()},
        "outputs": outputs,
    }


def build_failure_result(
    *,
    review_id: str,
    error: str,
    details: str = "",
    stdout: str = "",
    stderr: str = "",
) -> dict[str, Any]:
    return {
        "review_id": review_id,
        "status": "failed",
        "error": scrub_failure_text(error),
        "details": scrub_failure_text(details),
        "stdout_tail": scrub_failure_text(stdout),
        "stderr_tail": scrub_failure_text(stderr),
    }


def run_from_payload(
    payload_path: Path,
    *,
    mode: str = MODE_CORE_ONLY,
    timeout_seconds: int,
    review_id: str | None = None,
    run_dir: Path | None = None,
) -> tuple[int, Path]:
    if mode not in SUPPORTED_MODES:
        raise ValueError(f"Unsupported bridge mode: {mode}")

    if (review_id is None) != (run_dir is None):
        raise ValueError("review_id and run_dir must be provided together.")
    if review_id is None or run_dir is None:
        review_id, run_dir = create_run_dir()
    else:
        run_dir.mkdir(parents=True, exist_ok=True)
    result_path = run_dir / "review_result.json"

    try:
        payload = _read_json(payload_path)
        normalized = normalize_payload(payload)

        copied_payload_path = run_dir / "payload.json"
        write_json(copied_payload_path, payload)

        input_config = build_input_config(normalized, run_dir)
        input_path = run_dir / "input.yml"
        input_path.write_text(
            yaml.safe_dump(input_config, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )

        completed = run_backend_for_payload(input_path, mode=mode, timeout_seconds=timeout_seconds)
        if backend_failure_looks_like_transient_market_data_empty(completed):
            first_attempt = completed
            completed = run_backend_for_payload(input_path, mode=mode, timeout_seconds=timeout_seconds)
            completed.stdout = (
                f"{first_attempt.stdout}\n\n[frontend_bridge_retry] "
                "Retried once after transient empty market-data panel.\n"
                f"{completed.stdout}"
            )
            completed.stderr = (
                f"{first_attempt.stderr}\n\n[frontend_bridge_retry] "
                "Retried once after transient empty market-data panel.\n"
                f"{completed.stderr}"
            )
        if completed.returncode != 0:
            backend_script = backend_failure_source(completed, input_path, mode=mode)
            write_json(
                result_path,
                build_failure_result(
                    review_id=review_id,
                    error="Backend run failed.",
                    details=f"{backend_script} exited with code {completed.returncode}.",
                    stdout=completed.stdout,
                    stderr=completed.stderr,
                ),
            )
            return completed.returncode, result_path

        paths = expected_output_paths(run_dir, mode=mode)
        outputs = read_outputs(paths, mode=mode)
        write_json(
            result_path,
            build_success_result(
                review_id=review_id,
                mode=mode,
                normalized=normalized,
                paths=paths,
                outputs=outputs,
            ),
        )
        return 0, result_path
    except subprocess.TimeoutExpired as exc:
        write_json(
            result_path,
            build_failure_result(
                review_id=review_id,
                error="Backend run timed out.",
                details=f"Timeout after {timeout_seconds} seconds.",
                stdout=exc.stdout or "",
                stderr=exc.stderr or "",
            ),
        )
        return 124, result_path
    except Exception as exc:
        write_json(
            result_path,
            build_failure_result(
                review_id=review_id,
                error=scrub_failure_text(exc),
                details=failure_details_code(exc),
            ),
        )
        return 1, result_path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Portfolio MRI core diagnostics from a frontend JSON portfolio payload."
    )
    parser.add_argument("--payload", type=Path, help="Path to frontend payload JSON.")
    parser.add_argument(
        "--mode",
        choices=SUPPORTED_MODES,
        default=MODE_CORE_ONLY,
        help=f"Bridge mode. Default: {MODE_CORE_ONLY}.",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=DEFAULT_TIMEOUT_SECONDS,
        help=f"Backend subprocess timeout. Default: {DEFAULT_TIMEOUT_SECONDS}.",
    )
    parser.add_argument(
        "--prepare-builder",
        action="store_true",
        help="Prepare run-local Builder setup for a selected Launchpad card; does not generate.",
    )
    parser.add_argument(
        "--generate-candidate",
        action="store_true",
        help="Generate one run-local candidate from the selected Builder setup.",
    )
    parser.add_argument(
        "--run-comparison",
        action="store_true",
        help="Write run-local Block 8 current-vs-candidate outputs for one selected generated candidate.",
    )
    parser.add_argument(
        "--run-verdict",
        action="store_true",
        help="Write run-local Block 9 decision verdict for one selected generated candidate.",
    )
    parser.add_argument(
        "--run-report-context",
        action="store_true",
        help="Write run-local grounded report / AI Commentary context for one selected candidate.",
    )
    parser.add_argument("--review-id", help="Existing frontend_review_* run id.")
    parser.add_argument("--selected-card-id", help="Selected Candidate Launchpad card id.")
    parser.add_argument("--builder-method", help="Optional selected Builder method override.")
    parser.add_argument("--constraint-preset", help="Optional Builder constraint preset override.")
    parser.add_argument("--builder-mode", help="Optional Builder mode override.")
    parser.add_argument(
        "--force-candidate",
        action="store_true",
        help="Pass --force to one-candidate factory generation.",
    )
    parser.add_argument(
        "--factory-execution-mode",
        choices=["fast", "standard", "legacy_full"],
        default="fast",
        help="Candidate factory execution mode for --generate-candidate. Default: fast.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    selected_actions = sum(
        bool(flag)
        for flag in (
            args.prepare_builder,
            args.generate_candidate,
            args.run_comparison,
            args.run_verdict,
            args.run_report_context,
        )
    )
    if selected_actions > 1:
        print(
            "Use only one of --prepare-builder, --generate-candidate, --run-comparison, --run-verdict, or --run-report-context.",
            file=sys.stderr,
        )
        return 2
    if args.prepare_builder:
        if not args.review_id or not args.selected_card_id:
            print("--prepare-builder requires --review-id and --selected-card-id.", file=sys.stderr)
            return 2
        try:
            result = prepare_selected_builder_setup(
                review_id=args.review_id,
                selected_card_id=args.selected_card_id,
                method=args.builder_method,
                constraint_preset=args.constraint_preset,
                mode=args.builder_mode,
            )
        except Exception as exc:
            result = {
                "review_id": args.review_id,
                "status": "failed",
                "stage": "builder_setup",
                "selected_card_id": args.selected_card_id,
                "error": scrub_failure_text(exc),
                "details": failure_details_code(exc),
            }
            try:
                run_dir = safe_review_run_dir(args.review_id)
            except Exception:
                print(json.dumps(result, ensure_ascii=False), file=sys.stderr)
                return 1
            result_path = run_dir / "builder_setup_result.json"
            write_json(result_path, result)
            print(display_path(result_path.resolve()))
            return 1

        run_dir = safe_review_run_dir(args.review_id)
        result_path = run_dir / "builder_setup_result.json"
        write_json(result_path, result)
        print(display_path(result_path.resolve()))
        return 0

    if args.generate_candidate:
        if not args.review_id or not args.selected_card_id:
            print("--generate-candidate requires --review-id and --selected-card-id.", file=sys.stderr)
            return 2
        try:
            result = generate_selected_candidate(
                review_id=args.review_id,
                selected_card_id=args.selected_card_id,
                force=bool(args.force_candidate),
                factory_execution_mode=args.factory_execution_mode,
            )
        except Exception as exc:
            result = {
                "review_id": args.review_id,
                "status": "failed",
                "stage": "candidate_generation",
                "selected_card_id": args.selected_card_id,
                "error": scrub_failure_text(exc),
                "details": failure_details_code(exc),
            }
            try:
                run_dir = safe_review_run_dir(args.review_id)
            except Exception:
                print(json.dumps(result, ensure_ascii=False), file=sys.stderr)
                return 1
            result_path = run_dir / "candidate_generation_result.json"
            write_json(result_path, result)
            print(display_path(result_path.resolve()))
            return 1

        run_dir = safe_review_run_dir(args.review_id)
        result_path = run_dir / "candidate_generation_result.json"
        write_json(result_path, result)
        print(display_path(result_path.resolve()))
        return 0 if result.get("status") == "completed" else 1

    if args.run_comparison:
        if not args.review_id or not args.selected_card_id:
            print("--run-comparison requires --review-id and --selected-card-id.", file=sys.stderr)
            return 2
        try:
            result = compare_selected_candidate(
                review_id=args.review_id,
                selected_card_id=args.selected_card_id,
            )
        except Exception as exc:
            result = {
                "review_id": args.review_id,
                "status": "failed",
                "stage": "current_vs_candidate",
                "selected_card_id": args.selected_card_id,
                "error": scrub_failure_text(exc),
                "details": failure_details_code(exc),
            }
            try:
                run_dir = safe_review_run_dir(args.review_id)
            except Exception:
                print(json.dumps(result, ensure_ascii=False), file=sys.stderr)
                return 1
            result_path = run_dir / "current_vs_candidate_result.json"
            write_json(result_path, result)
            print(display_path(result_path.resolve()))
            return 1

        run_dir = safe_review_run_dir(args.review_id)
        result_path = run_dir / "current_vs_candidate_result.json"
        write_json(result_path, result)
        print(display_path(result_path.resolve()))
        return 0

    if args.run_verdict:
        if not args.review_id or not args.selected_card_id:
            print("--run-verdict requires --review-id and --selected-card-id.", file=sys.stderr)
            return 2
        try:
            result = write_selected_candidate_verdict(
                review_id=args.review_id,
                selected_card_id=args.selected_card_id,
            )
        except Exception as exc:
            result = {
                "review_id": args.review_id,
                "status": "failed",
                "stage": "decision_verdict",
                "selected_card_id": args.selected_card_id,
                "error": scrub_failure_text(exc),
                "details": failure_details_code(exc),
            }
            try:
                run_dir = safe_review_run_dir(args.review_id)
            except Exception:
                print(json.dumps(result, ensure_ascii=False), file=sys.stderr)
                return 1
            result_path = run_dir / "decision_verdict_result.json"
            write_json(result_path, result)
            print(display_path(result_path.resolve()))
            return 1

        run_dir = safe_review_run_dir(args.review_id)
        result_path = run_dir / "decision_verdict_result.json"
        write_json(result_path, result)
        print(display_path(result_path.resolve()))
        return 0

    if args.run_report_context:
        if not args.review_id or not args.selected_card_id:
            print("--run-report-context requires --review-id and --selected-card-id.", file=sys.stderr)
            return 2
        try:
            result = write_selected_report_context(
                review_id=args.review_id,
                selected_card_id=args.selected_card_id,
            )
        except Exception as exc:
            result = {
                "review_id": args.review_id,
                "status": "failed",
                "stage": "report_commentary",
                "selected_card_id": args.selected_card_id,
                "error": scrub_failure_text(exc),
                "details": failure_details_code(exc),
            }
            try:
                run_dir = safe_review_run_dir(args.review_id)
            except Exception:
                print(json.dumps(result, ensure_ascii=False), file=sys.stderr)
                return 1
            result_path = run_dir / "report_commentary_result.json"
            write_json(result_path, result)
            print(display_path(result_path.resolve()))
            return 1

        run_dir = safe_review_run_dir(args.review_id)
        result_path = run_dir / "report_commentary_result.json"
        write_json(result_path, result)
        print(display_path(result_path.resolve()))
        return 0

    if args.payload is None:
        print(
            "--payload is required unless --prepare-builder, --generate-candidate, --run-comparison, --run-verdict, or --run-report-context is used.",
            file=sys.stderr,
        )
        return 2
    code, result_path = run_from_payload(
        args.payload, mode=args.mode, timeout_seconds=args.timeout_seconds
    )
    print(display_path(result_path.resolve()))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
