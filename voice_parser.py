"""
Smart Home Expense Tracker - Voice & Natural Language Parser
Extracts amount, category, item, payment mode, and date from spoken Tanglish/English text.
"""

import re
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

import storage

# Category Keywords (English + Tanglish / Tamil Transliterated)
CATEGORY_KEYWORDS = {
    "Food & Groceries": [
        "milk", "paal", "pal", "grocery", "groceries", "maligai", "provisions",
        "vegetable", "vegetables", "veggies", "kaygari", "kaaikari", "thakkali", "tomato",
        "onion", "vengayam", "potato", "urulaikizhangu", "fruits", "fruit", "pazham",
        "biryani", "briyani", "rice", "saadham", "tea", "chai", "coffee", "kaapi",
        "hotel", "restaurant", "food", "sappadu", "snacks", "tiffin", "breakfast",
        "lunch", "dinner", "biscuit", "biscuits", "curd", "thayir", "bread", "butter",
        "egg", "eggs", "muttai", "chicken", "mutton", "fish", "meen", "oil", "ennai"
    ],
    "Fuel & Commute": [
        "petrol", "diesel", "fuel", "gas", "auto", "auto fare", "cab", "taxi",
        "bus", "bus fare", "ticket", "toll", "parking", "bike service", "car service",
        "puncture", "service", "uber", "ola", "rapido", "metro", "train", "commute",
        "travel", "ride"
    ],
    "Stationery & Office": [
        "printout", "print", "xerox", "photocopy", "book", "books", "puthagam",
        "pen", "pens", "pencil", "notebook", "notebooks", "note", "paper", "papers",
        "courier", "post", "stapler", "binding", "stationery", "chart", "marker",
        "office supplies", "school supplies"
    ],
    "Medical & Healthcare": [
        "medicine", "medicines", "tablet", "tablets", "marunthu", "maathirai",
        "doctor", "doctor fees", "hospital", "clinic", "syrup", "injection",
        "test", "blood test", "scan", "pharmacy", "medical", "consultation",
        "dentist", "drops", "bandage", "ointment"
    ],
    "General & Daily Utilities": [
        "recharge", "mobile recharge", "current bill", "eb bill", "electricity",
        "electricity bill", "water bill", "wifi", "broadband", "cylinder", "gas cylinder",
        "plumber", "repair", "electrician", "rent", "maintenance", "maid",
        "newspaper", "misc", "miscellaneous", "cash expense"
    ]
}

# Words to remove when extracting the item description
FILLER_WORDS = {
    # English fillers
    "i", "bought", "buy", "spent", "spend", "paid", "pay", "gave", "give", "cost",
    "for", "at", "to", "the", "a", "an", "on", "in", "my", "of", "some", "and",
    "rupees", "rupee", "rs", "rs.", "inr", "bucks", "rooba", "roobai", "today", "yesterday",
    # Tanglish / Tamil action words
    "vanginen", "vaanginen", "vangithen", "potten", "pottan", "paninen", "pannen",
    "kuduthen", "kuduthan", "aachu", "aayiduchu", "aachu", "irukku", "ku", "la",
    "nethu", "netru", "kaasu", "panam", "roobai"
}

# Payment Mode Keywords
PAYMENT_KEYWORDS = {
    "UPI": ["gpay", "google pay", "phonepe", "paytm", "upi", "online", "scan", "qr", "bhim"],
    "Cash": ["cash", "kaasu", "panam", "hand cash"],
    "Credit Card": ["credit card", "credit", "card"],
    "Debit Card": ["debit card", "debit", "atm"],
    "Net Banking": ["net banking", "netbanking", "bank transfer", "neft", "imps"]
}


def extract_amount(text: str) -> Optional[float]:
    """
    Extract monetary amount from spoken text.
    Handles patterns like:
    - 'paal 30'
    - 'petrol 200 rupees'
    - '50 rs'
    - 'recharge paninen 299'
    - 'tablet 150.50'
    """
    # Pattern 1: Number adjacent to currency tokens
    pattern_currency = re.search(
        r'(?:rs\.?|rupees?|roobai?|₹|inr)\s*(\d+(?:\.\d{1,2})?)',
        text,
        re.IGNORECASE
    )
    if pattern_currency:
        try:
            return float(pattern_currency.group(1))
        except ValueError:
            pass

    pattern_number_first = re.search(
        r'(\d+(?:\.\d{1,2})?)\s*(?:rs\.?|rupees?|roobai?|₹|inr|rooba)',
        text,
        re.IGNORECASE
    )
    if pattern_number_first:
        try:
            return float(pattern_number_first.group(1))
        except ValueError:
            pass

    # Pattern 2: Any standalone numeric value in the sentence
    numbers = re.findall(r'\b\d+(?:\.\d{1,2})?\b', text)
    if numbers:
        # Prefer the last number (e.g. "milk 30") or largest reasonable price
        try:
            return float(numbers[-1])
        except ValueError:
            pass

    return None


