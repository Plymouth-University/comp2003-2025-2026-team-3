# Tailwind Configuration – Technical Documentation
### `frontend/tailwind.config.js`

This document is developer-facing technical documentation for the Tailwind CSS configuration used in this project.

It explains:
- What `tailwind.config.js` is
- Why it exists
- Every major option and its use cases
- How developers should (and should not) modify it
- How it scales as the project grows

---

## 1. Purpose of `tailwind.config.js`

`tailwind.config.js` defines the Tailwind “language” your project speaks.

It does not style components directly.

Instead, it controls:
- which utility classes exist
- where Tailwind looks for class names
- how the design system is extended
- which plugins are enabled

---

## 2. Why This File Is Required

Tailwind works by scanning your source code and generating CSS only for the classes you use.

Without this file:
- Tailwind would not know which files to scan
- CSS output would be incorrect or missing
- customization would be impossible

---

## 3. Current Structure

```js
/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,html}"],
  theme: {
    extend: {},
  },
  plugins: [],
};
```

---

## 4. `content` — Class Scanning

This tells Tailwind where to look for class names. In this project, it is configured to scan `index.html` and all `.ts` and `.html` files within the `src` directory.

Rules:
- All UI files must be included in this array.
- Class names must be statically present in the files.
- Do not build class names dynamically (e.g., `const myClass = 'bg-red-' + '500';`).

---

## 5. `theme.extend` — Design System

This section is used to add or override parts of the default Tailwind theme. It's the right place for:
- brand colors
- custom spacing units
- new fonts
- additional breakpoints
- custom shadows

**Always extend, never replace the default theme unless you have a specific reason.**

---

## 6. `plugins` — Optional Extensions

Plugins add new utilities, variants, or components to Tailwind. Use them only when a pattern repeats across many components and cannot be solved with existing utilities.

---

## 7. What Not To Do

- **Do not edit generated CSS files** (like `styles.css`). Your changes will be overwritten.
- **Do not dynamically generate class names.** Tailwind's scanner cannot find them.
- **Do not override the entire theme object** unless you are intentionally replacing it completely. Use `extend` for additions.

---

## 8. Build Pipeline Context

The frontend build process uses this file to generate the final stylesheet:

```
TypeScript/HTML Files → Tailwind Scan (using config) → PostCSS → styles.css
```

---

## 9. Version Control Rules

- **Commit this file** to version control.
- **Review changes carefully.** A small change here can have a large impact.
- **Treat it as infrastructure.** Most developers should not need to edit it frequently.

---

## 10. Summary

This file controls Tailwind’s behavior globally and is critical for maintaining a consistent and scalable design system. Changes should be made thoughtfully and with an understanding of their project-wide impact.
