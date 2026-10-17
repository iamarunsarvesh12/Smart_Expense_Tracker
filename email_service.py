"""
Smart Home Expense Tracker - Month-End Email Dispatch Service (Pure Python Standard Library)
Zero external dependencies: uses native smtplib and email.mime modules.
Supports automated month-end dispatch and manual on-demand triggers.
"""

import os
import io
import csv
import json
import smtplib
import threading
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from typing import Tuple, Dict, Any, Optional

import storage

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DISPATCH_TRACKER_JSON = DATA_DIR / "last_dispatched.json"

DEFAULT_RECIPIENT = "sarveshsantosh2007s@gmail.com"


def get_smtp_config() -> Dict[str, Any]:
    """
    Retrieve SMTP configuration from environment variables with safe defaults.
    """
    return {
        "server": os.getenv("SMTP_SERVER", "smtp.gmail.com").strip(),
        "port": int(os.getenv("SMTP_PORT", 587)),
        "user": os.getenv("EMAIL_USER", DEFAULT_RECIPIENT).strip(),
        "password": os.getenv("EMAIL_PASS", "").strip(),
        "recipient": os.getenv("RECIPIENT_EMAIL", DEFAULT_RECIPIENT).strip() or DEFAULT_RECIPIENT
    }


def generate_month_csv_data(month_str: str) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Generate an itemized CSV string for a specific month (YYYY-MM).
    Columns: Date, Category, Item, Amount, Payment Mode, Notes
    """
    all_expenses = storage.read_all_expenses()
    month_records = [e for e in all_expenses if e.get("date", "").startswith(month_str)]
    
    # Sort chronologically by date
    month_records.sort(key=lambda x: (x.get("date", ""), x.get("id", "")))

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Date", "Category", "Item", "Amount", "Payment Mode", "Notes"])

    for r in month_records:
        writer.writerow([
            r.get("date", ""),
            r.get("category", ""),
            r.get("item", ""),
            f"{float(r.get('amount', 0)):.2f}",
            r.get("payment_mode", ""),
            r.get("notes", "")
        ])

    return output.getvalue(), month_records


def build_email_message(month_str: str, recipient: str, csv_content: str, summary: Dict[str, Any]) -> MIMEMultipart:
    """
    Construct MIME email with HTML summary table, plain-text fallback,
    and attached Expenses_<YYYY-MM>.csv file.
    """
    try:
        month_dt = datetime.strptime(month_str, "%Y-%m")
        month_label = month_dt.strftime("%B %Y")
    except ValueError:
        month_label = month_str

    total_spent = summary.get("total_spending", 0.0)
    income = summary.get("monthly_income", 0.0)
    net_savings = summary.get("net_savings", 0.0)
    savings_rate = summary.get("savings_rate", 0.0)
    category_budgets = summary.get("category_budgets", {})

    msg = MIMEMultipart("mixed")
    msg["Subject"] = f"Smart Expense Report - {month_label} (Total: ₹{total_spent:,.2f})"
    msg["From"] = f"Smart Expense Tracker <{get_smtp_config()['user']}>"
    msg["To"] = recipient

    # HTML Body Design
    cat_rows_html = ""
    for cat, data in category_budgets.items():
        spent = data.get("spent", 0.0)
        allocated = data.get("allocated", 0.0)
        remaining = data.get("remaining", 0.0)
        is_over = data.get("is_over", False)
        status_color = "#dc2626" if is_over else "#16a34a"
        status_text = "OVER BUDGET" if is_over else "Within Budget"

        cat_rows_html += f"""
        <tr style="border-bottom: 1px solid #f1f5f9;">
            <td style="padding: 10px 12px; font-weight: 600; color: #1e293b;">{cat}</td>
            <td style="padding: 10px 12px; text-align: right; color: #475569;">₹{allocated:,.2f}</td>
            <td style="padding: 10px 12px; text-align: right; font-weight: 600; color: #0f172a;">₹{spent:,.2f}</td>
            <td style="padding: 10px 12px; text-align: right; color: {status_color}; font-weight: 600;">₹{remaining:,.2f}</td>
            <td style="padding: 10px 12px; text-align: center; color: {status_color}; font-size: 11px; font-weight: 700;">{status_text}</td>
        </tr>
        """

    savings_color = "#16a34a" if net_savings >= 0 else "#dc2626"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
    </head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f8fafc; margin: 0; padding: 24px; color: #334155;">
        <div style="max-width: 640px; margin: 0 auto; background: #ffffff; border-radius: 16px; border: 1px solid #e2e8f0; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);">
            <!-- Header Banner -->
            <div style="background: linear-gradient(135deg, #4f46e5 0%, #6366f1 100%); padding: 28px 24px; color: #ffffff;">
                <div style="font-size: 12px; text-transform: uppercase; font-weight: 700; letter-spacing: 0.05em; opacity: 0.9;">Monthly Financial Statement</div>
                <h1 style="margin: 6px 0 0 0; font-size: 24px; font-weight: 800; color: #ffffff;">{month_label} Expense Report</h1>
                <p style="margin: 4px 0 0 0; font-size: 13px; opacity: 0.85;">Automated digest dispatched to {recipient}</p>
            </div>

            <!-- Metric Cards -->
            <div style="padding: 24px 20px 8px 20px;">
                <table style="width: 100%; border-collapse: separate; border-spacing: 12px 0;">
                    <tr>
                        <td style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 14px; text-align: left; width: 33%;">
                            <div style="font-size: 11px; text-transform: uppercase; font-weight: 700; color: #64748b;">Total Spent</div>
                            <div style="font-size: 18px; font-weight: 800; color: #0f172a; margin-top: 4px;">₹{total_spent:,.2f}</div>
                        </td>
                        <td style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 14px; text-align: left; width: 33%;">
                            <div style="font-size: 11px; text-transform: uppercase; font-weight: 700; color: #64748b;">Monthly Income</div>
                            <div style="font-size: 18px; font-weight: 800; color: #0f172a; margin-top: 4px;">₹{income:,.2f}</div>
                        </td>
                        <td style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 14px; text-align: left; width: 33%;">
                            <div style="font-size: 11px; text-transform: uppercase; font-weight: 700; color: #64748b;">Net Savings</div>
                            <div style="font-size: 18px; font-weight: 800; color: {savings_color}; margin-top: 4px;">₹{net_savings:,.2f}</div>
                            <div style="font-size: 10px; color: #64748b; font-weight: 600;">{savings_rate:.1f}% saved</div>
                        </td>
                    </tr>
                </table>
            </div>

            <!-- Category Breakdown Table -->
            <div style="padding: 16px 24px 24px 24px;">
                <h3 style="font-size: 14px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: #0f172a; margin: 0 0 12px 0;">
                    Category Budget & Spending Breakdown
                </h3>
                <table style="width: 100%; border-collapse: collapse; font-size: 13px;">
                    <thead>
                        <tr style="background: #f1f5f9; text-align: left; color: #475569; font-size: 11px; text-transform: uppercase;">
                            <th style="padding: 8px 12px; border-radius: 6px 0 0 6px;">Category</th>
                            <th style="padding: 8px 12px; text-align: right;">Budget</th>
                            <th style="padding: 8px 12px; text-align: right;">Spent</th>
                            <th style="padding: 8px 12px; text-align: right;">Remaining</th>
                            <th style="padding: 8px 12px; text-align: center; border-radius: 0 6px 6px 0;">Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        {cat_rows_html}
                    </tbody>
                </table>
            </div>

            <!-- Attachment Note & Footer -->
            <div style="background: #f8fafc; border-top: 1px solid #e2e8f0; padding: 16px 24px; font-size: 12px; color: #64748b;">
                <p style="margin: 0 0 4px 0;">
                    📎 <strong>Attached:</strong> <code>Expenses_{month_str}.csv</code> contains itemized transactions with date, category, amount, payment mode, and notes.
                </p>
                <p style="margin: 0; font-size: 11px; color: #94a3b8;">
                    Smart Home Expense Tracker • Built with Python & Flask • No External Dependencies
                </p>
            </div>
        </div>
    </body>
    </html>
    """

    alt_part = MIMEMultipart("alternative")
    plain_text = f"Smart Expense Report - {month_label}\nTotal Spent: ₹{total_spent:,.2f}\nMonthly Income: ₹{income:,.2f}\nNet Savings: ₹{net_savings:,.2f}\n\nAttached CSV: Expenses_{month_str}.csv"
    alt_part.attach(MIMEText(plain_text, "plain", "utf-8"))
    alt_part.attach(MIMEText(html_content, "html", "utf-8"))
    msg.attach(alt_part)

    # Attach CSV
    attachment = MIMEBase("text", "csv")
    attachment.set_payload(csv_content.encode("utf-8"))
    encoders.encode_base64(attachment)
    attachment.add_header("Content-Disposition", f'attachment; filename="Expenses_{month_str}.csv"')
    msg.attach(attachment)

    return msg


