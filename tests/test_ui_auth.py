from fastapi.testclient import TestClient


def login(client: TestClient, username: str = "admin", password: str = "change-me") -> None:
    client.post(
        "/ui/login",
        data={"username": username, "password": password},
        allow_redirects=True,
    )


def test_dashboard_requires_login(client: TestClient):
    response = client.get("/", allow_redirects=False)
    assert response.status_code in (302, 307)
    assert response.headers.get("Location", "").endswith("/ui/login")


def test_login_with_valid_credentials_sets_session(client: TestClient):
    response = client.post(
        "/ui/login",
        data={"username": "admin", "password": "change-me"},
        allow_redirects=False,
    )
    assert response.status_code in (302, 303)
    assert "session" in client.cookies


def test_authenticated_user_can_access_dashboard(client: TestClient):
    login(client)
    response = client.get("/")
    assert response.status_code == 200
    assert "Dashboard" in response.text


def test_logout_clears_session(client: TestClient):
    login(client)
    assert "session" in client.cookies

    response = client.get("/ui/logout", allow_redirects=False)
    assert response.status_code in (302, 303)

    response = client.get("/", allow_redirects=False)
    assert response.status_code in (302, 307)
    assert response.headers.get("Location", "").endswith("/ui/login")
