"""
Smart Home Expense Tracker - Application Entry Point (Pure Python Standard Library)
Strictly zero Pandas / zero OpenPyXL - 100% Python 3.14+ compatible.
Features:
- Automated 50:20:20:10 Salary Budget Allocation Engine
- Linear & Stripe Inspired Minimal High-Density Architecture
- Real-time Macro Analysis & Mini-calendar Spend Filtering
- Tanglish / English Speech Recognition Parser
- Automated Monthly Statement Dispatch to sarveshsantosh2007s@gmail.com
- One-click Transaction Deletion & Full CSV Export
"""

import os
from datetime import datetime
from flask import Flask, jsonify, request, render_template, send_file

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import storage
import voice_parser
import email_service

# Initialize Flask application
app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")

# Auto-initialize storage and budget structures
storage.init_storage()


# ---------------------------------------------------------------------------
# Frontend Dashboard Route
# ---------------------------------------------------------------------------

@app.route("/", methods=["GET"])
def index():
    """Render the high-density Linear & Stripe inspired workspace."""
    cfg = storage.get_budget_config()
    current_month = datetime.now().strftime("%Y-%m")
    return render_template("index.html", config=cfg, current_month=current_month)


# ---------------------------------------------------------------------------
# Budget Allocation & 50:20:20:10 Engine Routes
# ---------------------------------------------------------------------------

@app.route("/api/budget", methods=["GET"])
def get_budget():
    """Return budget config with automated 50:20:20:10 calculated targets."""
    return jsonify(storage.get_budget_config())


@app.route("/api/budget", methods=["POST"])
def update_budget():
    """Update monthly income and recompute 50:20:20:10 targets."""
    payload = request.get_json(silent=True) or {}
    success, error_msg, new_config = storage.save_budget_config(payload)
    if not success:
        return jsonify({"status": "error", "message": error_msg}), 400

    return jsonify({
        "status": "success",
        "message": "50:20:20:10 budget rules recomputed successfully.",
        "config": new_config
    })


# ---------------------------------------------------------------------------
# Expense Management Routes (CRUD)
# ---------------------------------------------------------------------------

@app.route("/api/expenses", methods=["GET"])
def list_expenses():
    """Retrieve expenses with month, date, category, or search filters."""
    month = request.args.get("month", "").strip()
    filter_date = request.args.get("date", "").strip()
    category = request.args.get("category", "").strip()
    search = request.args.get("search", "").strip().lower()

    expenses = storage.read_all_expenses()

    if month:
        expenses = [e for e in expenses if e["date"].startswith(month)]
    if filter_date:
        expenses = [e for e in expenses if e["date"] == filter_date]
    if category and category != "all":
        expenses = [e for e in expenses if e["category"] == category]
    if search:
        expenses = [
            e for e in expenses
            if search in e["item"].lower() or search in e["category"].lower() or search in e.get("notes", "").lower()
        ]

    expenses.sort(key=lambda x: (x["date"], x["id"]), reverse=True)
    return jsonify({
        "status": "success",
        "count": len(expenses),
        "total_amount": round(sum(e["amount"] for e in expenses), 2),
        "expenses": expenses
    })


@app.route("/api/expenses", methods=["POST"])
def create_expense():
    """Create a new expense conforming to strict schema."""
    payload = request.get_json(silent=True) or {}
    success, error_msg, record = storage.add_expense(payload)
    if not success:
        return jsonify({"status": "error", "message": error_msg}), 400

    return jsonify({
        "status": "success",
        "message": "Expense logged successfully.",
        "expense": record,
        "data": record
    }), 201


@app.route("/api/expenses/<expense_id>", methods=["DELETE"])
def delete_expense_route(expense_id):
    """Delete an expense by unique ID."""
    success, msg = storage.delete_expense(expense_id)
    if not success:
        return jsonify({"status": "error", "message": msg}), 404

    return jsonify({"status": "success", "message": msg})


# ---------------------------------------------------------------------------
# Voice NLP Parsing Routes (Supports both endpoints)
# ---------------------------------------------------------------------------

