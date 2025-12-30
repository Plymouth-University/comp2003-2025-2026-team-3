from sentence_transformers import SentenceTransformer, util
import spacy

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

def preprocess_text(text):
    doc = nlp(text.lower())
    return [token.lemma_ for token in doc if not token.is_stop and not token.is_punct]

# Chooses a category based on keywords found in the text
def predict_category(text):
    tokens = preprocess_text(text)
    scores = {} 
    print("TOKENS:", tokens)

    # Iterate through each category and its keywords
    for category, desc in CATEGORY_DESCRIPTIONS.items():
        keyword_list = desc.lower().replace(",", "").split()
        score = sum(1 for kw in keyword_list if kw in tokens)
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


# Scores the priority based on the keywords and categories
def calculate_priority(text, category):
    # Initialise base priority score
    base = 10

    # Add urgency based on the category
    if category == "data_breach":
        base += PRIORITY_WEIGHTS["critical"]
    elif category == "malware":
        base += PRIORITY_WEIGHTS["high"]
    elif category == "network":
        base += PRIORITY_WEIGHTS["medium"]
    else:
        base += PRIORITY_WEIGHTS["low"]

    # Ensure the score is within 0-100 range
    return min(max(base, 0), 100)

# Main function to process a ticket text
def process_ticket(ticket_text):
    category, method_used, semantic_scores = hybrid_category_prediction(ticket_text)
    priority = calculate_priority(ticket_text, category)

    # Prints the result of a ticket
    return {
        "input_text": ticket_text,
        "predicted_category": category,
        "priority_score": priority,
        "priority_label": (
            "Critical" if priority > 80 else
            "High" if priority > 60 else
            "Medium" if priority > 40 else
            "Low"
        ),
        "category_detection_method": method_used,
        "semantic_scores": semantic_scores
    }

# Example testing

if __name__ == "__main__":
    sample_tickets = [
        "URGENT: Entire network is down, cannot reach any servers.",
        "User reports suspicious email asking for credentials.",
        "Laptop infected with a virus, files encrypted.",
        "Need help resetting password for new employee.",
        "Possible data breach, customer data exposed externally.",
        "Our systems were breached and sensitive information might have been leaked."
    ]

    # Process and print results for each sample ticket
    for t in sample_tickets:
        print("\n---- Incoming Ticket ----")
        result = process_ticket(t)
        for k, v in result.items():
            print(f"{k}: {v}")

    n = True
    while n is True:
        input_text = input("\nDo you want to test another ticket? (yes/no): ").strip().lower()
        if input_text != 'yes':
            n = False
        else:
            ticket_text = input("Enter the ticket text: ")
            print("\n---- Incoming Ticket ----")
            result = process_ticket(ticket_text)
            for k, v in result.items():
                print(f"{k}: {v}")