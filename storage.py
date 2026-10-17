"""
Smart Home Expense Tracker - Storage Engine
Handles CSV persistence, Pandas analytics, category validation,
and rolling 3-month archival.
"""

import os
import uuid
from datetime import datetime, timedelta
from pathlib import Path
import threading
from typing import Dict, Any, List, Optional, Tuple

import pandas as pd

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
    Ensure the data directory and expenses.csv file exist with the correct headers.
    """
    with _file_lock:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        
        if not EXPENSES_CSV.exists():
            df_new = pd.DataFrame(columns=COLUMNS)
            df_new.to_csv(EXPENSES_CSV, index=False)
            return

        # Check existing file header compatibility
        try:
            df_existing = pd.read_csv(EXPENSES_CSV)
            if list(df_existing.columns) != COLUMNS:
                # Re-align existing data if compatible or initialize with required headers
                aligned = pd.DataFrame(columns=COLUMNS)
                for col in COLUMNS:
                    if col in df_existing.columns:
                        aligned[col] = df_existing[col]
                    else:
                        aligned[col] = ""
                aligned.to_csv(EXPENSES_CSV, index=False)
        except Exception:
            # If file is empty or corrupted, reinitialize clean
            df_new = pd.DataFrame(columns=COLUMNS)
            df_new.to_csv(EXPENSES_CSV, index=False)


def validate_expense_payload(payload: Dict[str, Any]) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """
    Validate incoming expense payload according to business rules.
    Returns (is_valid, error_message, sanitized_data).
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

    # Validate Time (optional, defaults to current time)
    time_str = payload.get("time")
    if time_str and isinstance(time_str, str) and time_str.strip():
        try:
            # Accept HH:MM:SS or HH:MM
            time_val = time_str.strip()
            if len(time_val) == 5:
                parsed_time = datetime.strptime(time_val, "%H:%M")
                normalized_time = parsed_time.strftime("%H:%M:00")
            else:
                parsed_time = datetime.strptime(time_val, "%H:%M:%S")
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
        # Round to 2 decimal places
        amount = round(amount, 2)
    except (ValueError, TypeError):
        return False, "Field 'amount' must be a valid numeric value.", None

    # Validate Payment Mode
    payment_mode = payload.get("payment_mode")
    if not payment_mode or not isinstance(payment_mode, str) or not payment_mode.strip():
        return False, "Field 'payment_mode' is required (e.g., UPI, Cash, Card, Net Banking).", None
    normalized_payment_mode = payment_mode.strip()

    # Validate Notes (Optional)
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
    Archives records older than `months` rolling months into expenses_archive.csv
    and keeps expenses.csv pruned.
    Returns count of archived records.
    """
    with _file_lock:
        if not EXPENSES_CSV.exists():
            return 0

        df = pd.read_csv(EXPENSES_CSV)
        if df.empty or "date" not in df.columns:
            return 0

        # Cutoff date: 90 days ago from today
        cutoff_date = (datetime.now() - timedelta(days=months * 30)).strftime("%Y-%m-%d")

        # Convert date to string comparison
        older_mask = df["date"] < cutoff_date
        older_df = df[older_mask]
        recent_df = df[~older_mask]

        if not older_df.empty:
            # Append older records to expenses_archive.csv
            if ARCHIVE_CSV.exists():
                older_df.to_csv(ARCHIVE_CSV, mode="a", index=False, header=False)
            else:
                older_df.to_csv(ARCHIVE_CSV, index=False)

            # Rewrite active expenses.csv with only recent records
            recent_df.to_csv(EXPENSES_CSV, index=False)
            return len(older_df)

        return 0


def add_expense(payload: Dict[str, Any]) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """
    Validate, assign ID, append expense record to CSV, and run rolling prune check.
    """
    is_valid, error_msg, sanitized = validate_expense_payload(payload)
    if not is_valid:
        return False, error_msg, None

    # Generate unique ID (8-char hexadecimal identifier)
    expense_id = f"exp_{uuid.uuid4().hex[:8]}"
    record = {
        "id": expense_id,
        **sanitized
    }

    with _file_lock:
        # Read or create
        if EXPENSES_CSV.exists() and os.path.getsize(EXPENSES_CSV) > 0:
            df = pd.read_csv(EXPENSES_CSV)
        else:
            df = pd.DataFrame(columns=COLUMNS)

        new_row = pd.DataFrame([record])
        if df.empty:
            df = new_row
        else:
            df = pd.concat([df, new_row], ignore_index=True)
        df.to_csv(EXPENSES_CSV, index=False)

    # Automatically enforce rolling 3-month window
    prune_rolling_history(months=3)

    return True, None, record


def get_expenses_dataframe() -> pd.DataFrame:
    """
    Safely load active expenses into a DataFrame with consistent types.
    """
    with _file_lock:
        if not EXPENSES_CSV.exists():
            return pd.DataFrame(columns=COLUMNS)
        try:
            df = pd.read_csv(
                EXPENSES_CSV,
                dtype={
                    "id": str,
                    "date": str,
                    "time": str,
                    "category": str,
                    "item": str,
                    "payment_mode": str,
                    "notes": str
                }
            )
            # Ensure amount is numeric float
            df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0.0)
            df["notes"] = df["notes"].fillna("")
            return df
        except Exception:
            return pd.DataFrame(columns=COLUMNS)


def get_expenses_by_date(date_str: Optional[str] = None) -> Dict[str, Any]:
    """
    Retrieve expenses. If date_str is provided, filters for that exact date
    and calculates daily total.
    """
    df = get_expenses_dataframe()

    if date_str:
        filtered_df = df[df["date"] == date_str]
        selected_date = date_str
    else:
        filtered_df = df
        selected_date = None

    # Sort by date and time descending
    if not filtered_df.empty and "date" in filtered_df.columns and "time" in filtered_df.columns:
        filtered_df = filtered_df.sort_values(by=["date", "time"], ascending=[False, False])

    records = filtered_df.to_dict(orient="records")
    total_amount = round(float(filtered_df["amount"].sum()), 2) if not filtered_df.empty else 0.0

    return {
        "date": selected_date,
        "daily_total": total_amount,
        "count": len(records),
        "expenses": records
    }


def get_monthly_summary(year: int, month: int) -> Dict[str, Any]:
    """
    Generate monthly summary:
    - Total spending for that month
    - Daily totals array for calendar indicators
    - Category-wise spending breakdown across all 5 buckets
    """
    df = get_expenses_dataframe()
    month_prefix = f"{year:04d}-{month:02d}"

    if df.empty:
        month_df = pd.DataFrame(columns=COLUMNS)
    else:
        month_df = df[df["date"].str.startswith(month_prefix)]

    total_spending = round(float(month_df["amount"].sum()), 2) if not month_df.empty else 0.0

    # Daily totals array for calendar indicators: [{"date": "...", "total": ..., "count": ...}]
    daily_totals: List[Dict[str, Any]] = []
    if not month_df.empty:
        daily_grp = month_df.groupby("date")["amount"].agg(["sum", "count"]).reset_index()
        daily_grp = daily_grp.sort_values(by="date")
        for _, row in daily_grp.iterrows():
            daily_totals.append({
                "date": str(row["date"]),
                "total": round(float(row["sum"]), 2),
                "count": int(row["count"])
            })

    # Category breakdown across all 5 standard categories
    category_breakdown: Dict[str, float] = {cat: 0.0 for cat in VALID_CATEGORIES}
    category_percentages: Dict[str, float] = {cat: 0.0 for cat in VALID_CATEGORIES}

    if not month_df.empty:
        cat_grp = month_df.groupby("category")["amount"].sum()
        for cat in VALID_CATEGORIES:
            amt = float(cat_grp.get(cat, 0.0))
            category_breakdown[cat] = round(amt, 2)
            if total_spending > 0:
                category_percentages[cat] = round((amt / total_spending) * 100, 1)

    return {
        "year": year,
        "month": month,
        "month_label": datetime(year, month, 1).strftime("%B %Y"),
        "total_spending": total_spending,
        "transaction_count": len(month_df),
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
    df = get_expenses_dataframe()
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")

    if df.empty:
        window_df = pd.DataFrame(columns=COLUMNS)
    else:
        window_df = df[(df["date"] >= start_str) & (df["date"] <= end_str)]

    total_expense = round(float(window_df["amount"].sum()), 2) if not window_df.empty else 0.0
    
    # 90 calendar days in window
    total_days = 90
    daily_average = round(total_expense / total_days, 2) if total_days > 0 else 0.0

    # Category distribution
    category_distribution: Dict[str, float] = {cat: 0.0 for cat in VALID_CATEGORIES}
    category_percentages: Dict[str, float] = {cat: 0.0 for cat in VALID_CATEGORIES}

    if not window_df.empty:
        cat_grp = window_df.groupby("category")["amount"].sum()
        for cat in VALID_CATEGORIES:
            amt = float(cat_grp.get(cat, 0.0))
            category_distribution[cat] = round(amt, 2)
            if total_expense > 0:
                category_percentages[cat] = round((amt / total_expense) * 100, 1)

    # Monthly breakdown trend
    monthly_trend: List[Dict[str, Any]] = []
    if not window_df.empty:
        temp_df = window_df.copy()
        temp_df["year_month"] = temp_df["date"].str.slice(0, 7)
        m_grp = temp_df.groupby("year_month")["amount"].agg(["sum", "count"]).reset_index()
        m_grp = m_grp.sort_values(by="year_month")
        for _, row in m_grp.iterrows():
            monthly_trend.append({
                "month": str(row["year_month"]),
                "total": round(float(row["sum"]), 2),
                "count": int(row["count"])
            })

    return {
        "period": {
            "start_date": start_str,
            "end_date": end_str,
            "total_days": total_days
        },
        "total_expense": total_expense,
        "daily_average": daily_average,
        "transaction_count": len(window_df),
        "category_distribution": category_distribution,
        "category_percentages": category_percentages,
        "monthly_trend": monthly_trend
    }


def generate_export_file(format_type: str = "csv") -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Prepare file export in CSV or Excel format.
    Returns (file_path_or_buffer, filename, mimetype).
    """
    df = get_expenses_dataframe()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if format_type.lower() in ("excel", "xlsx"):
        export_file = DATA_DIR / f"expenses_export_{timestamp}.xlsx"
        try:
            # Use pandas ExcelWriter with openpyxl
            with pd.ExcelWriter(export_file, engine="openpyxl") as writer:
                df.to_excel(writer, sheet_name="Expenses", index=False)
                
                # Also include category summary sheet
                summary_data = []
                for cat in VALID_CATEGORIES:
                    amt = float(df[df["category"] == cat]["amount"].sum()) if not df.empty else 0.0
                    summary_data.append({"Category": cat, "Total Amount": round(amt, 2)})
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name="Category Summary", index=False)
            
            return str(export_file), f"expenses_{timestamp}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        except Exception:
            # If openpyxl is unavailable, fall back cleanly to CSV
            pass

    # Default to CSV export
    export_file = DATA_DIR / f"expenses_export_{timestamp}.csv"
    df.to_csv(export_file, index=False)
    return str(export_file), f"expenses_{timestamp}.csv", "text/csv"
