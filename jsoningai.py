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
TICKETS_BASE_PATH = r"c:\Users\toby\2003\Processed Tickets"
INPUT_TICKETS_PATH = r"c:\Users\toby\2003\Unprocessed Tickets"
CONFIG_PATH = r"c:\Users\toby\2003\config.json"

def load_config():
    # Load keywords and company names from config file.
    global CATEGORY_KEYWORDS, COMPANY_NAMES
    
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r') as f:
                config = json.load(f)
                CATEGORY_KEYWORDS = config.get("category_keywords", CATEGORY_KEYWORDS)
                COMPANY_NAMES = set(config.get("company_names", list(COMPANY_NAMES)))
                print(f"Config loaded from {CONFIG_PATH}")
        except Exception as e:
            print(f"Failed to load config: {e}")
    else:
        print(f"Config file not found, creating with defaults...")
        save_config()

def save_config():
    # Save updated keywords and company names to config file.
    try:
        config = {
            "category_keywords": CATEGORY_KEYWORDS,
            "company_names": list(COMPANY_NAMES)
        }
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        with open(CONFIG_PATH, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"Config saved to {CONFIG_PATH}")
    except Exception as e:
        print(f"Failed to save config: {e}")

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

# Filters out irrelevant keywords like company names and common words.
def filter_irrelevant_keywords(tokens, ticket_text):
    # Words that are too generic or irrelevant to add as keywords
    irrelevant_words = {
        "user", "help", "issue", "problem", "ticket", "email", "day", "time",
        "new", "old", "need", "want", "make", "get", "set", "etc", "please"
    }
    
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

def update_category_keywords(ticket_text, predicted_category):
    tokens = preprocess_text(ticket_text)
    
    # Filter tokens to only relevant ones
    filtered_tokens = filter_irrelevant_keywords(tokens, ticket_text)
    
    # Get new keywords that aren't already in the category
    new_keywords = [t for t in filtered_tokens if t not in CATEGORY_KEYWORDS[predicted_category]]
    
    if new_keywords:
        CATEGORY_KEYWORDS[predicted_category].extend(new_keywords)
        save_config()  # Save updated keywords to config

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
    
    return detected_companies if detected_companies else ["unknown"]


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
            if company != "unknown":
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
            if company != "unknown":
                company_path = os.path.join(TICKETS_BASE_PATH, "Company", company)
                company_file = os.path.join(company_path, filename)
                with open(company_file, 'w') as f:
                    json.dump(ticket_data, f, indent=2)
        
        print(f"Ticket saved to Categories/{category}/{filename}")
        print(f"Ticket saved to Priority/{priority_label.lower()}/{filename}")
        for company in companies:
            if company != "unknown":
                print(f"Ticket saved to Company/{company}/{filename}")
    except Exception as e:
        print(f"Error saving ticket: {e}")


# Main function to process a ticket text
def process_ticket(ticket_text):
    category, method_used, semantic_scores = hybrid_category_prediction(ticket_text)
    priority = calculate_dynamic_priority(ticket_text, category, semantic_scores)
    priority_label = get_priority_label(priority)
    companies = detect_company(ticket_text)
    sorted_scores = dict(sorted(semantic_scores.items(), key=lambda item: item[1], reverse=True))

    if method_used == "semantic": 
        update_category_keywords(ticket_text, category)

    # Create ticket data structure
    ticket_data = {
        "timestamp": datetime.now().isoformat(),
        "input_text": ticket_text,
        "predicted_category": category,
        "category_detection_method": method_used,
        "priority_score": priority,
        "priority_label": priority_label,
        "detected_companies": companies,
        "semantic_scores": sorted_scores,
        "tokens_found": preprocess_text(ticket_text)
    }
    
    if method_used == "keyword":
        ticket_data["keywords_used"] = CATEGORY_KEYWORDS[category]
    elif method_used == "semantic":
        ticket_data["updated_keywords"] = CATEGORY_KEYWORDS[category]
    
    # Save to JSON files
    save_ticket_to_json(ticket_data, category, priority_label, companies)
    
    # Also print summary
    print(f"\n---- Ticket Processed ----")
    print(f"Category: {category} | Priority: {priority_label} ({priority})")
    print(f"Companies: {', '.join(companies)}")

def process_input_tickets():
    # Process all tickets from the Input folder.
    load_config()
    
    input_files = get_input_tickets()
    if not input_files:
        print(f"No tickets found in {INPUT_TICKETS_PATH}")
        return
    
    print(f"Found {len(input_files)} ticket(s) to process\n")
    
    for ticket_file in input_files:
        try:
            # Read ticket from file
            if ticket_file.endswith(".json"):
                with open(ticket_file, 'r') as f:
                    data = json.load(f)
                    ticket_text = data.get("text") or data.get("input_text") or str(data)
            else:  # .txt file
                with open(ticket_file, 'r') as f:
                    ticket_text = f.read().strip()
            
            if ticket_text:
                print(f"Processing: {os.path.basename(ticket_file)}")
                process_ticket(ticket_text)
                # Optionally move or delete processed file
                # os.remove(ticket_file)
        except Exception as e:
            print(f"Failed to process {ticket_file}: {e}")
    
    print(f"\nAll tickets processed and config updated!")

# Example testing
if __name__ == "__main__":
    # Load config and process input tickets
    process_input_tickets()
