# Profile Service Implementation Guide

## Overview

Your SecOps application includes a multi-tenant profile management system that supports multiple organizations with isolated user profiles, external identity provider integration, and role-based specialisms. This system is integrated with Microsoft Entra ID for authentication.

## Architecture at a Glance

### System Layers

```
┌─────────────────────────────────────────────────────────────┐
│ Frontend (Vue 3)                                           │
│ - Authentication UI (Sign in/out)                          │
│ - Profile management pages                                 │
│ - Account settings                                         │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP/REST API
                     ↓
┌─────────────────────────────────────────────────────────────┐
│ Backend API (FastAPI)                                      │
│ ┌──────────────────────────────────────────────────────┐  │
│ │ Routers: /auth, /api/v1/profiles, etc.              │  │
│ └──────────────────┬───────────────────────────────────┘  │
│                    │                                       │
│ ┌──────────────────▼───────────────────────────────────┐  │
│ │ Services: ProfileService, TenantService, etc.       │  │
│ │ - Business logic                                    │  │
│ │ - Auto-provisioning on first login                 │  │
│ │ - Multi-tenant isolation                           │  │
│ └──────────────────┬───────────────────────────────────┘  │
│                    │                                       │
│ ┌──────────────────▼───────────────────────────────────┐  │
│ │ Repositories: Database access layer                 │  │
│ │ - Query building                                    │  │
│ │ - Relationship management                          │  │
│ └──────────────────┬───────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────────┘
                     │ SQL/Async Queries
                     ↓
┌─────────────────────────────────────────────────────────────┐
│ PostgreSQL Database                                        │
│ - Tenants (organizations)                                  │
│ - Profiles (users)                                         │
│ - Identity providers (Entra, Google, etc.)                │
│ - Specialisms (skills/roles)                              │
└─────────────────────────────────────────────────────────────┘
```

## Database Schema

### Core Tables

#### `tenant`
Represents an organization or workspace.

```sql
id (UUID, primary key)
tenant_name (VARCHAR) -- Name of the organization
created_at (TIMESTAMP) -- Creation time
updated_at (TIMESTAMP) -- Last update time
```

**Notes:**
- Auto-created by `resolve_entra_profile()` on first login
- Default tenant name: `profile-service-test` (configurable via `ENTRA_INTERNAL_TENANT_NAME`)

#### `profile`
Represents a user account within a tenant.

```sql
profile_id (UUID, primary key)
tenant_id (UUID, foreign key) -- Tenant this profile belongs to
display_name (VARCHAR) -- User's display name
status (VARCHAR) -- 'active', 'deactivated', 'suspended'
created_at (TIMESTAMP)
updated_at (TIMESTAMP)
```

**Statuses:**
- `active` - Normal user account
- `deactivated` - Soft-deleted with reason tracking
- `suspended` - Temporarily disabled (e.g., pending review)

#### `identity_provider`
External authentication sources.

```sql
id (UUID, primary key)
provider_name (VARCHAR) -- 'microsoft', 'google', 'local', etc.
is_active (BOOLEAN) -- Whether this provider is enabled
created_at (TIMESTAMP)
```

**Default Providers:**
- `microsoft` - Created during Entra authentication setup
- Can add more as needed (Google, GitHub, etc.)

#### `profile_identity`
Links a profile to external identities (one profile can have multiple external accounts).

```sql
profile_id (UUID, foreign key)
identity_provider_id (UUID, foreign key)
idp_subject (VARCHAR) -- External user ID (e.g., Entra object_id)
idp_tenant_subject (VARCHAR) -- External tenant/org ID (e.g., Entra tid)
last_login (TIMESTAMP) -- Last authentication time
```

**Composition:** `profile_id` + `identity_provider_id` forms the primary key (allows one profile multiple identities).

**Entra ID Mapping:**
- `idp_subject` = Entra `oid` (object ID - unique user)
- `idp_tenant_subject` = Entra `tid` (tenant ID - which org)

#### `profile_display`
Customized display information for a profile.

```sql
profile_id (UUID, primary key/foreign key)
display_name (VARCHAR) -- Can differ from profile.display_name
avatar_url (VARCHAR) -- URL to custom avatar
```

#### `profile_avatar`
Avatar preferences and configuration.

```sql
profile_id (UUID, primary key/foreign key)
avatar_preset_id (UUID, foreign key) -- Link to preset
custom_avatar_url (VARCHAR)
```

#### `avatar_preset`
Pre-defined avatar options (useful for team consistency).

```sql
id (UUID, primary key)
preset_name (VARCHAR) -- 'initials', 'gradient', 'emoji', etc.
icon_url (VARCHAR)
color_scheme (VARCHAR)
```

