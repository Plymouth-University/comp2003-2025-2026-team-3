"""API routes for profile management."""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from types import SimpleNamespace
from typing import List, Optional
from uuid import UUID

from ..auth import AuthenticatedSession, get_current_session
from ..database import get_db
from ..services.log_writer import LogContext, LogWriter
from ..services.profile_service import ProfileService, TenantService, SpecialismService
from ..schemas.profile import (
    ProfileCreate,
    ProfileUpdate,
    ProfileResponse,
    TenantCreate,
    TenantResponse,
    SpecialismCreate,
    SpecialismResponse,
    ProfileIdentityCreate,
    AuthenticatedProfileSpecialismsUpdateRequest,
    ProfileSpecialismAssignmentItem,
)

router = APIRouter(prefix="/api/v1", tags=["profiles"])
log_writer = LogWriter()


def _log_context(
    request: Request,
    *,
    tenant_id: UUID | None = None,
    profile_id: UUID | None = None,
) -> LogContext:
    return LogContext.from_request(
        request,
        session=SimpleNamespace(tenant_id=tenant_id, profile_id=profile_id),
        logger_name=__name__,
    )


async def _write_profile_event(
    *,
    context: LogContext,
    action: str,
    message: str,
    entity_type: str | None = None,
    entity_id: str | None = None,
    details: dict | None = None,
) -> None:
    await log_writer.write_application_log(
        context=context,
        log_type="profile_management",
        subsystem="profiles",
        action=action,
        level="info",
        message=message,
        outcome="success",
        entity_type=entity_type,
        entity_id=entity_id,
        details=details,
    )


# ============ Tenant Endpoints ============


@router.post(
    "/tenants", response_model=TenantResponse, status_code=status.HTTP_201_CREATED
)
async def create_tenant(
    request: Request,
    tenant_data: TenantCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new tenant/organization."""
    service = TenantService(db)
    tenant = await service.create_tenant(tenant_data)
    await _write_profile_event(
        context=_log_context(request, tenant_id=tenant.tenant_id),
        action="tenant_created",
        message="Tenant created",
        entity_type="tenant",
        entity_id=str(tenant.tenant_id),
    )
    return tenant


@router.get("/tenants/{tenant_id}", response_model=TenantResponse)
async def get_tenant(tenant_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get tenant by ID."""
    service = TenantService(db)
    tenant = await service.get_tenant(tenant_id)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant {tenant_id} not found",
        )
    return tenant


@router.get("/tenants", response_model=List[TenantResponse])
async def list_tenants(db: AsyncSession = Depends(get_db)):
    """List all tenants."""
    service = TenantService(db)
    return await service.list_tenants()


# ============ Profile Endpoints ============


@router.post(
    "/profiles", response_model=ProfileResponse, status_code=status.HTTP_201_CREATED
)
async def create_profile(
    request: Request,
    profile_data: ProfileCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new user profile."""
    service = ProfileService(db)
    try:
        profile = await service.create_profile(profile_data)
    except ValueError as e:
        await log_writer.write_error_log(
            context=_log_context(request, tenant_id=profile_data.tenant_id),
            service_name="profiles",
            severity="medium",
            message="Failed to create profile",
            error=e,
            action="profile_create",
            status_code=status.HTTP_400_BAD_REQUEST,
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    await _write_profile_event(
        context=_log_context(
            request,
            tenant_id=profile.tenant_id,
            profile_id=profile.profile_id,
        ),
        action="profile_created",
        message="Profile created",
        entity_type="profile",
        entity_id=str(profile.profile_id),
    )
    return profile


@router.get("/profiles/{profile_id}", response_model=ProfileResponse)
async def get_profile(
    profile_id: UUID,
    tenant_id: UUID = Query(..., description="Tenant ID for isolation"),
    db: AsyncSession = Depends(get_db),
):
    """Get profile by ID."""
    service = ProfileService(db)
    profile = await service.get_profile(profile_id, tenant_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile {profile_id} not found",
        )
    return profile


@router.get("/tenants/{tenant_id}/profiles", response_model=List[ProfileResponse])
async def list_profiles(
    tenant_id: UUID,
    status_filter: Optional[str] = Query(
        None, alias="status", description="Filter by status"
    ),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List all profiles for a tenant."""
    service = ProfileService(db)
    return await service.list_profiles(
        tenant_id=tenant_id, status=status_filter, limit=limit, offset=offset
    )


@router.patch("/profiles/{profile_id}", response_model=ProfileResponse)
async def update_profile(
    request: Request,
    profile_id: UUID,
    profile_data: ProfileUpdate,
    tenant_id: UUID = Query(..., description="Tenant ID for isolation"),
    db: AsyncSession = Depends(get_db),
):
    """Update profile information."""
    service = ProfileService(db)
    profile = await service.update_profile(profile_id, tenant_id, profile_data)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile {profile_id} not found",
        )
    await _write_profile_event(
        context=_log_context(request, tenant_id=tenant_id, profile_id=profile_id),
        action="profile_updated",
        message="Profile updated",
        entity_type="profile",
        entity_id=str(profile_id),
        details={"updated_fields": sorted(profile_data.model_fields_set)},
    )
    return profile


