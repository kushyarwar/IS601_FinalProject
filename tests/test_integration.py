"""
Integration tests for all API routes: auth, BREAD, profile, password change, and reports.
"""
import pytest


def _register(client, username="testuser", email=None, password="pass1234"):
    if email is None:
        email = f"{username}@example.com"
    res = client.post("/users/register", json={
        "username": username,
        "email": email,
        "password": password,
    })
    assert res.status_code == 201, res.text
    data = res.json()
    return data["user"]["id"], data["token"]


def _headers(token):
    return {"Authorization": f"Bearer {token}"}


def _add_calc(client, token, a=10, b=5, op="Add"):
    res = client.post(
        "/calculations",
        json={"a": a, "b": b, "type": op},
        headers=_headers(token),
    )
    assert res.status_code == 201, res.text
    return res.json()


# ── Auth Tests ─────────────────────────────────────────────────────────────

def test_register_and_login_return_jwt(client):
    res = client.post("/users/register", json={"email": "alice@example.com", "password": "secret123"})
    assert res.status_code == 201
    data = res.json()
    assert data["user"]["username"] == "alice"
    assert len(data["token"].split(".")) == 3

    login = client.post("/users/login", json={"email": "alice@example.com", "password": "secret123"})
    assert login.status_code == 200
    assert len(login.json()["token"].split(".")) == 3


def test_register_rejects_duplicate_email(client):
    _register(client, "dup1", "dup@example.com")
    res = client.post("/users/register", json={"email": "dup@example.com", "password": "pass1234"})
    assert res.status_code == 400


def test_login_rejects_wrong_password(client):
    _register(client, "wrongpass", password="correct123")
    res = client.post("/users/login", json={"email": "wrongpass@example.com", "password": "badpass123"})
    assert res.status_code == 401


def test_invalid_token_rejected(client):
    res = client.get("/calculations", headers={"Authorization": "Bearer bad-token"})
    assert res.status_code == 401


# ── Calculation BREAD Tests ────────────────────────────────────────────────

def test_add_calculation_correct_result(client):
    _, token = _register(client, "calc_owner")
    data = _add_calc(client, token, 10, 5, "Add")
    assert data["result"] == 15.0
    assert data["a"] == 10.0
    assert data["type"] == "Add"


def test_all_six_operations(client):
    _, token = _register(client, "ops_user")
    assert _add_calc(client, token, 9, 4, "Sub")["result"] == 5.0
    assert _add_calc(client, token, 6, 7, "Multiply")["result"] == 42.0
    assert _add_calc(client, token, 15, 3, "Divide")["result"] == 5.0
    assert _add_calc(client, token, 2, 8, "Power")["result"] == 256.0
    assert _add_calc(client, token, 10, 3, "Modulus")["result"] == 1.0


def test_browse_returns_only_own_calculations(client):
    _, token_a = _register(client, "owner_a")
    _, token_b = _register(client, "owner_b")
    own = _add_calc(client, token_a, 1, 2, "Add")
    _add_calc(client, token_b, 9, 9, "Multiply")

    res = client.get("/calculations", headers=_headers(token_a))
    assert res.status_code == 200
    rows = res.json()
    assert len(rows) == 1
    assert rows[0]["id"] == own["id"]


def test_read_calculation_by_id(client):
    _, token = _register(client, "reader")
    created = _add_calc(client, token, 4, 4, "Add")
    res = client.get(f"/calculations/{created['id']}", headers=_headers(token))
    assert res.status_code == 200
    assert res.json()["result"] == 8.0


def test_read_other_users_calculation_returns_404(client):
    _, owner_token = _register(client, "real_owner")
    _, other_token = _register(client, "other_user")
    created = _add_calc(client, owner_token, 4, 4, "Add")
    res = client.get(f"/calculations/{created['id']}", headers=_headers(other_token))
    assert res.status_code == 404


def test_edit_calculation_recomputes_result(client):
    _, token = _register(client, "editor")
    created = _add_calc(client, token, 10, 2, "Add")
    res = client.put(
        f"/calculations/{created['id']}",
        json={"a": 20, "b": 4, "type": "Divide"},
        headers=_headers(token),
    )
    assert res.status_code == 200
    assert res.json()["result"] == 5.0


def test_patch_calculation_partial_update(client):
    _, token = _register(client, "patcher")
    created = _add_calc(client, token, 6, 3, "Add")
    res = client.patch(
        f"/calculations/{created['id']}",
        json={"type": "Multiply"},
        headers=_headers(token),
    )
    assert res.status_code == 200
    assert res.json()["result"] == 18.0


def test_delete_calculation(client):
    _, token = _register(client, "deleter")
    created = _add_calc(client, token, 2, 2, "Multiply")
    del_res = client.delete(f"/calculations/{created['id']}", headers=_headers(token))
    read_res = client.get(f"/calculations/{created['id']}", headers=_headers(token))
    assert del_res.status_code == 204
    assert read_res.status_code == 404


def test_delete_other_users_calculation_returns_404(client):
    _, owner_token = _register(client, "delete_owner")
    _, other_token = _register(client, "delete_other")
    created = _add_calc(client, owner_token, 8, 2, "Divide")
    res = client.delete(f"/calculations/{created['id']}", headers=_headers(other_token))
    assert res.status_code == 404


def test_calculation_routes_require_auth(client):
    assert client.get("/calculations").status_code == 401
    assert client.post("/calculations", json={"a": 1, "b": 2, "type": "Add"}).status_code == 401
    assert client.get("/calculations/1").status_code == 401
    assert client.put("/calculations/1", json={"a": 3}).status_code == 401
    assert client.delete("/calculations/1").status_code == 401


