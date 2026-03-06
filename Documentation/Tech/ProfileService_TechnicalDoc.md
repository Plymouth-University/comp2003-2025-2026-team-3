
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
- **PROFILE:** One Tenant has many Profiles.  
- **SPECIALISM:** One Tenant defines many Specialisms.

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
- **PROFILE_IDENTITY:** To map back to Entra ID.  
- **PROFILE_SPECIALISM:** To track the analyst's skills.

---

## 3. IDENTITY_PROVIDER

**Purpose:**  
A lookup table defining valid external authentication sources (e.g., Microsoft Entra ID, Okta).

| Attribute | Type | Function / Purpose |
|---|---|---|
| idp_id | Smallint (PK) | Unique ID for the provider. |
| idp_name | Text | Name of the provider (e.g., "EntraID"). |

**Links to**
- **PROFILE_IDENTITY:** Provides the context for the external mapping.

---

## 4. PROFILE_IDENTITY

**Purpose:**  
The "Bridge" table. It maps a local `profile_id` to an external IDP's unique user identifier. This allows a user to log in via Entra ID and be recognized by your service.

| Attribute | Type | Function / Purpose |
|---|---|---|
| profile_identity_id | UUID (PK) | Unique record for this specific identity mapping. |
| idp_tenant_subject | Text | The composite key (e.g., `tid:oid`) from Entra ID. |
| last_login_at | Timestamptz | Tracks user activity for security monitoring. |

**Links to**
- **IDENTITY_PROVIDER:** Identifies which service issued the credential.  
- **PROFILE:** Connects the external login to the internal profile.

---

## 5. SPECIALISM

**Purpose:**  
Defines the expertise categories available within the SOC (e.g., "Malware Analysis"). This is managed locally in your service, not in Entra ID.

| Attribute | Type | Function / Purpose |
|---|---|---|
| specialism_id | UUID (PK) | Unique identifier for the skill. |
| specialism_key | Text | Constant slug used in code logic (e.g., `tier_3_ir`). |
| specialism_name | Text | Display name for the UI (e.g., "Incident Response L3"). |
| is_active | Boolean | Allows retiring specialisms without deleting historical data. |

**Links to**
- **TENANT:** Allows each tenant to have their own custom skill tree.  
- **PROFILE_SPECIALISM:** Maps these skills to specific analysts.

---

## 6. PROFILE_SPECIALISM

**Purpose:**  
An associative table (link entity) that assigns skills to analysts and tracks their proficiency.

| Attribute | Type | Function / Purpose |
|---|---|---|
| profile_id | UUID (FK) | The analyst being assigned the skill. |
| specialism_id | UUID (FK) | The skill being assigned. |
| proficiency_level | Text | Skill depth (e.g., Junior, Senior, Expert). |
| assigned_by_profile_id | UUID (FK) | Audit trail: which Lead Analyst verified this skill. |

**Links to**
- **PROFILE:** The user receiving the skill.  
- **SPECIALISM:** The skill definition.

---

## 7. PROFILE_DISPLAY & PROFILE_AVATAR

**Purpose:**  
Handles user-facing personalization. These are 1:1 extensions of the Profile to keep the core table slim.

| Table | Attribute | Purpose |
|---|---|---|
| DISPLAY | display_name | The user's preferred name in the SOC dashboard. |
| AVATAR | avatar_source | Indicates if using a preset or an upload. |
| AVATAR | avatar_preset_id | FK to the AVATAR_PRESET gallery. |

---

## Profile Database ERD

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

---

## Sequence Diagram

sequenceDiagram

participant API
participant ProfileService
participant ProfileDB

API->>ProfileService: ResolveProfile(tid, oid, name)

ProfileService->>ProfileDB: Lookup profile_identity by subject

alt First Login (Not Found)

ProfileService->>ProfileDB: BEGIN TRANSACTION
ProfileService->>ProfileDB: Insert PROFILE
ProfileService->>ProfileDB: Insert PROFILE_IDENTITY
ProfileService->>ProfileDB: Insert PROFILE_DISPLAY
ProfileService->>ProfileDB: Insert PROFILE_AVATAR
ProfileService->>ProfileDB: Insert PROFILE_SPECIALISM (optional defaults)
ProfileService->>ProfileDB: COMMIT

ProfileService-->>API: profile_id

else Profile Exists

ProfileService-->>API: profile_id

end


1. API calls **ProfileService** to resolve profile.
2. **ProfileService** queries profile from the **Profile DB**.
3. If the profile is not found, a new profile will be created and the new `profile_id` returned to the API.
4. If the profile is found, the existing `profile_id` is returned.

---

## Login and Profile Registration Sequence Diagram

sequenceDiagram

participant Browser
participant Frontend
participant Backend
participant Gateway
participant ProfileService
participant ProfileDB

Browser->>Frontend: Click "Sign In"

Frontend->>Backend: OAuth callback
Backend->>Gateway: Call API with bearer token

Gateway->>ProfileService: ResolveProfile(tid, oid, name)

ProfileService->>ProfileDB: SELECT profile_identity

alt Profile Exists

ProfileService->>ProfileDB: UPDATE last_login_at
ProfileService-->>Gateway: profile_id

else First Login

ProfileService->>ProfileDB: BEGIN TRANSACTION
ProfileService->>ProfileDB: INSERT profile
ProfileService->>ProfileDB: INSERT profile_identity
ProfileService->>ProfileDB: INSERT profile_display
ProfileService->>ProfileDB: INSERT profile_specialism (defaults)
ProfileService->>ProfileDB: COMMIT

ProfileService-->>Gateway: profile_id

end

Gateway-->>Backend: profile_id
Backend-->>Frontend: Session established
