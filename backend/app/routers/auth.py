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
from ..services.log_writer import LogContext, LogWriter
from ..services.profile_service import ProfileService

router = APIRouter(tags=["auth"])
log_writer = LogWriter()

STATE_COOKIE_NAME = "entra_auth_state"


@router.get("/auth/login")
async def login(request: Request) -> RedirectResponse:
    """Start the Entra ID authorization-code flow."""
    state = create_state_token()
    response = RedirectResponse(
        build_authorization_url(state), status_code=status.HTTP_302_FOUND
    )
    response.set_cookie(STATE_COOKIE_NAME, state, **build_cookie_settings())
    await log_writer.write_application_log(
        context=LogContext.from_request(
            request,
            logger_name=__name__,
        ),
        log_type="auth",
        subsystem="auth",
        action="login_started",
        level="info",
        message="Entra login flow started",
        outcome="redirected",
        status_code=status.HTTP_302_FOUND,
        details={"idp": settings.ENTRA_IDP_NAME},
    )
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
    context = LogContext.from_request(
        request,
        logger_name=__name__,
    )
    if not expected_state or expected_state != state:
        await log_writer.write_error_log(
            context=context,
            service_name="auth",
            severity="medium",
            message="Invalid Entra authentication state",
            error_type="InvalidAuthState",
            action="auth_callback",
            status_code=status.HTTP_400_BAD_REQUEST,
            details={"idp": settings.ENTRA_IDP_NAME},
        )
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
        await log_writer.write_error_log(
            context=context,
            service_name="auth",
            severity="medium",
            message="Entra profile resolution was denied",
            error=exc,
            action="profile_resolution_denied",
            status_code=status.HTTP_403_FORBIDDEN,
            details={"idp": settings.ENTRA_IDP_NAME, "entra_tenant_id": identity.tid},
        )
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
    await log_writer.write_application_log(
        context=LogContext.from_request(
            request,
            session=AuthenticatedSession(
                profile_id=str(profile.profile_id),
                tenant_id=str(profile.tenant_id),
                entra_tenant_id=identity.tid,
                object_id=identity.oid,
                display_name=identity.name,
                issuer=identity.iss,
                exp=0,
            ),
            logger_name=__name__,
        ),
        log_type="auth",
        subsystem="auth",
        action="login_completed",
        level="info",
        message="Entra login flow completed",
        outcome="success",
        status_code=status.HTTP_302_FOUND,
        details={"idp": settings.ENTRA_IDP_NAME, "entra_tenant_id": identity.tid},
    )
    return redirect


@router.get("/api/v1/auth/me")
async def get_authenticated_user(
    request: Request,
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
        await log_writer.write_error_log(
            context=LogContext.from_request(
                request,
                session=session,
                logger_name=__name__,
            ),
            service_name="auth",
            severity="medium",
            message="Session profile no longer exists",
            error_type="MissingSessionProfile",
            action="get_authenticated_user",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session profile no longer exists",
        )

    return {"session": session.model_dump(), "profile": profile.model_dump(mode="json")}


@router.post("/api/v1/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(request: Request):
    """Clear the backend session cookie."""
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    response.delete_cookie(settings.SESSION_COOKIE_NAME)
    response.delete_cookie(STATE_COOKIE_NAME)
    await log_writer.write_application_log(
        context=LogContext.from_request(
            request,
            logger_name=__name__,
        ),
        log_type="auth",
        subsystem="auth",
        action="logout",
        level="info",
        message="Session cookies cleared",
        outcome="success",
        status_code=status.HTTP_204_NO_CONTENT,
    )
    return response
