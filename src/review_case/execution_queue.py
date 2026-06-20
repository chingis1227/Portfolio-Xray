"""Optional execution-queue seam for Review Case staged diagnosis work.

The current FastAPI staged-review route starts background diagnosis execution
inside the API process. This module keeps that behavior as the default while
adding a narrow, opt-in RQ plus Redis adapter for later productionization.
Redis and RQ are optional: they are imported only when the queue backend is
explicitly requested, and failed or incomplete RQ configuration falls back to
the existing in-process worker path.
"""

from __future__ import annotations

import importlib
import os
import re
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping


ReviewCaseExecutionRunner = Callable[..., None]
ReserveWorkerSlot = Callable[[], bool]

_RQ_BACKENDS = {"rq", "redis", "rq_redis"}
_IN_PROCESS_BACKENDS = {"", "in_process", "in-process", "local", "thread", "threads"}
_DEFAULT_QUEUE_NAME = "pmri-review-case-execution"
_QUEUE_NAME_PATTERN = re.compile(r"^[A-Za-z0-9_.:-]{1,128}$")
_SUPPORTED_REDIS_URL_PREFIXES = ("redis://", "rediss://", "unix://")


def _clean_env_value(value: str | None) -> str:
    return (value or "").strip()


def _normalize_queue_name(raw_name: str | None) -> tuple[str, tuple[str, ...]]:
    queue_name = _clean_env_value(raw_name) or _DEFAULT_QUEUE_NAME
    if _QUEUE_NAME_PATTERN.fullmatch(queue_name):
        return queue_name, ()
    return _DEFAULT_QUEUE_NAME, ("invalid_queue_name",)


def _redis_url_supported(redis_url: str | None) -> bool:
    if not redis_url:
        return False
    return redis_url.startswith(_SUPPORTED_REDIS_URL_PREFIXES)


@dataclass(frozen=True)
class ReviewCaseExecutionJob:
    """Execution request for one staged Review Case diagnosis run."""

    review_id: str
    payload_path: Path
    mode: str

    def runner_kwargs(self) -> dict[str, Any]:
        return {
            "review_id": self.review_id,
            "payload_path": self.payload_path,
            "mode": self.mode,
        }


@dataclass(frozen=True)
class ReviewCaseExecutionEnqueueResult:
    """Internal result for enqueue attempts.

    This shape is intentionally not part of the public FastAPI response. It is
    used only by the route adapter to decide whether the existing start request
    should proceed or return the already-established queue-full error envelope.
    """

    accepted: bool
    backend: str
    job_id: str | None = None
    reason: str | None = None
    fallback_from: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ReviewCaseExecutionQueueConfig:
    """Validated internal queue configuration.

    This configuration is intentionally internal-only. It is safe to log the
    metadata returned by :meth:`operational_metadata` because it records whether
    a Redis URL was configured without copying the URL value or credentials.
    """

    backend: str
    requested_backend: str
    redis_url: str | None
    queue_name: str
    warnings: tuple[str, ...] = ()

    def operational_metadata(self) -> dict[str, Any]:
        return {
            "backend": self.backend,
            "requested_backend": self.requested_backend,
            "queue_name": self.queue_name,
            "redis_url_configured": bool(self.redis_url),
            "warnings": list(self.warnings),
        }


class InProcessReviewCaseExecutionQueue:
    """Default local background queue using the existing daemon-thread path."""

    backend = "in_process"

    def __init__(
        self,
        *,
        runner: ReviewCaseExecutionRunner,
        reserve_slot: ReserveWorkerSlot,
    ) -> None:
        self.runner = runner
        self.reserve_slot = reserve_slot

    def enqueue(self, job: ReviewCaseExecutionJob) -> ReviewCaseExecutionEnqueueResult:
        if not self.reserve_slot():
            return ReviewCaseExecutionEnqueueResult(
                accepted=False,
                backend=self.backend,
                reason="local_worker_queue_full",
                metadata={"queue_name": self.backend},
            )
        worker = threading.Thread(
            target=self.runner,
            kwargs=job.runner_kwargs(),
            name=f"staged-review-{job.review_id}",
            daemon=True,
        )
        worker.start()
        return ReviewCaseExecutionEnqueueResult(
            accepted=True,
            backend=self.backend,
            metadata={"queue_name": self.backend},
        )


