export type BackendTicket = {
  autotask_ticket_id: number;
  ticket_number: string;
  company: string;
  contact: string;
  status: string;
  priority: string;
  created: string;
  title: string;
  description: string;
  strike_level: string;
  due_date: string;
  source: string;
  issue_type: string;
  sub_issue_type: string;
  location: string;
  additional_contacts: [];
  work_type: string;
  primary_resource: string;
  secondary_resource: string;
  queue: string;
  ai: {
    category: string;
    confidence: number;
    priority: string;
    priority_score: number;
    method: string;
  };
};
