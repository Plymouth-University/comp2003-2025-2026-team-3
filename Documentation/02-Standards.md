# Project Standardisation & Engineering Procedures
### TypeScript + Tailwind SPA (No React / No Vite)

This document defines **standardised procedures and conventions** for developing, extending, and maintaining this codebase.

It is intentionally prescriptive. If you follow it:
- the project remains scalable as screens/features grow
- new developers can onboard quickly
- refactors are safer
- UI remains consistent

---

## 0) Guiding Principles

1. **Single source of truth**  
   Centralise shared rules (routes, UI patterns, status mappings, formatting) in one place.

2. **Consistency beats cleverness**  
   Prefer predictable patterns over “smart” abstractions.

3. **Edit source, not output**  
   Only edit `src/` and owned assets/docs. Never edit generated output (`dist/`) or vendor code (`node_modules/`).

4. **Small modules, clear ownership**  
   Each file owns one concept: a screen, a component, or a helper.

---

## 1) Approved Editing Zones

✅ Safe / expected to edit:
- `src/**`
- `README.md` and `docs/**`
- owned static assets (`src/assets/**` if present)

🚫 Do not edit:
- `dist/**`
- `node_modules/**`
- generated lock/caches (`*.tsbuildinfo`)

---

## 2) Required Project Structure

Use this folder layout (introduce missing folders as the app grows):

```
src/
├─ main.ts              # entry point only
├─ app.ts               # app controller: shell + routing
├─ screens/             # screen modules (1 file per screen)
├─ components/          # reusable UI pieces
├─ lib/                 # shared helpers/utilities (pure, reusable)
├─ data/                # mock data only (remove when backend exists)
├─ api/                 # backend client (fetch wrappers, endpoints)
├─ store/               # shared state (if/when needed)
└─ assets/              # owned icons/images
```

### Definition of "screen" vs "component"
- **Screen:** represents a route/page-level view (Ticket List, Ticket Detail, Settings).
- **Component:** reusable UI building block (TicketCard, Dropdown, Button).

Rule:
> Screens coordinate. Components render.

---

## 3) Routing & Screen Registration Standard

### 3.1 Route naming conventions
- Use kebab-case for route paths: `#/ticket/123`, `#/settings`
- Route segments should be stable and meaningful: `ticket`, `settings`, `reports`

### 3.2 One route = one screen module
Each route should map to exactly one screen module under `src/screens/`.

Example:
- `#/tickets` → `src/screens/TicketsScreen.ts`
- `#/ticket/:id` → `src/screens/TicketDetailScreen.ts`

### 3.3 Screen module interface (standard)
Every screen module must export **one** function:

```ts
export function renderXyzScreen(params: XyzParams): HTMLElement
```

Rules:
- returns a single root `HTMLElement`
- does not mutate global DOM except within its own subtree
- receives dependencies via parameters (data, callbacks), not imports from other screens

---

## 4) DOM Creation Standard (No raw DOM spaghetti)

### 4.1 Always use the DOM helper for element creation
Use `el(...)` (or the project’s standard helper) for creating elements.

✅ Preferred:
```ts
const card = el("div", { className: "p-4 bg-white rounded shadow" }, [...children]);
```

🚫 Avoid:
```ts
const div = document.createElement("div");
// dozens of property assignments...
```

### 4.2 Avoid `innerHTML` for UI rendering
Reason: security + maintainability (XSS risk and brittle markup).

Only use `innerHTML` when:
- you are rendering trusted static templates
- and you document why it is safe

---

## 5) Tailwind Styling Standard

### 5.1 Where Tailwind belongs
- Layout-level styling can live in `app.ts` / screens
- Component-level styling belongs in the component file
- Shared “design patterns” should be documented and reused

### 5.2 No dynamic Tailwind class generation
Tailwind scans static strings. Do not generate class names like `"bg-" + color`.

✅ Allowed (controlled selection):
```ts
const cls = priority === "high" ? "bg-red-500" : "bg-green-400";
```

🚫 Not allowed:
```ts
const cls = "bg-" + priorityColor;
```

### 5.3 Standard UI patterns (reuse these)
Define a small set of common patterns and stick to them:

**Card**
- `"bg-white rounded shadow p-4"`

**Panel**
- `"rounded-xl shadow p-6 border border-slate-200"`

**Primary button**
- `"px-3 py-2 rounded bg-slate-900 text-white hover:bg-slate-800"`

**Ghost button**
- `"px-3 py-2 rounded hover:bg-slate-100"`

**Row layout**
- `"flex items-center justify-between gap-3"`

If a new UI element resembles an existing pattern, reuse the same class bundle.

---

