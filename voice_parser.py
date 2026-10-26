"""
Smart Home Expense Tracker - Voice & Natural Language Parser
Extracts amount, category, item, payment mode, and date from spoken Tanglish/English text.
Calibrated for the 50:20:20:10 Granular Expense Categories.
"""

import re
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

import storage

CATEGORY_KEYWORDS = {
    "Food": [
        "food", "hotel", "restaurant", "swiggy", "zomato", "tea", "chai", "coffee",
        "kaapi", "snacks", "tiffin", "breakfast", "lunch", "dinner", "biryani",
        "briyani", "fast food", "bakery", "cake", "pizza", "burger", "samosa",
        "juice", "cool drinks", "mess", "shawarma", "noodles", "parotta", "biscuit",
        "biscuits", "ice cream", "sweet", "sweets", "meals", "sapadu"
    ],
    "Groceries": [
        "grocery", "groceries", "provisions", "maligai", "supermarket", "vegetable",
        "vegetables", "veggies", "kaygari", "kaaikari", "thakkali", "tomato", "onion",
        "vengayam", "potato", "urulaikizhangu", "fruits", "fruit", "pazham", "milk",
        "paal", "pal", "curd", "thayir", "butter", "paneer", "rice", "saadham", "arisi",
        "oil", "ennai", "egg", "eggs", "muttai", "chicken", "mutton", "fish", "meen",
        "dal", "paruppu", "masala", "salt", "uppu", "sugar", "sarkkarai", "bread"
    ],
    "Bike & Car": [
        "petrol", "diesel", "fuel", "bike", "car", "auto", "ola", "uber", "rapido",
        "bus", "train", "metro", "ticket", "fare", "toll", "parking", "service",
        "mechanic", "puncture", "tyre", "tire", "air", "helmet", "oil change",
        "spare parts", "taxi", "cab", "scooter", "commute", "travel", "chain lube"
    ],
    "Bills & Utilities": [
        "electricity", "current bill", "eb bill", "eb", "power", "water bill", "water",
        "gas", "cylinder", "lpg", "bharat gas", "indane", "hp gas", "wifi", "internet",
        "broadband", "airtel", "jio", "vi", "bsnl", "recharge", "mobile recharge",
        "phone bill", "dth", "tata sky", "sun direct", "cable", "maintenance",
        "house rent", "room rent", "rent", "maid", "newspaper", "utility", "tneb"
    ],
    "Stationery & Office": [
        "stationery", "stationery items", "pen", "pencil", "notebook", "note", "book",
        "books", "paper", "a4 sheet", "xerox", "photocopy", "printout", "print",
        "file", "folder", "envelope", "eraser", "sharpener", "scale", "ruler",
        "stapler", "pins", "marker", "highlighter", "glue", "fevicol", "tape",
        "office supplies", "calculator", "diary", "courier", "postage"
    ],
    "Medical & Healthcare": [
        "medical", "medicine", "medicines", "tablet", "tablets", "syrup", "capsule",
        "marunthu", "doctor", "consultation", "hospital", "clinic", "pharmacy",
        "medical shop", "apollo", "medplus", "injection", "test", "blood test",
        "scan", "x-ray", "bandage", "ointment", "dettol", "cotton", "thermometer",
        "drops", "eye drops", "pain balm", "healthcare"
    ],
    "General & Others": [
        "movie", "cinema", "theatre", "shopping", "dress", "clothes", "shirt",
        "pant", "t-shirt", "saree", "shoes", "slippers", "chappal", "haircut",
        "salon", "parlour", "spa", "cosmetics", "creams", "powder", "perfume",
        "gift", "gifts", "recharge", "electronics", "gadget", "charger", "cable",
        "earphones", "headphones", "cover", "repair", "temple", "donation", "tips",
        "entertainment", "general", "others", "miscellaneous"
    ],
    "Investments & SIP": [
        "sip", "mutual fund", "investment", "invest", "shares", "stock", "stocks",
        "gold", "etf", "fd", "rd", "fixed deposit", "zerodha", "groww", "nifty"
    ],
    "Emergency Fund": [
        "emergency", "buffer", "emergency fund", "backup fund", "emergency reserve", "contingency"
    ]
}


def parse_voice_text(text: str) -> Dict[str, Any]:
    """Parse Tanglish speech transcript into structured expense fields."""
    raw = text.strip()
    lower = raw.lower()

    # 1. Extract Amount
    amount = 0.0
    amt_match = re.search(r'(?:₹|rs\.?|rupees|rooba|rubai|inr)?\s*(\d+(?:\.\d{1,2})?)\s*(k|thousand|₹|rs\.?|rupees|rooba|rubai)?', lower)
    if amt_match:
        try:
            val = float(amt_match.group(1))
            unit = (amt_match.group(2) or '').lower()
            if unit in ['k', 'thousand'] or re.search(rf'{int(val)}k', lower):
                val *= 1000
            amount = round(val, 2)
        except ValueError:
            amount = 0.0

    # 2. Extract Category
    matched_cat = "General & Others"
    matched_keyword = ""
    for cat, kw_list in CATEGORY_KEYWORDS.items():
        for kw in kw_list:
            if re.search(rf'\b{re.escape(kw)}\b', lower):
                matched_cat = cat
                matched_keyword = kw
                break
        if matched_keyword:
            break

    # 3. Extract Payment Mode
    payment_mode = "UPI"
    if any(k in lower for k in ["cash", "panam", "kaasu", "hand"]):
        payment_mode = "Cash"
    elif any(k in lower for k in ["credit card", "credit", "cc"]):
        payment_mode = "Credit Card"
    elif any(k in lower for k in ["debit card", "debit", "dc"]):
        payment_mode = "Debit Card"
    elif any(k in lower for k in ["net banking", "netbanking", "neft", "bank transfer"]):
        payment_mode = "Net Banking"

    # 4. Extract Date
    exp_date = datetime.now().strftime("%Y-%m-%d")
    if any(k in lower for k in ["yesterday", "nethu", "kal"]):
        exp_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    # 5. Extract Item description
    clean_item = lower
    for w in ["iniku", "nethu", "today", "yesterday", "rupees", "rs", "rooba", "rubai", "vanginen", "potten", "paid", "spent", "upi", "cash", "to"]:
        clean_item = re.sub(rf'\b{w}\b', '', clean_item)
    clean_item = re.sub(r'\d+(?:\.\d+)?', '', clean_item)
    clean_item = re.sub(r'\s+', ' ', clean_item).strip().title()

    if not clean_item or len(clean_item) < 2:
        clean_item = f"{matched_cat} Expense"

    res = {
        "date": exp_date,
        "category": matched_cat,
        "item": clean_item,
        "amount": amount,
        "payment_mode": payment_mode,
        "notes": f'Voice logged: "{raw}"',
        "success": True
    }
    res["data"] = res.copy()
    return res


# Backward-compatible alias
parse_voice_transcript = parse_voice_text
