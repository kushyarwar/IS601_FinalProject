"""
Playwright E2E tests covering all final project features:
- Register / Login flows
- Calculation BREAD (including Power and Modulus)
- Profile update and password change
- Reports dashboard
"""
import httpx
import pytest

SERVER_URL = "http://127.0.0.1:8001"


def _api_register(email, password="securepass123"):
    res = httpx.post(f"{SERVER_URL}/register", json={"email": email, "password": password})
    return res.json()


# ── Auth E2E Tests ─────────────────────────────────────────────────────────

def test_register_valid_data(page, live_server):
    page.goto(f"{SERVER_URL}/static/register.html")
    page.fill("#email", "e2e_register@example.com")
    page.fill("#password", "securepass123")
    page.fill("#confirm_password", "securepass123")
    page.click("button[type=submit]")
    page.wait_for_selector("#success-msg", state="visible", timeout=8000)
    assert "success" in page.inner_text("#success-msg").lower()


def test_register_short_password_shows_error(page, live_server):
    page.goto(f"{SERVER_URL}/static/register.html")
    page.fill("#email", "shortpw@example.com")
    page.fill("#password", "abc")
    page.fill("#confirm_password", "abc")
    page.click("button[type=submit]")
    page.wait_for_selector("#error-msg", state="visible", timeout=5000)
    assert "password" in page.inner_text("#error-msg").lower()


def test_register_password_mismatch_shows_error(page, live_server):
    page.goto(f"{SERVER_URL}/static/register.html")
    page.fill("#email", "mismatch@example.com")
    page.fill("#password", "securepass123")
    page.fill("#confirm_password", "differentpass123")
    page.click("button[type=submit]")
    page.wait_for_selector("#error-msg", state="visible", timeout=5000)
    assert "match" in page.inner_text("#error-msg").lower()


def test_login_valid_credentials(page, live_server):
    _api_register("e2e_login@example.com")
    page.goto(f"{SERVER_URL}/static/login.html")
    page.fill("#email", "e2e_login@example.com")
    page.fill("#password", "securepass123")
    page.click("button[type=submit]")
    page.wait_for_selector("#success-msg", state="visible", timeout=8000)
    assert "success" in page.inner_text("#success-msg").lower()


def test_login_wrong_password_shows_error(page, live_server):
    _api_register("wrongpw@example.com")
    page.goto(f"{SERVER_URL}/static/login.html")
    page.fill("#email", "wrongpw@example.com")
    page.fill("#password", "totallyWrongPass999")
    page.click("button[type=submit]")
    page.wait_for_selector("#error-msg", state="visible", timeout=8000)
    assert "invalid" in page.inner_text("#error-msg").lower()


# ── Calculation BREAD E2E Tests ────────────────────────────────────────────

def test_calculations_without_login_shows_error(page, live_server):
    page.goto(f"{SERVER_URL}/static/calculations.html")
    page.evaluate("localStorage.removeItem('jwt_token')")
    page.reload()
    page.wait_for_selector("#error-msg", state="visible", timeout=5000)
    assert "login" in page.inner_text("#error-msg").lower()


def test_calculation_add_create_read_edit_delete(page, live_server):
    data = _api_register("e2e_bread@example.com")
    token = data["token"]

    page.goto(f"{SERVER_URL}/static/calculations.html")
    page.evaluate("(t) => localStorage.setItem('jwt_token', t)", token)
    page.reload()

    # Create
    page.fill("#a", "8")
    page.fill("#b", "4")
    page.select_option("#type", "Add")
    page.click("#save-btn")
    page.wait_for_selector("#success-msg", state="visible", timeout=8000)
    assert "created" in page.inner_text("#success-msg").lower()
    assert "12" in page.inner_text("#calc-list")

    # Read
    page.click("button[data-action='read']")
    page.wait_for_selector("#detail-box", state="visible", timeout=5000)
    assert "12" in page.inner_text("#detail-box")

    # Edit
    page.click("button[data-action='edit']")
    page.wait_for_function("document.querySelector('#calc-id').value !== ''")
    page.fill("#a", "20")
    page.fill("#b", "5")
    page.select_option("#type", "Divide")
    page.click("#save-btn")
    page.wait_for_selector("#success-msg", state="visible", timeout=8000)
    assert "updated" in page.inner_text("#success-msg").lower()
    assert "4" in page.inner_text("#calc-list")

    # Delete
    page.click("button[data-action='delete']")
    page.wait_for_selector("#success-msg", state="visible", timeout=8000)
    assert "deleted" in page.inner_text("#success-msg").lower()
    page.wait_for_selector("#empty-msg", state="visible", timeout=5000)


def test_calculation_divide_by_zero_shows_error(page, live_server):
    data = _api_register("e2e_divzero@example.com")
    token = data["token"]
    page.goto(f"{SERVER_URL}/static/calculations.html")
    page.evaluate("(t) => localStorage.setItem('jwt_token', t)", token)
    page.reload()
    page.fill("#a", "9")
    page.fill("#b", "0")
    page.select_option("#type", "Divide")
    page.click("#save-btn")
    page.wait_for_selector("#error-msg", state="visible", timeout=5000)
    assert "division by zero" in page.inner_text("#error-msg").lower()


