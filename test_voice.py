import voice_parser

test_cases = [
    ("Paal vanginen 30 rupees", "Paal", 30.0, "Food & Groceries"),
    ("Milk 30", "Milk", 30.0, "Food & Groceries"),
    ("Petrol 200 potten", "Petrol", 200.0, "Fuel & Commute"),
    ("Printout 50 rupees", "Printout", 50.0, "Stationery & Office"),
    ("Xerox 40", "Xerox", 40.0, "Stationery & Office"),
    ("Tablet 150 rooba", "Tablet", 150.0, "Medical & Healthcare"),
    ("Doctor fees 300", "Doctor Fees", 300.0, "Medical & Healthcare"),
    ("Recharge paninen 299", "Recharge", 299.0, "General & Daily Utilities"),
    ("Nethu vegetables 250 gpay paninen", "Vegetables", 250.0, "Food & Groceries")
]

print("=== RUNNING VOICE NLP PARSER UNIT TESTS ===")
for t, expected_item, expected_amt, expected_cat in test_cases:
    res = voice_parser.parse_voice_transcript(t)
    assert res["success"] is True, f"Failed for '{t}'"
    d = res["data"]
    print(f"Transcript: '{t}'")
    print(f"  Result -> Item: '{d['item']}', Amount: {d['amount']}, Cat: '{d['category']}', Mode: '{d['payment_mode']}', Date: {d['date']}")
    assert d["amount"] == expected_amt, f"Expected amount {expected_amt}, got {d['amount']}"
    assert d["category"] == expected_cat, f"Expected cat {expected_cat}, got {d['category']}"

print("\nALL VOICE PARSER TEST CASES PASSED SUCCESSFULLY!")
