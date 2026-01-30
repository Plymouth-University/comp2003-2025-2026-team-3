"""
Ticket Processor Module

Main orchestrator for AI-powered ticket processing. Coordinates all AI modules
to process, categorize, and prioritize tickets.
"""

import logging
import time
from datetime import datetime

from .categorizer import predict_category_hybrid
from .priority_calculator import calculate_priority_score, get_priority_label
from .text_processor import extract_ticket_text, detect_company, preprocess_text
from .description_generator import generate_ai_description
from .storage import save_ticket_to_json, get_input_tickets, load_tickets_from_file

logger = logging.getLogger(__name__)


def process_ticket(ticket_input: dict) -> dict:
    """
    Main function to process a ticket end-to-end.
    
    Handles:
    - Text extraction from various formats
    - Category prediction (keyword + semantic)
    - Priority calculation
    - Company detection
    - Description generation
    - JSON storage
    
    Args:
        ticket_input: Ticket data (dict or string)
        
    Returns:
        Organized ticket summary dictionary
    """
    ticket_start = time.time()
    logger.debug(f"[TIMING] ========== process_ticket START ==========")
    
    # Extract ticket text and metadata
    if isinstance(ticket_input, dict):
        extract_start = time.time()
        ticket_text = extract_ticket_text(ticket_input)
        extract_time = time.time() - extract_start
        logger.debug(f"[TIMING] extract_ticket_text() took {extract_time*1000:.2f}ms")
        
        ticket_metadata = ticket_input
        ai_description = generate_ai_description(ticket_input) if ticket_input else None
    else:
        ticket_text = ticket_input
        ticket_metadata = {}
        ai_description = None
    
    # Extract metadata fields
    ticket_number = ticket_metadata.get("ticket_number", "N/A")
    title = ticket_metadata.get("title", "No title provided")
    company = ticket_metadata.get("company", "N/A")
    contact = ticket_metadata.get("contact", "N/A")
    due_date = ticket_metadata.get("due_date", "N/A")
    
    # Predict category
    pred_start = time.time()
    category, method_used, semantic_scores = predict_category_hybrid(ticket_text)
    pred_time = time.time() - pred_start
    logger.debug(f"[TIMING] predict_category_hybrid() took {pred_time*1000:.2f}ms")
    
    # Calculate priority
    priority = calculate_priority_score(ticket_text, category, semantic_scores)
    priority_label = get_priority_label(priority)
    
    # Detect companies
    companies = detect_company(ticket_text)
    if "company" in ticket_metadata and ticket_metadata["company"] not in companies:
        companies.append(ticket_metadata["company"])
    
    # Sort scores by confidence
    sorted_scores = dict(sorted(semantic_scores.items(), key=lambda item: item[1], reverse=True))
    
    # Build organized ticket output
    organized_ticket = {
        "ticket_number": ticket_number,
        "title": title,
        "company": company,
        "contact": contact,
        "due_date": due_date,
        "category": category,
        "priority_level": priority_label,
        "priority_score": priority,
        "ai_generated_description": ai_description if ai_description else "No AI description available"
    }
    
    # Build comprehensive ticket data for storage
    ticket_data = {
        "ticket_number": ticket_number,
        "title": title,
        "company": company,
        "contact": contact,
        "due_date": due_date,
        "category": category,
        "priority_level": priority_label,
        "priority_score": priority,
        "ai_generated_description": ai_description if ai_description else "No AI description available",
        "detection_method": method_used,
        "confidence_scores": sorted_scores,
        "detected_companies": companies,
        "processed_timestamp": datetime.now().isoformat(),
        "input_text": ticket_text,
        "tokens_found": preprocess_text(ticket_text),
        "original_metadata": ticket_metadata
    }
    
    # Add method-specific details
    if method_used == "keyword":
        ticket_data["keywords_used"] = None  # Keywords are in categorizer module
    elif method_used == "semantic":
        ticket_data["semantic_confidence"] = semantic_scores.get(category, 0)
    
    # Save to JSON
    save_start = time.time()
    save_ticket_to_json(ticket_data, category, priority_label, companies)
    save_time = time.time() - save_start
    logger.debug(f"[TIMING] save_ticket_to_json() took {save_time*1000:.2f}ms")
    
    # Print summary
    _print_ticket_summary(ticket_data, sorted_scores)
    
    total_time = time.time() - ticket_start
    logger.info(f"[TIMING] process_ticket() TOTAL: {total_time*1000:.2f}ms for ticket '{title[:50]}'")
    logger.debug(f"[TIMING] ========== process_ticket END ==========")
    
    return organized_ticket


