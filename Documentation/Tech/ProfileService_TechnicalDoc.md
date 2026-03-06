
# Profile Service Technical Documentation

**System:** Security Operations Profile Service  
**Architecture:** Multi-tenant, JIT Provisioning  

---

## 1. TENANT

**Purpose:**  
The root entity for multi-tenancy. It ensures logical data isolation between different organizations or IT departments using the SOC extension.

| Attribute | Type | Function / Purpose |
|---|---|---|
| tenant_id | UUID (PK) | Unique identifier for the organization. |
| tenant_name | Text | Human-readable name of the company/department. |
| created_at | Timestamptz | Audit trail for when the tenant was onboarded. |

**Links to**
- PROFILE: One Tenant has many Profiles.
- SPECIALISM: One Tenant defines many Specialisms.

---

## 2. PROFILE

**Purpose:**  
The central identity record within the SOC extension. It represents a "User" but is decoupled from the external Auth provider to allow for internal state management (like deactivation reasons).

| Attribute | Type | Function / Purpose |
|---|---|---|
| profile_id | UUID (PK) | Primary internal reference for the user. |
| tenant_id | UUID (FK) | Links the user to their specific organization. |
| status | Text | Current state (e.g., active, deactivated, pending). |
| deactivated_at | Timestamptz | Recorded time for security offboarding. |
| deactivated_reason | Text | Context for why access was revoked (important for SOC audits). |

**Links to**
- PROFILE_IDENTITY: To map back to Entra ID.
- PROFILE_SPECIALISM: To track the analyst's skills.

---

## 3. IDENTITY_PROVIDER

**Purpose:**  
A lookup table defining valid external authentication sources (e.g., Microsoft Entra ID, Okta).

| Attribute | Type | Function / Purpose |
|---|---|---|
| idp_id | Smallint (PK) | Unique ID for the provider. |
| idp_name | Text | Name of the provider (e.g., "EntraID"). |

**Links to**
- PROFILE_IDENTITY: Provides the context for the external mapping.

---

## 4. PROFILE_IDENTITY

**Purpose:**  
The bridge table that maps a local profile_id to an external IDP user identifier.

| Attribute | Type | Function / Purpose |
|---|---|---|
| profile_identity_id | UUID (PK) | Unique record for this identity mapping. |
| idp_tenant_subject | Text | Composite key from Entra ID (e.g., tid:oid). |
| last_login_at | Timestamptz | Tracks user activity for security monitoring. |

**Links to**
- IDENTITY_PROVIDER: Identifies which service issued the credential.
- PROFILE: Connects the external login to the internal profile.

---

## 5. SPECIALISM

**Purpose:**  
Defines expertise categories available within the SOC (e.g., Malware Analysis).

| Attribute | Type | Function / Purpose |
|---|---|---|
| specialism_id | UUID (PK) | Unique identifier for the skill. |
| specialism_key | Text | Constant slug used in code logic (e.g., tier_3_ir). |
| specialism_name | Text | Display name for the UI (e.g., Incident Response L3). |
| is_active | Boolean | Allows retiring specialisms without deleting historical data. |

**Links to**
- TENANT: Each tenant can define their own skill tree.
- PROFILE_SPECIALISM: Maps skills to analysts.

---

## 6. PROFILE_SPECIALISM

**Purpose:**  
Associative table assigning skills to analysts and tracking proficiency.

| Attribute | Type | Function / Purpose |
|---|---|---|
| profile_id | UUID (FK) | Analyst receiving the skill. |
| specialism_id | UUID (FK) | Skill assigned. |
| proficiency_level | Text | Skill depth (Junior, Senior, Expert). |
| assigned_by_profile_id | UUID (FK) | Lead analyst who verified the skill. |

**Links to**
- PROFILE
- SPECIALISM

---

## 7. PROFILE_DISPLAY & PROFILE_AVATAR

**Purpose:**  
Handles user-facing personalization. These are 1:1 extensions of the Profile to keep the core table slim.

| Table | Attribute | Purpose |
|---|---|---|
| DISPLAY | display_name | Preferred display name in SOC dashboard |
| AVATAR | avatar_source | Indicates preset or uploaded avatar |
| AVATAR | avatar_preset_id | FK to avatar preset gallery |

---

# Profile Database ERD

```mermaid
erDiagram

TENANT {
    uuid tenant_id PK
    text tenant_name
    timestamptz created_at
}

PROFILE {
    uuid profile_id PK
    uuid tenant_id FK
    text status
    timestamptz deactivated_at
    text deactivated_reason
}

IDENTITY_PROVIDER {
    smallint idp_id PK
    text idp_name
}

PROFILE_IDENTITY {
    uuid profile_identity_id PK
    text idp_tenant_subject
    timestamptz last_login_at
}

SPECIALISM {
    uuid specialism_id PK
    text specialism_key
    text specialism_name
    boolean is_active
}

PROFILE_SPECIALISM {
    uuid profile_id FK
    uuid specialism_id FK
    text proficiency_level
    uuid assigned_by_profile_id
}

PROFILE_DISPLAY {
    uuid profile_id PK
    text display_name
}

PROFILE_AVATAR {
    uuid profile_id PK
    text avatar_source
    uuid avatar_preset_id
}

TENANT ||--o{ PROFILE : owns
TENANT ||--o{ SPECIALISM : defines

PROFILE ||--o{ PROFILE_IDENTITY : mapped_to
IDENTITY_PROVIDER ||--o{ PROFILE_IDENTITY : issued_by

PROFILE ||--o{ PROFILE_SPECIALISM : has
SPECIALISM ||--o{ PROFILE_SPECIALISM : assigned

PROFILE ||--|| PROFILE_DISPLAY : has
PROFILE ||--|| PROFILE_AVATAR : has
```

---

# Sequence Diagram — Profile Resolution

```mermaid
sequenceDiagram

participant API
participant ProfileService
participant ProfileDB

API->>ProfileService: ResolveProfile(tid, oid)

ProfileService->>ProfileDB: Lookup profile_identity

alt Profile not found
ProfileService->>ProfileDB: INSERT profile
ProfileService->>ProfileDB: INSERT profile_identity
ProfileService-->>API: Return new profile_id
else Profile exists
ProfileService-->>API: Return existing profile_id
end
```

---

# Sequence Diagram — Login and Profile Registration

```mermaid
sequenceDiagram

participant Browser
participant Frontend
participant Backend
participant API
participant ProfileService
participant ProfileDB

Browser->>Frontend: Sign In
Frontend->>Backend: OAuth callback
Backend->>API: Request with bearer token

API->>ProfileService: ResolveProfile(tid, oid)

ProfileService->>ProfileDB: Check profile_identity

alt Existing profile
ProfileService->>ProfileDB: Update last_login_at
ProfileService-->>API: profile_id
else First login
ProfileService->>ProfileDB: Create profile
ProfileService->>ProfileDB: Create profile_identity
ProfileService->>ProfileDB: Create display/avatar
ProfileService-->>API: new profile_id
end

API-->>Backend: profile_id
Backend-->>Frontend: session established
```
