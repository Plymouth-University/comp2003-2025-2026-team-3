# Tailwind Configuration – Technical Documentation
### `tailwind.config.js`

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

## 3. Typical Structure

```js
export default {
  content: ["./src/**/*.{ts,html}"],
  theme: {
    extend: {}
  },
  plugins: []
};
```

---

## 4. `content` — Class Scanning

This tells Tailwind where to look for class names.

Rules:
- All UI files must be included
- Class names must be statically present
- Do not build class names dynamically

---

## 5. `theme.extend` — Design System

Used to add:
- brand colors
- spacing
- fonts
- breakpoints
- shadows

Always extend, never replace the default theme.

---

## 6. `plugins` — Optional Extensions

Plugins add new utilities or variants.

Use only when patterns repeat across many components.

---

## 7. What Not To Do

- Do not edit generated CSS
- Do not dynamically generate class names
- Do not override the entire theme

---

## 8. Build Pipeline Context

```
TypeScript → Tailwind Scan → PostCSS → styles.css
```

---

## 9. Version Control Rules

- Commit this file
- Review changes carefully
- Treat as infrastructure

---

## 10. Summary

This file controls Tailwind’s behavior globally and is critical for scalability.
