from pydantic import BaseModel, Field
from typing import List

class Ticket(BaseModel):
    autotask_ticket_id: int
    ticket_number: str
    company: str
    contact: str
    status: str
    priority: str
    created: str
    title: str
    description: str
    strike_level: str | None = None
    due_date: str
    source: str
    issue_type: str
    sub_issue_type: str
    location: str | None = None
    additional_contacts: List[str] = Field(default_factory=list)
    work_type: str
    primary_resource: str | None = None
    secondary_resource: str | None = None
    queue: str
