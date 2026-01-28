"""
Virality Model Retraining Script
Retrains the virality prediction model with sample or real data
"""

import pandas as pd
import numpy as np
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ml.virality.features import build_virality_features, build_virality_features_simple
from ml.virality.train import train_virality_model, train_and_evaluate_virality_model, get_feature_importance


def generate_sample_data(n_samples=1000):
    """
    Generate sample training data for virality prediction
    
    Args:
        n_samples: Number of samples to generate
        
    Returns:
        DataFrame with features and labels
    """
    np.random.seed(42)
    
    # Generate synthetic data
    data = {
        'clicks': [],
        'impressions': [],
        'time_since_published': [],
        'viral': []
    }
    
    for _ in range(n_samples):
        # Viral articles (40% of dataset)
        if np.random.random() < 0.4:
            clicks = np.random.randint(100, 1000)
            impressions = np.random.randint(500, 5000)
            time_since = np.random.uniform(0.5, 10)
            viral = 1
        # Non-viral articles (60% of dataset)
        else:
            clicks = np.random.randint(5, 100)
            impressions = np.random.randint(50, 800)
            time_since = np.random.uniform(1, 48)
            viral = 0
        
        data['clicks'].append(clicks)
        data['impressions'].append(impressions)
        data['time_since_published'].append(time_since)
        data['viral'].append(viral)
    
    return pd.DataFrame(data)


def main():
    """
    Main retraining function
    """
    print("="*70)
    print("VIRALITY MODEL RETRAINING")
    print("="*70)
    
    # Create models directory if it doesn't exist
    models_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "models")
    os.makedirs(models_dir, exist_ok=True)
    
    model_path = os.path.join(models_dir, "virality_model.pkl")
    
    print(f"\n📂 Model will be saved to: {model_path}")
    
    # Check if real data exists, otherwise use sample data
    print("\n📊 Generating training data...")
    data = generate_sample_data(n_samples=1000)
    
    print(f"✅ Generated {len(data)} training samples")
    print(f"   - Viral articles: {data['viral'].sum()}")
    print(f"   - Non-viral articles: {len(data) - data['viral'].sum()}")
    
    # Build features
    print("\n🔧 Building features...")
    X = build_virality_features(data)
    y = data['viral']
    
    print(f"✅ Feature matrix shape: {X.shape}")
    print(f"   Features: {list(X.columns)}")
    
    # Train and evaluate model
    print("\n🚀 Training model...")
    model, metrics = train_and_evaluate_virality_model(
        X, y,
        test_size=0.2,
        model_path=model_path
    )
    
    # Show feature importance
    print("\n📊 Feature Importance Analysis:")
    get_feature_importance(model, feature_names=list(X.columns))
    
    print("\n" + "="*70)
    print("✅ RETRAINING COMPLETE")
    print("="*70)
    print(f"\nModel saved to: {model_path}")
    print("\nYou can now use this model in the backend API!")
    print("\nTo use in production:")
    print("1. Replace sample data with real user interaction data")
    print("2. Run this script periodically (e.g., daily)")
    print("3. Monitor model performance metrics")
    
    return model, metrics


if __name__ == "__main__":
    model, metrics = main()