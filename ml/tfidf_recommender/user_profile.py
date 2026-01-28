"""
User Profile Builder
Builds user preference vectors from interaction history
"""

import numpy as np
from typing import List, Dict


def build_user_profile(
    interactions: List[Dict],
    tfidf_matrix,
    article_id_to_index: Dict[str, int]
) -> np.ndarray:
    """
    Build user preference vector using click-weighted TF-IDF vectors
    
    Args:
        interactions: List of user interactions with articles
            Expected format: [
                {"article_id": str, "clicks": int},
                ...
            ]
        tfidf_matrix: TF-IDF matrix of all articles
        article_id_to_index: Mapping from article ID to matrix index
        
    Returns:
        User preference vector (weighted average of article vectors)
    """
    profile = None
    total_weight = 0.0
    
    for inter in interactions:
        aid = inter.get("article_id")
        clicks = inter.get("clicks", 1)
        
        # Get article index
        idx = article_id_to_index.get(aid)
        if idx is None:
            continue
        
        # Weight by number of clicks
        weight = float(clicks)
        
        # Get article vector and apply weight
        vec = tfidf_matrix[idx].toarray()[0] * weight
        
        # Accumulate weighted vectors
        if profile is None:
            profile = vec
        else:
            profile = profile + vec
        
        total_weight += weight
    
    # If no interactions found, return zero vector
    if profile is None:
        return np.zeros(tfidf_matrix.shape[1])
    
    # Normalize by total weight
    return profile / max(total_weight, 1e-6)


def build_user_profile_from_interests(
    interest_categories: List[str],
    tfidf_matrix,
    article_categories: List[str],
    article_id_to_index: Dict[str, int]
) -> np.ndarray:
    """
    Build user profile based on interest categories
    (Alternative when no interaction history available)
    
    Args:
        interest_categories: List of user's interest categories
        tfidf_matrix: TF-IDF matrix of all articles
        article_categories: List of article categories (same order as matrix)
        article_id_to_index: Mapping from article ID to matrix index
        
    Returns:
        User preference vector
    """
    profile = None
    count = 0
    
    for category in interest_categories:
        # Find articles matching this category
        for i, art_category in enumerate(article_categories):
            if art_category == category:
                vec = tfidf_matrix[i].toarray()[0]
                
                if profile is None:
                    profile = vec
                else:
                    profile = profile + vec
                
                count += 1
    
    # If no matching articles found, return zero vector
    if profile is None:
        return np.zeros(tfidf_matrix.shape[1])
    
    # Normalize
    return profile / max(count, 1)


def update_user_profile(
    current_profile: np.ndarray,
    new_interaction: Dict,
    tfidf_matrix,
    article_id_to_index: Dict[str, int],
    learning_rate: float = 0.1
) -> np.ndarray:
    """
    Incrementally update user profile with new interaction
    
    Args:
        current_profile: Current user preference vector
        new_interaction: New interaction data {"article_id": str, "clicks": int}
        tfidf_matrix: TF-IDF matrix
        article_id_to_index: Article ID to index mapping
        learning_rate: How much to weight new interaction (0-1)
        
    Returns:
        Updated user profile
    """
    aid = new_interaction.get("article_id")
    idx = article_id_to_index.get(aid)
    
    if idx is None:
        return current_profile
    
    # Get new article vector
    new_vec = tfidf_matrix[idx].toarray()[0]
    
    # Weight by clicks
    weight = new_interaction.get("clicks", 1)
    new_vec = new_vec * weight
    
    # Blend with current profile
    updated_profile = (1 - learning_rate) * current_profile + learning_rate * new_vec
    
    return updated_profile