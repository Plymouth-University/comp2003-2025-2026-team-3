import re
import random

# Create various keywords to identify categories 
CATEGORY_KEYWORDS = {
    "malware": ["malware", "virus", "infected", "trojan", "ransomware"],
    "phishing": ["phish", "scam", "fraud", "fake login"],
    "network": ["network", "offline", "unreachable", "latency", "dns"],
    "access": ["password", "login", "2fa", "authentication", "locked out"],
    "data_breach": ["breach", "leak", "compromised", "exposed"]
}

# Defines the priority weights for different levels
PRIORITY_WEIGHTS = {
    "critical": 90,
    "high": 70,
    "medium": 50,
    "low": 20
}

# Chooses a category based on keywords found in the text
def predict_category(text):
    text = text.lower() # Normalize text to lowercase
    scores = {} 

    # Iterate through each category and its keywords
    for category, keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text)
        if score > 0:
            scores[category] = score

    # If no keywords matched, return "unknown"
    if not scores:
        return "unknown"
    
    # Return the category with the highest score
    return max(scores, key=scores.get)

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
    category = predict_category(ticket_text)
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
        )
    }

# Example testing
if __name__ == "__main__":
    sample_tickets = [
        "URGENT: Entire network is down, cannot reach any servers.",
        "User reports suspicious email asking for credentials.",
        "Laptop infected with a virus, files encrypted.",
        "Need help resetting password for new employee.",
        "Possible data breach, customer data exposed externally."
    ]

    # Process and print results for each sample ticket
    for t in sample_tickets:
        print("\n---- Incoming Ticket ----")
        result = process_ticket(t)
        for k, v in result.items():
            print(f"{k}: {v}")