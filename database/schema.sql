-- NewsPulse Database Schema
-- MySQL Database for News Recommendation System

-- Create database
CREATE DATABASE IF NOT EXISTS newspulse
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE newspulse;

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL,
    is_active BOOLEAN DEFAULT TRUE,
    INDEX idx_email (email),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Interests/Categories table
CREATE TABLE IF NOT EXISTS interests (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insert default interests
INSERT IGNORE INTO interests (name, display_name, description) VALUES
('technology', 'Technology', 'Tech news, gadgets, software, and innovation'),
('business', 'Business', 'Business news, markets, economy, and finance'),
('sports', 'Sports', 'Sports news, scores, and athlete updates'),
('health', 'Health', 'Health, wellness, medical news, and fitness'),
('entertainment', 'Entertainment', 'Movies, music, celebrities, and pop culture'),
('science', 'Science', 'Scientific discoveries, research, and innovation');

-- User interests junction table
CREATE TABLE IF NOT EXISTS user_interests (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    interest_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (interest_id) REFERENCES interests(id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_interest (user_id, interest_id),
    INDEX idx_user_id (user_id),
    INDEX idx_interest_id (interest_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- User sessions table
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
    INDEX idx_expires_at (expires_at),
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- User preferences table
CREATE TABLE IF NOT EXISTS user_preferences (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT UNIQUE NOT NULL,
    theme VARCHAR(20) DEFAULT 'light',
    notifications_enabled BOOLEAN DEFAULT TRUE,
    email_digest BOOLEAN DEFAULT FALSE,
    digest_frequency VARCHAR(20) DEFAULT 'daily',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Saved articles table
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
    INDEX idx_user_id (user_id),
    INDEX idx_saved_at (saved_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Reading history table
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
    INDEX idx_category (category),
    INDEX idx_read_at (read_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- User activity log table
CREATE TABLE IF NOT EXISTS user_activity_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    activity_type VARCHAR(50) NOT NULL,
    activity_description TEXT,
    ip_address VARCHAR(45),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_activity_type (activity_type),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create useful views

-- View: User profiles with interests
CREATE OR REPLACE VIEW view_user_profiles AS
SELECT 
    u.id,
    u.name,
    u.email,
    u.created_at,
    u.last_login,
    GROUP_CONCAT(i.name) as interests,
    COUNT(DISTINCT rh.id) as articles_read,
    COUNT(DISTINCT sa.id) as articles_saved
FROM users u
LEFT JOIN user_interests ui ON u.id = ui.user_id
LEFT JOIN interests i ON ui.interest_id = i.id
LEFT JOIN reading_history rh ON u.id = rh.user_id
LEFT JOIN saved_articles sa ON u.id = sa.user_id
WHERE u.is_active = TRUE
GROUP BY u.id, u.name, u.email, u.created_at, u.last_login;

-- View: User reading statistics
CREATE OR REPLACE VIEW view_user_reading_stats AS
SELECT 
    user_id,
    COUNT(*) as total_articles_read,
    SUM(read_duration_seconds) as total_read_time_seconds,
    AVG(read_duration_seconds) as avg_read_time_seconds,
    COUNT(DISTINCT category) as categories_explored,
    MAX(read_at) as last_read_at
FROM reading_history
GROUP BY user_id;

-- View: Popular articles (most read)
CREATE OR REPLACE VIEW view_popular_articles AS
SELECT 
    article_title,
    article_url,
    category,
    COUNT(*) as read_count,
    AVG(read_duration_seconds) as avg_duration,
    MAX(read_at) as last_read
FROM reading_history
GROUP BY article_title, article_url, category
ORDER BY read_count DESC
LIMIT 100;

-- Stored Procedures

DELIMITER //

-- Procedure: Register new user
CREATE PROCEDURE IF NOT EXISTS sp_register_user(
    IN p_name VARCHAR(255),
    IN p_email VARCHAR(255),
    IN p_password VARCHAR(255),
    OUT p_user_id INT
)
BEGIN
    INSERT INTO users (name, email, password)
    VALUES (p_name, p_email, p_password);
    
    SET p_user_id = LAST_INSERT_ID();
END //

-- Procedure: Add user interests
CREATE PROCEDURE IF NOT EXISTS sp_add_user_interests(
    IN p_user_id INT,
    IN p_interests VARCHAR(500)
)
BEGIN
    DECLARE interest_name VARCHAR(100);
    DECLARE interest_id INT;
    DECLARE pos INT;
    DECLARE interests_list VARCHAR(500);
    
    SET interests_list = CONCAT(p_interests, ',');
    
    WHILE LENGTH(interests_list) > 0 DO
        SET pos = LOCATE(',', interests_list);
        SET interest_name = TRIM(SUBSTRING(interests_list, 1, pos - 1));
        SET interests_list = SUBSTRING(interests_list, pos + 1);
        
        IF LENGTH(interest_name) > 0 THEN
            SELECT id INTO interest_id FROM interests WHERE name = interest_name LIMIT 1;
            
            IF interest_id IS NOT NULL THEN
                INSERT IGNORE INTO user_interests (user_id, interest_id)
                VALUES (p_user_id, interest_id);
            END IF;
        END IF;
        
        SET interest_id = NULL;
    END WHILE;
END //

-- Procedure: Get user interests
CREATE PROCEDURE IF NOT EXISTS sp_get_user_interests(
    IN p_user_id INT
)
BEGIN
    SELECT i.*
    FROM interests i
    JOIN user_interests ui ON i.id = ui.interest_id
    WHERE ui.user_id = p_user_id AND i.is_active = TRUE;
END //

-- Procedure: Update last login
CREATE PROCEDURE IF NOT EXISTS sp_update_last_login(
    IN p_user_id INT
)
BEGIN
    UPDATE users 
    SET last_login = CURRENT_TIMESTAMP 
    WHERE id = p_user_id;
END //

-- Procedure: Clean expired sessions
CREATE PROCEDURE IF NOT EXISTS sp_clean_expired_sessions()
BEGIN
    UPDATE user_sessions
    SET is_active = FALSE
    WHERE expires_at < CURRENT_TIMESTAMP AND is_active = TRUE;
END //

DELIMITER ;

-- Create event to auto-clean expired sessions (runs daily)
CREATE EVENT IF NOT EXISTS event_clean_expired_sessions
ON SCHEDULE EVERY 1 DAY
STARTS CURRENT_TIMESTAMP
DO CALL sp_clean_expired_sessions();

-- Sample data for testing (optional)
-- Uncomment to insert test users

/*
INSERT INTO users (name, email, password) VALUES
('John Doe', 'john@example.com', '$2b$12$example_hash_1'),
('Jane Smith', 'jane@example.com', '$2b$12$example_hash_2');

INSERT INTO user_interests (user_id, interest_id) VALUES
(1, 1), (1, 2), (1, 4),  -- John likes tech, business, health
(2, 3), (2, 5), (2, 6);  -- Jane likes sports, entertainment, science
*/

-- Show created tables
SHOW TABLES;

SELECT '✅ Database schema created successfully!' as Status;