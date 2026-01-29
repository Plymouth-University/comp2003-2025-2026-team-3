# Workflow Rules (Project Policy)

These rules exist so we do not break the repo or block merges.

If you are unsure please ask Liam.

---

## 1) What each branch is for

### `development`
- Shared team branch for integration
- **Protected** (you cannot push directly)
- All work arrives here through Pull Requests

### `main`
- Final submission branch
- Only updated when we are ready to submit a stable version

### `documents`
- Documentation-only history branch
- **NO CODE is allowed on this branch**

### `feature/<task-name>`
- Your working branch for one task
- Short-lived: make it, finish it, merge it, delete it

✅ Good branch names:
- `feature/add-latency-logs`
- `feature/fix-ticket-detail`
- `feature/ui-settings-page`

❌ Bad branch names (do not do this):
- `feature-toby`
- `feature-khyati`
- `feature-liam`
(These get stale and cause conflicts.)

---

## 2) Golden rule: never push to development

If GitHub blocks you from pushing to development, that is correct.

You must:
1. create a feature branch  
2. push it  
3. open a PR into `development`

---

## 3) Pull Request rules

A PR must:
- Target `development`
- Be updated with the latest `development` before merging
- Have at least 1 approval

---

## 4) Commit message rules

Format:
```
Area: short message
```

Areas we use:
- `Front-End:`
- `Back-End:`
- `Docs:`
- `Chore:`

Examples:
- `Front-End: fix TicketDetail rendering`
- `Back-End: add timestamp latency logs`
- `Docs: add Git workflow guides`
- `Chore: remove unused folder`

---

## 5) One branch = one task

A feature branch should only contain work for a single task.

Do not mix tasks like:
- “UI improvements”
- “backend fixes”
- “documentation”
all inside the same branch.

If you need to do another task:
- finish + PR the first branch
- create a new feature branch for the next task
