# Microsoft Entra ID + Profile Service Integration

This document explains how Microsoft Entra ID authentication is integrated with the profile service. It covers the architecture, implementation details, code flow, file structure, and maintenance guidelines.

## Overview

The integration adds OAuth 2.0/OpenID Connect (OIDC) authentication using Microsoft Entra ID without storing company directory data. The backend serves as the authorization server, handling token exchange and session management.

### Design Principles

- **Entra ID for authentication** - Microsoft Entra ID is the single source of truth for user identity
- **Minimal data storage** - Only the identity markers (`tid` and `oid`) required to link back to Entra
- **Server-side sessions** - Backend manages session state; frontend never directly handles tokens
- **Auto-provisioning** - User profiles are created automatically on first login
- **Multi-tenancy ready** - Design supports multiple internal tenants and Entra tenants

## Database Schema

The integration uses these key database tables:

### `tenant`
Represents an organization/account within the system. The integration creates or uses an existing tenant during auto-provisioning (configured via `ENTRA_INTERNAL_TENANT_NAME`).

```sql
id (uuid, pk)
tenant_name (string)
created_at (timestamp)
```

### `profile`
Represents a user profile linked to a tenant.

```sql
profile_id (uuid, pk)
tenant_id (uuid, fk)
display_name (string)
status (string: active/deactivated/suspended)
created_at (timestamp)
updated_at (timestamp)
```

### `identity_provider`
Represents external auth sources (Entra ID, Google, etc).

```sql
id (uuid, pk)
provider_name (string) -- e.g., "microsoft"
is_active (boolean)
created_at (timestamp)
```

### `profile_identity`
Links a profile to an external identity. The `idp_subject` stores the Entra `oid` (object ID), and `idp_tenant_subject` stores the Entra `tid` (tenant ID).

```sql
profile_id (uuid, fk)
identity_provider_id (uuid, fk)
idp_subject (string) -- Entra object ID (oid)
idp_tenant_subject (string) -- Entra tenant ID (tid)
last_login (timestamp)
```

### `profile_display` and `profile_avatar`
Store user display customization.

```sql
profile_id (uuid, pk)
display_name (string)

profile_id (uuid, pk)
avatar_preset_id (uuid, fk)
```

## Entra ID Token Claims

When a user signs in through Entra ID, the following claims are extracted from the ID token:

- `tid` - Tenant ID (your Entra tenant, e.g., `24e92e30-83bf-4d0e-8a69-3a7b71901db6`)
- `oid` - Object ID (the unique user ID within that tenant)
- `name` - Display name from Entra
- `iss` - Issuer (always the Entra token endpoint)
- `aud` - Audience (must match your Client ID)
- `email` - User's email (if available)
- `preferred_username` - User's principal name

The `tid + oid` combination uniquely identifies a user across all Entra tenants and is used as the local identity key.

## Authentication Flow

This is a backend-led OAuth 2.0 / OIDC authorization code flow.

### User Journey (Browser)

1. User opens the frontend at `http://localhost:5173` (or your configured `FRONTEND_URL`)
2. Frontend calls `GET /api/v1/auth/me` to check session status
3. If no session cookie exists, UI shows the sign-out screen with "Sign in with Microsoft" button
4. User clicks the sign-in button
5. Frontend redirects to `GET /auth/login` on the backend
6. Backend redirects user to Microsoft Entra ID login page
7. User signs in with their Entra credentials
8. Microsoft redirects back to `GET /auth/callback?code=...&state=...` on backend
9. Backend validates the callback, creates a profile if needed, and sets a session cookie
10. Backend redirects user to `FRONTEND_URL` (e.g., `http://localhost:5173`)
11. Frontend calls `GET /api/v1/auth/me` and renders the authenticated app

### Step-by-Step Code Flow

**Step 1: User clicks "Sign in"**
- File: `backend/app/routers/auth.py:26-32` (`GET /auth/login`)
- Creates a random CSRF state token (`create_state_token()`)
- Calls `build_authorization_url(state)` which:
  - Fetches Entra's OpenID configuration from Microsoft
  - Builds a URL with your `ENTRA_CLIENT_ID`, redirect URI, and state
  - Returns the Entra login endpoint

