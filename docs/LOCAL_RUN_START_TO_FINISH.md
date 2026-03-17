# Local Development Setup - Complete Guide

This guide walks through setting up the entire application for local development, including the database, backend API, and frontend UI.

## What Gets Started

- **PostgreSQL Database** on `localhost:5432`
- **Backend API** on `http://localhost:8000`
- **Frontend UI** on `http://localhost:5173`

## Prerequisites

- **Git** - For cloning the repository
- **Python 3.9+** - For backend development
- **Node.js 16+** - For frontend development (includes npm)
- **Docker** - For PostgreSQL container
- **Internet connection** - For downloading dependencies and ML models

## One-Time Setup

### 1. Clone the Repository

```bash
git clone https://github.com/Plymouth-University/comp2003-2025-2026-team-3.git
cd comp2003-2025-2026-team-3
```

### 2. Start the PostgreSQL Database

From the repository root, navigate to the backend directory and start Docker Compose:

```bash
cd backend
docker compose up -d
```

**Verify the database is running:**
```bash
docker compose ps
```

You should see a `postgres` container in the `Up` state.

### 3. Create Backend Python Environment

Navigate back to the backend directory and create a virtual environment:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

**Upgrade pip:**
```bash
pip install --upgrade pip
```

**Install PyTorch (CPU-only to save space):**
```bash
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

**Install backend dependencies:**
```bash
pip install -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cpu
```

**Download spaCy language model (used for text processing):**
```bash
python -m spacy download en_core_web_sm
```

### 4. Apply Database Migrations

Ensure you're in the backend directory with the virtual environment activated:

```bash
cd backend
source .venv/bin/activate  # If not already activated
alembic upgrade head
```

This creates all required database tables from the migrations.

**Verify migrations applied:**
```bash
alembic current
```

### 5. Configure Backend Environment Variables

Create a `.env` file in the `backend` directory. If it doesn't exist:

```bash
cd backend
```

Add these required variables (see `ENTRA_PROFILE_SERVICE_INTEGRATION.md` for details):

```bash
# Database
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/mydb

# Application
ENVIRONMENT=development
DEBUG=True

# Security (change these in production!)
SECRET_KEY=dev-secret-key-change-in-production
ALGORITHM=HS256

# Microsoft Entra ID (get these from Azure Portal)
ENTRA_TENANT_ID=your-entra-tenant-id
ENTRA_CLIENT_ID=your-app-registration-client-id
ENTRA_CLIENT_SECRET=your-app-registration-client-secret
ENTRA_REDIRECT_URI=http://localhost:8000/auth/callback
ENTRA_IDP_NAME=microsoft
ENTRA_INTERNAL_TENANT_NAME=profile-service-test

# Session
SESSION_COOKIE_NAME=secops_session
SESSION_MAX_AGE_SECONDS=28800

# URLs
FRONTEND_URL=http://localhost:5173

# CORS (for frontend communication)
CORS_ORIGINS=["http://localhost:5173", "http://127.0.0.1:5173"]
```

### 6. Install Frontend Dependencies

Open a new terminal window and navigate to the frontend:

```bash
cd frontend
npm install
```

This downloads all JavaScript dependencies defined in `package.json`.

## Running the Application

Once setup is complete, use two separate terminal windows to run the backend and frontend.

### Terminal 1: Backend

```bash
cd backend
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
./run_local.sh
```

Expected output:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

First startup takes longer due to model downloads.

### Terminal 2: Frontend

```bash
cd frontend
npm run dev
```

Expected output:
```
  VITE v4.x.x  ready in xxx ms
  ➜  Local:   http://localhost:5173/
```

### Open in Browser

Navigate to `http://localhost:5173` and you should see the application.

## Verification Checklist

### Backend Health

Check that the backend is responding:

```bash
curl -i http://localhost:8000/health
```

Expected response: `200 OK`

### Unauthenticated Session Check

Before logging in, verify that protected endpoints require authentication:

```bash
curl -i http://localhost:8000/api/v1/auth/me
```

Expected response: `401 Unauthorized`

### Frontend Verification

- Open `http://localhost:5173`
- You should see a signed-out screen
- There should be a "Sign in with Microsoft" button visible
- Browser console (F12) should have no errors

### Database Verification

Check that migrations created tables:

```bash
cd backend
docker compose exec postgres psql -U postgres -d mydb -c "\dt"
```

