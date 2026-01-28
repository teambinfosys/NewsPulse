"""
Setup script for Oracle Cloud MySQL Database
Initializes tables and data for NewsPulse
"""

import pymysql
from pymysql.cursors import DictCursor
import os
from dotenv import load_dotenv

load_dotenv()

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'port': int(os.getenv('DB_PORT', 3306)),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'charset': 'utf8mb4',
    'cursorclass': DictCursor,
    'connect_timeout': 10
}

def test_connection():
    """Test Oracle Cloud MySQL connection"""
    try:
        print("🔍 Testing AWS RDS MySQL connection...")
        print(f"   Host: {DB_CONFIG['host']}")
        print(f"   Port: {DB_CONFIG['port']}")
        print(f"   User: {DB_CONFIG['user']}")
        
        connection = pymysql.connect(**DB_CONFIG)
        with connection.cursor() as cursor:
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()
            print(f"✅ Connected to MySQL {version['VERSION()']}")
        connection.close()
        return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

def create_database():
    """Create newspulse database if not exists"""
    try:
        print("\n📦 Creating database...")
        connection = pymysql.connect(**DB_CONFIG)
        with connection.cursor() as cursor:
            cursor.execute("CREATE DATABASE IF NOT EXISTS newspulse CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            cursor.execute("USE newspulse")
            print("✅ Database 'newspulse' ready")
        connection.commit()
        connection.close()
        
        # Update config to use the database
        DB_CONFIG['database'] = 'newspulse'
        return True
    except Exception as e:
        print(f"❌ Database creation failed: {e}")
        return False

def create_tables():
    """Create all required tables"""
    try:
        print("\n📋 Creating tables...")
        connection = pymysql.connect(**DB_CONFIG)
        
        with connection.cursor() as cursor:
            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    country VARCHAR(100),
                    state VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    INDEX idx_email (email)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            print("   ✓ users")
            
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
            print("   ✓ interests")
            
            # User interests
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
            print("   ✓ user_interests")
            
            # Sessions
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
                    INDEX idx_user_id (user_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            print("   ✓ user_sessions")
            
            # Preferences
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_preferences (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT UNIQUE NOT NULL,
                    theme VARCHAR(20) DEFAULT 'light',
                    notifications_enabled BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            print("   ✓ user_preferences")
            
            # Saved articles
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
            print("   ✓ saved_articles")
            
            # Reading history
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
                    INDEX idx_user_id (user_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            print("   ✓ reading_history")
            
            # Activity log
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_activity_log (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    activity_type VARCHAR(50) NOT NULL,
                    activity_description TEXT,
                    ip_address VARCHAR(45),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    INDEX idx_user_id (user_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            print("   ✓ user_activity_log")
        
        connection.commit()
        connection.close()
        print("✅ All tables created successfully")
        return True
    except Exception as e:
        print(f"❌ Table creation failed: {e}")
        return False

def insert_default_data():
    """Insert default interests"""
    try:
        print("\n📝 Inserting default data...")
        connection = pymysql.connect(**DB_CONFIG)
        
        with connection.cursor() as cursor:
            # Check if interests already exist
            cursor.execute("SELECT COUNT(*) as count FROM interests")
            count = cursor.fetchone()['count']
            
            if count == 0:
                interests = [
                    ('technology', 'Technology'),
                    ('business', 'Business'),
                    ('sports', 'Sports'),
                    ('health', 'Health'),
                    ('entertainment', 'Entertainment'),
                    ('science', 'Science')
                ]
                
                cursor.executemany(
                    "INSERT INTO interests (name, display_name) VALUES (%s, %s)",
                    interests
                )
                print(f"   ✓ Inserted {len(interests)} default interests")
            else:
                print(f"   ℹ️  Interests already exist ({count} found)")
        
        connection.commit()
        connection.close()
        print("✅ Default data ready")
        return True
    except Exception as e:
        print(f"❌ Data insertion failed: {e}")
        return False

def main():
    """Main setup process"""
    print("="*60)
    print("NewsPulse - AWS Cloud MySQL Setup")
    print("="*60)
    
    # Step 1: Test connection
    if not test_connection():
        print("\n❌ Setup failed. Please check your database credentials in .env file")
        return False
    
    # Step 2: Create database
    if not create_database():
        print("\n❌ Setup failed at database creation")
        return False
    
    # Step 3: Create tables
    if not create_tables():
        print("\n❌ Setup failed at table creation")
        return False
    
    # Step 4: Insert default data
    if not insert_default_data():
        print("\n❌ Setup failed at data insertion")
        return False
    
    print("\n" + "="*60)
    print("✅ Setup completed successfully!")
    print("="*60)
    print("\n📋 Summary:")
    print("   • Database: newspulse")
    print("   • Tables: 8 tables created")
    print("   • Default interests: 6 categories")
    print("\n🚀 You can now start the backend server:")
    print("   cd backend")
    print("   uvicorn main:app --reload --port 8000")
    print("="*60)
    
    return True

if __name__ == "__main__":
    main()