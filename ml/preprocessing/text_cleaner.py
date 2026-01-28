"""
Text preprocessing and cleaning using NLTK
"""

import re
import string
from typing import List

try:
    import nltk
    from nltk.corpus import stopwords
    from nltk.stem import WordNetLemmatizer
    
    # Download required NLTK data (run once)
    try:
        nltk.data.find('corpora/stopwords')
    except LookupError:
        nltk.download('stopwords', quiet=True)
    
    try:
        nltk.data.find('corpora/wordnet')
    except LookupError:
        nltk.download('wordnet', quiet=True)
    
    _STOPWORDS = set(stopwords.words("english"))
    _LEMMATIZER = WordNetLemmatizer()
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False
    _STOPWORDS = set()
    _LEMMATIZER = None


def clean_text(text: str) -> str:
    """
    Clean raw news text using NLTK
    
    Args:
        text: Raw article text
        
    Returns:
        Cleaned and normalized text
    """
    if not text:
        return ""
    
    # Convert to lowercase
    text = text.lower()
    
    # Remove URLs
    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"www\S+", "", text)
    
    # Remove email addresses
    text = re.sub(r'\S+@\S+', '', text)
    
    # Remove punctuation
    text = text.translate(str.maketrans("", "", string.punctuation))
    
    # Remove numbers
    text = re.sub(r'\d+', '', text)
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Tokenize
    tokens: List[str] = text.split()
    
    if NLTK_AVAILABLE and _LEMMATIZER:
        # Remove stopwords and lemmatize
        tokens = [
            _LEMMATIZER.lemmatize(tok)
            for tok in tokens
            if tok not in _STOPWORDS and len(tok) > 2
        ]
    else:
        # Basic filtering without NLTK
        tokens = [tok for tok in tokens if len(tok) > 2]
    
    return " ".join(tokens)


def clean_text_simple(text: str) -> str:
    """
    Simple text cleaning without NLTK (fallback)
    
    Args:
        text: Raw article text
        
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    # Convert to lowercase
    text = text.lower()
    
    # Remove URLs and special characters
    text = re.sub(r"http\S+|www\S+|https\S+", '', text)
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\d+', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text


# Alias for backward compatibility
preprocess_text = clean_text