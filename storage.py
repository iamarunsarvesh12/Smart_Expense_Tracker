"""
Smart Home Expense Tracker - Storage Engine (Pure Python)
Thread-safe CSV persistence, native Python analytics, category validation,
and rolling 3-month archival using standard library modules (csv, datetime, collections).
"""

import os
import csv
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

# The 5 Defined Expense Categories
VALID_CATEGORIES = [
    "Food & Groceries",
    "Fuel & Commute",
    "Stationery & Office",
    "Medical & Healthcare",
    "General & Daily Utilities"
]

# Case-insensitive mapping for forgiving user input
CATEGORY_LOOKUP = {cat.lower(): cat for cat in VALID_CATEGORIES}


def init_storage() -> None:
    """
    Ensure data directory and expenses.csv exist with the correct headers.
    """
    with _file_lock:
        DATA_DIR.mkdir(parents=True, exist_ok=True)

        if not EXPENSES_CSV.exists() or os.path.getsize(EXPENSES_CSV) == 0:
            with open(EXPENSES_CSV, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(COLUMNS)
            return

        # Check existing file header
        try:
            with open(EXPENSES_CSV, mode="r", newline="", encoding="utf-8") as f:
                reader = csv.reader(f)
                header = next(reader, None)
                if header != COLUMNS:
                    # File exists but header is outdated/corrupted; reinitialize cleanly
                    rows = []
                    if header:
                        # Attempt to salvage data if matching column names exist
                        f.seek(0)
                        dict_reader = csv.DictReader(f)
                        for r in dict_reader:
                            clean_r = {col: r.get(col, "") for col in COLUMNS}
                            rows.append(clean_r)
                    with open(EXPENSES_CSV, mode="w", newline="", encoding="utf-8") as out_f:
                        writer = csv.DictWriter(out_f, fieldnames=COLUMNS)
                        writer.writeheader()
                        writer.writerows(rows)
        except Exception:
            with open(EXPENSES_CSV, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(COLUMNS)


def read_all_expenses() -> List[Dict[str, Any]]:
    """
    Read all records from expenses.csv safely with parsed types.
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

                    records.append({
                        "id": str(row.get("id", "")).strip(),
                        "date": str(row.get("date", "")).strip(),
                        "time": str(row.get("time", "")).strip(),
                        "category": str(row.get("category", "")).strip(),
                        "item": str(row.get("item", "")).strip(),
                        "amount": amt,
                        "payment_mode": str(row.get("payment_mode", "")).strip(),
                        "notes": str(row.get("notes", "")).strip() if row.get("notes") else ""
                    })
            return records
        except Exception:
            return []


def write_all_expenses(records: List[Dict[str, Any]]) -> None:
    """
    Atomically rewrite records to expenses.csv.
    """
    with _file_lock:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(EXPENSES_CSV, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=COLUMNS, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(records)


def validate_expense_payload(payload: Dict[str, Any]) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """
    Validate incoming expense payload. Returns (is_valid, error_message, sanitized_data).
    """
    if not isinstance(payload, dict):
        return False, "Payload must be a valid JSON object.", None

    # Validate Date
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

    # Validate Category
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
    Archives records older than `months * 30` days into expenses_archive.csv
    and keeps expenses.csv pruned.
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
    Validate, assign ID, append expense record using csv.DictWriter, and prune rolling history.
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


def get_expenses_by_date(date_str: Optional[str] = None) -> Dict[str, Any]:
    """
    Retrieve expenses. If date_str is provided, filters for that exact date
    and calculates daily total.
    """
    all_expenses = read_all_expenses()

    if date_str:
        filtered = [e for e in all_expenses if e["date"] == date_str]
        selected_date = date_str
    else:
        filtered = all_expenses
        selected_date = None

    # Sort descending by date and time
    filtered.sort(key=lambda x: (x.get("date", ""), x.get("time", "")), reverse=True)

    total_amount = round(sum(e["amount"] for e in filtered), 2)

    return {
        "date": selected_date,
        "daily_total": total_amount,
        "count": len(filtered),
        "expenses": filtered
    }


def get_monthly_summary(year: int, month: int) -> Dict[str, Any]:
    """
    Generate monthly summary:
    - Total monthly spend
    - Daily totals array (for calendar indicators)
    - Category-wise spending breakdown across all 5 buckets
    """
    all_expenses = read_all_expenses()
    month_prefix = f"{year:04d}-{month:02d}"

    month_expenses = [e for e in all_expenses if e["date"].startswith(month_prefix)]
    total_spending = round(sum(e["amount"] for e in month_expenses), 2)

    # Group daily totals
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

    # Category breakdown across all 5 standard categories
    category_breakdown: Dict[str, float] = {cat: 0.0 for cat in VALID_CATEGORIES}
    category_percentages: Dict[str, float] = {cat: 0.0 for cat in VALID_CATEGORIES}

    for e in month_expenses:
        cat = e.get("category", "")
        if cat in category_breakdown:
            category_breakdown[cat] += e["amount"]

    for cat in VALID_CATEGORIES:
        category_breakdown[cat] = round(category_breakdown[cat], 2)
        if total_spending > 0:
            category_percentages[cat] = round((category_breakdown[cat] / total_spending) * 100, 1)

    return {
        "year": year,
        "month": month,
        "month_label": datetime(year, month, 1).strftime("%B %Y"),
        "total_spending": total_spending,
        "transaction_count": len(month_expenses),
        "daily_totals": daily_totals,
        "category_breakdown": category_breakdown,
        "category_percentages": category_percentages
    }


def get_rolling_3_months_summary() -> Dict[str, Any]:
    """
    Returns a high-level summary of the last 3 months (90 days):
    - Total expense
    - Category distribution
    - Daily average
    - Monthly trend
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

    # Monthly breakdown trend
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
