import json
import logging
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from redis import Redis
from sqlalchemy import text

from app.api import (
    account_access,
    analytics,
    applications,
    auth,
    feedback,
    jobs,
    matching,
    reports,
    resumes,
    studio,
)
from app.core.config import settings
from app.db.session import engine


class RequestTooLarge(Exception):
    pass


class BodyLimitMiddleware:
    """Bound streamed/chunked requests too, before multipart spooling can exhaust disk."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        consumed = 0

        async def limited_receive():
            nonlocal consumed
            message = await receive()
            if message["type"] == "http.request":
                consumed += len(message.get("body", b""))
                if consumed > settings().max_upload_bytes + 65536:
                    raise RequestTooLarge()
            return message

        try:
            await self.app(scope, limited_receive, send)
        except RequestTooLarge:
            await JSONResponse({"detail": "Request too large"}, status_code=413)(scope, receive, send)


logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("talentlens")
app = FastAPI(
    title="TalentLens AI",
    version="0.1.0",
    description="Private, consent-based qualification analysis. Scores are heuristic, never hiring decisions.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings().app_origin],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Content-Type", "X-CSRF-Token"],
)
app.add_middleware(BodyLimitMiddleware)


@app.middleware("http")
async def security_and_logging(request: Request, call_next):
    started = time.monotonic()
    request_id = str(uuid.uuid4())
    if (
        request.method not in {"GET", "HEAD", "OPTIONS"}
        and request.headers.get("origin") != settings().app_origin
    ):
        return JSONResponse({"detail": "Untrusted request origin"}, status_code=403)
    length = request.headers.get("content-length")
    if length and (not length.isdigit() or int(length) > settings().max_upload_bytes + 65536):
        return JSONResponse({"detail": "Request too large"}, status_code=413)
    response = await call_next(request)
    response.headers.update(
        {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "Referrer-Policy": "no-referrer",
            "Cache-Control": "no-store",
            "X-Request-ID": request_id,
        }
    )
    logger.info(
        json.dumps(
            {
                "event": "http_request",
                "request_id": request_id,
                "method": request.method,
                "status": response.status_code,
                "duration_ms": round((time.monotonic() - started) * 1000),
            }
        )
    )
    return response


@app.exception_handler(Exception)
async def internal_error(request: Request, exc: Exception):
    logger.error(json.dumps({"event": "request_failed", "error_type": type(exc).__name__}))
    return JSONResponse({"detail": "Service temporarily unavailable. Please retry."}, status_code=500)


for router in [
    auth.router,
    account_access.router,
    studio.router,
    feedback.router,
    resumes.router,
    jobs.router,
    applications.router,
    matching.router,
    reports.router,
    analytics.router,
]:
    app.include_router(router, prefix="/api/v1")


@app.get("/api/v1/health")
def health():
    return {"status": "ok", "service": "talentlens-api", "demo_mode": settings().demo_mode}


@app.get("/api/v1/ready")
def ready():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1 FROM users LIMIT 1"))
            conn.execute(text("SELECT '[1,2,3]'::vector"))
        client = Redis.from_url(settings().redis_url, socket_connect_timeout=2, socket_timeout=2)
        client.ping()
        client.close()
        return {"status": "ready", "database": "ok", "redis": "ok", "models": "loaded on demand by worker"}
    except Exception:
        return JSONResponse(
            {"status": "not_ready", "detail": "Database migrations, pgvector or Redis unavailable"},
            status_code=503,
        )
