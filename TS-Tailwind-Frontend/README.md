# My UI (Vanilla TS + Tailwind)

This project rewrites the UI from the provided folder into **vanilla TypeScript + Tailwind CSS** (no React, no Vite).

## Requirements
- Node.js 18+ recommended

## Install
```bash
npm install
```

## Dev (watch TS + Tailwind + static server)
```bash
npm run dev
```
Then open the URL shown by `live-server` (default http://127.0.0.1:5173).

## Build
```bash
npm run build
```

Output:
- `dist/main.js` (compiled TypeScript)
- `dist/styles.css` (Tailwind build)
- `dist/assets/*` (copied images)
