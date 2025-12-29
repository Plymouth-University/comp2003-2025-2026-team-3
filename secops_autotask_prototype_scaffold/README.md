# SecOps AI Ticket Intelligence Platform

A centralized Security Operations (SecOps) intelligence platform that ingests Autotask tickets, enriches them using AI-driven prioritisation and categorisation, and presents a unified dashboard for efficient security triage and response.

This system is designed as a read-only intelligence layer on top of Autotask, ensuring no modification of production Autotask data while enabling advanced analysis, prioritisation, and future automation.

## 🔗 Links

**Prototype / development stage**

- **Frontend (local):** http://localhost:5173
- **Backend API (local):** http://127.0.0.1:8000
- **API Documentation (Swagger):** http://127.0.0.1:8000/docs
- **Repository:** (add GitHub repository URL)

## 🛠️ Tech Stack

### Front-end

- **Framework:** React (Vite)
- **Language:** TypeScript
- **Styling:** CSS (Tailwind planned)
- **Runtime:** Node.js
- **Hosting (future):** Cloud static hosting

### Back-end

- **Language:** Python
- **Framework:** FastAPI
- **AI Processing:** Custom NLP & weighted classification
- **Data Source (MVP):** Simulated Autotask dataset (JSON)
- **Database (future):** SQLite → PostgreSQL
- **Hosting (future):** Cloud VM / internal infrastructure

## ⚠️ Development Environment

**Important Notes:**
- All team members are working on **Windows**
- Python packages are installed **globally**
- No virtual environments are used for this project

## 🚀 Quick Start

### Prerequisites (Windows)

- Python 3.11+
- Node.js 18+
- Git
- PowerShell or Command Prompt

### Local Development

#### Backend (FastAPI – Global Install)

```bash
pip install fastapi uvicorn pydantic requests python-dotenv
cd backend
uvicorn app.main:app --reload
```

- **API:** http://127.0.0.1:8000
- **Swagger Docs:** http://127.0.0.1:8000/docs

#### Frontend (React + TypeScript)

```bash
cd frontend
npm install
npm run dev
```

- **UI:** http://127.0.0.1:5173
- API requests are proxied automatically to the backend

## 📋 Development Workflow

### Git Branching Strategy

- `main` – Integration branch
- `prod` – Production-ready branch (future)
- `feature/*` – Feature-specific development branches

### Commit Message Convention

**Format:**
```
Area: Short description
```

**Examples:**
- `Backend: Add fake Autotask provider`
- `AI: Implement ticket priority scoring`
- `Frontend: Add category dashboard`
- `Docs: Update system documentation`

## 📁 Project Structure

```
secops-autotask-project/
├── README.md
├── backend/
│   ├── requirements.txt
│   ├── mock_autotask_server.py
│   ├── data/
│   │   └── tickets.json
│   └── app/
│       ├── main.py
│       ├── models.py
│       ├── providers/
│       │   └── fake_autotask.py
│       └── services/
│           └── ai_categoriser.py
└── frontend/
    ├── package.json
    ├── vite.config.ts
    ├── index.html
    └── src/
        ├── App.tsx
        ├── api.ts
        ├── types.ts
        └── main.tsx
```

## 🧠 System Architecture Overview

```
Autotask (real system – read only)
        ↓
Provider Layer (Fake → Real)
        ↓
Internal Ticket Model
        ↓
AI Classification & Prioritisation
        ↓
FastAPI Backend
        ↓
React SecOps Dashboard
```

**This architecture ensures:**
- Clean separation of concerns
- No modification of Autotask data
- Seamless transition from simulated to real Autotask API

## 🤖 How Toby Plugs in the AI

The AI integration point is intentionally isolated to allow rapid iteration without affecting the rest of the system.

### AI Integration File

```
backend/app/services/ai_categoriser.py
```

### Required Function Contract

Toby must implement (or replace) the following function:

```python
def categorise_ticket(title: str, description: str) -> dict:
    return {
        "category": "<category name>",
        "score": 0-100,
        "reason": "<short explanation>"
    }
```

### Key Rules

- Function signature must not change
- Output keys (`category`, `score`, `reason`) must remain consistent
- AI logic can be rule-based, NLP-based, or ML-based

### Why This Works

- The backend automatically calls this function for every ticket
- The frontend already expects this AI output
- No API routes or UI code need modification

This design allows AI improvements without system-wide refactoring.

## 🔄 How We Migrate to the Real Autotask API

The system is designed so that only one component changes during migration.

### Current State (MVP)
```
FakeAutotaskProvider → tickets.json
```

### Future State (Production)
```
RealAutotaskProvider → Autotask REST API
```

### Migration Steps

1. Create a new provider file:
   ```
   backend/app/providers/real_autotask.py
   ```

2. Implement authenticated REST calls to Autotask

3. Map Autotask API responses into the existing Ticket model

4. Swap provider usage in `main.py`

### What Does NOT Change

- AI logic
- API endpoints
- Frontend UI
- Ticket model
- Category logic

### Why This Is Safe

- Autotask remains read-only
- No AI data is written back to Autotask
- Internal database (future) stores all AI enrichment

## 🧪 Testing & Validation

### Backend Checks

- **`/health`** – Backend running status
- **`/api/categories`** – Category buckets
- **`/api/tickets`** – Tickets with AI output
- **`/api/tickets?category=Backup%20failed`** – Filtering functionality

### AI Validation

- Compare AI output with known ticket patterns
- Use `category_bucket_hint` (MVP only) to evaluate accuracy

## 🐛 Troubleshooting

### Backend fails to start

1. Confirm Python version:
   ```bash
   python --version
   ```

2. Ensure FastAPI and Uvicorn are installed globally:
   ```bash
   pip install fastapi uvicorn
   ```

3. Check port 8000 availability

### Frontend cannot reach backend

1. Confirm backend is running (check http://127.0.0.1:8000/docs)

2. Ensure Vite proxy is active

3. Check browser console for network errors

## 📌 Project Notes

- All ticket data is synthetic and Datto RMM–style
- No real customer or Autotask data is used
- Database integration is intentionally deferred
- Designed for scalability and enterprise-grade workflows