**Step 2: Browser redirected to Entra**
- User authenticates with Entra at: `https://login.microsoftonline.com/{ENTRA_TENANT_ID}/oauth2/v2.0/authorize?...`

**Step 3: Entra redirects back to your backend**
- Browser goes to: `GET /auth/callback?code=...&state=...`
- File: `backend/app/routers/auth.py:35-77`

**Step 4: Backend exchanges authorization code**
- Function: `exchange_code_for_identity(code)` in `backend/app/auth.py:83-112`
- Sends the auth code to: `https://login.microsoftonline.com/{ENTRA_TENANT_ID}/oauth2/v2.0/token` with:
  - Your `ENTRA_CLIENT_ID` and `ENTRA_CLIENT_SECRET`
  - The authorization code
  - Redirect URI (must exactly match registered URI)
- Microsoft responds with `access_token` and `id_token`

**Step 5: Backend validates the ID token**
- Function: `validate_id_token(id_token)` in `backend/app/auth.py:115-159`
- Extracts the token header to get the key ID (`kid`)
- Fetches Microsoft's JSON Web Key Set (JWKS) using `get_jwks()` in `backend/app/auth.py:54-59`
  - JWKS URL is fetched from Entra's `.well-known/openid-configuration`
- Verifies the token signature using the public key from JWKS
- Decodes the token and validates:
  - Issuer matches Entra
  - Audience (`aud`) matches your `ENTRA_CLIENT_ID`
  - Token is not expired
- Extracts claims: `tid`, `oid`, `name`, `iss`

**Step 6: Backend resolves or creates the profile**
- Function: `resolve_entra_profile()` in `backend/app/services/profile_service.py`
- Builds identity key: `{tid}:{oid}` (e.g., `24e92e30-83bf-4d0e-8a69-3a7b71901db6:12345678-1234-1234-1234-123456789012`)
- Queries `profile_identity` table for a matching profile
- If found: Updates `last_login` and returns the profile
- If not found (first login):
  - Gets or creates the internal tenant (using `ENTRA_INTERNAL_TENANT_NAME` from config)
  - Creates a new `profile` row
  - Creates `profile_display` with the display name from Entra
  - Creates `profile_avatar` (optional, defaults to null)
  - Gets or creates the `identity_provider` row for "microsoft"
  - Creates `profile_identity` linking the profile to the Entra identity

**Step 7: Backend creates a signed session cookie**
- Function: `create_session_token()` in `backend/app/auth.py:162-181`
- Creates a JWT with claims:
  - `profile_id` - The resolved/created profile ID
  - `tenant_id` - The internal tenant ID
  - `entra_tenant_id` - The Entra `tid`
  - `object_id` - The Entra `oid`
  - `display_name` - User's name
  - `issuer` - The token issuer
  - `iat` - Issued at timestamp
  - `exp` - Expiration time (default: 8 hours)
- Signs the JWT with `SECRET_KEY` using `HS256`
- Cookie properties:
  - **HttpOnly** - Not accessible to JavaScript (prevents XSS theft)
  - **SameSite=Lax** - CSRF protection
  - **Secure=False** for localhost development (should be `True` in production)
  - **Max-Age** - 28800 seconds (8 hours)

**Step 8: Backend redirects to frontend**
- Sets the session cookie name: `secops_session` (configured via `SESSION_COOKIE_NAME`)
- Redirects to `FRONTEND_URL`

**Step 9: Frontend calls `GET /api/v1/auth/me`**
- File: `backend/app/routers/auth.py:80-97`
- Dependency: `get_current_session()` in `backend/app/auth.py:201-209`
  - Reads the `secops_session` cookie
  - Calls `decode_session_token(token)` to validate and decode
  - Returns `AuthenticatedSession` model
- Returns current session + resolved profile as JSON

## Code Architecture

### Backend Structure

The backend follows a layered architecture:

```
backend/
├── app/
│   ├── auth.py                    # Entra OIDC + session helpers
│   ├── config.py                  # Environment configuration
│   ├── main.py                    # FastAPI app + middleware
│   ├── database.py                # Database connection
│   ├── routers/
│   │   └── auth.py               # Auth endpoints
│   ├── services/
│   │   └── profile_service.py    # Profile resolution logic
│   ├── repositories/
│   │   └── profile_repository.py # Database queries
│   ├── models/
│   │   └── profile.py            # SQLAlchemy ORM models
│   └── schemas/
│       └── profile.py            # Pydantic validation schemas
└── alembic/                       # Database migrations
```

