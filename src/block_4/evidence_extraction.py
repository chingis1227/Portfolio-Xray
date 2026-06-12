"""Block 4 v2 evidence extraction from canonical Blocks 2.1–2.6 and 3.3–3.4.

Read-only translation of portfolio_xray.json and stress_report.json fields into
machine signal names consumed by problem scoring (Session 04+).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.block_2_6_portfolio_weakness_map import RISK_TYPES
from src.block_4.problem_taxonomy import get_problem_definition

BLOCK_2_1 = "block_2_1_asset_allocation"
BLOCK_2_2 = "block_2_2_portfolio_metrics"
BLOCK_2_3 = "block_2_3_factor_exposure"
BLOCK_2_4 = "block_2_4_hidden_exposure"
BLOCK_2_5 = "block_2_5_risk_budget_view"
BLOCK_2_6 = "block_2_6_portfolio_weakness_map"
BLOCK_3_3 = "block_3_3_hedge_gap_analysis"
BLOCK_3_4 = "block_3_4_current_portfolio_stress_scorecard"

ARTIFACT_XRAY = "portfolio_xray.json"
ARTIFACT_STRESS = "stress_report.json"
ARTIFACT_CLIENT_FIT = "client_fit_check.json"

HEDGE_GAP_V1_KEY = "hedge_gap_analysis_v1"
HEDGE_GAP_V1_VERSION = "hedge_gap_analysis_v1"
SCORECARD_V1_KEY = "current_portfolio_stress_scorecard_v1"
SCORECARD_V1_VERSION = "current_portfolio_stress_scorecard_v1"

_WEAK_PROTECTION = frozenset({"weak_protection", "no_protection"})
_STRONG_OFFSET_THRESHOLD = 0.55
_IMMATERIAL_STRESS_LOSS = -0.06
_MINIMAL_CREDIT_WEIGHT = 0.05
_SHORT_DURATION_FI_WEIGHT = 0.15
_BROAD_EQUAL_TOP1 = 0.12

_BLOCK_24_ALERT_SIGNALS: dict[str, str] = {
    "hidden_equity_beta": "hidden_equity_beta",
    "duration_concentration": "duration_concentration_alert",
    "credit_liquidity_risk": "credit_liquidity_risk_alert",
    "correlation_concentration": "correlation_concentration",
    "weak_hedge_behavior": "weak_hedge_behavior_alert",
    "tail_risk": "tail_risk_alert",
}

_BLOCK_26_STRESS_RISK_TYPES = frozenset(
    {"rates_shock", "credit_shock", "liquidity_shock", "recession_severe", "equity_shock"}
)


@dataclass(frozen=True)
class EvidenceSignal:
    signal: str
    value: Any
    source_block: str
    source_artifact: str
    evidence_path: str
    interpretation_en: str
    severity: str | None = None
    confidence: str | None = None
    linked_assets: tuple[str, ...] = ()
    limitation_en: str | None = None
    raw_field_path: str | None = None

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "signal": self.signal,
            "value": self.value,
            "source_block": self.source_block,
            "source_artifact": self.source_artifact,
            "evidence_path": self.evidence_path,
            "interpretation_en": self.interpretation_en,
        }
        if self.severity is not None:
            out["severity"] = self.severity
        if self.confidence is not None:
            out["confidence"] = self.confidence
        if self.linked_assets:
            out["linked_assets"] = list(self.linked_assets)
        if self.limitation_en is not None:
            out["limitation_en"] = self.limitation_en
        if self.raw_field_path is not None:
            out["raw_field_path"] = self.raw_field_path
        return out


@dataclass
class EvidenceExtractionResult:
    signals: dict[str, list[EvidenceSignal]] = field(default_factory=dict)
    signal_count: int = 0
    legacy_sections_fallback_used: bool = False
    data_quality_warnings: list[str] = field(default_factory=list)
    source_provenance: dict[str, str | None] = field(default_factory=dict)

    def has_signal(self, name: str) -> bool:
        return bool(self.signals.get(name))

    def get_signals(self, name: str) -> list[EvidenceSignal]:
        return list(self.signals.get(name, ()))


@dataclass(frozen=True)
class DiagnosisEvidenceBundle:
    """Structured v3 triage view over already-extracted evidence.

    This layer does not add a new model score. It separates root-cause evidence,
    symptom evidence, negative evidence, mixed-evidence notes, and data-quality
    notes so the narrative builder can avoid confusing symptoms with the
    primary diagnosis.
    """

    root_cause_evidence: dict[str, list[dict[str, Any]]]
    symptom_evidence: dict[str, list[dict[str, Any]]]
    negative_evidence: dict[str, list[dict[str, Any]]]
    mixed_evidence_notes: list[dict[str, Any]]
    data_quality_notes: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "root_cause_evidence": self.root_cause_evidence,
            "symptom_evidence": self.symptom_evidence,
            "negative_evidence": self.negative_evidence,
            "mixed_evidence_notes": self.mixed_evidence_notes,
            "data_quality_notes": self.data_quality_notes,
        }


def build_diagnosis_evidence_bundle(
    evidence: EvidenceExtractionResult,
    scoring: Any,
) -> DiagnosisEvidenceBundle:
    """Build the Block 4 v3 evidence triage bundle from existing score rows."""
    root: dict[str, list[dict[str, Any]]] = {}
    symptoms: dict[str, list[dict[str, Any]]] = {}
    negative: dict[str, list[dict[str, Any]]] = {}

    rows = getattr(scoring, "rows", {}) if scoring is not None else {}
    if isinstance(rows, dict):
        for problem_id, row in rows.items():
            defn = get_problem_definition(str(problem_id))
            if defn is None:
                continue
            refs = [dict(ref) for ref in getattr(row, "evidence_refs", [])]
            neg_refs = [dict(ref) for ref in getattr(row, "negative_evidence_refs", [])]
            if refs:
                if defn.diagnosis_role == "symptom":
                    symptoms[str(problem_id)] = refs
                elif defn.diagnosis_role == "root_cause":
                    root[str(problem_id)] = refs
            if neg_refs:
                negative[str(problem_id)] = neg_refs

    mixed_notes: list[dict[str, Any]] = []
    if bool(getattr(scoring, "conflicting_signal_bundle", False)):
        mixed_notes.append(
            {
                "note_id": "mixed_evidence_note_01",
                "severity": "warning",
                "interpretation_en": (
                    "Some evidence families are in tension; this is a warning unless no root-cause diagnosis dominates."
                ),
            }
        )

    return DiagnosisEvidenceBundle(
        root_cause_evidence=root,
        symptom_evidence=symptoms,
        negative_evidence=negative,
        mixed_evidence_notes=mixed_notes,
        data_quality_notes=list(evidence.data_quality_warnings),
    )


def extract_evidence_signals(
    portfolio_xray: dict[str, Any] | None,
    stress_report: dict[str, Any] | None,
    client_fit_check: dict[str, Any] | None = None,
) -> EvidenceExtractionResult:
    """Extract taxonomy signal names from Blocks 2.1-2.6, 3.3-3.4, and Client Fit V1."""
    xray = portfolio_xray if isinstance(portfolio_xray, dict) else {}
    stress = stress_report if isinstance(stress_report, dict) else {}
    client_fit = client_fit_check if isinstance(client_fit_check, dict) else {}
    bucket: dict[str, list[EvidenceSignal]] = {}
    warnings: list[str] = []
    legacy_used = False

    stress_available = _stress_blocks_available(stress)
    evidence_path_pre = "pre_stress_only" if not stress_available else "primary"

    _extract_block_2_1(bucket, xray, evidence_path_pre)
    used_legacy_22 = _extract_block_2_2(bucket, xray, evidence_path_pre)
    legacy_used = legacy_used or used_legacy_22
    used_legacy_23 = _extract_block_2_3(bucket, xray, evidence_path_pre)
    legacy_used = legacy_used or used_legacy_23
    _extract_block_2_4(bucket, xray, evidence_path_pre)
    _extract_block_2_5(bucket, xray, evidence_path_pre)
    _extract_block_2_6(bucket, xray, evidence_path_pre)
    provenance = _extract_stress_blocks(bucket, stress, warnings)
    _extract_client_fit(bucket, client_fit, warnings)
    _extract_data_quality(bucket, xray, stress, warnings)

    if legacy_used:
        warnings.append("Legacy sections.* fallback used for one or more canonical block readers.")

    count = sum(len(rows) for rows in bucket.values())
    return EvidenceExtractionResult(
        signals=bucket,
        signal_count=count,
        legacy_sections_fallback_used=legacy_used,
        data_quality_warnings=warnings,
        source_provenance=provenance,
    )

def _extract_client_fit(
    bucket: dict[str, list[EvidenceSignal]],
    client_fit: dict[str, Any],
    warnings: list[str],
) -> None:
    if not isinstance(client_fit, dict) or not client_fit:
        return
    if client_fit.get("schema_version") != "client_fit_check_v1":
        warnings.append("Client Fit artifact has unsupported or missing schema_version.")
        return

    status = str(client_fit.get("client_fit_status") or "evidence_insufficient")
    _emit(
        bucket,
        EvidenceSignal(
            signal="client_fit_status",
            value=status,
            source_block="client_fit_check_v1",
            source_artifact=ARTIFACT_CLIENT_FIT,
            evidence_path="client_fit_context",
            interpretation_en=f"Client Fit status is {status.replace('_', ' ')}.",
            severity="high" if status in {"breach", "conflict"} else "medium" if status == "watch" else "low",
            raw_field_path="client_fit_status",
        ),
    )
    if status == "fit":
        _emit(
            bucket,
            EvidenceSignal(
                signal="client_fit_within_profile",
                value={"status": "fit"},
                source_block="client_fit_check_v1",
                source_artifact=ARTIFACT_CLIENT_FIT,
                evidence_path="client_fit_context",
                interpretation_en=(
                    "Client Fit status is fit; the provided profile does not add a personal-risk breach."
                ),
                severity="low",
                raw_field_path="client_fit_status",
            ),
        )

    conflict = client_fit.get("goal_risk_conflict")
    if isinstance(conflict, dict) and str(conflict.get("status") or "") == "conflict":
        _emit(
            bucket,
            EvidenceSignal(
                signal="goal_risk_conflict",
                value={"status": "conflict", "reasons": list(conflict.get("reasons") or [])},
                source_block="client_fit_check_v1",
                source_artifact=ARTIFACT_CLIENT_FIT,
                evidence_path="client_fit_context",
                interpretation_en=str(
                    conflict.get("interpretation")
                    or "Client objectives show an internal goal-risk conflict."
                ),
                severity="high",
                raw_field_path="goal_risk_conflict",
            ),
        )

    for row in client_fit.get("checks") or []:
        if not isinstance(row, dict):
            continue
        check_status = str(row.get("status") or "")
        dimension = str(row.get("dimension") or "")
        if check_status not in {"watch", "breach", "conflict", "evidence_insufficient"}:
            continue
        signal_name = f"client_fit_{dimension}" if dimension else "client_fit_check"
        _emit(
            bucket,
            EvidenceSignal(
                signal=signal_name,
                value={
                    "status": check_status,
                    "portfolio_value": row.get("portfolio_value"),
                    "client_limit": row.get("client_limit"),
                    "client_range": row.get("client_range"),
                },
                source_block="client_fit_check_v1",
                source_artifact=ARTIFACT_CLIENT_FIT,
                evidence_path="client_fit_context",
                interpretation_en=str(row.get("interpretation") or f"Client Fit check {dimension} is {check_status}."),
                severity="high" if check_status in {"breach", "conflict"} else "medium",
                raw_field_path=f"checks[{dimension}]",
            ),
        )


def _stress_blocks_available(stress: dict[str, Any]) -> bool:
    hg = _hedge_gap_block(stress)
    sc = _scorecard_block(stress)
    hg_ok = isinstance(hg, dict) and str(hg.get("block_status") or "") not in {"", "unavailable"}
    sc_ok = isinstance(sc, dict) and sc.get("availability") != "unavailable"
    if hg_ok or sc_ok:
        return True
    legacy = stress.get("stress_conclusions")
    return isinstance(legacy, dict) and bool(legacy)


def _hedge_gap_block(stress: dict[str, Any]) -> dict[str, Any] | None:
    block = stress.get(HEDGE_GAP_V1_KEY)
    if isinstance(block, dict) and block.get("version") == HEDGE_GAP_V1_VERSION:
        return block
    return None


def _scorecard_block(stress: dict[str, Any]) -> dict[str, Any] | None:
    block = stress.get(SCORECARD_V1_KEY)
    if isinstance(block, dict) and block.get("version") == SCORECARD_V1_VERSION:
        return block
    return None


def _block_status_ok(block: dict[str, Any] | None) -> bool:
    if not isinstance(block, dict):
        return False
    status = str(block.get("status") or "ok").lower()
    return status not in {"unavailable", "missing"}


def _sections(xray: dict[str, Any]) -> dict[str, Any]:
    sections = xray.get("sections")
    return sections if isinstance(sections, dict) else {}


def _items(section: Any) -> list[dict[str, Any]]:
    if not isinstance(section, dict):
        return []
    raw = section.get("items")
    if not isinstance(raw, list):
        return []
    return [item for item in raw if isinstance(item, dict)]


def _as_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _first_float(*values: Any) -> float | None:
    for value in values:
        parsed = _as_float(value)
        if parsed is not None:
            return parsed
    return None


def _normalize_band(value: Any) -> str | None:
    if value is None:
        return None
    raw = str(value).strip().lower()
    mapping = {
        "low": "low",
        "medium": "medium",
        "moderate": "medium",
        "high": "high",
        "unavailable": "unavailable",
        "unknown": "unavailable",
    }
    return mapping.get(raw)


def _severity_from_block_26(severity: Any) -> str | None:
    raw = str(severity or "").strip()
    if raw in {"Low", "Medium", "High", "Unavailable"}:
        return _normalize_band(raw)
    return _normalize_band(raw)


def _linked_assets_from_alert(alert: dict[str, Any]) -> tuple[str, ...]:
    assets: list[str] = []
    for row in alert.get("contributing_assets") or []:
        if isinstance(row, dict):
            ticker = row.get("ticker") or row.get("label")
            if ticker:
                assets.append(str(ticker))
        elif isinstance(row, str):
            assets.append(row)
    return tuple(assets)


def _emit(
    bucket: dict[str, list[EvidenceSignal]],
    signal: EvidenceSignal,
) -> None:
    bucket.setdefault(signal.signal, []).append(signal)


def _extract_block_2_1(
    bucket: dict[str, list[EvidenceSignal]],
    xray: dict[str, Any],
    evidence_path: str,
) -> None:
    block = xray.get(BLOCK_2_1)
    if not _block_status_ok(block):
        return
    assert isinstance(block, dict)

    top1_w: float | None = None
    snap = block.get("portfolio_composition_snapshot") or block.get("concentration_snapshot") or {}
    if isinstance(snap, dict):
        top1 = snap.get("top1_holding") if isinstance(snap.get("top1_holding"), dict) else {}
        top1_w = _as_float(top1.get("weight_pct"))
        if top1_w is not None:
            _emit(
                bucket,
                EvidenceSignal(
                    signal="top1_weight_pct",
                    value=top1_w,
                    source_block=BLOCK_2_1,
                    source_artifact=ARTIFACT_XRAY,
                    evidence_path=evidence_path,
                    interpretation_en=f"Top holding weight is {top1_w:.1f}% of capital.",
                    linked_assets=(str(top1.get("ticker")),) if top1.get("ticker") else (),
                    raw_field_path=f"{BLOCK_2_1}.portfolio_composition_snapshot.top1_holding.weight_pct",
                ),
            )
        top3_w = _as_float(snap.get("top3_weight_pct"))
        if top3_w is not None:
            _emit(
                bucket,
                EvidenceSignal(
                    signal="top3_weight_pct",
                    value=top3_w,
                    source_block=BLOCK_2_1,
                    source_artifact=ARTIFACT_XRAY,
                    evidence_path=evidence_path,
                    interpretation_en=f"Top three holdings sum to {top3_w:.1f}% of capital.",
                    raw_field_path=f"{BLOCK_2_1}.portfolio_composition_snapshot.top3_weight_pct",
                ),
            )

    flags = block.get("concentration_flags")
    if isinstance(flags, list) and flags:
        _emit(
            bucket,
            EvidenceSignal(
                signal="concentration_flags",
                value=len(flags),
                source_block=BLOCK_2_1,
                source_artifact=ARTIFACT_XRAY,
                evidence_path=evidence_path,
                interpretation_en=f"{len(flags)} concentration flag(s) raised on allocation dimensions.",
                severity=_normalize_band(
                    next(
                        (
                            str(f.get("severity") or "medium")
                            for f in flags
                            if isinstance(f, dict) and str(f.get("severity") or "").lower() == "high"
                        ),
                        str(flags[0].get("severity") or "medium") if isinstance(flags[0], dict) else "medium",
                    )
                ),
                raw_field_path=f"{BLOCK_2_1}.concentration_flags",
            ),
        )

    dup_flags = block.get("duplicate_exposure_flags")
    if isinstance(dup_flags, list) and dup_flags:
        _emit(
            bucket,
            EvidenceSignal(
                signal="duplicate_exposure",
                value=len(dup_flags),
                source_block=BLOCK_2_1,
                source_artifact=ARTIFACT_XRAY,
                evidence_path=evidence_path,
                interpretation_en="Duplicate economic exposure detected across holdings.",
                raw_field_path=f"{BLOCK_2_1}.duplicate_exposure_flags",
            ),
        )

    breakdown = block.get("capital_allocation_breakdown")
    fi_weight: float | None = None
    if isinstance(breakdown, dict):
        for row in breakdown.get("by_asset_class") or []:
            if not isinstance(row, dict):
                continue
            if str(row.get("name") or "").lower() in {"fixed_income", "bond", "bonds"}:
                fi_weight = _as_float(row.get("weight_pct"))
                break
    if fi_weight is not None:
        _emit(
            bucket,
            EvidenceSignal(
                signal="fixed_income_weight",
                value=fi_weight,
                source_block=BLOCK_2_1,
                source_artifact=ARTIFACT_XRAY,
                evidence_path=evidence_path,
                interpretation_en=f"Fixed-income sleeve is {fi_weight:.1f}% of capital.",
                raw_field_path=f"{BLOCK_2_1}.capital_allocation_breakdown.by_asset_class",
            ),
        )
        if fi_weight <= _SHORT_DURATION_FI_WEIGHT * 100:
            _emit(
                bucket,
                EvidenceSignal(
                    signal="short_duration_book",
                    value=fi_weight,
                    source_block=BLOCK_2_1,
                    source_artifact=ARTIFACT_XRAY,
                    evidence_path=evidence_path,
                    interpretation_en="Fixed-income weight is small relative to typical duration hedges.",
                    raw_field_path=f"{BLOCK_2_1}.capital_allocation_breakdown.by_asset_class",
                ),
            )

    credit_weight: float | None = None
    if isinstance(breakdown, dict):
        for row in breakdown.get("by_main_risk_factor") or []:
            if not isinstance(row, dict):
                continue
            if str(row.get("name") or "").lower() == "credit":
                credit_weight = _as_float(row.get("weight_pct"))
                break
    if credit_weight is not None and credit_weight <= _MINIMAL_CREDIT_WEIGHT * 100:
        _emit(
            bucket,
            EvidenceSignal(
                signal="minimal_credit_weight",
                value=credit_weight,
                source_block=BLOCK_2_1,
                source_artifact=ARTIFACT_XRAY,
                evidence_path=evidence_path,
                interpretation_en="Credit-like capital weight is minimal.",
                raw_field_path=f"{BLOCK_2_1}.capital_allocation_breakdown.by_main_risk_factor",
            ),
        )

    if top1_w is not None and top1_w <= _BROAD_EQUAL_TOP1 * 100:
        _emit(
            bucket,
            EvidenceSignal(
                signal="broad_equal_weights",
                value=top1_w,
                source_block=BLOCK_2_1,
                source_artifact=ARTIFACT_XRAY,
                evidence_path=evidence_path,
                interpretation_en="Top holding weight is near equal-weight breadth.",
                raw_field_path=f"{BLOCK_2_1}.portfolio_composition_snapshot.top1_holding.weight_pct",
            ),
        )


def _extract_block_2_2(
    bucket: dict[str, list[EvidenceSignal]],
    xray: dict[str, Any],
    evidence_path: str,
) -> bool:
    block = xray.get(BLOCK_2_2)
    legacy_used = False
    if _block_status_ok(block) and isinstance(block, dict):
        metrics = block.get("return_risk_metrics") if isinstance(block.get("return_risk_metrics"), dict) else {}
        drawdown = block.get("drawdown_diagnostics") if isinstance(block.get("drawdown_diagnostics"), dict) else {}
        tail = block.get("tail_risk_diagnostics") if isinstance(block.get("tail_risk_diagnostics"), dict) else {}
        bench = block.get("benchmark_dependence") if isinstance(block.get("benchmark_dependence"), dict) else {}
        rolling = block.get("rolling_diagnostics") if isinstance(block.get("rolling_diagnostics"), dict) else {}
        corr = block.get("correlation_breakdown") if isinstance(block.get("correlation_breakdown"), dict) else {}

        vol = _as_float(metrics.get("vol_annual"))
        if vol is not None:
            _emit(
                bucket,
                EvidenceSignal(
                    signal="vol_annual",
                    value=vol,
                    source_block=BLOCK_2_2,
                    source_artifact=ARTIFACT_XRAY,
                    evidence_path=evidence_path,
                    interpretation_en=f"Annualized volatility is {vol:.3f} on the primary window.",
                    raw_field_path=f"{BLOCK_2_2}.return_risk_metrics.vol_annual",
                ),
            )

        for sig, key, label in (
            ("sharpe", "sharpe", "Sharpe ratio"),
            ("sortino", "sortino", "Sortino ratio"),
            ("cagr", "portfolio_cagr", "CAGR"),
        ):
            val = _as_float(metrics.get(key))
            if val is not None:
                _emit(
                    bucket,
                    EvidenceSignal(
                        signal=sig,
                        value=val,
                        source_block=BLOCK_2_2,
                        source_artifact=ARTIFACT_XRAY,
                        evidence_path=evidence_path,
                        interpretation_en=f"{label} is {val:.3f} on the primary window.",
                        raw_field_path=f"{BLOCK_2_2}.return_risk_metrics.{key}",
                    ),
                )

        max_dd = _as_float(drawdown.get("max_drawdown"))
        if max_dd is not None:
            _emit(
                bucket,
                EvidenceSignal(
                    signal="max_drawdown",
                    value=max_dd,
                    source_block=BLOCK_2_2,
                    source_artifact=ARTIFACT_XRAY,
                    evidence_path=evidence_path,
                    interpretation_en=f"Maximum drawdown is {max_dd:.3f} on the primary window.",
                    raw_field_path=f"{BLOCK_2_2}.drawdown_diagnostics.max_drawdown",
                ),
            )
            if drawdown.get("recovered") is True:
                ttr = _as_float(drawdown.get("ttr_months") or drawdown.get("recovery_months"))
                _emit(
                    bucket,
                    EvidenceSignal(
                        signal="drawdown_recovered_quickly",
                        value=ttr,
                        source_block=BLOCK_2_2,
                        source_artifact=ARTIFACT_XRAY,
                        evidence_path=evidence_path,
                        interpretation_en="Drawdown episode recovered within the sample window.",
                        raw_field_path=f"{BLOCK_2_2}.drawdown_diagnostics.recovered",
                    ),
                )

        underwater = _as_float(drawdown.get("pct_time_underwater"))
        if underwater is not None:
            _emit(
                bucket,
                EvidenceSignal(
                    signal="time_underwater",
                    value=underwater,
                    source_block=BLOCK_2_2,
                    source_artifact=ARTIFACT_XRAY,
                    evidence_path=evidence_path,
                    interpretation_en=f"Portfolio spent {underwater:.1%} of the window below prior peak.",
                    raw_field_path=f"{BLOCK_2_2}.drawdown_diagnostics.pct_time_underwater",
                ),
            )

        for sig, key in (("var_95", "var_95"), ("es_95", "es_95")):
            val = _as_float(tail.get(key))
            if val is not None:
                _emit(
                    bucket,
                    EvidenceSignal(
                        signal=sig,
                        value=val,
                        source_block=BLOCK_2_2,
                        source_artifact=ARTIFACT_XRAY,
                        evidence_path=evidence_path,
                        interpretation_en=f"{sig.upper().replace('_', ' ')} tail metric is {val:.3f}.",
                        raw_field_path=f"{BLOCK_2_2}.tail_risk_diagnostics.{key}",
                    ),
                )

        beta_port = _as_float(bench.get("beta_portfolio") or bench.get("beta_base"))
        if beta_port is not None:
            _emit(
                bucket,
                EvidenceSignal(
                    signal="beta_portfolio",
                    value=beta_port,
                    source_block=BLOCK_2_2,
                    source_artifact=ARTIFACT_XRAY,
                    evidence_path=evidence_path,
                    interpretation_en=f"Portfolio beta to the base benchmark is {beta_port:.3f}.",
                    raw_field_path=f"{BLOCK_2_2}.benchmark_dependence.beta_portfolio",
                ),
            )

        downside_beta = _as_float(bench.get("downside_beta"))
        if downside_beta is not None:
            _emit(
                bucket,
                EvidenceSignal(
                    signal="downside_beta",
                    value=downside_beta,
                    source_block=BLOCK_2_2,
                    source_artifact=ARTIFACT_XRAY,
                    evidence_path=evidence_path,
                    interpretation_en=f"Downside beta is {downside_beta:.3f}.",
                    raw_field_path=f"{BLOCK_2_2}.benchmark_dependence.downside_beta",
                ),
            )

        core = rolling.get("core_view") if isinstance(rolling.get("core_view"), dict) else {}
        roll_vol = core.get("rolling_volatility_12m") if isinstance(core.get("rolling_volatility_12m"), dict) else {}
        roll_latest = _as_float(roll_vol.get("latest"))
        if roll_latest is not None:
            _emit(
                bucket,
                EvidenceSignal(
                    signal="rolling_volatility",
                    value=roll_latest,
                    source_block=BLOCK_2_2,
                    source_artifact=ARTIFACT_XRAY,
                    evidence_path=evidence_path,
                    interpretation_en=f"Latest 12-month rolling volatility is {roll_latest:.3f}.",
                    raw_field_path=f"{BLOCK_2_2}.rolling_diagnostics.core_view.rolling_volatility_12m.latest",
                ),
            )

        avg_corr = _as_float(corr.get("avg_pairwise_correlation"))
        if avg_corr is not None:
            _emit(
                bucket,
                EvidenceSignal(
                    signal="avg_pairwise_correlation",
                    value=avg_corr,
                    source_block=BLOCK_2_2,
                    source_artifact=ARTIFACT_XRAY,
                    evidence_path=evidence_path,
                    interpretation_en=f"Average pairwise correlation is {avg_corr:.3f}.",
                    raw_field_path=f"{BLOCK_2_2}.correlation_breakdown.avg_pairwise_correlation",
                ),
            )
            if avg_corr <= 0.35:
                _emit(
                    bucket,
                    EvidenceSignal(
                        signal="low_correlation_breadth",
                        value=avg_corr,
                        source_block=BLOCK_2_2,
                        source_artifact=ARTIFACT_XRAY,
                        evidence_path=evidence_path,
                        interpretation_en="Pairwise correlations suggest reasonable breadth.",
                        raw_field_path=f"{BLOCK_2_2}.correlation_breakdown.avg_pairwise_correlation",
                    ),
                )
        return legacy_used

    sections = _sections(xray)
    for item in _items(sections.get("risk_diagnostics")):
        legacy_used = True
        vol = _as_float(
            item.get("vol_annual")
            or item.get("volatility")
            or item.get("portfolio_volatility")
        )
        if vol is not None:
            _emit(
                bucket,
                EvidenceSignal(
                    signal="vol_annual",
                    value=vol,
                    source_block="sections.risk_diagnostics",
                    source_artifact=ARTIFACT_XRAY,
                    evidence_path="legacy_fallback",
                    interpretation_en=f"Legacy risk diagnostics report volatility {vol:.3f}.",
                    limitation_en="Canonical block_2_2_portfolio_metrics unavailable.",
                    raw_field_path="sections.risk_diagnostics.items",
                ),
            )
        drawdown = _as_float(item.get("max_drawdown") or item.get("drawdown"))
        if drawdown is not None:
            _emit(
                bucket,
                EvidenceSignal(
                    signal="max_drawdown",
                    value=drawdown,
                    source_block="sections.risk_diagnostics",
                    source_artifact=ARTIFACT_XRAY,
                    evidence_path="legacy_fallback",
                    interpretation_en=f"Legacy risk diagnostics report max drawdown {drawdown:.3f}.",
                    limitation_en="Canonical block_2_2_portfolio_metrics unavailable.",
                    raw_field_path="sections.risk_diagnostics.items",
                ),
            )
    return legacy_used


def _extract_block_2_3(
    bucket: dict[str, list[EvidenceSignal]],
    xray: dict[str, Any],
    evidence_path: str,
) -> bool:
    block = xray.get(BLOCK_2_3)
    legacy_used = False
    if _block_status_ok(block) and isinstance(block, dict):
        betas_5y = block.get("factor_betas_5y") if isinstance(block.get("factor_betas_5y"), dict) else {}
        snapshot = block.get("factor_beta_snapshot") if isinstance(block.get("factor_beta_snapshot"), dict) else {}
        beta_source = betas_5y.get("betas") if isinstance(betas_5y.get("betas"), dict) else snapshot
        if isinstance(beta_source, dict):
            for sig, key, label in (
                ("beta_eq", "beta_eq", "Equity factor beta"),
                ("beta_rr", "beta_rr", "Real-rates factor beta"),
                ("beta_credit", "beta_credit", "Credit factor beta"),
            ):
                val = _as_float(beta_source.get(key))
                if val is not None:
                    _emit(
                        bucket,
                        EvidenceSignal(
                            signal=sig,
                            value=val,
                            source_block=BLOCK_2_3,
                            source_artifact=ARTIFACT_XRAY,
                            evidence_path=evidence_path,
                            interpretation_en=f"{label} is {val:.3f} (5Y weekly factor regression).",
                            raw_field_path=f"{BLOCK_2_3}.factor_betas_5y.betas.{key}",
                        ),
                    )
        return legacy_used

    sections = _sections(xray)
    for item in _items(sections.get("factor_exposure")):
        legacy_used = True
        beta = _as_float(item.get("beta_eq") or item.get("equity_beta"))
        if beta is not None:
            _emit(
                bucket,
                EvidenceSignal(
                    signal="beta_eq",
                    value=beta,
                    source_block="sections.factor_exposure",
                    source_artifact=ARTIFACT_XRAY,
                    evidence_path="legacy_fallback",
                    interpretation_en=f"Legacy factor exposure reports equity beta {beta:.3f}.",
                    limitation_en="Canonical block_2_3_factor_exposure unavailable.",
                    raw_field_path="sections.factor_exposure.items",
                ),
            )
            _emit(
                bucket,
                EvidenceSignal(
                    signal="beta_portfolio",
                    value=beta,
                    source_block="sections.factor_exposure",
                    source_artifact=ARTIFACT_XRAY,
                    evidence_path="legacy_fallback",
                    interpretation_en="Legacy factor exposure used as beta cross-check.",
                    limitation_en="Canonical block_2_3_factor_exposure unavailable.",
                    raw_field_path="sections.factor_exposure.items",
                ),
            )
    return legacy_used


def _extract_block_2_4(
    bucket: dict[str, list[EvidenceSignal]],
    xray: dict[str, Any],
    evidence_path: str,
) -> None:
    block = xray.get(BLOCK_2_4)
    if not _block_status_ok(block) or not isinstance(block, dict):
        return
    alerts = block.get("alerts")
    if not isinstance(alerts, dict):
        return
    for alert_id, signal_name in _BLOCK_24_ALERT_SIGNALS.items():
        alert = alerts.get(alert_id)
        if not isinstance(alert, dict):
            continue
        status = str(alert.get("status") or "")
        if status in {"", "Low", "Unavailable"}:
            continue
        _emit(
            bucket,
            EvidenceSignal(
                signal=signal_name,
                value={
                    "status": status,
                    "score": alert.get("score"),
                },
                source_block=BLOCK_2_4,
                source_artifact=ARTIFACT_XRAY,
                evidence_path=evidence_path,
                interpretation_en=str(alert.get("summary") or alert.get("interpretation") or f"{alert_id} alert is {status}."),
                severity=_normalize_band(status),
                confidence=_normalize_band(alert.get("confidence")),
                linked_assets=_linked_assets_from_alert(alert),
                raw_field_path=f"{BLOCK_2_4}.alerts.{alert_id}",
            ),
        )


def _extract_block_2_5(
    bucket: dict[str, list[EvidenceSignal]],
    xray: dict[str, Any],
    evidence_path: str,
) -> None:
    block = xray.get(BLOCK_2_5)
    if not _block_status_ok(block) or not isinstance(block, dict):
        return
    top1 = block.get("top1_rc_asset") if isinstance(block.get("top1_rc_asset"), dict) else {}
    rc_share = _as_float(top1.get("rc_pct") or top1.get("risk_contribution_pct"))
    if rc_share is not None:
        linked = (str(top1.get("ticker")),) if top1.get("ticker") else ()
        _emit(
            bucket,
            EvidenceSignal(
                signal="rc_top1_share",
                value=rc_share,
                source_block=BLOCK_2_5,
                source_artifact=ARTIFACT_XRAY,
                evidence_path=evidence_path,
                interpretation_en=f"Largest variance risk contributor holds {rc_share:.1f}% of portfolio variance risk.",
                linked_assets=linked,
                raw_field_path=f"{BLOCK_2_5}.top1_rc_asset.rc_pct",
            ),
        )


def _extract_block_2_6(
    bucket: dict[str, list[EvidenceSignal]],
    xray: dict[str, Any],
    evidence_path: str,
) -> None:
    block = xray.get(BLOCK_2_6)
    if not isinstance(block, dict):
        return
    for risk in block.get("risk_types") or []:
        if not isinstance(risk, dict):
            continue
        risk_type = str(risk.get("risk_type") or "")
        if risk_type not in RISK_TYPES:
            continue
        severity = _severity_from_block_26(risk.get("severity"))
        if severity in {None, "low", "unavailable"}:
            continue
        signal_name = f"block_2_6_{risk_type}"
        _emit(
            bucket,
            EvidenceSignal(
                signal=signal_name,
                value={
                    "score_0_100": risk.get("score_0_100"),
                    "severity": risk.get("severity"),
                },
                source_block=BLOCK_2_6,
                source_artifact=ARTIFACT_XRAY,
                evidence_path=evidence_path,
                interpretation_en=str(
                    risk.get("short_diagnosis")
                    or risk.get("why_status")
                    or risk.get("risk_title")
                    or f"{risk_type} weakness hypothesis is {risk.get('severity')}."
                ),
                severity=severity,
                confidence=_normalize_band(risk.get("confidence")),
                raw_field_path=f"{BLOCK_2_6}.risk_types[{risk_type}]",
            ),
        )


def _extract_stress_blocks(
    bucket: dict[str, list[EvidenceSignal]],
    stress: dict[str, Any],
    warnings: list[str],
) -> dict[str, str | None]:
    provenance: dict[str, str | None] = {
        "hedge_gap_source": None,
        "stress_scorecard_source": None,
    }

    hg = _hedge_gap_block(stress)
    if hg is not None and str(hg.get("block_status") or "") != "unavailable":
        provenance["hedge_gap_source"] = HEDGE_GAP_V1_KEY
        _extract_hedge_gap_v1(bucket, hg)
    else:
        legacy_status = (
            (stress.get("stress_conclusions") or {}).get("hedge_gap_status")
            if isinstance(stress.get("stress_conclusions"), dict)
            else None
        )
        if legacy_status:
            provenance["hedge_gap_source"] = "stress_conclusions.hedge_gap_status"
            _extract_hedge_gap_legacy(bucket, stress, str(legacy_status))
        else:
            warnings.append("Hedge gap block unavailable; hedge signals omitted or pre-stress only.")

    scorecard = _scorecard_block(stress)
    if scorecard is not None:
        provenance["stress_scorecard_source"] = SCORECARD_V1_KEY
        _extract_scorecard_v1(bucket, scorecard)
    else:
        _extract_stress_legacy(bucket, stress)
        if stress.get("stress_scorecard_v1"):
            provenance["stress_scorecard_source"] = "stress_scorecard_v1"
        else:
            provenance["stress_scorecard_source"] = None
            warnings.append("Stress scorecard v1 unavailable.")

    return provenance


def _extract_hedge_gap_v1(bucket: dict[str, list[EvidenceSignal]], hg: dict[str, Any]) -> None:
    summary = hg.get("summary") if isinstance(hg.get("summary"), dict) else {}
    main = summary.get("main_hedge_gap") if isinstance(summary.get("main_hedge_gap"), dict) else {}
    ratio = _first_float(
        main.get("offset_coverage_ratio"),
        summary.get("main_hedge_gap_offset_coverage_ratio"),
    )
    protection = str(main.get("protection_status") or "")
    loss = _first_float(
        main.get("portfolio_loss_pct"),
        summary.get("main_hedge_gap_portfolio_loss_pct"),
    )

    if ratio is not None:
        _emit(
            bucket,
            EvidenceSignal(
                signal="offset_coverage_ratio",
                value=ratio,
                source_block=BLOCK_3_3,
                source_artifact=ARTIFACT_STRESS,
                evidence_path="primary",
                interpretation_en=f"Offset coverage ratio is {ratio:.2f} in the main hedge-gap scenario.",
                severity="high" if ratio <= 0.2 else "medium" if ratio <= 0.45 else "low",
                confidence=_normalize_band(main.get("confidence")),
                raw_field_path=f"{HEDGE_GAP_V1_KEY}.summary.main_hedge_gap.offset_coverage_ratio",
            ),
        )
        if ratio >= _STRONG_OFFSET_THRESHOLD:
            _emit(
                bucket,
                EvidenceSignal(
                    signal="strong_offset_coverage",
                    value=ratio,
                    source_block=BLOCK_3_3,
                    source_artifact=ARTIFACT_STRESS,
                    evidence_path="primary",
                    interpretation_en="Hurt assets were materially offset by assets that helped in stress.",
                    raw_field_path=f"{HEDGE_GAP_V1_KEY}.summary.main_hedge_gap.offset_coverage_ratio",
                ),
            )
            _emit(
                bucket,
                EvidenceSignal(
                    signal="strong_hedge_offset",
                    value=ratio,
                    source_block=BLOCK_3_3,
                    source_artifact=ARTIFACT_STRESS,
                    evidence_path="primary",
                    interpretation_en="Strong internal hedge offset observed in main stress scenario.",
                    raw_field_path=f"{HEDGE_GAP_V1_KEY}.summary.main_hedge_gap.offset_coverage_ratio",
                ),
            )

    if protection:
        _emit(
            bucket,
            EvidenceSignal(
                signal="protection_status",
                value=protection,
                source_block=BLOCK_3_3,
                source_artifact=ARTIFACT_STRESS,
                evidence_path="primary",
                interpretation_en=f"Main hedge-gap protection status is {protection.replace('_', ' ')}.",
                severity="high" if protection in _WEAK_PROTECTION else "medium",
                raw_field_path=f"{HEDGE_GAP_V1_KEY}.summary.main_hedge_gap.protection_status",
            ),
        )

    if main:
        _emit(
            bucket,
            EvidenceSignal(
                signal="main_hedge_gap",
                value={
                    "risk_type": main.get("risk_type"),
                    "portfolio_loss_pct": loss,
                    "offset_coverage_ratio": ratio,
                },
                source_block=BLOCK_3_3,
                source_artifact=ARTIFACT_STRESS,
                evidence_path="primary",
                interpretation_en=str(summary.get("diagnosis_summary_en") or "Main hedge-gap row from Block 3.3."),
                raw_field_path=f"{HEDGE_GAP_V1_KEY}.summary.main_hedge_gap",
            ),
        )

    for row in hg.get("by_risk_type") or []:
        if not isinstance(row, dict):
            continue
        risk_type = str(row.get("risk_type") or "")
        scenario_id = str(row.get("linked_scenario_id") or "")
        pnl = _as_float(row.get("portfolio_loss_pct"))
        if "rates" in risk_type.lower() or scenario_id == "rates_shock":
            if pnl is not None:
                _emit(
                    bucket,
                    EvidenceSignal(
                        signal="rates_scenario_loss",
                        value=pnl,
                        source_block=BLOCK_3_3,
                        source_artifact=ARTIFACT_STRESS,
                        evidence_path="primary",
                        interpretation_en=f"Rates-linked scenario loss is {pnl:.1%}.",
                        raw_field_path=f"{HEDGE_GAP_V1_KEY}.by_risk_type[{risk_type}]",
                    ),
                )
            prot = str(row.get("protection_status") or "")
            if prot in {"strong_protection", "partial_protection"}:
                _emit(
                    bucket,
                    EvidenceSignal(
                        signal="rates_hedge_present",
                        value=prot,
                        source_block=BLOCK_3_3,
                        source_artifact=ARTIFACT_STRESS,
                        evidence_path="primary",
                        interpretation_en="Rates-up scenario shows partial or strong internal protection.",
                        raw_field_path=f"{HEDGE_GAP_V1_KEY}.by_risk_type[{risk_type}]",
                    ),
                )
        if scenario_id == "rates_shock" or "rates" in risk_type.lower():
            _emit(
                bucket,
                EvidenceSignal(
                    signal="rates_shock_stress",
                    value={"portfolio_loss_pct": pnl, "protection_status": row.get("protection_status")},
                    source_block=BLOCK_3_3,
                    source_artifact=ARTIFACT_STRESS,
                    evidence_path="primary",
                    interpretation_en="Rates shock stress row from hedge-gap analysis.",
                    raw_field_path=f"{HEDGE_GAP_V1_KEY}.by_risk_type[{risk_type}]",
                ),
            )
        if scenario_id in {"liquidity_shock", "credit_shock"} or "liquidity" in risk_type.lower():
            _emit(
                bucket,
                EvidenceSignal(
                    signal="liquidity_shock_stress",
                    value={"scenario_id": scenario_id, "portfolio_loss_pct": pnl},
                    source_block=BLOCK_3_3,
                    source_artifact=ARTIFACT_STRESS,
                    evidence_path="primary",
                    interpretation_en="Liquidity or credit stress row from hedge-gap analysis.",
                    raw_field_path=f"{HEDGE_GAP_V1_KEY}.by_risk_type[{risk_type}]",
                ),
            )


def _extract_hedge_gap_legacy(
    bucket: dict[str, list[EvidenceSignal]],
    stress: dict[str, Any],
    status: str,
) -> None:
    _emit(
        bucket,
        EvidenceSignal(
            signal="protection_status",
            value=status,
            source_block="stress_conclusions",
            source_artifact=ARTIFACT_STRESS,
            evidence_path="legacy_fallback",
            interpretation_en=f"Legacy hedge-gap status is {status.replace('_', ' ')}.",
            limitation_en="hedge_gap_analysis_v1 unavailable.",
            raw_field_path="stress_conclusions.hedge_gap_status",
        ),
    )
    if status in {"weak", "mostly_weak_protection", "no_protection", "weak_protection"}:
        _emit(
            bucket,
            EvidenceSignal(
                signal="offset_coverage_ratio",
                value=0.0,
                source_block="stress_conclusions",
                source_artifact=ARTIFACT_STRESS,
                evidence_path="legacy_fallback",
                interpretation_en="Legacy hedge-gap status implies weak offset coverage.",
                limitation_en="hedge_gap_analysis_v1 unavailable.",
                raw_field_path="stress_conclusions.hedge_gap_status",
            ),
        )


def _extract_scorecard_v1(bucket: dict[str, list[EvidenceSignal]], scorecard: dict[str, Any]) -> None:
    worst_syn = scorecard.get("worst_synthetic_scenario")
    if isinstance(worst_syn, dict) and worst_syn.get("availability") == "available":
        loss = _as_float(worst_syn.get("portfolio_loss_pct"))
        _emit(
            bucket,
            EvidenceSignal(
                signal="worst_synthetic_scenario",
                value={
                    "scenario_id": worst_syn.get("scenario_id"),
                    "portfolio_loss_pct": loss,
                },
                source_block=BLOCK_3_4,
                source_artifact=ARTIFACT_STRESS,
                evidence_path="primary",
                interpretation_en=f"Worst synthetic stress loss is {loss:.1%}." if loss is not None else "Worst synthetic scenario available.",
                severity="high" if loss is not None and loss <= -0.12 else "medium" if loss is not None and loss <= -0.06 else "low",
                raw_field_path=f"{SCORECARD_V1_KEY}.worst_synthetic_scenario",
            ),
        )
        if loss is not None and loss > _IMMATERIAL_STRESS_LOSS:
            _emit(
                bucket,
                EvidenceSignal(
                    signal="immaterial_stress_loss",
                    value=loss,
                    source_block=BLOCK_3_4,
                    source_artifact=ARTIFACT_STRESS,
                    evidence_path="primary",
                    interpretation_en="Worst synthetic stress loss is below materiality floor.",
                    raw_field_path=f"{SCORECARD_V1_KEY}.worst_synthetic_scenario.portfolio_loss_pct",
                ),
            )
            _emit(
                bucket,
                EvidenceSignal(
                    signal="stress_loss_immaterial",
                    value=loss,
                    source_block=BLOCK_3_4,
                    source_artifact=ARTIFACT_STRESS,
                    evidence_path="primary",
                    interpretation_en="Stress losses are not material on worst synthetic scenario.",
                    raw_field_path=f"{SCORECARD_V1_KEY}.worst_synthetic_scenario.portfolio_loss_pct",
                ),
            )

    worst_hist = scorecard.get("worst_historical_scenario")
    if isinstance(worst_hist, dict) and worst_hist.get("availability") == "available":
        dd = _as_float(worst_hist.get("drawdown_pct") or worst_hist.get("portfolio_loss_pct"))
        _emit(
            bucket,
            EvidenceSignal(
                signal="worst_historical_scenario",
                value={
                    "episode_id": worst_hist.get("episode_id"),
                    "drawdown_pct": dd,
                },
                source_block=BLOCK_3_4,
                source_artifact=ARTIFACT_STRESS,
                evidence_path="primary",
                interpretation_en=f"Worst historical drawdown is {dd:.1%}." if dd is not None else "Worst historical scenario available.",
                raw_field_path=f"{SCORECARD_V1_KEY}.worst_historical_scenario",
            ),
        )

    diagnosis = scorecard.get("stress_diagnosis")
    if isinstance(diagnosis, dict) and diagnosis.get("availability") == "available":
        _emit(
            bucket,
            EvidenceSignal(
                signal="stress_diagnosis",
                value={
                    "headline_en": diagnosis.get("headline_en"),
                    "stress_severity": diagnosis.get("stress_severity"),
                },
                source_block=BLOCK_3_4,
                source_artifact=ARTIFACT_STRESS,
                evidence_path="primary",
                interpretation_en=str(diagnosis.get("headline_en") or "Stress diagnosis headline from Block 3.4."),
                severity=_normalize_band(diagnosis.get("stress_severity")),
                confidence=_normalize_band(diagnosis.get("diagnosis_confidence")),
                raw_field_path=f"{SCORECARD_V1_KEY}.stress_diagnosis",
            ),
        )

    hg_summary = scorecard.get("hedge_gap_summary")
    if isinstance(hg_summary, dict) and hg_summary.get("availability") == "available":
        _emit(
            bucket,
            EvidenceSignal(
                signal="main_hedge_gap",
                value=hg_summary,
                source_block=BLOCK_3_4,
                source_artifact=ARTIFACT_STRESS,
                evidence_path="primary",
                interpretation_en=str(hg_summary.get("headline_en") or "Hedge-gap summary from stress scorecard."),
                raw_field_path=f"{SCORECARD_V1_KEY}.hedge_gap_summary",
            ),
        )

    vol_sig = bucket.get("vol_annual")
    tail_sig = bucket.get("es_95") or bucket.get("tail_risk_alert")
    if vol_sig and tail_sig and worst_syn is None:
        vol_val = _as_float(vol_sig[0].value)
        if vol_val is not None and vol_val < 0.14:
            _emit(
                bucket,
                EvidenceSignal(
                    signal="vol_low_tail_high_only_pre_stress",
                    value={"vol_annual": vol_val},
                    source_block=BLOCK_3_4,
                    source_artifact=ARTIFACT_STRESS,
                    evidence_path="pre_stress_only",
                    interpretation_en="Tail metrics elevated while volatility is moderate and stress scorecard synthetic worst is unavailable.",
                    limitation_en="Pre-stress tail read without synthetic stress confirmation.",
                    raw_field_path=f"{SCORECARD_V1_KEY}.worst_synthetic_scenario",
                ),
            )

    vol_only = bucket.get("vol_annual")
    if (
        vol_only
        and worst_syn
        and isinstance(worst_syn, dict)
        and worst_syn.get("availability") == "available"
    ):
        vol_val = _as_float(vol_only[0].value)
        syn_loss = _as_float(worst_syn.get("portfolio_loss_pct"))
        if vol_val is not None and syn_loss is not None and vol_val >= 0.18 and syn_loss > _IMMATERIAL_STRESS_LOSS:
            _emit(
                bucket,
                EvidenceSignal(
                    signal="low_stress_loss_with_high_vol",
                    value={"vol_annual": vol_val, "worst_synthetic_loss": syn_loss},
                    source_block=BLOCK_3_4,
                    source_artifact=ARTIFACT_STRESS,
                    evidence_path="primary",
                    interpretation_en="Volatility is elevated but worst synthetic stress loss is not material.",
                    raw_field_path=f"{SCORECARD_V1_KEY}.worst_synthetic_scenario",
                ),
            )


def _extract_stress_legacy(bucket: dict[str, list[EvidenceSignal]], stress: dict[str, Any]) -> None:
    legacy = stress.get("stress_scorecard_v1")
    if not isinstance(legacy, dict):
        return
    worst_id = legacy.get("worst_scenario_id")
    if worst_id:
        for row in stress.get("scenario_results") or []:
            if not isinstance(row, dict):
                continue
            if row.get("scenario_id") != worst_id:
                continue
            pnl = _as_float(row.get("portfolio_pnl_pct"))
            _emit(
                bucket,
                EvidenceSignal(
                    signal="worst_synthetic_scenario",
                    value={"scenario_id": worst_id, "portfolio_loss_pct": pnl},
                    source_block="stress_scorecard_v1",
                    source_artifact=ARTIFACT_STRESS,
                    evidence_path="legacy_fallback",
                    interpretation_en=f"Legacy stress scorecard worst scenario {worst_id}.",
                    limitation_en="current_portfolio_stress_scorecard_v1 unavailable.",
                    raw_field_path="stress_scorecard_v1.worst_scenario_id",
                ),
            )
            break


def _extract_data_quality(
    bucket: dict[str, list[EvidenceSignal]],
    xray: dict[str, Any],
    stress: dict[str, Any],
    warnings: list[str],
) -> None:
    sections = _sections(xray)
    partial = [
        key
        for key, section in sections.items()
        if isinstance(section, dict) and section.get("status") in {"partial", "unavailable"}
    ]
    product_partial = [
        key
        for key in (
            BLOCK_2_1,
            BLOCK_2_2,
            BLOCK_2_3,
            BLOCK_2_4,
            BLOCK_2_5,
            BLOCK_2_6,
        )
        if isinstance(xray.get(key), dict)
        and str(xray[key].get("status") or "ok").lower() in {"partial", "unavailable"}
    ]
    if partial or product_partial:
        _emit(
            bucket,
            EvidenceSignal(
                signal="partial_sections",
                value={"legacy_sections": partial, "product_blocks": product_partial},
                source_block="portfolio_xray",
                source_artifact=ARTIFACT_XRAY,
                evidence_path="primary",
                interpretation_en=(
                    f"{len(partial)} legacy section(s) and {len(product_partial)} product block(s) "
                    "are partial or unavailable."
                ),
                severity="medium" if product_partial else None,
                raw_field_path="sections.*.status;block_2_*.*.status",
            ),
        )
    if len(partial) >= 3 or len(product_partial) >= 3:
        _emit(
            bucket,
            EvidenceSignal(
                signal="data_trust_failure",
                value={"partial_count": len(partial) + len(product_partial)},
                source_block="sections",
                source_artifact=ARTIFACT_XRAY,
                evidence_path="primary",
                interpretation_en="Multiple upstream blocks are partial or unavailable; diagnosis trust is reduced.",
                severity="high",
                raw_field_path="sections.*.status",
            ),
        )
        warnings.append("Data trust failure: three or more sections/blocks partial or unavailable.")

    hg = _hedge_gap_block(stress)
    sc = _scorecard_block(stress)
    stress_missing = (
        (hg is None or str(hg.get("block_status") or "") == "unavailable")
        and (sc is None or sc.get("availability") == "unavailable")
        and not stress.get("stress_conclusions")
    )
    if stress_missing:
        _emit(
            bucket,
            EvidenceSignal(
                signal="stress_block_unavailable",
                value=True,
                source_block=BLOCK_3_4,
                source_artifact=ARTIFACT_STRESS,
                evidence_path="primary",
                interpretation_en="Stress report blocks 3.3/3.4 are unavailable.",
                severity="high",
                raw_field_path=f"{ARTIFACT_STRESS}",
            ),
        )
        warnings.append("Stress blocks unavailable for evidence extraction.")
