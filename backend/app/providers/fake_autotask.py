import json
from pathlib import Path
from ..models import Ticket
import time
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# reads tickets from backend/data/tickets.json
# converts each ticket to model obkects 
# returns model objects to api
# for future conversion to autotask just replace where tickets getting pulled from

DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "tickets.json"

class FakeAutotaskProvider:
    """Reads tickets from local JSON (your simulated Autotask source)."""
    def __init__(self):
        self._tickets: list[Ticket] | None = None

    def _load(self):
        load_start = time.time()
        load_start_str = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        logger.info(f"[{load_start_str}] FakeAutotaskProvider: Starting JSON file load from {DATA_PATH}...")
        
        try:
            raw = json.loads(DATA_PATH.read_text(encoding="utf-8"))
            logger.info(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] FakeAutotaskProvider: JSON file read successfully, parsing {len(raw)} tickets...")
            
            parse_start = time.time()
            self._tickets = [Ticket(**t) for t in raw]
            parse_time = time.time() - parse_start
            
            load_time = time.time() - load_start
            logger.info(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] FakeAutotaskProvider: Parsing complete in {parse_time:.3f}s")
            logger.info(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] FakeAutotaskProvider: Total load time {load_time:.3f}s for {len(self._tickets)} tickets")
        except Exception as e:
            logger.error(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] FakeAutotaskProvider: Error loading tickets: {str(e)}", exc_info=True)
            raise

    def get_tickets(self) -> list[Ticket]:
        call_time = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        if self._tickets is None:
            logger.info(f"[{call_time}] FakeAutotaskProvider.get_tickets(): Tickets not cached, loading...")
            self._load()
            logger.info(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] FakeAutotaskProvider.get_tickets(): Cache populated, returning {len(self._tickets)} tickets")
        else:
            logger.debug(f"[{call_time}] FakeAutotaskProvider.get_tickets(): Returning {len(self._tickets)} cached tickets")
        return self._tickets

    def get_ticket(self, autotask_ticket_id: int) -> Ticket:
        call_time = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        if self._tickets is None:
            logger.info(f"[{call_time}] FakeAutotaskProvider.get_ticket({autotask_ticket_id}): Cache empty, loading...")
            self._load()
        
        search_start = time.time()
        for t in self._tickets:
            if t.autotask_ticket_id == autotask_ticket_id:
                search_time = time.time() - search_start
                logger.debug(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] FakeAutotaskProvider.get_ticket({autotask_ticket_id}): Found in {search_time:.3f}s")
                return t
        
        search_time = time.time() - search_start
        logger.warning(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] FakeAutotaskProvider.get_ticket({autotask_ticket_id}): Not found after {search_time:.3f}s")
        raise KeyError(f"Ticket not found: {autotask_ticket_id}")
