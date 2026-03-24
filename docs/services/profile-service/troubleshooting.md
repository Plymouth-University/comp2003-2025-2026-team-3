# Profile Service Troubleshooting

## Purpose

This runbook covers likely failure modes for the current profile service implementation.

Source of truth:

- `backend/app/routers/profiles.py`
- `backend/app/services/profile_service.py`
- `backend/app/repositories/profile_repository.py`
- `backend/app/database.py`
- `backend/app/config.py`

## Quick Checks

When a profile-service flow fails, check these first:

1. Is PostgreSQL running and reachable from `DATABASE_URL`?
2. Does the referenced tenant/profile/specialism ID actually exist?
3. Are the required query parameters present, especially `tenant_id`?
4. If auth is involved, are Entra settings configured correctly?
5. Is the target profile in `active` status for login-related flows?

## Symptom: `400 Tenant ... not found` when creating a profile

Likely cause:

- `ProfileService.create_profile(...)` verifies tenant existence before creation

Where to look:

- `backend/app/services/profile_service.py`
- `backend/app/repositories/profile_repository.py`

What to check:

- confirm the `tenant_id` in the request body
- confirm the tenant row exists in the database
- create the tenant first through `POST /api/v1/tenants` if needed

## Symptom: `404 Profile ... not found`

Likely causes:

- wrong `profile_id`
- wrong `tenant_id`
- profile exists in another tenant

Where to look:

- `GET /api/v1/profiles/{profile_id}`
- `PATCH /api/v1/profiles/{profile_id}`
- `POST /api/v1/profiles/{profile_id}/deactivate`

What to check:

- ensure `tenant_id` query parameter matches the profile's tenant
- verify the profile row exists
- verify the route is using the correct UUID

## Symptom: profile search returns no matches

Likely causes:

- search is case-normalized substring matching on `display_name_normalized`
- the expected display name may not be stored as assumed

Where to look:

- `ProfileRepository.search_profiles_by_name(...)`

What to check:

- use a substring of the current display name
- confirm `profile_display` rows exist
- verify the display name was updated as expected

## Symptom: Entra login fails with `403 Profile is not active`

Likely cause:

- `resolve_entra_profile(...)` explicitly blocks sign-in when a linked profile's `status` is not `active`

Where to look:

- `backend/app/services/profile_service.py`
- `backend/app/routers/auth.py`

What to check:

- inspect the linked profile status
- if the profile was intentionally deactivated, this is expected behavior
- if the profile should be allowed back in, the codebase currently has no dedicated reactivation endpoint

## Symptom: Entra login fails with `500 Internal Server Error` on a new machine

Likely causes:

- the teammate copied the backend `.env`, but the local PostgreSQL schema was never created
- the local `mydb` exists but does not yet contain tables such as `tenant`, `profile`, `identity_provider`, and `profile_identity`

Where to look:

- `backend/app/routers/auth.py`
- `backend/app/services/profile_service.py`
- `backend/alembic/versions/`

Why this happens:

- `resolve_entra_profile(...)` can create some rows on first login, such as the internal tenant, identity provider, and profile
- it cannot do that until the underlying tables already exist
- if the schema was never applied, the callback flow fails before local provisioning can finish

What to check:

- confirm PostgreSQL is running and `DATABASE_URL` points to the intended local database
- from `backend/`, run `alembic upgrade head`
- confirm tables now exist in `mydb`
- restart the backend and retry sign-in

Important operational note:

- this migration step is not something developers should run on every startup
- run it during first-time machine setup
- run it again only when the schema changes or when the local database has been recreated

## Symptom: Entra login creates unexpected users in one shared tenant

Likely cause:

- Entra provisioning currently uses `settings.ENTRA_INTERNAL_TENANT_NAME` as the local tenant lookup/create key

Where to look:

- `ProfileService.resolve_entra_profile(...)`
- `backend/app/config.py`

What to check:

- the configured value of `ENTRA_INTERNAL_TENANT_NAME`
- whether the current design intentionally uses a single internal tenant

## Symptom: `400 Failed to link identity`

Likely causes:

- duplicate `(idp_id, idp_tenant_subject)` value
- invalid referenced profile or tenant
- other database integrity failure

Where to look:

- `ProfileService.link_external_identity(...)`
- `IdentityRepository.link_profile_identity(...)`

What to check:

- whether that provider subject is already linked
- whether `profile_id`, `tenant_id`, and `idp_id` are valid

Why diagnosis is harder than it should be:

- the service catches broad exceptions and returns `False`, so the HTTP layer hides the specific database error

## Symptom: `400 Failed to assign specialism`

Likely causes:

- invalid profile or specialism ID
- duplicate assignment row
- tenant mismatch or foreign key failure

Where to look:

- `SpecialismService.assign_to_profile(...)`
- `SpecialismRepository.assign_specialism_to_profile(...)`

What to check:

- that the profile exists
- that the specialism exists
- that both belong to the intended tenant context
- that the assignment does not already exist

## Symptom: `/api/v1/auth/profile` returns `404`

Likely causes:

- the identity provider name does not exist
- the subject string does not match any linked profile

Where to look:

- `ProfileService.find_profile_by_identity(...)`
- `IdentityRepository.get_identity_provider_by_name(...)`
- `IdentityRepository.get_profile_by_identity(...)`

What to check:

- provider name, such as `microsoft`
- exact subject format stored for the user
- for Entra-created users, the subject format is `{entra_tenant_id}:{object_id}`

## Symptom: database writes appear partially committed

Likely cause:

- repository methods call `commit()` internally, so writes may commit before the outer request lifecycle completes

Where to look:

- `backend/app/repositories/profile_repository.py`
- `backend/app/database.py`

What to check:

- whether a multi-step flow expects all changes to roll back together
- whether a repository committed earlier than expected

## Known Implementation Gaps

These are not necessarily bugs, but they can surprise developers:

- profile routes are not guarded by session auth in `backend/app/routers/profiles.py`
- there is no audit trail for profile mutations
- there is no specialism removal endpoint
- there is no dedicated profile reactivation endpoint
- direct identity linking and specialism assignment expose only generic `400` errors on failure
