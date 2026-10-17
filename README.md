# Smart Home Expense Tracker 🎙️📊💰

A modern, production-grade household expense & monthly budget tracking application built with **Flask**, Python's native standard library (**csv**, **json**, **datetime**, **collections**), **Tailwind CSS**, and browser-native **Web Speech API** for AI-powered Tanglish and English voice expense recording. Fully compatible with Python 3.14+ with zero heavy C-dependencies (strictly **no Pandas** and **no OpenPyXL**).

---

## 🌟 Key Features

1. **💰 Monthly Income & Category Budgeting Engine**:
   - **Monthly Budget Settings Modal**: Configure monthly household income (e.g., ₹25,000) and allocate custom spending limits across all 7 categories.
   - **Category Progress Bars**: Real-time visualization of Allocated Budget, Amount Spent, and Remaining Balance. Progress meters dynamically shift color (<75% Emerald, 75–90% Amber, >90% Rose/Over-budget).
   - **Net Monthly Savings Tracker**: Prominently displays `Total Income - Total Spent This Month = Net Savings` alongside a percentage savings rate meter.
   - **Recommended Daily Burn Rate**: Compares daily spending trends against the month's recommended daily burn rate (`Income / days_in_month`).
   - Lightweight JSON configuration persisted to `data/budget_config.json`.

2. **🗂️ 7 Granular Category Architecture**:
   - **Food**: Restaurants, Tea, Snacks, Swiggy / Zomato, Outside food.
   - **Groceries**: Provisions, Vegetables, Milk / Paal, Supermarket items.
   - **Bike & Car**: Petrol, Diesel, Vehicle Service, Mechanics, Punctures, Toll.
   - **Bills & Utilities**: EB / Electricity bill, Wi-Fi / Broadband, Mobile Recharge, Gas cylinder.
   - **Stationery & Office**: Printouts, Xerox, Books, Pens, Courier, Office supplies.
   - **Medical & Healthcare**: Medicines, Doctor consultation, Medical tests, Tablets.
   - **General & Others**: Money given to others, Lending, Casual cash spends, Miscellaneous.

3. **🎙️ AI Voice Assistant & Tanglish NLP Parser**:
   - Browser-native speech recognition (`en-IN` / `ta-IN`) for seamless conversational expense entry.
   - Smart entity extraction for amounts, dates (today, yesterday / nethu), payment modes (UPI, Cash, Card), and category matching.
   - **Safety Confirmation Flow**: Speech is transcribed and presented in an editable confirmation modal with Web Audio API chime sounds before saving.

4. **📊 Enhanced Spending Analytics (Chart.js)**:
   - **Daily Spend vs. Recommended Burn Rate**: Combined interactive Bar & Line chart showing daily spending against the recommended daily budget target line.
   - **Category Spend Ranking**: Horizontal bar chart automatically sorted descending by spend amount. Clicking any category bar instantly filters the transaction panel.

5. **📅 Interactive Monthly Calendar**:
   - Monthly grid with visual status dots and badges showing daily spending totals.
   - Quick date inspection panel showing individual items, payment modes, category icons, timestamps, and notes.

6. **💾 Pure Python Data Storage & Pruning**:
   - Structured CSV persistence in `data/expenses.csv` using native `csv.DictReader` and `csv.DictWriter`.
   - Thread-safe file operations with concurrent access locks.
   - Automatic 90-day rolling history with archival to `data/expenses_archive.csv`.

7. **📥 Export & Offline Backup**:
   - Instant direct download of `expenses.csv` via Flask's built-in `send_file`.

8. **🚀 Production Deployment Ready**:
   - Pre-configured `Procfile` for **Gunicorn** and cloud deployment on **Render**.

---

## 🏗️ Project Architecture

```text
Smart_Expense_Tracker/
├── app.py                 # Flask REST application & routing
├── storage.py             # Pure Python CSV & JSON storage engine with 3-month archival
├── voice_parser.py        # 7-Category Voice NLP parser & entity extraction
├── requirements.txt       # Pinned production dependencies (flask, gunicorn, python-dotenv)
├── Procfile               # WSGI runner for Render (Gunicorn)
├── .env.example           # Environment configuration template
├── .gitignore             # Git ignore rules for venv, secrets, logs
├── data/
│   ├── expenses.csv       # Active rolling 3-month records
│   ├── expenses_archive.csv # Historical archived records
│   └── budget_config.json # Monthly income and category budget limits
├── static/
│   ├── css/
│   │   └── style.css      # Custom animations, wave bars, category styles
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
Open your browser and navigate to `http://127.0.0.1:5000`.

---

## 🧪 Running Automated Tests

Run the comprehensive test suite verifying pure Python standard library operations, the 7-category classification engine, budget persistence, and voice NLP parsing:

```bash
python test_voice.py
python test_phase2.py
python test_phase3.py
python test_phase4.py
```

---

## 🌐 API Reference

### System & Health
- `GET /api/health` - Check service status, category configuration, and storage readiness.
- `GET /api/categories` - Returns the list of 7 valid category names.

### Monthly Budget & Income
- `GET /api/budget` - Get current monthly income and category allocations.
- `POST /api/budget` - Update monthly income and category allocation limits.

### Expenses & Analytics
- `GET /api/expenses` - Query expenses with optional `date=YYYY-MM-DD` and `category=Name` filters.
- `POST /api/expenses` - Add a new expense (validates category, amount, item, and date).
- `GET /api/summary/monthly?year=YYYY&month=MM` - Monthly totals, daily totals array, burn rate, category spent vs. allocated, and net savings.
- `GET /api/summary/rolling-3-months` - Rolling 90-day aggregate and category distribution.
- `GET /api/export` - Download `expenses.csv` data.

### AI Voice Assistant
- `POST /api/parse-voice` - Natural language Tanglish/English parser returning structured fields (`amount`, `category`, `item`, `date`, `payment_mode`).

---

## 📄 License
MIT License. Open-source household finance management.
