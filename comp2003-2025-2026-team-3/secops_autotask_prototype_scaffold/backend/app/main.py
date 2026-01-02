from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from .providers.fake_autotask import FakeAutotaskProvider
from .services.ai_categoriser import categorise_ticket

app = FastAPI(title="SecOps Autotask Prototype API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

provider = FakeAutotaskProvider()

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/api/categories")
def categories():
    return {"items": [{"key": k, "label": k} for k in [
        "Email blocked/held",
        "Backup failed",
        "Backup suspended",
        "Hardware offline",
        "Patching vulnerabilities",
        "Patch failed",
    ]]}

@app.get("/api/tickets")
def list_tickets(
    status: str | None = None,
    priority: str | None = None,
    category: str | None = None,
    limit: int = Query(100, ge=1, le=500),
):
    tickets = provider.get_tickets()
    if status:
        tickets = [t for t in tickets if t.status == status]
    if priority:
        tickets = [t for t in tickets if t.priority == priority]

    enriched = []
    for t in tickets[:limit]:
        ai = categorise_ticket(t.title, t.description)
        row = t.model_dump()
        row["ai"] = ai
        enriched.append(row)

    if category:
        enriched = [t for t in enriched if t["ai"]["category"] == category]

    return {"items": enriched, "count": len(enriched)}

@app.get("/api/tickets/{autotask_ticket_id}")
def get_ticket(autotask_ticket_id: int):
    t = provider.get_ticket(autotask_ticket_id)
    row = t.model_dump()
    row["ai"] = categorise_ticket(t.title, t.description)
    return row
