from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from src.review_case.execution_queue import (
    InProcessReviewCaseExecutionQueue,
    ReviewCaseExecutionJob,
    RqRedisReviewCaseExecutionQueue,
    enqueue_with_optional_rq,
    review_case_queue_backend,
    review_case_queue_config,
    review_case_queue_name,
)


def test_default_queue_backend_is_in_process_when_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PMRI_REVIEW_CASE_QUEUE_BACKEND", raising=False)

    assert review_case_queue_backend() == "in_process"


def test_queue_config_falls_back_for_unsupported_backend_and_invalid_name() -> None:
    config = review_case_queue_config(
        {
            "PMRI_REVIEW_CASE_QUEUE_BACKEND": "celery",
            "PMRI_REVIEW_CASE_RQ_QUEUE": "unsafe queue name",
        }
    )

    assert config.backend == "in_process"
    assert config.requested_backend == "celery"
    assert config.queue_name == "pmri-review-case-execution"
    assert config.warnings == ("unsupported_queue_backend", "invalid_queue_name")
    assert config.operational_metadata() == {
        "backend": "in_process",
        "requested_backend": "celery",
        "queue_name": "pmri-review-case-execution",
        "redis_url_configured": False,
        "warnings": ["unsupported_queue_backend", "invalid_queue_name"],
    }


def test_queue_config_warns_on_invalid_opt_in_redis_url() -> None:
    config = review_case_queue_config(
        {
            "PMRI_REVIEW_CASE_QUEUE_BACKEND": "rq",
            "PMRI_REVIEW_CASE_REDIS_URL": "http://example.invalid/redis",
        }
    )

    assert config.backend == "rq_redis"
    assert config.redis_url == "http://example.invalid/redis"
    assert config.warnings == ("redis_url_unsupported_scheme",)
    assert review_case_queue_name({"PMRI_REVIEW_CASE_QUEUE_NAME": "pmri.safe:queue"}) == (
        "pmri.safe:queue"
    )


