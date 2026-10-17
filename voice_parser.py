"""
Smart Home Expense Tracker - Voice & Natural Language Parser
Extracts amount, category, item, payment mode, and date from spoken Tanglish/English text.
Calibrated for the 7 Granular Expense Categories.
"""

import re
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

import storage

# Category Keywords (English + Tanglish / Tamil Transliterated) for 7 Categories
CATEGORY_KEYWORDS = {
    # 1. Food (Restaurant, Tea, Snacks, Swiggy/Zomato, Outside food)
    "Food": [
        "food", "hotel", "restaurant", "swiggy", "zomato", "tea", "chai", "coffee",
        "kaapi", "snacks", "tiffin", "breakfast", "lunch", "dinner", "biryani",
        "briyani", "fast food", "bakery", "cake", "pizza", "burger", "samosa",
        "juice", "cool drinks", "mess", "shawarma", "noodles", "parotta", "biscuit",
        "biscuits", "ice cream", "sweet", "sweets"
    ],

    # 2. Groceries (Provisions, Vegetables, Milk/Paal, Supermarket items)
    "Groceries": [
        "grocery", "groceries", "provisions", "maligai", "supermarket", "vegetable",
        "vegetables", "veggies", "kaygari", "kaaikari", "thakkali", "tomato", "onion",
        "vengayam", "potato", "urulaikizhangu", "fruits", "fruit", "pazham", "milk",
        "paal", "pal", "curd", "thayir", "butter", "paneer", "rice", "saadham", "arisi",
        "oil", "ennai", "egg", "eggs", "muttai", "chicken", "mutton", "fish", "meen",
        "wheat", "dhal", "paruppu", "masala", "salt", "sugar", "department store"
    ],

    # 3. Bike & Car (Petrol, Diesel, Vehicle Service, Mechanics, Puncture, Toll)
    "Bike & Car": [
        "petrol", "diesel", "fuel", "bike", "car", "vehicle", "service", "bike service",
        "car service", "mechanic", "puncture", "tyre", "air", "toll", "toll gate",
        "parking", "auto", "auto fare", "cab", "taxi", "rapido", "uber", "ola",
        "spare parts", "wash", "car wash", "bike wash", "engine oil", "scooter",
        "activa", "bullet", "helmet", "clutch", "brake"
    ],

    # 4. Bills & Utilities (EB / Electricity Bill, Wi-Fi / Broadband Bill, Mobile Recharge, Gas cylinder)
    "Bills & Utilities": [
        "recharge", "mobile recharge", "phone recharge", "eb bill", "current bill",
        "electricity", "electricity bill", "eb", "wifi", "broadband", "internet bill",
        "water bill", "cylinder", "gas", "gas cylinder", "indane", "bharat gas",
        "hp gas", "dth", "tata sky", "sun direct", "airtel", "jio", "vi", "bsnl",
        "cable", "cable tv", "postpaid", "prepaid"
    ],

    # 5. Stationery & Office (Printout, Xerox, Books, Pens, Courier, Office stationery)
    "Stationery & Office": [
        "printout", "print", "xerox", "photocopy", "book", "books", "puthagam",
        "pen", "pens", "pencil", "notebook", "notebooks", "note", "paper", "papers",
        "courier", "post", "speed post", "envelope", "stapler", "file", "chart",
        "marker", "office supplies", "school supplies", "scanner", "spiral binding",
        "lamination"
    ],

    # 6. Medical & Healthcare (Medicines, Doctor consultation, Medical tests, Tablets)
    "Medical & Healthcare": [
        "medicine", "medicines", "tablet", "tablets", "marunthu", "maathirai",
        "doctor", "doctor fees", "hospital", "clinic", "syrup", "injection",
        "test", "blood test", "lab test", "scan", "pharmacy", "medical",
        "consultation", "medical shop", "apollo", "dentist", "drops", "bandage",
        "ointment", "fever", "cough"
    ],

    # 7. General & Others (Money given to others, Lending, Casual cash spends, Miscellaneous)
    "General & Others": [
        "money given", "given to", "lending", "loan", "borrowed", "casual cash",
        "cash expense", "donation", "charity", "tip", "maid", "laundry", "iron",
        "dry clean", "newspaper", "barber", "salon", "haircut", "spa", "plumber",
        "electrician", "carpenter", "repair", "rent", "house rent", "maintenance",
        "gift", "misc", "miscellaneous", "others"
    ]
}

# Words to filter out when extracting item name
FILLER_WORDS = {
    # English
    "i", "bought", "buy", "spent", "spend", "paid", "pay", "gave", "give", "cost",
    "for", "at", "to", "the", "a", "an", "on", "in", "my", "of", "some", "and",
    "rupees", "rupee", "rs", "rs.", "inr", "bucks", "rooba", "roobai", "today", "yesterday",
    # Tanglish
    "vanginen", "vaanginen", "vangithen", "potten", "pottan", "paninen", "pannen",
    "kuduthen", "kuduthan", "aachu", "aayiduchu", "irukku", "ku", "la", "nethu",
    "netru", "kaasu", "panam"
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

    # Pattern 2: Standalone numbers
    numbers = re.findall(r'\b\d+(?:\.\d{1,2})?\b', text)
    if numbers:
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
    Match spoken words against the 7 defined expense categories.
    Falls back to 'General & Others' if uncertain.
    """
    text_lower = text.lower()

    category_scores = {cat: 0 for cat in storage.VALID_CATEGORIES}

    for cat, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if re.search(rf'\b{re.escape(kw)}\b', text_lower):
                category_scores[cat] += len(kw.split()) + 1

    best_category = max(category_scores, key=category_scores.get)
    if category_scores[best_category] > 0:
        return best_category

    return "General & Others"


def extract_item_name(text: str, amount: Optional[float], category: str) -> str:
    """
    Clean up numbers, currency symbols, and action verbs to isolate the core item.
    """
    cleaned = text
    if amount is not None:
        amt_str = str(int(amount)) if amount.is_integer() else str(amount)
        cleaned = re.sub(rf'\b{re.escape(amt_str)}\b', '', cleaned)
        cleaned = re.sub(r'\b\d+(?:\.\d+)?\b', '', cleaned)

    for keywords in PAYMENT_KEYWORDS.values():
        for kw in keywords:
            cleaned = re.sub(rf'\b{re.escape(kw)}\b', '', cleaned, flags=re.IGNORECASE)

    words = re.findall(r'\b[a-zA-Z]+\b', cleaned)
    item_tokens = [w for w in words if w.lower() not in FILLER_WORDS]

    if item_tokens:
        return " ".join(item_tokens).title()

    # Fallback to category name
    return category


def parse_voice_transcript(transcript: str) -> Dict[str, Any]:
    """
    End-to-end NLP parser that takes raw speech transcript and returns
    structured expense candidate fields across the 7 categories.
    """
    if not transcript or not transcript.strip():
        return {
            "success": False,
            "message": "Empty or silent transcript received."
        }

    raw_text = transcript.strip()

    amount = extract_amount(raw_text)
    category = classify_category(raw_text)
    item = extract_item_name(raw_text, amount, category)
    date_str = extract_date(raw_text)
    payment_mode = extract_payment_mode(raw_text)

    return {
        "success": True,
        "transcript": raw_text,
        "data": {
            "date": date_str,
            "category": category,
            "item": item,
            "amount": amount if amount is not None else 0.0,
            "payment_mode": payment_mode,
            "notes": f"Voice input: \"{raw_text}\""
        }
    }
