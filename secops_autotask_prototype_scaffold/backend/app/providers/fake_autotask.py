import json
from pathlib import Path
from ..models import Ticket

DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "tickets.json"

class FakeAutotaskProvider:
    """Reads tickets from local JSON (your simulated Autotask source)."""
    def __init__(self):
        self._tickets: list[Ticket] | None = None

    def _load(self):
        raw = json.loads(DATA_PATH.read_text(encoding="utf-8"))
        self._tickets = [Ticket(**t) for t in raw]

    def get_tickets(self) -> list[Ticket]:
        if self._tickets is None:
            self._load()
        return self._tickets

    def get_ticket(self, autotask_ticket_id: int) -> Ticket:
        if self._tickets is None:
            self._load()
        for t in self._tickets:
            if t.autotask_ticket_id == autotask_ticket_id:
                return t
        raise KeyError(f"Ticket not found: {autotask_ticket_id}")