def extract_date(text: str) -> str:
    """
    Extract transaction date. Defaults to today unless relative terms like
    'yesterday', 'nethu', or 'munthanethu' are detected.
    """
    text_lower = text.lower()
    now = datetime.now()

    if any(k in text_lower for k in ["day before yesterday", "munthanethu", "mundhanethu"]):
        return (now - timedelta(days=2)).strftime("%Y-%m-%d")

    if any(k in text_lower for k in ["yesterday", "nethu", "netru", "nethikku"]):
        return (now - timedelta(days=1)).strftime("%Y-%m-%d")

    return now.strftime("%Y-%m-%d")


def extract_payment_mode(text: str) -> str:
    """
    Extract payment mode based on keywords. Defaults to UPI.
    """
    text_lower = text.lower()
    for mode, keywords in PAYMENT_KEYWORDS.items():
        for kw in keywords:
            if re.search(rf'\b{re.escape(kw)}\b', text_lower):
                return mode
    return "UPI"


def classify_category(text: str) -> str:
    """
    Match spoken words against the 5 predefined expense categories.
    Falls back to 'General & Daily Utilities' if uncertain.
    """
    text_lower = text.lower()

    # Score each category based on keyword matches
    category_scores = {cat: 0 for cat in storage.VALID_CATEGORIES}

    for cat, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            # Word boundary matching
            if re.search(rf'\b{re.escape(kw)}\b', text_lower):
                # Exact or compound match
                category_scores[cat] += len(kw.split()) + 1

    best_category = max(category_scores, key=category_scores.get)
    if category_scores[best_category] > 0:
        return best_category

    return "General & Daily Utilities"


def extract_item_name(text: str, amount: Optional[float], category: str) -> str:
    """
    Clean up numbers, currency symbols, and action verbs to isolate the core item.
    """
    # Remove amount if present
    cleaned = text
    if amount is not None:
        # Remove integer or float representation
        amt_str = str(int(amount)) if amount.is_integer() else str(amount)
        cleaned = re.sub(rf'\b{re.escape(amt_str)}\b', '', cleaned)
        cleaned = re.sub(r'\b\d+(?:\.\d+)?\b', '', cleaned)

    # Remove payment keywords
    for keywords in PAYMENT_KEYWORDS.values():
        for kw in keywords:
            cleaned = re.sub(rf'\b{re.escape(kw)}\b', '', cleaned, flags=re.IGNORECASE)

    # Split into words and filter fillers
    words = re.findall(r'\b[a-zA-Z]+\b', cleaned)
    item_tokens = [w for w in words if w.lower() not in FILLER_WORDS]

    if item_tokens:
        raw_name = " ".join(item_tokens).title()
        return raw_name

    # Fallback to category base name
    if category == "Food & Groceries":
        return "Groceries"
    if category == "Fuel & Commute":
        return "Fuel"
    if category == "Stationery & Office":
        return "Stationery"
    if category == "Medical & Healthcare":
        return "Medicines"
    return "General Expense"


def parse_voice_transcript(transcript: str) -> Dict[str, Any]:
    """
    End-to-end NLP parser that takes raw speech transcript and returns
    structured expense candidate fields.
    """
    if not transcript or not transcript.strip():
        return {
            "success": False,
            "message": "Empty or silent transcript received."
        }

    raw_text = transcript.strip()

    # 1. Extract Amount
    amount = extract_amount(raw_text)

    # 2. Extract Category
    category = classify_category(raw_text)

    # 3. Extract Item Name
    item = extract_item_name(raw_text, amount, category)

    # 4. Extract Date
    date_str = extract_date(raw_text)

    # 5. Extract Payment Mode
    payment_mode = extract_payment_mode(raw_text)

    return {
        "success": True,
        "transcript": raw_text,
        "data": {
            "date": date_str,
            "time": datetime.now().strftime("%H:%M:%S"),
            "category": category,
            "item": item,
            "amount": amount if amount is not None else 0.0,
            "payment_mode": payment_mode,
            "notes": f"Voice input: \"{raw_text}\""
        }
    }
