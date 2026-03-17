"""Profile service layer - business logic for profile management."""
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from uuid import UUID

from ..config import settings
from ..repositories.profile_repository import (
    ProfileRepository, TenantRepository, IdentityRepository, SpecialismRepository
)
from ..schemas.profile import (
    ProfileCreate, ProfileUpdate, ProfileResponse,
    TenantCreate, TenantResponse,
    SpecialismCreate, SpecialismResponse,
    ProfileIdentityCreate
)
from ..models.profile import Profile, Tenant, Specialism


class ProfileService:
    """Business logic for profile management."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.profile_repo = ProfileRepository(db)
        self.tenant_repo = TenantRepository(db)
        self.identity_repo = IdentityRepository(db)
        self.specialism_repo = SpecialismRepository(db)
    
    async def create_profile(self, profile_data: ProfileCreate) -> ProfileResponse:
        """Create a new profile with display name and avatar."""
        # Verify tenant exists
        tenant = await self.tenant_repo.get_tenant_by_id(profile_data.tenant_id)
        if not tenant:
            raise ValueError(f"Tenant {profile_data.tenant_id} not found")
        
        # Create profile
        profile = await self.profile_repo.create_profile(
            tenant_id=profile_data.tenant_id,
            display_name=profile_data.display_name,
            status=profile_data.status,
            avatar_preset_id=profile_data.avatar_preset_id
        )
        
        return ProfileResponse.model_validate(profile)
    
    async def get_profile(self, profile_id: UUID, tenant_id: UUID) -> Optional[ProfileResponse]:
        """Get a profile by ID."""
        profile = await self.profile_repo.get_profile_by_id(profile_id, tenant_id)
        if not profile:
            return None
        return ProfileResponse.model_validate(profile)
    
    async def list_profiles(
        self,
        tenant_id: UUID,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[ProfileResponse]:
        """List profiles for a tenant with optional filters."""
        profiles = await self.profile_repo.get_profiles_by_tenant(
            tenant_id=tenant_id,
            status=status,
            limit=limit,
            offset=offset
        )
        return [ProfileResponse.model_validate(p) for p in profiles]
    
    async def update_profile(
        self,
        profile_id: UUID,
        tenant_id: UUID,
        profile_data: ProfileUpdate
    ) -> Optional[ProfileResponse]:
        """Update profile information."""
        # Update profile fields
        updates = profile_data.model_dump(exclude_unset=True)
        
        # Handle display name separately
        if "display_name" in updates:
            display_name = updates.pop("display_name")
            await self.profile_repo.update_display_name(profile_id, tenant_id, display_name)
        
        # Update remaining fields
        if updates:
            profile = await self.profile_repo.update_profile(profile_id, tenant_id, **updates)
            if not profile:
                return None
        
        # Return updated profile
        return await self.get_profile(profile_id, tenant_id)
    
    async def deactivate_profile(
        self,
        profile_id: UUID,
        tenant_id: UUID,
        reason: Optional[str] = None
    ) -> bool:
        """Deactivate a profile."""
        return await self.profile_repo.deactivate_profile(profile_id, tenant_id, reason)
    
    async def search_profiles(
        self,
        tenant_id: UUID,
        search_term: str,
        limit: int = 20
    ) -> List[ProfileResponse]:
        """Search profiles by display name."""
        profiles = await self.profile_repo.search_profiles_by_name(
            tenant_id=tenant_id,
            search_term=search_term,
            limit=limit
        )
        return [ProfileResponse.model_validate(p) for p in profiles]
    
    async def link_external_identity(
        self,
        identity_data: ProfileIdentityCreate
    ) -> bool:
        """Link an external identity provider to a profile."""
        try:
            await self.identity_repo.link_profile_identity(
                profile_id=identity_data.profile_id,
                tenant_id=identity_data.tenant_id,
                idp_id=identity_data.idp_id,
                idp_tenant_subject=identity_data.idp_tenant_subject
            )
            return True
        except Exception:
            return False
    
    async def find_profile_by_identity(
        self,
        idp_name: str,
        idp_tenant_subject: str
    ) -> Optional[ProfileResponse]:
        """Find a profile by external identity (for authentication)."""
        # Get identity provider
        idp = await self.identity_repo.get_identity_provider_by_name(idp_name)
        if not idp:
            return None
        
        # Find profile
        profile = await self.identity_repo.get_profile_by_identity(
            idp_id=idp.idp_id,
            idp_tenant_subject=idp_tenant_subject
        )
        
        if profile:
            # Update last login
            await self.identity_repo.update_last_login(idp.idp_id, idp_tenant_subject)
            return ProfileResponse.model_validate(profile)

        return None

    async def resolve_entra_profile(
        self,
        entra_tenant_id: str,
        object_id: str,
        display_name: str,
    ) -> ProfileResponse:
        """Resolve or provision a profile from Entra token claims."""
        tenant = await self.tenant_repo.get_tenant_by_name(settings.ENTRA_INTERNAL_TENANT_NAME)
        if not tenant:
            tenant = await self.tenant_repo.create_tenant(settings.ENTRA_INTERNAL_TENANT_NAME)

        idp = await self.identity_repo.get_or_create_identity_provider(settings.ENTRA_IDP_NAME)
        subject = f"{entra_tenant_id}:{object_id}"

        profile = await self.identity_repo.get_profile_by_identity(
            idp_id=idp.idp_id,
            idp_tenant_subject=subject,
        )

        if profile:
            await self.identity_repo.update_last_login(idp.idp_id, subject)
            if profile.status != "active":
                raise PermissionError("Profile is not active")

            if profile.display and profile.display.display_name != display_name:
                await self.profile_repo.update_display_name(
                    profile.profile_id,
                    tenant.tenant_id,
                    display_name,
                )

            refreshed = await self.profile_repo.get_profile_by_id(profile.profile_id, tenant.tenant_id)
            return ProfileResponse.model_validate(refreshed or profile)

        created_profile = await self.profile_repo.create_profile(
            tenant_id=tenant.tenant_id,
            display_name=display_name,
            status="active",
            avatar_preset_id=None,
        )
        await self.identity_repo.link_profile_identity(
            profile_id=created_profile.profile_id,
            tenant_id=tenant.tenant_id,
            idp_id=idp.idp_id,
            idp_tenant_subject=subject,
        )
        await self.identity_repo.update_last_login(idp.idp_id, subject)
        resolved = await self.profile_repo.get_profile_by_id(created_profile.profile_id, tenant.tenant_id)
        return ProfileResponse.model_validate(resolved or created_profile)


class TenantService:
    """Business logic for tenant management."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.tenant_repo = TenantRepository(db)
    
    async def create_tenant(self, tenant_data: TenantCreate) -> TenantResponse:
        """Create a new tenant."""
        tenant = await self.tenant_repo.create_tenant(tenant_data.tenant_name)
        return TenantResponse.model_validate(tenant)
    
    async def get_tenant(self, tenant_id: UUID) -> Optional[TenantResponse]:
        """Get a tenant by ID."""
        tenant = await self.tenant_repo.get_tenant_by_id(tenant_id)
        if not tenant:
            return None
        return TenantResponse.model_validate(tenant)
    
    async def list_tenants(self) -> List[TenantResponse]:
        """List all tenants."""
        tenants = await self.tenant_repo.get_all_tenants()
        return [TenantResponse.model_validate(t) for t in tenants]


