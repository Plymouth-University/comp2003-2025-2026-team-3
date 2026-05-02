"""SQLAlchemy models for the multi-tenant profile system."""

from sqlalchemy import Column, Text, Boolean, SmallInteger, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from ..database import ProfileBase


class Tenant(ProfileBase):
    """Tenant/Organization model."""

    __tablename__ = "tenant"

    tenant_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_name = Column(Text, nullable=False)
    created_at = Column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    profiles = relationship(
        "Profile", back_populates="tenant", cascade="all, delete-orphan"
    )
    specialisms = relationship(
        "Specialism", back_populates="tenant", cascade="all, delete-orphan"
    )
    avatar_presets = relationship(
        "AvatarPreset", back_populates="tenant", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Tenant(id={self.tenant_id}, name='{self.tenant_name}')>"


class Profile(ProfileBase):
    """User profile model."""

    __tablename__ = "profile"

    profile_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenant.tenant_id", ondelete="CASCADE"),
        nullable=False,
    )
    status = Column(
        Text, nullable=False, default="active"
    )  # active, deactivated, suspended
    created_at = Column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )
    deactivated_at = Column(TIMESTAMP(timezone=True), nullable=True)
    deactivated_reason = Column(Text, nullable=True)

    # Relationships
    tenant = relationship("Tenant", back_populates="profiles")
    display = relationship(
        "ProfileDisplay",
        back_populates="profile",
        uselist=False,
        cascade="all, delete-orphan",
    )
    identities = relationship(
        "ProfileIdentity", back_populates="profile", cascade="all, delete-orphan"
    )
    avatar = relationship(
        "ProfileAvatar",
        back_populates="profile",
        uselist=False,
        cascade="all, delete-orphan",
    )
    specialisms = relationship(
        "ProfileSpecialism",
        back_populates="profile",
        foreign_keys="ProfileSpecialism.profile_id",
        cascade="all, delete-orphan",
    )

    # Indexes
    __table_args__ = (
        Index("ix_profile_tenant_id", "tenant_id"),
        Index("ix_profile_status", "status"),
    )

    def __repr__(self):
        return f"<Profile(id={self.profile_id}, status='{self.status}')>"


class IdentityProvider(ProfileBase):
    """Identity provider configuration (OAuth, SAML, etc.)."""

    __tablename__ = "identity_provider"

    idp_id = Column(SmallInteger, primary_key=True, autoincrement=True)
    idp_name = Column(
        Text, nullable=False, unique=True
    )  # e.g., 'google', 'microsoft', 'local'

    # Relationships
    identities = relationship("ProfileIdentity", back_populates="provider")

    def __repr__(self):
        return f"<IdentityProvider(id={self.idp_id}, name='{self.idp_name}')>"


class ProfileIdentity(ProfileBase):
    """Maps profiles to external identity providers."""

    __tablename__ = "profile_identity"

    profile_identity_id = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenant.tenant_id", ondelete="CASCADE"),
        nullable=False,
    )
    profile_id = Column(
        UUID(as_uuid=True),
        ForeignKey("profile.profile_id", ondelete="CASCADE"),
        nullable=False,
    )
    idp_id = Column(
        SmallInteger,
        ForeignKey("identity_provider.idp_id", ondelete="CASCADE"),
        nullable=False,
    )
    idp_tenant_subject = Column(Text, nullable=False)  # External ID from the provider
    created_at = Column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )
    last_login_at = Column(TIMESTAMP(timezone=True), nullable=True)

    # Relationships
    profile = relationship("Profile", back_populates="identities")
    provider = relationship("IdentityProvider", back_populates="identities")

    # Indexes
    __table_args__ = (
        Index("ix_profile_identity_tenant_profile", "tenant_id", "profile_id"),
        Index(
            "ix_profile_identity_idp_subject",
            "idp_id",
            "idp_tenant_subject",
            unique=True,
        ),
    )

    def __repr__(self):
        return (
            f"<ProfileIdentity(id={self.profile_identity_id}, provider={self.idp_id})>"
        )


class ProfileDisplay(ProfileBase):
    """Profile display name and presentation information."""

    __tablename__ = "profile_display"

    profile_id = Column(
        UUID(as_uuid=True),
        ForeignKey("profile.profile_id", ondelete="CASCADE"),
        primary_key=True,
    )
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenant.tenant_id", ondelete="CASCADE"),
        nullable=False,
    )
    display_name = Column(Text, nullable=False)
    display_name_normalized = Column(Text, nullable=False)  # Lowercase for searching
    created_at = Column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    profile = relationship("Profile", back_populates="display")

    # Indexes
    __table_args__ = (
        Index("ix_profile_display_normalized", "tenant_id", "display_name_normalized"),
    )

    def __repr__(self):
        return f"<ProfileDisplay(profile_id={self.profile_id}, name='{self.display_name}')>"


