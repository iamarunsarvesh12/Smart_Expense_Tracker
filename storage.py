"""
Smart Home Expense Tracker - Storage Engine (Pure Python Standard Library)
Strictly zero Pandas / zero OpenPyXL - 100% Python 3.14+ compatible.
Features:
- Automated 50:20:20:10 Salary Budget Allocation Engine
- Categories mapped to 4 Smart Pillars: Needs (50%), Lifestyle (20%), Investments (20%), Emergency (10%)
- Date-Only Schema: id,date,category,item,amount,payment_mode,notes (No time field)
- Remaining Balances, 6-Month Emergency Buffer Tracking & Net Savings Analytics
- Strict 3-Month Rolling Retention Purge
- One-click Expense Deletion & Safe Reset
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

_file_lock = threading.Lock()

# Standard CSV Schema
COLUMNS = [
    "id",
    "date",
    "category",
    "item",
    "amount",
    "payment_mode",
    "notes"
]

# The Granular Expense Categories
VALID_CATEGORIES = [
    "Groceries",
    "Food",
    "Bills & Utilities",
    "Medical & Healthcare",
    "Bike & Car",
    "Stationery & Office",
    "General & Others",
    "Investments & SIP",
    "Emergency Fund"
]

# 50:20:20:10 Category Mapping
CATEGORY_BUCKETS = {
    "Groceries": "needs",
    "Food": "needs",
    "Bills & Utilities": "needs",
    "Medical & Healthcare": "needs",
    "Bike & Car": "lifestyle",
    "Stationery & Office": "lifestyle",
    "General & Others": "lifestyle",
    "Investments & SIP": "investments",
    "Emergency Fund": "emergency"
}

# Canonical lookup mapping for forgiving user input & legacy migration
CATEGORY_LOOKUP = {
    "food": "Food",
    "groceries": "Groceries",
    "grocery": "Groceries",
    "bike & car": "Bike & Car",
    "bike": "Bike & Car",
    "car": "Bike & Car",
    "petrol": "Bike & Car",
    "bills & utilities": "Bills & Utilities",
    "bills": "Bills & Utilities",
    "utilities": "Bills & Utilities",
    "eb": "Bills & Utilities",
    "stationery & office": "Stationery & Office",
    "stationery": "Stationery & Office",
    "office": "Stationery & Office",
    "medical & healthcare": "Medical & Healthcare",
    "medical": "Medical & Healthcare",
    "healthcare": "Medical & Healthcare",
    "general & others": "General & Others",
    "general": "General & Others",
    "others": "General & Others",
    "investments & sip": "Investments & SIP",
    "investments": "Investments & SIP",
    "sip": "Investments & SIP",
    "investment": "Investments & SIP",
    "mutual fund": "Investments & SIP",
    "emergency fund": "Emergency Fund",
    "emergency": "Emergency Fund",
    "buffer": "Emergency Fund",
    "food & groceries": "Food",
    "fuel & commute": "Bike & Car",
    "general & daily utilities": "Bills & Utilities"
}

DEFAULT_BUDGET = {
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
    },
    "categories": {
        "Groceries": 3500.0,
        "Food": 2500.0,
        "Bills & Utilities": 2500.0,
        "Medical & Healthcare": 1500.0,
        "Bike & Car": 2000.0,
        "Stationery & Office": 500.0,
        "General & Others": 1500.0,
        "Investments & SIP": 4000.0,
        "Emergency Fund": 2000.0
    }
}


def init_storage() -> None:
    """Initialize data directory, expenses CSV, and default 50:20:20:10 budget."""
    with _file_lock:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        if not EXPENSES_CSV.exists() or os.path.getsize(EXPENSES_CSV) == 0:
            with open(EXPENSES_CSV, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(COLUMNS)

        if not BUDGET_JSON.exists() or os.path.getsize(BUDGET_JSON) == 0:
            with open(BUDGET_JSON, mode="w", encoding="utf-8") as f:
                json.dump(DEFAULT_BUDGET, f, indent=2)


def get_budget_config() -> Dict[str, Any]:
    """Load budget configuration from data/budget_config.json with 50:20:20:10 rule."""
    with _file_lock:
        if not BUDGET_JSON.exists() or os.path.getsize(BUDGET_JSON) == 0:
            return DEFAULT_BUDGET.copy()

        try:
            with open(BUDGET_JSON, mode="r", encoding="utf-8") as f:
                config = json.load(f)

            monthly_income = float(config.get("monthly_income", DEFAULT_BUDGET["monthly_income"]))
            rule = config.get("rule_split", DEFAULT_BUDGET["rule_split"])
            needs_pct = float(rule.get("needs_pct", 50))
            lifestyle_pct = float(rule.get("lifestyle_pct", 20))
            investments_pct = float(rule.get("investments_pct", 20))
            emergency_pct = float(rule.get("emergency_pct", 10))

            needs_target = round(monthly_income * (needs_pct / 100.0), 2)
            lifestyle_target = round(monthly_income * (lifestyle_pct / 100.0), 2)
            investments_target = round(monthly_income * (investments_pct / 100.0), 2)
            emergency_target = round(monthly_income * (emergency_pct / 100.0), 2)
            target_months = int(config.get("emergency_target_months", 6))
            emergency_goal = round(needs_target * target_months, 2)

            categories = config.get("categories", {})
            sanitized_cats = {}
            for cat in VALID_CATEGORIES:
                val = categories.get(cat, DEFAULT_BUDGET["categories"].get(cat, 0.0))
                try:
                    sanitized_cats[cat] = round(float(val), 2)
                except (ValueError, TypeError):
                    sanitized_cats[cat] = 0.0

            return {
                "monthly_income": round(monthly_income, 2),
                "currency": "₹",
                "emergency_fund_accumulated": float(config.get("emergency_fund_accumulated", 36000.0)),
                "emergency_target_months": target_months,
                "rule_split": {
                    "needs_pct": needs_pct,
                    "lifestyle_pct": lifestyle_pct,
                    "investments_pct": investments_pct,
                    "emergency_pct": emergency_pct
                },
                "calculated_targets": {
                    "needs": needs_target,
                    "lifestyle": lifestyle_target,
                    "investments": investments_target,
                    "emergency": emergency_target,
                    "emergency_goal": emergency_goal
                },
                "category_mapping": CATEGORY_BUCKETS,
                "categories": sanitized_cats
            }
        except Exception:
            return DEFAULT_BUDGET.copy()


def save_budget_config(payload: Dict[str, Any]) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """Save monthly income and recompute 50:20:20:10 smart allocation targets."""
    if not isinstance(payload, dict):
        return False, "Budget payload must be a JSON object.", None

    raw_income = payload.get("monthly_income")
    if raw_income is None:
        raw_income = DEFAULT_BUDGET["monthly_income"]
    try:
        monthly_income = max(0.0, round(float(raw_income), 2))
    except (ValueError, TypeError):
        return False, "Monthly income must be a valid number.", None

    curr = get_budget_config()
    rule = payload.get("rule_split", curr.get("rule_split", DEFAULT_BUDGET["rule_split"]))
    needs_pct = float(rule.get("needs_pct", 50))
    lifestyle_pct = float(rule.get("lifestyle_pct", 20))
    investments_pct = float(rule.get("investments_pct", 20))
    emergency_pct = float(rule.get("emergency_pct", 10))

    needs_target = round(monthly_income * (needs_pct / 100.0), 2)
    lifestyle_target = round(monthly_income * (lifestyle_pct / 100.0), 2)
    investments_target = round(monthly_income * (investments_pct / 100.0), 2)
    emergency_target = round(monthly_income * (emergency_pct / 100.0), 2)

    target_months = int(payload.get("emergency_target_months", curr.get("emergency_target_months", 6)))
    emergency_goal = round(needs_target * target_months, 2)

    accumulated = float(payload.get("emergency_fund_accumulated", curr.get("emergency_fund_accumulated", 36000.0)))

    # Categories
    raw_categories = payload.get("categories", curr.get("categories", {}))
    sanitized_cats = {}
    for cat in VALID_CATEGORIES:
        val = raw_categories.get(cat, DEFAULT_BUDGET["categories"].get(cat, 0.0))
        try:
            sanitized_cats[cat] = round(float(val), 2)
        except (ValueError, TypeError):
            sanitized_cats[cat] = 0.0

    new_config = {
        "monthly_income": monthly_income,
        "currency": "₹",
        "emergency_fund_accumulated": accumulated,
        "emergency_target_months": target_months,
        "rule_split": {
            "needs_pct": needs_pct,
            "lifestyle_pct": lifestyle_pct,
            "investments_pct": investments_pct,
            "emergency_pct": emergency_pct
        },
        "calculated_targets": {
            "needs": needs_target,
            "lifestyle": lifestyle_target,
            "investments": investments_target,
            "emergency": emergency_target,
            "emergency_goal": emergency_goal
        },
        "category_mapping": CATEGORY_BUCKETS,
        "categories": sanitized_cats,
        "updated_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    }

    with _file_lock:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(BUDGET_JSON, mode="w", encoding="utf-8") as f:
            json.dump(new_config, f, indent=2)

    return True, None, new_config


def read_all_expenses() -> List[Dict[str, Any]]:
    """Read all expenses from CSV using standard csv.DictReader."""
    init_storage()
    records: List[Dict[str, Any]] = []
    with _file_lock:
        if not EXPENSES_CSV.exists():
            return records

        with open(EXPENSES_CSV, mode="r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    amt = float(row.get("amount", 0.0))
                except (ValueError, TypeError):
                    amt = 0.0

                raw_cat = row.get("category", "General & Others").strip()
                cat = CATEGORY_LOOKUP.get(raw_cat.lower(), raw_cat)
                if cat not in VALID_CATEGORIES:
                    cat = "General & Others"

                bucket = CATEGORY_BUCKETS.get(cat, "lifestyle")

                records.append({
                    "id": row.get("id", "").strip(),
                    "date": row.get("date", "").strip(),
                    "category": cat,
                    "item": row.get("item", "").strip(),
                    "amount": round(amt, 2),
                    "payment_mode": row.get("payment_mode", "UPI").strip(),
                    "notes": row.get("notes", "").strip(),
                    "bucket": bucket
                })
    return records


def add_expense(payload: Dict[str, Any]) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """Validate and append an expense record to expenses.csv."""
    init_storage()
    item = str(payload.get("item", "")).strip()
    if not item:
        return False, "Item description is required.", None

    try:
        amount = round(float(payload.get("amount", 0.0)), 2)
        if amount <= 0:
            return False, "Amount must be greater than zero.", None
    except (ValueError, TypeError):
        return False, "Amount must be a valid positive number.", None

    exp_date = str(payload.get("date", "")).strip() or datetime.now().strftime("%Y-%m-%d")
    raw_cat = str(payload.get("category", "General & Others")).strip()
    category = CATEGORY_LOOKUP.get(raw_cat.lower(), raw_cat)
    if category not in VALID_CATEGORIES:
        category = "General & Others"

    payment_mode = str(payload.get("payment_mode", "UPI")).strip() or "UPI"
    notes = str(payload.get("notes", "")).strip()
    expense_id = f"exp_{int(datetime.now().timestamp() * 1000)}"

    bucket = CATEGORY_BUCKETS.get(category, "lifestyle")
    record = {
        "id": expense_id,
        "date": exp_date,
        "category": category,
        "item": item,
        "amount": f"{amount:.2f}",
        "payment_mode": payment_mode,
        "notes": notes
    }

    with _file_lock:
        with open(EXPENSES_CSV, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=COLUMNS)
            writer.writerow(record)

    output = record.copy()
    output["amount"] = amount
    output["bucket"] = bucket
    return True, None, output


def delete_expense(expense_id: str) -> Tuple[bool, str]:
    """Delete an expense by unique ID."""
    with _file_lock:
        if not EXPENSES_CSV.exists():
            return False, "Expenses database file does not exist."

        all_records = []
        found = False
        with open(EXPENSES_CSV, mode="r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames or COLUMNS
            for row in reader:
                if row.get("id") == expense_id:
                    found = True
                else:
                    all_records.append(row)

        if not found:
            return False, f"Expense with ID '{expense_id}' not found."

        with open(EXPENSES_CSV, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_records)

        return True, f"Expense '{expense_id}' deleted successfully."


def get_expenses_by_date(date_str: Optional[str] = None, category_filter: Optional[str] = None) -> Dict[str, Any]:
    """Retrieve expenses filtered by date and/or category."""
    all_expenses = read_all_expenses()
    filtered = all_expenses
    if date_str:
        filtered = [e for e in filtered if e["date"] == date_str]
    if category_filter and category_filter != "all":
        filtered = [e for e in filtered if e["category"] == category_filter]

    filtered.sort(key=lambda x: (x["date"], x["id"]), reverse=True)
    return {
        "date": date_str,
        "count": len(filtered),
        "total_amount": round(sum(e["amount"] for e in filtered), 2),
        "expenses": filtered
    }


def get_monthly_summary(year: int, month: int) -> Dict[str, Any]:
    """
    Comprehensive 50:20:20:10 monthly metrics alongside category allocations:
    - 50% Household Needs
    - 20% Lifestyle & Wants
    - 20% Monthly Investments & SIP
    - 10% Emergency Fund (targeting 6 months of backup)
    """
    all_expenses = read_all_expenses()
    month_prefix = f"{year:04d}-{month:02d}"

    if month == 12:
        next_month_date = datetime(year + 1, 1, 1)
    else:
        next_month_date = datetime(year, month + 1, 1)
    days_in_month = (next_month_date - datetime(year, month, 1)).days

    month_expenses = [e for e in all_expenses if e["date"].startswith(month_prefix)]
    month_expenses.sort(key=lambda x: (x["date"], x["id"]), reverse=True)
    total_spending = round(sum(e["amount"] for e in month_expenses), 2)

    cfg = get_budget_config()
    monthly_income = cfg["monthly_income"]
    targets = cfg["calculated_targets"]
    needs_limit = targets["needs"]
    lifestyle_limit = targets["lifestyle"]
    investments_target = targets["investments"]
    emergency_target = targets["emergency"]
    emergency_goal = targets["emergency_goal"]
    accumulated_base = cfg.get("emergency_fund_accumulated", 36000.0)

    needs_spent = 0.0
    lifestyle_spent = 0.0
    investments_spent = 0.0
    emergency_allocated = 0.0

    category_summary = {cat: {"amount": 0.0, "count": 0, "bucket": b} for cat, b in CATEGORY_BUCKETS.items()}
    daily_spend = {}

    for exp in month_expenses:
        amt = exp["amount"]
        b = exp["bucket"]
        cat = exp["category"]
        d = exp["date"]

        if b == "needs":
            needs_spent += amt
        elif b == "lifestyle":
            lifestyle_spent += amt
        elif b == "investments":
            investments_spent += amt
        elif b == "emergency":
            emergency_allocated += amt

        if cat in category_summary:
            category_summary[cat]["amount"] += amt
            category_summary[cat]["count"] += 1
        else:
            category_summary[cat] = {"amount": amt, "count": 1, "bucket": b}

        daily_spend[d] = round(daily_spend.get(d, 0.0) + amt, 2)

    needs_spent = round(needs_spent, 2)
    lifestyle_spent = round(lifestyle_spent, 2)
    investments_spent = round(investments_spent, 2)
    emergency_allocated = round(emergency_allocated, 2)

    needs_pct = round((needs_spent / needs_limit * 100), 1) if needs_limit > 0 else 0.0
    needs_status = "danger" if needs_pct > 90.0 else ("warning" if needs_pct >= 75.0 else "normal")

    lifestyle_pct = round((lifestyle_spent / lifestyle_limit * 100), 1) if lifestyle_limit > 0 else 0.0
    lifestyle_status = "danger" if lifestyle_pct > 90.0 else ("warning" if lifestyle_pct >= 75.0 else "normal")

    investments_pct = round((investments_spent / investments_target * 100), 1) if investments_target > 0 else 0.0
    investments_status = "normal" if investments_pct >= 100.0 else "pending"

    emergency_pct = round((emergency_allocated / emergency_target * 100), 1) if emergency_target > 0 else 0.0
    emergency_status = "normal" if emergency_pct >= 100.0 else "pending"

    lifetime_emergency_added = sum(e["amount"] for e in all_expenses if e["bucket"] == "emergency")
    total_emergency_accumulated = round(accumulated_base + lifetime_emergency_added, 2)
    emergency_goal_pct = round((total_emergency_accumulated / emergency_goal * 100), 1) if emergency_goal > 0 else 0.0

    category_list = []
    for cat_name, info in category_summary.items():
        cat_amt = round(info["amount"], 2)
        pct_of_total = round((cat_amt / total_spending * 100), 1) if total_spending > 0 else 0.0
        category_list.append({
            "category": cat_name,
            "amount": cat_amt,
            "count": info["count"],
            "bucket": info["bucket"],
            "pct_of_total": pct_of_total
        })
    category_list.sort(key=lambda x: x["amount"], reverse=True)

    daily_totals = [{"date": d, "total": daily_spend[d], "count": 1} for d in sorted(daily_spend.keys())]

    return {
        "year": year,
        "month": month,
        "month_label": datetime(year, month, 1).strftime("%B %Y"),
        "days_in_month": days_in_month,
        "income": monthly_income,
        "currency": "₹",
        "total_spent": total_spending,
        "total_spending": total_spending,
        "net_remaining": round(monthly_income - total_spending, 2),
        "net_savings": round(monthly_income - total_spending, 2),
        "savings_rate": round(((monthly_income - total_spending) / monthly_income) * 100, 1) if monthly_income > 0 else 0.0,
        "daily_spending": daily_spend,
        "active_days": list(daily_spend.keys()),
        "daily_totals": daily_totals,
        "transaction_count": len(month_expenses),
        "pillars": {
            "needs": {
                "name": "Household Needs",
                "allocation_pct": cfg["rule_split"]["needs_pct"],
                "limit": needs_limit,
                "spent": needs_spent,
                "remaining": round(needs_limit - needs_spent, 2),
                "pct_used": needs_pct,
                "status": needs_status,
                "categories": ["Groceries", "Food", "Bills & Utilities", "Medical & Healthcare"]
            },
            "lifestyle": {
                "name": "Lifestyle & Wants",
                "allocation_pct": cfg["rule_split"]["lifestyle_pct"],
                "limit": lifestyle_limit,
                "spent": lifestyle_spent,
                "remaining": round(lifestyle_limit - lifestyle_spent, 2),
                "pct_used": lifestyle_pct,
                "status": lifestyle_status,
                "categories": ["Bike & Car", "Stationery & Office", "General & Others"]
            },
            "investments": {
                "name": "Monthly Investments",
                "allocation_pct": cfg["rule_split"]["investments_pct"],
                "target": investments_target,
                "allocated": investments_spent,
                "remaining_to_target": max(0.0, round(investments_target - investments_spent, 2)),
                "pct_achieved": investments_pct,
                "status": investments_status,
                "categories": ["Investments & SIP"]
            },
            "emergency": {
                "name": "Emergency Fund",
                "allocation_pct": cfg["rule_split"]["emergency_pct"],
                "target": emergency_target,
                "allocated": emergency_allocated,
                "remaining_to_target": max(0.0, round(emergency_target - emergency_allocated, 2)),
                "pct_achieved": emergency_pct,
                "status": emergency_status,
                "accumulated_total": total_emergency_accumulated,
                "goal_6_months": emergency_goal,
                "goal_progress_pct": min(100.0, emergency_goal_pct),
                "categories": ["Emergency Fund"]
            }
        },
        "category_summary": category_list,
        "category_breakdown": {c["category"]: c["amount"] for c in category_list},
        "recent_expenses": month_expenses[:30]
    }


def reset_database() -> Tuple[bool, str]:
    """Pristine reset of database files and restoration of 50:20:20:10 budget."""
    with _file_lock:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(EXPENSES_CSV, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(COLUMNS)

        with open(BUDGET_JSON, mode="w", encoding="utf-8") as f:
            json.dump(DEFAULT_BUDGET, f, indent=2)

        return True, "Database successfully reset to default state with 50:20:20:10 rule."