### Key Backend Files

#### 1. `backend/app/auth.py` - Core Authentication

This file contains all Entra ID and session cookie logic:

**Entra Configuration & Token Validation:**
- `get_openid_configuration()` - Fetches and caches `https://login.microsoftonline.com/{ENTRA_TENANT_ID}/.well-known/openid-configuration`
- `get_jwks()` - Fetches and caches the JWKS (JSON Web Key Set) used to verify token signatures
- `build_authorization_url(state)` - Constructs the Entra login URL
- `create_state_token()` - Generates random CSRF state for the login flow
- `exchange_code_for_identity(code)` - Posts to `token_endpoint`, receives tokens, validates ID token
- `validate_id_token(id_token)` - Verifies JWT signature and claims, extracts user info
- `_find_signing_key(kid)` - Finds the signing key from JWKS by key ID
- `_fetch_json(target)` - Helper for HTTPS requests to Microsoft

**Session Cookie:**
- `create_session_token(...)` - Creates and signs a JWT for the browser cookie
- `decode_session_token(token)` - Decodes and validates the session JWT
- `get_current_session(request)` - FastAPI dependency that validates the current user's session
- `build_cookie_settings()` - Returns cookie configuration (HttpOnly, SameSite, etc.)

**Models:**
- `EntraIdentity` - Pydantic model for `tid`, `oid`, `name`, `iss` extracted from token
- `AuthenticatedSession` - Pydantic model for the session cookie payload

#### 2. `backend/app/routers/auth.py` - Auth Endpoints

HTTP endpoints for the auth flow:

- `GET /auth/login` - Initiates Entra login, creates state token, redirects to Entra
- `GET /auth/callback` - Handles Entra redirect, exchanges code, resolves profile, sets session cookie
- `GET /api/v1/auth/me` - Returns current session + profile (requires valid session cookie)
- `POST /api/v1/auth/logout` - Clears session cookies

#### 3. `backend/app/config.py` - Configuration

Loads environment variables:

```python
ENTRA_TENANT_ID           # Your Entra tenant ID
ENTRA_CLIENT_ID           # Your app registration's client ID
ENTRA_CLIENT_SECRET       # Your app registration's client secret
ENTRA_REDIRECT_URI        # Callback URL (e.g., http://localhost:8000/auth/callback)
ENTRA_INTERNAL_TENANT_NAME # Tenant name when creating profiles (e.g., "profile-service-test")
ENTRA_IDP_NAME            # Identity provider name stored in DB (e.g., "microsoft")
FRONTEND_URL              # Frontend URL to redirect after login
SESSION_COOKIE_NAME       # Cookie name (e.g., "secops_session")
SESSION_MAX_AGE_SECONDS   # Session expiry (e.g., 28800 = 8 hours)
SECRET_KEY                # Used to sign session JWTs
ALGORITHM                 # JWT algorithm (e.g., "HS256")
```

#### 4. `backend/app/services/profile_service.py` - Profile Resolution

Key method: `resolve_entra_profile(entra_tenant_id, object_id, display_name)`

- Builds identity key: `{tid}:{oid}`
- Queries `profile_identity` for existing profile
- If found: updates `last_login`, returns profile
- If not found:
  - Gets or creates `tenant` by `ENTRA_INTERNAL_TENANT_NAME`
  - Creates new `profile` in that tenant
  - Creates `profile_display` with name
  - Gets or creates `identity_provider` for "microsoft"
  - Creates `profile_identity` linking them
  - Returns the new profile

#### 5. `backend/app/repositories/profile_repository.py` - Database Access

Methods added/modified:
- `get_tenant_by_name(name)` - Finds or creates tenant by name
- `get_or_create_identity_provider(name)` - Looks up or creates identity provider
- Profile CRUD operations modified to support multi-tenancy

#### 6. `backend/app/main.py` - FastAPI Setup

- Registers auth routes
- Adds middleware for CORS
- Protects ticket endpoints with `Depends(get_current_session)`
- Enables request logging

### Frontend Integration

