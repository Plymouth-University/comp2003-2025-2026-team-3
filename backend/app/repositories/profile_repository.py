"""Repository layer for profile data access."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, update, delete, func
from sqlalchemy.orm import selectinload
from typing import Optional, List
from uuid import UUID
from datetime import datetime

from ..models.profile import (
    Profile, ProfileDisplay, ProfileIdentity, ProfileAvatar,
    Tenant, IdentityProvider, Specialism, ProfileSpecialism, AvatarPreset
)


class ProfileRepository:
    """Data access layer for profiles."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_profile(
        self,
        tenant_id: UUID,
        display_name: str,
        status: str = "active",
        avatar_preset_id: Optional[UUID] = None
    ) -> Profile:
        """Create a new profile with display name and optional avatar."""
        # Create profile
        profile = Profile(tenant_id=tenant_id, status=status)
        self.db.add(profile)
        await self.db.flush()
        
        # Create display name
        display = ProfileDisplay(
            profile_id=profile.profile_id,
            tenant_id=tenant_id,
            display_name=display_name,
            display_name_normalized=display_name.lower()
        )
        self.db.add(display)
        
        # Create avatar
        avatar = ProfileAvatar(
            profile_id=profile.profile_id,
            tenant_id=tenant_id,
            avatar_source="preset" if avatar_preset_id else "preset",
            avatar_preset_id=avatar_preset_id
        )
        self.db.add(avatar)
        
        await self.db.commit()
        await self.db.refresh(profile)
        return profile
    
    async def get_profile_by_id(self, profile_id: UUID, tenant_id: UUID) -> Optional[Profile]:
        """Get profile by ID with all relationships loaded."""
        query = (
            select(Profile)
            .options(
                selectinload(Profile.display),
                selectinload(Profile.avatar),
                selectinload(Profile.identities),
                selectinload(Profile.specialisms)
            )
            .where(and_(Profile.profile_id == profile_id, Profile.tenant_id == tenant_id))
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_profiles_by_tenant(
        self,
        tenant_id: UUID,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Profile]:
        """Get all profiles for a tenant with optional filters."""
        query = (
            select(Profile)
            .options(
                selectinload(Profile.display),
                selectinload(Profile.avatar)
            )
            .where(Profile.tenant_id == tenant_id)
        )
        
        if status:
            query = query.where(Profile.status == status)
        
        query = query.limit(limit).offset(offset)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_profiles_by_tenant_with_specialisms(
        self,
        tenant_id: UUID,
        status: Optional[str] = None,
    ) -> List[Profile]:
        """Get profiles for a tenant with display and specialism relationships loaded."""
        query = (
            select(Profile)
            .options(
                selectinload(Profile.display),
                selectinload(Profile.specialisms).selectinload(ProfileSpecialism.specialism),
            )
            .where(Profile.tenant_id == tenant_id)
        )

        if status:
            query = query.where(Profile.status == status)

        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def update_profile(
        self,
        profile_id: UUID,
        tenant_id: UUID,
        **updates
    ) -> Optional[Profile]:
        """Update profile fields."""
        profile = await self.get_profile_by_id(profile_id, tenant_id)
        if not profile:
            return None
        
        for key, value in updates.items():
            if hasattr(profile, key):
                setattr(profile, key, value)
        
        await self.db.commit()
        await self.db.refresh(profile)
        return profile
    
    async def update_display_name(
        self,
        profile_id: UUID,
        tenant_id: UUID,
        display_name: str
    ) -> bool:
        """Update profile display name."""
        stmt = (
            update(ProfileDisplay)
            .where(and_(
                ProfileDisplay.profile_id == profile_id,
                ProfileDisplay.tenant_id == tenant_id
            ))
            .values(
                display_name=display_name,
                display_name_normalized=display_name.lower(),
                updated_at=datetime.utcnow()
            )
        )
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.rowcount > 0
    
    async def deactivate_profile(
        self,
        profile_id: UUID,
        tenant_id: UUID,
        reason: Optional[str] = None
    ) -> bool:
        """Deactivate a profile."""
        stmt = (
            update(Profile)
            .where(and_(
                Profile.profile_id == profile_id,
                Profile.tenant_id == tenant_id
            ))
            .values(
                status="deactivated",
                deactivated_at=datetime.utcnow(),
                deactivated_reason=reason
            )
        )
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.rowcount > 0
    
    async def search_profiles_by_name(
        self,
        tenant_id: UUID,
        search_term: str,
        limit: int = 20
    ) -> List[Profile]:
        """Search profiles by display name."""
        normalized_term = search_term.lower()
        query = (
            select(Profile)
            .join(ProfileDisplay)
            .options(selectinload(Profile.display))
            .where(and_(
                Profile.tenant_id == tenant_id,
                ProfileDisplay.display_name_normalized.contains(normalized_term)
            ))
            .limit(limit)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_profiles_by_display_names(
        self,
        tenant_id: UUID,
        display_names: List[str],
    ) -> List[Profile]:
        """Resolve profiles by exact normalized display names for a tenant."""
        normalized_names = [name.strip().lower() for name in display_names if name and name.strip()]
        if not normalized_names:
            return []

        query = (
            select(Profile)
            .join(ProfileDisplay)
            .options(selectinload(Profile.display))
            .where(
                and_(
                    Profile.tenant_id == tenant_id,
                    ProfileDisplay.display_name_normalized.in_(normalized_names),
                )
            )
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())


class TenantRepository:
    """Data access layer for tenants."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_tenant(self, tenant_name: str) -> Tenant:
        """Create a new tenant."""
        tenant = Tenant(tenant_name=tenant_name)
        self.db.add(tenant)
        await self.db.commit()
        await self.db.refresh(tenant)
        return tenant
    
    async def get_tenant_by_id(self, tenant_id: UUID) -> Optional[Tenant]:
        """Get tenant by ID."""
        query = select(Tenant).where(Tenant.tenant_id == tenant_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_tenant_by_name(self, tenant_name: str) -> Optional[Tenant]:
        """Get tenant by display name."""
        query = select(Tenant).where(Tenant.tenant_name == tenant_name)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_all_tenants(self) -> List[Tenant]:
        """Get all tenants."""
        query = select(Tenant)
        result = await self.db.execute(query)
        return list(result.scalars().all())


class IdentityRepository:
    """Data access layer for identity providers and profile identities."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_identity_provider(self, idp_name: str) -> IdentityProvider:
        """Create a new identity provider."""
        idp = IdentityProvider(idp_name=idp_name)
        self.db.add(idp)
        await self.db.commit()
        await self.db.refresh(idp)
        return idp
    
    async def get_identity_provider_by_name(self, idp_name: str) -> Optional[IdentityProvider]:
        """Get identity provider by name."""
        query = select(IdentityProvider).where(IdentityProvider.idp_name == idp_name)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_or_create_identity_provider(self, idp_name: str) -> IdentityProvider:
        """Get an identity provider, creating it when needed."""
        existing = await self.get_identity_provider_by_name(idp_name)
        if existing:
            return existing
        return await self.create_identity_provider(idp_name)
    
    async def link_profile_identity(
        self,
        profile_id: UUID,
        tenant_id: UUID,
        idp_id: int,
        idp_tenant_subject: str
    ) -> ProfileIdentity:
        """Link a profile to an external identity."""
        identity = ProfileIdentity(
            profile_id=profile_id,
            tenant_id=tenant_id,
            idp_id=idp_id,
            idp_tenant_subject=idp_tenant_subject
        )
        self.db.add(identity)
        await self.db.commit()
        await self.db.refresh(identity)
        return identity
    
    async def get_profile_by_identity(
        self,
        idp_id: int,
        idp_tenant_subject: str
    ) -> Optional[Profile]:
        """Find profile by external identity."""
        query = (
            select(Profile)
            .join(ProfileIdentity)
            .options(
                selectinload(Profile.display),
                selectinload(Profile.avatar),
                selectinload(Profile.identities),
            )
            .where(and_(
                ProfileIdentity.idp_id == idp_id,
                ProfileIdentity.idp_tenant_subject == idp_tenant_subject
            ))
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def update_last_login(
        self,
        idp_id: int,
        idp_tenant_subject: str
    ) -> bool:
        """Update last login timestamp for an identity."""
        stmt = (
            update(ProfileIdentity)
            .where(and_(
                ProfileIdentity.idp_id == idp_id,
                ProfileIdentity.idp_tenant_subject == idp_tenant_subject
            ))
            .values(last_login_at=datetime.utcnow())
        )
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.rowcount > 0


class SpecialismRepository:
    """Data access layer for specialisms."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_specialism(
        self,
        tenant_id: UUID,
        specialism_key: str,
        specialism_name: str,
        description: Optional[str] = None,
        commit: bool = True,
    ) -> Specialism:
        """Create a new specialism."""
        specialism = Specialism(
            tenant_id=tenant_id,
            specialism_key=specialism_key,
            specialism_name=specialism_name,
            description=description
        )
        self.db.add(specialism)
        await self.db.flush()
        if commit:
            await self.db.commit()
            await self.db.refresh(specialism)
        return specialism
    
    async def get_specialisms_by_tenant(
        self,
        tenant_id: UUID,
        active_only: bool = True
    ) -> List[Specialism]:
        """Get all specialisms for a tenant."""
        query = select(Specialism).where(Specialism.tenant_id == tenant_id)
        
        if active_only:
            query = query.where(Specialism.is_active == True)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_specialisms_by_keys(
        self,
        tenant_id: UUID,
        specialism_keys: List[str],
        active_only: bool = True,
    ) -> List[Specialism]:
        """Resolve specialisms by tenant-scoped stable keys."""
        if not specialism_keys:
            return []

        query = select(Specialism).where(
            and_(
                Specialism.tenant_id == tenant_id,
                Specialism.specialism_key.in_(specialism_keys),
            )
        )
        if active_only:
            query = query.where(Specialism.is_active.is_(True))

        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def assign_specialism_to_profile(
        self,
        tenant_id: UUID,
        profile_id: UUID,
        specialism_id: UUID,
        proficiency_level: Optional[str] = None,
        assigned_by_profile_id: Optional[UUID] = None
    ) -> ProfileSpecialism:
        """Assign a specialism to a profile."""
        profile_specialism = ProfileSpecialism(
            tenant_id=tenant_id,
            profile_id=profile_id,
            specialism_id=specialism_id,
            proficiency_level=proficiency_level,
            assigned_by_profile_id=assigned_by_profile_id
        )
        self.db.add(profile_specialism)
        await self.db.commit()
        return profile_specialism
    
    async def get_profile_specialisms(
        self,
        tenant_id: UUID,
        profile_id: UUID
    ) -> List[ProfileSpecialism]:
        """Get all specialisms for a profile."""
        query = (
            select(ProfileSpecialism)
            .options(selectinload(ProfileSpecialism.specialism))
            .where(and_(
                ProfileSpecialism.tenant_id == tenant_id,
                ProfileSpecialism.profile_id == profile_id,
                ProfileSpecialism.unassigned_at.is_(None)
            ))
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def replace_profile_specialisms(
        self,
        tenant_id: UUID,
        profile_id: UUID,
        specialism_ids: List[UUID],
        assigned_by_profile_id: Optional[UUID] = None,
    ) -> None:
        """Replace all specialisms assigned to a profile with the provided set."""
        delete_stmt = delete(ProfileSpecialism).where(
            and_(
                ProfileSpecialism.tenant_id == tenant_id,
                ProfileSpecialism.profile_id == profile_id,
            )
        )
        await self.db.execute(delete_stmt)

        for specialism_id in specialism_ids:
            self.db.add(
                ProfileSpecialism(
                    tenant_id=tenant_id,
                    profile_id=profile_id,
                    specialism_id=specialism_id,
                    assigned_by_profile_id=assigned_by_profile_id,
                )
            )

        await self.db.commit()
