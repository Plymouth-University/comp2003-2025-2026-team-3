from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import secrets, json
from pathlib import Path

app = FastAPI(title="Mock Autotask REST (Dev Only)", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "tickets.json"
TOKENS = set()

@app.post("/oauth2/token")
def token(grant_type: str = "client_credentials", client_id: str = "dev", client_secret: str = "dev"):
    t = secrets.token_urlsafe(24)
    TOKENS.add(t)
    return {"access_token": t, "token_type": "bearer", "expires_in": 3600}

def require_token(authorization: str | None):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    tok = authorization.split(" ", 1)[1].strip()
    if tok not in TOKENS:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.get("/v1.0/Tickets")
def tickets(authorization: str | None = Header(default=None)):
    require_token(authorization)
    return {"items": json.loads(DATA_PATH.read_text(encoding="utf-8")), "count": 100}

@app.post("/v1.0/Tickets/query")
def tickets_query(payload: dict, authorization: str | None = Header(default=None)):
    require_token(authorization)
    items = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    for f in payload.get("filter", []):
        if f.get("op") != "eq":
            continue
        field = f.get("field")
        value = f.get("value")
        items = [t for t in items if t.get(field) == value]
    return {"items": items, "count": len(items)}
