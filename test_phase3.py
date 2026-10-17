"""
Phase 3 Verification Script
Tests that frontend dashboard template and static assets render correctly.
"""

from app import app

def verify_frontend():
    client = app.test_client()

    # 1. Test GET /
    res = client.get("/")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    html = res.data.decode("utf-8")

    # Check key element IDs and integrations
    required_strings = [
        "Smart Home Expense Tracker",
        "chart-category-ranking",
        "chart-daily-bars",
        "calendar-grid",
        "modal-add-expense",
        "modal-voice-confirm",
        "modal-budget-settings",
        "btn-voice-header",
        "cdn.jsdelivr.net/npm/chart.js",
        "tailwindcss.com",
        "static/css/style.css",
        "static/js/app.js"
    ]
    for req in required_strings:
        assert req in html, f"Missing required snippet in index.html: '{req}'"

    # 2. Test static css
    css_res = client.get("/static/css/style.css")
    assert css_res.status_code == 200, "CSS not served"
    assert "calendar-tile" in css_res.data.decode("utf-8")

    # 3. Test static js
    js_res = client.get("/static/js/app.js")
    assert js_res.status_code == 200, "JS not served"
    assert "CATEGORY_CONFIG" in js_res.data.decode("utf-8")

    print("[PASS] Phase 3 Frontend verification completed successfully with all components present!")

if __name__ == "__main__":
    verify_frontend()