#### `specialism`
Skills or expertise categories (per-tenant customizable).

```sql
id (UUID, primary key)
tenant_id (UUID, foreign key) -- Tenants can define own specialisms
specialism_key (VARCHAR) -- Programmatic identifier ('linux_admin', 'network_security')
specialism_name (VARCHAR) -- Display name ('Linux Administration')
description (TEXT) -- Full description
is_active (BOOLEAN)
created_at (TIMESTAMP)
```

#### `profile_specialism`
Maps users to their skills and proficiency levels.

```sql
profile_id (UUID, foreign key)
specialism_id (UUID, foreign key)
proficiency_level (VARCHAR) -- 'beginner', 'intermediate', 'expert', 'master'
assigned_by (UUID, foreign key) -- Who assigned this skill
assigned_at (TIMESTAMP)
```

**Composition:** `profile_id` + `specialism_id` forms the primary key.

## File Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── config.py                # Environment configuration
│   ├── database.py              # SQLAlchemy async setup
│   ├── main.py                  # FastAPI application
│   │
│   ├── auth.py                  # Entra OIDC + session helpers
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   └── profile.py           # SQLAlchemy ORM models
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── profile.py           # Pydantic validation classes
│   │
│   ├── repositories/
│   │   ├── __init__.py
│   │   └── profile_repository.py # Database access layer
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   └── profile_service.py   # Business logic layer
│   │
│   └── routers/
│       ├── __init__.py
│       ├── auth.py              # Authentication endpoints
│       └── profiles.py          # Profile CRUD endpoints
│
├── alembic/
│   ├── env.py                   # Migration environment config
│   ├── script.py.mako           # Migration template
│   └── versions/                # Migration files
│
├── alembic.ini                  # Alembic configuration
├── docker-compose.yml           # PostgreSQL container definition
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment template
└── run_local.sh                 # Local development startup script
```

## API Endpoints

### Authentication Routes

See `ENTRA_PROFILE_SERVICE_INTEGRATION.md` for detailed Entra ID flow.

```http
GET    /auth/login                    # Redirect to Entra login
GET    /auth/callback                 # Entra redirect callback
GET    /api/v1/auth/me               # Get current session + profile
POST   /api/v1/auth/logout           # Clear session
```

### Profile Management Routes

**List Profiles**
```http
GET /api/v1/tenants/{tenant_id}/profiles?status=active&limit=100&offset=0
```

Response:
```json
{
  "profiles": [
    {
      "profile_id": "uuid",
      "tenant_id": "uuid",
      "display_name": "John Doe",
      "status": "active",
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 42,
  "limit": 100,
  "offset": 0
}
```

**Get Single Profile**
```http
GET /api/v1/profiles/{profile_id}?tenant_id={tenant_id}
```

Response:
```json
{
  "profile_id": "uuid",
  "tenant_id": "uuid",
  "display_name": "John Doe",
  "status": "active",
  "created_at": "2024-01-15T10:30:00Z",
  "last_login": "2024-01-20T14:22:00Z",
  "specialisms": [
    {
      "specialism_id": "uuid",
      "specialism_name": "Network Security",
      "proficiency_level": "expert"
    }
  ]
}
```

**Create Profile**
```http
POST /api/v1/profiles
Content-Type: application/json

{
  "tenant_id": "uuid",
  "display_name": "Jane Smith",
  "status": "active"
}
```

**Update Profile**
```http
PATCH /api/v1/profiles/{profile_id}?tenant_id={tenant_id}
Content-Type: application/json

{
  "display_name": "Jane S. Smith",
  "status": "active"
}
```

**Search Profiles**
```http
GET /api/v1/tenants/{tenant_id}/profiles/search?q=jane&limit=20
```

**Deactivate Profile**
```http
POST /api/v1/profiles/{profile_id}/deactivate?tenant_id={tenant_id}&reason=Left%20company
```

### Tenant Management Routes

**Create Tenant**
```http
POST /api/v1/tenants
Content-Type: application/json

{
  "tenant_name": "Acme Corporation"
}
```

**List Tenants**
```http
GET /api/v1/tenants?limit=100
```

**Get Tenant**
```http
GET /api/v1/tenants/{tenant_id}
```

### Specialism Management Routes

**Create Specialism**
```http
POST /api/v1/specialisms
Content-Type: application/json

{
  "tenant_id": "uuid",
  "specialism_key": "network_security",
  "specialism_name": "Network Security",
  "description": "Expertise in network security and firewall management",
  "is_active": true
}
```

**List Specialisms**
```http
GET /api/v1/tenants/{tenant_id}/specialisms?active_only=true
```

**Assign Specialism to Profile**
```http
POST /api/v1/profiles/{profile_id}/specialisms/{specialism_id}?tenant_id={tenant_id}
Content-Type: application/json

{
  "proficiency_level": "expert"
}
```

Values: `beginner`, `intermediate`, `expert`, `master`

**Get Profile Specialisms**
```http
GET /api/v1/profiles/{profile_id}/specialisms?tenant_id={tenant_id}
```

### Identity Management Routes

**Link External Identity**
```http
POST /api/v1/profiles/identities
Content-Type: application/json

{
  "profile_id": "uuid",
  "tenant_id": "uuid",
  "identity_provider_id": "uuid",
  "idp_subject": "12345-67890",
  "idp_tenant_subject": "org-tenant-id"
}
```

**Authenticate via External Identity**
```http
GET /api/v1/auth/profile?idp_name=microsoft&idp_subject=user-oid&idp_tenant_subject=tenant-id
```

## Code Patterns

### Service Layer Pattern

Services contain business logic and coordinate repositories:

```python
# backend/app/services/profile_service.py

class ProfileService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = ProfileRepository(db)

    async def resolve_entra_profile(
        self,
        entra_tenant_id: str,
        object_id: str,
        display_name: str
    ) -> Profile:
        """
        Find or create a profile based on Entra identity.
        Called during /auth/callback when user logs in.
        """
        # ... implementation
```

### Repository Layer Pattern

Repositories handle database access:

```python
# backend/app/repositories/profile_repository.py

class ProfileRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_profile_by_id(
        self,
        profile_id: UUID,
        tenant_id: UUID
    ) -> Optional[Profile]:
        """Get a single profile with tenant isolation."""
        # ... SQL query
```

### Route Pattern

Routes handle HTTP and delegate to services:

```python
# backend/app/routers/profiles.py

@router.get("/api/v1/profiles/{profile_id}")
async def get_profile(
    profile_id: UUID,
    tenant_id: UUID = Query(...),
    session: AuthenticatedSession = Depends(get_current_session),
    db: AsyncSession = Depends(get_db)
):
    """Get profile by ID (requires authentication)."""
    profile_service = ProfileService(db)
    profile = await profile_service.get_profile(profile_id, tenant_id)

    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    return profile
```

## Database Migrations

Migrations are version-controlled and applied sequentially.

### Viewing Migrations

```bash
cd backend
alembic history    # All migrations
alembic current    # Currently applied migration
```

### Applying Migrations

On first run:
```bash
alembic upgrade head  # Apply all pending migrations
```

After pulling new migrations:
```bash
alembic upgrade +2    # Apply next 2 migrations
```

### Creating a New Migration

When you modify models in `backend/app/models/profile.py`:

```bash
cd backend
source .venv/bin/activate
alembic revision --autogenerate -m "Add email column to profile"
```

Review the generated file in `alembic/versions/` to ensure it's correct.

Apply it:
```bash
alembic upgrade head
```

### Rolling Back Migrations

Undo the last migration:
```bash
alembic downgrade -1
```

Undo multiple:
```bash
alembic downgrade -2
```

Go to a specific version:
```bash
alembic downgrade abc123def456
```

### Production Migration Strategy

1. **Test migrations locally** before deployment
2. **Backup the database** before running migrations
3. **Run migrations before deploying code** that depends on them
4. **Monitor for long-running migrations** on large tables
5. **Have a rollback plan** if something goes wrong

## Security & Multi-Tenancy

### Tenant Isolation

All queries include the tenant in the WHERE clause:

```python
# ✅ Correct - Tenant-scoped query
profiles = await db.execute(
    select(Profile).where(
        (Profile.tenant_id == tenant_id) &
        (Profile.status == 'active')
    )
)

# ❌ Wrong - No tenant filter (security issue!)
profiles = await db.execute(
    select(Profile).where(Profile.status == 'active')
)
```

### Authentication Requirement

All profile endpoints require a valid `secops_session` cookie:

```python
@router.get("/api/v1/profiles/{profile_id}")
async def get_profile(
    session: AuthenticatedSession = Depends(get_current_session),
    # ... other parameters
):
    """get_current_session dependency enforces authentication."""
    pass
```

If session is missing or invalid, returns `401 Unauthorized`.

### Session-Based Authorization

The `session` object contains:
- `session.profile_id` - Current user's profile
- `session.tenant_id` - Current user's tenant
- `session.entra_tenant_id` - User's Entra tenant
- `session.object_id` - User's Entra object ID

Use these to enforce authorization policies:

```python
@router.get("/api/v1/profiles/{profile_id}")
async def get_profile(
    profile_id: UUID,
    session: AuthenticatedSession = Depends(get_current_session),
    db: AsyncSession = Depends(get_db)
):
    # Allow users to view their own profile
    if str(profile_id) == session.profile_id:
        # ... fetch and return
        pass

    # Otherwise, check if user has admin role
    # (implement role check as needed)
    raise HTTPException(status_code=403, detail="Not authorized")
```

## Testing

### Unit Testing

Test services in isolation:

```python
# backend/tests/test_profile_service.py
import pytest
from app.services.profile_service import ProfileService

@pytest.mark.asyncio
async def test_resolve_entra_profile(db):
    service = ProfileService(db)
    profile = await service.resolve_entra_profile(
        entra_tenant_id="tenant-123",
        object_id="user-456",
        display_name="Test User"
    )

    assert profile.display_name == "Test User"
    assert profile.status == "active"
```

### Integration Testing

Test full API flows:

```python
@pytest.mark.asyncio
async def test_profile_creation_flow(client):
    # Create tenant
    tenant_response = client.post("/api/v1/tenants", json={
        "tenant_name": "Test Org"
    })
    tenant_id = tenant_response.json()["id"]

    # Login (which auto-creates profile)
    login_response = client.get("/auth/login")

    # Verify profile was created
    me_response = client.get("/api/v1/auth/me")
    assert me_response.status_code == 200
```

### Using Swagger UI

FastAPI auto-generates interactive API documentation:

1. Start the backend: `./run_local.sh`
2. Open `http://localhost:8000/docs`
3. Try endpoints directly from the browser

## Common Development Tasks

### Adding a New Field to Profiles

1. Update the model in `backend/app/models/profile.py`:
   ```python
   class Profile(Base):
       __tablename__ = "profile"
       # ... existing fields
       department: Mapped[Optional[str]] = mapped_column(String, nullable=True)
   ```

2. Update the schema in `backend/app/schemas/profile.py`:
   ```python
   class ProfileUpdate(BaseModel):
       # ... existing fields
       department: Optional[str] = None
   ```

3. Create a migration:
   ```bash
   alembic revision --autogenerate -m "Add department to profile"
   ```

4. Review and apply:
   ```bash
   alembic upgrade head
   ```

### Debugging Database Issues

```bash
# Connect to PostgreSQL
cd backend
docker compose exec postgres psql -U postgres -d mydb

# Useful commands inside psql
\dt                 # List tables
\d profile          # Show profile table schema
SELECT * FROM profile LIMIT 5;  # View some data
```

### Checking Async Query Performance

Use SQLAlchemy's echo mode:

```python
# In backend/app/config.py
engine = create_async_engine(
    DATABASE_URL,
    echo=True  # Prints all SQL queries
)
```

Be aware: Echo mode adds logging overhead. Remove in production.

## Next Steps

- **Authentication**: See `ENTRA_PROFILE_SERVICE_INTEGRATION.md` for Entra ID setup
- **Local Development**: See `LOCAL_RUN_START_TO_FINISH.md` for environment setup
- **Deployment**: See architecture docs for production deployment strategy
- **API Reference**: See Swagger UI at `http://localhost:8000/docs`

## Troubleshooting

### Connection pooling errors

**Symptom:** `QueuePool limit exceeded`

**Solution:** Ensure you're not opening too many database connections. Use dependency injection properly:

```python
# ✅ Correct - Connection returned to pool
@router.get("/")
async def route(db: AsyncSession = Depends(get_db)):
    result = await db.execute(...)
    # Connection returned when route completes
```

```python
# ❌ Wrong - Connection never returned
engine = create_async_engine(DATABASE_URL)
db = Session(engine)  # Global session - never closed
```

### Alembic revision conflicts

If multiple team members create migrations simultaneously:

1. Resolve manually by merging the revision files
2. Run `alembic upgrade head` to apply all
3. Communicate on the team to wait before next migration

### Profile not found after login

Check that `ENTRA_INTERNAL_TENANT_NAME` exists:

```bash
# Inside psql
SELECT * FROM tenant WHERE tenant_name = 'profile-service-test';
```

If not found, auto-provisioning failed. Check backend logs.

### Weird SQLAlchemy relationship errors

Ensure models properly import each other:

```python
# backend/app/models/profile.py
from sqlalchemy.orm import relationship

class Profile(Base):
    # ... fields
    display: Mapped["ProfileDisplay"] = relationship(back_populates="profile")
```

Make sure back_populates matches the reverse relationship exactly.