def test_in_process_queue_starts_daemon_worker_when_slot_is_available(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    started: list[dict[str, object]] = []

    class FakeThread:
        def __init__(self, *, target, kwargs, name, daemon):  # type: ignore[no-untyped-def]
            self._target = target
            self._kwargs = kwargs
            self.name = name
            self.daemon = daemon
            started.append({"name": name, "daemon": daemon, "kwargs": kwargs})

        def start(self) -> None:
            self._target(**self._kwargs)

    calls: list[tuple[str, Path, str]] = []

    def runner(review_id: str, payload_path: Path, *, mode: str) -> None:
        calls.append((review_id, payload_path, mode))

    monkeypatch.setattr("src.review_case.execution_queue.threading.Thread", FakeThread)

    queue = InProcessReviewCaseExecutionQueue(
        runner=runner,
        reserve_slot=lambda: True,
    )
    result = queue.enqueue(
        ReviewCaseExecutionJob(
            review_id="frontend_review_test",
            payload_path=Path("payload.json"),
            mode="demo_qa",
        )
    )

    assert result.accepted is True
    assert result.backend == "in_process"
    assert calls == [("frontend_review_test", Path("payload.json"), "demo_qa")]
    assert started == [
        {
            "name": "staged-review-frontend_review_test",
            "daemon": True,
            "kwargs": {
                "review_id": "frontend_review_test",
                "payload_path": Path("payload.json"),
                "mode": "demo_qa",
            },
        }
    ]


def test_in_process_queue_reports_full_when_slot_cannot_be_reserved() -> None:
    queue = InProcessReviewCaseExecutionQueue(
        runner=lambda *_args, **_kwargs: None,
        reserve_slot=lambda: False,
    )

    result = queue.enqueue(
        ReviewCaseExecutionJob(
            review_id="frontend_review_full",
            payload_path=Path("payload.json"),
            mode="live",
        )
    )

    assert result.accepted is False
    assert result.backend == "in_process"
    assert result.reason == "local_worker_queue_full"


def test_rq_queue_enqueues_to_configured_redis_without_running_job() -> None:
    enqueued: list[dict[str, object]] = []

    class FakeRedis:
        @staticmethod
        def from_url(url: str):  # type: ignore[no-untyped-def]
            return {"url": url}

    class FakeQueue:
        def __init__(self, name: str, *, connection):  # type: ignore[no-untyped-def]
            self.name = name
            self.connection = connection

        def enqueue(self, runner, *, kwargs, job_id, result_ttl, failure_ttl):  # type: ignore[no-untyped-def]
            enqueued.append(
                {
                    "name": self.name,
                    "connection": self.connection,
                    "runner": runner,
                    "kwargs": kwargs,
                    "job_id": job_id,
                    "result_ttl": result_ttl,
                    "failure_ttl": failure_ttl,
                }
            )
            return SimpleNamespace(id=job_id)

    queue = RqRedisReviewCaseExecutionQueue(
        runner=lambda *_args, **_kwargs: None,
        redis_url="redis://localhost:6379/0",
        queue_name="pmri-test",
        rq_module=SimpleNamespace(Queue=FakeQueue),
        redis_module=SimpleNamespace(Redis=FakeRedis),
    )

    result = queue.enqueue(
        ReviewCaseExecutionJob(
            review_id="frontend_review_rq",
            payload_path=Path("payload.json"),
            mode="live",
        )
    )

    assert result.accepted is True
    assert result.backend == "rq_redis"
    assert result.job_id == "review-case-execution:frontend_review_rq"
    assert result.metadata == {
        "queue_name": "pmri-test",
        "redis_url_configured": True,
        "result_ttl_seconds": 3600,
        "failure_ttl_seconds": 86400,
    }
    assert enqueued == [
        {
            "name": "pmri-test",
            "connection": {"url": "redis://localhost:6379/0"},
            "runner": queue.runner,
            "kwargs": {
                "review_id": "frontend_review_rq",
                "payload_path": Path("payload.json"),
                "mode": "live",
            },
            "job_id": "review-case-execution:frontend_review_rq",
            "result_ttl": 3600,
            "failure_ttl": 86400,
        }
    ]


def test_opt_in_rq_without_redis_url_falls_back_to_in_process(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PMRI_REVIEW_CASE_QUEUE_BACKEND", "rq")
    monkeypatch.delenv("PMRI_REVIEW_CASE_REDIS_URL", raising=False)
    monkeypatch.delenv("REDIS_URL", raising=False)

    calls: list[str] = []

    def runner(review_id: str, payload_path: Path, *, mode: str) -> None:
        calls.append(f"{review_id}:{payload_path.name}:{mode}")

    class FakeThread:
        def __init__(self, *, target, kwargs, name, daemon):  # type: ignore[no-untyped-def]
            self._target = target
            self._kwargs = kwargs

        def start(self) -> None:
            self._target(**self._kwargs)

    monkeypatch.setattr("src.review_case.execution_queue.threading.Thread", FakeThread)

    result = enqueue_with_optional_rq(
        ReviewCaseExecutionJob(
            review_id="frontend_review_fallback",
            payload_path=Path("payload.json"),
            mode="live",
        ),
        runner=runner,
        reserve_slot=lambda: True,
    )

    assert result.accepted is True
    assert result.backend == "in_process"
    assert result.fallback_from == "rq_redis"
    assert calls == ["frontend_review_fallback:payload.json:live"]


def test_rq_queue_rejects_unsupported_redis_url_without_importing_optional_packages() -> None:
    queue = RqRedisReviewCaseExecutionQueue(
        runner=lambda *_args, **_kwargs: None,
        redis_url="http://example.invalid/redis",
        queue_name="pmri-test",
    )

    result = queue.enqueue(
        ReviewCaseExecutionJob(
            review_id="frontend_review_bad_url",
            payload_path=Path("payload.json"),
            mode="live",
        )
    )

    assert result.accepted is False
    assert result.backend == "rq_redis"
    assert result.reason == "redis_url_unsupported_scheme"
    assert result.metadata == {
        "queue_name": "pmri-test",
        "redis_url_configured": True,
    }


def test_rq_queue_normalizes_unsafe_direct_queue_name() -> None:
    queue = RqRedisReviewCaseExecutionQueue(
        runner=lambda *_args, **_kwargs: None,
        redis_url="http://example.invalid/redis",
        queue_name="unsafe queue name",
    )

    result = queue.enqueue(
        ReviewCaseExecutionJob(
            review_id="frontend_review_bad_queue_name",
            payload_path=Path("payload.json"),
            mode="live",
        )
    )

    assert result.accepted is False
    assert result.reason == "redis_url_unsupported_scheme"
    assert result.metadata == {
        "queue_name": "pmri-review-case-execution",
        "redis_url_configured": True,
        "warnings": ["invalid_queue_name"],
    }


def test_rq_enqueue_failure_returns_bounded_reason_without_leaking_redis_url_secret() -> None:
    class FakeRedis:
        @staticmethod
        def from_url(url: str):  # type: ignore[no-untyped-def]
            return {"url": url}

    class FakeQueue:
        def __init__(self, name: str, *, connection):  # type: ignore[no-untyped-def]
            self.name = name
            self.connection = connection

        def enqueue(self, *_args, **_kwargs):  # type: ignore[no-untyped-def]
            raise RuntimeError("connection failed for redis://:secret@example.invalid/0")

    queue = RqRedisReviewCaseExecutionQueue(
        runner=lambda *_args, **_kwargs: None,
        redis_url="redis://:secret@example.invalid/0",
        queue_name="pmri-test",
        rq_module=SimpleNamespace(Queue=FakeQueue),
        redis_module=SimpleNamespace(Redis=FakeRedis),
    )

    result = queue.enqueue(
        ReviewCaseExecutionJob(
            review_id="frontend_review_rq_failure",
            payload_path=Path("payload.json"),
            mode="live",
        )
    )

    assert result.accepted is False
    assert result.backend == "rq_redis"
    assert result.reason == "rq_enqueue_failed"
    assert result.metadata == {
        "queue_name": "pmri-test",
        "redis_url_configured": True,
        "error_type": "RuntimeError",
    }
    assert "secret" not in result.reason


def test_opt_in_rq_enqueue_failure_falls_back_with_operational_metadata(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PMRI_REVIEW_CASE_QUEUE_BACKEND", "rq")
    monkeypatch.setenv("PMRI_REVIEW_CASE_REDIS_URL", "redis://localhost:6379/0")

    class FakeRedis:
        @staticmethod
        def from_url(url: str):  # type: ignore[no-untyped-def]
            return {"url": url}

    class FakeQueue:
        def __init__(self, name: str, *, connection):  # type: ignore[no-untyped-def]
            self.name = name
            self.connection = connection

        def enqueue(self, *_args, **_kwargs):  # type: ignore[no-untyped-def]
            raise ConnectionError("redis unavailable")

    def fake_import_module(name: str):  # type: ignore[no-untyped-def]
        if name == "rq":
            return SimpleNamespace(Queue=FakeQueue)
        if name == "redis":
            return SimpleNamespace(Redis=FakeRedis)
        raise AssertionError(f"unexpected import: {name}")

    calls: list[str] = []

    def runner(review_id: str, payload_path: Path, *, mode: str) -> None:
        calls.append(f"{review_id}:{payload_path.name}:{mode}")

    class FakeThread:
        def __init__(self, *, target, kwargs, name, daemon):  # type: ignore[no-untyped-def]
            self._target = target
            self._kwargs = kwargs

        def start(self) -> None:
            self._target(**self._kwargs)

    monkeypatch.setattr("src.review_case.execution_queue.importlib.import_module", fake_import_module)
    monkeypatch.setattr("src.review_case.execution_queue.threading.Thread", FakeThread)

    result = enqueue_with_optional_rq(
        ReviewCaseExecutionJob(
            review_id="frontend_review_rq_failure_fallback",
            payload_path=Path("payload.json"),
            mode="live",
        ),
        runner=runner,
        reserve_slot=lambda: True,
    )

    assert result.accepted is True
    assert result.backend == "in_process"
    assert result.reason == "rq_enqueue_failed"
    assert result.fallback_from == "rq_redis"
    assert result.metadata == {
        "backend": "rq_redis",
        "requested_backend": "rq",
        "queue_name": "pmri-review-case-execution",
        "redis_url_configured": True,
        "warnings": [],
        "fallback_reason": "rq_enqueue_failed",
        "fallback_metadata": {
            "queue_name": "pmri-review-case-execution",
            "redis_url_configured": True,
            "error_type": "ConnectionError",
        },
        "fallback_backend": "in_process",
    }
    assert calls == ["frontend_review_rq_failure_fallback:payload.json:live"]
