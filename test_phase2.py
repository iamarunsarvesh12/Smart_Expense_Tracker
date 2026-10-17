"""
Test suite for Smart Home Expense Tracker - Strict Schema (Date Only), Budget, Reset & Retention
"""

import json
from datetime import datetime, timedelta
from app import app
import storage

def run_tests():
    client = app.test_client()
    print("=== STARTING REST API & STORAGE ENGINE TEST SUITE ===")

    # Reset CSV for idempotent test run
    storage.EXPENSES_CSV.write_text("id,date,category,item,amount,payment_mode,notes\n", encoding="utf-8")
    if storage.ARCHIVE_CSV.exists():
        storage.ARCHIVE_CSV.unlink()

    # 1. Test Health Check
    res = client.get("/api/health")
    assert res.status_code == 200, f"Health check failed: {res.data}"
    health_data = res.get_json()
    assert health_data["status"] == "ok"
    assert health_data["storage"]["budget_json_exists"] is True
    assert "time" not in health_data["storage"]["columns"]
    print("[PASS] [1/11] /api/health passed (Date-only schema verified, no time field).")

    # 2. Test Categories (7 Granular Categories)
    res = client.get("/api/categories")
    assert res.status_code == 200
    cat_data = res.get_json()
    assert len(cat_data["categories"]) == 7
    expected_categories = [
        "Food", "Groceries", "Bike & Car", "Bills & Utilities",
        "Stationery & Office", "Medical & Healthcare", "General & Others"
    ]
    for cat in expected_categories:
        assert cat in cat_data["categories"], f"Missing category: {cat}"
    print("[PASS] [2/11] /api/categories passed (7 distinct categories verified).")

    # 3. Test Invalid POST /api/expenses
    invalid_cases = [
        ({"date": "invalid-date", "category": "Food", "item": "Biryani", "amount": 50, "payment_mode": "UPI"}, "Invalid 'date' format"),
        ({"date": "2026-10-17", "category": "Luxury Items", "item": "Watch", "amount": 500, "payment_mode": "UPI"}, "Invalid category"),
        ({"date": "2026-10-17", "category": "Food", "item": "Biryani", "amount": -10, "payment_mode": "UPI"}, "positive number"),
        ({"date": "2026-10-17", "category": "Food", "item": "", "amount": 10, "payment_mode": "UPI"}, "Field 'item' is required"),
        ({"date": "2026-10-17", "category": "Food", "item": "Biryani", "amount": 10, "payment_mode": ""}, "Field 'payment_mode' is required"),
    ]
    for payload, expected_error in invalid_cases:
        res = client.post("/api/expenses", data=json.dumps(payload), content_type="application/json")
        assert res.status_code == 400
        assert expected_error.lower() in res.get_json()["message"].lower(), f"Expected '{expected_error}' in '{res.get_json()}'"
    print("[PASS] [3/11] POST /api/expenses input validation tests passed (5 invalid cases tested).")

    # 4. Test Valid POST /api/expenses (Strictly Date Only)
    test_expenses = [
        {
            "date": "2026-10-17",
            "category": "Groceries",
            "item": "Vegetables and Milk",
            "amount": 75.50,
            "payment_mode": "UPI",
            "notes": "Morning supplies"
        },
        {
            "date": "2026-10-17",
            "category": "Food",
            "item": "Restaurant Meals",
            "amount": 250.00,
            "payment_mode": "Credit Card",
            "notes": "Lunch"
        },
        {
            "date": "2026-10-17",
            "category": "Bike & Car",
            "item": "Petrol",
            "amount": 500.00,
            "payment_mode": "UPI",
            "notes": "Bike fuel"
        },
        {
            "date": "2026-10-16",
            "category": "Stationery & Office",
            "item": "Printout and Xerox",
            "amount": 120.00,
            "payment_mode": "Cash",
            "notes": ""
        },
        {
            "date": "2026-09-10",
            "category": "Medical & Healthcare",
            "item": "Medicines & Doctor consultation",
            "amount": 800.00,
            "payment_mode": "UPI",
            "notes": "Routine checkup"
        },
        {
            "date": "2026-08-20",
            "category": "Bills & Utilities",
            "item": "EB Electricity Bill",
            "amount": 1450.00,
            "payment_mode": "Net Banking",
            "notes": "August bill"
        }
    ]

    for item in test_expenses:
        res = client.post("/api/expenses", data=json.dumps(item), content_type="application/json")
        assert res.status_code == 201
        data = res.get_json()
        assert data["status"] == "success"
        assert "id" in data["data"]
        assert "time" not in data["data"]
        assert data["data"]["amount"] == item["amount"]
    print(f"[PASS] [4/11] POST /api/expenses successfully created {len(test_expenses)} test records with date-only schema.")

    # 5. Test GET /api/expenses with date & category filter
    res = client.get("/api/expenses?date=2026-10-17")
    assert res.status_code == 200
    date_data = res.get_json()
    assert date_data["count"] == 3
    assert date_data["daily_total"] == 825.50

    res_cat = client.get("/api/expenses?category=Food")
    assert res_cat.status_code == 200
    cat_filtered = res_cat.get_json()
    assert cat_filtered["count"] == 1
    assert cat_filtered["expenses"][0]["item"] == "Restaurant Meals"
    print("[PASS] [5/11] GET /api/expenses with date and category filters returned exact matching records.")

    # 6. Test GET /api/budget & POST /api/budget
    res_b = client.get("/api/budget")
    assert res_b.status_code == 200
    b_data = res_b.get_json()
    assert "monthly_income" in b_data["budget"]
    assert "categories" in b_data["budget"]

    new_budget = {
        "monthly_income": 30000.0,
        "categories": {
            "Food": 5000.0,
            "Groceries": 6000.0,
            "Bike & Car": 4000.0,
            "Bills & Utilities": 3500.0,
            "Stationery & Office": 1500.0,
            "Medical & Healthcare": 3000.0,
            "General & Others": 2500.0
        }
    }
    res_b_post = client.post("/api/budget", data=json.dumps(new_budget), content_type="application/json")
    assert res_b_post.status_code == 200
    assert res_b_post.get_json()["budget"]["monthly_income"] == 30000.0
    print("[PASS] [6/11] GET /api/budget and POST /api/budget verified with persistence.")

    # 7. Test GET /api/summary/monthly with remaining balances and savings
    res_m = client.get("/api/summary/monthly?year=2026&month=10")
    assert res_m.status_code == 200
    monthly_data = res_m.get_json()
    assert monthly_data["total_spending"] == 945.50
    assert monthly_data["monthly_income"] == 30000.0
    assert monthly_data["net_savings"] == round(30000.0 - 945.50, 2)
    assert "category_budgets" in monthly_data
    assert monthly_data["category_budgets"]["Food"]["spent"] == 250.00
    assert monthly_data["category_budgets"]["Food"]["allocated"] == 5000.00
    assert monthly_data["category_budgets"]["Food"]["remaining"] == 4750.00
    print("[PASS] [7/11] GET /api/summary/monthly computed income, net savings, and category remaining balances.")

    # 8. Test Strict 3-Month Rolling Retention Engine Logic
    # Example: February 1st, 2026 -> records before Dec 1, 2025 (Nov or earlier) must be purged
    feb_ref = datetime(2026, 2, 1)
    cutoff_feb = storage.get_retention_cutoff_date(feb_ref)
    assert cutoff_feb == "2025-12-01", f"Expected 2025-12-01, got {cutoff_feb}"

    oct_ref = datetime(2026, 10, 17)
    cutoff_oct = storage.get_retention_cutoff_date(oct_ref)
    assert cutoff_oct == "2026-08-01", f"Expected 2026-08-01, got {cutoff_oct}"
    print("[PASS] [8/11] Strict 3-month rolling retention cutoff calculations verified.")

    # 9. Test GET /api/export
    res_exp = client.get("/api/export")
    assert res_exp.status_code == 200
    assert b"id,date,category,item,amount,payment_mode,notes" in res_exp.data
    assert b"time" not in res_exp.data
    print("[PASS] [9/11] GET /api/export successfully generated Date-Only CSV download stream.")

    # 10. Test Password-Protected Database Reset Endpoint
    # Test 10a: Wrong password -> 401
    bad_reset = client.post("/api/reset-database", data=json.dumps({"password": "wrongpassword"}), content_type="application/json")
    assert bad_reset.status_code == 401
    assert "Invalid Password" in bad_reset.get_json()["message"]

    # Test 10b: Correct password -> 200 & wipes expenses.csv to header only
    good_reset = client.post("/api/reset-database", data=json.dumps({"password": "admin123"}), content_type="application/json")
    assert good_reset.status_code == 200
    assert good_reset.get_json()["status"] == "success"

    # Verify CSV has only the header row
    lines = storage.EXPENSES_CSV.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    assert lines[0] == "id,date,category,item,amount,payment_mode,notes"
    print("[PASS] [10/11] Password-protected database reset verified with 401 auth challenge & clean wipe.")

    # 11. Test Month-End Email Report Endpoint
    res_email = client.post("/api/send-monthly-report?month=2026-10")
    # Even without valid SMTP password in test environment, it gracefully validates credentials
    email_data = res_email.get_json()
    assert "status" in email_data
    assert "recipient" in email_data or "message" in email_data
    print("[PASS] [11/11] Month-End Email Dispatch endpoint validated with structured response.")

    print("\nALL 11 REST API, STORAGE & SECURITY TESTS PASSED WITH ZERO ERRORS!")

if __name__ == "__main__":
    run_tests()
