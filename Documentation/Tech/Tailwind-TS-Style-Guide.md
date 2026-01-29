# UI Style & Structure Guide
### TypeScript + Tailwind CSS (No React, No Vite)

---

## 📌 Purpose of This Document

This document explains **exactly how styling works in this project**, focusing only on:
- `src/` TypeScript files
- Tailwind CSS usage via `className` strings

It is written for developers who:
- Have **general programming experience**
- Have **little or no CSS / Tailwind experience**
- Want a **clear mental model** of how the UI is built and styled

> ⚠️ You should **never edit `dist/`**.  
> All styling decisions live in **TypeScript (`src/`) only**.

---

## 🧠 Core Rule (Memorize This)

> **Styling is done ONLY with Tailwind class strings inside TypeScript.**

There are:
- ❌ No handwritten CSS rules
- ❌ No component stylesheets
- ❌ No editing `dist/styles.css`

Tailwind **generates CSS automatically** based on the class names it finds in `src/`.

---

## 📂 Where Tailwind Is Used

Tailwind classes appear only in UI-related files:

```
src/
├─ app.ts
├─ components/
│  ├─ TicketListContainer.ts
│  ├─ TicketCard.ts
│  └─ EllipsisMenu.ts
```

Files with **no styling at all**:
- `src/main.ts`
- `src/data/*`
- `src/lib/*`

---

## 🧩 How Styling Works (Step-by-Step)

1. A DOM element is created in TypeScript
2. A `className` string is attached
3. Tailwind scans that string
4. Matching CSS is generated automatically
5. Browser applies the styles

Example:
```ts
el("div", {
  className: "flex gap-4 p-4 bg-white rounded shadow"
});
```

Each word is a **single-purpose styling instruction**.

---

## 🎨 Tailwind Mental Model

Think of Tailwind as:

> **Predefined LEGO bricks for UI styling**

Each class:
- Does **one thing**
- Is predictable
- Never conflicts with others

You build visuals by **composing many small classes**.

---

## 🧱 Common Utility Categories

### Layout
- `flex` – horizontal layout
- `flex-col` – vertical layout
- `items-center` – vertical alignment
- `justify-between` – spread children apart

### Spacing
- `p-*` – padding
- `m*`, `mt-*`, `mb-*` – margin
- `gap-*` – spacing between children

### Size
- `w-*`, `h-*` – width / height
- `min-h-screen` – full viewport height

### Typography
- `text-xs/sm/lg/xl`
- `font-semibold`, `font-bold`
- `text-slate-*` – muted to dark text

### Visuals
- `bg-*` – background color
- `rounded-*` – border radius
- `border`, `border-*`
- `shadow`, `shadow-lg`

### Interaction
- `hover:*`
- `focus:*`
- `transition`

---

## 🗂 File-by-File Tailwind Usage

### `src/app.ts`
Responsible for:
- App layout
- Sidebar
- Header
- Ticket detail page

Key patterns:
```ts
"min-h-screen flex"
"bg-white border-b border-slate-200"
"rounded-xl shadow p-6"
```

---

### `src/components/TicketListContainer.ts`
Responsible for:
- Ticket list screen
- Sorting controls
- Collapsible list

Key patterns:
```ts
"flex justify-between items-center"
"bg-slate-300 rounded-xl p-6"
"flex flex-col gap-4"
```

---

### `src/components/TicketCard.ts`
Responsible for:
- Individual ticket cards

Key patterns:
```ts
"bg-white p-4 rounded shadow"
"hover:ring-2 hover:ring-slate-400"
"truncate"
"absolute bottom-3 right-3 rounded-full"
```

---

### `src/components/EllipsisMenu.ts`
Responsible for:
- “…” menu
- Dropdown interactions

Key patterns:
```ts
"relative"
"hover:bg-slate-100 focus:ring-2"
"absolute right-0 shadow-lg rounded-lg"
```

---

## ♻️ Reusable Design Patterns

### Card Pattern
```ts
"bg-white rounded shadow p-4"
```

### Button Pattern
```ts
"px-3 py-2 rounded hover:bg-slate-100"
```

### Layout Row Pattern
```ts
"flex items-center justify-between gap-3"
```

---

## ➕ Adding a New Screen (Checklist)

1. Create a new file in `src/components/` or `src/screens/`
2. Use existing layout & card patterns
3. Compose styles via Tailwind class strings
4. Do **not** write CSS
5. Do **not** edit `dist/`

---

## 🚫 What NOT To Do

- ❌ Do not edit `dist/styles.css`
- ❌ Do not write random CSS rules
- ❌ Do not duplicate styling logic
- ❌ Do not inline styles

---

## 🧭 Final Mental Model

- **TypeScript builds structure**
- **Tailwind class strings define appearance**
- **Tailwind generates CSS automatically**
- **`dist/` is output only**

If you only edit `src/`, you are doing it correctly.

---

## ✅ You Are Ready

If you can read this:

```ts
"flex gap-4 p-4 bg-white rounded shadow"
```

You now understand **how all styling in this project works**.
