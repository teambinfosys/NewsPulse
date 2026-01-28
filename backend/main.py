"""
NewsPulse - Updated Backend with Dynamic Country Support
"""

from fastapi import FastAPI, HTTPException, Depends, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
import httpx
import os
from datetime import datetime, timedelta
import jwt
import bcrypt
from dotenv import load_dotenv
import numpy as np
import sys

# Add parent directory to path for ML imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import database functions
from database import (
    UserDB, InterestDB, SessionDB, PreferencesDB,
    SavedArticlesDB, ReadingHistoryDB, ActivityLogDB
)

# Import ML components
try:
    from ml.tfidf_recommender.vectorizer import TfidfArticleVectorizer
    from ml.tfidf_recommender.user_profile import build_user_profile
    from ml.tfidf_recommender.recommender import recommend_articles
    from ml.virality.inference import predict_virality
    from ml.preprocessing.text_cleaner import clean_text
    ML_AVAILABLE = True
except ImportError as e:
    print(f"ML modules not available: {e}")
    ML_AVAILABLE = False

# Initialize FastAPI
app = FastAPI(title="NewsPulse API", version="2.0.0")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
load_dotenv()
NEWS_API_KEY = os.getenv("NEWSDATA_API_KEY")
NEWS_API_BASE_URL = "https://newsdata.io/api/1/latest"  # Changed from /news to /latest
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

# Validate API key on startup
if not NEWS_API_KEY or NEWS_API_KEY == "YOUR_API_KEY_HERE":
    print("⚠️  WARNING: NEWSDATA_API_KEY not properly configured in .env file")
    print(f"   Current value: {NEWS_API_KEY}")
else:
    print(f"✅ NewsData API Key loaded: {NEWS_API_KEY[:10]}...{NEWS_API_KEY[-4:]}")

