"""
MySQL Database Connection and Helper Functions
Handles all database operations for NewsPulse
"""

import pymysql
from pymysql.cursors import DictCursor
from contextlib import contextmanager
import os
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

# ===== DATABASE CONFIGURATION =====
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 3306)),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'newspulse'),
    'charset': 'utf8mb4',
    'cursorclass': DictCursor,
    'connect_timeout': 10,
    'read_timeout': 30,
    'write_timeout': 30
}

# AWS RDS does NOT require SSL for Free Tier
# Keep it simple and stable

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT", 3306)),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
    "cursorclass": DictCursor,
    "connect_timeout": 10,
    "read_timeout": 30,
    "write_timeout": 30,
    "charset": "utf8mb4"
}


# ===== CONNECTION POOL =====
@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    connection = None
    try:
        connection = pymysql.connect(**DB_CONFIG)
        yield connection
        connection.commit()
    except Exception as e:
        if connection:
            connection.rollback()
        raise e
    finally:
        if connection:
            connection.close()

# ===== AUTO-CREATE TABLES =====
def initialize_database():
    """Create database tables if they don't exist"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # Users table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        name VARCHAR(255) NOT NULL,
                        email VARCHAR(255) UNIQUE NOT NULL,
                        password VARCHAR(255) NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_login TIMESTAMP NULL,
                        is_active BOOLEAN DEFAULT TRUE,
                        INDEX idx_email (email)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """)
                
                # Interests table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS interests (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        name VARCHAR(100) UNIQUE NOT NULL,
                        display_name VARCHAR(100) NOT NULL,
                        is_active BOOLEAN DEFAULT TRUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """)
                
                # Insert default interests if table is empty
                cursor.execute("SELECT COUNT(*) as count FROM interests")
                if cursor.fetchone()['count'] == 0:
                    default_interests = [
                        ('technology', 'Technology'),
                        ('business', 'Business'),
                        ('sports', 'Sports'),
                        ('health', 'Health'),
                        ('entertainment', 'Entertainment'),
                        ('science', 'Science')
                    ]
                    cursor.executemany(
                        "INSERT INTO interests (name, display_name) VALUES (%s, %s)",
                        default_interests
                    )
                
                # User interests junction table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS user_interests (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        user_id INT NOT NULL,
                        interest_id INT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                        FOREIGN KEY (interest_id) REFERENCES interests(id) ON DELETE CASCADE,
                        UNIQUE KEY unique_user_interest (user_id, interest_id)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """)
                
                # Sessions table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS user_sessions (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        user_id INT NOT NULL,
                        token TEXT NOT NULL,
                        expires_at TIMESTAMP NOT NULL,
                        ip_address VARCHAR(45),
                        user_agent TEXT,
                        is_active BOOLEAN DEFAULT TRUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                        INDEX idx_user_id (user_id),
                        INDEX idx_expires_at (expires_at)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """)
                
                # User preferences table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS user_preferences (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        user_id INT UNIQUE NOT NULL,
                        theme VARCHAR(20) DEFAULT 'light',
                        notifications_enabled BOOLEAN DEFAULT TRUE,
                        email_digest BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """)
                
                # Saved articles table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS saved_articles (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        user_id INT NOT NULL,
                        article_url TEXT NOT NULL,
                        article_title TEXT NOT NULL,
                        article_description TEXT,
                        article_image_url TEXT,
                        source_name VARCHAR(255),
                        published_at VARCHAR(50),
                        notes TEXT,
                        saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                        INDEX idx_user_id (user_id)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """)
                
                # Reading history table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS reading_history (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        user_id INT NOT NULL,
                        article_url TEXT NOT NULL,
                        article_title TEXT NOT NULL,
                        category VARCHAR(100),
                        read_duration_seconds INT DEFAULT 0,
                        read_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                        INDEX idx_user_id (user_id),
                        INDEX idx_category (category)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """)
                
                # Activity log table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS user_activity_log (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        user_id INT NOT NULL,
                        activity_type VARCHAR(50) NOT NULL,
                        activity_description TEXT,
                        ip_address VARCHAR(45),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                        INDEX idx_user_id (user_id),
                        INDEX idx_activity_type (activity_type)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """)
                
        print("✅ Database tables initialized successfully!")
        return True
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False

# ===== USER OPERATIONS =====
class UserDB:
    """User database operations"""
    
    @staticmethod
    def create_user(name: str, email: str, password_hash: str, 
                   country: str = None, state: str = None) -> Optional[int]:
        """Create new user and return user_id"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    sql = "INSERT INTO users (name, email, password, country, state) VALUES (%s, %s, %s, %s, %s)"
                    cursor.execute(sql, (name, email, password_hash, country, state))
                    return cursor.lastrowid
        except pymysql.IntegrityError:
            return None
        except Exception as e:
            print(f"Error creating user: {e}")
            return None
    
    @staticmethod
    def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                sql = "SELECT * FROM users WHERE email = %s AND is_active = TRUE"
                cursor.execute(sql, (email,))
                return cursor.fetchone()
    
    @staticmethod
    def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                sql = "SELECT * FROM users WHERE id = %s AND is_active = TRUE"
                cursor.execute(sql, (user_id,))
                return cursor.fetchone()
    
    @staticmethod
    def update_last_login(user_id: int) -> bool:
        """Update user's last login timestamp"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    sql = "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = %s"
                    cursor.execute(sql, (user_id,))
                    return True
        except Exception as e:
            print(f"Error updating last login: {e}")
            return False

# ===== INTEREST OPERATIONS =====
class InterestDB:
    """Interest database operations"""
    
    @staticmethod
    def add_user_interests(user_id: int, interests: List[str]) -> bool:
        """Add interests for a user"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    for interest_name in interests:
                        # Get interest ID
                        cursor.execute("SELECT id FROM interests WHERE name = %s", (interest_name,))
                        result = cursor.fetchone()
                        
                        if result:
                            interest_id = result['id']
                            # Insert user interest (ignore if already exists)
                            sql = """
                                INSERT IGNORE INTO user_interests (user_id, interest_id) 
                                VALUES (%s, %s)
                            """
                            cursor.execute(sql, (user_id, interest_id))
                    return True
        except Exception as e:
            print(f"Error adding interests: {e}")
            return False
    
    @staticmethod
    def get_user_interests(user_id: int) -> List[Dict[str, Any]]:
        """Get all interests for a user"""
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                sql = """
                    SELECT i.* FROM interests i
                    JOIN user_interests ui ON i.id = ui.interest_id
                    WHERE ui.user_id = %s AND i.is_active = TRUE
                """
                cursor.execute(sql, (user_id,))
                return cursor.fetchall()
    
    @staticmethod
    def get_all_interests() -> List[Dict[str, Any]]:
        """Get all available interests"""
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                sql = "SELECT * FROM interests WHERE is_active = TRUE ORDER BY display_name"
                cursor.execute(sql)
                return cursor.fetchall()

