"""
Smart Home Expense Tracker - Storage Engine (Pure Python Standard Library)
Strictly zero Pandas / zero OpenPyXL - 100% Python 3.14+ compatible.
Features:
- 7 Granular Expense Categories
- Date-Only Schema: id,date,category,item,amount,payment_mode,notes (No time field)
- Monthly Income & Category Budgeting Engine
- Remaining Balances & Net Savings Analytics
- Strict 3-Month Rolling Retention Purge
- Password-Protected Database Reset
"""

import os
import csv
import json
import uuid
import threading
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
from typing import Dict, Any, List, Optional, Tuple

# File & Directory Paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
EXPENSES_CSV = DATA_DIR / "expenses.csv"
ARCHIVE_CSV = DATA_DIR / "expenses_archive.csv"
BUDGET_JSON = DATA_DIR / "budget_config.json"
DISPATCH_TRACKER_JSON = DATA_DIR / "last_dispatched.json"

# Thread safety lock for concurrent file access
_file_lock = threading.Lock()

# Standard CSV Schema (Strictly Date Only, No Time)
COLUMNS = [
    "id",
    "date",
    "category",
    "item",
    "amount",
    "payment_mode",
    "notes"
]

# The 7 Granular Expense Categories
VALID_CATEGORIES = [
    "Food",
    "Groceries",
    "Bike & Car",
    "Bills & Utilities",
    "Stationery & Office",
    "Medical & Healthcare",
    "General & Others"
]

# Canonical lookup mapping for forgiving user input & legacy category migration
CATEGORY_LOOKUP = {
    # 7 Canonical categories
    "food": "Food",
    "groceries": "Groceries",
    "bike & car": "Bike & Car",
    "bike": "Bike & Car",
    "car": "Bike & Car",
    "bills & utilities": "Bills & Utilities",
    "bills": "Bills & Utilities",
    "utilities": "Bills & Utilities",
    "stationery & office": "Stationery & Office",
    "stationery": "Stationery & Office",
    "office": "Stationery & Office",
    "medical & healthcare": "Medical & Healthcare",
    "medical": "Medical & Healthcare",
    "general & others": "General & Others",
    "general": "General & Others",
    "others": "General & Others",
    # Legacy category aliases from Phase 1-3
    "food & groceries": "Food",
    "fuel & commute": "Bike & Car",
    "general & daily utilities": "Bills & Utilities"
}

# Default Budget Configuration
DEFAULT_BUDGET = {
    "monthly_income": 25000.0,
    "categories": {
        "Food": 4000.0,
        "Groceries": 5000.0,
        "Bike & Car": 3500.0,
        "Bills & Utilities": 3000.0,
        "Stationery & Office": 1000.0,
        "Medical & Healthcare": 2500.0,
        "General & Others": 2000.0
    }
}


# ---------------------------------------------------------------------------
# Storage & Budget Configuration Initialization
# ---------------------------------------------------------------------------

