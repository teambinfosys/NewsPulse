# 📰 NewsPulse – AI-Powered News Recommendation System

A full-stack news recommendation platform powered by **Machine Learning**, **FastAPI**, and **cloud-based infrastructure**, delivering personalized, real-time news with intelligent ranking and filtering.

---

## 🌟 Features

* **User Authentication** – Secure login & signup using JWT
* **Personalized News Feed** – ML-powered recommendations
* **Virality Prediction** – Detects trending articles
* **TF-IDF Recommender** – Content-based filtering
* **Multi-Country News Support** – Powered by **NewsData.io API**
* **Reading History Tracking**
* **Interest-Based Filtering**
* **Dark / Light Mode UI**
* **Responsive Design**
* **Cloud Database (Amazon RDS)**

---

## 🏗️ Architecture

```
newspulse/
├── frontend/           # HTML, CSS, JavaScript
├── backend/            # FastAPI server
├── ml/                 # Machine Learning modules
│   ├── preprocessing/
│   ├── tfidf_recommender/
│   ├── svd_recommender/
│   ├── virality/
│   ├── hybrid/
│   └── summarization/
├── database/           # SQL schema
└── models/             # Trained ML models
```

---

## 📋 Prerequisites

* **Python 3.8+**
* **Amazon RDS (MySQL)**
* **NewsData.io API Key**
* **Modern Web Browser**

---

## 🚀 Quick Start

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/your-org/newspulse.git

cd newspulse
```

---

### 2️⃣ Install Dependencies

```bash
cd backend

pip install -r requirements.txt
```

---

### 3️⃣ Setup Amazon RDS Database

Create an **Amazon RDS instance**:

* Engine: MySQL / PostgreSQL
* Public access: Yes (for development)
* Port: 3306 (MySQL) or 5432 (Postgres)

Then import schema:

```sql
CREATE DATABASE newspulse;
USE newspulse;
SOURCE database/schema.sql;
```

---

### 4️⃣ Configure Environment Variables

```bash
cd backend

cp .env.example .env
```

### Required `.env` values:

```env
NEWS_API_KEY=your_newsdata_api_key
DB_HOST=your-rds-endpoint.amazonaws.com
DB_PORT=3306
DB_USER=admin
DB_PASSWORD=your_password
DB_NAME=newspulse
SECRET_KEY=your_secure_secret
```

🔹 **Get API Key:** [https://newsdata.io/](https://newsdata.io/)

---

### 5️⃣ Start Backend Server

```bash
python main.py
```

Backend will run at:

```
http://localhost:8000
```

---

### 6️⃣ Run Frontend

```bash
open frontend/index.html
```

---

## 🗄️ Database (Amazon RDS)

### Tables Used

1. **users**
2. **interests**
3. **user_interests**
4. **user_sessions**
5. **reading_history**
6. **user_activity_log**

✔ Scalable
✔ Cloud-hosted
✔ Secure
✔ Production-ready

---

## 🤖 Machine Learning Modules

### 🔹 TF-IDF Recommendation

* Article similarity-based recommendations
* Personalized news feed

### 🔹 Virality Prediction

* Predicts trending news
* Uses engagement & freshness

### 🔹 Hybrid Model

* Combines content + behavior
* Improves recommendation accuracy

---

## 🐛 Troubleshooting

### ❌ No News Showing

* Check **NewsData.io API key**
* Verify API quota
* Ensure correct country code

### ❌ Database Error

* Verify RDS security group allows inbound traffic
* Check DB credentials
* Confirm schema imported

### ❌ ML Not Working

* Install all dependencies
* Check backend logs
* Restart server

---

## Tech Stack

### Backend

* FastAPI
* Python
* JWT Authentication
* SQLAlchemy
* Scikit-learn
* NLTK
* Transformers

### Frontend

* HTML
* CSS
* JavaScript

### Cloud

* **Amazon RDS**
* **NewsData.io API**

---

## 🔐 Security Best Practices

* Use `.env` for secrets
* Never commit API keys
* Enable HTTPS in production
* Restrict RDS access
* Use strong JWT secret

---

## 📄 License

This project is intended for **educational and academic use**.

---
## Contributing

Contributions are welcome! Feel free to submit issues and pull requests.

## 👥 Team
- **Member 1**: [Shaik Khaja](https://github.com/khaja-shaik-21)
- **Member 2**: [Muskan Yadav](https://github.com/muskanyadav28)
- **Member 3**: [Priya Tiwari](https://github.com/2110priyatiwari)
- **Member 4**: [Murali Krishna](https://github.com/your-github-profile)

---

⭐ Star this repo if you find it helpful!