@router.post(
    "/profiles/{profile_id}/deactivate", status_code=status.HTTP_204_NO_CONTENT
)
async def deactivate_profile(
    request: Request,
    profile_id: UUID,
    tenant_id: UUID = Query(..., description="Tenant ID for isolation"),
    reason: Optional[str] = Query(None, description="Reason for deactivation"),
    db: AsyncSession = Depends(get_db),
):
    """Deactivate a profile."""
    service = ProfileService(db)
    success = await service.deactivate_profile(profile_id, tenant_id, reason)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile {profile_id} not found",
        )
    await _write_profile_event(
        context=_log_context(request, tenant_id=tenant_id, profile_id=profile_id),
        action="profile_deactivated",
        message="Profile deactivated",
        entity_type="profile",
        entity_id=str(profile_id),
        details={"reason_provided": bool(reason)},
    )


@router.get(
    "/tenants/{tenant_id}/profiles/search", response_model=List[ProfileResponse]
)
async def search_profiles(
    tenant_id: UUID,
    q: str = Query(..., min_length=1, description="Search term"),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Search profiles by display name."""
    service = ProfileService(db)
    return await service.search_profiles(tenant_id, q, limit)


# ============ Identity Endpoints ============


@router.post("/profiles/identities", status_code=status.HTTP_201_CREATED)
async def link_identity(
    request: Request,
    identity_data: ProfileIdentityCreate,
    db: AsyncSession = Depends(get_db),
):
    """Link an external identity provider to a profile."""
    service = ProfileService(db)
    success = await service.link_external_identity(identity_data)
    if not success:
        await log_writer.write_error_log(
            context=_log_context(
                request,
                tenant_id=identity_data.tenant_id,
                profile_id=identity_data.profile_id,
            ),
            service_name="profiles",
            severity="medium",
            message="Failed to link external profile identity",
            error_type="IdentityLinkFailed",
            action="identity_link",
            status_code=status.HTTP_400_BAD_REQUEST,
            details={"idp_id": identity_data.idp_id},
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to link identity"
        )
    await _write_profile_event(
        context=_log_context(
            request,
            tenant_id=identity_data.tenant_id,
            profile_id=identity_data.profile_id,
        ),
        action="identity_linked",
        message="External profile identity linked",
        entity_type="profile",
        entity_id=str(identity_data.profile_id),
        details={"idp_id": identity_data.idp_id},
    )
    return {"status": "success", "message": "Identity linked successfully"}


@router.get("/auth/profile", response_model=ProfileResponse)
async def get_profile_by_identity(
    idp_name: str = Query(..., description="Identity provider name"),
    idp_subject: str = Query(..., description="External subject/user ID"),
    db: AsyncSession = Depends(get_db),
):
    """Find profile by external identity (authentication endpoint)."""
    service = ProfileService(db)
    profile = await service.find_profile_by_identity(idp_name, idp_subject)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found for this identity",
        )
    return profile


# ============ Specialism Endpoints ============


@router.post(
    "/specialisms",
    response_model=SpecialismResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_specialism(
    request: Request,
    specialism_data: SpecialismCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new specialism/skill category."""
    service = SpecialismService(db)
    specialism = await service.create_specialism(specialism_data)
    await _write_profile_event(
        context=_log_context(request, tenant_id=specialism.tenant_id),
        action="specialism_created",
        message="Specialism created",
        entity_type="specialism",
        entity_id=str(specialism.specialism_id),
        details={"specialism_key": specialism.specialism_key},
    )
    return specialism


@router.get("/tenants/{tenant_id}/specialisms", response_model=List[SpecialismResponse])
async def list_specialisms(
    tenant_id: UUID,
    active_only: bool = Query(True, description="Only return active specialisms"),
    db: AsyncSession = Depends(get_db),
):
    """List specialisms for a tenant."""
    service = SpecialismService(db)
    return await service.list_specialisms(tenant_id, active_only)


@router.post(
    "/profiles/{profile_id}/specialisms/{specialism_id}",
    status_code=status.HTTP_201_CREATED,
)
async def assign_specialism(
    request: Request,
    profile_id: UUID,
    specialism_id: UUID,
    tenant_id: UUID = Query(..., description="Tenant ID for isolation"),
    proficiency_level: Optional[str] = Query(None, description="Proficiency level"),
    assigned_by: Optional[UUID] = Query(None, description="Profile ID of assigner"),
    db: AsyncSession = Depends(get_db),
):
    """Assign a specialism to a profile."""
    service = SpecialismService(db)
    success = await service.assign_to_profile(
        tenant_id=tenant_id,
        profile_id=profile_id,
        specialism_id=specialism_id,
        proficiency_level=proficiency_level,
        assigned_by_profile_id=assigned_by,
    )
    if not success:
        await log_writer.write_error_log(
            context=_log_context(request, tenant_id=tenant_id, profile_id=profile_id),
            service_name="profiles",
            severity="medium",
            message="Failed to assign specialism",
            error_type="SpecialismAssignmentFailed",
            action="specialism_assign",
            status_code=status.HTTP_400_BAD_REQUEST,
            details={"specialism_id": str(specialism_id)},
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to assign specialism",
        )
    await _write_profile_event(
        context=_log_context(request, tenant_id=tenant_id, profile_id=profile_id),
        action="specialism_assigned",
        message="Specialism assigned to profile",
        entity_type="profile",
        entity_id=str(profile_id),
        details={
            "specialism_id": str(specialism_id),
            "assigned_by": str(assigned_by) if assigned_by else None,
            "proficiency_level": proficiency_level,
        },
    )
    return {"status": "success", "message": "Specialism assigned successfully"}


@router.get("/profiles/{profile_id}/specialisms")
async def get_profile_specialisms(
    profile_id: UUID,
    tenant_id: UUID = Query(..., description="Tenant ID for isolation"),
    db: AsyncSession = Depends(get_db),
):
    """Get all specialisms assigned to a profile."""
    service = SpecialismService(db)
    return await service.get_profile_specialisms(tenant_id, profile_id)


@router.get(
    "/auth/profile/specialisms", response_model=List[ProfileSpecialismAssignmentItem]
)
async def get_authenticated_profile_specialisms(
    session: AuthenticatedSession = Depends(get_current_session),
    db: AsyncSession = Depends(get_db),
):
    """Get the authenticated user's assigned specialisms."""
    service = SpecialismService(db)
    return await service.get_profile_specialisms(
        tenant_id=UUID(session.tenant_id),
        profile_id=UUID(session.profile_id),
    )


@router.put(
    "/auth/profile/specialisms", response_model=List[ProfileSpecialismAssignmentItem]
)
async def replace_authenticated_profile_specialisms(
    request_http: Request,
    request: AuthenticatedProfileSpecialismsUpdateRequest,
    session: AuthenticatedSession = Depends(get_current_session),
    db: AsyncSession = Depends(get_db),
):
    """Replace the authenticated user's specialisms using AI category keys."""
    service = SpecialismService(db)
    try:
        specialisms = await service.replace_profile_specialisms_from_category_keys(
            tenant_id=UUID(session.tenant_id),
            profile_id=UUID(session.profile_id),
            category_keys=request.specialism_keys,
            assigned_by_profile_id=UUID(session.profile_id),
        )
    except ValueError as exc:
        await log_writer.write_error_log(
            context=LogContext.from_request(
                request_http,
                session=session,
                logger_name=__name__,
            ),
            service_name="profiles",
            severity="medium",
            message="Failed to replace authenticated profile specialisms",
            error=exc,
            action="authenticated_specialisms_replace",
            status_code=status.HTTP_400_BAD_REQUEST,
            details={"specialism_count": len(request.specialism_keys)},
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    await _write_profile_event(
        context=LogContext.from_request(
            request_http,
            session=session,
            logger_name=__name__,
        ),
        action="authenticated_specialisms_replaced",
        message="Authenticated profile specialisms replaced",
        entity_type="profile",
        entity_id=session.profile_id,
        details={"specialism_count": len(request.specialism_keys)},
    )
    return specialisms