# ===== SESSION OPERATIONS =====
class SessionDB:
    """Session database operations"""
    
    @staticmethod
    def create_session(user_id: int, token: str, expires_at: str, 
                      ip_address: str = None, user_agent: str = None) -> bool:
        """Create new session"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    sql = """
                        INSERT INTO user_sessions 
                        (user_id, token, expires_at, ip_address, user_agent)
                        VALUES (%s, %s, %s, %s, %s)
                    """
                    cursor.execute(sql, (user_id, token, expires_at, ip_address, user_agent))
                    return True
        except Exception as e:
            print(f"Error creating session: {e}")
            return False
    
    @staticmethod
    def invalidate_session(token: str) -> bool:
        """Invalidate a session"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    sql = "UPDATE user_sessions SET is_active = FALSE WHERE token = %s"
                    cursor.execute(sql, (token,))
                    return True
        except Exception as e:
            print(f"Error invalidating session: {e}")
            return False

# ===== PREFERENCES OPERATIONS =====
class PreferencesDB:
    """User preferences operations"""
    
    @staticmethod
    def get_preferences(user_id: int) -> Optional[Dict[str, Any]]:
        """Get user preferences"""
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                sql = "SELECT * FROM user_preferences WHERE user_id = %s"
                cursor.execute(sql, (user_id,))
                return cursor.fetchone()

