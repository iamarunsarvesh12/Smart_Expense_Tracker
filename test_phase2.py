"""
Test suite for Smart Home Expense Tracker - 7-Category REST API & Storage Engine
"""

import json
from datetime import datetime, timedelta
from app import app
import storage

def run_tests():
    client = app.test_client()
    print("=== STARTING 7-CATEGORY REST API TEST SUITE ===")

    # Reset CSV for idempotent test run
    storage.EXPENSES_CSV.write_text("id,date,time,category,item,amount,payment_mode,notes\n", encoding="utf-8")
    if storage.ARCHIVE_CSV.exists():
        storage.ARCHIVE_CSV.unlink()

    # 1. Test Health Check
    res = client.get("/api/health")
    assert res.status_code == 200, f"Health check failed: {res.data}"
    health_data = res.get_json()
    assert health_data["status"] == "ok"
    assert health_data["storage"]["budget_json_exists"] is True
    print("[PASS] [1/9] /api/health passed.")

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
    print("[PASS] [2/9] /api/categories passed (7 distinct categories verified).")

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
    print("[PASS] [3/9] POST /api/expenses input validation tests passed (5 invalid cases tested).")

    # 4. Test Valid POST /api/expenses
    test_expenses = [
        {
            "date": "2026-10-17",
            "time": "08:30:00",
            "category": "Groceries",
            "item": "Vegetables and Milk",
            "amount": 75.50,
            "payment_mode": "UPI",
            "notes": "Morning supplies"
        },
        {
            "date": "2026-10-17",
            "time": "12:15:00",
            "category": "Food",
            "item": "Restaurant Meals",
            "amount": 250.00,
            "payment_mode": "Credit Card",
            "notes": "Lunch"
        },
        {
            "date": "2026-10-17",
            "time": "14:00:00",
            "category": "Bike & Car",
            "item": "Petrol",
            "amount": 500.00,
            "payment_mode": "UPI",
            "notes": "Bike fuel"
        },
        {
            "date": "2026-10-16",
            "time": "18:00:00",
            "category": "Stationery & Office",
            "item": "Printout and Xerox",
            "amount": 120.00,
            "payment_mode": "Cash",
            "notes": ""
        },
        {
            "date": "2026-09-10",
            "time": "10:00:00",
            "category": "Medical & Healthcare",
            "item": "Medicines & Doctor consultation",
            "amount": 800.00,
            "payment_mode": "UPI",
            "notes": "Routine checkup"
        },
        {
            "date": "2026-08-20",
            "time": "15:00:00",
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
        assert data["data"]["amount"] == item["amount"]
    print(f"[PASS] [4/9] POST /api/expenses successfully created {len(test_expenses)} test records across categories.")

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
    print("[PASS] [5/9] GET /api/expenses with date and category filters returned exact matching records.")

    # 6. Test GET /api/budget & POST /api/budget
    res_b = client.get("/api/budget")
    assert res_b.status_code == 200
    b_data = res_b.get_json()
    assert "monthly_income" in b_data["budget"]
    assert "categories" in b_data["budget"]

    # Update budget
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
    print("[PASS] [6/9] GET /api/budget and POST /api/budget verified with persistence.")

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
    assert monthly_data["category_budgets"]["Food"]["is_over"] is False
    print("[PASS] [7/9] GET /api/summary/monthly computed income, net savings, and category remaining balances.")

    # 8. Test GET /api/summary/rolling-3-months
    res_r = client.get("/api/summary/rolling-3-months")
    assert res_r.status_code == 200
    rolling_data = res_r.get_json()
    assert rolling_data["total_expense"] == 3195.50
    assert rolling_data["daily_average"] > 0
    assert len(rolling_data["category_distribution"]) == 7
    print("[PASS] [8/9] GET /api/summary/rolling-3-months computed 90-day aggregate across all 7 categories.")

    # 9. Test GET /api/export
    res_exp = client.get("/api/export")
    assert res_exp.status_code == 200
    assert b"id,date,time,category,item,amount,payment_mode,notes" in res_exp.data
    print("[PASS] [9/9] GET /api/export successfully generated CSV download stream.")

    print("\nALL 9 REST API & STORAGE TESTS PASSED WITH ZERO ERRORS!")

if __name__ == "__main__":
    run_tests()
