# Multi-Tenant Profile Service Implementation Guide

## Overview

Your SecOps application has been enhanced with a complete multi-tenant profile management system. This allows your software to support multiple organizations (tenants) with isolated user profiles, external identity provider integration, and skill-based specialisms.

## What Was Implemented

### 1. Database Layer
- **PostgreSQL database** with full multi-tenant support
- **Alembic migrations** for schema version control (no more table drops!)
- **All tables from your ER diagram**:
  - `tenant` - Organizations/companies
  - `profile` - User profiles
  - `identity_provider` - OAuth/SSO providers (Google, Microsoft, etc.)
  - `profile_identity` - Links profiles to external identities
  - `profile_display` - User display names
  - `profile_avatar` - Avatar configuration
  - `avatar_preset` - Preset avatar options
  - `specialism` - Skills/expertise categories
  - `profile_specialism` - User skills with proficiency levels

### 2. Application Architecture

```
┌─────────────────────────────────────┐
│  API Endpoints                      │
│  /api/v1/profiles                   │
│  /api/v1/tenants                    │
│  /api/v1/specialisms                │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│  Service Layer                      │
│  - ProfileService                   │
│  - TenantService                    │
│  - SpecialismService                │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│  Repository Layer                   │
│  - ProfileRepository                │
│  - TenantRepository                 │
│  - IdentityRepository               │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│  Database (PostgreSQL)              │
└─────────────────────────────────────┘
```

## Quick Start

### 1. Environment Setup

Create a `.env` file in the `backend` folder:

```bash
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/mydb
ENVIRONMENT=development
DEBUG=True
SECRET_KEY=your-secret-key-change-in-production
```

### 2. Start the Database

```powershell
cd backend
docker compose up -d
```

### 3. Run Migrations

```powershell
python -m alembic upgrade head
```

### 4. Start the API Server

```powershell
python -m uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

## API Endpoints

### Tenant Management

**Create Tenant**
```http
POST /api/v1/tenants
Content-Type: application/json

{
  "tenant_name": "Acme Corporation"
}
```

**Get All Tenants**
```http
GET /api/v1/tenants
```

### Profile Management

**Create Profile**
```http
POST /api/v1/profiles
Content-Type: application/json

{
  "tenant_id": "uuid-here",
  "display_name": "John Doe",
  "status": "active",
  "avatar_preset_id": "uuid-or-null"
}
```

**List Profiles for Tenant**
```http
GET /api/v1/tenants/{tenant_id}/profiles?status=active&limit=100
```

**Get Profile by ID**
```http
GET /api/v1/profiles/{profile_id}?tenant_id={tenant_id}
```

**Update Profile**
```http
PATCH /api/v1/profiles/{profile_id}?tenant_id={tenant_id}
Content-Type: application/json

{
  "display_name": "Jane Doe",
  "status": "active"
}
```

**Search Profiles**
```http
GET /api/v1/tenants/{tenant_id}/profiles/search?q=john
```

**Deactivate Profile**
```http
POST /api/v1/profiles/{profile_id}/deactivate?tenant_id={tenant_id}&reason=Left%20company
```

### Identity Provider Integration

**Link External Identity**
```http
POST /api/v1/profiles/identities
Content-Type: application/json

{
  "profile_id": "uuid-here",
  "tenant_id": "uuid-here",
  "idp_id": 1,
  "idp_tenant_subject": "google-oauth-id-12345"
}
```

**Authenticate via External Identity**
```http
GET /api/v1/auth/profile?idp_name=google&idp_subject=google-oauth-id-12345
```

### Specialism Management

**Create Specialism**
```http
POST /api/v1/specialisms
Content-Type: application/json

{
  "tenant_id": "uuid-here",
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
POST /api/v1/profiles/{profile_id}/specialisms/{specialism_id}?tenant_id={tenant_id}&proficiency_level=expert
```

**Get Profile's Specialisms**
```http
GET /api/v1/profiles/{profile_id}/specialisms?tenant_id={tenant_id}
```

## Database Migrations

### Creating a New Migration

When you modify the models in `app/models/profile.py`:

```powershell
python -m alembic revision --autogenerate -m "Description of changes"
```

### Applying Migrations

```powershell
python -m alembic upgrade head
```

### Rolling Back Migrations

```powershell
python -m alembic downgrade -1
```

### View Migration History

```powershell
python -m alembic history
python -m alembic current
```

## Key Features

### Multi-Tenant Isolation
- All data is isolated by `tenant_id`
- API endpoints require tenant context for security
- Each tenant can have custom specialisms and avatar presets

### Flexible Authentication
- Support for multiple identity providers (OAuth, SAML, local)
- One profile can have multiple linked identities
- Track last login per identity

### Profile Status Management
- **Active**: Normal user
- **Deactivated**: Soft-deleted with reason tracking
- **Suspended**: Temporarily disabled

### Specialism/Skills System
- Define custom skill categories per tenant
- Assign proficiency levels: beginner, intermediate, expert, master
- Track who assigned each skill and when

## Code Structure

```
backend/
├── app/
│   ├── config.py              # Application configuration
│   ├── database.py            # Database connection setup
│   ├── main.py                # FastAPI application
│   ├── models/
│   │   └── profile.py         # SQLAlchemy models
│   ├── schemas/
│   │   └── profile.py         # Pydantic validation schemas
│   ├── repositories/
│   │   └── profile_repository.py  # Data access layer
│   ├── services/
│   │   └── profile_service.py     # Business logic
│   └── routers/
│       └── profiles.py        # API endpoints
├── alembic/
│   ├── versions/              # Migration files
│   └── env.py                 # Alembic configuration
├── alembic.ini                # Alembic settings
├── compose.yml                # Docker PostgreSQL setup
└── .env.example               # Environment variables template

```

## Next Steps

### 1. Add Authentication/Authorization
- Implement JWT token generation
- Add middleware for tenant context extraction
- Create login/logout endpoints

### 2. Add Avatar Upload
- Integrate with cloud storage (AWS S3, Azure Blob)
- Add upload endpoint
- Generate thumbnails

### 3. Extend Identity Providers
- Add Google OAuth integration
- Add Microsoft Azure AD integration
- Add local password authentication

### 4. Add Audit Logging
- Track profile changes
- Log identity provider logins
- Monitor specialism assignments

### 5. Frontend Integration
- Create profile management UI
- Add user switcher for multi-profile support
- Build skill matrix visualization

## Testing

### Using Swagger UI

Visit `http://localhost:8000/docs` to interact with the API through Swagger UI.

### Example Flow

1. **Create a tenant**
2. **Create identity providers** (google, microsoft, local)
3. **Create a profile** for a user
4. **Link external identity** to the profile
5. **Create specialisms** (e.g., "Linux Administration", "Network Security")
6. **Assign specialisms** to the profile with proficiency levels
7. **Test authentication** using the external identity

## Troubleshooting

### Database Connection Issues
- Ensure PostgreSQL is running: `docker compose ps`
- Check connection string in `.env` or `app/config.py`
- Verify database exists: `docker compose exec postgres psql -U postgres -l`

### Migration Errors
- Reset migrations (development only): `python -m alembic downgrade base`
- Check model imports in `alembic/env.py`
- Ensure database URL is correct in `alembic/env.py`

### Import Errors
- Reinstall dependencies: `pip install -r requirements.txt`
- Check Python path: `echo $env:PYTHONPATH` (PowerShell)

## Support

For questions or issues, refer to:
- FastAPI docs: https://fastapi.tiangolo.com/
- SQLAlchemy docs: https://docs.sqlalchemy.org/
- Alembic docs: https://alembic.sqlalchemy.org/