class AvatarPreset(ProfileBase):
    """Pre-configured avatar options for users to choose from."""

    __tablename__ = "avatar_preset"

    avatar_preset_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenant.tenant_id", ondelete="CASCADE"),
        nullable=False,
    )
    label = Column(Text, nullable=False)
    asset_ref = Column(Text, nullable=False)  # Path or URL to avatar asset
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    tenant = relationship("Tenant", back_populates="avatar_presets")
    profile_avatars = relationship("ProfileAvatar", back_populates="preset")

    # Indexes
    __table_args__ = (
        Index("ix_avatar_preset_tenant_active", "tenant_id", "is_active"),
    )

    def __repr__(self):
        return f"<AvatarPreset(id={self.avatar_preset_id}, label='{self.label}')>"


class ProfileAvatar(ProfileBase):
    """User's avatar configuration."""

    __tablename__ = "profile_avatar"

    profile_id = Column(
        UUID(as_uuid=True),
        ForeignKey("profile.profile_id", ondelete="CASCADE"),
        primary_key=True,
    )
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenant.tenant_id", ondelete="CASCADE"),
        nullable=False,
    )
    avatar_source = Column(
        Text, nullable=False, default="preset"
    )  # 'preset' or 'uploaded'
    avatar_preset_id = Column(
        UUID(as_uuid=True),
        ForeignKey("avatar_preset.avatar_preset_id", ondelete="SET NULL"),
        nullable=True,
    )
    uploaded_asset_ref = Column(Text, nullable=True)  # S3/blob storage reference
    updated_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    profile = relationship("Profile", back_populates="avatar")
    preset = relationship("AvatarPreset", back_populates="profile_avatars")

    def __repr__(self):
        return f"<ProfileAvatar(profile_id={self.profile_id}, source='{self.avatar_source}')>"


class Specialism(ProfileBase):
    """Skill/expertise categories defined by tenant."""

    __tablename__ = "specialism"

    specialism_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenant.tenant_id", ondelete="CASCADE"),
        nullable=False,
    )
    specialism_key = Column(Text, nullable=False)  # e.g., 'network_security'
    specialism_name = Column(Text, nullable=False)  # e.g., 'Network Security'
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    tenant = relationship("Tenant", back_populates="specialisms")
    profile_specialisms = relationship("ProfileSpecialism", back_populates="specialism")

    # Indexes
    __table_args__ = (
        Index("ix_specialism_tenant_key", "tenant_id", "specialism_key", unique=True),
        Index("ix_specialism_tenant_active", "tenant_id", "is_active"),
    )

    def __repr__(self):
        return f"<Specialism(id={self.specialism_id}, name='{self.specialism_name}')>"


class ProfileSpecialism(ProfileBase):
    """Links profiles to their specialisms/skills."""

    __tablename__ = "profile_specialism"

    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenant.tenant_id", ondelete="CASCADE"),
        primary_key=True,
    )
    profile_id = Column(
        UUID(as_uuid=True),
        ForeignKey("profile.profile_id", ondelete="CASCADE"),
        primary_key=True,
    )
    specialism_id = Column(
        UUID(as_uuid=True),
        ForeignKey("specialism.specialism_id", ondelete="CASCADE"),
        primary_key=True,
    )
    proficiency_level = Column(
        Text, nullable=True
    )  # e.g., 'beginner', 'intermediate', 'expert'
    assigned_at = Column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )
    unassigned_at = Column(TIMESTAMP(timezone=True), nullable=True)
    assigned_by_profile_id = Column(
        UUID(as_uuid=True),
        ForeignKey("profile.profile_id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    profile = relationship(
        "Profile", back_populates="specialisms", foreign_keys=[profile_id]
    )
    specialism = relationship("Specialism", back_populates="profile_specialisms")
    assigned_by = relationship("Profile", foreign_keys=[assigned_by_profile_id])

    # Indexes
    __table_args__ = (
        Index("ix_profile_specialism_profile", "tenant_id", "profile_id"),
    )

    def __repr__(self):
        return f"<ProfileSpecialism(profile_id={self.profile_id}, specialism_id={self.specialism_id})>"
