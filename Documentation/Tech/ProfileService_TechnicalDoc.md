
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

*(Diagram referenced in original document)*

---

## Sequence Diagram

1. API calls **ProfileService** to resolve profile.
2. **ProfileService** queries profile from the **Profile DB**.
3. If the profile is not found, a new profile will be created and the new `profile_id` returned to the API.
4. If the profile is found, the existing `profile_id` is returned.

---

## Login and Profile Registration Sequence Diagram

*(Diagram referenced in original document)*
