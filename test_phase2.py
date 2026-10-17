"""
Test suite for Smart Home Expense Tracker - Phase 2 REST API & Storage Engine
"""

import json
from datetime import datetime, timedelta
from app import app
import storage

def run_tests():
    client = app.test_client()
    print("=== STARTING PHASE 2 AUTOMATED TEST SUITE ===")

    # Reset CSV for idempotent test run
    storage.EXPENSES_CSV.write_text("id,date,time,category,item,amount,payment_mode,notes\n", encoding="utf-8")
    if storage.ARCHIVE_CSV.exists():
        storage.ARCHIVE_CSV.unlink()

    # 1. Test Health Check
    res = client.get("/api/health")
    assert res.status_code == 200, f"Health check failed: {res.data}"
    health_data = res.get_json()
    assert health_data["status"] == "ok"
    print("[PASS] [1/8] /api/health passed.")

    # 2. Test Categories
    res = client.get("/api/categories")
    assert res.status_code == 200
    cat_data = res.get_json()
    assert len(cat_data["categories"]) == 5
    print("[PASS] [2/8] /api/categories passed (5 categories verified).")

    # 3. Test Invalid POST /api/expenses
    invalid_cases = [
        ({"date": "invalid-date", "category": "Food & Groceries", "item": "Milk", "amount": 50, "payment_mode": "UPI"}, "Invalid 'date' format"),
        ({"date": "2026-10-17", "category": "Luxury Items", "item": "Watch", "amount": 500, "payment_mode": "UPI"}, "Invalid category"),
        ({"date": "2026-10-17", "category": "Food & Groceries", "item": "Milk", "amount": -10, "payment_mode": "UPI"}, "positive number"),
        ({"date": "2026-10-17", "category": "Food & Groceries", "item": "", "amount": 10, "payment_mode": "UPI"}, "Field 'item' is required"),
        ({"date": "2026-10-17", "category": "Food & Groceries", "item": "Milk", "amount": 10, "payment_mode": ""}, "Field 'payment_mode' is required"),
    ]
    for payload, expected_error in invalid_cases:
        res = client.post("/api/expenses", data=json.dumps(payload), content_type="application/json")
        assert res.status_code == 400
        assert expected_error.lower() in res.get_json()["message"].lower(), f"Expected '{expected_error}' in '{res.get_json()}'"
    print("[PASS] [3/8] POST /api/expenses input validation tests passed (5 invalid cases tested).")

    # 4. Test Valid POST /api/expenses
    test_expenses = [
        {
            "date": "2026-10-17",
            "time": "08:30:00",
            "category": "Food & Groceries",
            "item": "Milk and Bread",
            "amount": 75.50,
            "payment_mode": "UPI",
            "notes": "Daily morning supplies"
        },
        {
            "date": "2026-10-17",
            "time": "12:15:00",
            "category": "Fuel & Commute",
            "item": "Petrol",
            "amount": 500.00,
            "payment_mode": "Credit Card",
            "notes": "Bike fuel"
        },
        {
            "date": "2026-10-16",
            "time": "18:00:00",
            "category": "Stationery & Office",
            "item": "Notebooks and Pens",
            "amount": 120.00,
            "payment_mode": "Cash",
            "notes": ""
        },
        {
            "date": "2026-09-10",
            "time": "10:00:00",
            "category": "Medical & Healthcare",
            "item": "Doctor consultation and pills",
            "amount": 800.00,
            "payment_mode": "UPI",
            "notes": "Routine checkup"
        },
        {
            "date": "2026-08-20",
            "time": "15:00:00",
            "category": "General & Daily Utilities",
            "item": "Electricity Bill",
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
    print("[PASS] [4/8] POST /api/expenses successfully created 5 test records across all categories.")

    # 5. Test GET /api/expenses with and without date filter
    res = client.get("/api/expenses?date=2026-10-17")
    assert res.status_code == 200
    date_data = res.get_json()
    assert date_data["count"] == 2
    assert date_data["daily_total"] == 575.50
    print("[PASS] [5/8] GET /api/expenses?date=2026-10-17 returned filtered records with daily total 575.50.")

    # 6. Test GET /api/summary/monthly
    res = client.get("/api/summary/monthly?year=2026&month=10")
    assert res.status_code == 200
    monthly_data = res.get_json()
    assert monthly_data["total_spending"] == 695.50
    assert len(monthly_data["daily_totals"]) == 2  # 16th and 17th
    assert "Food & Groceries" in monthly_data["category_breakdown"]
    assert monthly_data["category_breakdown"]["Food & Groceries"] == 75.50
    assert monthly_data["category_breakdown"]["Fuel & Commute"] == 500.00
    assert monthly_data["category_breakdown"]["Stationery & Office"] == 120.00
    print("[PASS] [6/8] GET /api/summary/monthly correctly aggregated total, daily array, and categories.")

    # 7. Test GET /api/summary/rolling-3-months
    res = client.get("/api/summary/rolling-3-months")
    assert res.status_code == 200
    rolling_data = res.get_json()
    assert rolling_data["total_expense"] == 2945.50
    assert rolling_data["daily_average"] > 0
    assert len(rolling_data["category_distribution"]) == 5
    print("[PASS] [7/8] GET /api/summary/rolling-3-months computed 90-day aggregate and distributions.")

    # 8. Test GET /api/export
    res = client.get("/api/export")
    assert res.status_code == 200
    assert b"id,date,time,category,item,amount,payment_mode,notes" in res.data
    print("[PASS] [8/8] GET /api/export successfully generated file download stream.")

    print("\nALL 8 TESTS PASSED WITH ZERO ERRORS!")

if __name__ == "__main__":
    run_tests()