# ===== SUPPORTED COUNTRIES =====
SUPPORTED_COUNTRIES = [
    {"code": "", "name": "Global", "flag": "🌍"},
    {"code": "ae", "name": "United Arab Emirates", "flag": "🇦🇪"},
    {"code": "ar", "name": "Argentina", "flag": "🇦🇷"},
    {"code": "at", "name": "Austria", "flag": "🇦🇹"},
    {"code": "au", "name": "Australia", "flag": "🇦🇺"},
    {"code": "be", "name": "Belgium", "flag": "🇧🇪"},
    {"code": "bg", "name": "Bulgaria", "flag": "🇧🇬"},
    {"code": "br", "name": "Brazil", "flag": "🇧🇷"},
    {"code": "ca", "name": "Canada", "flag": "🇨🇦"},
    {"code": "ch", "name": "Switzerland", "flag": "🇨🇭"},
    {"code": "cn", "name": "China", "flag": "🇨🇳"},
    {"code": "co", "name": "Colombia", "flag": "🇨🇴"},
    {"code": "cu", "name": "Cuba", "flag": "🇨🇺"},
    {"code": "cz", "name": "Czech Republic", "flag": "🇨🇿"},
    {"code": "de", "name": "Germany", "flag": "🇩🇪"},
    {"code": "eg", "name": "Egypt", "flag": "🇪🇬"},
    {"code": "fr", "name": "France", "flag": "🇫🇷"},
    {"code": "gb", "name": "United Kingdom", "flag": "🇬🇧"},
    {"code": "gr", "name": "Greece", "flag": "🇬🇷"},
    {"code": "hk", "name": "Hong Kong", "flag": "🇭🇰"},
    {"code": "hu", "name": "Hungary", "flag": "🇭🇺"},
    {"code": "id", "name": "Indonesia", "flag": "🇮🇩"},
    {"code": "ie", "name": "Ireland", "flag": "🇮🇪"},
    {"code": "il", "name": "Israel", "flag": "🇮🇱"},
    {"code": "in", "name": "India", "flag": "🇮🇳"},
    {"code": "it", "name": "Italy", "flag": "🇮🇹"},
    {"code": "jp", "name": "Japan", "flag": "🇯🇵"},
    {"code": "kr", "name": "South Korea", "flag": "🇰🇷"},
    {"code": "lt", "name": "Lithuania", "flag": "🇱🇹"},
    {"code": "lv", "name": "Latvia", "flag": "🇱🇻"},
    {"code": "ma", "name": "Morocco", "flag": "🇲🇦"},
    {"code": "mx", "name": "Mexico", "flag": "🇲🇽"},
    {"code": "my", "name": "Malaysia", "flag": "🇲🇾"},
    {"code": "ng", "name": "Nigeria", "flag": "🇳🇬"},
    {"code": "nl", "name": "Netherlands", "flag": "🇳🇱"},
    {"code": "no", "name": "Norway", "flag": "🇳🇴"},
    {"code": "nz", "name": "New Zealand", "flag": "🇳🇿"},
    {"code": "ph", "name": "Philippines", "flag": "🇵🇭"},
    {"code": "pl", "name": "Poland", "flag": "🇵🇱"},
    {"code": "pt", "name": "Portugal", "flag": "🇵🇹"},
    {"code": "ro", "name": "Romania", "flag": "🇷🇴"},
    {"code": "rs", "name": "Serbia", "flag": "🇷🇸"},
    {"code": "ru", "name": "Russia", "flag": "🇷🇺"},
    {"code": "sa", "name": "Saudi Arabia", "flag": "🇸🇦"},
    {"code": "se", "name": "Sweden", "flag": "🇸🇪"},
    {"code": "sg", "name": "Singapore", "flag": "🇸🇬"},
    {"code": "si", "name": "Slovenia", "flag": "🇸🇮"},
    {"code": "sk", "name": "Slovakia", "flag": "🇸🇰"},
    {"code": "th", "name": "Thailand", "flag": "🇹🇭"},
    {"code": "tr", "name": "Turkey", "flag": "🇹🇷"},
    {"code": "tw", "name": "Taiwan", "flag": "🇹🇼"},
    {"code": "ua", "name": "Ukraine", "flag": "🇺🇦"},
    {"code": "us", "name": "United States", "flag": "🇺🇸"},
    {"code": "ve", "name": "Venezuela", "flag": "🇻🇪"},
    {"code": "za", "name": "South Africa", "flag": "🇿🇦"}
]

# ===== GLOBAL ML STATE =====
article_vectorizer = None
article_cache: Dict[str, Dict] = {}
is_ml_ready = False
api_cache: Dict[str, Dict] = {}  # Cache for API responses
cache_timestamps: Dict[str, datetime] = {}  # Track cache age
session_article_cache: Dict[str, set] = {}  # Track all seen URLs per user session/filter to prevent duplicates across pagination
CACHE_DURATION_MINUTES = 30  # Cache valid for 30 minutes

if ML_AVAILABLE:
    article_vectorizer = TfidfArticleVectorizer(max_features=5000, min_df=1)

# ===== MODELS =====
class SignupRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    interests: List[str]
    country: Optional[str] = None
    state: Optional[str] = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class SaveArticleRequest(BaseModel):
    url: str
    title: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    source: Optional[str] = None
    published_at: Optional[str] = None
    notes: Optional[str] = None

class ArticleInteractionRequest(BaseModel):
    article_url: str
    article_title: str
    category: Optional[str] = None
    duration_seconds: int = 0

# ===== HELPER FUNCTIONS =====
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_token(user_id: int) -> str:
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(days=7)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str) -> Optional[int]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("user_id")
    except:
        return None

def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = authorization.split(" ")[1]
    user_id = verify_token(token)
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    user = UserDB.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user

