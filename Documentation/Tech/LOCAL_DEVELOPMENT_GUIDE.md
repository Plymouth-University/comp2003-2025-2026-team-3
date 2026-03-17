# Local Run Start To Finish

This guide provides the minimum steps required to run the full application stack locally and test the Microsoft Entra ID login through the UI.

## What this starts

- **PostgreSQL Database**: Runs in a Docker container on `localhost:5432`.
- **Backend API**: A FastAPI application served on `http://localhost:8000`.
- **Frontend UI**: A TypeScript SPA served on `http://localhost:5173`.

## One-time Setup

All commands should be run from the repository root: `/home/liam/Documents/GitHub/comp2003-2025-2026-team-3`.

### 1. Start the Database

```bash
cd backend
docker compose up -d
```
This command starts a PostgreSQL container in detached mode.

### 2. Set up the Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cpu
python -m spacy download en_core_web_sm
alembic upgrade head
```
This sets up a Python virtual environment, installs all required dependencies (including CPU-only PyTorch for the AI models), downloads the necessary spaCy language model, and applies the database schema.

### 3. Set up the Frontend

```bash
cd frontend
npm install
```
This command installs all the necessary Node.js dependencies for the frontend application.

## Running the Application

To run the application, you will need to open two separate terminal windows.

**Terminal 1: Start the Backend**
```bash
cd backend
./run_local.sh
```

**Terminal 2: Start the Frontend**
```bash
cd frontend
./run_local.sh
```

## Browser Test

1. Open your web browser and navigate to `http://localhost:5173`.
2. You should be greeted with a signed-out screen that includes a **"Sign in with Microsoft"** button.
3. Click the button to initiate the authentication flow.
4. Sign in using a user from the test tenant: `24e92e30-83bf-4d0e-8a69-3a7b71901db6`.
5. Upon successful authentication, Entra will redirect you to `http://localhost:8000/auth/callback`.
6. The backend will then create or resolve your internal profile and redirect you back to the frontend at `http://localhost:5173`.
7. The application UI should now be visible, and you should be logged in as an authenticated user.

## Quick Checks

You can use `curl` to perform some quick checks on the backend services.

**Health Check:**
```bash
curl -i http://localhost:8000/health
```
- **Expected Result**: `200 OK`

**Unauthenticated Session Check:**
```bash
curl -i http://localhost:8000/api/v1/auth/me
```
- **Expected Result (before login)**: `401 Unauthorized`

## Shutting Down

To stop the application, press `Ctrl+C` in each of the terminal windows.

To stop the PostgreSQL database container:
```bash
cd backend
docker compose down
```

## Troubleshooting

### Login Fails
- Ensure the Entra app registration has `http://localhost:8000/auth/callback` configured under **Web** redirect URIs.
- Verify that the `ENTRA_TENANT_ID` and `ENTRA_CLIENT_ID` in `backend/.env` match the values in your Entra app registration.
- Make sure the backend server is running before you attempt to sign in.
- Double-check that the frontend is accessed via `http://localhost:5173`.

### Slow Backend Start
- The first time you start the backend, it may take a while to download the sentence-transformer model (`all-MiniLM-L6-v2`) from Hugging Face. This is expected. Subsequent startups will be much faster.

### Security Note
- The `backend/.env` file contains a live Entra client secret for local testing. It is recommended to rotate this secret after testing is complete.
- To rotate the secret, generate a new one in the Microsoft Entra admin center and update the `ENTRA_CLIENT_SECRET` value in the `.env` file.
