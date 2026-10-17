import voice_parser

test_cases = [
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
    ("Money given to friend 1000", "Given Friend", 1000.0, "General & Others"),
    ("Casual cash 150", "Casual", 150.0, "General & Others")
]

print("=== RUNNING 7-CATEGORY VOICE NLP PARSER UNIT TESTS ===")
for t, expected_item_keyword, expected_amt, expected_cat in test_cases:
    res = voice_parser.parse_voice_transcript(t)
    assert res["success"] is True, f"Failed for '{t}'"
    d = res["data"]
    print(f"Transcript: '{t}'")
    print(f"  Result -> Item: '{d['item']}', Amount: {d['amount']}, Cat: '{d['category']}', Mode: '{d['payment_mode']}', Date: {d['date']}")
    assert d["amount"] == expected_amt, f"Expected amount {expected_amt}, got {d['amount']}"
    assert d["category"] == expected_cat, f"Expected category '{expected_cat}', got '{d['category']}'"

print("\nALL 7-CATEGORY VOICE PARSER TEST CASES PASSED SUCCESSFULLY!")
