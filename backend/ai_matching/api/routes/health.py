"""
Health and Diagnostic Endpoints.

Defines GET /health for service liveness and readiness monitoring. Reports
only whether a model is configured, never the model path or any secret.

Author: Alok Tiwari (C7 — AI Matching and Data Intelligence Engineer)
Architecture: Component B (FastAPI AI Matching Engine)
Status: Week 2 implementation.
"""

from fastapi import APIRouter, Depends

from ai_matching.api.dependencies import settings_dependency
from ai_matching.core.config import EngineSettings
from ai_matching.core.constants import CONTRACT_VERSION, SERVICE_NAME

router = APIRouter(tags=["health"])


@router.get("/health")
def health(settings: EngineSettings = Depends(settings_dependency)) -> dict:
    return {
        "status": "ok",
        "service": SERVICE_NAME,
        "contract_version": CONTRACT_VERSION,
        "embedding_provider": settings.embedding_provider,
        "embedding_model_configured": settings.embedding_model_configured,
    }
