"""
Smart Home Expense Tracker - Storage Engine (Pure Python)
Handles 7 granular expense categories, monthly income & category budgeting,
remaining balances & net savings, and CSV persistence with rolling 3-month archival.
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

# Thread safety lock for concurrent file access
_file_lock = threading.Lock()

# Standard CSV Schema
COLUMNS = [
    "id",
    "date",
    "time",
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
    Ensures correct headers and valid budget defaults exist.
    """
    with _file_lock:
        DATA_DIR.mkdir(parents=True, exist_ok=True)

        # 1. Initialize expenses.csv
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


def save_budget_config(payload: Dict[str, Any]) -> Tuple[bool, Optional[str], Dict[str, Any]]:
    """
    Validate and save monthly income and category allocations to data/budget_config.json.
    """
    if not isinstance(payload, dict):
        return False, "Payload must be a valid JSON object.", {}

    raw_income = payload.get("monthly_income")
    if raw_income is None:
        return False, "Field 'monthly_income' is required.", {}
    try:
        monthly_income = float(raw_income)
        if monthly_income <= 0:
            return False, "Field 'monthly_income' must be greater than 0.", {}
        monthly_income = round(monthly_income, 2)
    except (ValueError, TypeError):
        return False, "Field 'monthly_income' must be a valid numeric amount.", {}

    raw_cats = payload.get("categories", {})
    if not isinstance(raw_cats, dict):
        return False, "Field 'categories' must be an object with allocations for each category.", {}

    sanitized_cats = {}
    for cat in VALID_CATEGORIES:
        val = raw_cats.get(cat, 0.0)
        try:
            amt = float(val)
            if amt < 0:
                return False, f"Budget for '{cat}' cannot be negative.", {}
            sanitized_cats[cat] = round(amt, 2)
        except (ValueError, TypeError):
            sanitized_cats[cat] = 0.0

    updated_config = {
        "monthly_income": monthly_income,
        "categories": sanitized_cats,
        "updated_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    }

    with _file_lock:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(BUDGET_JSON, mode="w", encoding="utf-8") as f:
            json.dump(updated_config, f, indent=2)

    return True, None, updated_config


# ---------------------------------------------------------------------------
# Expense Persistence & Filtering
# ---------------------------------------------------------------------------

def read_all_expenses() -> List[Dict[str, Any]]:
    """
    Read all records from expenses.csv using csv.DictReader with parsed types.
    """
    with _file_lock:
        if not EXPENSES_CSV.exists() or os.path.getsize(EXPENSES_CSV) == 0:
            return []

        records: List[Dict[str, Any]] = []
        try:
            with open(EXPENSES_CSV, mode="r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        amt = round(float(row.get("amount", 0.0) or 0.0), 2)
                    except (ValueError, TypeError):
                        amt = 0.0

                    # Map legacy category names if encountered
                    raw_cat = str(row.get("category", "")).strip()
                    norm_cat = CATEGORY_LOOKUP.get(raw_cat.lower(), raw_cat)
                    if norm_cat not in VALID_CATEGORIES:
                        norm_cat = "General & Others"

                    records.append({
                        "id": str(row.get("id", "")).strip(),
                        "date": str(row.get("date", "")).strip(),
                        "time": str(row.get("time", "")).strip(),
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
    Validate incoming expense payload according to the 7 defined categories.
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

    # Validate Time
    time_str = payload.get("time")
    if time_str and isinstance(time_str, str) and time_str.strip():
        try:
            t = time_str.strip()
            if len(t) == 5:
                parsed_time = datetime.strptime(t, "%H:%M")
                normalized_time = parsed_time.strftime("%H:%M:00")
            else:
                parsed_time = datetime.strptime(t, "%H:%M:%S")
                normalized_time = parsed_time.strftime("%H:%M:%S")
        except ValueError:
            return False, "Invalid 'time' format. Must be HH:MM or HH:MM:SS.", None
    else:
        normalized_time = datetime.now().strftime("%H:%M:%S")

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
        "time": normalized_time,
        "category": canonical_category,
        "item": normalized_item,
        "amount": amount,
        "payment_mode": normalized_payment_mode,
        "notes": normalized_notes
    }

    return True, None, sanitized


def prune_rolling_history(months: int = 3) -> int:
    """
    Archives records older than `months * 30` days into expenses_archive.csv.
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

        cutoff_date = (datetime.now() - timedelta(days=months * 30)).strftime("%Y-%m-%d")

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


def add_expense(payload: Dict[str, Any]) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """
    Append new expense record safely via csv.DictWriter and prune rolling history.
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

    prune_rolling_history(months=3)
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

    # Sort descending by date and time
    filtered.sort(key=lambda x: (x.get("date", ""), x.get("time", "")), reverse=True)
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
    Comprehensive monthly summary including:
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
        "monthly_income": monthly_income,
        "total_spending": total_spending,
        "total_budget_allocated": total_allocated,
        "net_savings": net_savings,
        "savings_rate": savings_rate,
        "daily_budget_target": daily_budget_target,
        "transaction_count": len(month_expenses),
        "daily_totals": daily_totals,
        "category_breakdown": category_breakdown,
        "category_percentages": category_percentages,
        "category_budgets": category_budgets
    }


def get_rolling_3_months_summary() -> Dict[str, Any]:
    """
    High-level summary of the last 3 months (90 days).
    """
    all_expenses = read_all_expenses()

    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")

    window_expenses = [e for e in all_expenses if start_str <= e["date"] <= end_str]
    total_expense = round(sum(e["amount"] for e in window_expenses), 2)

    total_days = 90
    daily_average = round(total_expense / total_days, 2) if total_days > 0 else 0.0

    category_distribution: Dict[str, float] = {cat: 0.0 for cat in VALID_CATEGORIES}
    category_percentages: Dict[str, float] = {cat: 0.0 for cat in VALID_CATEGORIES}

    for e in window_expenses:
        cat = e.get("category", "")
        if cat in category_distribution:
            category_distribution[cat] += e["amount"]

    for cat in VALID_CATEGORIES:
        category_distribution[cat] = round(category_distribution[cat], 2)
        if total_expense > 0:
            category_percentages[cat] = round((category_distribution[cat] / total_expense) * 100, 1)

    month_map: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"total": 0.0, "count": 0})
    for e in window_expenses:
        ym = e["date"][:7]
        month_map[ym]["total"] += e["amount"]
        month_map[ym]["count"] += 1

    monthly_trend: List[Dict[str, Any]] = []
    for ym in sorted(month_map.keys()):
        monthly_trend.append({
            "month": ym,
            "total": round(month_map[ym]["total"], 2),
            "count": month_map[ym]["count"]
        })

    return {
        "period": {
            "start_date": start_str,
            "end_date": end_str,
            "total_days": total_days
        },
        "total_expense": total_expense,
        "daily_average": daily_average,
        "transaction_count": len(window_expenses),
        "category_distribution": category_distribution,
        "category_percentages": category_percentages,
        "monthly_trend": monthly_trend
    }
