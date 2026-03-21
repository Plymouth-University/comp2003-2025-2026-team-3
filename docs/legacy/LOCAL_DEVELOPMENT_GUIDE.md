# Local Development Guide

This guide is split into three parts:

1. Clean setup from the beginning
2. Normal run cheat sheet
3. Troubleshooting and where to find errors

## 1. Clean Setup From The Beginning

Use this section if you want a fully clean local start.

### Step 1: Go to the repo root

```bash
cd /home/liam/Documents/GitHub/comp2003-2025-2026-team-3
```

### Step 2: Stop any old processes

If you think old frontend or backend processes may still be running:

```bash
pkill -f "uvicorn app.main:app" || true
pkill -f "live-server --port=5173" || true
```

### Step 3: Remove old local installs if you want a full reset

Backend virtual environment:

```bash
rm -rf backend/.venv
```

Frontend packages and build output:

```bash
rm -rf frontend/node_modules
rm -rf frontend/dist
```

Optional Docker cleanup for a fresh database:

```bash
cd backend
docker compose down -v
cd ..
```

Warning:

- `docker compose down -v` deletes the local PostgreSQL volume and wipes the local database.

### Step 4: Start PostgreSQL

```bash
cd backend
docker compose up -d
cd ..
```

### Step 5: Set up the backend from scratch

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cpu
python -m spacy download en_core_web_sm
alembic upgrade head
cd ..
```

What this does:

- creates the Python virtual environment
- installs backend dependencies
- installs CPU-only PyTorch
- installs the spaCy English model
- applies the database schema

### Step 6: Set up the frontend from scratch

```bash
cd frontend
npm install
cd ..
```

### Step 7: Start the backend

Open terminal 1:

```bash
cd /home/liam/Documents/GitHub/comp2003-2025-2026-team-3/backend
./run_local.sh
```

Wait until you see:

- `Application startup complete`
- `Uvicorn running on http://0.0.0.0:8000`

### Step 8: Start the frontend

Open terminal 2:

```bash
cd /home/liam/Documents/GitHub/comp2003-2025-2026-team-3/frontend
./run_local.sh
```

### Step 9: Open the app

Open this in your browser:

```text
http://localhost:5173
```

### Step 10: Test sign-in

1. Click `Sign in with Microsoft`
2. Sign in with a user from your Entra tenant
3. You should be redirected back to `http://localhost:5173`

## 2. Normal Run Cheat Sheet

Use this section when everything has already been installed before.

### Start database

```bash
cd /home/liam/Documents/GitHub/comp2003-2025-2026-team-3/backend
docker compose up -d
```

### Start backend

In terminal 1:

```bash
cd /home/liam/Documents/GitHub/comp2003-2025-2026-team-3/backend
./run_local.sh
```

### Start frontend

In terminal 2:

```bash
cd /home/liam/Documents/GitHub/comp2003-2025-2026-team-3/frontend
./run_local.sh
```

### Open app

```text
http://localhost:5173
```

### Stop app

Press `Ctrl+C` in the backend terminal and frontend terminal.

To stop PostgreSQL too:

```bash
cd /home/liam/Documents/GitHub/comp2003-2025-2026-team-3/backend
docker compose down
```

## 3. Troubleshooting And Where To Find Errors

This section is for when the app does not load, login fails, or the UI shows a blank screen.

### Quick health checks

Check backend health:

```bash
curl -i http://localhost:8000/health
```

Expected:

- `200 OK`

Check unauthenticated auth response:

```bash
curl -i http://localhost:8000/api/v1/auth/me
```

Expected before login:

- `401 Unauthorized`

If you get a connection error instead, the backend is not running properly.

### Check whether PostgreSQL is running

```bash
cd /home/liam/Documents/GitHub/comp2003-2025-2026-team-3/backend
docker compose ps
```

If Postgres is not up:

```bash
docker compose up -d
```

### Check backend startup errors

Start the backend manually and watch the terminal:

```bash
cd /home/liam/Documents/GitHub/comp2003-2025-2026-team-3/backend
./run_local.sh
```

Important:

- backend errors usually appear directly in this terminal
- if the backend does not fully start, the frontend may show a warning or a blank-looking page

### Check frontend startup errors

Start the frontend manually and watch the terminal:

```bash
cd /home/liam/Documents/GitHub/comp2003-2025-2026-team-3/frontend
./run_local.sh
```

Important:

- TypeScript compile errors appear in this terminal
- frontend asset serving messages also appear here

### Check backend log files

The AI service writes logs into:

```text
/home/liam/Documents/GitHub/comp2003-2025-2026-team-3/backend/logs/ai_services
```

Useful commands:

Main log:

```bash
tail -n 100 backend/logs/ai_services/ai_services.log
```

Performance log:

```bash
tail -n 100 backend/logs/ai_services/ai_services_performance.log
```

Error log:

```bash
tail -n 100 backend/logs/ai_services/ai_services_errors.log
```

Watch logs live:

```bash
tail -f backend/logs/ai_services/ai_services.log
```

### Check Docker database logs

If you suspect database problems:

```bash
cd /home/liam/Documents/GitHub/comp2003-2025-2026-team-3/backend
docker compose logs postgres
```

Watch them live:

```bash
docker compose logs -f postgres
```

### Common problems

#### Problem: White screen or almost blank page

Most likely causes:

- backend is not running
- backend is still starting up
- Postgres is down
- frontend loaded before backend was available

Do this:

1. `docker compose ps`
2. `curl -i http://localhost:8000/health`
3. if backend is down, start backend first
4. refresh `http://localhost:5173`

#### Problem: Login button appears but sign-in fails

Check:

- Entra redirect URI is still `http://localhost:8000/auth/callback`
- `backend/.env` has the correct tenant ID, client ID, and client secret
- backend terminal shows no auth exceptions

#### Problem: Backend starts slowly

Reason:

- on first run, the AI model may download from Hugging Face
- after that, startup should be faster

#### Problem: Database schema errors

Re-run migrations:

```bash
cd /home/liam/Documents/GitHub/comp2003-2025-2026-team-3/backend
source .venv/bin/activate
alembic upgrade head
```

#### Problem: Frontend packages are broken

Reinstall frontend packages:

```bash
cd /home/liam/Documents/GitHub/comp2003-2025-2026-team-3/frontend
rm -rf node_modules dist
npm install
npm run build
```

#### Problem: Backend packages are broken

Rebuild backend environment:

```bash
cd /home/liam/Documents/GitHub/comp2003-2025-2026-team-3/backend
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cpu
python -m spacy download en_core_web_sm
```

### Security note

Your backend `.env` contains a live Entra client secret for local testing.

After testing:

1. rotate the secret in Microsoft Entra
2. update `backend/.env`
3. restart the backend
