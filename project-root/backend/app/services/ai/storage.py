"""
Storage Module

Handles saving and loading of processed tickets to/from JSON files.
"""

import json
import os
import logging
import time
from datetime import datetime
from .config import TICKETS_BASE_PATH, INPUT_TICKETS_PATH

logger = logging.getLogger(__name__)


def save_ticket_to_json(
    ticket_data: dict,
    category: str,
    priority_label: str,
    companies: list
) -> bool:
    """
    Save ticket data to JSON files organized by category, priority, and company.
    
    Args:
        ticket_data: Complete ticket data structure
        category: Ticket category
        priority_label: Priority label (Critical, High, Medium, Low)
        companies: List of detected companies
        
    Returns:
        True if save successful, False otherwise
    """
    try:
        # Create directory structure if it doesn't exist
        category_path = os.path.join(TICKETS_BASE_PATH, "Categories", category)
        priority_path = os.path.join(TICKETS_BASE_PATH, "Priority", priority_label.lower())
        
        logger.debug(f"Saving ticket to category_path: {category_path}")
        logger.debug(f"TICKETS_BASE_PATH: {TICKETS_BASE_PATH}")
        logger.debug(f"Path exists: {os.path.exists(TICKETS_BASE_PATH)}")
        
        os.makedirs(category_path, exist_ok=True)
        os.makedirs(priority_path, exist_ok=True)
        
        # Create company folders
        for company in companies:
            company_path = os.path.join(TICKETS_BASE_PATH, "Company", company)
            os.makedirs(company_path, exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"ticket_{timestamp}.json"
        
        # Save to Category folder
        category_file = os.path.join(category_path, filename)
        with open(category_file, 'w') as f:
            json.dump(ticket_data, f, indent=2)
        logger.info(f"[SAVED] Categories/{category}/{filename}")
        print(f"[SAVED] Categories/{category}/{filename}")
        
        # Save to Priority folder
        priority_file = os.path.join(priority_path, filename)
        with open(priority_file, 'w') as f:
            json.dump(ticket_data, f, indent=2)
        logger.info(f"[SAVED] Priority/{priority_label.lower()}/{filename}")
        print(f"[SAVED] Priority/{priority_label.lower()}/{filename}")
        
        # Save to Company folders
        for company in companies:
            company_path = os.path.join(TICKETS_BASE_PATH, "Company", company)
            company_file = os.path.join(company_path, filename)
            with open(company_file, 'w') as f:
                json.dump(ticket_data, f, indent=2)
            logger.info(f"[SAVED] Company/{company}/{filename}")
            print(f"[SAVED] Company/{company}/{filename}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error saving ticket: {e}", exc_info=True)
        print(f"Error saving ticket: {e}")
        return False


def get_input_tickets() -> list:
    """
    Get all ticket files from the input folder.
    
    Returns:
        Sorted list of ticket file paths
    """
    if not os.path.exists(INPUT_TICKETS_PATH):
        os.makedirs(INPUT_TICKETS_PATH, exist_ok=True)
        logger.info(f"Created input folder: {INPUT_TICKETS_PATH}")
        print(f"Created input folder: {INPUT_TICKETS_PATH}")
        return []
    
    ticket_files = []
    for file in os.listdir(INPUT_TICKETS_PATH):
        if file.endswith(".txt") or file.endswith(".json"):
            ticket_files.append(os.path.join(INPUT_TICKETS_PATH, file))
    
    return sorted(ticket_files)


def load_tickets_from_file(ticket_file: str) -> list:
    """
    Load ticket(s) from a JSON or TXT file.
    
    Args:
        ticket_file: Path to ticket file
        
    Returns:
        List of ticket data dictionaries
    """
    tickets = []
    
    try:
        if ticket_file.endswith(".json"):
            with open(ticket_file, 'r') as f:
                data = json.load(f)
                
                # Handle both single tickets and lists
                if isinstance(data, list):
                    tickets = data
                else:
                    tickets = [data]
                    
        else:  # .txt file
            with open(ticket_file, 'r') as f:
                ticket_text = f.read().strip()
                if ticket_text:
                    tickets = [{"text": ticket_text}]
        
        logger.debug(f"Loaded {len(tickets)} ticket(s) from {ticket_file}")
        
    except Exception as e:
        logger.error(f"Error loading tickets from {ticket_file}: {e}")
        print(f"Error loading tickets from {ticket_file}: {e}")
    
    return tickets
