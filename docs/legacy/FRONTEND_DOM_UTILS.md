# DOM Utilities – Technical Documentation
## `src/shared/lib/dom.ts`

This document describes the purpose, responsibilities, integration points, and safe usage rules for `src/shared/lib/dom.ts`.

It is intended as a **developer reference** (not a line-by-line code walkthrough).

---

## 1. Role in the System

`src/shared/lib/dom.ts` is the project’s **DOM utility layer**.

It exists to provide:
- a consistent way to create DOM elements
- a small abstraction over repetitive DOM boilerplate
- safer, cleaner UI rendering code inside `src/pages/*` and `src/app/App.ts`

If this project had a UI framework, this file would be less necessary.  
Because this project is **framework-free**, `dom.ts` serves as the lightweight “UI helper toolkit”.

---

## 2. Why Developers Should Be Careful Editing It

Most UI-related files depend on this module.

Changing its behavior can:
- break rendering across the entire app
- introduce subtle bugs (event listeners, attributes, child order)
- cause accessibility regressions

Rule of thumb:

> **Most developers should treat this file as infrastructure.  
> Edit it only when you have a clear, system-wide need.**

---

## 3. Responsibilities

`src/shared/lib/dom.ts` provides the following helpers.

### 3.1 Element Creation Helper: `el()`
The `el()` function:
- creates a DOM element by tag name (e.g., `"div"`, `"button"`)
- applies properties such as:
  - `className`
  - `textContent`
  - attributes (like `type`, `href`, `alt`)
- appends children in a consistent order

This gives you a single standard way to build UI elements across the codebase.

### 3.2 Date Formatting Helper: `formatDueDate()`
The `formatDueDate()` function provides a simple and stable way to format ISO date strings. Currently, it returns the date part of the ISO string.

---

## 4. Integration Points (Who Uses This)

### 4.1 Used By
- `src/app/App.ts` — building the shell layout and swapping screens
- `src/pages/*` — for creating page content
- `src/components/*` — for creating component DOM

### 4.2 Why This Matters
Because all UI is DOM-built, this module sits on the “hot path” of nearly every render.

---

## 5. Tailwind Interaction (Important)

Tailwind usage in this project happens by assigning class strings to elements, usually via:

- `className: "..."` in an element creation call

`dom.ts` is the mechanism that applies these classes to actual DOM nodes.

### Key rule
Tailwind **requires class names to be statically detectable** by its scanner.

So developers should avoid patterns like:
- dynamically concatenating class names from arbitrary strings
- creating class names based on user input

Preferred pattern:
- explicit, static class strings
- or controlled conditional selection (e.g., selecting from a small known set)

---

## 6. Safe Usage Guidelines (Do / Don’t)

### ✅ DO
- use `el()` for all UI DOM creation to stay consistent
- keep element creation calls small and readable
- pass children as actual nodes, not raw HTML strings
- attach event handlers via `addEventListener` after creation
- rely on this utility to reduce duplication, not to hide complexity

### ❌ DON’T
- insert raw HTML using `innerHTML` for UI rendering (XSS risk + harder to maintain)
- build giant nested trees in one statement; split into small helpers/components
- add app-specific UI logic here (this is a shared utility layer)
- silently ignore invalid arguments (either handle or fail loudly)

---

## 7. Error Handling Expectations

This module should behave predictably.

Good patterns:
- throw when invalid tag names or invalid children are passed
- fail early if required attributes are missing (optional)
- never swallow errors that would otherwise be visible during development

---

## 8. Extending `dom.ts` (When It’s Appropriate)

Add new helpers only when:
- a pattern repeats across multiple components
- it reduces boilerplate significantly
- it does not hide important logic

Good examples of additions:
- `icon(src, alt, className)` builder
- `button(label, className, onClick)` factory
- `mount(root, node)` helper

Bad examples:
- ticket-specific helpers
- routing logic
- data transformations

---

## 9. Performance Notes

DOM operations can be expensive if done carelessly.

Guidelines:
- minimize repeated DOM mutations in loops (build nodes first, then append)
- prefer `document.createDocumentFragment()` for large batches (optional)
- avoid layout thrashing (reading layout properties while writing styles)

This project is currently small; these optimizations become relevant when screens become large.

---

## 10. Summary

`src/shared/lib/dom.ts` is an infrastructure module that provides:
- consistent element creation
- safer rendering patterns
- reduced boilerplate in UI components

Most developers should:
- understand how to use it
- avoid modifying it unless necessary
- treat it as a stable foundation for the SPA UI

