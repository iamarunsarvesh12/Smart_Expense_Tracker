"""
Smart Home Expense Tracker - Application Entry Point
Phase 2: CSV/Excel Data Storage Engine & Backend REST APIs
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

# Initialize storage and CSV structures
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
# System & Meta API Routes
# ---------------------------------------------------------------------------

@app.route("/api/health", methods=["GET"])
def health_check():
    """
    Status check route returning system health and storage readiness.
    """
    return jsonify({
        "status": "ok",
        "app": "Smart Home Expense Tracker",
        "version": "1.0.0",
        "phase": "Phase 2 - Storage Engine & REST APIs",
        "storage": {
            "csv_exists": storage.EXPENSES_CSV.exists(),
            "archive_exists": storage.ARCHIVE_CSV.exists(),
            "valid_categories": storage.VALID_CATEGORIES
        }
    }), 200


@app.route("/api/categories", methods=["GET"])
def get_categories():
    """
    Return the 5 defined expense categories for UI form population and validation.
    """
    return jsonify({
        "status": "success",
        "categories": storage.VALID_CATEGORIES
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
    Optional query parameter:
      - `date=YYYY-MM-DD`: filters for a specific date and returns daily total.
    If date is omitted, returns all active expenses in the 3-month window.
    """
    date_param = request.args.get("date")

    if date_param:
        date_param = date_param.strip()
        try:
            datetime.strptime(date_param, "%Y-%m-%d")
        except ValueError:
            return jsonify({
                "status": "error",
                "message": "Invalid date format for 'date'. Please use YYYY-MM-DD."
            }), 400

    result = storage.get_expenses_by_date(date_param)
    return jsonify({
        "status": "success",
        **result
    }), 200


@app.route("/api/summary/monthly", methods=["GET"])
def monthly_summary():
    """
    Get monthly spending summary:
    - total spending for that month
    - daily totals array (for calendar indicators)
    - category-wise spending breakdown
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
    Get rolling 3-month high-level overview:
    - total expense
    - category distribution
    - daily average
    - monthly trend
    """
    summary = storage.get_rolling_3_months_summary()
    return jsonify({
        "status": "success",
        **summary
    }), 200


@app.route("/api/export", methods=["GET"])
def export_expenses():
    """
    Generate and download the full expenses dataset.
    Query param: `format=csv` (default) or `format=excel`.
    """
    format_type = request.args.get("format", "csv").strip().lower()
    
    file_path, filename, mimetype = storage.generate_export_file(format_type)
    if not file_path or not os.path.exists(file_path):
        return jsonify({
            "status": "error",
            "message": "Failed to generate export file."
        }), 500

    return send_file(
        file_path,
        as_attachment=True,
        download_name=filename,
        mimetype=mimetype
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
