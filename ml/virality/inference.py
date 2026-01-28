"""
Virality Prediction Inference
Real-time prediction of article virality
"""

import joblib
import numpy as np
import os


# Global model instance (loaded once)
_predictor = None
_model_path = os.path.join(os.path.dirname(__file__), "..", "..", "models", "virality_model.pkl")


class ViralityPredictor:
    """
    Wrapper class for virality prediction model
    """
    
    def __init__(self, model_path: str = None):
        """
        Initialize predictor with trained model
        
        Args:
            model_path: Path to saved model file
        """
        if model_path is None:
            model_path = _model_path
        
        try:
            self.model = joblib.load(model_path)
            print(f"✅ Virality model loaded from {model_path}")
        except FileNotFoundError:
            print(f"⚠️  Virality model not found at {model_path}")
            print("    Using fallback prediction (random scores)")
            self.model = None
    
    def predict(
        self,
        ctr: float,
        impressions: int,
        time_since_published: float
    ) -> float:
        """
        Predict probability of article being viral
        
        Args:
            ctr: Click-through rate (0-1)
            impressions: Number of impressions
            time_since_published: Hours since published
            
        Returns:
            Probability of being viral (0-1)
        """
        if self.model is None:
            # Fallback: simple heuristic
            return min(ctr * 2, 1.0) * 0.5 + min(impressions / 10000, 1.0) * 0.3 + (1 / (1 + time_since_published)) * 0.2
        
        # Calculate features
        log_impressions = np.log1p(impressions)
        log_clicks = np.log1p(int(ctr * impressions))
        freshness = 1 / (1 + time_since_published)
        engagement_rate = (ctr * impressions) / (time_since_published + 1)
        impression_velocity = impressions / (time_since_published + 1)
        
        # Create feature vector (same order as training)
        X = np.array([[
            ctr,
            log_impressions,
            log_clicks,
            freshness,
            engagement_rate,
            impression_velocity
        ]])
        
        # Predict probability
        try:
            prob = float(self.model.predict_proba(X)[0][1])
            return prob
        except Exception as e:
            print(f"Prediction error: {e}")
            return 0.5
    
    def predict_batch(self, features: np.ndarray) -> np.ndarray:
        """
        Predict virality for multiple articles
        
        Args:
            features: Feature matrix (n_samples x n_features)
            
        Returns:
            Array of virality probabilities
        """
        if self.model is None:
            return np.random.uniform(0.3, 0.7, size=len(features))
        
        return self.model.predict_proba(features)[:, 1]


def predict_virality(article_stats: dict) -> float:
    """
    Predict virality score from raw article statistics
    This is the main function called by the backend API
    
    Args:
        article_stats: Dictionary with keys:
            - clicks: int
            - impressions: int
            - time_since_published: float (hours)
    
    Returns:
        Virality probability (0-1)
    """
    global _predictor
    
    # Lazy load predictor
    if _predictor is None:
        _predictor = ViralityPredictor()
    
    # Extract stats
    clicks = article_stats.get("clicks", 0)
    impressions = article_stats.get("impressions", 1)
    time_since_published = article_stats.get("time_since_published", 24.0)
    
    # Calculate CTR
    ctr = clicks / max(impressions, 1)
    
    # Predict
    return _predictor.predict(
        ctr=ctr,
        impressions=impressions,
        time_since_published=time_since_published
    )


def load_model(model_path: str):
    """
    Load virality model from disk
    
    Args:
        model_path: Path to model file
        
    Returns:
        Loaded model or None
    """
    try:
        model = joblib.load(model_path)
        return model
    except Exception as e:
        print(f"Error loading model: {e}")
        return None


def predict_with_model(model, article_stats: dict) -> float:
    """
    Predict using a specific model instance
    
    Args:
        model: Loaded model
        article_stats: Article statistics
        
    Returns:
        Virality score
    """
    clicks = article_stats.get("clicks", 0)
    impressions = article_stats.get("impressions", 1)
    time_since = article_stats.get("time_since_published", 24.0)
    
    ctr = clicks / max(impressions, 1)
    log_impressions = np.log1p(impressions)
    log_clicks = np.log1p(clicks)
    freshness = 1 / (1 + time_since)
    engagement_rate = clicks / (time_since + 1)
    impression_velocity = impressions / (time_since + 1)
    
    X = np.array([[ctr, log_impressions, log_clicks, freshness, engagement_rate, impression_velocity]])
    
    return float(model.predict_proba(X)[0][1])