# ===== DEDUPLICATION HELPER =====
def deduplicate_articles(articles: List[Dict]) -> List[Dict]:
    """
    Remove duplicate articles from a list.
    
    Uses URL as primary key for deduplication.
    Handles both NewsData.io ('link') and standard ('url') field names.
    
    Args:
        articles: List of article dictionaries
        
    Returns:
        List of unique articles (order preserved)
    """
    seen_urls = set()
    unique_articles = []
    
    for article in articles:
        # Get URL with fallback to 'link' field (NewsData.io)
        article_url = article.get('url') or article.get('link')
        
        # Skip articles without URL
        if not article_url:
            continue
        
        # Skip if we've already seen this URL
        if article_url in seen_urls:
            continue
        
        # Add to seen set and unique list
        seen_urls.add(article_url)
        unique_articles.append(article)
    
    return unique_articles

def extract_article_text(article: Dict) -> str:
    """Extract and clean article text for ML"""
    text_parts = []
    if article.get('title'):
        text_parts.append(article['title'])
    if article.get('description'):
        text_parts.append(article['description'])
    if article.get('content'):
        text_parts.append(article['content'])
    
    full_text = ' '.join(text_parts)
    if ML_AVAILABLE:
        return clean_text(full_text)
    return full_text

def calculate_virality_score(article: Dict) -> float:
    """Calculate virality score for an article"""
    if not ML_AVAILABLE:
        return 0.0
        
    try:
        article_stats = {
            "clicks": article.get("engagement", {}).get("clicks", 0),
            "impressions": article.get("engagement", {}).get("impressions", 1),
            "time_since_published": calculate_hours_since_published(article.get("publishedAt"))
        }
        
        return predict_virality(article_stats)
    except Exception as e:
        print(f"Virality prediction error: {e}")
        return 0.0

def calculate_hours_since_published(published_at: str) -> float:
    """Calculate hours since article was published"""
    try:
        pub_date = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
        delta = datetime.now(pub_date.tzinfo) - pub_date
        return delta.total_seconds() / 3600
    except:
        return 24.0

# ===== NEW ENDPOINT: GET COUNTRIES =====
@app.get("/api/countries")
async def get_countries():
    """Get list of supported countries for news"""
    return {
        "status": "success",
        "countries": SUPPORTED_COUNTRIES
    }

# ===== AUTH ENDPOINTS =====
@app.post("/api/auth/signup")
async def signup(request: SignupRequest, req: Request):
    """Register new user"""
    existing_user = UserDB.get_user_by_email(request.email)
    if existing_user:
        return {"status": "error", "message": "Email already registered"}
    
    password_hash = hash_password(request.password)
    
    # Create user with location
    user_id = UserDB.create_user(
        request.name, 
        request.email, 
        password_hash,
        request.country,
        request.state
    )
    
    if not user_id:
        return {"status": "error", "message": "Failed to create account"}
    
    if request.interests:
        InterestDB.add_user_interests(user_id, request.interests)
    
    ip_address = req.client.host if req.client else None
    ActivityLogDB.log_activity(user_id, "signup", "User registered", ip_address)
    
    return {"status": "success", "message": "Account created successfully"}

@app.post("/api/auth/login")
async def login(request: LoginRequest, req: Request):
    """Login user"""
    user = UserDB.get_user_by_email(request.email)
    
    if not user or not verify_password(request.password, user['password']):
        return {"status": "error", "message": "Invalid email or password"}
    
    token = create_token(user['id'])
    UserDB.update_last_login(user['id'])
    
    expires_at = (datetime.utcnow() + timedelta(days=7)).isoformat()
    ip_address = req.client.host if req.client else None
    user_agent = req.headers.get('user-agent')
    SessionDB.create_session(user['id'], token, expires_at, ip_address, user_agent)
    
    interests = InterestDB.get_user_interests(user['id'])
    interest_names = [i['name'] for i in interests]
    
    ActivityLogDB.log_activity(user['id'], "login", "User logged in", ip_address)
    
    return {
        "status": "success",
        "token": token,
        "user": {
            "id": user['id'],
            "name": user['name'],
            "email": user['email'],
            "interests": interest_names,
            "country": user.get('country'),
            "state": user.get('state')
        }
    }