# ===== SAVED ARTICLES OPERATIONS =====
class SavedArticlesDB:
    """Saved articles operations"""
    
    @staticmethod
    def save_article(user_id: int, article_data: Dict[str, Any]) -> bool:
        """Save an article"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    sql = """
                        INSERT INTO saved_articles 
                        (user_id, article_url, article_title, article_description, 
                         article_image_url, source_name, published_at, notes)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    cursor.execute(sql, (
                        user_id,
                        article_data.get('url'),
                        article_data.get('title'),
                        article_data.get('description'),
                        article_data.get('image_url'),
                        article_data.get('source'),
                        article_data.get('published_at'),
                        article_data.get('notes')
                    ))
                    return True
        except Exception as e:
            print(f"Error saving article: {e}")
            return False
    
    @staticmethod
    def get_saved_articles(user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """Get user's saved articles"""
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                sql = """
                    SELECT * FROM saved_articles 
                    WHERE user_id = %s 
                    ORDER BY saved_at DESC 
                    LIMIT %s
                """
                cursor.execute(sql, (user_id, limit))
                return cursor.fetchall()
    
    @staticmethod
    def delete_saved_article(user_id: int, article_id: int) -> bool:
        """Delete a saved article"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    sql = "DELETE FROM saved_articles WHERE id = %s AND user_id = %s"
                    cursor.execute(sql, (article_id, user_id))
                    return True
        except Exception as e:
            print(f"Error deleting article: {e}")
            return False

# ===== READING HISTORY OPERATIONS =====
class ReadingHistoryDB:
    """Reading history operations"""
    
    @staticmethod
    def add_to_history(user_id: int, article_data: Dict[str, Any]) -> bool:
        """Add article to reading history"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    sql = """
                        INSERT INTO reading_history 
                        (user_id, article_url, article_title, category, read_duration_seconds)
                        VALUES (%s, %s, %s, %s, %s)
                    """
                    cursor.execute(sql, (
                        user_id,
                        article_data.get('url'),
                        article_data.get('title'),
                        article_data.get('category'),
                        article_data.get('duration', 0)
                    ))
                    return True
        except Exception as e:
            print(f"Error adding to history: {e}")
            return False
    
    @staticmethod
    def get_reading_stats(user_id: int) -> Optional[Dict[str, Any]]:
        """Get user reading statistics"""
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                sql = """
                    SELECT 
                        COUNT(*) as total_articles_read,
                        SUM(read_duration_seconds) as total_read_time,
                        category,
                        COUNT(*) as category_count
                    FROM reading_history 
                    WHERE user_id = %s
                    GROUP BY category
                    ORDER BY category_count DESC
                """
                cursor.execute(sql, (user_id,))
                return cursor.fetchone()

# ===== ACTIVITY LOG OPERATIONS =====
class ActivityLogDB:
    """Activity log operations"""
    
    @staticmethod
    def log_activity(user_id: int, activity_type: str, 
                    description: str = None, ip_address: str = None) -> bool:
        """Log user activity"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    sql = """
                        INSERT INTO user_activity_log 
                        (user_id, activity_type, activity_description, ip_address)
                        VALUES (%s, %s, %s, %s)
                    """
                    cursor.execute(sql, (user_id, activity_type, description, ip_address))
                    return True
        except Exception as e:
            print(f"Error logging activity: {e}")
            return False

# ===== TEST CONNECTION =====
def test_connection():
    """Test database connection"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                print("✅ Database connection successful!")
                return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing database connection...")
    if test_connection():
        print("\nInitializing database tables...")
        initialize_database()