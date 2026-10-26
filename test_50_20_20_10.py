"""
Automated Verification Suite for Smart Home Expense Tracker (Smart_Expense_Tracker)
Verifies 50:20:20:10 engine, CSV schema preservation, Tanglish voice parsing, and Flask endpoints.
"""

import os
import sys
import json
import csv
from datetime import datetime

import app
import storage
import voice_parser
import email_service

def test_no_pandas_or_openpyxl():
    print("Checking Python modules to ensure no pandas or openpyxl...")
    assert "pandas" not in sys.modules, "STRICT ERROR: pandas must not be imported!"
    assert "openpyxl" not in sys.modules, "STRICT ERROR: openpyxl must not be imported!"
    print("  [OK] Pure Python standard library verified (No Pandas, No OpenPyXL).")

def test_csv_schema():
    print("Validating data/expenses.csv schema...")
    assert storage.EXPENSES_CSV.exists(), "expenses.csv missing!"
    with open(storage.EXPENSES_CSV, mode="r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        expected = ["id", "date", "category", "item", "amount", "payment_mode", "notes"]
        assert header == expected, f"Header mismatch: {header} vs {expected}"
    print("  [OK] Schema matches: id,date,category,item,amount,payment_mode,notes")

def test_budget_50_20_20_10_engine():
    print("Testing 50:20:20:10 Salary Budget Allocation Engine...")
    storage.save_budget_config({"monthly_income": 20000.0})
    cfg = storage.get_budget_config()
    income = cfg["monthly_income"]
    assert income == 20000.0, f"Expected default 20000, got {income}"

    targets = cfg["calculated_targets"]
    assert targets["needs"] == 10000.0, f"Needs 50% should be 10000, got {targets['needs']}"
    assert targets["lifestyle"] == 4000.0, f"Lifestyle 20% should be 4000, got {targets['lifestyle']}"
    assert targets["investments"] == 4000.0, f"Investments 20% should be 4000, got {targets['investments']}"
    assert targets["emergency"] == 2000.0, f"Emergency 10% should be 2000, got {targets['emergency']}"
    assert targets["emergency_goal"] == 60000.0, f"6-month goal should be 60000, got {targets['emergency_goal']}"
    print(f"  [OK] 50:20:20:10 Targets computed perfectly for income {income}: {targets}")

    # Test monthly metrics calculation
    metrics = storage.get_monthly_summary(2026, 10)
    pillars = metrics["pillars"]
    assert "needs" in pillars and "lifestyle" in pillars and "investments" in pillars and "emergency" in pillars
    print(f"  [OK] Pillars summary verified: Needs Spent: Rs.{pillars['needs']['spent']} ({pillars['needs']['pct_used']}%), Status: {pillars['needs']['status']}")
    print(f"  [OK] Lifestyle Spent: Rs.{pillars['lifestyle']['spent']} ({pillars['lifestyle']['pct_used']}%), Status: {pillars['lifestyle']['status']}")
    print(f"  [OK] Investments: Rs.{pillars['investments']['allocated']}/{pillars['investments']['target']}, Status: {pillars['investments']['status']}")
    print(f"  [OK] Emergency: Rs.{pillars['emergency']['allocated']}/{pillars['emergency']['target']}, Accumulated: Rs.{pillars['emergency']['accumulated_total']}/{pillars['emergency']['goal_6_months']}")

def test_tanglish_voice_parsing():
    print("Testing Tanglish voice recognition parser...")
    
    # Test Case 1: Bike petrol
    p1 = voice_parser.parse_voice_text("Iniku petrol 300 rupees bike upi potten")
    assert p1["category"] == "Bike & Car", f"Expected Bike & Car, got {p1['category']}"
    assert p1["amount"] == 300.0, f"Expected 300.0, got {p1['amount']}"
    assert p1["payment_mode"] == "UPI"
    print(f"  [OK] Parsed petrol: {p1['item']} | Rs.{p1['amount']} | {p1['category']} | {p1['payment_mode']}")

    # Test Case 2: Groceries
    p2 = voice_parser.parse_voice_text("Maligai groceries 1450 cash vanginen")
    assert p2["category"] == "Groceries", f"Expected Groceries, got {p2['category']}"
    assert p2["amount"] == 1450.0, f"Expected 1450.0, got {p2['amount']}"
    assert p2["payment_mode"] == "Cash"
    print(f"  [OK] Parsed groceries: {p2['item']} | Rs.{p2['amount']} | {p2['category']} | {p2['payment_mode']}")

    # Test Case 3: Food Swiggy
    p3 = voice_parser.parse_voice_text("Swiggy food dinner 480 card")
    assert p3["category"] == "Food", f"Expected Food, got {p3['category']}"
    assert p3["amount"] == 480.0
    print(f"  [OK] Parsed food: {p3['item']} | Rs.{p3['amount']} | {p3['category']} | {p3['payment_mode']}")

    # Test Case 4: EB Bill
    p4 = voice_parser.parse_voice_text("TNEB current bill 750 upi")
    assert p4["category"] == "Bills & Utilities"
    assert p4["amount"] == 750.0
    print(f"  [OK] Parsed bill: {p4['item']} | Rs.{p4['amount']} | {p4['category']} | {p4['payment_mode']}")

    # Test Case 5: Investment SIP
    p5 = voice_parser.parse_voice_text("SIP mutual fund investment 2500 net banking")
    assert p5["category"] == "Investments & SIP"
    assert p5["amount"] == 2500.0
    print(f"  [OK] Parsed SIP: {p5['item']} | Rs.{p5['amount']} | {p5['category']} | {p5['payment_mode']}")

def test_flask_endpoints():
    print("Testing Flask REST endpoints via test client...")
    client = app.app.test_client()

    # 1. GET /
    res = client.get("/")
    assert res.status_code == 200, f"GET / returned {res.status_code}"
    assert b"Smart Home Expense" in res.data
    assert b"50:20:20:10" in res.data
    print("  [OK] GET / rendered successfully.")

    # 2. GET /api/budget
    res = client.get("/api/budget")
    assert res.status_code == 200
    b_data = res.get_json()
    assert b_data["monthly_income"] == 20000.0
    print("  [OK] GET /api/budget returned valid config.")

    # 3. POST /api/budget (Update income to 30000)
    res = client.post("/api/budget", json={"monthly_income": 30000.0})
    assert res.status_code == 200
    updated_b = res.get_json()["config"]
    assert updated_b["calculated_targets"]["needs"] == 15000.0  # 50%
    assert updated_b["calculated_targets"]["lifestyle"] == 6000.0 # 20%
    assert updated_b["calculated_targets"]["investments"] == 6000.0 # 20%
    assert updated_b["calculated_targets"]["emergency"] == 3000.0 # 10%
    print("  [OK] POST /api/budget correctly recomputed 50:20:20:10 for Rs.30,000.")

    # Reset back to 20000
    client.post("/api/budget", json={"monthly_income": 20000.0})

    # 4. GET /api/summary/monthly
    res = client.get("/api/summary/monthly?month=2026-10")
    assert res.status_code == 200
    s_data = res.get_json()["data"]
    assert s_data["month"] == 10
    assert s_data["transaction_count"] > 0
    print(f"  [OK] GET /api/summary/monthly returned {s_data['transaction_count']} expenses for 2026-10.")

    # 5. POST /api/expenses (Add new test expense)
    test_exp = {
        "date": "2026-10-26",
        "category": "Food",
        "item": "Filter Coffee & Snacks",
        "amount": 85.0,
        "payment_mode": "UPI",
        "notes": "Evening break"
    }
    res = client.post("/api/expenses", json=test_exp)
    assert res.status_code == 201
    created = res.get_json()["expense"]
    created_id = created["id"]
    print(f"  [OK] POST /api/expenses created expense ID: {created_id}")

    # 6. DELETE /api/expenses/<id>
    del_res = client.delete(f"/api/expenses/{created_id}")
    assert del_res.status_code == 200
    print(f"  [OK] DELETE /api/expenses/{created_id} succeeded.")

    # 7. POST /api/voice-parse
    vp_res = client.post("/api/voice-parse", json={"transcript": "Apollo pharmacy tablet 250 cash"})
    assert vp_res.status_code == 200
    vp_data = vp_res.get_json()["parsed"]
    assert vp_data["category"] == "Medical & Healthcare"
    assert vp_data["amount"] == 250.0
    print("  [OK] POST /api/voice-parse returned structured output.")

    # 8. POST /api/email-report
    email_res = client.post("/api/email-report?month=2026-10")
    assert email_res.status_code == 200
    e_json = email_res.get_json()
    assert e_json["recipient"] == "sarveshsantosh2007s@gmail.com"
    print(f"  [OK] POST /api/email-report dispatched to {e_json['recipient']}.")

if __name__ == "__main__":
    print("==================================================")
    print("STARTING TEST SUITE: SMART EXPENSE TRACKER")
    print("==================================================")
    test_no_pandas_or_openpyxl()
    test_csv_schema()
    test_budget_50_20_20_10_engine()
    test_tanglish_voice_parsing()
    test_flask_endpoints()
    print("==================================================")
    print("ALL TESTS PASSED WITH 100% SUCCESS!")
    print("==================================================")