def init_storage() -> None:
    """
    Auto-initialize data directory, expenses.csv, and budget_config.json.
    Ensures correct schema headers (Date only, no time) exist.
    """
    with _file_lock:
        DATA_DIR.mkdir(parents=True, exist_ok=True)

        # 1. Initialize expenses.csv with strict schema
        if not EXPENSES_CSV.exists() or os.path.getsize(EXPENSES_CSV) == 0:
            with open(EXPENSES_CSV, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(COLUMNS)
        else:
            try:
                with open(EXPENSES_CSV, mode="r", newline="", encoding="utf-8") as f:
                    reader = csv.reader(f)
                    header = next(reader, None)
                    if header != COLUMNS:
                        f.seek(0)
                        dict_reader = csv.DictReader(f)
                        aligned_rows = []
                        for r in dict_reader:
                            aligned_rows.append({col: r.get(col, "") for col in COLUMNS})
                        with open(EXPENSES_CSV, mode="w", newline="", encoding="utf-8") as out_f:
                            writer = csv.DictWriter(out_f, fieldnames=COLUMNS, extrasaction="ignore")
                            writer.writeheader()
                            writer.writerows(aligned_rows)
            except Exception:
                with open(EXPENSES_CSV, mode="w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(COLUMNS)

        # 2. Initialize budget_config.json
        if not BUDGET_JSON.exists() or os.path.getsize(BUDGET_JSON) == 0:
            with open(BUDGET_JSON, mode="w", encoding="utf-8") as f:
                json.dump(DEFAULT_BUDGET, f, indent=2)


def get_budget_config() -> Dict[str, Any]:
    """
    Load budget configuration from data/budget_config.json.
    Guarantees all 7 categories are present.
    """
    with _file_lock:
        if not BUDGET_JSON.exists() or os.path.getsize(BUDGET_JSON) == 0:
            return DEFAULT_BUDGET.copy()

        try:
            with open(BUDGET_JSON, mode="r", encoding="utf-8") as f:
                config = json.load(f)

            monthly_income = float(config.get("monthly_income", DEFAULT_BUDGET["monthly_income"]))
            categories = config.get("categories", {})
            
            # Ensure all 7 categories exist in dictionary
            sanitized_cats = {}
            for cat in VALID_CATEGORIES:
                val = categories.get(cat, DEFAULT_BUDGET["categories"].get(cat, 0.0))
                try:
                    sanitized_cats[cat] = round(float(val), 2)
                except (ValueError, TypeError):
                    sanitized_cats[cat] = 0.0

            return {
                "monthly_income": round(monthly_income, 2),
                "categories": sanitized_cats
            }
        except Exception:
            return DEFAULT_BUDGET.copy()


def save_budget_config(payload: Dict[str, Any]) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """
    Validate and save monthly income and category allocations to budget_config.json.
    """
    if not isinstance(payload, dict):
        return False, "Budget payload must be a JSON object.", None

    # Validate monthly income
    raw_income = payload.get("monthly_income")
    if raw_income is None:
        return False, "Field 'monthly_income' is required.", None
    try:
        monthly_income = float(raw_income)
        if monthly_income < 0:
            return False, "Monthly income cannot be negative.", None
        monthly_income = round(monthly_income, 2)
    except (ValueError, TypeError):
        return False, "Monthly income must be a valid number.", None

    # Validate categories map
    raw_categories = payload.get("categories")
    if not isinstance(raw_categories, dict):
        return False, "Field 'categories' must be an object with category budgets.", None

    sanitized_cats = {}
    for cat in VALID_CATEGORIES:
        val = raw_categories.get(cat, 0.0)
        try:
            num = float(val)
            if num < 0:
                return False, f"Budget for category '{cat}' cannot be negative.", None
            sanitized_cats[cat] = round(num, 2)
        except (ValueError, TypeError):
            return False, f"Budget for category '{cat}' must be a valid number.", None

    new_config = {
        "monthly_income": monthly_income,
        "categories": sanitized_cats,
        "updated_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    }

    with _file_lock:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(BUDGET_JSON, mode="w", encoding="utf-8") as f:
            json.dump(new_config, f, indent=2)

    return True, None, new_config


# ---------------------------------------------------------------------------
# Strict 3-Month Rolling Retention Engine
# ---------------------------------------------------------------------------

def get_retention_cutoff_date(now: Optional[datetime] = None) -> str:
    """
    Calculates the strict 3-month retention cutoff date (YYYY-MM-DD).
    Maintains current calendar month plus the previous 2 months.
    Example: On February 1st -> records before Dec 1st (Nov or earlier) are purged.
    """
    if now is None:
        now = datetime.now()
    year = now.year
    month = now.month
    
    # 2 months prior start date
    month_cutoff = month - 2
    year_cutoff = year
    if month_cutoff <= 0:
        month_cutoff += 12
        year_cutoff -= 1
        
    return f"{year_cutoff:04d}-{month_cutoff:02d}-01"


def prune_rolling_history(now: Optional[datetime] = None) -> int:
    """
    Purges records older than current month + previous 2 months from expenses.csv,
    archiving them safely into expenses_archive.csv.
    """
    with _file_lock:
        if not EXPENSES_CSV.exists() or os.path.getsize(EXPENSES_CSV) == 0:
            return 0

        all_records: List[Dict[str, Any]] = []
        with open(EXPENSES_CSV, mode="r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                all_records.append(r)

        if not all_records:
            return 0

        cutoff_date = get_retention_cutoff_date(now)

        recent: List[Dict[str, Any]] = []
        older: List[Dict[str, Any]] = []

        for r in all_records:
            if r.get("date", "") < cutoff_date:
                older.append(r)
            else:
                recent.append(r)

        if older:
            archive_exists = ARCHIVE_CSV.exists() and os.path.getsize(ARCHIVE_CSV) > 0
            with open(ARCHIVE_CSV, mode="a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=COLUMNS, extrasaction="ignore")
                if not archive_exists:
                    writer.writeheader()
                writer.writerows(older)

            with open(EXPENSES_CSV, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=COLUMNS, extrasaction="ignore")
                writer.writeheader()
                writer.writerows(recent)

            return len(older)

        return 0


# ---------------------------------------------------------------------------
# Database Reset (Password-Protected Backend Action)
# ---------------------------------------------------------------------------

def reset_database() -> Tuple[bool, str]:
    """
    Completely wipe all expense records and reset data files to a clean slate.
    Truncates expenses.csv to header only, deletes archives, and resets budget defaults.
    """
    with _file_lock:
        DATA_DIR.mkdir(parents=True, exist_ok=True)

        # 1. Truncate expenses.csv to headers only
        with open(EXPENSES_CSV, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(COLUMNS)

        # 2. Remove archive if present
        if ARCHIVE_CSV.exists():
            try:
                ARCHIVE_CSV.unlink()
            except Exception:
                pass

        # 3. Reset budget config to pristine defaults
        with open(BUDGET_JSON, mode="w", encoding="utf-8") as f:
            json.dump(DEFAULT_BUDGET, f, indent=2)

        # 4. Remove auto-dispatch tracker if present
        if DISPATCH_TRACKER_JSON.exists():
            try:
                DISPATCH_TRACKER_JSON.unlink()
            except Exception:
                pass

        return True, "Database successfully reset to pristine empty state."


# ---------------------------------------------------------------------------
# Core Expense CRUD & Aggregation Engine
# ---------------------------------------------------------------------------

def read_all_expenses() -> List[Dict[str, Any]]:
    """
    Thread-safe read of active expenses from data/expenses.csv.
    """
    with _file_lock:
        if not EXPENSES_CSV.exists() or os.path.getsize(EXPENSES_CSV) == 0:
            return []

        records = []
        try:
            with open(EXPENSES_CSV, mode="r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if not row.get("id") or not row.get("date"):
                        continue

                    try:
                        amt = round(float(row.get("amount", 0.0) or 0.0), 2)
                    except (ValueError, TypeError):
                        amt = 0.0

                    raw_cat = str(row.get("category", "")).strip()
                    norm_cat = CATEGORY_LOOKUP.get(raw_cat.lower(), raw_cat)
                    if norm_cat not in VALID_CATEGORIES:
                        norm_cat = "General & Others"

                    records.append({
                        "id": str(row.get("id", "")).strip(),
                        "date": str(row.get("date", "")).strip(),
                        "category": norm_cat,
                        "item": str(row.get("item", "")).strip(),
                        "amount": amt,
                        "payment_mode": str(row.get("payment_mode", "")).strip(),
                        "notes": str(row.get("notes", "")).strip() if row.get("notes") else ""
                    })
            return records
        except Exception:
            return []


def validate_expense_payload(payload: Dict[str, Any]) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """
    Validate incoming expense payload according to the strict schema.
    Date format: YYYY-MM-DD. No time field.
    """
    if not isinstance(payload, dict):
        return False, "Payload must be a valid JSON object.", None

    # Validate Date (YYYY-MM-DD)
    date_str = payload.get("date")
    if not date_str or not isinstance(date_str, str):
        return False, "Field 'date' is required in YYYY-MM-DD format.", None
    try:
        parsed_date = datetime.strptime(date_str.strip(), "%Y-%m-%d")
        normalized_date = parsed_date.strftime("%Y-%m-%d")
    except ValueError:
        return False, "Invalid 'date' format. Must be YYYY-MM-DD.", None

    # Validate Category against the 7 defined buckets
    raw_category = payload.get("category")
    if not raw_category or not isinstance(raw_category, str):
        return False, f"Field 'category' is required. Allowed values: {', '.join(VALID_CATEGORIES)}", None

    canonical_category = CATEGORY_LOOKUP.get(raw_category.strip().lower())
    if not canonical_category:
        return False, f"Invalid category '{raw_category}'. Allowed categories: {', '.join(VALID_CATEGORIES)}", None

    # Validate Item
    item = payload.get("item")
    if not item or not isinstance(item, str) or not item.strip():
        return False, "Field 'item' is required and must be a non-empty string.", None
    normalized_item = item.strip()

    # Validate Amount
    raw_amount = payload.get("amount")
    if raw_amount is None:
        return False, "Field 'amount' is required.", None
    try:
        amount = float(raw_amount)
        if amount <= 0:
            return False, "Field 'amount' must be a positive number greater than 0.", None
        amount = round(amount, 2)
    except (ValueError, TypeError):
        return False, "Field 'amount' must be a valid numeric value.", None

    # Validate Payment Mode
    payment_mode = payload.get("payment_mode")
    if not payment_mode or not isinstance(payment_mode, str) or not payment_mode.strip():
        return False, "Field 'payment_mode' is required (e.g., UPI, Cash, Card, Net Banking).", None
    normalized_payment_mode = payment_mode.strip()

    # Validate Notes
    notes = payload.get("notes", "")
    normalized_notes = str(notes).strip() if notes is not None else ""

    sanitized = {
        "date": normalized_date,
        "category": canonical_category,
        "item": normalized_item,
        "amount": amount,
        "payment_mode": normalized_payment_mode,
        "notes": normalized_notes
    }

    return True, None, sanitized


def add_expense(payload: Dict[str, Any]) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """
    Append new expense record safely via csv.DictWriter and run rolling retention purge.
    """
    is_valid, error_msg, sanitized = validate_expense_payload(payload)
    if not is_valid or sanitized is None:
        return False, error_msg, None

    expense_id = f"exp_{uuid.uuid4().hex[:8]}"
    record = {
        "id": expense_id,
        **sanitized
    }

    with _file_lock:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        file_exists = EXPENSES_CSV.exists() and os.path.getsize(EXPENSES_CSV) > 0

        with open(EXPENSES_CSV, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=COLUMNS, extrasaction="ignore")
            if not file_exists:
                writer.writeheader()
            writer.writerow(record)

    # Automatic 3-month rolling retention prune
    prune_rolling_history()
    return True, None, record


def get_expenses_by_date(date_str: Optional[str] = None, category_filter: Optional[str] = None) -> Dict[str, Any]:
    """
    Query expenses by specific date or category filter.
    """
    all_expenses = read_all_expenses()

    filtered = all_expenses
    if date_str:
        filtered = [e for e in filtered if e["date"] == date_str]
    if category_filter:
        norm_cat = CATEGORY_LOOKUP.get(category_filter.strip().lower(), category_filter.strip())
        filtered = [e for e in filtered if e["category"] == norm_cat]

    # Sort descending by date and ID
    filtered.sort(key=lambda x: (x.get("date", ""), x.get("id", "")), reverse=True)
    daily_total = round(sum(e["amount"] for e in filtered), 2)

    return {
        "date": date_str,
        "category_filter": category_filter,
        "daily_total": daily_total,
        "count": len(filtered),
        "expenses": filtered
    }


def get_monthly_summary(year: int, month: int) -> Dict[str, Any]:
    """
    Comprehensive monthly summary:
    - Total monthly spend & transaction count
    - Monthly Income, Net Savings & Savings Rate %
    - Daily spend totals array & recommended daily burn rate
    - Category spend breakdown, allocated budgets, remaining balances, and over-budget alerts
    """
    all_expenses = read_all_expenses()
    month_prefix = f"{year:04d}-{month:02d}"

    # Days in this month
    if month == 12:
        next_month_date = datetime(year + 1, 1, 1)
    else:
        next_month_date = datetime(year, month + 1, 1)
    days_in_month = (next_month_date - datetime(year, month, 1)).days

    month_expenses = [e for e in all_expenses if e["date"].startswith(month_prefix)]
    total_spending = round(sum(e["amount"] for e in month_expenses), 2)

    # Budget Configuration
    budget_cfg = get_budget_config()
    monthly_income = budget_cfg.get("monthly_income", DEFAULT_BUDGET["monthly_income"])
    category_allocations = budget_cfg.get("categories", {})

    # Net Savings & Savings Rate
    net_savings = round(monthly_income - total_spending, 2)
    savings_rate = round((net_savings / monthly_income) * 100, 1) if monthly_income > 0 else 0.0

    # Recommended Daily Burn Rate: Income / days_in_month
    daily_budget_target = round(monthly_income / days_in_month, 2) if days_in_month > 0 else 0.0

    # Daily Totals Map
    daily_map: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"total": 0.0, "count": 0})
    for e in month_expenses:
        d = e["date"]
        daily_map[d]["total"] += e["amount"]
        daily_map[d]["count"] += 1

    daily_totals: List[Dict[str, Any]] = []
    for d in sorted(daily_map.keys()):
        daily_totals.append({
            "date": d,
            "total": round(daily_map[d]["total"], 2),
            "count": daily_map[d]["count"]
        })

    # Category Breakdown across all 7 Categories
    category_breakdown: Dict[str, float] = {cat: 0.0 for cat in VALID_CATEGORIES}
    category_percentages: Dict[str, float] = {cat: 0.0 for cat in VALID_CATEGORIES}
    category_budgets: Dict[str, Dict[str, Any]] = {}

    for e in month_expenses:
        cat = e.get("category", "")
        if cat in category_breakdown:
            category_breakdown[cat] += e["amount"]

    total_allocated = round(sum(category_allocations.get(cat, 0.0) for cat in VALID_CATEGORIES), 2)

    for cat in VALID_CATEGORIES:
        spent = round(category_breakdown[cat], 2)
        category_breakdown[cat] = spent
        if total_spending > 0:
            category_percentages[cat] = round((spent / total_spending) * 100, 1)

        allocated = round(category_allocations.get(cat, 0.0), 2)
        remaining = round(allocated - spent, 2)
        pct_used = round((spent / allocated) * 100, 1) if allocated > 0 else (100.0 if spent > 0 else 0.0)
        is_over = spent > allocated if allocated > 0 else (spent > 0)

        category_budgets[cat] = {
            "spent": spent,
            "allocated": allocated,
            "remaining": remaining,
            "pct_used": pct_used,
            "is_over": is_over
        }

    return {
        "year": year,
        "month": month,
        "month_label": datetime(year, month, 1).strftime("%B %Y"),
        "days_in_month": days_in_month,
        "total_spending": total_spending,
        "transaction_count": len(month_expenses),
        "monthly_income": monthly_income,
        "total_budget_allocated": total_allocated,
        "net_savings": net_savings,
        "savings_rate": savings_rate,
        "daily_budget_target": daily_budget_target,
        "daily_totals": daily_totals,
        "category_breakdown": category_breakdown,
        "category_percentages": category_percentages,
        "category_budgets": category_budgets
    }


def get_rolling_3_months_summary() -> Dict[str, Any]:
    """
    Get rolling 3-month aggregated metrics.
    """
    all_expenses = read_all_expenses()
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")

    rolling_expenses = [e for e in all_expenses if start_str <= e["date"] <= end_str]
    total_spent = round(sum(e["amount"] for e in rolling_expenses), 2)
    daily_avg = round(total_spent / 90, 2)

    cat_counts: Dict[str, float] = {cat: 0.0 for cat in VALID_CATEGORIES}
    for e in rolling_expenses:
        cat = e.get("category", "")
        if cat in cat_counts:
            cat_counts[cat] += e["amount"]

    return {
        "start_date": start_str,
        "end_date": end_str,
        "total_expense": total_spent,
        "daily_average": daily_avg,
        "transaction_count": len(rolling_expenses),
        "category_distribution": {k: round(v, 2) for k, v in cat_counts.items()}
    }
