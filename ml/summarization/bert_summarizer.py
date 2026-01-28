"""
BERT-based Article Summarization
Uses pre-trained transformer models for extractive summarization
"""

try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    print("⚠️  transformers not installed. Summarization will use fallback method.")


# Global summarizer instance (loaded once)
_summarizer = None


def _load_summarizer():
    """
    Lazy load the summarization model
    """
    global _summarizer
    
    if _summarizer is None and TRANSFORMERS_AVAILABLE:
        try:
            print("Loading BART summarization model...")
            _summarizer = pipeline(
                "summarization",
                model="facebook/bart-large-cnn",
                device=-1  # Use CPU
            )
            print("✅ Summarizer loaded successfully")
        except Exception as e:
            print(f"⚠️  Failed to load summarizer: {e}")
            _summarizer = None
    
    return _summarizer


def summarize_article(text: str, max_length: int = 130, min_length: int = 30) -> str:
    """
    Summarize article text using BART model
    
    Args:
        text: Full article text
        max_length: Maximum summary length in words
        min_length: Minimum summary length in words
        
    Returns:
        Summarized text
    """
    if not text or len(text.strip()) == 0:
        return ""
    
    # Try to use transformer model
    summarizer = _load_summarizer()
    
    if summarizer is not None:
        try:
            # Truncate text if too long (BART has max input length)
            max_input_length = 1024
            if len(text.split()) > max_input_length:
                text = ' '.join(text.split()[:max_input_length])
            
            # Generate summary
            summary = summarizer(
                text,
                max_length=max_length,
                min_length=min_length,
                do_sample=False
            )
            
            return summary[0]["summary_text"]
        
        except Exception as e:
            print(f"Summarization error: {e}")
            return fallback_summarize(text, max_length)
    
    else:
        # Use fallback method
        return fallback_summarize(text, max_length)


def fallback_summarize(text: str, max_length: int = 130) -> str:
    """
    Simple extractive summarization fallback
    Takes first N sentences up to max_length words
    
    Args:
        text: Full article text
        max_length: Maximum summary length in words
        
    Returns:
        Summary text
    """
    import re
    
    # Split into sentences
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    if not sentences:
        return ""
    
    # Build summary by adding sentences until reaching max_length
    summary = []
    word_count = 0
    
    for sentence in sentences:
        sentence_words = len(sentence.split())
        
        if word_count + sentence_words <= max_length:
            summary.append(sentence)
            word_count += sentence_words
        else:
            break
    
    if not summary:
        # If first sentence is too long, truncate it
        first_sentence = sentences[0]
        words = first_sentence.split()[:max_length]
        return ' '.join(words) + '...'
    
    return '. '.join(summary) + '.'


def summarize_article_batch(texts: list, max_length: int = 130) -> list:
    """
    Summarize multiple articles in batch
    
    Args:
        texts: List of article texts
        max_length: Maximum summary length
        
    Returns:
        List of summaries
    """
    summaries = []
    
    for text in texts:
        summary = summarize_article(text, max_length=max_length)
        summaries.append(summary)
    
    return summaries


def get_key_sentences(text: str, num_sentences: int = 3) -> list:
    """
    Extract key sentences from article
    
    Args:
        text: Full article text
        num_sentences: Number of key sentences to extract
        
    Returns:
        List of key sentences
    """
    import re
    from collections import Counter
    
    # Split into sentences
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip() and len(s.split()) > 5]
    
    if len(sentences) <= num_sentences:
        return sentences
    
    # Simple scoring: sentences with more frequent words are more important
    words = text.lower().split()
    word_freq = Counter(words)
    
    # Remove very common words
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for'}
    for word in stop_words:
        word_freq.pop(word, None)
    
    # Score sentences
    sentence_scores = []
    for sentence in sentences:
        score = sum(word_freq.get(word.lower(), 0) for word in sentence.split())
        sentence_scores.append((sentence, score))
    
    # Sort by score and take top N
    sentence_scores.sort(key=lambda x: x[1], reverse=True)
    key_sentences = [s for s, _ in sentence_scores[:num_sentences]]
    
    return key_sentences


def extractive_summary(text: str, num_sentences: int = 3) -> str:
    """
    Create extractive summary by selecting key sentences
    
    Args:
        text: Full article text
        num_sentences: Number of sentences in summary
        
    Returns:
        Summary text
    """
    key_sentences = get_key_sentences(text, num_sentences)
    return '. '.join(key_sentences) + '.' if key_sentences else ""