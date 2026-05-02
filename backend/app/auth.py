"""Authentication helpers for Entra ID and backend session cookies."""

from __future__ import annotations

import json
import secrets
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from typing import Any, Optional
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from fastapi import HTTPException, Request as FastAPIRequest, status
from jose import JWTError, jwt
from pydantic import BaseModel

from .config import settings


class AuthenticatedSession(BaseModel):
    """Authenticated browser session stored in a signed cookie."""

    profile_id: str
    tenant_id: str
    entra_tenant_id: str
    object_id: str
    display_name: str
    issuer: str
    exp: int


class EntraIdentity(BaseModel):
    """Minimal identity information extracted from a validated Entra ID token."""

    tid: str
    oid: str
    name: str
    iss: str


@lru_cache(maxsize=1)
def get_openid_configuration() -> dict[str, Any]:
    """Load and cache the tenant OpenID configuration."""
    if not settings.ENTRA_TENANT_ID:
        raise RuntimeError("ENTRA_TENANT_ID is not configured")

    url = (
        f"https://login.microsoftonline.com/{settings.ENTRA_TENANT_ID}"
        "/v2.0/.well-known/openid-configuration"
    )
    return _fetch_json(url)


@lru_cache(maxsize=1)
def get_jwks() -> dict[str, Any]:
    """Load and cache the JWKS document used to validate Entra tokens."""
    config = get_openid_configuration()
    jwks_uri = config["jwks_uri"]
    return _fetch_json(jwks_uri)


def build_authorization_url(state: str) -> str:
    """Build the Entra authorization request URL."""
    config = get_openid_configuration()
    query = urlencode(
        {
            "client_id": settings.ENTRA_CLIENT_ID,
            "response_type": "code",
            "redirect_uri": settings.ENTRA_REDIRECT_URI,
            "response_mode": "query",
            "scope": "openid profile",
            "state": state,
        }
    )
    return f"{config['authorization_endpoint']}?{query}"


def create_state_token() -> str:
    """Create a random CSRF state token for the OIDC round-trip."""
    return secrets.token_urlsafe(32)


def exchange_code_for_identity(code: str) -> EntraIdentity:
    """Exchange an authorization code for tokens and validate the Entra ID token."""
    config = get_openid_configuration()
    payload = urlencode(
        {
            "grant_type": "authorization_code",
            "client_id": settings.ENTRA_CLIENT_ID,
            "client_secret": settings.ENTRA_CLIENT_SECRET,
            "code": code,
            "redirect_uri": settings.ENTRA_REDIRECT_URI,
            "scope": "openid profile",
        }
    ).encode("utf-8")

    request = Request(
        config["token_endpoint"],
        data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )

    token_response = _fetch_json(request)
    id_token = token_response.get("id_token")
    if not id_token:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Entra token response did not include an ID token",
        )

    return validate_id_token(id_token)


def validate_id_token(id_token: str) -> EntraIdentity:
    """Validate the Entra ID token signature and required claims."""
    try:
        header = jwt.get_unverified_header(id_token)
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid ID token header",
        ) from exc

    key = _find_signing_key(header.get("kid"))
    config = get_openid_configuration()

    try:
        claims = jwt.decode(
            id_token,
            key,
            algorithms=["RS256"],
            audience=settings.ENTRA_CLIENT_ID,
            issuer=config["issuer"],
            options={"verify_at_hash": False},
        )
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Failed to validate Entra ID token",
        ) from exc

    display_name = (
        claims.get("name")
        or claims.get("preferred_username")
        or claims.get("upn")
        or "Unknown User"
    )

    tid = claims.get("tid")
    oid = claims.get("oid")
    iss = claims.get("iss")
    if not tid or not oid or not iss:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Entra ID token is missing required claims",
        )

    return EntraIdentity(tid=tid, oid=oid, name=display_name, iss=iss)


def create_session_token(
    *,
    profile_id: str,
    tenant_id: str,
    identity: EntraIdentity,
) -> str:
    """Create a signed backend session cookie."""
    now = datetime.now(timezone.utc)
    expires = now + timedelta(seconds=settings.SESSION_MAX_AGE_SECONDS)
    payload = {
        "profile_id": profile_id,
        "tenant_id": tenant_id,
        "entra_tenant_id": identity.tid,
        "object_id": identity.oid,
        "display_name": identity.name,
        "issuer": identity.iss,
        "iat": int(now.timestamp()),
        "exp": int(expires.timestamp()),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_session_token(token: str) -> AuthenticatedSession:
    """Decode and validate the signed backend session cookie."""
    try:
        claims = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session",
        ) from exc

    return AuthenticatedSession.model_validate(claims)


async def get_current_session(request: FastAPIRequest) -> AuthenticatedSession:
    """FastAPI dependency for routes that require an authenticated session."""
    token = request.cookies.get(settings.SESSION_COOKIE_NAME)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    return decode_session_token(token)


def build_cookie_settings() -> dict[str, Any]:
    """Cookie settings for local development."""
    return {
        "httponly": True,
        "samesite": "lax",
        "secure": False,
        "max_age": settings.SESSION_MAX_AGE_SECONDS,
    }


def _find_signing_key(kid: Optional[str]) -> dict[str, Any]:
    keys = get_jwks().get("keys", [])
    for key in keys:
        if key.get("kid") == kid:
            return key

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Unable to find matching Entra signing key",
    )


def _fetch_json(target: str | Request) -> dict[str, Any]:
    try:
        with urlopen(target, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except (URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to reach Microsoft Entra ID",
        ) from exc
