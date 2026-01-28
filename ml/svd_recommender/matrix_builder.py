"""
Interaction Matrix Builder for SVD
Builds user-article interaction matrices for collaborative filtering
"""

import numpy as np
from scipy.sparse import csr_matrix
from typing import Dict, List


def build_interaction_matrix(
    interactions: List[Dict],
    user_map: Dict[str, int],
    article_map: Dict[str, int]
) -> csr_matrix:
    """
    Build sparse user-article interaction matrix
    
    Args:
        interactions: List of interaction dictionaries
            Expected format: [
                {"user_id": str, "article_id": str, "weight": float},
                ...
            ]
        user_map: Mapping from user_id to matrix row index
        article_map: Mapping from article_id to matrix column index
        
    Returns:
        Sparse CSR matrix of shape (n_users, n_articles)
    """
    rows = []
    cols = []
    data = []
    
    for inter in interactions:
        user_id = inter.get("user_id")
        article_id = inter.get("article_id")
        weight = inter.get("weight", 1.0)
        
        # Skip if user or article not in mapping
        if user_id not in user_map or article_id not in article_map:
            continue
        
        rows.append(user_map[user_id])
        cols.append(article_map[article_id])
        data.append(weight)
    
    # Get matrix dimensions
    n_users = len(user_map)
    n_articles = len(article_map)
    
    # Create sparse matrix
    matrix = csr_matrix(
        (data, (rows, cols)),
        shape=(n_users, n_articles)
    )
    
    return matrix


def build_interaction_matrix_from_history(
    user_histories: Dict[str, List[Dict]]
) -> tuple:
    """
    Build interaction matrix from user reading histories
    Also returns user and article mappings
    
    Args:
        user_histories: Dictionary mapping user_id to list of articles
            Format: {
                "user_1": [
                    {"article_id": "art1", "clicks": 5, "duration": 120},
                    ...
                ],
                ...
            }
    
    Returns:
        Tuple of (matrix, user_map, article_map)
    """
    # Collect all unique users and articles
    all_users = list(user_histories.keys())
    all_articles = set()
    
    for articles in user_histories.values():
        for article in articles:
            all_articles.add(article.get("article_id"))
    
    all_articles = list(all_articles)
    
    # Create mappings
    user_map = {user_id: idx for idx, user_id in enumerate(all_users)}
    article_map = {art_id: idx for idx, art_id in enumerate(all_articles)}
    
    # Build interactions list
    interactions = []
    for user_id, articles in user_histories.items():
        for article in articles:
            article_id = article.get("article_id")
            
            # Calculate weight from clicks and duration
            clicks = article.get("clicks", 1)
            duration = article.get("duration", 0)
            
            # Weight combines clicks and time spent
            weight = clicks + (duration / 60.0)  # Convert duration to minutes
            
            interactions.append({
                "user_id": user_id,
                "article_id": article_id,
                "weight": weight
            })
    
    # Build matrix
    matrix = build_interaction_matrix(interactions, user_map, article_map)
    
    return matrix, user_map, article_map


def add_interaction_to_matrix(
    matrix: csr_matrix,
    user_idx: int,
    article_idx: int,
    weight: float
):
    """
    Add or update single interaction in matrix
    Note: This returns a new matrix (sparse matrices are immutable)
    
    Args:
        matrix: Existing interaction matrix
        user_idx: User index
        article_idx: Article index
        weight: Interaction weight
        
    Returns:
        Updated matrix
    """
    # Convert to LIL format for efficient updates
    lil_matrix = matrix.tolil()
    
    # Update value
    lil_matrix[user_idx, article_idx] = weight
    
    # Convert back to CSR
    return lil_matrix.tocsr()


def get_user_interactions(matrix: csr_matrix, user_idx: int) -> np.ndarray:
    """
    Get all interactions for a specific user
    
    Args:
        matrix: Interaction matrix
        user_idx: User index
        
    Returns:
        Array of interaction weights for this user
    """
    return matrix[user_idx].toarray().flatten()


def get_article_interactions(matrix: csr_matrix, article_idx: int) -> np.ndarray:
    """
    Get all interactions for a specific article
    
    Args:
        matrix: Interaction matrix
        article_idx: Article index
        
    Returns:
        Array of interaction weights for this article
    """
    return matrix[:, article_idx].toarray().flatten()


def normalize_matrix(matrix: csr_matrix, method: str = "user") -> csr_matrix:
    """
    Normalize interaction matrix
    
    Args:
        matrix: Interaction matrix
        method: "user" (row normalization) or "article" (column normalization)
        
    Returns:
        Normalized matrix
    """
    if method == "user":
        # Normalize by user (each row sums to 1)
        row_sums = np.array(matrix.sum(axis=1)).flatten()
        row_sums[row_sums == 0] = 1  # Avoid division by zero
        row_indices, col_indices = matrix.nonzero()
        matrix.data = matrix.data / row_sums[row_indices]
        
    elif method == "article":
        # Normalize by article (each column sums to 1)
        col_sums = np.array(matrix.sum(axis=0)).flatten()
        col_sums[col_sums == 0] = 1  # Avoid division by zero
        row_indices, col_indices = matrix.nonzero()
        matrix.data = matrix.data / col_sums[col_indices]
    
    return matrix