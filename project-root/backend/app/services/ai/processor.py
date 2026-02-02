"""
Ticket Processor Module

Main orchestrator for AI-powered ticket processing. Coordinates all AI modules
to process, categorize, and prioritize tickets.
"""

import logging
import time
from datetime import datetime

from .logging_config import logger as base_logger, perf_logger, metrics
from .categorizer import predict_category_hybrid
from .priority_calculator import calculate_priority_score, get_priority_label
from .text_processor import extract_ticket_text, detect_company, preprocess_text
from .description_generator import generate_ai_description
from .storage import save_ticket_to_json, get_input_tickets, load_tickets_from_file

logger = base_logger.getChild("processor")


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
    
    # Extract ticket text and metadata
    if isinstance(ticket_input, dict):
        extract_start = time.time()
        ticket_text = extract_ticket_text(ticket_input)
        extract_time = time.time() - extract_start
        metrics.record_operation("extract_ticket_text", extract_time * 1000)
        perf_logger.debug(f"[TIMING] extract_ticket_text() took {extract_time*1000:.2f}ms")
        
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
    metrics.record_operation("predict_category_hybrid", pred_time * 1000)
    perf_logger.debug(f"[TIMING] predict_category_hybrid() took {pred_time*1000:.2f}ms")
    
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
    metrics.record_operation("save_ticket_to_json", save_time * 1000)
    perf_logger.debug(f"[TIMING] save_ticket_to_json() took {save_time*1000:.2f}ms")
    
    total_time = time.time() - ticket_start
    metrics.record_operation("process_ticket_total", total_time * 1000)
    logger.info(f"Processed ticket '{title[:50]}' in {total_time*1000:.2f}ms - Category: {category}, Priority: {priority_label}")
    
    return organized_ticket


def process_input_tickets() -> int:
    """
    Process all tickets in the input folder.
    
    Returns:
        Total number of tickets processed
    """
    input_files = get_input_tickets()
    
    if not input_files:
        logger.info("No tickets found in input folder")
        return 0
    
    logger.info(f"Found {len(input_files)} ticket file(s) to process")
    
    total_tickets_processed = 0
    batch_start = time.time()
    
    for ticket_file in input_files:
        try:
            tickets_to_process = load_tickets_from_file(ticket_file)
            
            if tickets_to_process:
                logger.info(f"Processing: {ticket_file} ({len(tickets_to_process)} ticket(s))")
                
                for ticket_data in tickets_to_process:
                    process_ticket(ticket_data)
                    total_tickets_processed += 1
            
        except Exception as e:
            logger.error(f"Failed to process {ticket_file}: {e}")
    
    batch_time = time.time() - batch_start
    logger.info(f"Batch complete: Processed {total_tickets_processed} total ticket(s) in {batch_time:.2f}s")
    
    # Log performance summary
    metrics.log_summary(logger)
    
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
    pass
