"""
TF-IDF Article Vectorizer
Converts article text into TF-IDF feature vectors
"""

from typing import List, Dict
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np


class TfidfArticleVectorizer:
    """
    Vectorize articles using TF-IDF
    """
    
    def __init__(self, max_features: int = 15000, min_df: int = 1):
        """
        Initialize TF-IDF vectorizer
        
        Args:
            max_features: Maximum number of features to extract
            min_df: Minimum document frequency
        """
        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),  # Use unigrams and bigrams
            max_features=max_features,
            min_df=min_df,
            stop_words='english',
            lowercase=True,
            strip_accents='unicode'
        )
        self.article_id_to_index: Dict[str, int] = {}
        self.tfidf_matrix = None
    
    def fit_transform(self, article_ids: List[str], texts: List[str]) -> None:
        """
        Fit vectorizer and transform articles
        
        Args:
            article_ids: List of article identifiers
            texts: List of article texts
        """
        # Transform texts to TF-IDF matrix
        self.tfidf_matrix = self.vectorizer.fit_transform(texts)
        
        # Create article ID to matrix index mapping
        self.article_id_to_index = {
            aid: idx for idx, aid in enumerate(article_ids)
        }
    
    def transform(self, texts: List[str]):
        """
        Transform new texts using fitted vectorizer
        
        Args:
            texts: List of article texts
            
        Returns:
            TF-IDF matrix
        """
        if self.vectorizer is None:
            raise ValueError("Vectorizer not fitted. Call fit_transform first.")
        
        return self.vectorizer.transform(texts)
    
    def get_article_vector(self, article_id: str) -> np.ndarray:
        """
        Get TF-IDF vector for a specific article
        
        Args:
            article_id: Article identifier
            
        Returns:
            TF-IDF vector as numpy array
        """
        idx = self.article_id_to_index.get(article_id)
        if idx is None:
            raise ValueError(f"Article {article_id} not found in index")
        
        return self.tfidf_matrix[idx].toarray()[0]
    
    def get_feature_names(self) -> List[str]:
        """
        Get feature names (words/terms)
        
        Returns:
            List of feature names
        """
        return self.vectorizer.get_feature_names_out().tolist()
    
    def get_top_terms(self, article_id: str, top_n: int = 10) -> List[tuple]:
        """
        Get top N terms for an article
        
        Args:
            article_id: Article identifier
            top_n: Number of top terms to return
            
        Returns:
            List of (term, score) tuples
        """
        vector = self.get_article_vector(article_id)
        feature_names = self.get_feature_names()
        
        # Get indices of top N values
        top_indices = vector.argsort()[-top_n:][::-1]
        
        return [(feature_names[i], vector[i]) for i in top_indices]