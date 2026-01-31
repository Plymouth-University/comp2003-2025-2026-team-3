"""
AI Category Generation Script

This script loads tickets from the data folder and uses AI to:
1. Analyze all tickets without predefined categories
2. Automatically discover and generate new categories based on ticket patterns
3. Cluster similar tickets together using semantic analysis
4. Print the discovered categories at the end
"""

import json
import sys
from pathlib import Path
from collections import Counter, defaultdict
from typing import List, Dict, Tuple
import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.ai.config import model
from app.services.ai.text_processor import preprocess_text
from sentence_transformers import util


def load_tickets(tickets_path: str) -> list:
    """
    Load tickets from JSON file.
    
    Args:
        tickets_path: Path to the tickets JSON file
        
    Returns:
        List of ticket dictionaries
    """
    with open(tickets_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def prepare_ticket_data(tickets: list) -> Tuple[list, np.ndarray]:
    """
    Prepare ticket data by creating embeddings for clustering.
    
    Args:
        tickets: List of ticket dictionaries
        
    Returns:
        Tuple of (processed_tickets, embeddings_array)
    """
    processed_tickets = []
    embeddings_list = []
    
    print("\nGenerating embeddings for all tickets...")
    for i, ticket in enumerate(tickets, 1):
        # Combine title and description for analysis
        text = f"{ticket.get('title', '')} {ticket.get('description', '')}"
        
        # Generate embedding
        embedding = model.encode(text, convert_to_tensor=False)
        embeddings_list.append(embedding)
        
        # Store processed ticket
        processed_tickets.append({
            'ticket_number': ticket.get('ticket_number', 'N/A'),
            'ticket_id': ticket.get('autotask_ticket_id', 'N/A'),
            'company': ticket.get('company', 'N/A'),
            'title': ticket.get('title', 'N/A'),
            'description': ticket.get('description', ''),
            'full_text': text,
            'embedding': embedding
        })
        
        if i % 50 == 0:
            print(f"  Processed {i}/{len(tickets)} tickets...")
    
    # Convert to numpy array for clustering
    embeddings_array = np.array(embeddings_list)
    
    return processed_tickets, embeddings_array


def find_optimal_clusters(embeddings: np.ndarray, min_clusters: int = 3, max_clusters: int = 15) -> int:
    """
    Find the optimal number of clusters using silhouette score.
    
    Args:
        embeddings: Array of ticket embeddings
        min_clusters: Minimum number of clusters to try
        max_clusters: Maximum number of clusters to try
        
    Returns:
        Optimal number of clusters
    """
    print(f"\nFinding optimal number of categories (testing {min_clusters} to {max_clusters})...")
    
    silhouette_scores = []
    cluster_range = range(min_clusters, min(max_clusters + 1, len(embeddings)))
    
    for n_clusters in cluster_range:
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = kmeans.fit_predict(embeddings)
        score = silhouette_score(embeddings, labels)
        silhouette_scores.append(score)
        print(f"  {n_clusters} categories: silhouette score = {score:.3f}")
    
    # Find the best number of clusters
    best_idx = np.argmax(silhouette_scores)
    optimal_clusters = cluster_range[best_idx]
    
    print(f"\nOptimal number of categories: {optimal_clusters} (score: {silhouette_scores[best_idx]:.3f})")
    
    return optimal_clusters


def cluster_tickets(tickets: list, embeddings: np.ndarray, n_clusters: int) -> Dict[int, List[dict]]:
    """
    Cluster tickets into categories using K-means.
    
    Args:
        tickets: List of processed ticket dictionaries
        embeddings: Array of ticket embeddings
        n_clusters: Number of clusters to create
        
    Returns:
        Dictionary mapping cluster IDs to lists of tickets
    """
    print(f"\nClustering tickets into {n_clusters} categories...")
    
    # Perform K-means clustering
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(embeddings)
    
    # Group tickets by cluster
    clusters = defaultdict(list)
    for ticket, label in zip(tickets, labels):
        ticket['cluster_id'] = int(label)
        clusters[int(label)].append(ticket)
    
    # Sort clusters by size
    sorted_clusters = {k: v for k, v in sorted(clusters.items(), key=lambda x: len(x[1]), reverse=True)}
    
    print("Clustering complete!")
    for cluster_id, cluster_tickets in sorted_clusters.items():
        print(f"  Category {cluster_id + 1}: {len(cluster_tickets)} tickets")
    
    return sorted_clusters


def identify_cluster_theme(tickets: List[dict]) -> List[str]:
    """
    Identify the common theme/keywords in a cluster of tickets.
    
    Args:
        tickets: List of similar tickets
        
    Returns:
        List of common keywords representing the theme
    """
    # Combine all text
    all_text = ' '.join([t['full_text'] for t in tickets])
    tokens = preprocess_text(all_text)
    
    # Get most common keywords
    keyword_counts = Counter(tokens)
    common_words = {
        'user', 'ticket', 'system', 'error', 'issue', 'problem', 'help', 'need', 
        'cant', 'cannot', 'please', 'would', 'could', 'datto', 'rmm', 'generated',
        'alert', 'company', 'device', 'site', 'office', 'observed', 'suggested'
    }
    
    # Get top themes (excluding common words)
    themes = [word for word, count in keyword_counts.most_common(30) 
             if word not in common_words and len(word) > 3][:10]
    
    return themes


def generate_category_name(themes: List[str], cluster_id: int) -> str:
    """
    Generate a descriptive category name from themes.
    
    Args:
        themes: List of common keywords
        cluster_id: Cluster identifier
        
    Returns:
        Generated category name
    """
    if not themes:
        return f"category_{cluster_id + 1}"
    
    # Use top 1-2 themes for the name
    if len(themes) >= 2:
        return f"{themes[0]}_{themes[1]}"
    else:
        return themes[0]


def generate_category_description(themes: List[str], sample_titles: List[str]) -> str:
    """
    Generate a description for a category based on themes and sample tickets.
    
    Args:
        themes: Common keywords in the category
        sample_titles: Sample ticket titles
        
    Returns:
        Generated description
    """
    if not themes:
        return "Miscellaneous tickets"
    
    # Create description from themes
    theme_str = ', '.join(themes[:5])
    return f"Tickets related to {theme_str}. Common issues in this category involve these topics."


def analyze_and_name_categories(clusters: Dict[int, List[dict]]) -> List[Dict]:
    """
    Analyze each cluster and generate category names and descriptions.
    
    Args:
        clusters: Dictionary of cluster ID to ticket lists
        
    Returns:
        List of generated categories with metadata
    """
    print("\nGenerating category names and descriptions...")
    
    generated_categories = []
    
    for cluster_id, tickets in clusters.items():
        # Identify common themes
        themes = identify_cluster_theme(tickets)
        
        # Generate name and description
        category_name = generate_category_name(themes, cluster_id)
        description = generate_category_description(themes, [t['title'] for t in tickets])
        
        # Get sample tickets
        sample_titles = [t['title'] for t in tickets[:5]]
        
        category_info = {
            'category_id': cluster_id + 1,
            'category_name': category_name,
            'description': description,
            'ticket_count': len(tickets),
            'common_themes': themes,
            'sample_titles': sample_titles,
            'tickets': tickets
        }
        
        generated_categories.append(category_info)
        
        print(f"  Category {cluster_id + 1}: '{category_name}' ({len(tickets)} tickets)")
    
    return generated_categories


def print_results(categories: List[Dict]):
    """
    Print the generated categories in a formatted manner.
    
    Args:
        categories: List of generated category dictionaries
    """
    print("AI-GENERATED CATEGORIES")
    
    total_tickets = sum(cat['ticket_count'] for cat in categories)
    
    print(f"\nTotal Tickets Analyzed: {total_tickets}")
    print(f"Number of Categories Discovered: {len(categories)}")
    
    # Print category summary
    print("DISCOVERED CATEGORIES")
    
    for category in categories:
        print(f"CATEGORY {category['category_id']}: {category['category_name'].upper()}")
        print(f"Ticket Count: {category['ticket_count']}")
        print(f"Description: {category['description']}")
        print(f"\nCommon Themes/Keywords:")
        print(f"  {', '.join(category['common_themes'][:10])}")
        
        print(f"\nSample Ticket Titles:")
        for i, title in enumerate(category['sample_titles'], 1):
            print(f"  {i}. {title[:90]}{'...' if len(title) > 90 else ''}")
    
    # Print detailed ticket assignments
    print("DETAILED TICKET ASSIGNMENTS (First 30 tickets)")
    
    ticket_count = 0
    for category in categories:
        for ticket in category['tickets']:
            if ticket_count >= 30:
                break
            
            ticket_count += 1
            print(f"\n[{ticket_count}] {ticket['ticket_number']}")
            print(f"    Category: {category['category_name']} (Category {category['category_id']})")
            print(f"    Company: {ticket['company']}")
            print(f"    Title: {ticket['title'][:80]}{'...' if len(ticket['title']) > 80 else ''}")
        
        if ticket_count >= 30:
            break
    
    # Print category distribution chart
    print("CATEGORY DISTRIBUTION")
    
    max_count = max(cat['ticket_count'] for cat in categories)
    
    for category in categories:
        count = category['ticket_count']
        percentage = (count / total_tickets) * 100
 
        print(f"{category['category_name']} {count} ({percentage:.1f}%)")


def main():
    """
    Main function to run AI category generation from scratch.
    """
    print("AI CATEGORY GENERATION - Discovering Categories from Ticket Data")
    
    # Path to tickets file
    tickets_path = Path(__file__).parent / "data" / "tickets.json"
    
    if not tickets_path.exists():
        print(f"Error: Tickets file not found at {tickets_path}")
        print("Please ensure the tickets.json file exists in the data folder.")
        return
    
    # Load tickets
    print(f"\nLoading tickets from {tickets_path}...")
    tickets = load_tickets(str(tickets_path))
    print(f"Loaded {len(tickets)} tickets.")
    
    # Prepare ticket data and generate embeddings
    processed_tickets, embeddings = prepare_ticket_data(tickets)
    
    # Find optimal number of clusters
    optimal_n_clusters = find_optimal_clusters(embeddings, min_clusters=4, max_clusters=12)
    
    # Cluster tickets into categories
    clusters = cluster_tickets(processed_tickets, embeddings, optimal_n_clusters)
    
    # Analyze clusters and generate category names
    generated_categories = analyze_and_name_categories(clusters)
    
    # Print all results
    print_results(generated_categories)
    
    # Save results to file
    output_path = Path(__file__).parent / "data" / "generated_categories.json"
    output_data = {
        'total_tickets': len(processed_tickets),
        'number_of_categories': len(generated_categories),
        'categories': [
            {
                'category_id': cat['category_id'],
                'category_name': cat['category_name'],
                'description': cat['description'],
                'ticket_count': cat['ticket_count'],
                'common_themes': cat['common_themes'],
                'sample_titles': cat['sample_titles']
            }
            for cat in generated_categories
        ],
        'detailed_tickets': [
            {
                'ticket_number': ticket['ticket_number'],
                'ticket_id': ticket['ticket_id'],
                'company': ticket['company'],
                'title': ticket['title'],
                'assigned_category': next(
                    cat['category_name'] for cat in generated_categories 
                    if ticket in cat['tickets']
                )
            }
            for ticket in processed_tickets
        ]
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"\nResults saved to {output_path}")
    print("Category generation complete!")



if __name__ == "__main__":
    main()