## 6) Naming Standards

### 6.1 Files
- Screens: `XyzScreen.ts`
- Components: `Xyz.ts` or `XyzComponent.ts` (pick one and keep consistent)
- Helpers: `xyz.ts` (lowercase file names)

### 6.2 Identifiers
- Functions: `camelCase` (`renderTicketListScreen`)
- Types/Interfaces: `PascalCase` (`Ticket`, `TicketStatus`)
- Constants: `UPPER_SNAKE_CASE` for global constants only
- DOM nodes: suffix with `El` (`rootEl`, `menuEl`, `contentEl`)

### 6.3 Avoid ambiguous names
Prefer:
- `ticketsByPriority`
- `sortedTickets`
- `isCollapsed`

Avoid:
- `data`
- `thing`
- `temp`
- `arr`

---

## 7) TypeScript Standards

### 7.1 Types first for shared data
Define shared data shapes once (and reuse):
- `Ticket`
- `TicketStatus`
- `Priority`

Do not duplicate shapes across files.

### 7.2 Avoid `any`
Use:
- union types
- generics
- `unknown` (then narrow)

### 7.3 Explicit return types for public functions
Any exported function should have an explicit return type.

---

## 8) State Management Standard

### 8.1 Screen-local state
State that affects only one screen belongs inside that screen module.

Examples:
- current sort mode
- collapsed/expanded state

### 8.2 Shared state (when needed)
When multiple screens need the same state:
- create a `src/store/` module
- use a minimal pub/sub or observable pattern
- keep state serialisable where possible

Do not store complex state in `app.ts` unless it is layout/routing state.

---

## 9) Data & Backend Integration Standard

### 9.1 Mock data policy
`src/data/` is allowed only for:
- prototyping UI
- demos
- tests

When backend is introduced:
- move data access to `src/api/`
- convert screens to call API client
- delete or isolate `src/data/`

### 9.2 API client standard
- centralise `fetch` wrappers (base URL, headers, auth)
- no direct `fetch` scattered across screens/components
- one module per endpoint group

---

## 10) AI Integration Standards (Practical)

AI features typically add:
- summarisation fields
- classification labels
- confidence scores
- suggested actions

Standards:
- AI output should be treated as **data**, not logic
- store AI results in `Ticket`-related fields or separate `AiInsight` types
- map AI labels to UI display via a central mapping file (like status mapping)

Never bake AI decisions directly into UI rendering.

---

## 11) Error Handling & UX

### 11.1 Fail fast in development
- missing root elements should throw
- invalid route params should show a clear screen-level error

### 11.2 User-facing errors
Screens should render safe fallbacks:
- "Ticket not found"
- "Something went wrong"
- "No data available"

---

## 12) Testing & Quality Gates (Lightweight)

Minimum expectations:
- run TypeScript typecheck before merging
- avoid committing build output
- keep screens/components small enough to review

Recommended:
- add basic unit tests for helpers in `src/lib/`
- add minimal integration tests for routing if the app becomes large

---

## 13) Code Review Checklist (Use this every PR)

- [ ] No changes in `dist/` or `node_modules/`
- [ ] New screen lives in `src/screens/` and is registered in routing
- [ ] DOM creation uses helper functions, not raw DOM boilerplate
- [ ] Tailwind classes are static strings (no dynamic generation)
- [ ] Shared logic extracted to `src/lib/` or `src/store/`
- [ ] Naming conventions followed (`*El`, `Screen`, etc.)
- [ ] Exported functions have explicit types
- [ ] No secrets committed (`.env` ignored)

---

## 14) Standard Procedure: Adding a New Screen

1. Create screen file: `src/screens/NewScreen.ts`
2. Export: `renderNewScreen(params): HTMLElement`
3. Add route mapping in `src/app.ts`
4. Use standard layout patterns (Card/Panel/Button)
5. Keep screen logic inside screen; push reusable pieces to `components/`
6. Commit only `src/` changes (no `dist/`)

---

## 15) Standard Procedure: Adding a New Reusable Component

1. Create `src/components/Xyz.ts`
2. Component accepts data + callbacks, returns `HTMLElement`
3. Use `el()` helper for DOM creation
4. Tailwind classes stay local to that component
5. No routing logic inside components
6. Document new UI pattern in the project style guide if it becomes common

---

## 16) Appendix: Definitions

**Infrastructure file:** config/tooling file that affects the entire build (edit rarely).  
**Generated output:** produced by build pipeline; never edited manually.  
**Screen:** route-level view.  
**Component:** reusable UI block.

---

## Final Rule

> If you’re unsure where something belongs:  
> **Screen coordinates → component renders → lib helps.**

