# Local Run Start To Finish

This is the minimum path to run the software locally and test the Microsoft Entra ID login through the UI.

## What this starts

- PostgreSQL on `localhost:5432`
- Backend API on `http://localhost:8000`
- Frontend UI on `http://localhost:5173`

## One-time setup

From the repo root:

```bash
cd /home/liam/Documents/GitHub/comp2003-2025-2026-team-3
```

### 1. Start the database

```bash
cd backend
docker compose up -d
```

### 2. Create the backend virtual environment and install packages

```bash
cd /home/liam/Documents/GitHub/comp2003-2025-2026-team-3/backend
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cpu
python -m spacy download en_core_web_sm
```

### 3. Apply the database schema

```bash
cd /home/liam/Documents/GitHub/comp2003-2025-2026-team-3/backend
source .venv/bin/activate
alembic upgrade head
```

### 4. Install frontend packages

```bash
cd /home/liam/Documents/GitHub/comp2003-2025-2026-team-3/frontend
npm install
```

## Every time you want to run it

Open terminal 1:

```bash
cd /home/liam/Documents/GitHub/comp2003-2025-2026-team-3/backend
./run_local.sh
```

Open terminal 2:

```bash
cd /home/liam/Documents/GitHub/comp2003-2025-2026-team-3/frontend
./run_local.sh
```

## Browser test

1. Open `http://localhost:5173`
2. You should see a signed-out screen with a `Sign in with Microsoft` button.
3. Click it.
4. Sign in with a user from tenant `24e92e30-83bf-4d0e-8a69-3a7b71901db6`.
5. Entra should redirect to `http://localhost:8000/auth/callback`.
6. The backend should resolve or create your internal profile and redirect you back to `http://localhost:5173`.
7. You should then land in the app UI as an authenticated user.

## Quick checks

Unauthenticated session check:

```bash
curl -i http://localhost:8000/api/v1/auth/me
```

Expected result before login:

- `401 Unauthorized`

Health check:

```bash
curl -i http://localhost:8000/health
```

Expected result:

- `200 OK`

## Shutdown

Stop the frontend and backend with `Ctrl+C` in each terminal.

To stop PostgreSQL:

```bash
cd /home/liam/Documents/GitHub/comp2003-2025-2026-team-3/backend
docker compose down
```

## Important security note

The current local backend `.env` contains a live Entra client secret for testing.

After you finish testing:

1. Rotate the client secret in Microsoft Entra admin center.
2. Update `/home/liam/Documents/GitHub/comp2003-2025-2026-team-3/backend/.env`.

## If login fails

Check these first:

- The Entra app registration still has `http://localhost:8000/auth/callback` configured under `Web` redirect URIs.
- The tenant ID and client ID in `backend/.env` still match the Entra app.
- The backend is running before you click `Sign in with Microsoft`.
- The frontend is opened on `http://localhost:5173`.
