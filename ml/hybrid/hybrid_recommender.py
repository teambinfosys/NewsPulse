"""
Hybrid Recommender System
Combines TF-IDF (content-based) and SVD (collaborative filtering)
"""

import numpy as np
from typing import List, Tuple


def hybrid_score(
    tfidf_scores: np.ndarray,
    svd_scores: np.ndarray,
    alpha: float = 0.6
) -> np.ndarray:
    """
    Combine TF-IDF and SVD scores using weighted average
    
    Args:
        tfidf_scores: Content-based similarity scores
        svd_scores: Collaborative filtering scores
        alpha: Weight for TF-IDF scores (0-1)
               alpha=1 means only content-based
               alpha=0 means only collaborative
               
    Returns:
        Combined scores
    """
    # Normalize scores to [0, 1] range
    tfidf_normalized = normalize_scores(tfidf_scores)
    svd_normalized = normalize_scores(svd_scores)
    
    # Weighted combination
    combined = alpha * tfidf_normalized + (1 - alpha) * svd_normalized
    
    return combined


def normalize_scores(scores: np.ndarray) -> np.ndarray:
    """
    Normalize scores to [0, 1] range using min-max scaling
    
    Args:
        scores: Raw scores
        
    Returns:
        Normalized scores
    """
    scores = np.array(scores)
    
    # Handle edge cases
    if len(scores) == 0:
        return scores
    
    min_score = scores.min()
    max_score = scores.max()
    
    # Avoid division by zero
    if max_score == min_score:
        return np.ones_like(scores) * 0.5
    
    normalized = (scores - min_score) / (max_score - min_score)
    
    return normalized


def hybrid_recommend(
    tfidf_scores: np.ndarray,
    svd_scores: np.ndarray,
    seen_indices: List[int],
    top_k: int = 10,
    alpha: float = 0.6
) -> List[int]:
    """
    Generate hybrid recommendations
    
    Args:
        tfidf_scores: Content-based scores
        svd_scores: Collaborative filtering scores
        seen_indices: Articles to exclude
        top_k: Number of recommendations
        alpha: Weight for content-based scores
        
    Returns:
        List of recommended article indices
    """
    # Combine scores
    combined = hybrid_score(tfidf_scores, svd_scores, alpha)
    
    # Filter out seen articles
    for idx in seen_indices:
        if idx < len(combined):
            combined[idx] = -np.inf
    
    # Get top K
    top_indices = np.argsort(combined)[::-1][:top_k]
    
    return top_indices.tolist()


def adaptive_hybrid_score(
    tfidf_scores: np.ndarray,
    svd_scores: np.ndarray,
    user_interaction_count: int,
    min_interactions: int = 5
) -> np.ndarray:
    """
    Adaptive hybrid scoring that adjusts weights based on user history
    
    For new users (few interactions): rely more on content-based
    For experienced users (many interactions): rely more on collaborative
    
    Args:
        tfidf_scores: Content-based scores
        svd_scores: Collaborative filtering scores
        user_interaction_count: Number of articles user has interacted with
        min_interactions: Threshold for considering user experienced
        
    Returns:
        Combined scores
    """
    # Calculate adaptive alpha
    # New users: alpha closer to 1 (more content-based)
    # Experienced users: alpha closer to 0.5 (balanced)
    if user_interaction_count < min_interactions:
        # New user: 0.8 content, 0.2 collaborative
        alpha = 0.8 - (user_interaction_count / min_interactions) * 0.3
    else:
        # Experienced user: balanced approach
        alpha = 0.5
    
    return hybrid_score(tfidf_scores, svd_scores, alpha)


def weighted_hybrid_score(
    scores_dict: dict,
    weights: dict = None
) -> np.ndarray:
    """
    Combine multiple scoring methods with custom weights
    
    Args:
        scores_dict: Dictionary of {method_name: scores_array}
            Example: {
                'tfidf': array([...]),
                'svd': array([...]),
                'popularity': array([...])
            }
        weights: Dictionary of {method_name: weight}
            If None, uses equal weights
            
    Returns:
        Combined scores
    """
    if weights is None:
        # Equal weights
        weights = {k: 1.0 / len(scores_dict) for k in scores_dict.keys()}
    
    # Normalize weights to sum to 1
    total_weight = sum(weights.values())
    normalized_weights = {k: v / total_weight for k, v in weights.items()}
    
    # Initialize combined scores
    combined = None
    
    for method, scores in scores_dict.items():
        weight = normalized_weights.get(method, 0)
        
        # Normalize scores
        normalized_scores = normalize_scores(np.array(scores))
        
        # Add weighted scores
        if combined is None:
            combined = weight * normalized_scores
        else:
            combined += weight * normalized_scores
    
    return combined


def cascading_hybrid(
    primary_scores: np.ndarray,
    secondary_scores: np.ndarray,
    threshold: float = 0.5,
    top_k: int = 10
) -> List[int]:
    """
    Cascading hybrid: use secondary scores to break ties in primary scores
    
    Args:
        primary_scores: Primary ranking method scores
        secondary_scores: Secondary method for tie-breaking
        threshold: Similarity threshold for considering scores as ties
        top_k: Number of recommendations
        
    Returns:
        List of recommended indices
    """
    # Normalize both score sets
    primary_norm = normalize_scores(primary_scores)
    secondary_norm = normalize_scores(secondary_scores)
    
    # Create combined score: primary + small weight for secondary
    # This ensures primary dominates, but secondary breaks ties
    combined = primary_norm + 0.1 * secondary_norm
    
    # Get top K
    top_indices = np.argsort(combined)[::-1][:top_k]
    
    return top_indices.tolist()


def switching_hybrid(
    tfidf_scores: np.ndarray,
    svd_scores: np.ndarray,
    tfidf_confidence: float,
    svd_confidence: float,
    top_k: int = 10
) -> List[int]:
    """
    Switching hybrid: choose method based on confidence
    
    Args:
        tfidf_scores: Content-based scores
        svd_scores: Collaborative scores
        tfidf_confidence: Confidence in content-based method (0-1)
        svd_confidence: Confidence in collaborative method (0-1)
        top_k: Number of recommendations
        
    Returns:
        List of recommended indices
    """
    # Choose method with higher confidence
    if tfidf_confidence > svd_confidence:
        scores = tfidf_scores
    else:
        scores = svd_scores
    
    # Get top K
    top_indices = np.argsort(scores)[::-1][:top_k]
    
    return top_indices.tolist()