def process_input_tickets() -> int:
    """
    Process all tickets in the input folder.
    
    Returns:
        Total number of tickets processed
    """
    input_files = get_input_tickets()
    
    if not input_files:
        print(f"No tickets found in input folder")
        logger.info("No tickets found in input folder")
        return 0
    
    print(f"Found {len(input_files)} ticket file(s) to process\n")
    logger.info(f"Found {len(input_files)} ticket file(s) to process")
    
    total_tickets_processed = 0
    
    for ticket_file in input_files:
        try:
            tickets_to_process = load_tickets_from_file(ticket_file)
            
            if tickets_to_process:
                print(f"Processing: {ticket_file} ({len(tickets_to_process)} ticket(s))")
                logger.info(f"Processing: {ticket_file} ({len(tickets_to_process)} ticket(s))")
                
                for ticket_data in tickets_to_process:
                    process_ticket(ticket_data)
                    total_tickets_processed += 1
            
        except Exception as e:
            logger.error(f"Failed to process {ticket_file}: {e}")
            print(f"Failed to process {ticket_file}: {e}")
    
    print(f"\nCompleted! Processed {total_tickets_processed} total ticket(s)")
    logger.info(f"Completed! Processed {total_tickets_processed} total ticket(s)")
    
    return total_tickets_processed


def categorise_ticket(ticket_data: dict) -> dict:
    """
    Backwards compatible alias for process_ticket.
    
    Args:
        ticket_data: Ticket data to process
        
    Returns:
        Organized ticket summary
    """
    try:
        logger.debug(f"categorise_ticket called with data: {ticket_data}")
        result = process_ticket(ticket_data)
        logger.debug(f"categorise_ticket returning: {result}")
        return result
    except Exception as e:
        logger.error(f"Error in categorise_ticket: {str(e)}", exc_info=True)
        # Return safe default on error
        return {
            "category": "unknown",
            "priority_level": "Low",
            "priority_score": 0,
            "error": str(e)
        }


def _print_ticket_summary(ticket_data: dict, sorted_scores: dict) -> None:
    """
    Print formatted ticket processing summary.
    
    Args:
        ticket_data: Complete ticket data
        sorted_scores: Sorted confidence scores
    """
    print("\n" + "="*80)
    print("TICKET SUMMARY".center(80))
    print("="*80)
    
    print(f"Ticket Number: {ticket_data.get('ticket_number', 'N/A')}")
    print(f"Title:         {ticket_data.get('title', 'N/A')}")
    print(f"\nCompany:       {ticket_data.get('company', 'N/A')}")
    print(f"Contact:       {ticket_data.get('contact', 'N/A')}")
    print(f"Due Date:      {ticket_data.get('due_date', 'N/A')}")
    print(f"\nCategory:      {ticket_data.get('category', 'N/A')}")
    print(f"Priority:      {ticket_data.get('priority_level', 'N/A')} ({ticket_data.get('priority_score', 0)}/100)")
    
    print("\n" + "-"*80)
    print("AI GENERATED DESCRIPTION".center(80))
    print("-"*80)
    
    ai_desc = ticket_data.get('ai_generated_description', 'N/A')
    if ai_desc and ai_desc != "No AI description available":
        print(ai_desc)
    else:
        print("No AI description available")
    
    print("\n" + "-"*80)
    print("DETECTION INFORMATION".center(80))
    print("-"*80)
    print(f"Detection Method: {ticket_data.get('detection_method', 'N/A')}")
    print(f"Confidence Scores:")
    for cat, score in sorted_scores.items():
        print(f"  {cat}: {score}%")
    
    print("\n" + "="*80)
