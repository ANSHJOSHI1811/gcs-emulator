"""
Auth Bypass Middleware
======================
Mode: BYPASS (STIMULATOR_AUTH_MODE=bypass)

Accepts ALL requests — never blocks anything.
Extracts caller identity from request headers for logging/audit only.

Identity resolution priority:
  1. Authorization: Bearer <token>  → decoded to extract email
  2. X-Stimulator-Identity: user:ansh@example.com  → used directly
  3. No header  → identity = "anonymous@stimulator"

Adds to every response:
  X-Stimulator-Auth-Identity: <resolved identity>
  X-Stimulator-Auth-Mode: bypass
"""

import base64
import json
import logging
import os
from datetime import datetime

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger("stimulator.auth")

# Paths that skip auth processing entirely
_BYPASS_PATHS = {
    "/health",
    "/",
    "/docs",
    "/openapi.json",
    "/redoc",
}


def _extract_email_from_bearer(token: str) -> str:
    """
    Best-effort extraction of email from a Bearer token.
    Handles both real GCP tokens (JWT format) and simulated tokens.
    Never raises — returns a fallback string on any failure.
    """
    try:
        # JWT format: header.payload.signature
        parts = token.split(".")
        if len(parts) == 3:
            # Add padding if needed for base64 decode
            payload = parts[1]
            payload += "=" * (4 - len(payload) % 4)
            decoded = json.loads(base64.urlsafe_b64decode(payload).decode("utf-8"))
            # Try common JWT email fields
            for field in ("email", "sub", "user_id"):
                if field in decoded:
                    return decoded[field]

        # Non-JWT Bearer (e.g., opaque token) — return a generic identity
        return f"bearer-user@stimulator"

    except Exception:
        return "unknown-token@stimulator"


def _resolve_identity(request: Request) -> tuple[str, str]:
    """
    Resolve caller identity from request headers.

    Returns:
        (identity: str, auth_method: str)
    """
    # Priority 1: Authorization: Bearer <token>
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header.removeprefix("Bearer ").strip()
        identity = _extract_email_from_bearer(token)
        return identity, "bearer"

    # Priority 2: X-Stimulator-Identity: user:ansh@example.com
    sim_identity = request.headers.get("X-Stimulator-Identity", "")
    if sim_identity:
        # Strip the "user:" / "serviceAccount:" prefix if present
        identity = sim_identity.split(":", 1)[-1] if ":" in sim_identity else sim_identity
        return identity, "header"

    # Priority 3: No identity provided
    return "anonymous@stimulator", "anonymous"


class AuthBypassMiddleware(BaseHTTPMiddleware):
    """
    Bypass auth middleware — all requests are allowed through.
    Logs identity and attaches it to request.state for downstream use.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip processing for health/docs paths
        if request.url.path in _BYPASS_PATHS:
            response = await call_next(request)
            return response

        # Resolve identity
        identity, auth_method = _resolve_identity(request)

        # Attach to request state so any route can access it
        request.state.user = identity
        request.state.auth_method = auth_method
        request.state.auth_mode = "bypass"

        # Log request with identity
        logger.info(
            "[AUTH] %s %s — identity=%s (%s)",
            request.method,
            request.url.path,
            identity,
            auth_method,
        )

        # Always call the next handler — NEVER block in bypass mode
        response = await call_next(request)

        # Add informational headers to every response
        response.headers["X-Stimulator-Auth-Identity"] = identity
        response.headers["X-Stimulator-Auth-Mode"] = "bypass"

        return response