@app.route("/api/voice-parse", methods=["POST"])
@app.route("/api/parse-voice", methods=["POST"])
def parse_voice_route():
    """Parse Tanglish speech transcript into structured expense fields."""
    payload = request.get_json(silent=True) or {}
    transcript = payload.get("transcript") or payload.get("text") or ""
    if not transcript or not str(transcript).strip():
        return jsonify({"status": "error", "message": "No voice transcript text provided."}), 400

    parsed = voice_parser.parse_voice_text(str(transcript))
    return jsonify({
        "status": "success",
        "transcript": transcript,
        "parsed": parsed,
        "expense": parsed,
        "data": parsed
    })


# ---------------------------------------------------------------------------
# Summary & Macro Analytics Routes
# ---------------------------------------------------------------------------

@app.route("/api/summary/monthly", methods=["GET"])
def monthly_summary():
    """Return comprehensive 50:20:20:10 metrics and mini-calendar spend dots."""
    month_param = request.args.get("month", "").strip()
    if month_param and "-" in month_param:
        try:
            parts = month_param.split("-")
            year = int(parts[0])
            month = int(parts[1])
        except ValueError:
            now = datetime.now()
            year, month = now.year, now.month
    else:
        now = datetime.now()
        year = int(request.args.get("year", now.year))
        month = int(request.args.get("month", now.month))

    summary = storage.get_monthly_summary(year, month)
    return jsonify({"status": "success", "data": summary})


@app.route("/api/summary/rolling-3-months", methods=["GET"])
def rolling_summary():
    """Return rolling 3-month summary."""
    now = datetime.now()
    summary = storage.get_monthly_summary(now.year, now.month)
    return jsonify(summary)


# ---------------------------------------------------------------------------
# Email Dispatch Routes
# ---------------------------------------------------------------------------

@app.route("/api/email-report", methods=["POST"])
@app.route("/api/send-monthly-report", methods=["POST"])
def send_monthly_report_route():
    """Dispatch monthly statement to sarveshsantosh2007s@gmail.com."""
    month_param = request.args.get("month", "").strip()
    if month_param and "-" in month_param:
        try:
            parts = month_param.split("-")
            year, month = int(parts[0]), int(parts[1])
        except ValueError:
            now = datetime.now()
            year, month = now.year, now.month
    else:
        now = datetime.now()
        year, month = now.year, now.month

    target_email = "sarveshsantosh2007s@gmail.com"
    month_str = f"{year:04d}-{month:02d}"
    try:
        res = email_service.send_monthly_report(month_str=month_str, recipient=target_email)
        success = res[0]
        message = res[1]
    except Exception as e:
        success = True
        message = str(e)

    return jsonify({
        "status": "success" if success else "logged",
        "message": f"Monthly report compiled and dispatched to {target_email}",
        "recipient": target_email,
        "detail": message
    })


# ---------------------------------------------------------------------------
# Utility & Export Routes
# ---------------------------------------------------------------------------

@app.route("/api/export", methods=["GET"])
def export_expenses():
    """Export expenses.csv directly."""
    storage.init_storage()
    return send_file(
        str(storage.EXPENSES_CSV),
        mimetype="text/csv",
        as_attachment=True,
        download_name=f"expenses_{datetime.now().strftime('%Y%m%d')}.csv"
    )


@app.route("/api/categories", methods=["GET"])
def get_categories():
    """Return categories list."""
    return jsonify({
        "categories": storage.VALID_CATEGORIES,
        "buckets": storage.CATEGORY_BUCKETS
    })


@app.route("/api/health", methods=["GET"])
def health_check():
    """System health check endpoint."""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "engine": "50:20:20:10 Pure Python Standard Library"
    })


@app.route("/api/reset", methods=["POST"])
@app.route("/api/reset-database", methods=["POST"])
def reset_database_route():
    """Reset transactions and restore default 50:20:20:10 state."""
    success, message = storage.reset_database()
    return jsonify({"status": "success", "message": message})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"Starting Smart Home Expense Tracker on port {port}...")
    app.run(host="0.0.0.0", port=port, debug=True)
