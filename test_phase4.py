"""
Phase 4 Automated Verification Suite
Tests AI Voice Assistant natural language parser, endpoints, and frontend bindings across all 7 categories.
"""

import json
from datetime import datetime, timedelta
from app import app
import storage

def run_phase4_tests():
    client = app.test_client()
    print("=== STARTING 7-CATEGORY VOICE NLP AUTOMATED TEST SUITE ===")

    # 1. Test POST /api/parse-voice with all specified Tanglish & English patterns across the 7 categories
    voice_cases = [
        ("Paal vanginen 30 rupees", "Paal", 30.0, "Groceries"),
        ("Milk 30", "Milk", 30.0, "Groceries"),
        ("Tea 15 rupees", "Tea", 15.0, "Food"),
        ("Swiggy biryani 350", "Swiggy Biryani", 350.0, "Food"),
        ("Petrol 200 potten", "Petrol", 200.0, "Bike & Car"),
        ("Puncture 50", "Puncture", 50.0, "Bike & Car"),
        ("EB bill 1450", "Eb Bill", 1450.0, "Bills & Utilities"),
        ("Recharge paninen 299", "Recharge", 299.0, "Bills & Utilities"),
        ("Printout 50 rupees", "Printout", 50.0, "Stationery & Office"),
        ("Xerox 40", "Xerox", 40.0, "Stationery & Office"),
        ("Tablet 150 rooba", "Tablet", 150.0, "Medical & Healthcare"),
        ("Doctor fees 300", "Doctor Fees", 300.0, "Medical & Healthcare"),
        ("Money given to friend 1000", "Money Given Friend", 1000.0, "General & Others"),
        ("Casual cash 150", "Casual", 150.0, "General & Others")
    ]

    for phrase, expected_item, expected_amt, expected_cat in voice_cases:
        res = client.post(
            "/api/parse-voice",
            data=json.dumps({"text": phrase}),
            content_type="application/json"
        )
        assert res.status_code == 200, f"Parse failed for '{phrase}': {res.data}"
        body = res.get_json()
        assert body["status"] == "success"
        data = body["data"]
        assert data["amount"] == expected_amt, f"Expected {expected_amt}, got {data['amount']} in '{phrase}'"
        assert data["category"] == expected_cat, f"Expected {expected_cat}, got {data['category']} in '{phrase}'"
        assert expected_item.lower() in data["item"].lower(), f"Expected '{expected_item}' in '{data['item']}'"
    print(f"[PASS] [1/4] POST /api/parse-voice correctly parsed all {len(voice_cases)} test phrases into the 7 categories.")

    # 2. Test relative date parsing (yesterday / nethu)
    res = client.post(
        "/api/parse-voice",
        data=json.dumps({"text": "Nethu vegetables 120 rooba gpay"}),
        content_type="application/json"
    )
    assert res.status_code == 200
    yesterday_str = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    data = res.get_json()["data"]
    assert data["date"] == yesterday_str
    assert data["amount"] == 120.0
    assert data["category"] == "Groceries"
    assert data["payment_mode"] == "UPI"
    print("[PASS] [2/4] Relative date ('nethu'), Groceries category, and payment mode ('gpay') correctly extracted.")

    # 3. Test Full Confirmation Flow (Parse -> Confirm & Save to expenses.csv)
    parse_res = client.post(
        "/api/parse-voice",
        data=json.dumps({"text": "Petrol 500 potten card"}),
        content_type="application/json"
    )
    parsed_payload = parse_res.get_json()["data"]
    
    save_res = client.post(
        "/api/expenses",
        data=json.dumps(parsed_payload),
        content_type="application/json"
    )
    assert save_res.status_code == 201
    created_id = save_res.get_json()["data"]["id"]
    print(f"[PASS] [3/4] Parsed voice entity confirmed and committed to storage with ID: {created_id}.")

    # 4. Verify Frontend Voice UI Bindings
    html_res = client.get("/")
    assert html_res.status_code == 200
    html = html_res.data.decode("utf-8")
    
    required_ui_elements = [
        "btn-voice-header",
        "btn-voice-fab",
        "voice-listening-overlay",
        "voice-live-transcript",
        "modal-voice-confirm",
        "form-voice-confirm",
        "voice-original-text",
        "voice-input-category",
        "voice-input-item",
        "voice-input-amount",
        "btn-stop-voice",
        "btn-cancel-voice"
    ]
    for el in required_ui_elements:
        assert el in html, f"Missing voice UI element ID '{el}' in index.html"

    print("[PASS] [4/4] All Phase 4 Frontend Voice UI elements verified in template.")
    print("\nALL 7-CATEGORY VOICE TESTS COMPLETED WITH ZERO ERRORS!")

if __name__ == "__main__":
    run_phase4_tests()
