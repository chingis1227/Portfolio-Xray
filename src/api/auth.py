from __future__ import annotations

import hashlib
import hmac
import os
import time
from dataclasses import dataclass

from fastapi import Header, HTTPException, status


@dataclass(frozen=True)
class InternalAuthContext:
    """Trusted identity forwarded by the Next.js server, never by the browser."""

    user_id: str


def _env_value(name: str) -> str | None:
    value = os.getenv(name)
    return value.strip() if isinstance(value, str) and value.strip() else None


def _is_production() -> bool:
    return (_env_value("NODE_ENV") or _env_value("ENVIRONMENT") or "").lower() == "production"


def _dev_bypass_enabled() -> bool:
    return _env_value("PMRI_FASTAPI_AUTH_MODE") == "dev_bypass" and not _is_production()


def _secret() -> str | None:
    return _env_value("PMRI_FASTAPI_INTERNAL_SECRET") or _env_value("PMRI_INTERNAL_AUTH_SECRET")


def _expected_signature(user_id: str, timestamp: str, secret: str) -> str:
    return hmac.new(
        secret.encode("utf-8"),
        f"{user_id}.{timestamp}".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def require_internal_auth(
    x_pmri_user_id: str | None = Header(default=None, alias="X-PMRI-User-Id"),
    x_pmri_auth_timestamp: str | None = Header(default=None, alias="X-PMRI-Auth-Timestamp"),
    x_pmri_internal_signature: str | None = Header(default=None, alias="X-PMRI-Internal-Signature"),
) -> InternalAuthContext:
    """Require a short-lived signed internal auth context from Next.js."""

    if _dev_bypass_enabled():
        return InternalAuthContext(user_id=_env_value("PMRI_FASTAPI_DEV_USER_ID") or "local-dev-user")
    secret = _secret()
    if not secret:
        if not _is_production():
            return InternalAuthContext(user_id=_env_value("PMRI_FASTAPI_DEV_USER_ID") or "local-dev-user")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing trusted internal auth context.")
    if not x_pmri_user_id or not x_pmri_auth_timestamp or not x_pmri_internal_signature:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing trusted internal auth context.")
    user_id = x_pmri_user_id.strip()
    timestamp = x_pmri_auth_timestamp.strip()
    signature = x_pmri_internal_signature.strip().lower()
    try:
        timestamp_ms = int(timestamp)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid trusted internal auth context.") from exc
    if abs(int(time.time() * 1000) - timestamp_ms) > 5 * 60 * 1000:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Expired trusted internal auth context.")
    expected = _expected_signature(user_id, timestamp, secret)
    if not hmac.compare_digest(signature, expected):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid trusted internal auth context.")
    return InternalAuthContext(user_id=user_id)
