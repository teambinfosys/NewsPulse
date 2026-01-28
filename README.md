# NewsPulse - News Recommendation System

A full-stack news recommendation platform powered by Machine Learning, featuring personalized content delivery, virality prediction, and intelligent article ranking.

## 🌟 Features

- **User Authentication**: Secure signup/login with JWT tokens
- **Personalized News**: ML-powered recommendations based on user interests
- **Virality Prediction**: AI predicts trending articles
- **TF-IDF Recommender**: Content-based filtering using article similarity
- **Reading History Tracking**: Learns from user behavior
- **Interest-Based Filtering**: Customizable news categories
- **Dark/Light Theme**: User-friendly UI with theme toggle
- **Responsive Design**: Works on all devices

## 🏗️ Architecture

```
newspulse/
├── frontend/          # HTML, CSS, JavaScript
├── backend/           # FastAPI server
├── ml/                # Machine Learning modules
│   ├── preprocessing/ # Text cleaning
│   ├── tfidf_recommender/
│   ├── svd_recommender/
│   ├── virality/      # Virality prediction
│   ├── hybrid/        # Hybrid recommender
│   └── summarization/ # BERT summarization
├── database/          # SQL schema
└── models/            # Trained ML models
```

## 📋 Prerequisites

- **Python 3.8+**
- **MySQL 5.7+** or **MariaDB 10.3+**
- **NewsAPI Key** (free from [newsapi.org](https://newsapi.org/))
- **Modern Web Browser** (Chrome, Firefox, Safari, Edge)

## 🚀 Quick Start

### 1. Clone the Repository

```bash
cd /Users/khaja_21/Documents/Projects/news/newspulse
```

### 2. Install Python Dependencies

```bash
cd backend
pip3 install -r requirements.txt
```

### 3. Setup MySQL Database

```bash
# Login to MySQL
mysql -u root -p

# Create database
CREATE DATABASE newspulse CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# Import schema
USE newspulse;
SOURCE ../database/schema.sql;

# Exit MySQL
EXIT;
```

### 4. Configure Environment Variables

```bash
cd backend
cp .env.example .env
# Edit .env and add your NewsAPI key and database credentials
```

**Required in `.env`:**

- `NEWS_API_KEY`: Get from https://newsapi.org/
- `DB_PASSWORD`: Your MySQL root password
- `SECRET_KEY`: Change to a random string for production

### 5. Start the Backend Server

```bash
cd backend
python3 main.py
```

Server will start at: `http://localhost:8000`

### 6. Open the Frontend

```bash
# Open in browser
open ../frontend/index.html
# Or navigate to: file:///path/to/newspulse/frontend/index.html
```

## 🔧 Configuration

### Environment Variables (`.env`)

| Variable       | Description         | Default              |
| -------------- | ------------------- | -------------------- |
| `NEWS_API_KEY` | NewsAPI.org API key | Required             |
| `DB_HOST`      | MySQL host          | localhost            |
| `DB_PORT`      | MySQL port          | 3306                 |
| `DB_USER`      | MySQL username      | root                 |
| `DB_PASSWORD`  | MySQL password      | (empty)              |
| `DB_NAME`      | Database name       | newspulse            |
| `SECRET_KEY`   | JWT secret key      | Change in production |

## 📊 Database Schema

The system uses 8 tables:

1. **users** - User accounts
2. **interests** - Available categories
3. **user_interests** - User-interest mapping
4. **user_sessions** - Active sessions
5. **user_preferences** - UI preferences
6. **saved_articles** - Bookmarked articles
7. **reading_history** - Article interactions (for ML)
8. **user_activity_log** - Activity tracking

## 🤖 Machine Learning Features

### TF-IDF Recommender

- Analyzes article content using Term Frequency-Inverse Document Frequency
- Builds user preference profiles from reading history
- Recommends similar articles based on cosine similarity

### Virality Prediction

- Predicts article popularity using engagement metrics
- Considers click-through rate, impressions, and freshness
- Highlights trending articles with virality badges

### Hybrid Recommender

- Combines multiple recommendation strategies
- Balances personalization with diversity
- Adapts to user behavior over time

## 🧪 Testing

### Test Database Connection

```bash
cd backend
python3 -c "from database import test_connection; test_connection()"
```

### Test API Endpoints

```bash
# Health check
curl http://localhost:8000/

# ML status
curl http://localhost:8000/api/ml/status
```

### Test Complete Flow

1. Open frontend in browser
2. Click "Get Started"
3. Create account with test credentials
4. Login and verify news loads
5. Test filters and interactions

## 🐛 Troubleshooting

### Backend won't start

- **Check Python version**: `python3 --version` (need 3.8+)
- **Install dependencies**: `pip3 install -r requirements.txt`
- **Check MySQL**: Ensure MySQL is running
- **Verify .env**: Check all variables are set

### No news articles showing

- **Check NewsAPI key**: Verify it's valid in `.env`
- **Check API quota**: Free tier has 100 requests/day
- **Check console**: Open browser DevTools for errors
- **Check CORS**: Backend must be running on port 8000

### Database errors

- **Check credentials**: Verify DB_USER and DB_PASSWORD in `.env`
- **Check database exists**: `mysql -u root -p -e "SHOW DATABASES;"`
- **Re-run schema**: `mysql -u root -p newspulse < database/schema.sql`

### ML features not working

- **Check dependencies**: Ensure scikit-learn, numpy installed
- **Check logs**: Backend console shows ML availability
- **Fallback mode**: System works without ML models

## 📦 Dependencies

### Backend (Python)

- FastAPI - Web framework
- Uvicorn - ASGI server
- PyMySQL - MySQL connector
- Scikit-learn - ML library
- NLTK - Text processing
- Transformers - BERT models
- XGBoost - Gradient boosting

### Frontend

- Vanilla JavaScript (no framework)
- Font Awesome - Icons
- Modern CSS with CSS Variables

## 🔐 Security Notes

- **Change SECRET_KEY** in production
- **Use HTTPS** in production
- **Secure database** credentials
- **Rate limit** API endpoints
- **Validate** all user inputs

## 📝 API Documentation

Once the server is running, visit:

- API Docs: `http://localhost:8000/docs`
- Alternative Docs: `http://localhost:8000/redoc`

## 🤝 Contributing

This is a complete project. To extend:

1. Add new ML models in `ml/` directory
2. Create new API endpoints in `backend/main.py`
3. Enhance UI in `frontend/` files
4. Add new database tables in `schema.sql`

## 📄 License

This project is for educational purposes.

## 🙋 Support

For issues:

1. Check troubleshooting section
2. Verify all prerequisites installed
3. Check backend console logs
4. Check browser console (F12)

## 🎯 Next Steps

After setup:

1. Get your NewsAPI key from https://newsapi.org/
2. Customize interests in database
3. Train custom ML models
4. Deploy to production server
5. Add more news sources

---

**Built with ❤️ using FastAPI, MySQL, and Machine Learning**
