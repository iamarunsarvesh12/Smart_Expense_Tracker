# Smart Home Expense Tracker 🎙️📊

A modern, production-grade household expense tracking application built with **Flask**, **Pandas**, **Tailwind CSS**, and browser-native **Web Speech API** for AI-powered Tanglish and English voice expense recording.

---

## 🌟 Key Features

1. **🎙️ AI Voice Assistant & Tanglish NLP Parser**:
   - Browser-native speech recognition (`en-IN` / `ta-IN`) for seamless conversational expense entry.
   - Smart entity extraction for amounts, dates (today, yesterday/nethu), payment modes (UPI, Cash, Card), and category matching.
   - **Safety Confirmation Flow**: Speech is transcribed and presented in an editable confirmation modal with Web Audio API chime sounds before saving.

2. **📅 Interactive Monthly Calendar**:
   - Monthly grid with visual status dots and badges showing daily spending totals.
   - Quick date inspection panel showing individual items, payment modes, category icons, timestamps, and notes.

3. **📊 Real-Time Spending Analytics**:
   - **Chart.js** Donut Chart for 5-category monthly spending breakdown.
   - Daily spending trend bar chart to easily spot high-expenditure days.

4. **🗂️ 5 Defined Category Buckets**:
   - Food & Groceries
   - Fuel & Commute
   - Stationery & Office
   - Medical & Healthcare
   - General & Daily Utilities

5. **💾 Robust Data Storage & Pruning**:
   - Structured CSV persistence in `data/expenses.csv`.
   - Thread-safe file operations with concurrent access locks.
   - Automatic 90-day rolling history with archival to `data/expenses_archive.csv`.

6. **📥 Export & Offline Backup**:
   - One-click export to **CSV** and styled **Excel (.xlsx)** via OpenPyXL.

7. **🚀 Production Deployment Ready**:
   - Pre-configured `Procfile` for **Gunicorn** and cloud deployment on **Render**.

---

## 🏗️ Project Architecture

```text
Smart_Expense_Tracker/
├── app.py                 # Flask REST application & routing
├── storage.py             # CSV engine, Pandas analytics & 3-month archival
├── voice_parser.py        # Voice NLP parser & entity extraction
├── requirements.txt       # Pinned production dependencies
├── Procfile               # WSGI runner for Render (Gunicorn)
├── .env.example           # Environment configuration template
├── .gitignore             # Git ignore rules for venv, secrets, logs
├── data/
│   ├── expenses.csv       # Active rolling 3-month records
│   └── expenses_archive.csv # Historical archived records
├── static/
│   ├── css/
│   │   └── style.css      # Custom animations, wave bars & calendar styles
│   └── js/
│       └── app.js         # Web Speech API, Chart.js & dynamic UI logic
└── templates/
    └── index.html         # Tailwind CSS + FontAwesome frontend dashboard
```

---

## 🚀 Getting Started Locally

### 1. Clone the Repository
```bash
git clone https://github.com/iamarunsarvesh12/Smart_Expense_Tracker.git
cd Smart_Expense_Tracker
```

### 2. Create and Activate Virtual Environment
```bash
# Windows
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Environment
```bash
cp .env.example .env
```

### 5. Run Development Server
```bash
python app.py
```
Open **`http://127.0.0.1:5000`** in your browser.

---

## 🧪 Running Automated Tests

Run the included automated test suites:

```bash
# Phase 2 Storage & REST API tests
python test_phase2.py

# Phase 3 Frontend verification
python test_phase3.py

# Phase 4 AI Voice Assistant NLP tests
python test_phase4.py
```

---

## ☁️ Deploying to Render

1. Create a new **Web Service** on [Render](https://render.com/).
2. Connect your GitHub repository `iamarunsarvesh12/Smart_Expense_Tracker`.
3. Configure the service settings:
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
4. Set Environment Variables in Render:
   - `SECRET_KEY`: `[generate a secure random string]`
   - `FLASK_DEBUG`: `False`
5. Click **Deploy Web Service**!

---

## 📜 License
MIT License. Built for smart household expense management.
