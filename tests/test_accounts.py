def test_create_and_get_account(client):
    payload = {
        "display_name": "Test Account",
        "email_address": "test@example.com",
        "smtp_host": "smtp.example.com",
        "smtp_port": 587,
        "smtp_username": "user",
        "smtp_password_encrypted": "pass",
        "use_ssl": False,
        "use_tls": True,
    }

    create_resp = client.post("/accounts/", json=payload)
    assert create_resp.status_code == 201
    account_id = create_resp.json()["id"]

    get_resp = client.get(f"/accounts/{account_id}")
    data = get_resp.json()
    assert get_resp.status_code == 200
    assert data["email_address"] == payload["email_address"]

    list_resp = client.get("/accounts/")
    assert list_resp.status_code == 200
    assert any(acc["id"] == account_id for acc in list_resp.json())
