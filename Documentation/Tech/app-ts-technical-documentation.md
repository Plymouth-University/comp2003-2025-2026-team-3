# Application Controller – Technical Documentation
## `src/app.ts`

This document describes the purpose, responsibilities, integration points, and engineering constraints for `src/app.ts`.

It is **not** a line-by-line commentary.  
It is intended to help developers understand **where this file fits**, **what belongs here**, and **how to extend it safely**.

---

## 1. Role in the System

`src/app.ts` is the **application controller** for the SPA.

It is responsible for:
- constructing the persistent UI shell (layout)
- coordinating routing and screen selection
- rendering the correct screen into the main content area
- reacting to navigation changes (URL changes)

If `src/main.ts` is the bootstrap entry point, `src/app.ts` is the “runtime brain”.

---

## 2. High-Level Responsibilities

### 2.1 Persistent Layout (UI Shell)
`src/app.ts` builds the app’s **outer frame**, typically:
- sidebar (left)
- header (top)
- content container (center)

This layout is designed to persist across navigation changes.

**Why:**
- avoids flicker
- avoids re-creating shared UI
- improves performance and perceived stability
- enables shared UI state (e.g., sidebar open/closed)

---

### 2.2 Routing Coordination
`src/app.ts` owns the routing logic.

Routing is responsible for:
- parsing the current route from the URL (hash routing)
- mapping the route to a screen
- calling the correct screen renderer
- handling unknown routes (fallback behavior if implemented)

`src/app.ts` should define the project’s **route vocabulary** (e.g., `#/`, `#/ticket/:id`).

---

### 2.3 Screen Rendering Lifecycle
`src/app.ts` manages the screen lifecycle by:
- clearing the main content container
- rendering a new screen into that container
- ensuring the shell remains intact

A “screen” in this project is a DOM-rendering function, typically in:
- `src/components/*` (current)
- or a future `src/screens/*` folder if introduced

---

### 2.4 Navigation Event Handling
`src/app.ts` attaches listeners for navigation changes, usually:
- `hashchange` (hash routing)
- optionally `popstate` if migrating to History API routing later

On navigation change:
- the route is re-evaluated
- the screen is re-rendered

---

## 3. Integration Points (What This File Links To)

### 3.1 Entry Link
`src/app.ts` is invoked from:
- `src/main.ts`

`main.ts` provides:
- the root DOM node
- the startup call (handoff point)

---

### 3.2 Component Links
`src/app.ts` should call screen renderers from:
- `src/components/TicketListContainer.ts`
- ticket detail renderer (implemented in `src/app.ts` or extracted)
- any future screen modules

Important rule:
- `src/app.ts` decides **which** component renders
- components decide **how** they render themselves

---

### 3.3 Data Links
`src/app.ts` may read from:
- `src/data/dummyTickets.ts` (mock data)
- later: real API clients in `src/api/*`

Best practice:
- treat data access as a dependency
- keep data selection minimal here
- push heavy transformation down into dedicated modules/services

---

### 3.4 Styling Links
Tailwind is used in this file only to style **high-level layout containers**.

Rule of thumb:
- layout-level Tailwind belongs here
- component-level Tailwind belongs in the component modules

---

## 4. What Belongs in `src/app.ts`

### ✅ DO
- define the app shell
- define route parsing and route-to-screen mapping
- keep a single main content container and swap screens within it
- provide navigation helpers (e.g., `navigateTo(route)`)
- add global UI scaffolding (toasts, modal root, etc.) if needed
- keep route handlers small and delegate to screens/components

---

## 5. What Does NOT Belong in `src/app.ts`

### ❌ DO NOT
- implement ticket card UI (belongs in `TicketCard.ts`)
- implement list sorting/collapse behavior (belongs in `TicketListContainer.ts`)
- implement dropdown menu behavior (belongs in `EllipsisMenu.ts`)
- embed business rules directly (extract to `lib/` or `services/`)
- build complex DOM trees inline (delegate to components/screens)
- create “utility/helper” functions that are used across files (put in `src/lib/`)

If `src/app.ts` is growing quickly, add structure:
- `src/router/*`
- `src/layouts/*`
- `src/screens/*`

---

## 6. Extending the App Safely

### 6.1 Adding a New Screen
Recommended flow:
1. create a new renderer module (e.g., `src/screens/Settings.ts`)
2. export a function that returns an `HTMLElement` (or renders into a container)
3. register a route mapping in `src/app.ts`
4. in the route handler: clear content container, then append the new screen

---

### 6.2 Adding a New Route
- define a stable route string
- keep parsing deterministic
- avoid dynamic class generation for Tailwind (Tailwind scanning requirement)
- keep route handlers thin

---

### 6.3 Error Handling Expectations
- missing route parameters should not crash silently
- unknown route should render a safe fallback (optional but recommended)
- missing data (e.g., ticket id not found) should render a user-facing message

---

## 7. Performance & Maintainability Notes

### 7.1 Avoid Rebuilding the Shell
Only the screen content should be replaced.  
If the shell is rebuilt on every route change, you will introduce:
- flicker
- lost state
- more DOM churn

### 7.2 Keep Global State Minimal
If you introduce state here, ensure it is:
- layout-level state (sidebar open, theme, etc.)
- or routing state

For cross-screen state, prefer:
- a dedicated store module (`src/store/*`)

---

## 8. Future Scalability Roadmap (Optional Guidance)

As screens grow beyond ~8–10, consider splitting responsibilities:

- `src/router/routes.ts` – route table and parsing
- `src/layouts/AppShell.ts` – sidebar/header shell creation
- `src/screens/*` – each screen module
- `src/store/*` – shared state and eventing
- `src/api/*` – network/data access

`src/app.ts` then becomes a thin coordinator.

---

## 9. Summary

`src/app.ts` is the application’s coordinator:
- it creates the persistent layout shell
- it decides which screen is currently active
- it handles navigation changes
- it swaps screen content without reloading the page

It should remain a **controller**, not a dumping ground for UI details or business logic.
