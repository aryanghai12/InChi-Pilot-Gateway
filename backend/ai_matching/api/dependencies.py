"""
Shared API Dependencies.

FastAPI dependency providers for settings, the embedding provider and the
request correlation ID.

Author: Alok Tiwari (C7 — AI Matching and Data Intelligence Engineer)
Architecture: Component B (FastAPI AI Matching Engine)
Status: Week 2 foundation.

NOTE ON ARCHITECTURE & DECISIONS:
# OPEN: service-to-service authentication between Django and this engine
# (THREAT_MODEL Boundary 3) is not designed yet. It needs Ajendra's review and
# must be added here as a dependency before the engine is reachable from any
# network other than the backend container.
"""

from __future__ import annotations

import re
import uuid

from fastapi import Header

from ai_matching.core.config import EngineSettings, get_settings
from ai_matching.providers.base import EmbeddingProvider
from ai_matching.providers.embedding_provider import get_embedding_provider

_SAFE_CORRELATION_ID = re.compile(r"^[A-Za-z0-9\-_.]{1,100}$")


def settings_dependency() -> EngineSettings:
    return get_settings()


def embedding_provider_dependency() -> EmbeddingProvider:
    return get_embedding_provider(get_settings())


def resolve_correlation_id(raw: str | None) -> str:
    """Accept the caller's X-Correlation-ID only if it is a safe token; otherwise generate one."""
    if raw and _SAFE_CORRELATION_ID.match(raw):
        return raw
    return str(uuid.uuid4())


def correlation_id_dependency(x_correlation_id: str | None = Header(default=None)) -> str:
    return resolve_correlation_id(x_correlation_id)