@app.post("/api/auth/logout")
async def logout(authorization: Optional[str] = Header(None)):
    """Logout user"""
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        SessionDB.invalidate_session(token)
    return {"status": "success", "message": "Logged out successfully"}

@app.get("/api/auth/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    """Get current user info"""
    interests = InterestDB.get_user_interests(current_user['id'])
    interest_names = [i['name'] for i in interests]
    
    return {
        "status": "success",
        "user": {
            "id": current_user['id'],
            "name": current_user['name'],
            "email": current_user['email'],
            "interests": interest_names,
            "country": current_user.get('country'),
            "state": current_user.get('state'),
            "created_at": current_user['created_at'].isoformat() if current_user.get('created_at') else None,
            "last_login": current_user['last_login'].isoformat() if current_user.get('last_login') else None
        }
    }

# ===== NEWS ENDPOINTS (INTEGRATED WITH ML) =====
@app.get("/api/news")
async def get_news(
    country: Optional[str] = None,
    category: Optional[str] = None,
    sortBy: Optional[str] = "publishedAt",
    q: Optional[str] = None,
    page: int = 1,
    pageSize: int = 10,
    nextPage: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    MAIN NEWS ENDPOINT - Integrated with ML recommendations
    Flow: NewsAPI → ML Processing → Personalized Ranking → Frontend
    Supports pagination with nextPage token from NewsData.io
    
    Query Parameters:
    - country: Country code (e.g., 'us', 'gb', 'in')
    - category: News category (e.g., 'business', 'sports', 'entertainment')
    - sortBy: Sort order (default: 'publishedAt')
    - q: Search query
    - nextPage: Pagination token from previous response (for subsequent pages)
    """
    
    print(f"\n🔵 ===== /api/news REQUEST =====")
    print(f"📌 User: {current_user['email']}")
    print(f"📍 Country: {country}")
    print(f"📂 Category: {category}")
    print(f"📄 Page: {page}, NextPageToken: {nextPage[:20] if nextPage else 'None'}...")
    
    if NEWS_API_KEY == "YOUR_API_KEY_HERE":
        return {"status": "error", "message": "API key not configured. Please add your NewsAPI key in .env file"}
    
    # Step 1: Fetch news from NewsAPI with pagination support
    articles, next_page_token = await fetch_news_from_api(country, category, sortBy, q, pageSize, page, nextPage)
    
    if not articles:
        return {
            "status": "success", 
            "totalResults": 0, 
            "articles": [], 
            "page": page, 
            "pageSize": pageSize,
            "nextPage": None
        }
    
    # Step 1.5: Deduplicate articles immediately after fetching
    articles = deduplicate_articles(articles)
    print(f"✅ Deduplicated articles: {len(articles)} unique articles after removing duplicates")
    
    # Create session key to track seen articles across pagination
    session_key = f"user_{current_user['id']}_{country or 'global'}_{category or 'all'}"
    
    # Initialize session cache if needed (reset on first page)
    if page == 1 and not nextPage:
        session_article_cache[session_key] = set()
        print(f"🔄 Starting new news session: {session_key}")
    
    # Ensure session cache exists
    if session_key not in session_article_cache:
        session_article_cache[session_key] = set()
    
    # Deduplicate articles by URL - both within this response AND across pagination
    # Also strictly filter out articles without images
    unique_articles = []
    new_urls_count = 0
    
    for article in articles:
        article_url = article.get('url') or article.get('link')
        image_url = article.get('image_url') or article.get('urlToImage')
        
        # STRICT FILTER: Article must have both a valid URL and a valid Image URL
        if article_url and image_url and image_url.startswith('http'):
            # Check if we've seen this URL before in this session/filter combination
            if article_url not in session_article_cache[session_key]:
                session_article_cache[session_key].add(article_url)
                unique_articles.append(article)
                new_urls_count += 1
    
    print(f"📰 Filtered & Deduplicated: {len(articles)} raw → {new_urls_count} valid with images (dropped {len(articles) - new_urls_count})")
    
    # Step 2: Process articles through ML pipeline
    processed_articles = process_articles_with_ml(unique_articles, current_user['id'])
    
    # Step 3: Return ranked articles with pagination info
    return {
        "status": "success",
        "totalResults": len(processed_articles),
        "articles": processed_articles,
        "ml_enhanced": ML_AVAILABLE and is_ml_ready,
        "country": country or "global",
        "category": category or "all",
        "page": page,
        "pageSize": pageSize,
        "nextPage": next_page_token  # Pass pagination token for infinite scroll
    }

async def fetch_news_from_api(country, category, sortBy, q, pageSize, page=1, nextPage=None):
    try:
        # Create base cache key from parameters
        cache_key = f"{country or 'global'}_{category or 'all'}"
        
        # Include page token in cache key to support pagination
        if nextPage:
            cache_key = f"{cache_key}_page_{nextPage[:20]}"
        
        print(f"📋 Cache Key: {cache_key} (country={country}, category={category}, page={page})")
        
        # Check cache first
        if cache_key in api_cache and cache_key in cache_timestamps:
            cache_age = datetime.utcnow() - cache_timestamps[cache_key]
            if cache_age < timedelta(minutes=CACHE_DURATION_MINUTES):
                print(f"✅ Using cached results for: {cache_key} (age: {int(cache_age.total_seconds())}s)")
                cached_data = api_cache[cache_key]
                # Return tuple of (articles, nextPage token)
                if isinstance(cached_data, tuple):
                    return cached_data
                return cached_data, None
            else:
                print(f"⏰ Cache expired for: {cache_key}")
        
        # NewsData.io /latest endpoint - supports pagination with nextPage token
        # Supports: apikey, country, category, language, page
        # Free tier: 10 articles per page, Paid: 50 articles per page
        
        params = {
            "apikey": NEWS_API_KEY,
            "language": "en"
        }

        # Country filter (NewsData supports country code)
        if country and country != "global":
            params["country"] = country
            print(f"🌍 Adding country filter: {country}")

        # Category filter
        if category:
            params["category"] = category
            print(f"📚 Adding category filter: {category}")

        # Pagination: use nextPage token if provided
        if nextPage:
            params["page"] = nextPage
            print(f"📡 NewsData API Request (/latest) - Next Page: {nextPage[:30]}...")
        else:
            print(f"📡 NewsData API Request (/latest): {params}")

        async with httpx.AsyncClient() as client:
            response = await client.get(
                NEWS_API_BASE_URL,
                params=params,
                timeout=10.0
            )

        data = response.json()

        if data.get("status") == "success":
            articles = data.get("results", [])
            next_page_token = data.get("nextPage")  # Store nextPage token for pagination
            
            # Cache the results with pagination info
            api_cache[cache_key] = (articles, next_page_token)
            cache_timestamps[cache_key] = datetime.utcnow()
            
            print(f"✅ NewsData fetched: {len(articles)} articles from /latest endpoint")
            if next_page_token:
                print(f"📄 Next page available: {next_page_token[:30]}...")
            return articles, next_page_token

        # Handle rate limiting - return cached data if available
        if data.get("results", {}).get("code") == "RateLimitExceeded":
            if cache_key in api_cache:
                print(f"⚠️ Rate limit exceeded - serving cached data for: {cache_key}")
                cached_data = api_cache[cache_key]
                if isinstance(cached_data, tuple):
                    return cached_data
                return cached_data, None
            else:
                print(f"❌ Rate limit exceeded and no cache available")
                return [], None
        
        print("❌ NewsData error:", data)
        return [], None

    except Exception as e:
        print("❌ NewsData exception:", e)
        # Return cached data if available even on exception
        cache_key = f"{country or 'global'}_{category or 'all'}"
        if cache_key in api_cache:
            print(f"⚠️ Exception occurred - serving cached data for: {cache_key}")
            cached_data = api_cache[cache_key]
            if isinstance(cached_data, tuple):
                return cached_data
            return cached_data, None
        return [], None


def process_articles_with_ml(articles: List[Dict], user_id: int) -> List[Dict]:
    """
    Process articles through ML pipeline:
    1. Extract text features
    2. Build TF-IDF vectors
    3. Calculate virality scores
    4. Personalize ranking based on user profile
    
    Normalize field names: NewsData uses 'link' instead of 'url'
    """
    global article_vectorizer, article_cache, is_ml_ready
    
    if not articles:
        return articles
    
    # Normalize article fields for compatibility
    for article in articles:
        # NewsData uses 'link' instead of 'url'
        if 'link' in article and 'url' not in article:
            article['url'] = article['link']
        
        # Ensure all required fields exist
        article.setdefault('url', article.get('link', ''))
        article.setdefault('source', {'name': article.get('source_id', 'Unknown')})
        article.setdefault('urlToImage', article.get('image_url', ''))
        article.setdefault('publishedAt', article.get('pubDate', ''))
    
    if not ML_AVAILABLE:
        # Return articles with basic virality scores
        for article in articles:
            article['virality_score'] = 0.5
            article['ml_processed'] = False
        return articles
    
    # Cache articles - skip articles without URLs
    for article in articles:
        if article.get('url'):
            article_cache[article['url']] = article
    
    # Extract article IDs and texts (only for articles with URLs)
    article_ids = [article['url'] for article in articles if article.get('url')]
    article_texts = [extract_article_text(article) for article in articles if article.get('url')]
    
    if not article_ids:
        # No valid articles to process
        for article in articles:
            article['virality_score'] = 0.5
            article['ml_processed'] = False
        return articles
    
    # Build TF-IDF matrix if not ready
    if not is_ml_ready and len(article_texts) > 0:
        try:
            article_vectorizer.fit_transform(article_ids, article_texts)
            is_ml_ready = True
        except Exception as e:
            print(f"ML initialization error: {e}")
            for article in articles:
                article['virality_score'] = 0.5
                article['ml_processed'] = False
            return articles
    
    # Get user's reading history for personalization
    user_interactions = get_user_interaction_data(user_id)
    
    # Build user profile and get recommendations
    if is_ml_ready and user_interactions:
        try:
            ranked_article_ids = get_ml_recommendations(
                user_id, 
                user_interactions, 
                article_ids
            )
            
            # Reorder articles based on ML ranking
            articles_dict = {a['url']: a for a in articles if a.get('url')}
            ranked_articles = [articles_dict[aid] for aid in ranked_article_ids if aid in articles_dict]
            
            # Add remaining articles
            remaining = [a for a in articles if a.get('url') and a['url'] not in ranked_article_ids]
            articles = ranked_articles + remaining
            
        except Exception as e:
            print(f"ML ranking error: {e}")
    
    # Add virality scores
    for article in articles:
        article['virality_score'] = calculate_virality_score(article)
        article['ml_processed'] = True
    
    return articles

def get_user_interaction_data(user_id: int) -> List[Dict]:
    """Get user's article interactions from database"""
    try:
        # Get reading history - convert to interaction format
        # In production, this would query actual interaction data
        return []
    except Exception as e:
        print(f"Error fetching user interactions: {e}")
        return []

def get_ml_recommendations(user_id: int, user_interactions: List[Dict], available_articles: List[str]) -> List[str]:
    """Get ML-based article recommendations"""
    global article_vectorizer
    
    if not user_interactions or not is_ml_ready:
        return available_articles
    
    try:
        # Build user profile from interactions
        user_vector = build_user_profile(
            interactions=user_interactions,
            tfidf_matrix=article_vectorizer.tfidf_matrix,
            article_id_to_index=article_vectorizer.article_id_to_index
        )
        
        # Get seen article indices
        seen_indices = [
            article_vectorizer.article_id_to_index.get(i["article_id"], -1)
            for i in user_interactions
        ]
        seen_indices = [idx for idx in seen_indices if idx >= 0]
        
        # Get recommendations
        recommended_indices = recommend_articles(
            user_vector=user_vector,
            tfidf_matrix=article_vectorizer.tfidf_matrix,
            seen_indices=seen_indices,
            top_k=len(available_articles)
        )
        
        # Convert indices back to article IDs
        index_to_id = {idx: aid for aid, idx in article_vectorizer.article_id_to_index.items()}
        recommended_ids = [index_to_id.get(idx) for idx in recommended_indices if idx in index_to_id]
        
        return recommended_ids
    except Exception as e:
        print(f"Recommendation error: {e}")
        return available_articles

# ===== ARTICLE INTERACTION TRACKING =====
@app.post("/api/articles/track-interaction")
async def track_interaction(
    interaction: ArticleInteractionRequest,
    current_user: dict = Depends(get_current_user)
):
    """Track when user reads/clicks an article - feeds ML model"""
    
    article_data = {
        "url": interaction.article_url,
        "title": interaction.article_title,
        "category": interaction.category,
        "duration": interaction.duration_seconds
    }
    
    success = ReadingHistoryDB.add_to_history(current_user['id'], article_data)
    
    if success:
        ActivityLogDB.log_activity(
            current_user['id'], 
            "read_article", 
            f"Read: {interaction.article_title}"
        )
    
    return {"status": "success" if success else "error"}

# ===== SAVED ARTICLES =====
@app.post("/api/articles/save")
async def save_article(
    article: SaveArticleRequest,
    current_user: dict = Depends(get_current_user)
):
    """Save an article"""
    article_data = article.dict()
    success = SavedArticlesDB.save_article(current_user['id'], article_data)
    
    if success:
        ActivityLogDB.log_activity(current_user['id'], "save_article", f"Saved: {article.title}")
        return {"status": "success", "message": "Article saved"}
    
    return {"status": "error", "message": "Failed to save article"}

@app.get("/api/articles/saved")
async def get_saved_articles(
    limit: int = 50,
    current_user: dict = Depends(get_current_user)
):
    """Get user's saved articles"""
    articles = SavedArticlesDB.get_saved_articles(current_user['id'], limit)
    return {"status": "success", "articles": articles}

@app.delete("/api/articles/saved/{article_id}")
async def delete_saved_article(
    article_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Delete a saved article"""
    success = SavedArticlesDB.delete_saved_article(current_user['id'], article_id)
    
    if success:
        return {"status": "success", "message": "Article deleted"}
    
    return {"status": "error", "message": "Failed to delete article"}

# ===== STATISTICS =====
@app.get("/api/stats/reading")
async def get_reading_stats(current_user: dict = Depends(get_current_user)):
    """Get user reading statistics"""
    stats = ReadingHistoryDB.get_reading_stats(current_user['id'])
    return {"status": "success", "stats": stats if stats else {}}

@app.get("/api/interests")
async def get_all_interests():
    """Get all available interests"""
    interests = InterestDB.get_all_interests()
    return {"status": "success", "interests": interests}

# ===== ML ADMIN ENDPOINTS =====
@app.post("/api/ml/retrain")
async def retrain_ml_models(current_user: dict = Depends(get_current_user)):
    """Retrain ML models with latest data"""
    global is_ml_ready
    is_ml_ready = False
    
    return {"status": "success", "message": "ML models will retrain on next request"}

@app.get("/api/ml/status")
async def ml_status():
    """Check ML system status"""
    return {
        "status": "success",
        "ml_available": ML_AVAILABLE,
        "ml_ready": is_ml_ready,
        "articles_cached": len(article_cache),
        "vectorizer_ready": article_vectorizer.tfidf_matrix is not None if article_vectorizer else False
    }

@app.get("/")
async def root():
    """API health check"""
    return {
        "status": "success",
        "message": "NewsPulse API with ML Integration",
        "version": "2.0.0",
        "ml_enabled": ML_AVAILABLE,
        "features": ["ML Recommendations", "Virality Prediction", "User Profiling", "Country-specific News"]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)