#### `frontend/src/shared/auth.ts`
Session utilities:
- `getAuthMe()` - Calls API `GET /api/v1/auth/me`
- `logout()` - Calls API `POST /api/v1/auth/logout`
- Session response types

#### `frontend/src/main.ts`
Bootstrap logic:
- Calls `getAuthMe()` on app startup
- If 401, shows signed-out UI
- If 200, initializes authenticated app

#### `frontend/src/app/App.ts`
- Signed-out screen with "Sign in with Microsoft" button
- Links to `GET /auth/login`
- Signed-in UI with profile info and logout button

#### `frontend/src/pages/AccountPage.ts`
Shows:
- Display name from session
- Entra tenant ID
- Entra object ID
- Last login time

## Session Management

### Session Lifecycle

**Creation:**
1. User successfully completes Entra login
2. Backend creates a signed JWT containing:
   - `profile_id` - Internal profile UUID
   - `tenant_id` - Internal tenant UUID
   - `entra_tenant_id` - Entra tenant ID (tid)
   - `object_id` - Entra user ID (oid)
   - `display_name` - User's name
   - `issuer` - Entra token issuer
   - `iat` - When the token was created
   - `exp` - When it expires

3. JWT is signed with `SECRET_KEY` (default: `dev-secret-key-change-in-production`)
4. Signed JWT is placed in an HTTP-only cookie named `secops_session`

**Validation:**
- Dependency `get_current_session()` is used on protected endpoints
- Extracts `secops_session` cookie from request
- Verifies JWT signature with `SECRET_KEY`
- Validates expiration time
- Returns `AuthenticatedSession` model if valid; raises 401 if not

**Invalidation:**
- `POST /api/v1/auth/logout` deletes the `secops_session` cookie
- Cookie is immediately unusable in the browser

### Cookie Security

