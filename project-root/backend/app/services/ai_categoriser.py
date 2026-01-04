from sentence_transformers import SentenceTransformer, util
import spacy
import json
import os
from datetime import datetime

nlp = spacy.load("en_core_web_sm")
model = SentenceTransformer('all-MiniLM-L6-v2')

# Create various keywords to identify categories 
CATEGORY_DESCRIPTIONS = {
    "malware": "Device infected with malware, virus, trojan or ransomware.",
    "phishing": "User received fraudulent or deceptive emails asking for credentials.",
    "network": "Network outage, slow connectivity, servers unreachable.",
    "access": "Login problems, password resets, authentication issues, 2FA failures.",
    "data_breach": "Sensitive information leaked or exposed without authorisation."
}

# Create various keywords to identify categories 
CATEGORY_KEYWORDS = {
    "malware": ["malware", "virus", "infect", "trojan", "ransomware"],
    "phishing": ["phish", "scam", "fraud", "fake", "login", "suspicious", "email"],
    "network": ["network", "offline", "unreachable", "latency", "dns"],
    "access": ["password", "login", "2fa", "authentication", "lock"],
    "data_breach": ["breach", "leak", "compromise", "expose"]
}

CATEGORY_EMBEDDINGS = {
    cat: model.encode(desc, convert_to_tensor=True)
    for cat, desc in CATEGORY_DESCRIPTIONS.items()
}

# Defines the priority weights for different levels
PRIORITY_WEIGHTS = {
    "critical": 90,
    "high": 70,
    "medium": 50,
    "low": 20
}

# Common company names to detect
COMPANY_NAMES = {"association a", "business b", "company c", "division d", "employer e", "foundation f", "gym g", "hotel h"}

# Base path for ticket storage
TICKETS_BASE_PATH = r"c:\secops_autotask_prototype_scaffold\backend\data\Processed Tickets"
INPUT_TICKETS_PATH = r"c:\secops_autotask_prototype_scaffold\backend\data\Unprocessed Tickets"

def get_input_tickets():
    # Get all ticket files from the Input folder.
    if not os.path.exists(INPUT_TICKETS_PATH):
        os.makedirs(INPUT_TICKETS_PATH, exist_ok=True)
        print(f"Created input folder: {INPUT_TICKETS_PATH}")
        return []
    
    ticket_files = []
    for file in os.listdir(INPUT_TICKETS_PATH):
        if file.endswith(".txt") or file.endswith(".json"):
            ticket_files.append(os.path.join(INPUT_TICKETS_PATH, file))
    
    return sorted(ticket_files)

def preprocess_text(text):
    doc = nlp(text.lower())
    return [token.lemma_ for token in doc if not token.is_stop and not token.is_punct]

    
    # Build set of all words from multi-word company names for filtering
    company_words = set()
    for company in COMPANY_NAMES:
        company_words.update(company.lower().split())
    
    # Check if text contains any multi-word company names to exclude related tokens
    text_lower = ticket_text.lower()
    company_tokens_to_exclude = set()
    for company in COMPANY_NAMES:
        if company in text_lower:
            # If a multi-word company is found, mark all its words for exclusion
            company_tokens_to_exclude.update(company.split())
    
    # Filter out company names and irrelevant words
    filtered = [
        t for t in tokens 
        if t not in irrelevant_words 
        and t not in company_tokens_to_exclude
        and len(t) > 2  # Filter out very short tokens
    ]
    return filtered


# Chooses a category based on keywords found in the text
def predict_category(text):
    tokens = preprocess_text(text)
    scores = {} 

    # Iterate through each category and its keywords
    for category, desc in CATEGORY_KEYWORDS.items():
        for category, keywords in CATEGORY_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in tokens)
            if score > 0:
                scores[category] = score

    # If no keywords matched, return "unknown"
    if not scores:
        return {}
    
    # Return the category with the highest score
    return scores

def semantic_category_prediction(text):
    ticket_embedding = model.encode(text, convert_to_tensor=True)
    
    similarities = {}
    for category, cat_emb in CATEGORY_EMBEDDINGS.items():
        similarity = util.cos_sim(ticket_embedding, cat_emb).item()
        scaled = int(((similarity + 1) / 2) * 100)
        similarities[category] = scaled
    
    # Return category with highest semantic similarity
    best_cat = max(similarities, key=similarities.get)
    return best_cat, similarities

