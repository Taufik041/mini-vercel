import pytest

pytestmark = pytest.mark.anyio


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------


async def test_health_check_returns_ok(client):
    response = await client.get("/auth/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# Signup
# ---------------------------------------------------------------------------


async def test_signup_with_valid_data_returns_201(client):
    response = await client.post(
        "/auth/signup",
        json={
            "name": "New User",
            "email": "newuser@example.com",
            "creds": 5.0,
            "password": "password123",
            "confirm_password": "password123",
        },
    )
    assert response.status_code == 201


async def test_signup_with_duplicate_email_returns_400(client, existing_user):
    response = await client.post(
        "/auth/signup",
        json={
            "name": "Duplicate",
            "email": existing_user.email,
            "creds": 5.0,
            "password": "password123",
            "confirm_password": "password123",
        },
    )
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


async def test_signup_with_mismatched_passwords_returns_400(client):
    response = await client.post(
        "/auth/signup",
        json={
            "name": "User",
            "email": "mismatch@example.com",
            "creds": 5.0,
            "password": "password123",
            "confirm_password": "different456",
        },
    )
    assert response.status_code == 400
    assert "passwords don't match" in response.json()["detail"]


async def test_signup_with_missing_name_returns_422(client):
    response = await client.post(
        "/auth/signup",
        json={
            "email": "noname@example.com",
            "creds": 5.0,
            "password": "password123",
            "confirm_password": "password123",
        },
    )
    assert response.status_code == 422


async def test_signup_with_missing_email_returns_422(client):
    response = await client.post(
        "/auth/signup",
        json={
            "name": "No Email",
            "creds": 5.0,
            "password": "password123",
            "confirm_password": "password123",
        },
    )
    assert response.status_code == 422


async def test_signup_with_missing_confirm_password_returns_422(client):
    response = await client.post(
        "/auth/signup",
        json={
            "name": "User",
            "email": "noconfirm@example.com",
            "creds": 5.0,
            "password": "password123",
        },
    )
    assert response.status_code == 422


async def test_signup_with_invalid_email_format_returns_422(client):
    response = await client.post(
        "/auth/signup",
        json={
            "name": "User",
            "email": "not-an-email",
            "creds": 5.0,
            "password": "password123",
            "confirm_password": "password123",
        },
    )
    assert response.status_code == 422


async def test_signup_with_empty_body_returns_422(client):
    response = await client.post("/auth/signup", json={})
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------


async def test_login_with_valid_credentials_returns_bearer_token(client, existing_user):
    response = await client.post(
        "/auth/login",
        data={
            "username": existing_user.email,
            "password": "correctpassword",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"
    assert len(body["access_token"]) > 0


async def test_login_with_wrong_password_returns_404(client, existing_user):
    response = await client.post(
        "/auth/login",
        data={
            "username": existing_user.email,
            "password": "wrongpassword",
        },
    )
    assert response.status_code == 404
    assert "incorrect password" in response.json()["detail"]


async def test_login_with_nonexistent_email_returns_404(client):
    response = await client.post(
        "/auth/login",
        data={
            "username": "ghost@example.com",
            "password": "anypassword",
        },
    )
    assert response.status_code == 404
    assert "User not found" in response.json()["detail"]


async def test_login_with_missing_username_returns_422(client):
    response = await client.post(
        "/auth/login",
        data={
            "password": "password123",
        },
    )
    assert response.status_code == 422


async def test_login_with_missing_password_returns_422(client):
    response = await client.post(
        "/auth/login",
        data={
            "username": "user@example.com",
        },
    )
    assert response.status_code == 422


async def test_login_with_empty_form_returns_422(client):
    response = await client.post("/auth/login", data={})
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------


async def test_logout_with_valid_token_returns_200(authenticated_client):
    response = await authenticated_client.post("/auth/logout")
    assert response.status_code == 200


async def test_logout_without_token_returns_401(client):
    response = await client.post("/auth/logout")
    assert response.status_code == 401


async def test_logout_with_invalid_token_returns_401(client):
    client.headers.update({"Authorization": "Bearer invalid.jwt.token"})
    response = await client.post("/auth/logout")
    assert response.status_code == 401
    assert "Invalid token" in response.json()["detail"]


async def test_logout_with_garbled_bearer_value_returns_401(client):
    client.headers.update({"Authorization": "Bearer !!notbase64!!"})
    response = await client.post("/auth/logout")
    assert response.status_code == 401


async def test_logout_with_wrong_auth_scheme_returns_401(client):
    client.headers.update({"Authorization": "Basic dXNlcjpwYXNz"})
    response = await client.post("/auth/logout")
    assert response.status_code == 401