The cookie is configured with:
- **HttpOnly** - Prevents JavaScript access (XSS protection)
- **SameSite=Lax** - Prevents cross-site requests (CSRF protection)
- **Path=/** - Available to all endpoints
- **Secure=False** for localhost development
  - **Must be `True` in production** (requires HTTPS)
- **Max-Age=28800** - Expires in 8 hours (configurable via `SESSION_MAX_AGE_SECONDS`)

### Environment Variables

In `backend/.env`, configure:

```bash
# Entra ID
ENTRA_TENANT_ID=24e92e30-83bf-4d0e-8a69-3a7b71901db6  # Your Entra tenant
ENTRA_CLIENT_ID=52b091e9-0fd8-47d7-9e82-9f140281fe55   # Your app registration
ENTRA_CLIENT_SECRET=your-secret-here                    # Keep this secret!
ENTRA_REDIRECT_URI=http://localhost:8000/auth/callback  # After Entra login
ENTRA_IDP_NAME=microsoft                                # Provider name in DB
ENTRA_INTERNAL_TENANT_NAME=profile-service-test          # Default internal tenant

# Session & Security
SECRET_KEY=dev-secret-key-change-in-production           # Change in production!
SESSION_COOKIE_NAME=secops_session                       # Cookie name
SESSION_MAX_AGE_SECONDS=28800                            # 8 hours

# Frontend
FRONTEND_URL=http://localhost:5173                       # Redirect after login
```

## Configuring Entra ID

### 1. Create an App Registration

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to **Azure Active Directory > App registrations**
3. Click **New registration**
4. Enter an application name (e.g., "SecOps Profile Service")
5. Leave **Supported account types** as "Accounts in this organizational directory only"
6. Under **Redirect URI**, select **Web** and enter `http://localhost:8000/auth/callback`
7. Click **Register**

### 2. Get Your Credentials

After registration:
- Copy the **Application (client) ID** → `ENTRA_CLIENT_ID`
- Copy the **Directory (tenant) ID** → `ENTRA_TENANT_ID`

### 3. Create a Client Secret

1. In your app registration, go to **Certificates & secrets**
2. Click **New client secret**
3. Enter a description and expiry
4. Copy the secret value → `ENTRA_CLIENT_SECRET`
5. **Store safely!** You cannot view this again

### 4. Configure Redirect URI

Ensure the Redirect URI is registered:
1. Go to **Authentication** in your app registration
2. Under **Redirect URIs**, verify `http://localhost:8000/auth/callback` is listed
3. For production, add your production callback URL (e.g., `https://yourapp.com/auth/callback`)

### 5. Update Environment Variables

In `backend/.env`:

```bash
ENTRA_TENANT_ID=<Directory (tenant) ID from step 2>
ENTRA_CLIENT_ID=<Application (client) ID from step 2>
ENTRA_CLIENT_SECRET=<Client secret from step 3>
ENTRA_REDIRECT_URI=http://localhost:8000/auth/callback
```

### Why "Web" Application Type?

This integration uses the **Web** app type (not SPA) because:
- Backend performs the OAuth code exchange
- Backend has access to the client secret (never exposed to frontend)
- Frontend never handles tokens; only uses backend session cookies
- More secure for SPAs: tokens never leave the server

### Protected Routes

The following endpoints require a valid `secops_session` cookie:

- `GET /api/v1/tickets` - List tickets
- `GET /api/v1/tickets/{autotask_ticket_id}` - Get ticket details
- `GET /api/v1/tickets/stream/categorize` - Stream ticket categorization
- `GET /api/v1/auth/me` - Get current user info

Any request to these without a valid session will return `401 Unauthorized`.

## Troubleshooting

### Frontend shows "Sign in" but nothing happens

**Check:**
1. Backend is running on `http://localhost:8000` (or configured URL)
2. Browser console for JavaScript errors
3. Network tab shows request to `/auth/login`

### Entra login fails with "Invalid redirect URI"

**Check:**
1. `ENTRA_REDIRECT_URI` in `backend/.env` matches Azure portal exactly
2. No trailing slashes or extra parameters
3. HTTP vs HTTPS matches (both should be HTTP for localhost)

**Example:**
- ✅ `http://localhost:8000/auth/callback`
- ❌ `http://localhost:8000/auth/callback/`
- ❌ `https://localhost:8000/auth/callback`

### Backend returns 401 on `/api/v1/auth/me`

**Before login:**
- Correct - you don't have a session yet

**After login:**
- Check: Browser was redirected back to frontend after Entra callback
- Check: Look at backend logs for `/auth/callback` errors
- Check: Browser cookies include `secops_session`

**How to verify:**
```bash
curl -i -b "secops_session=COOKIE_VALUE" http://localhost:8000/api/v1/auth/me
```

### Backend returns 502 "Failed to reach Microsoft Entra ID"

**Likely causes:**
1. No internet connection
2. Firewall blocking `login.microsoftonline.com`
3. DNS resolution issues

**Check:**
```bash
curl https://login.microsoftonline.com/common/.well-known/openid-configuration
```

Should return JSON configuration without errors.

### Backend starts slowly

First run takes time due to:
- Downloading sentence-transformer model (`all-MiniLM-L6-v2`)
- Downloading spaCy models
- CUDA/torch initialization

Subsequent runs are faster once models are cached.

### Session not persisting after refresh

**Check:**
1. Frontend URL and backend cookies are on same domain/port
2. Cookie `SameSite` is `Lax` (allows same-site requests)
3. Cookie `HttpOnly` is enabled (can't be accessed by JavaScript)

**For different hosts:**
- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8000`
- Cookies work (same machine, different ports)

**For different domains:**
- May need CORS adjustments
- Requires `Secure` cookies (HTTPS)

### Profile not created on first login

**Check backend logs:**
1. Was `/auth/callback` reached?
2. Did token validation pass?
3. Did `resolve_entra_profile()` get called?

**If `ENTRA_INTERNAL_TENANT_NAME` tenant doesn't exist:**
- Backend auto-creates it on first login
- Check database: `SELECT * FROM tenant;`

## Security Considerations

### Client Secret Rotation

After initial testing:
1. Go to Azure portal > Your app registration > Certificates & secrets
2. Delete the old secret
3. Create a new one
4. Update `ENTRA_CLIENT_SECRET` in `backend/.env`
5. Restart backend

### Production Deployment

**Before going to production:**

1. **Enable HTTPS**
   - Set `SECURE=True` in cookie settings (not configurable via .env yet - code change needed)
   - Ensure backend runs on HTTPS
   - Update `ENTRA_REDIRECT_URI` to `https://yourdomain.com/auth/callback`

2. **Rotate `SECRET_KEY`**
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```
   - Use a strong, random value
   - Store securely (not in git!)

3. **Update environment for production**
   ```bash
   ENVIRONMENT=production
   DEBUG=False
   FRONTEND_URL=https://yourdomain.com
   ENTRA_REDIRECT_URI=https://yourdomain.com/auth/callback
   ```

4. **Backend Session Strategy**
   - Consider using a distributed cache (Redis) for sessions instead of JWT-only
   - Allows invalidating sessions immediately
   - Current JWT approach has no early logout mechanism

5. **Monitor & Audit**
   - Log all authentication events
   - Track profile creation
   - Monitor failed logins for security threats

### Data Privacy

This integration stores only:
- `tid` (Entra tenant ID)
- `oid` (Entra user ID)
- Display name (from Entra)
- Timestamps

**It does NOT store:**
- Emails (not extracted from token)
- Phone numbers
- Company data
- User identity tokens
- Access tokens (single-use, discarded after token exchange)

### Token Validation Details

The backend validates:
1. **Signature** - Token was signed by Microsoft (JWKS verification)
2. **Issuer** - Token came from your Entra tenant
3. **Audience** - Token is intended for your app (client ID matches)
4. **Expiration** - Token is not expired
5. **Required claims** - `tid`, `oid`, `iss` are present

If any validation fails, the request is rejected with `401 Unauthorized`.

## Extending & Customizing

### Adding Multiple Identity Providers

To support Google, Azure AD, or other providers:

1. Add new `identity_provider` rows to the database
2. Create new OAuth handler functions (similar to `exchange_code_for_identity`)
3. Add routes like `GET /auth/google/login` and `GET /auth/google/callback`
4. Modify `resolve_entra_profile()` to accept provider-agnostic parameters
5. Update frontend to show login buttons for each provider

### Changing Session Expiry

Modify `backend/app/config.py`:
```python
SESSION_MAX_AGE_SECONDS: int = 3600  # 1 hour instead of 8
```

Or override in `backend/.env`:
```bash
SESSION_MAX_AGE_SECONDS=3600
```

### Linking Multiple Entra Accounts

Users with multiple Entra identities can be linked to one profile:

Currently: One user = one profile (created on first login)

Enhancement:
1. Add UI endpoint `POST /api/v1/auth/link` to link additional identities
2. Check if user already has profile in different tenant
3. Create new `profile_identity` for same profile + different Entra account

### Email-Based Lookup

Currently uses `tid + oid` (tenant-scoped lookup).

To use email instead:
1. Extract `email` claim from Entra token (it's available)
2. Create email-based `profile_identity` lookups
3. Handle email domain organizational logic

### Adding Profile Data

To capture additional user info beyond display name:

1. Add columns to `profile` table (e.g., `email`, `department`)
2. Extract claims from Entra token (see claims list above)
3. Update `resolve_entra_profile()` to store them

### Customizing Auto-Provisioning

Current behavior: Creates profile in `ENTRA_INTERNAL_TENANT_NAME` tenant

To customize:
1. Add logic in `resolve_entra_profile()` to determine which tenant based on email domain
2. Or reject auto-provisioning: raise `PermissionError` if org is not whitelisted

### Session Validation on Protected Routes

Protected routes currently check for valid session cookie.

To add additional validation (e.g., tenant-specific checks):

```python
@router.get("/api/v1/tickets")
async def list_tickets(
    session: AuthenticatedSession = Depends(get_current_session),
    db: AsyncSession = Depends(get_db),
):
    # Check custom rules
    profile_service = ProfileService(db)
    profile = await profile_service.get_profile(...)

    if profile.status == "suspended":
        raise HTTPException(status_code=403, detail="Account suspended")

    # ... rest of handler
```

## References

- [Microsoft Entra ID Documentation](https://docs.microsoft.com/en-us/azure/active-directory/)
- [OAuth 2.0 Authorization Code Flow](https://docs.microsoft.com/en-us/azure/active-directory/develop/v2-oauth2-auth-code-flow)
- [OpenID Connect Protocol](https://openid.net/connect/)
- [FastAPI Security Documentation](https://fastapi.tiangolo.com/tutorial/security/)
- [Python-Jose JWT Library](https://python-jose.readthedocs.io/)
