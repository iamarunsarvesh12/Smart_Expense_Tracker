"""
Smart Home Expense Tracker - Application Entry Point (Pure Python Standard Library)
Supports 7 granular expense categories, monthly income & budget allocations,
remaining balances & net savings, and voice NLP extraction.
Strictly zero Pandas / zero OpenPyXL - 100% Python 3.14+ compatible.
"""

import os
from datetime import datetime
from flask import Flask, jsonify, request, render_template, send_file
from dotenv import load_dotenv

import storage
import voice_parser

# Load environment variables
load_dotenv()

# Initialize Flask application
app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")

# Auto-initialize storage, CSV structures, and default budget
storage.init_storage()


# ---------------------------------------------------------------------------
# Frontend Routes
# ---------------------------------------------------------------------------

@app.route("/", methods=["GET"])
def index():
    """
    Render the frontend dashboard.
    """
    return render_template("index.html")


# ---------------------------------------------------------------------------
# System & Metadata Routes
# ---------------------------------------------------------------------------

@app.route("/api/health", methods=["GET"])
def health_check():
    """
    Status check route returning system health and storage readiness.
    """
    return jsonify({
        "status": "ok",
        "app": "Smart Home Expense Tracker",
        "version": "2.0.0",
        "engine": "Pure Python Standard Library (No Pandas / No OpenPyXL)",
        "storage": {
            "csv_exists": storage.EXPENSES_CSV.exists(),
            "budget_json_exists": storage.BUDGET_JSON.exists(),
            "valid_categories": storage.VALID_CATEGORIES
        }
    }), 200


@app.route("/api/categories", methods=["GET"])
def get_categories():
    """
    Return the 7 defined expense categories for UI form population and validation.
    """
    return jsonify({
        "status": "success",
        "categories": storage.VALID_CATEGORIES
    }), 200


# ---------------------------------------------------------------------------
# Income & Budget Configuration Endpoints
# ---------------------------------------------------------------------------

@app.route("/api/budget", methods=["GET"])
def get_budget():
    """
    Get current monthly income and category allocations from budget_config.json.
    """
    config = storage.get_budget_config()
    return jsonify({
        "status": "success",
        "budget": config
    }), 200


@app.route("/api/budget", methods=["POST"])
def update_budget():
    """
    Save updated monthly income and category allocations.
    Accepts JSON: { "monthly_income": 30000, "categories": { "Food": 5000, ... } }
    """
    if not request.is_json:
        return jsonify({
            "status": "error",
            "message": "Request body must be JSON."
        }), 400

    payload = request.get_json()
    success, error_msg, updated_config = storage.save_budget_config(payload)

    if not success:
        return jsonify({
            "status": "error",
            "message": error_msg
        }), 400

    return jsonify({
        "status": "success",
        "message": "Budget settings updated successfully.",
        "budget": updated_config
    }), 200


# ---------------------------------------------------------------------------
# Voice & AI Natural Language Parsing Endpoint
# ---------------------------------------------------------------------------

@app.route("/api/parse-voice", methods=["POST"])
def parse_voice():
    """
    Parse natural language speech transcript into structured expense fields.
    Accepts JSON: { "text": "Paal vanginen 30 rupees" }
    """
    if not request.is_json:
        return jsonify({
            "status": "error",
            "message": "Request body must be JSON."
        }), 400

    payload = request.get_json()
    transcript = payload.get("text", "")

    result = voice_parser.parse_voice_transcript(transcript)
    if not result.get("success"):
        return jsonify({
            "status": "error",
            "message": result.get("message", "Unable to extract expense details from speech.")
        }), 400

    return jsonify({
        "status": "success",
        **result
    }), 200


# ---------------------------------------------------------------------------
# Core Expense API Endpoints
# ---------------------------------------------------------------------------

@app.route("/api/expenses", methods=["POST"])
def create_expense():
    """
    Create a new expense entry.
    Accepts JSON payload: { date, time (optional), category, item, amount, payment_mode, notes }
    """
    if not request.is_json:
        return jsonify({
            "status": "error",
            "message": "Request body must be JSON."
        }), 400

    payload = request.get_json()
    success, error_msg, record = storage.add_expense(payload)

    if not success:
        return jsonify({
            "status": "error",
            "message": error_msg
        }), 400

    return jsonify({
        "status": "success",
        "message": "Expense recorded successfully.",
        "data": record
    }), 201


@app.route("/api/expenses", methods=["GET"])
def list_expenses():
    """
    Query expenses.
    Optional query parameters:
      - `date=YYYY-MM-DD`: filters for a specific date
      - `category=Name`: filters for a specific category
    """
    date_param = request.args.get("date")
    cat_param = request.args.get("category")

    if date_param:
        date_param = date_param.strip()
        try:
            datetime.strptime(date_param, "%Y-%m-%d")
        except ValueError:
            return jsonify({
                "status": "error",
                "message": "Invalid date format for 'date'. Please use YYYY-MM-DD."
            }), 400

    result = storage.get_expenses_by_date(date_str=date_param, category_filter=cat_param)
    return jsonify({
        "status": "success",
        **result
    }), 200


@app.route("/api/summary/monthly", methods=["GET"])
def monthly_summary():
    """
    Get monthly spending summary:
    - Total monthly spend & transaction count
    - Monthly income, net savings & savings rate %
    - Daily spend map / array & recommended daily burn rate
    - Category spend breakdown, budget limits, remaining balances & over-budget alerts
    Query params: `year=YYYY` and `month=MM` (defaults to current year/month).
    """
    now = datetime.now()
    year_param = request.args.get("year", str(now.year))
    month_param = request.args.get("month", str(now.month))

    try:
        year = int(year_param)
        month = int(month_param)
        if not (1 <= month <= 12):
            raise ValueError("Month must be between 1 and 12.")
        if year < 1970 or year > 2100:
            raise ValueError("Year must be a reasonable 4-digit year.")
    except (ValueError, TypeError) as err:
        return jsonify({
            "status": "error",
            "message": f"Invalid year or month parameter: {str(err)}"
        }), 400

    summary = storage.get_monthly_summary(year, month)
    return jsonify({
        "status": "success",
        **summary
    }), 200


@app.route("/api/summary/rolling-3-months", methods=["GET"])
def rolling_summary():
    """
    Get rolling 3-month high-level overview.
    """
    summary = storage.get_rolling_3_months_summary()
    return jsonify({
        "status": "success",
        **summary
    }), 200


@app.route("/api/export", methods=["GET"])
def export_expenses():
    """
    Generate and download the full expenses.csv dataset using Flask's send_file.
    """
    if not storage.EXPENSES_CSV.exists():
        storage.init_storage()

    timestamp = datetime.now().strftime("%Y%m%d")
    return send_file(
        str(storage.EXPENSES_CSV),
        as_attachment=True,
        download_name=f"expenses_{timestamp}.csv",
        mimetype="text/csv"
    )


# ---------------------------------------------------------------------------
# Error Handlers
# ---------------------------------------------------------------------------

@app.errorhandler(404)
def not_found(error):
    if request.path.startswith("/api/"):
        return jsonify({
            "status": "error",
            "message": f"API endpoint '{request.path}' not found."
        }), 404
    return render_template("index.html"), 404


@app.errorhandler(500)
def server_error(error):
    return jsonify({
        "status": "error",
        "message": "An internal server error occurred."
    }), 500


# ---------------------------------------------------------------------------
# Application Server Startup
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug_mode = os.getenv("FLASK_DEBUG", "True").strip().lower() in ("true", "1", "t")
    app.run(host="0.0.0.0", port=port, debug=debug_mode)
