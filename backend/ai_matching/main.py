"""
FastAPI AI Matching Engine Application Entry Point.

Builds the FastAPI app, registers the /health and /match routers, and installs
exception handlers that return the project error envelope
{"code", "message", "field_errors", "correlation_id"} (ARCHITECTURE.md §5).

No CORS middleware: the engine is called server-to-server by Django only, never
by a browser (ARCHITECTURE.md §1, TD-09). Interactive docs are disabled.

Run locally (from backend/):
    uvicorn ai_matching.main:app --host 127.0.0.1 --port 8001

Author: Alok Tiwari (C7 — AI Matching and Data Intelligence Engineer)
Architecture: Component B (FastAPI AI Matching Engine)
Status: Week 2 implementation.

NOTE ON ARCHITECTURE & DECISIONS:
# PENDING DECISION: engine runtime/deployment arrangement (ARCHITECTURE.md §6.3).
# OPEN: Django -> engine authentication (see api/dependencies.py).
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from ai_matching.api.dependencies import resolve_correlation_id
from ai_matching.api.routes import health, matching
from ai_matching.core.constants import SERVICE_NAME
from ai_matching.core.exceptions import MatchingEngineException
from ai_matching.core.logging import get_logger

logger = get_logger("api")


def _correlation_id(request: Request) -> str:
    return resolve_correlation_id(request.headers.get("x-correlation-id"))


def _envelope(code: str, message: str, correlation_id: str, field_errors: dict | None = None) -> dict:
    return {"code": code, "message": message, "field_errors": field_errors or {}, "correlation_id": correlation_id}


def create_app() -> FastAPI:
    app = FastAPI(title=SERVICE_NAME, docs_url=None, redoc_url=None)
    app.include_router(health.router)
    app.include_router(matching.router)

    @app.exception_handler(RequestValidationError)
    async def _validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        # Report locations and messages only; never echo submitted values.
        field_errors: dict[str, list[str]] = {}
        for error in exc.errors():
            location = ".".join(str(part) for part in error.get("loc", ()) if part != "body") or "non_field_errors"
            field_errors.setdefault(location, []).append(str(error.get("msg", "Invalid value.")))
        return JSONResponse(
            status_code=422,
            content=_envelope(
                "validation_error", "The matching request failed validation.", _correlation_id(request), field_errors
            ),
        )

    @app.exception_handler(MatchingEngineException)
    async def _engine_error(request: Request, exc: MatchingEngineException) -> JSONResponse:
        correlation_id = _correlation_id(request)
        logger.warning("engine_error code=%s correlation_id=%s", exc.code, correlation_id)
        return JSONResponse(
            status_code=exc.http_status,
            content=_envelope(exc.code, exc.message, correlation_id, exc.field_errors),
        )

    @app.exception_handler(Exception)
    async def _unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        correlation_id = _correlation_id(request)
        logger.exception("unexpected_error correlation_id=%s", correlation_id)
        return JSONResponse(
            status_code=500,
            content=_envelope("internal_error", "An unexpected matching engine error occurred.", correlation_id),
        )

    return app


app = create_app()