def test_invalid_operation_type_rejected(client):
    _, token = _register(client, "badtype")
    res = client.post("/calculations", json={"a": 5, "b": 3, "type": "InvalidOp"}, headers=_headers(token))
    assert res.status_code == 422


def test_divide_by_zero_rejected(client):
    _, token = _register(client, "divzero")
    res = client.post("/calculations", json={"a": 5, "b": 0, "type": "Divide"}, headers=_headers(token))
    assert res.status_code == 422


def test_modulus_by_zero_rejected(client):
    _, token = _register(client, "modzero")
    res = client.post("/calculations", json={"a": 5, "b": 0, "type": "Modulus"}, headers=_headers(token))
    assert res.status_code == 422


def test_delete_user_cascades_calculations(client):
    user_id, token = _register(client, "cascade_user")
    _add_calc(client, token, 5, 5, "Add")
    assert client.delete(f"/users/{user_id}").status_code == 204
    assert client.get("/calculations", headers=_headers(token)).status_code == 401


# ── Profile Feature Tests ──────────────────────────────────────────────────

def test_get_profile_returns_user_info(client):
    _, token = _register(client, "profuser")
    res = client.get("/users/me/profile", headers=_headers(token))
    assert res.status_code == 200
    data = res.json()
    assert data["username"] == "profuser"
    assert data["email"] == "profuser@example.com"


def test_update_profile_username(client):
    _, token = _register(client, "oldname")
    res = client.put(
        "/users/me/profile",
        json={"username": "newname"},
        headers=_headers(token),
    )
    assert res.status_code == 200
    assert res.json()["username"] == "newname"


def test_update_profile_bio(client):
    _, token = _register(client, "biouser")
    res = client.put(
        "/users/me/profile",
        json={"bio": "I love math!"},
        headers=_headers(token),
    )
    assert res.status_code == 200
    assert res.json()["bio"] == "I love math!"


def test_update_profile_duplicate_username_rejected(client):
    _register(client, "taken_name")
    _, token = _register(client, "other_user")
    res = client.put(
        "/users/me/profile",
        json={"username": "taken_name"},
        headers=_headers(token),
    )
    assert res.status_code == 400


def test_change_password_success(client):
    _, token = _register(client, "pwuser", password="OldPass123")
    res = client.post(
        "/users/me/change-password",
        json={"current_password": "OldPass123", "new_password": "NewPass456"},
        headers=_headers(token),
    )
    assert res.status_code == 200
    assert "success" in res.json()["message"].lower()


def test_change_password_wrong_current(client):
    _, token = _register(client, "pwbad", password="CorrectPass1")
    res = client.post(
        "/users/me/change-password",
        json={"current_password": "WrongPass1", "new_password": "NewPass456"},
        headers=_headers(token),
    )
    assert res.status_code == 400


def test_change_password_then_login_with_new(client):
    _, token = _register(client, "pwlogin", password="OldPass123")
    client.post(
        "/users/me/change-password",
        json={"current_password": "OldPass123", "new_password": "NewPass456"},
        headers=_headers(token),
    )
    login = client.post("/users/login", json={"email": "pwlogin@example.com", "password": "NewPass456"})
    assert login.status_code == 200


def test_profile_routes_require_auth(client):
    assert client.get("/users/me/profile").status_code == 401
    assert client.put("/users/me/profile", json={"bio": "test"}).status_code == 401
    assert client.post("/users/me/change-password", json={
        "current_password": "a", "new_password": "b"
    }).status_code == 401


# ── Reports Tests ──────────────────────────────────────────────────────────

def test_report_empty_for_new_user(client):
    _, token = _register(client, "empty_reporter")
    res = client.get("/reports/summary", headers=_headers(token))
    assert res.status_code == 200
    data = res.json()
    assert data["total_calculations"] == 0
    assert data["most_used_operation"] is None
    assert data["last_calculation"] is None


def test_report_counts_calculations(client):
    _, token = _register(client, "report_counter")
    _add_calc(client, token, 1, 2, "Add")
    _add_calc(client, token, 3, 4, "Add")
    _add_calc(client, token, 2, 3, "Multiply")

    res = client.get("/reports/summary", headers=_headers(token))
    assert res.status_code == 200
    data = res.json()
    assert data["total_calculations"] == 3
    assert data["most_used_operation"] == "Add"
    assert data["operation_counts"]["Add"] == 2
    assert data["operation_counts"]["Multiply"] == 1


def test_report_average_result(client):
    _, token = _register(client, "avg_reporter")
    _add_calc(client, token, 10, 0, "Add")
    _add_calc(client, token, 20, 0, "Add")

    res = client.get("/reports/summary", headers=_headers(token))
    assert res.status_code == 200
    assert res.json()["average_result"] == pytest.approx(15.0, abs=0.01)


def test_report_last_calculation(client):
    _, token = _register(client, "last_reporter")
    _add_calc(client, token, 5, 3, "Add")
    last = _add_calc(client, token, 9, 9, "Multiply")

    res = client.get("/reports/summary", headers=_headers(token))
    data = res.json()
    assert data["last_calculation"]["id"] == last["id"]
    assert data["last_calculation"]["result"] == 81.0


def test_report_requires_auth(client):
    assert client.get("/reports/summary").status_code == 401


# ── Health Check ───────────────────────────────────────────────────────────

def test_health_endpoint(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}
