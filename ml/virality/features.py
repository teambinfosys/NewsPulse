"""
Virality Feature Engineering
Builds features for predicting article virality
"""

import numpy as np
import pandas as pd


def compute_ctr(clicks: int, impressions: int) -> float:
    """
    Compute Click Through Rate safely
    
    Args:
        clicks: Number of clicks
        impressions: Number of impressions
        
    Returns:
        CTR value (0-1)
    """
    if impressions == 0:
        return 0.0
    return clicks / impressions


def build_virality_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build virality features from article engagement data
    
    Required columns in df:
    - clicks: Number of clicks
    - impressions: Number of impressions
    - time_since_published: Hours since publication
    
    Args:
        df: DataFrame with raw engagement metrics
        
    Returns:
        DataFrame with engineered features
    """
    df = df.copy()
    
    # Feature 1: Click-Through Rate (CTR)
    df["ctr"] = df.apply(
        lambda row: compute_ctr(row["clicks"], row["impressions"]),
        axis=1
    )
    
    # Feature 2: Log-scaled impressions (for stability)
    df["log_impressions"] = np.log1p(df["impressions"])
    
    # Feature 3: Log-scaled clicks
    df["log_clicks"] = np.log1p(df["clicks"])
    
    # Feature 4: Time decay factor (freshness)
    # More recent articles get higher scores
    df["freshness"] = 1 / (1 + df["time_since_published"])
    
    # Feature 5: Engagement rate (clicks per hour)
    df["engagement_rate"] = df["clicks"] / (df["time_since_published"] + 1)
    
    # Feature 6: Impression velocity (impressions per hour)
    df["impression_velocity"] = df["impressions"] / (df["time_since_published"] + 1)
    
    # Select features for model
    feature_columns = [
        "ctr",
        "log_impressions",
        "log_clicks",
        "freshness",
        "engagement_rate",
        "impression_velocity"
    ]
    
    return df[feature_columns]


def build_virality_features_simple(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build simplified virality features (3 features only)
    Used when data is limited
    
    Args:
        df: DataFrame with raw metrics
        
    Returns:
        DataFrame with 3 core features
    """
    df = df.copy()
    
    # Core feature 1: CTR
    df["ctr"] = df.apply(
        lambda row: compute_ctr(row["clicks"], row["impressions"]),
        axis=1
    )
    
    # Core feature 2: Log impressions
    df["log_impressions"] = np.log1p(df["impressions"])
    
    # Core feature 3: Freshness
    df["freshness"] = 1 / (1 + df["time_since_published"])
    
    return df[["ctr", "log_impressions", "freshness"]]


def extract_virality_features_from_dict(article_stats: dict) -> np.ndarray:
    """
    Extract virality features from a single article's stats dictionary
    
    Args:
        article_stats: Dictionary with keys:
            - clicks
            - impressions
            - time_since_published
            
    Returns:
        Feature vector as numpy array
    """
    clicks = article_stats.get("clicks", 0)
    impressions = article_stats.get("impressions", 1)
    time_since = article_stats.get("time_since_published", 24.0)
    
    # Calculate features
    ctr = compute_ctr(clicks, impressions)
    log_impressions = np.log1p(impressions)
    log_clicks = np.log1p(clicks)
    freshness = 1 / (1 + time_since)
    engagement_rate = clicks / (time_since + 1)
    impression_velocity = impressions / (time_since + 1)
    
    # Return as array (same order as training features)
    return np.array([
        ctr,
        log_impressions,
        log_clicks,
        freshness,
        engagement_rate,
        impression_velocity
    ])