class RqRedisReviewCaseExecutionQueue:
    """Opt-in RQ plus Redis queue adapter.

    RQ is a small Python job queue that stores jobs in Redis. This prototype
    only enqueues the existing module-level staged-review runner. It does not
    start or manage workers, migrate public status fields, or require RQ/Redis
    for default local development.
    """

    backend = "rq_redis"

    def __init__(
        self,
        *,
        runner: ReviewCaseExecutionRunner,
        redis_url: str | None,
        queue_name: str,
        rq_module: Any | None = None,
        redis_module: Any | None = None,
    ) -> None:
        self.runner = runner
        self.redis_url = (redis_url or "").strip()
        self.queue_name, self._queue_name_warnings = _normalize_queue_name(queue_name)
        self._rq_module = rq_module
        self._redis_module = redis_module

    def enqueue(self, job: ReviewCaseExecutionJob) -> ReviewCaseExecutionEnqueueResult:
        metadata = {
            "queue_name": self.queue_name,
            "redis_url_configured": bool(self.redis_url),
        }
        if self._queue_name_warnings:
            metadata["warnings"] = list(self._queue_name_warnings)
        if not self.redis_url:
            return ReviewCaseExecutionEnqueueResult(
                accepted=False,
                backend=self.backend,
                reason="redis_url_missing",
                metadata=metadata,
            )
        if not _redis_url_supported(self.redis_url):
            return ReviewCaseExecutionEnqueueResult(
                accepted=False,
                backend=self.backend,
                reason="redis_url_unsupported_scheme",
                metadata=metadata,
            )
        try:
            rq_module = self._rq_module or importlib.import_module("rq")
            redis_module = self._redis_module or importlib.import_module("redis")
            connection = redis_module.Redis.from_url(self.redis_url)
            queue = rq_module.Queue(self.queue_name, connection=connection)
            queued_job = queue.enqueue(
                self.runner,
                kwargs=job.runner_kwargs(),
                job_id=f"review-case-execution:{job.review_id}",
                result_ttl=3600,
                failure_ttl=86400,
            )
        except Exception as exc:  # pragma: no cover - exercised through fallback wrapper
            return ReviewCaseExecutionEnqueueResult(
                accepted=False,
                backend=self.backend,
                reason="rq_enqueue_failed",
                metadata={
                    **metadata,
                    "error_type": type(exc).__name__,
                },
            )
        return ReviewCaseExecutionEnqueueResult(
            accepted=True,
            backend=self.backend,
            job_id=str(getattr(queued_job, "id", "")) or None,
            metadata={
                **metadata,
                "result_ttl_seconds": 3600,
                "failure_ttl_seconds": 86400,
            },
        )


def review_case_queue_config(
    env: Mapping[str, str] | None = None,
) -> ReviewCaseExecutionQueueConfig:
    """Return validated internal queue configuration.

    Unsupported backends and unsafe queue names fall back to safe local
    defaults. This keeps default operation and misconfigured deployments from
    requiring Redis/RQ while still making opt-in queue intent inspectable.
    """

    source = env if env is not None else os.environ
    requested_backend = _clean_env_value(source.get("PMRI_REVIEW_CASE_QUEUE_BACKEND")).lower()
    warnings: list[str] = []
    if requested_backend in _RQ_BACKENDS:
        backend = "rq_redis"
    elif requested_backend in _IN_PROCESS_BACKENDS:
        backend = "in_process"
    else:
        backend = "in_process"
        warnings.append("unsupported_queue_backend")

    queue_name, queue_warnings = _normalize_queue_name(
        source.get("PMRI_REVIEW_CASE_RQ_QUEUE")
        or source.get("PMRI_REVIEW_CASE_QUEUE_NAME")
    )
    warnings.extend(queue_warnings)

    redis_url = _clean_env_value(
        source.get("PMRI_REVIEW_CASE_REDIS_URL") or source.get("REDIS_URL")
    ) or None
    if backend == "rq_redis":
        if not redis_url:
            warnings.append("redis_url_missing")
        elif not _redis_url_supported(redis_url):
            warnings.append("redis_url_unsupported_scheme")

    return ReviewCaseExecutionQueueConfig(
        backend=backend,
        requested_backend=requested_backend or "in_process",
        redis_url=redis_url,
        queue_name=queue_name,
        warnings=tuple(warnings),
    )


def review_case_queue_backend(env: Mapping[str, str] | None = None) -> str:
    """Return the configured internal Review Case queue backend.

    The default is ``in_process`` to preserve local and production behavior
    unless an operator explicitly opts into the prototype RQ/Redis path.
    """

    return review_case_queue_config(env).backend


def review_case_redis_url(env: Mapping[str, str] | None = None) -> str | None:
    return review_case_queue_config(env).redis_url


def review_case_queue_name(env: Mapping[str, str] | None = None) -> str:
    return review_case_queue_config(env).queue_name


def enqueue_with_optional_rq(
    job: ReviewCaseExecutionJob,
    *,
    runner: ReviewCaseExecutionRunner,
    reserve_slot: ReserveWorkerSlot,
    env: Mapping[str, str] | None = None,
) -> ReviewCaseExecutionEnqueueResult:
    """Enqueue one staged Review Case job with RQ only when explicitly enabled."""

    config = review_case_queue_config(env)
    if config.backend == "rq_redis":
        rq_result = RqRedisReviewCaseExecutionQueue(
            runner=runner,
            redis_url=config.redis_url,
            queue_name=config.queue_name,
        ).enqueue(job)
        if rq_result.accepted:
            return ReviewCaseExecutionEnqueueResult(
                accepted=True,
                backend=rq_result.backend,
                job_id=rq_result.job_id,
                metadata={
                    **config.operational_metadata(),
                    **dict(rq_result.metadata),
                },
            )
        local_result = InProcessReviewCaseExecutionQueue(
            runner=runner,
            reserve_slot=reserve_slot,
        ).enqueue(job)
        return ReviewCaseExecutionEnqueueResult(
            accepted=local_result.accepted,
            backend=local_result.backend,
            job_id=local_result.job_id,
            reason=local_result.reason or rq_result.reason,
            fallback_from=rq_result.backend,
            metadata={
                **config.operational_metadata(),
                "fallback_reason": rq_result.reason,
                "fallback_metadata": dict(rq_result.metadata),
                "fallback_backend": local_result.backend,
            },
        )
    return InProcessReviewCaseExecutionQueue(
        runner=runner,
        reserve_slot=reserve_slot,
    ).enqueue(job)
