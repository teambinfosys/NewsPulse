"""
Content-Based Recommender using TF-IDF
Recommends articles based on cosine similarity
"""

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from typing import List


def recommend_articles(
    user_vector: np.ndarray,
    tfidf_matrix,
    seen_indices: List[int],
    top_k: int = 10
) -> List[int]:
    """
    Recommend articles based on user preference vector
    
    Args:
        user_vector: User's preference vector
        tfidf_matrix: TF-IDF matrix of all articles
        seen_indices: Indices of articles user has already seen
        top_k: Number of recommendations to return
        
    Returns:
        List of article indices sorted by relevance
    """
    # Calculate cosine similarity between user vector and all articles
    scores = cosine_similarity(
        user_vector.reshape(1, -1),
        tfidf_matrix
    )[0]
    
    # Filter out already seen articles
    for idx in seen_indices:
        if idx < len(scores):
            scores[idx] = -1
    
    # Get top K article indices
    top_indices = scores.argsort()[::-1][:top_k]
    
    return top_indices.tolist()


def recommend_articles_batch(
    user_vectors: np.ndarray,
    tfidf_matrix,
    seen_indices_list: List[List[int]],
    top_k: int = 10
) -> List[List[int]]:
    """
    Batch recommendation for multiple users
    
    Args:
        user_vectors: Matrix of user preference vectors (n_users x n_features)
        tfidf_matrix: TF-IDF matrix of all articles
        seen_indices_list: List of seen article indices for each user
        top_k: Number of recommendations per user
        
    Returns:
        List of recommendation lists (one per user)
    """
    # Calculate similarities for all users at once
    scores = cosine_similarity(user_vectors, tfidf_matrix)
    
    recommendations = []
    
    for i, seen_indices in enumerate(seen_indices_list):
        user_scores = scores[i].copy()
        
        # Filter out seen articles
        for idx in seen_indices:
            if idx < len(user_scores):
                user_scores[idx] = -1
        
        # Get top K
        top_indices = user_scores.argsort()[::-1][:top_k]
        recommendations.append(top_indices.tolist())
    
    return recommendations


def get_similar_articles(
    article_index: int,
    tfidf_matrix,
    top_k: int = 5
) -> List[int]:
    """
    Find articles similar to a given article
    
    Args:
        article_index: Index of the reference article
        tfidf_matrix: TF-IDF matrix of all articles
        top_k: Number of similar articles to return
        
    Returns:
        List of similar article indices
    """
    # Get the article vector
    article_vector = tfidf_matrix[article_index]
    
    # Calculate similarities
    scores = cosine_similarity(
        article_vector,
        tfidf_matrix
    )[0]
    
    # Exclude the article itself
    scores[article_index] = -1
    
    # Get top K similar articles
    top_indices = scores.argsort()[::-1][:top_k]
    
    return top_indices.tolist()


def diversify_recommendations(
    recommendation_indices: List[int],
    tfidf_matrix,
    diversity_weight: float = 0.3
) -> List[int]:
    """
    Re-rank recommendations to increase diversity
    
    Args:
        recommendation_indices: Initial recommendation list
        tfidf_matrix: TF-IDF matrix
        diversity_weight: Weight for diversity (0-1)
        
    Returns:
        Diversified recommendation list
    """
    if len(recommendation_indices) <= 1:
        return recommendation_indices
    
    diversified = [recommendation_indices[0]]  # Start with top recommendation
    remaining = recommendation_indices[1:]
    
    while remaining and len(diversified) < len(recommendation_indices):
        max_score = -1
        best_idx = None
        
        for idx in remaining:
            # Calculate average similarity to already selected items
            selected_vectors = tfidf_matrix[diversified]
            candidate_vector = tfidf_matrix[idx]
            
            avg_similarity = cosine_similarity(
                candidate_vector,
                selected_vectors
            ).mean()
            
            # Score combines position in original list and diversity
            position_score = 1.0 - (remaining.index(idx) / len(remaining))
            diversity_score = 1.0 - avg_similarity
            
            combined_score = (1 - diversity_weight) * position_score + diversity_weight * diversity_score
            
            if combined_score > max_score:
                max_score = combined_score
                best_idx = idx
        
        if best_idx is not None:
            diversified.append(best_idx)
            remaining.remove(best_idx)
    
    return diversified