"""
SVD Model Training for Collaborative Filtering
Trains Truncated SVD on user-article interaction matrix
"""

from sklearn.decomposition import TruncatedSVD
import joblib
import numpy as np


def train_svd(matrix, n_components: int = 50, random_state: int = 42):
    """
    Train SVD model on interaction matrix
    
    Args:
        matrix: User-article interaction matrix (sparse)
        n_components: Number of latent factors
        random_state: Random seed for reproducibility
        
    Returns:
        Fitted TruncatedSVD model
    """
    n_users, n_items = matrix.shape
    
    # Adjust n_components based on matrix dimensions
    max_components = min(n_users - 1, n_items - 1)
    
    if max_components <= 0:
        raise ValueError(f"Not enough data to train SVD. Matrix shape: {matrix.shape}")
    
    # Use minimum of requested components and maximum possible
    n_components = min(n_components, max_components)
    
    print(f"Training SVD with {n_components} components on matrix shape {matrix.shape}")
    
    # Initialize and fit SVD
    svd = TruncatedSVD(
        n_components=n_components,
        random_state=random_state,
        algorithm='randomized',
        n_iter=5
    )
    
    svd.fit(matrix)
    
    # Print explained variance
    explained_var = svd.explained_variance_ratio_.sum()
    print(f"✅ SVD trained. Explained variance: {explained_var:.4f}")
    
    return svd


def train_svd_with_validation(
    train_matrix,
    val_matrix=None,
    n_components: int = 50,
    random_state: int = 42
):
    """
    Train SVD with validation
    
    Args:
        train_matrix: Training interaction matrix
        val_matrix: Validation interaction matrix (optional)
        n_components: Number of components
        random_state: Random seed
        
    Returns:
        Tuple of (model, train_error, val_error)
    """
    # Train model
    svd = train_svd(train_matrix, n_components, random_state)
    
    # Calculate reconstruction error on training set
    train_reconstructed = svd.inverse_transform(svd.transform(train_matrix))
    train_error = np.mean((train_matrix.toarray() - train_reconstructed) ** 2)
    
    print(f"Training reconstruction error: {train_error:.6f}")
    
    # Calculate validation error if validation set provided
    val_error = None
    if val_matrix is not None:
        val_reconstructed = svd.inverse_transform(svd.transform(val_matrix))
        val_error = np.mean((val_matrix.toarray() - val_reconstructed) ** 2)
        print(f"Validation reconstruction error: {val_error:.6f}")
    
    return svd, train_error, val_error


def get_user_factors(svd, matrix):
    """
    Get user latent factor representations
    
    Args:
        svd: Trained SVD model
        matrix: User-article interaction matrix
        
    Returns:
        User factor matrix (n_users x n_components)
    """
    return svd.transform(matrix)


def get_article_factors(svd):
    """
    Get article latent factor representations
    
    Args:
        svd: Trained SVD model
        
    Returns:
        Article factor matrix (n_components x n_articles)
    """
    return svd.components_


def reconstruct_matrix(svd, matrix):
    """
    Reconstruct interaction matrix from SVD
    
    Args:
        svd: Trained SVD model
        matrix: Original interaction matrix
        
    Returns:
        Reconstructed matrix
    """
    return svd.inverse_transform(svd.transform(matrix))


def save_model(model, path: str):
    """
    Save SVD model to disk
    
    Args:
        model: Trained SVD model
        path: File path to save
    """
    joblib.dump(model, path)
    print(f"✅ SVD model saved to {path}")


def load_model(path: str):
    """
    Load SVD model from disk
    
    Args:
        path: File path to load from
        
    Returns:
        Loaded SVD model
    """
    model = joblib.load(path)
    print(f"✅ SVD model loaded from {path}")
    return model


def find_optimal_components(
    matrix,
    component_range: range = range(10, 101, 10),
    random_state: int = 42
):
    """
    Find optimal number of components by testing different values
    
    Args:
        matrix: Interaction matrix
        component_range: Range of component counts to test
        random_state: Random seed
        
    Returns:
        Dictionary with component counts and their explained variance
    """
    results = {}
    
    n_users, n_items = matrix.shape
    max_components = min(n_users - 1, n_items - 1)
    
    print(f"Testing component counts from {min(component_range)} to {min(max(component_range), max_components)}")
    
    for n_comp in component_range:
        if n_comp >= max_components:
            break
        
        svd = TruncatedSVD(
            n_components=n_comp,
            random_state=random_state,
            algorithm='randomized'
        )
        
        svd.fit(matrix)
        
        explained_var = svd.explained_variance_ratio_.sum()
        results[n_comp] = explained_var
        
        print(f"  n_components={n_comp:3d}: explained_variance={explained_var:.4f}")
    
    # Find best
    best_n = max(results, key=results.get)
    print(f"\n✅ Best n_components: {best_n} (explained variance: {results[best_n]:.4f})")
    
    return results