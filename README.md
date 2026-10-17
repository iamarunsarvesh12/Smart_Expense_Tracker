# Smart Home Expense Tracker 🎙️📊💰✉️

A modern, production-grade household expense & monthly budget tracking application built with **Flask**, Python's native standard library (**csv**, **json**, **datetime**, **smtplib**, **collections**), **Tailwind CSS**, and browser-native **Web Speech API** for AI-powered Tanglish and English voice expense recording. Fully compatible with Python 3.14+ with zero heavy C-dependencies (strictly **no Pandas** and **no OpenPyXL**).

---

## 🌟 Key Features

1. **🗓️ Date-Only Strict Schema (No Time Field)**:
   - Clean, lightweight CSV schema in `data/expenses.csv`:
     ```csv
     id,date,category,item,amount,payment_mode,notes
     ```
   - Standardized ISO `YYYY-MM-DD` date formatting across manual entry, voice parsing, filters, and reports.

2. **✉️ Month-End Email Dispatch**:
   - Automated dispatch on month-end (last day or 1st day of next month) and manual on-demand trigger via header button.
   - Strictly configured recipient: `sarveshsantosh2007s@gmail.com`.
   - Rich HTML financial statement with total spent, monthly income, net savings, and category budget progress.
   - Automatically generates and attaches an itemized CSV named `Expenses_<YYYY-MM>.csv` (Columns: Date, Category, Item, Amount, Payment Mode, Notes).
   - Zero external libraries — powered by Python standard `smtplib` and `email.mime`.

3. **🔒 Password-Protected Database Reset**:
   - Danger zone control in UI header with confirmation security modal.
   - Validates against `ADMIN_RESET_PASSWORD` configured in `.env` (default: `admin123`).
   - Returns `401 Unauthorized` on invalid password.
   - Upon authentication, truncates `data/expenses.csv` to headers only, clears archives, and resets budget defaults.

4. **🔄 Strict 3-Month Rolling Retention Engine**:
   - Automatically purges historical data older than the current calendar month plus the previous 2 months.
   - *Example*: On February 1st, records from November or earlier are purged from active storage, maintaining a lean rolling window.

5. **💰 Monthly Income & Category Budgeting Engine**:
   - **Monthly Budget Settings Modal**: Configure monthly household income (e.g., ₹25,000) and allocate custom spending limits across all 7 categories.
   - **Category Progress Bars**: Real-time visualization of Allocated Budget, Amount Spent, and Remaining Balance. Progress meters dynamically shift color (<75% Emerald, 75–90% Amber, >90% Rose/Over-budget).
   - **Net Monthly Savings Tracker**: Prominently displays `Total Income - Total Spent This Month = Net Savings` alongside a percentage savings rate meter.
   - **Recommended Daily Burn Rate**: Compares daily spending trends against the month's recommended daily burn rate (`Income / days_in_month`).
   - Persisted to `data/budget_config.json`.

6. **🗂️ 7 Granular Category Architecture**:
   - **Food**: Restaurants, Tea, Snacks, Swiggy / Zomato, Outside food.
   - **Groceries**: Provisions, Vegetables, Milk / Paal, Supermarket items.
   - **Bike & Car**: Petrol, Diesel, Vehicle Service, Mechanics, Punctures, Toll.
   - **Bills & Utilities**: EB / Electricity bill, Wi-Fi / Broadband, Mobile Recharge, Gas cylinder.
   - **Stationery & Office**: Printouts, Xerox, Books, Pens, Courier, Office supplies.
   - **Medical & Healthcare**: Medicines, Doctor consultation, Medical tests, Tablets.
   - **General & Others**: Money given to others, Lending, Casual cash spends, Miscellaneous.

7. **🎙️ AI Voice Assistant & Tanglish NLP Parser**:
   - Browser-native speech recognition (`en-IN` / `ta-IN`) for conversational expense entry.
   - Smart entity extraction for amounts, dates (today, yesterday / nethu), payment modes (UPI, Cash, Card), and category matching.
   - **Safety Confirmation Flow**: Speech is transcribed and presented in an editable confirmation modal before saving.

8. **📊 Enhanced Spending Analytics (Chart.js)**:
   - **Daily Spend vs. Recommended Burn Rate**: Combined interactive Bar & Line chart showing daily spending against the recommended daily budget target line.
   - **Category Spend Ranking**: Horizontal bar chart automatically sorted descending by spend amount. Clicking any category bar instantly filters the transaction panel.

---

## 🏗️ Project Architecture

```text
Smart_Expense_Tracker/
├── app.py                 # Flask REST application & routing
├── storage.py             # Pure Python CSV & JSON storage engine with 3-month retention & reset
├── email_service.py       # smtplib email dispatch service & CSV attachment generator
├── voice_parser.py        # 7-Category Voice NLP parser & entity extraction
├── requirements.txt       # Pinned production dependencies (flask, gunicorn, python-dotenv)
├── Procfile               # WSGI runner for Render (Gunicorn)
├── .env.example           # Environment configuration template
├── .gitignore             # Git ignore rules for venv, secrets, logs, and dispatch markers
├── data/
│   ├── expenses.csv       # Active rolling 3-month records (id,date,category,item,amount,payment_mode,notes)
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

### 2. Configure Environment
```bash
cp .env.example .env
```
Edit `.env` with your Gmail App Password if you want to enable real email delivery:
```env
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USER=sarveshsantosh2007s@gmail.com
EMAIL_PASS=your_gmail_app_password
RECIPIENT_EMAIL=sarveshsantosh2007s@gmail.com
ADMIN_RESET_PASSWORD=admin123
```

### 3. Run Development Server
```bash
python app.py
```
Navigate to `http://127.0.0.1:5000` in your browser.

---

## 🧪 Running Automated Tests

Run the comprehensive test suite verifying pure Python standard library operations, the strict schema (no time), 3-month retention, database reset, and email dispatch:

```bash
python test_phase2.py
python test_phase3.py
python test_phase4.py
python test_voice.py
```

---

## 🌐 API Reference

### System & Health
- `GET /api/health` - Check service status, schema columns, and storage readiness.
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

### Email Dispatch & Admin Controls
- `POST /api/send-monthly-report?month=YYYY-MM` - Dispatches monthly financial statement and attached CSV to `sarveshsantosh2007s@gmail.com`.
- `POST /api/reset-database` - Requires `{ "password": "..." }`. Wipes `expenses.csv` to header row and resets configurations.

### AI Voice Assistant
- `POST /api/parse-voice` - Natural language Tanglish/English parser returning structured fields (`amount`, `category`, `item`, `date`, `payment_mode`).

---

## 📄 License
MIT License. Open-source household finance management.
