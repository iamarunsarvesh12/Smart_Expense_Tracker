# Smart Home Expense Tracker · 50:20:20:10 Budget OS

A high-density, minimal household financial workspace and automated monthly budgeting engine inspired by **Linear and Stripe UI/UX principles**. Built with **Flask** and Python standard libraries only (**csv**, **json**, **datetime**, **smtplib**, **collections**), browser-native **Web Speech API** for Tanglish & English voice logging, and **Chart.js**.

Fully compatible with **Python 3.14+** with strictly **no Pandas** and **no OpenPyXL**.

---

## 💎 Key Features

### 1. Automated 50:20:20:10 Salary Budget Engine
When the user specifies their Monthly Salary / Income (e.g., ₹20,000 or custom), the engine automatically computes and tracks four macro financial pillars:

1. **Household Needs (50% — Salary × 0.50)**:
   - *Mapped Categories*: Groceries, Food, Bills & Utilities, Medical & Healthcare.
   - *Progress Meter*: Dynamic status tracking (Emerald < 75%, Amber 75–90%, Rose > 90%).
2. **Lifestyle & Wants (20% — Salary × 0.20)**:
   - *Mapped Categories*: Bike & Car (Transport/Fuel), Stationery & Office, General & Others (Entertainment/Shopping).
   - *Progress Meter*: Dynamic threshold alerts.
3. **Monthly Investments & SIP (20% — Salary × 0.20)**:
   - *Mapped Category*: Investments & SIP.
   - Dedicated allocation tracker for mutual funds, index SIPs, and wealth creation.
4. **Emergency Fund (10% — Salary × 0.10)**:
   - *Mapped Category*: Emergency Fund.
   - Dedicated contingency buffer tracking towards a **6-month backup goal** (`6 × Needs Limit = ₹60,000`).

Data is persisted in `data/budget_config.json`:
```json
{
  "monthly_income": 20000.0,
  "currency": "₹",
  "emergency_fund_accumulated": 36000.0,
  "emergency_target_months": 6,
  "rule_split": {
    "needs_pct": 50,
    "lifestyle_pct": 20,
    "investments_pct": 20,
    "emergency_pct": 10
  },
  "calculated_targets": {
    "needs": 10000.0,
    "lifestyle": 4000.0,
    "investments": 4000.0,
    "emergency": 2000.0,
    "emergency_goal": 60000.0
  }
}
```

---

### 2. Linear & Stripe Inspired UI/UX Workspace
Completely refactored into a focused, utilitarian, uncluttered financial interface:

- **Top Minimal Navbar**:
  - Brand monomark with `50:20:20:10 Engine` badge.
  - Interactive month stepper (`← October 2026 →`) with one-click `Today` jump.
  - "Voice Input" trigger with live audio-wave indicator.
  - "Email Report" trigger for instant statement dispatch.
  - "Settings / Reset" dropdown menu (salary config, CSV export, safe reset).
- **5-Pillar Budget Ribbon**:
  - Horizontal high-density segmented ribbon displaying `Total Salary`, `50% Needs`, `20% Lifestyle`, `20% Investments`, and `10% Emergency Fund`.
  - Elegant, thin hairline progress bars with intelligent color coding:
    - 🟢 **Emerald**: Spending under 75% of limit.
    - 🟡 **Amber**: Approaching limit (75%–90%).
    - 🔴 **Rose**: Exceeding allocation threshold (>90%).
- **Workspace Split-View**:
  - **Left Column (Input & Calendar)**:
    - Compact inline expense form (Date, Category, Item description, Amount in ₹, Payment mode, Notes).
    - Keyboard shortcut support: `Ctrl + Enter` to submit.
    - Minimalist monthly date picker / mini-calendar with small subtle dots indicating spending days. Clicking a date filters the ledger with an active filter pill.
    - Sleek Tanglish voice dictation button with animated wave ticker.
  - **Right Column (Macro Analytics & Ledger)**:
    - Desaturated Chart.js bar chart comparing **50:20:20:10 Rule Targets vs Actual Spend**.
    - Minimalist transaction feed grouped by date with category badges and one-click delete.
    - Real-time search filter and category dropdown selector.

---

### 3. Date-Only Strict CSV Schema
Expenses are stored in `data/expenses.csv` conforming to the exact schema:
```csv
id,date,category,item,amount,payment_mode,notes
exp_1001,2026-10-02,Groceries,Supermarket Provisions,2450.00,UPI,Monthly grocery stock
exp_1002,2026-10-03,Bills & Utilities,TNEB Electricity Bill,1320.00,UPI,Bi-monthly power bill
```

---

### 4. Tanglish & English Voice NLP Assistant
- Natural speech recognition via browser Web Speech API (`ta-IN` / `en-IN`).
- Extracts amount, category, item, payment mode, and date from conversational phrases:
  - *"Iniku petrol 300 rupees bike UPI"* → Bike & Car, ₹300, UPI
  - *"Supermarket groceries 1200 cash vanginen"* → Groceries, ₹1200, Cash
  - *"Swiggy food dinner 480 card"* → Food, ₹480, Credit Card
  - *"TNEB current bill 750 upi"* → Bills & Utilities, ₹750, UPI
  - *"SIP mutual fund 2500 net banking"* → Investments & SIP, ₹2500, Net Banking

---

### 5. Email Dispatch Service
- Dispatches rich monthly financial reports to `sarveshsantosh2007s@gmail.com`.
- HTML statement summarizing 50:20:20:10 allocations, spent percentages, and itemized CSV report.
- Standard library `smtplib` implementation with zero external dependencies.

---

## 🚀 Quickstart

1. **Clone & Setup**:
   ```bash
   git clone https://github.com/iamarunsarvesh12/Smart_Expense_Tracker.git
   cd Smart_Expense_Tracker
   ```

2. **Run Locally**:
   ```bash
   python app.py
   ```
   Open `http://localhost:5000` in your browser.

3. **Run Automated Test Suite**:
   ```bash
   python test_50_20_20_10.py
   python test_phase4.py
   python test_voice.py
   ```
