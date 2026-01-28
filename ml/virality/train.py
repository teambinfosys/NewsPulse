"""
Virality Model Training
Trains XGBoost classifier for predicting viral articles
"""

import xgboost as xgb
import joblib
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score, classification_report
import numpy as np


def train_virality_model(X, y, model_path="virality_model.pkl"):
    """
    Train XGBoost virality classifier using engagement features
    
    Args:
        X: Feature matrix (n_samples x n_features)
        y: Binary labels (0 = not viral, 1 = viral)
        model_path: Path to save trained model
        
    Returns:
        Trained XGBoost model
    """
    print(f"Training virality model on {len(X)} samples...")
    
    # Initialize XGBoost classifier
    model = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=4,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        eval_metric="logloss",
        random_state=42
    )
    
    # Train model
    model.fit(X, y)
    
    # Save model
    joblib.dump(model, model_path)
    print(f"✅ Model saved to {model_path}")
    
    return model


def train_and_evaluate_virality_model(X, y, test_size=0.2, model_path="virality_model.pkl"):
    """
    Train and evaluate virality model with train/test split
    
    Args:
        X: Feature matrix
        y: Binary labels
        test_size: Proportion of data for testing
        model_path: Path to save model
        
    Returns:
        Tuple of (model, metrics_dict)
    """
    print(f"Training with train/test split (test_size={test_size})...")
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=42, stratify=y
    )
    
    print(f"Train size: {len(X_train)}, Test size: {len(X_test)}")
    
    # Train model
    model = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=4,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        eval_metric="logloss",
        random_state=42
    )
    
    model.fit(X_train, y_train)
    
    # Evaluate
    metrics = evaluate_virality_model(model, X_test, y_test)
    
    # Save model
    joblib.dump(model, model_path)
    print(f"✅ Model saved to {model_path}")
    
    return model, metrics


def evaluate_virality_model(model, X_test, y_test):
    """
    Evaluate virality prediction model
    
    Args:
        model: Trained model
        X_test: Test features
        y_test: Test labels
        
    Returns:
        Dictionary of metrics
    """
    # Predictions
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]
    
    # Calculate metrics
    metrics = {
        "accuracy": accuracy_score(y_test, y_pred),
        "f1_score": f1_score(y_test, y_pred),
        "roc_auc": roc_auc_score(y_test, y_prob)
    }
    
    print("\n" + "="*50)
    print("VIRALITY MODEL EVALUATION")
    print("="*50)
    print(f"Accuracy:  {metrics['accuracy']:.4f}")
    print(f"F1 Score:  {metrics['f1_score']:.4f}")
    print(f"ROC AUC:   {metrics['roc_auc']:.4f}")
    print("="*50)
    
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=['Not Viral', 'Viral']))
    
    return metrics


def get_feature_importance(model, feature_names=None):
    """
    Get feature importance from trained model
    
    Args:
        model: Trained XGBoost model
        feature_names: List of feature names
        
    Returns:
        Dictionary of feature importances
    """
    importances = model.feature_importances_
    
    if feature_names is None:
        feature_names = [f"feature_{i}" for i in range(len(importances))]
    
    importance_dict = dict(zip(feature_names, importances))
    
    # Sort by importance
    sorted_importance = sorted(
        importance_dict.items(),
        key=lambda x: x[1],
        reverse=True
    )
    
    print("\nFeature Importances:")
    print("="*50)
    for feature, importance in sorted_importance:
        print(f"{feature:25s}: {importance:.4f}")
    print("="*50)
    
    return importance_dict


def save_model(model, path: str):
    """
    Save trained model to disk
    
    Args:
        model: Trained model
        path: File path to save to
    """
    joblib.dump(model, path)
    print(f"✅ Model saved to {path}")


def load_model(path: str):
    """
    Load trained model from disk
    
    Args:
        path: File path to load from
        
    Returns:
        Loaded model
    """
    model = joblib.load(path)
    print(f"✅ Model loaded from {path}")
    return model