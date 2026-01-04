# Installation, Run & Verification Guide

This guide explains **exactly how to install, run, and verify** the SecOps Autotask AI Ticketing System on a fresh machine.

It assumes:
- No Python virtual environment
- Global Python & Node installations
- Windows (PowerShell)  
  (macOS & Linux equivalents are very similar)

---

## 📦 Installation Guide

### 1️⃣ Backend Setup (Python + AI)

Navigate to the backend folder:

```powershell
cd backend
```

Run the setup script:

```powershell
.\setup.ps1
```

### What this does
- Updates `pip`
- Installs all **required Python dependencies**
- Downloads the required **spaCy NLP model**

If the setup script is unavailable, run manually:

```powershell
python -m pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

---

### 2️⃣ Frontend Setup (TypeScript + Tailwind)

Navigate to the frontend folder:

```powershell
cd frontend
```

Install frontend dependencies **using the lockfile**:

```powershell
npm ci
```

This guarantees all teammates install **exactly the same frontend dependencies**.

---

## ▶️ Run Guide

> ⚠️ Always start the **backend first**, then the frontend.

---

### Backend (choose ONE option)

#### Option A (recommended)
```powershell
python -m uvicorn app.main:app --reload
```

#### Option B (FastAPI CLI – optional)
```powershell
python -m fastapi dev app/main.py
```

### Backend access points

- **Swagger UI (primary interface):**  
  ```
  http://127.0.0.1:8000/docs
  ```

- Base API URL (used by frontend):  
  ```
  http://127.0.0.1:8000
  ```

> ℹ️ The backend does **not** serve a homepage at `/`.  
> Swagger (`/docs`) is the intended entry point for manual inspection and testing.

---

### Frontend

Open a **new terminal window**, then run:

```powershell
npm run dev
```

Frontend runs at:
```
http://127.0.0.1:5173
```

---

## ✅ Verification Guide

### Backend Verification

Open the following in your browser:

- **Swagger UI (recommended first check)**  
  ```
  http://127.0.0.1:8000/docs
  ```

- Health check  
  ```
  http://127.0.0.1:8000/health
  ```

- AI-enriched tickets endpoint  
  ```
  http://127.0.0.1:8000/api/tickets
  ```

All endpoints should return valid responses (no 500 errors).

---

### Frontend Verification

Open in your browser:

```
http://127.0.0.1:5173
```

You should see:
- Ticket list UI
- Tickets categorised by AI
- No console or network errors

---

## 🧪 Notes & Expected Behaviour

- The backend **does not serve content at `/`**
- Swagger (`/docs`) is the primary backend interface
- The frontend **requires the backend** to be running
- AI models may take longer to load on first run
- Subsequent starts are much faster

---

## 🧠 Recommended Versions

- **Python:** 3.12.x (most stable for AI dependencies)
- **Node.js:** 18+

---

## ✔️ Expected Workflow (TL;DR)

```powershell
# Backend
cd backend
.\setup.ps1
python -m uvicorn app.main:app --reload

# Frontend (new terminal)
cd frontend
npm ci
npm run dev
```

If all steps pass, the project is fully installed and operational.
