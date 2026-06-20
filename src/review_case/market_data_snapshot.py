"""Market-data basis metadata for Portfolio MRI Review Cases.

This module is an internal Review Case migration seam. It summarizes already
existing run metadata, provider status, and data-policy evidence so later
queue, storage, and screen read-model work can identify the market-data basis
of a review without fetching data, changing formulas, changing public FastAPI
envelopes, or changing generated artifact schemas.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from .artifact_manifest import ReviewCaseArtifactManifestError, review_case_artifact_ref

MARKET_DATA_SNAPSHOT_SCHEMA_VERSION = "review_case_market_data_snapshot_v1"


class ReviewCaseMarketDataSnapshotError(ValueError):
    """Raised when market-data snapshot metadata is unsafe or malformed."""


@dataclass(frozen=True)
class ReviewCaseMarketDataSnapshot:
    """Internal metadata summary of the market-data basis for one review.

    ``basis_key`` is a stable metadata fingerprint. It is not a price-panel
    fingerprint and must not be treated as proof that two reviews have identical
    raw observations; it identifies the already-disclosed provider/window/risk
    free basis available from existing run evidence.
    """

    review_id: str | None = None
    mode: str | None = None
    analysis_end: str | None = None
    analysis_window: str | None = None
    market_data_provider: str | None = None
    provider_status: Mapping[str, Any] = field(default_factory=dict)
    investor_currency: str | None = None
    returns_frequency: str | None = None
    configured_returns_frequency: str | None = None
    risk_free_source_requested: str | None = None
    risk_free_source_used: str | None = None
    risk_free_fallback_used: bool = False
    risk_free_fallback_reason: str | None = None
    benchmark_base_ticker: str | None = None
    cash_proxy_ticker: str | None = None
    source_refs: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        object.__setattr__(self, "review_id", _optional_text(self.review_id))
        object.__setattr__(self, "mode", _optional_text(self.mode))
        object.__setattr__(self, "analysis_end", _optional_text(self.analysis_end))
        object.__setattr__(self, "analysis_window", _optional_text(self.analysis_window))
        object.__setattr__(self, "market_data_provider", _optional_text(self.market_data_provider))
        object.__setattr__(self, "provider_status", _json_safe_mapping(self.provider_status))
        object.__setattr__(self, "investor_currency", _optional_text(self.investor_currency))
        object.__setattr__(self, "returns_frequency", _optional_text(self.returns_frequency))
        object.__setattr__(
            self,
            "configured_returns_frequency",
            _optional_text(self.configured_returns_frequency),
        )
        object.__setattr__(
            self,
            "risk_free_source_requested",
            _optional_text(self.risk_free_source_requested),
        )
        object.__setattr__(
            self,
            "risk_free_source_used",
            _optional_text(self.risk_free_source_used),
        )
        object.__setattr__(
            self,
            "risk_free_fallback_reason",
            _optional_text(self.risk_free_fallback_reason),
        )
        object.__setattr__(
            self,
            "benchmark_base_ticker",
            _optional_text(self.benchmark_base_ticker),
        )
        object.__setattr__(self, "cash_proxy_ticker", _optional_text(self.cash_proxy_ticker))
        object.__setattr__(
            self,
            "source_refs",
            tuple(_safe_source_ref(ref) for ref in self.source_refs),
        )

    @classmethod
    def from_run_metadata(
        cls,
        run_metadata: Mapping[str, Any],
        *,
        provider_status: Mapping[str, Any] | None = None,
        data_policy: Mapping[str, Any] | None = None,
        source_refs: Sequence[str] = (),
    ) -> "ReviewCaseMarketDataSnapshot":
        """Build snapshot metadata from existing run-local evidence.

        The method only reads dictionaries that are already present in current
        artifacts. It does not load market data providers, inspect generated
        price panels, or mutate the source artifacts.
        """

        if not isinstance(run_metadata, Mapping):
            raise ReviewCaseMarketDataSnapshotError("run_metadata must be a mapping.")

        analysis_setup = _mapping(run_metadata.get("analysis_setup"))
        input_assumptions = _mapping(run_metadata.get("input_assumptions"))
        run_info = _mapping(run_metadata.get("run_info"))
        resolved_config = _mapping(run_metadata.get("resolved_config"))
        derived_assumptions = _mapping(run_metadata.get("derived_assumptions"))
        resolved_assumptions = _mapping(analysis_setup.get("resolved_assumptions"))
        portfolio_input = _mapping(analysis_setup.get("portfolio_input"))
        risk_free_rate = _mapping(resolved_assumptions.get("risk_free_rate"))
        cash_proxy = _mapping(resolved_assumptions.get("cash_proxy"))
        risk_free_provenance = _mapping(derived_assumptions.get("risk_free_data_provenance"))
        policy = _mapping(data_policy)
        status = _provider_status(run_metadata, analysis_setup, provider_status)

        return cls(
            review_id=_text(run_metadata.get("review_id")),
            mode=_text(run_metadata.get("mode")),
            analysis_end=_text(
                run_metadata.get("analysis_end"),
                resolved_assumptions.get("analysis_end"),
                derived_assumptions.get("analysis_end_date"),
                run_info.get("analysis_end_date"),
            ),
            analysis_window=_text(
                analysis_setup.get("analysis_window"),
                input_assumptions.get("analysis_window"),
                run_metadata.get("analysis_end"),
                resolved_assumptions.get("analysis_end"),
            ),
            market_data_provider=_text(
                analysis_setup.get("market_data_provider"),
                resolved_assumptions.get("market_data_provider"),
                resolved_config.get("market_data_provider"),
                status.get("source") if status.get("source") == "frozen_fixture" else None,
            ),
            provider_status=status,
            investor_currency=_text(
                portfolio_input.get("investor_currency"),
                analysis_setup.get("investor_currency"),
                resolved_config.get("investor_currency"),
            ),
            returns_frequency=_text(
                resolved_assumptions.get("return_frequency"),
                derived_assumptions.get("returns_frequency"),
            ),
            configured_returns_frequency=_text(
                resolved_assumptions.get("configured_return_frequency"),
                derived_assumptions.get("configured_returns_frequency"),
            ),
            risk_free_source_requested=_text(
                risk_free_provenance.get("risk_free_source_requested"),
                risk_free_rate.get("source"),
                derived_assumptions.get("resolved_rf_source"),
            ),
            risk_free_source_used=_text(
                risk_free_provenance.get("risk_free_source_used"),
                risk_free_rate.get("source"),
                derived_assumptions.get("resolved_rf_source"),
            ),
            risk_free_fallback_used=bool(
                derived_assumptions.get("risk_free_fallback_used")
                or policy.get("risk_free_fallback_used")
                or risk_free_provenance.get("risk_free_fallback_used")
            ),
            risk_free_fallback_reason=_text(
                derived_assumptions.get("risk_free_fallback_reason"),
                policy.get("risk_free_fallback_reason"),
                risk_free_provenance.get("risk_free_fallback_reason"),
            ),
            benchmark_base_ticker=_text(
                resolved_assumptions.get("base_benchmark_ticker"),
                portfolio_input.get("base_benchmark_ticker"),
                resolved_config.get("benchmark_base_ticker"),
            ),
            cash_proxy_ticker=_text(
                cash_proxy.get("ticker"),
                derived_assumptions.get("resolved_cash_proxy_ticker"),
                resolved_config.get("cash_proxy_ticker"),
            ),
            source_refs=tuple(source_refs),
        )

    @property
    def basis_key(self) -> str:
        """Stable hash of the metadata fields that define the disclosed data basis."""

        return hashlib.sha256(
            json.dumps(
                self._basis_payload(),
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
            ).encode("utf-8")
        ).hexdigest()

    @property
    def evidence_source_ref(self) -> str:
        """Logical Evidence Graph source ref for this market-data basis."""

        return f"logical://market-data/{self.basis_key}"

    def to_dict(self) -> dict[str, Any]:
        """Serialize the internal metadata seam in a stable, testable shape."""

        return {
            "schema_version": MARKET_DATA_SNAPSHOT_SCHEMA_VERSION,
            "basis_key": self.basis_key,
            "evidence_source_ref": self.evidence_source_ref,
            "review_id": self.review_id,
            "mode": self.mode,
            "analysis_end": self.analysis_end,
            "analysis_window": self.analysis_window,
            "market_data_provider": self.market_data_provider,
            "provider_status": dict(self.provider_status),
            "investor_currency": self.investor_currency,
            "returns_frequency": self.returns_frequency,
            "configured_returns_frequency": self.configured_returns_frequency,
            "risk_free": {
                "source_requested": self.risk_free_source_requested,
                "source_used": self.risk_free_source_used,
                "fallback_used": self.risk_free_fallback_used,
                "fallback_reason": self.risk_free_fallback_reason,
            },
            "benchmark": {"base_ticker": self.benchmark_base_ticker},
            "cash_proxy": {"ticker": self.cash_proxy_ticker},
            "source_refs": list(self.source_refs),
        }

    def _basis_payload(self) -> dict[str, Any]:
        status = dict(self.provider_status)
        return {
            "analysis_end": self.analysis_end,
            "analysis_window": self.analysis_window,
            "market_data_provider": self.market_data_provider,
            "provider_source": status.get("source"),
            "provider_freshness": status.get("freshness"),
            "investor_currency": self.investor_currency,
            "returns_frequency": self.returns_frequency,
            "configured_returns_frequency": self.configured_returns_frequency,
            "risk_free_source_requested": self.risk_free_source_requested,
            "risk_free_source_used": self.risk_free_source_used,
            "risk_free_fallback_used": self.risk_free_fallback_used,
            "risk_free_fallback_reason": self.risk_free_fallback_reason,
            "benchmark_base_ticker": self.benchmark_base_ticker,
            "cash_proxy_ticker": self.cash_proxy_ticker,
        }


def _provider_status(
    run_metadata: Mapping[str, Any],
    analysis_setup: Mapping[str, Any],
    provider_status: Mapping[str, Any] | None,
) -> dict[str, Any]:
    return _json_safe_mapping(
        provider_status
        or _mapping(analysis_setup.get("provider_status"))
        or _mapping(run_metadata.get("provider_status"))
    )


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _text(*values: Any) -> str | None:
    for value in values:
        text = _optional_text(value)
        if text is not None:
            return text
    return None


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        text = value.strip()
        return text or None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return str(value)
    return None


def _safe_source_ref(value: Any) -> str:
    try:
        return review_case_artifact_ref(value)
    except ReviewCaseArtifactManifestError as exc:
        raise ReviewCaseMarketDataSnapshotError(str(exc)) from exc


def _json_safe_mapping(value: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ReviewCaseMarketDataSnapshotError("Provider status must be a mapping.")
    return {str(key): _json_safe(value) for key, value in value.items()}


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [_json_safe(item) for item in value]
    return str(value)