def test_calculation_modulus_by_zero_shows_error(page, live_server):
    data = _api_register("e2e_modzero@example.com")
    token = data["token"]
    page.goto(f"{SERVER_URL}/static/calculations.html")
    page.evaluate("(t) => localStorage.setItem('jwt_token', t)", token)
    page.reload()
    page.fill("#a", "10")
    page.fill("#b", "0")
    page.select_option("#type", "Modulus")
    page.click("#save-btn")
    page.wait_for_selector("#error-msg", state="visible", timeout=5000)
    assert "modulus by zero" in page.inner_text("#error-msg").lower()


def test_power_operation_in_ui(page, live_server):
    data = _api_register("e2e_power@example.com")
    token = data["token"]
    page.goto(f"{SERVER_URL}/static/calculations.html")
    page.evaluate("(t) => localStorage.setItem('jwt_token', t)", token)
    page.reload()
    page.fill("#a", "2")
    page.fill("#b", "10")
    page.select_option("#type", "Power")
    page.click("#save-btn")
    page.wait_for_selector("#success-msg", state="visible", timeout=8000)
    assert "1024" in page.inner_text("#calc-list")


def test_modulus_operation_in_ui(page, live_server):
    data = _api_register("e2e_modulus@example.com")
    token = data["token"]
    page.goto(f"{SERVER_URL}/static/calculations.html")
    page.evaluate("(t) => localStorage.setItem('jwt_token', t)", token)
    page.reload()
    page.fill("#a", "10")
    page.fill("#b", "3")
    page.select_option("#type", "Modulus")
    page.click("#save-btn")
    page.wait_for_selector("#success-msg", state="visible", timeout=8000)
    assert "1" in page.inner_text("#calc-list")


# ── Profile E2E Tests ──────────────────────────────────────────────────────

def test_profile_loads_user_info(page, live_server):
    data = _api_register("e2e_profile@example.com")
    token = data["token"]
    page.goto(f"{SERVER_URL}/static/profile.html")
    page.evaluate("(t) => localStorage.setItem('jwt_token', t)", token)
    page.reload()
    page.wait_for_function("document.querySelector('#username').value !== ''", timeout=5000)
    assert "e2e_profile" in page.input_value("#username")
    assert "e2e_profile@example.com" in page.input_value("#email")


def test_profile_update_bio(page, live_server):
    data = _api_register("e2e_bio@example.com")
    token = data["token"]
    page.goto(f"{SERVER_URL}/static/profile.html")
    page.evaluate("(t) => localStorage.setItem('jwt_token', t)", token)
    page.reload()
    page.wait_for_function("document.querySelector('#username').value !== ''", timeout=5000)
    page.fill("#bio", "I love calculators!")
    page.click("button[type=submit]")
    page.wait_for_selector("#profile-success", state="visible", timeout=8000)
    assert "success" in page.inner_text("#profile-success").lower()


def test_password_change_wrong_current_shows_error(page, live_server):
    data = _api_register("e2e_pwchange@example.com")
    token = data["token"]
    page.goto(f"{SERVER_URL}/static/profile.html")
    page.evaluate("(t) => localStorage.setItem('jwt_token', t)", token)
    page.reload()
    page.wait_for_function("document.querySelector('#username').value !== ''", timeout=5000)
    page.fill("#current-password", "WrongCurrentPass1")
    page.fill("#new-password", "NewSecurePass123")
    page.fill("#confirm-new-password", "NewSecurePass123")
    page.click("#pw-form button[type=submit]")
    page.wait_for_selector("#pw-error", state="visible", timeout=8000)
    assert "incorrect" in page.inner_text("#pw-error").lower()


def test_password_mismatch_shows_error(page, live_server):
    data = _api_register("e2e_pwmismatch@example.com")
    token = data["token"]
    page.goto(f"{SERVER_URL}/static/profile.html")
    page.evaluate("(t) => localStorage.setItem('jwt_token', t)", token)
    page.reload()
    page.wait_for_function("document.querySelector('#username').value !== ''", timeout=5000)
    page.fill("#current-password", "securepass123")
    page.fill("#new-password", "NewPass12345")
    page.fill("#confirm-new-password", "DifferentPass12")
    page.click("#pw-form button[type=submit]")
    page.wait_for_selector("#pw-error", state="visible", timeout=5000)
    assert "match" in page.inner_text("#pw-error").lower()


# ── Reports E2E Tests ──────────────────────────────────────────────────────

def test_reports_shows_stats(page, live_server):
    data = _api_register("e2e_reports@example.com")
    token = data["token"]

    httpx.post(f"{SERVER_URL}/calculations", json={"a": 5, "b": 3, "type": "Add"},
               headers={"Authorization": f"Bearer {token}"})
    httpx.post(f"{SERVER_URL}/calculations", json={"a": 2, "b": 8, "type": "Power"},
               headers={"Authorization": f"Bearer {token}"})

    page.goto(f"{SERVER_URL}/static/reports.html")
    page.evaluate("(t) => localStorage.setItem('jwt_token', t)", token)
    page.reload()

    page.wait_for_function("document.getElementById('total').textContent !== '–'", timeout=8000)
    assert page.inner_text("#total") == "2"
    assert page.inner_text("#most-used") != "–"


def test_reports_without_login_redirects(page, live_server):
    page.goto(f"{SERVER_URL}/static/reports.html")
    page.evaluate("localStorage.removeItem('jwt_token')")
    page.reload()
    page.wait_for_url("**/login.html", timeout=5000)
