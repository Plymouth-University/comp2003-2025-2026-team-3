"""Pydantic schemas for profile API requests and responses."""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from uuid import UUID


# ============ Tenant Schemas ============

class TenantBase(BaseModel):
    tenant_name: str = Field(..., min_length=1, max_length=255)


class TenantCreate(TenantBase):
    pass


class TenantResponse(TenantBase):
    tenant_id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============ Profile Schemas ============

class ProfileBase(BaseModel):
    status: str = Field(default="active", pattern="^(active|deactivated|suspended)$")


class ProfileCreate(ProfileBase):
    tenant_id: UUID
    display_name: str = Field(..., min_length=1, max_length=255)
    avatar_preset_id: Optional[UUID] = None


class ProfileUpdate(BaseModel):
    display_name: Optional[str] = Field(None, min_length=1, max_length=255)
    status: Optional[str] = Field(None, pattern="^(active|deactivated|suspended)$")
    deactivated_reason: Optional[str] = None
    avatar_source: Optional[str] = Field(None, pattern="^(preset|uploaded)$")
    avatar_preset_id: Optional[UUID] = None


class ProfileDisplayResponse(BaseModel):
    display_name: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ProfileAvatarResponse(BaseModel):
    avatar_source: str
    avatar_preset_id: Optional[UUID] = None
    uploaded_asset_ref: Optional[str] = None
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ProfileIdentityResponse(BaseModel):
    profile_identity_id: UUID
    idp_id: int
    created_at: datetime
    last_login_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ProfileResponse(ProfileBase):
    profile_id: UUID
    tenant_id: UUID
    created_at: datetime
    deactivated_at: Optional[datetime] = None
    deactivated_reason: Optional[str] = None
    display: Optional[ProfileDisplayResponse] = None
    avatar: Optional[ProfileAvatarResponse] = None
    identities: List[ProfileIdentityResponse] = []
    
    class Config:
        from_attributes = True


# ============ Identity Provider Schemas ============

class IdentityProviderBase(BaseModel):
    idp_name: str = Field(..., min_length=1, max_length=50)


class IdentityProviderCreate(IdentityProviderBase):
    pass


class IdentityProviderResponse(IdentityProviderBase):
    idp_id: int
    
    class Config:
        from_attributes = True


class ProfileIdentityCreate(BaseModel):
    profile_id: UUID
    tenant_id: UUID
    idp_id: int
    idp_tenant_subject: str = Field(..., min_length=1)


# ============ Specialism Schemas ============

class SpecialismBase(BaseModel):
    specialism_key: str = Field(..., min_length=1, max_length=100)
    specialism_name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    is_active: bool = True


class SpecialismCreate(SpecialismBase):
    tenant_id: UUID


class SpecialismUpdate(BaseModel):
    specialism_name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class SpecialismResponse(SpecialismBase):
    specialism_id: UUID
    tenant_id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True


class ProfileSpecialismCreate(BaseModel):
    tenant_id: UUID
    profile_id: UUID
    specialism_id: UUID
    proficiency_level: Optional[str] = Field(None, pattern="^(beginner|intermediate|expert|master)$")
    assigned_by_profile_id: Optional[UUID] = None


class ProfileSpecialismResponse(BaseModel):
    specialism_id: UUID
    proficiency_level: Optional[str] = None
    assigned_at: datetime
    unassigned_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# ============ Avatar Preset Schemas ============

class AvatarPresetBase(BaseModel):
    label: str = Field(..., min_length=1, max_length=100)
    asset_ref: str = Field(..., min_length=1)
    is_active: bool = True


class AvatarPresetCreate(AvatarPresetBase):
    tenant_id: UUID


class AvatarPresetUpdate(BaseModel):
    label: Optional[str] = Field(None, min_length=1, max_length=100)
    asset_ref: Optional[str] = None
    is_active: Optional[bool] = None


class AvatarPresetResponse(AvatarPresetBase):
    avatar_preset_id: UUID
    tenant_id: UUID
    
    class Config:
        from_attributes = True