def hybrid_category_prediction(text):
    keyword_scores = predict_category(text) 
    semantic_best, semantic_scores = semantic_category_prediction(text)

    # If keywords were confident, trust them
    if keyword_scores and max(keyword_scores.values()) >= 2:
        return max(keyword_scores, key=keyword_scores.get), "keyword", semantic_scores

    # Otherwise fall back to AI semantic match
    return semantic_best, "semantic", semantic_scores

def detect_company(text):
    # Detects company names mentioned in the ticket text.
    tokens = preprocess_text(text)
    text_lower = text.lower()
    
    detected_companies = []
    for company in COMPANY_NAMES:
        if company in tokens or company in text_lower:
            detected_companies.append(company)
    
    return detected_companies


def calculate_dynamic_priority(text, category, semantic_scores):
    base = 10

    # Category weight
    cat_weight = {
        "data_breach": 70,
        "malware": 60,
        "network": 30,
        "access": 20,
        "phishing": 35
    }.get(category, 10)
    base += cat_weight

    # Urgency words in text
    urgency_words = ["urgent", "immediately", "asap", "critical", "priority"]
    urgency_score = sum(10 for w in urgency_words if w in text.lower())
    base += urgency_score

    # Semantic confidence adjustment
    semantic_confidence = semantic_scores.get(category, 0)
    base += int(semantic_confidence / 10)  # scale similarity into priority

    # Length adjustment (optional)
    length_adjustment = min(len(text.split()) // 20, 10)  # +1 per 20 words, max 10
    base += length_adjustment

    # Cap between 0 and 100
    return min(max(base, 0), 100)

def get_priority_label(priority_score):
    # Convert priority score to label.
    if priority_score > 80:
        return "Critical"
    elif priority_score > 60:
        return "High"
    elif priority_score > 40:
        return "Medium"
    else:
        return "Low"

def save_ticket_to_json(ticket_data, category, priority_label, companies):
    #Save ticket data to JSON files in Category, Priority, and Company folders.
    try:
        # Create directory structure if it doesn't exist
        category_path = os.path.join(TICKETS_BASE_PATH, "Categories", category)
        priority_path = os.path.join(TICKETS_BASE_PATH, "Priority", priority_label.lower())
        
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
        
        # Save to Priority folder
        priority_file = os.path.join(priority_path, filename)
        with open(priority_file, 'w') as f:
            json.dump(ticket_data, f, indent=2)
        
        # Save to Company folders
        for company in companies:
            company_path = os.path.join(TICKETS_BASE_PATH, "Company", company)
            company_file = os.path.join(company_path, filename)
            with open(company_file, 'w') as f:
                json.dump(ticket_data, f, indent=2)
        
        print(f"[SAVED] Categories/{category}/{filename}")
        print(f"[SAVED] Priority/{priority_label.lower()}/{filename}")
        for company in companies:
            print(f"[SAVED] Company/{company}/{filename}")
    except Exception as e:
        print(f"Error saving ticket: {e}")


# Main function to process a ticket text
def process_ticket(ticket_input):
    # Handle both string text and structured ticket objects
    if isinstance(ticket_input, dict):
        ticket_text = extract_ticket_text(ticket_input)
        ticket_metadata = ticket_input
        ai_description = generate_ai_description(ticket_input) if ticket_input else None
    else:
        ticket_text = ticket_input
        ticket_metadata = {}
        ai_description = None
    
    # Extract ticket metadata fields
    ticket_number = ticket_metadata.get("ticket_number", "N/A")
    title = ticket_metadata.get("title", "No title provided")
    company = ticket_metadata.get("company", "N/A")
    contact = ticket_metadata.get("contact", "N/A")
    due_date = ticket_metadata.get("due_date", "N/A")
    
    category, method_used, semantic_scores = hybrid_category_prediction(ticket_text)
    priority = calculate_dynamic_priority(ticket_text, category, semantic_scores)
    priority_label = get_priority_label(priority)
    
    # Extract companies from both detected and metadata
    companies = detect_company(ticket_text)
    if "company" in ticket_metadata and ticket_metadata["company"] not in companies:
        companies.append(ticket_metadata["company"])
    
    sorted_scores = dict(sorted(semantic_scores.items(), key=lambda item: item[1], reverse=True))

    # Create organized ticket structure for display and storage
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

    # Create comprehensive ticket data structure - organized as displayed
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
    
    if method_used == "keyword":
        ticket_data["keywords_used"] = CATEGORY_KEYWORDS[category]
    elif method_used == "semantic":
        ticket_data["semantic_confidence"] = semantic_scores.get(category, 0)
    
    # Save to JSON files
    save_ticket_to_json(ticket_data, category, priority_label, companies)
    
    # Print organized ticket summary
    print("\n" + "="*80)
    print("TICKET SUMMARY".center(80))
    print("="*80)
    
    # Display ticket information in organized format
    print(f"Ticket Number: {ticket_number}")
    print(f"Title:         {title}")
    print(f"\nCompany:       {company}")
    print(f"Contact:       {contact}")
    print(f"Due Date:      {due_date}")
    print(f"\nCategory:      {category}")
    print(f"Priority:      {priority_label} ({priority}/100)")
    
    print("\n" + "-"*80)
    print("AI GENERATED DESCRIPTION".center(80))
    print("-"*80)
    
    if ai_description:
        print(ai_description)
    else:
        print("No AI description available")
    
    print("\n" + "-"*80)
    print("DETECTION INFORMATION".center(80))
    print("-"*80)
    print(f"Detection Method: {method_used}")
    print(f"Confidence Scores:")
    for cat, score in sorted_scores.items():
        print(f"  {cat}: {score}%")
    
    print("\n" + "="*80)
    
    return organized_ticket

def process_input_tickets():
    
    input_files = get_input_tickets()
    if not input_files:
        print(f"No tickets found in {INPUT_TICKETS_PATH}")
        return
    
    print(f"Found {len(input_files)} ticket file(s) to process\n")
    
    total_tickets_processed = 0
    
    for ticket_file in input_files:
        try:
            tickets_to_process = []
            
            # Read ticket(s) from file
            if ticket_file.endswith(".json"):
                with open(ticket_file, 'r') as f:
                    data = json.load(f)
                    
                    # Check if data is a list of tickets
                    if isinstance(data, list):
                        # Multiple tickets in one file
                        for item in data:
                            # Extract ticket text from structured format
                            ticket_text = extract_ticket_text(item)
                            if ticket_text:
                                tickets_to_process.append(item)
                    else:
                        # Single ticket in the file
                        ticket_text = extract_ticket_text(data)
                        if ticket_text:
                            tickets_to_process.append(data)
            else:  # .txt file
                with open(ticket_file, 'r') as f:
                    ticket_text = f.read().strip()
                    if ticket_text:
                        tickets_to_process.append({"text": ticket_text})
            
            # Process all tickets from this file
            if tickets_to_process:
                print(f"Processing: {os.path.basename(ticket_file)} ({len(tickets_to_process)} ticket(s))")
                for ticket_data in tickets_to_process:
                    process_ticket(ticket_data)
                    total_tickets_processed += 1
                # Optionally move or delete processed file
                # os.remove(ticket_file)
            
        except Exception as e:
            print(f"Failed to process {ticket_file}: {e}")
    
    print(f"\nCompleted! Processed {total_tickets_processed} total ticket(s) and updated config!")

def generate_ai_description(ticket_item):
    """Use the AI model to generate a comprehensive description."""
    # Build context from ticket fields
    context_parts = []
    
    if "title" in ticket_item:
        context_parts.append(f"Title: {ticket_item['title']}")
    
    if "description" in ticket_item:
        context_parts.append(f"Description: {ticket_item['description']}")
    
    if "sub_issue_type" in ticket_item:
        context_parts.append(f"Issue Type: {ticket_item['sub_issue_type']}")
    
    if "category_bucket_hint" in ticket_item:
        context_parts.append(f"Category: {ticket_item['category_bucket_hint']}")
    
    if "location" in ticket_item:
        context_parts.append(f"Location: {ticket_item['location']}")
    
    if "due_date" in ticket_item:
        context_parts.append(f"Due Date: {ticket_item['due_date']}")
    
    context = "\n".join(context_parts)
    
    # Create prompt for AI
    prompt = f"""Based on the following ticket information, provide a concise summary that includes:
1. A clear explanation of the issue
2. Potential causes
3. Suggested solutions/troubleshooting steps

Ticket Information:
{context}

Provide the response in a structured format with clear sections."""
    
    # Generate embedding and find similar description for context
    # Use semantic search to enhance the description
    try:
        response_embedding = model.encode(prompt, convert_to_tensor=True)
        
        # Build a comprehensive response based on issue type
        issue_type = ticket_item.get("sub_issue_type", "").lower()
        
        explanation = f"Issue: {ticket_item.get('title', 'Ticket Issue')}\n"
        explanation += f"Due: {ticket_item.get('due_date', 'Not specified')}\n\n"
        
        # Generate contextual explanation
        explanation += "Problem Explanation:\n"
        if ticket_item.get("description"):
            explanation += ticket_item["description"] + "\n\n"
        
        # Add AI-generated solutions based on issue type
        explanation += "Potential Causes & Solutions:\n"
        
        if "backup" in issue_type:
            explanation += "- Backup failure typically indicates: Storage capacity issues, agent/service failure, network interruption, or permissions problem\n"
            explanation += "- Remediation: Check backup agent status, verify storage access, review job logs, restart agent service, test network connectivity, confirm last restore point\n"
        elif "network" in issue_type or "connectivity" in issue_type or "offline" in issue_type or "dns" in issue_type:
            explanation += "- Network issues stem from: Router/firewall misconfiguration, connectivity loss, DNS resolution failure, or IP conflicts\n"
            explanation += "- Remediation: Verify network connectivity, ping gateway, check DNS settings, restart network devices, review firewall rules, check IP configuration\n"
        elif "performance" in issue_type or "slow" in issue_type:
            explanation += "- Performance degradation caused by: High resource utilization, heavy processes, insufficient disk space, or bandwidth saturation\n"
            explanation += "- Remediation: Monitor CPU/RAM/Disk usage, identify resource hogs, optimize queries, clear cache/temp files, check network bandwidth, review application logs\n"
        elif "access" in issue_type or "permission" in issue_type or "login" in issue_type:
            explanation += "- Access problems result from: Incorrect permissions, account lockout, expired credentials, or 2FA issues\n"
            explanation += "- Remediation: Verify user permissions, check account status, reset password if needed, enable/disable 2FA, review access logs, check account lockout threshold\n"
        elif "malware" in issue_type or "virus" in issue_type or "security" in issue_type or "breach" in issue_type:
            explanation += "- Security threats require: Immediate isolation, antivirus scanning, forensic analysis, and containment\n"
            explanation += "- Remediation: Isolate affected system, run full antivirus scan, update security definitions, review security logs, change credentials, check for lateral movement, engage incident response\n"
        elif "email" in issue_type or "phishing" in issue_type:
            explanation += "- Email issues include: Phishing attacks, spam, delivery failures, or configuration problems\n"
            explanation += "- Remediation: Check email logs, verify DNS/MX records, scan for phishing/malware, review security policies, user training, implement email filtering\n"
        else:
            explanation += "- General troubleshooting: Verify current system status, check recent changes, review error logs, test connectivity, restart services\n"
            explanation += "- Remediation: Diagnose root cause, apply appropriate fixes based on findings, test resolution, document changes\n"
        
        return explanation
    except Exception as e:
        print(f"Error generating AI description: {e}")
        return None

def extract_ticket_text(ticket_item):
    """Extract and combine relevant ticket information."""
    if isinstance(ticket_item, str):
        return ticket_item
    
    if not isinstance(ticket_item, dict):
        return None
    
    # Try to extract text from common field names
    if "text" in ticket_item:
        return ticket_item["text"]
    if "input_text" in ticket_item:
        return ticket_item["input_text"]
    
    # For structured tickets like Autotask format, use AI to generate description
    ai_description = generate_ai_description(ticket_item)
    
    if ai_description:
        return ai_description
    
    # Fallback to basic extraction if AI generation fails
    parts = []
    
    if "title" in ticket_item:
        parts.append(ticket_item["title"])
    
    if "description" in ticket_item:
        parts.append(ticket_item["description"])
    
    return " ".join(parts) if parts else None

# Example testing
if __name__ == "__main__":
    # Load config and process input tickets
    process_input_tickets()
[7]

def categorise_ticket(ticket_data: dict) -> dict:
    #Alias for process_ticket for backwards compatibility.
    return process_ticket(ticket_data)
