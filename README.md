# SecOps Autotask AI Ticketing System

> **An end‑to‑end security operations prototype combining AI‑driven ticket categorisation with a modern TypeScript + Tailwind frontend.**

---

## ✨ Project Overview

This project is a **full‑stack prototype** designed to demonstrate how **AI‑assisted ticket categorisation** can be integrated into a modern SecOps workflow.

It consists of:

- 🧠 **AI‑powered backend** (FastAPI + NLP models)
- 🖥️ **Lightweight frontend SPA** (Vanilla TypeScript + Tailwind CSS)
- 🔗 **Clear separation of concerns** between data ingestion, AI processing, and UI rendering
- 🚫 **No React, no Vite runtime, no frontend frameworks**

The frontend **never categorises tickets itself** — all intelligence comes from the backend AI pipeline.

---

## 🧩 Architecture Overview

```
Raw Tickets
   ↓
Fake Autotask Provider
   ↓
AI Categoriser (Sentence Transformers + spaCy)
   ↓
FastAPI (/api/tickets)
   ↓
TypeScript SPA (Tailwind UI)
```

### Key Principle
> **AI decisions live exclusively in the backend.**  
> The frontend is a pure consumer of AI‑enriched data.

---

## 📁 Project Structure

```
secops_autotask_prototype_scaffold/
├─ backend/
│  ├─ app/
│  │  ├─ main.py              # FastAPI entry point
│  │  ├─ providers/           # Ticket sources (mock Autotask)
│  │  ├─ services/            # AI categorisation logic
│  │  └─ models/              # Data models
│  │
│  └─ requirements.txt
│
├─ frontend/
│  ├─ src/
│  │  ├─ main.ts              # Frontend entry point
│  │  ├─ app.ts               # SPA controller
│  │  ├─ components/          # UI components
│  │  ├─ lib/                 # DOM helpers & utilities
│  │  └─ assets/
│  │
│  ├─ index.html
│  └─ tailwind.config.js
│
└─ README.md
```

---

## 🧠 Backend (FastAPI + AI)

### Technologies
- **FastAPI** – REST API framework
- **Sentence Transformers** – semantic similarity & embeddings
- **spaCy** – NLP preprocessing
- **Python 3.12+ recommended**

### Key Endpoints
| Endpoint | Description |
|--------|------------|
| `/health` | Service health check |
| `/api/categories` | Available AI categories |
| `/api/tickets` | Tickets enriched with AI categorisation |

Each ticket returned includes:
- AI‑assigned category
- Confidence score
- Original ticket metadata

---

## 🖥️ Frontend (TypeScript + Tailwind)

### Technologies
- **Vanilla TypeScript**
- **Tailwind CSS**
- **No frameworks**
- **SPA architecture**

### Design Goals
- Fast load time
- Framework‑free
- Explicit DOM control
- Easy extensibility
- Screen‑based organisation

### Styling Approach
- All styling via **Tailwind utility classes**
- No handwritten CSS rules
- Consistent UI patterns (cards, panels, lists)

---

## ▶️ How to Run (No Virtual Environment)

### Prerequisites
- Python 3.12+
- Node.js 18+

---

### 1️⃣ Backend

```bash
cd backend
pip install fastapi uvicorn sentence-transformers spacy
python -m spacy download en_core_web_sm
python -m uvicorn app.main:app --reload
```

Backend runs at:
```
http://127.0.0.1:8000
```

---

### 2️⃣ Frontend (new terminal)

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at:
```
http://127.0.0.1:5173
```

---

## 🔒 Key Engineering Decisions

- **No frontend frameworks** → clarity over abstraction
- **AI logic isolated to backend** → correctness & security
- **Explicit DOM construction** → predictable rendering
- **Static Tailwind classes** → build‑time safety
- **SPA routing** → scalable UI without reloads

---

## 🚀 Extending the Project

This architecture is intentionally scalable:

- Replace fake Autotask provider with real API
- Add authentication layer
- Add ticket detail screens
- Introduce persistent storage
- Swap AI models without frontend changes
- Add role‑based UI views

---

## 🧪 Known Limitations (Prototype Scope)

- Uses mock ticket data
- AI models load at runtime (cold start cost)
- No persistence layer
- No authentication

These are **intentional** for a prototype environment.

---

## 📜 License

Educational / prototype use.

---

## 🧠 Final Note

This project demonstrates that:

> **Modern, scalable frontends do not require heavy frameworks**  
> and **AI systems must be architecturally isolated from UI concerns**.

Both principles are enforced throughout this codebase.

---

*Built for clarity, maintainability, and technical assessment.*
