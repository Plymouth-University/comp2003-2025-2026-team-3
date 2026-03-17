"""API routes for profile management."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID

from ..database import get_db
from ..services.profile_service import ProfileService, TenantService, SpecialismService
from ..schemas.profile import (
    ProfileCreate, ProfileUpdate, ProfileResponse,
    TenantCreate, TenantResponse,
    SpecialismCreate, SpecialismResponse,
    ProfileIdentityCreate
)

router = APIRouter(prefix="/api/v1", tags=["profiles"])


# ============ Tenant Endpoints ============

@router.post("/tenants", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    tenant_data: TenantCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new tenant/organization."""
    service = TenantService(db)
    return await service.create_tenant(tenant_data)


@router.get("/tenants/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get tenant by ID."""
    service = TenantService(db)
    tenant = await service.get_tenant(tenant_id)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant {tenant_id} not found"
        )
    return tenant


@router.get("/tenants", response_model=List[TenantResponse])
async def list_tenants(db: AsyncSession = Depends(get_db)):
    """List all tenants."""
    service = TenantService(db)
    return await service.list_tenants()


# ============ Profile Endpoints ============

@router.post("/profiles", response_model=ProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_profile(
    profile_data: ProfileCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new user profile."""
    service = ProfileService(db)
    try:
        return await service.create_profile(profile_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/profiles/{profile_id}", response_model=ProfileResponse)
async def get_profile(
    profile_id: UUID,
    tenant_id: UUID = Query(..., description="Tenant ID for isolation"),
    db: AsyncSession = Depends(get_db)
):
    """Get profile by ID."""
    service = ProfileService(db)
    profile = await service.get_profile(profile_id, tenant_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile {profile_id} not found"
        )
    return profile


@router.get("/tenants/{tenant_id}/profiles", response_model=List[ProfileResponse])
async def list_profiles(
    tenant_id: UUID,
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """List all profiles for a tenant."""
    service = ProfileService(db)
    return await service.list_profiles(
        tenant_id=tenant_id,
        status=status_filter,
        limit=limit,
        offset=offset
    )


@router.patch("/profiles/{profile_id}", response_model=ProfileResponse)
async def update_profile(
    profile_id: UUID,
    profile_data: ProfileUpdate,
    tenant_id: UUID = Query(..., description="Tenant ID for isolation"),
    db: AsyncSession = Depends(get_db)
):
    """Update profile information."""
    service = ProfileService(db)
    profile = await service.update_profile(profile_id, tenant_id, profile_data)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile {profile_id} not found"
        )
    return profile


@router.post("/profiles/{profile_id}/deactivate", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_profile(
    profile_id: UUID,
    tenant_id: UUID = Query(..., description="Tenant ID for isolation"),
    reason: Optional[str] = Query(None, description="Reason for deactivation"),
    db: AsyncSession = Depends(get_db)
):
    """Deactivate a profile."""
    service = ProfileService(db)
    success = await service.deactivate_profile(profile_id, tenant_id, reason)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile {profile_id} not found"
        )


@router.get("/tenants/{tenant_id}/profiles/search", response_model=List[ProfileResponse])
async def search_profiles(
    tenant_id: UUID,
    q: str = Query(..., min_length=1, description="Search term"),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Search profiles by display name."""
    service = ProfileService(db)
    return await service.search_profiles(tenant_id, q, limit)


# ============ Identity Endpoints ============

@router.post("/profiles/identities", status_code=status.HTTP_201_CREATED)
async def link_identity(
    identity_data: ProfileIdentityCreate,
    db: AsyncSession = Depends(get_db)
):
    """Link an external identity provider to a profile."""
    service = ProfileService(db)
    success = await service.link_external_identity(identity_data)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to link identity"
        )
    return {"status": "success", "message": "Identity linked successfully"}


@router.get("/auth/profile", response_model=ProfileResponse)
async def get_profile_by_identity(
    idp_name: str = Query(..., description="Identity provider name"),
    idp_subject: str = Query(..., description="External subject/user ID"),
    db: AsyncSession = Depends(get_db)
):
    """Find profile by external identity (authentication endpoint)."""
    service = ProfileService(db)
    profile = await service.find_profile_by_identity(idp_name, idp_subject)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found for this identity"
        )
    return profile


# ============ Specialism Endpoints ============

@router.post("/specialisms", response_model=SpecialismResponse, status_code=status.HTTP_201_CREATED)
async def create_specialism(
    specialism_data: SpecialismCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new specialism/skill category."""
    service = SpecialismService(db)
    return await service.create_specialism(specialism_data)


@router.get("/tenants/{tenant_id}/specialisms", response_model=List[SpecialismResponse])
async def list_specialisms(
    tenant_id: UUID,
    active_only: bool = Query(True, description="Only return active specialisms"),
    db: AsyncSession = Depends(get_db)
):
    """List specialisms for a tenant."""
    service = SpecialismService(db)
    return await service.list_specialisms(tenant_id, active_only)


@router.post("/profiles/{profile_id}/specialisms/{specialism_id}", status_code=status.HTTP_201_CREATED)
async def assign_specialism(
    profile_id: UUID,
    specialism_id: UUID,
    tenant_id: UUID = Query(..., description="Tenant ID for isolation"),
    proficiency_level: Optional[str] = Query(None, description="Proficiency level"),
    assigned_by: Optional[UUID] = Query(None, description="Profile ID of assigner"),
    db: AsyncSession = Depends(get_db)
):
    """Assign a specialism to a profile."""
    service = SpecialismService(db)
    success = await service.assign_to_profile(
        tenant_id=tenant_id,
        profile_id=profile_id,
        specialism_id=specialism_id,
        proficiency_level=proficiency_level,
        assigned_by_profile_id=assigned_by
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to assign specialism"
        )
    return {"status": "success", "message": "Specialism assigned successfully"}


@router.get("/profiles/{profile_id}/specialisms")
async def get_profile_specialisms(
    profile_id: UUID,
    tenant_id: UUID = Query(..., description="Tenant ID for isolation"),
    db: AsyncSession = Depends(get_db)
):
    """Get all specialisms assigned to a profile."""
    service = SpecialismService(db)
    return await service.get_profile_specialisms(tenant_id, profile_id)
