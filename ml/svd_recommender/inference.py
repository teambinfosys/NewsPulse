"""
SVD Inference for Collaborative Filtering
Predicts article scores for users based on latent factors
"""

import numpy as np
from typing import List


def predict_scores(svd_model, interaction_matrix, user_index: int) -> np.ndarray:
    """
    Predict scores for all articles for a given user
    
    Args:
        svd_model: Trained SVD model
        interaction_matrix: User-article interaction matrix
        user_index: Index of the user
        
    Returns:
        Array of predicted scores for each article
    """
    # Get user's latent representation
    user_vector = interaction_matrix[user_index]
    
    # Transform to latent space
    user_latent = svd_model.transform(user_vector)
    
    # Get article factors (components)
    article_factors = svd_model.components_
    
    # Predict scores (dot product of user latent with article factors)
    scores = user_latent @ article_factors
    
    return scores.flatten()


def predict_scores_batch(
    svd_model,
    interaction_matrix,
    user_indices: List[int]
) -> np.ndarray:
    """
    Predict scores for multiple users
    
    Args:
        svd_model: Trained SVD model
        interaction_matrix: User-article interaction matrix
        user_indices: List of user indices
        
    Returns:
        Matrix of scores (n_users x n_articles)
    """
    scores_list = []
    
    for user_idx in user_indices:
        scores = predict_scores(svd_model, interaction_matrix, user_idx)
        scores_list.append(scores)
    
    return np.array(scores_list)


def recommend_articles_svd(
    svd_model,
    interaction_matrix,
    user_index: int,
    top_k: int = 10,
    exclude_seen: bool = True
) -> List[int]:
    """
    Recommend top K articles for a user using SVD
    
    Args:
        svd_model: Trained SVD model
        interaction_matrix: User-article interaction matrix
        user_index: User index
        top_k: Number of recommendations
        exclude_seen: Whether to exclude already seen articles
        
    Returns:
        List of recommended article indices
    """
    # Predict scores
    scores = predict_scores(svd_model, interaction_matrix, user_index)
    
    # Exclude already seen articles if requested
    if exclude_seen:
        user_interactions = interaction_matrix[user_index].toarray().flatten()
        seen_mask = user_interactions > 0
        scores[seen_mask] = -np.inf
    
    # Get top K article indices
    top_indices = np.argsort(scores)[::-1][:top_k]
    
    return top_indices.tolist()


def get_similar_users(
    svd_model,
    interaction_matrix,
    user_index: int,
    top_k: int = 5
) -> List[int]:
    """
    Find similar users based on latent factors
    
    Args:
        svd_model: Trained SVD model
        interaction_matrix: User-article interaction matrix
        user_index: Index of target user
        top_k: Number of similar users to return
        
    Returns:
        List of similar user indices
    """
    # Transform all users to latent space
    user_factors = svd_model.transform(interaction_matrix)
    
    # Get target user's factors
    target_user = user_factors[user_index]
    
    # Calculate cosine similarity
    from sklearn.metrics.pairwise import cosine_similarity
    similarities = cosine_similarity(
        target_user.reshape(1, -1),
        user_factors
    )[0]
    
    # Exclude the user themselves
    similarities[user_index] = -1
    
    # Get top K similar users
    similar_indices = np.argsort(similarities)[::-1][:top_k]
    
    return similar_indices.tolist()


def get_similar_articles(
    svd_model,
    article_index: int,
    top_k: int = 5
) -> List[int]:
    """
    Find similar articles based on latent factors
    
    Args:
        svd_model: Trained SVD model
        article_index: Index of target article
        top_k: Number of similar articles to return
        
    Returns:
        List of similar article indices
    """
    # Get article factors (components)
    article_factors = svd_model.components_.T
    
    # Get target article's factors
    target_article = article_factors[article_index]
    
    # Calculate cosine similarity
    from sklearn.metrics.pairwise import cosine_similarity
    similarities = cosine_similarity(
        target_article.reshape(1, -1),
        article_factors
    )[0]
    
    # Exclude the article itself
    similarities[article_index] = -1
    
    # Get top K similar articles
    similar_indices = np.argsort(similarities)[::-1][:top_k]
    
    return similar_indices.tolist()


def predict_user_article_score(
    svd_model,
    interaction_matrix,
    user_index: int,
    article_index: int
) -> float:
    """
    Predict score for a specific user-article pair
    
    Args:
        svd_model: Trained SVD model
        interaction_matrix: User-article interaction matrix
        user_index: User index
        article_index: Article index
        
    Returns:
        Predicted score
    """
    # Get all scores for this user
    scores = predict_scores(svd_model, interaction_matrix, user_index)
    
    # Return score for specific article
    return float(scores[article_index])