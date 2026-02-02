"""
Automatic Category Generator

Generates categories from ticket data on backend startup.
"""

import json
import logging
from pathlib import Path
from collections import Counter, defaultdict
from typing import List, Dict, Tuple
import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

from .config import model
from .text_processor import preprocess_text

logger = logging.getLogger(__name__)


def load_tickets(tickets_path: Path) -> list:
    """Load tickets from JSON file."""
    with open(tickets_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def prepare_ticket_data(tickets: list) -> Tuple[list, np.ndarray]:
    """Prepare ticket data by creating embeddings for clustering."""
    processed_tickets = []
    embeddings_list = []
    
    logger.info(f"Generating embeddings for {len(tickets)} tickets...")
    for i, ticket in enumerate(tickets, 1):
        text = f"{ticket.get('title', '')} {ticket.get('description', '')}"
        embedding = model.encode(text, convert_to_tensor=False)
        embeddings_list.append(embedding)
        
        processed_tickets.append({
            'ticket_number': ticket.get('ticket_number', 'N/A'),
            'ticket_id': ticket.get('autotask_ticket_id', 'N/A'),
            'title': ticket.get('title', 'N/A'),
            'description': ticket.get('description', ''),
            'full_text': text,
        })
        
        # Log progress for each ticket
        if i % 10 == 0:
            logger.info(f"  [{i}/{len(tickets)}] Processed: {ticket.get('ticket_number', 'N/A')} - {ticket.get('title', 'N/A')[:60]}...")
        elif i == len(tickets):
            logger.info(f"  [{i}/{len(tickets)}] Processed: {ticket.get('ticket_number', 'N/A')} - {ticket.get('title', 'N/A')[:60]}...")
    
    embeddings_array = np.array(embeddings_list)
    logger.info(f"✓ Completed embedding generation for all {len(tickets)} tickets")
    return processed_tickets, embeddings_array


def find_optimal_clusters(embeddings: np.ndarray, min_clusters: int = 4, max_clusters: int = 12) -> int:
    """Find the optimal number of clusters using silhouette score."""
    logger.info(f"Finding optimal number of categories ({min_clusters}-{max_clusters})...")
    
    silhouette_scores = []
    cluster_range = range(min_clusters, min(max_clusters + 1, len(embeddings)))
    
    for n_clusters in cluster_range:
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = kmeans.fit_predict(embeddings)
        score = silhouette_score(embeddings, labels)
        silhouette_scores.append(score)
        logger.info(f"  Testing {n_clusters} categories: silhouette score = {score:.3f}")
    
    best_idx = np.argmax(silhouette_scores)
    optimal_clusters = cluster_range[best_idx]
    logger.info(f"Optimal number of categories: {optimal_clusters} (score: {silhouette_scores[best_idx]:.3f})")
    
    return optimal_clusters


def cluster_tickets(tickets: list, embeddings: np.ndarray, n_clusters: int) -> Dict[int, List[dict]]:
    """Cluster tickets into categories using K-means."""
    logger.info(f"Clustering tickets into {n_clusters} categories...")
    
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(embeddings)
    
    clusters = defaultdict(list)
    for i, (ticket, label) in enumerate(zip(tickets, labels), 1):
        clusters[int(label)].append(ticket)
        # Log every ticket assignment
        if i % 10 == 0 or i == len(tickets):
            logger.info(f"  [{i}/{len(tickets)}] Assigned {ticket['ticket_number']} to cluster {label + 1}")
    
    sorted_clusters = {k: v for k, v in sorted(clusters.items(), key=lambda x: len(x[1]), reverse=True)}
    
    logger.info(f"Clustering complete! Category distribution:")
    for cluster_id, cluster_tickets in sorted_clusters.items():
        logger.info(f"  Category {cluster_id + 1}: {len(cluster_tickets)} tickets")
    
    return sorted_clusters


def identify_cluster_theme(tickets: List[dict]) -> List[str]:
    """Identify the common theme/keywords in a cluster of tickets."""
    all_text = ' '.join([t['full_text'] for t in tickets])
    tokens = preprocess_text(all_text)
    
    keyword_counts = Counter(tokens)
    common_words = {
        'user', 'ticket', 'system', 'error', 'issue', 'problem', 'help', 'need', 
        'cant', 'cannot', 'please', 'would', 'could', 'datto', 'rmm', 'generated',
        'alert', 'company', 'device', 'site', 'office', 'observed', 'suggested',
        'action', 'check', 'confirm'
    }
    
    themes = [word for word, count in keyword_counts.most_common(30) 
             if word not in common_words and len(word) > 3][:10]
    
    return themes


def generate_category_name(themes: List[str], cluster_id: int) -> str:
    """Generate a descriptive category name from themes."""
    if not themes:
        return f"category_{cluster_id + 1}"
    
    if len(themes) >= 2:
        return f"{themes[0]}_{themes[1]}"
    else:
        return themes[0]


def generate_category_description(themes: List[str]) -> str:
    """Generate a description for a category based on themes."""
    if not themes:
        return "Miscellaneous tickets"
    
    theme_str = ', '.join(themes[:5])
    return f"Tickets related to {theme_str}"


def analyze_and_name_categories(clusters: Dict[int, List[dict]]) -> List[Dict]:
    """Analyze each cluster and generate category names and descriptions."""
    logger.info("Generating category names and descriptions...")
    
    generated_categories = []
    
    for cluster_id, tickets in clusters.items():
        logger.info(f"Analyzing cluster {cluster_id + 1} with {len(tickets)} tickets...")
        themes = identify_cluster_theme(tickets)
        category_name = generate_category_name(themes, cluster_id)
        description = generate_category_description(themes)
        sample_titles = [t['title'] for t in tickets[:5]]
        
        category_info = {
            'category_id': cluster_id + 1,
            'category_name': category_name,
            'description': description,
            'ticket_count': len(tickets),
            'common_themes': themes,
            'sample_titles': sample_titles
        }
        
        generated_categories.append(category_info)
        logger.info(f"Category {cluster_id + 1}: '{category_name}'")
        logger.info(f"Description: {description}")
        logger.info(f"Common themes: {', '.join(themes[:5])}")
        logger.info(f"Sample tickets: {len(sample_titles)} examples")
    
    return generated_categories


def generate_categories_from_tickets(tickets_file: Path, output_file: Path, force_regenerate: bool = False) -> bool:
    """
    Generate categories from ticket data and save to file.
    
    Args:
        tickets_file: Path to tickets.json
        output_file: Path to save generated_categories.json
        force_regenerate: If True, regenerate even if file exists
        
    Returns:
        True if categories were generated, False if using existing
    """
    # Check if we need to regenerate
    if output_file.exists() and not force_regenerate:
        logger.info(f"Using existing categories from {output_file}")
        return False
    
    # Check if tickets file exists
    if not tickets_file.exists():
        logger.warning(f"Tickets file not found: {tickets_file}")
        logger.warning("Cannot generate categories. Will use default categories.")
        return False
    
    try:
        logger.info("=" * 80)
        logger.info("GENERATING CATEGORIES FROM TICKET DATA")
        logger.info("=" * 80)
        
        # Load tickets
        tickets = load_tickets(tickets_file)
        logger.info(f"Loaded {len(tickets)} tickets from {tickets_file}")
        
        if len(tickets) < 10:
            logger.warning(f"Too few tickets ({len(tickets)}) to generate meaningful categories")
            return False
        
        # Prepare data and generate embeddings
        processed_tickets, embeddings = prepare_ticket_data(tickets)
        
        # Find optimal number of clusters
        optimal_n_clusters = find_optimal_clusters(embeddings, min_clusters=4, max_clusters=12)
        
        # Cluster tickets
        clusters = cluster_tickets(processed_tickets, embeddings, optimal_n_clusters)
        
        # Generate category names and descriptions
        generated_categories = analyze_and_name_categories(clusters)
        
        # Save results
        output_data = {
            'total_tickets': len(processed_tickets),
            'number_of_categories': len(generated_categories),
            'categories': generated_categories
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        logger.info("=" * 80)
        logger.info(f"✓ Categories generated and saved to {output_file}")
        logger.info(f"✓ Generated {len(generated_categories)} categories from {len(tickets)} tickets")
        logger.info("=" * 80)
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to generate categories: {e}", exc_info=True)
        return False