def send_monthly_report(month_str: Optional[str] = None, recipient: Optional[str] = None) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Filter expenses, calculate budget summary, attach CSV, and dispatch email via SMTP.
    """
    now = datetime.now()
    if not month_str:
        month_str = now.strftime("%Y-%m")
    else:
        month_str = month_str.strip()

    try:
        y, m = [int(p) for p in month_str.split("-")]
    except ValueError:
        return False, "Invalid month format. Please use YYYY-MM.", {}

    config = get_smtp_config()
    target_recipient = (recipient or config["recipient"]).strip()

    # Generate CSV and Summary
    csv_content, records = generate_month_csv_data(month_str)
    summary = storage.get_monthly_summary(y, m)

    # Check credentials
    if not config["password"]:
        return False, "SMTP credentials missing: Please configure 'EMAIL_PASS' in .env (Gmail App Password).", {
            "month": month_str,
            "recipient": target_recipient,
            "records_count": len(records)
        }

    try:
        msg = build_email_message(month_str, target_recipient, csv_content, summary)

        # Connect via smtplib
        server = smtplib.SMTP(config["server"], config["port"], timeout=20)
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(config["user"], config["password"])
        server.send_message(msg)
        server.quit()

        # Update last dispatched marker
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(DISPATCH_TRACKER_JSON, mode="w", encoding="utf-8") as f:
            json.dump({
                "last_dispatched_month": month_str,
                "dispatched_at": now.isoformat(),
                "recipient": target_recipient,
                "records_count": len(records)
            }, f, indent=2)

        return True, f"Monthly report for {month_str} successfully sent to {target_recipient}.", {
            "month": month_str,
            "recipient": target_recipient,
            "records_count": len(records),
            "total_spent": summary.get("total_spending", 0.0)
        }
    except smtplib.SMTPAuthenticationError:
        return False, "SMTP Authentication Failed: Invalid email or app password. Check EMAIL_USER and EMAIL_PASS.", {}
    except Exception as e:
        return False, f"Failed to send email: {str(e)}", {}


def check_and_trigger_month_end_auto_dispatch() -> None:
    """
    Background worker: Checks if today is the last day of the month or 1st day of next month.
    If so, automatically dispatches the monthly report if not already dispatched.
    Runs asynchronously to never block web application requests.
    """
    def _worker():
        try:
            now = datetime.now()
            tomorrow = now + timedelta(days=1)
            is_last_day = (tomorrow.day == 1)
            is_first_day = (now.day == 1)

            if not (is_last_day or is_first_day):
                return

            if is_last_day:
                target_month = now.strftime("%Y-%m")
            else:
                # 1st day of month -> report previous month
                prev_month_date = now - timedelta(days=1)
                target_month = prev_month_date.strftime("%Y-%m")

            # Check if already dispatched
            if DISPATCH_TRACKER_JSON.exists():
                try:
                    with open(DISPATCH_TRACKER_JSON, mode="r", encoding="utf-8") as f:
                        data = json.load(f)
                        if data.get("last_dispatched_month") == target_month:
                            return  # Already sent for this month
                except Exception:
                    pass

            # Attempt auto-dispatch
            send_monthly_report(target_month)
        except Exception:
            pass  # Silent failure for background check

    threading.Thread(target=_worker, daemon=True).start()