You should see tables like `tenant`, `profile`, `identity_provider`, `profile_identity`, etc.

## Testing the Full Authentication Flow

### Prerequisites

You need a valid Entra ID tenant and app registration. See `ENTRA_PROFILE_SERVICE_INTEGRATION.md` for setup.

### Steps

1. Ensure backend and frontend are running
2. Open `http://localhost:5173` in your browser
3. Click "Sign in with Microsoft"
4. You'll be redirected to the Entra login page
5. Sign in with a user from your configured Entra tenant
6. You should be redirected back to the frontend
7. The app should now show authenticated content

### If Login Fails

Check:
1. `ENTRA_REDIRECT_URI` in `backend/.env` matches Azure portal exactly
2. Backend logs show `/auth/callback` was reached
3. `ENTRA_TENANT_ID`, `ENTRA_CLIENT_ID`, `ENTRA_CLIENT_SECRET` are correct
4. The user signing in belongs to the configured Entra tenant

## Useful Commands

### Check Running Services

```bash
# Backend (check if listening)
lsof -i :8000

# Frontend (check if listening)
lsof -i :5173

# Database (check if running)
docker compose ps
```

### Activate Virtual Environment

**Linux/Mac:**
```bash
source backend/.venv/bin/activate
```

**Windows (PowerShell):**
```powershell
backend\.venv\Scripts\Activate.ps1
```

**Windows (CMD):**
```cmd
backend\.venv\Scripts\activate.bat
```

### Run Backend Tests

```bash
cd backend
source .venv/bin/activate
pytest
```

### Run Frontend Tests

```bash
cd frontend
npm run test
```

### View Database Contents

```bash
cd backend
docker compose exec postgres psql -U postgres -d mydb
```

Common queries:
```sql
-- List all tables
\dt

-- View tenants
SELECT * FROM tenant;

-- View profiles
SELECT * FROM profile;

-- View authentication identities
SELECT * FROM profile_identity;
```

### Rebuild Database (destructive!)

**Warning: This deletes all data**

```bash
cd backend
docker compose down -v
docker compose up -d
alembic upgrade head
```

## Troubleshooting

### "Port 5432 already in use"

Another PostgreSQL instance is running. Either:
1. Stop it: `docker compose down`
2. Or use a different port in `docker-compose.yml`

### "ModuleNotFoundError: No module named 'app'"

Virtual environment not activated:
```bash
cd backend
source .venv/bin/activate
```

### Backend slow to start

Expected on first run - it's downloading AI models (~500MB). Subsequent runs are faster.

### "Connection refused" when accessing backend

Backend not running. Ensure:
1. Virtual environment is activated
2. `./run_local.sh` executed successfully
3. MySQL/other databases aren't using port 8000

### Frontend shows "Cannot GET /"

Ensure frontend started with `npm run dev` and check for errors in the terminal.

### "Failed to reach Microsoft Entra ID" (502 error)

- Check internet connection
- Verify firewall allows `login.microsoftonline.com`
- Entra configuration may be incorrect

### Profile not created after login

Check backend logs for errors in `/auth/callback`. Possible issues:
- Token validation failed
- Database write failed
- `ENTRA_INTERNAL_TENANT_NAME` tenant couldn't be created

## Shutdown

### Graceful Shutdown

**In each terminal window**, press `Ctrl+C`

### Stop Database

```bash
cd backend
docker compose down
```

Optional: Remove all data
```bash
docker compose down -v
```

## Next Steps

- Review `ENTRA_PROFILE_SERVICE_INTEGRATION.md` to understand authentication
- Review `PROFILE_SERVICE_GUIDE.md` for API/database structure
- Check the codebase structure:
  - `backend/app/` - FastAPI application
  - `frontend/src/` - Vue 3 application
  - `backend/alembic/versions/` - Database migrations

## Getting Help

### Common Documentation

- **Entra ID Setup**: See `ENTRA_PROFILE_SERVICE_INTEGRATION.md`
- **API Endpoints**: See `PROFILE_SERVICE_GUIDE.md`
- **Architecture**: See `AI_SYSTEM_ARCHITECTURE.md`

### Debugging

1. Check terminal output for error messages
2. Check browser console (F12) for frontend errors
3. Check backend logs for API errors
4. Verify environment variables are set correctly

### Team Communication

If you encounter issues not covered here:
1. Check existing issues on GitHub
2. Ask the team on Discord/Slack
3. Create a new issue if it's undocumented
