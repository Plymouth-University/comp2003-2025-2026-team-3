"""Authentication routes for Microsoft Entra ID sign-in."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import (
    AuthenticatedSession,
    build_authorization_url,
    build_cookie_settings,
    create_session_token,
    create_state_token,
    exchange_code_for_identity,
    get_current_session,
)
from ..config import settings
from ..database import get_db
from ..services.profile_service import ProfileService

router = APIRouter(tags=["auth"])

STATE_COOKIE_NAME = "entra_auth_state"


@router.get("/auth/login")
async def login() -> RedirectResponse:
    """Start the Entra ID authorization-code flow."""
    state = create_state_token()
    response = RedirectResponse(
        build_authorization_url(state), status_code=status.HTTP_302_FOUND
    )
    response.set_cookie(STATE_COOKIE_NAME, state, **build_cookie_settings())
    return response


@router.get("/auth/callback")
async def auth_callback(
    request: Request,
    code: str = Query(...),
    state: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Handle the Entra redirect, resolve the profile, and create a backend session."""
    expected_state = request.cookies.get(STATE_COOKIE_NAME)
    if not expected_state or expected_state != state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Entra authentication state",
        )

    identity = exchange_code_for_identity(code)
    profile_service = ProfileService(db)
    try:
        profile = await profile_service.resolve_entra_profile(
            entra_tenant_id=identity.tid,
            object_id=identity.oid,
            display_name=identity.name,
        )
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc

    session_token = create_session_token(
        profile_id=str(profile.profile_id),
        tenant_id=str(profile.tenant_id),
        identity=identity,
    )

    redirect = RedirectResponse(
        settings.FRONTEND_URL, status_code=status.HTTP_302_FOUND
    )
    redirect.set_cookie(
        settings.SESSION_COOKIE_NAME,
        session_token,
        **build_cookie_settings(),
    )
    redirect.delete_cookie(STATE_COOKIE_NAME)
    return redirect


@router.get("/api/v1/auth/me")
async def get_authenticated_user(
    session: AuthenticatedSession = Depends(get_current_session),
    db: AsyncSession = Depends(get_db),
):
    """Return the current authenticated session and resolved profile."""
    profile_service = ProfileService(db)
    profile = await profile_service.get_profile(
        profile_id=UUID(session.profile_id),
        tenant_id=UUID(session.tenant_id),
    )
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session profile no longer exists",
        )

    return {"session": session.model_dump(), "profile": profile.model_dump(mode="json")}


@router.post("/api/v1/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout():
    """Clear the backend session cookie."""
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    response.delete_cookie(settings.SESSION_COOKIE_NAME)
    response.delete_cookie(STATE_COOKIE_NAME)
    return response