class SpecialismService:
    """Business logic for specialisms/skills management."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.specialism_repo = SpecialismRepository(db)
    
    async def create_specialism(self, specialism_data: SpecialismCreate) -> SpecialismResponse:
        """Create a new specialism."""
        specialism = await self.specialism_repo.create_specialism(
            tenant_id=specialism_data.tenant_id,
            specialism_key=specialism_data.specialism_key,
            specialism_name=specialism_data.specialism_name,
            description=specialism_data.description
        )
        return SpecialismResponse.model_validate(specialism)
    
    async def list_specialisms(
        self,
        tenant_id: UUID,
        active_only: bool = True
    ) -> List[SpecialismResponse]:
        """List specialisms for a tenant."""
        specialisms = await self.specialism_repo.get_specialisms_by_tenant(
            tenant_id=tenant_id,
            active_only=active_only
        )
        return [SpecialismResponse.model_validate(s) for s in specialisms]
    
    async def assign_to_profile(
        self,
        tenant_id: UUID,
        profile_id: UUID,
        specialism_id: UUID,
        proficiency_level: Optional[str] = None,
        assigned_by_profile_id: Optional[UUID] = None
    ) -> bool:
        """Assign a specialism to a profile."""
        try:
            await self.specialism_repo.assign_specialism_to_profile(
                tenant_id=tenant_id,
                profile_id=profile_id,
                specialism_id=specialism_id,
                proficiency_level=proficiency_level,
                assigned_by_profile_id=assigned_by_profile_id
            )
            return True
        except Exception:
            return False
    
    async def get_profile_specialisms(
        self,
        tenant_id: UUID,
        profile_id: UUID
    ) -> List[dict]:
        """Get all specialisms assigned to a profile."""
        profile_specialisms = await self.specialism_repo.get_profile_specialisms(
            tenant_id=tenant_id,
            profile_id=profile_id
        )
        return [
            {
                "specialism": SpecialismResponse.model_validate(ps.specialism),
                "proficiency_level": ps.proficiency_level,
                "assigned_at": ps.assigned_at
            }
            for ps in profile_specialisms
        ]
