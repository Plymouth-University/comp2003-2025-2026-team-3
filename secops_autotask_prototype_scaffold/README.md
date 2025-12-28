# SecOps Autotask Prototype (Backend + Frontend)

This scaffold includes:
- FastAPI backend serving **100** Datto RMM-style SecOps tickets (fake data)
- A simple built-in AI categoriser (keyword-based) for the UI buckets
- React + TypeScript frontend that calls the backend

## Backend quick start

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Backend: http://127.0.0.1:8000  
Docs: http://127.0.0.1:8000/docs

## Frontend quick start

```bash
cd frontend
npm install
npm run dev
```

Frontend: http://127.0.0.1:5173

Vite proxies `/api` to the backend automatically.
