from fastapi.testclient import TestClient


def create_account_payload():
    return {
        "display_name": "Sender",
        "email_address": "sender@example.com",
        "smtp_host": "smtp.example.com",
        "smtp_port": 587,
        "smtp_username": "user",
        "smtp_password_encrypted": "pass",
        "use_ssl": False,
        "use_tls": True,
    }


def test_create_and_get_account(client: TestClient):
    payload = create_account_payload()
    create_resp = client.post("/accounts/", json=payload)
    assert create_resp.status_code == 201
    created = create_resp.json()
    assert created["display_name"] == payload["display_name"]
    assert created["email_address"] == payload["email_address"]

    get_resp = client.get(f"/accounts/{created['id']}")
    assert get_resp.status_code == 200
    fetched = get_resp.json()
    assert fetched["id"] == created["id"]
    assert fetched["email_address"] == payload["email_address"]


def test_create_contact_and_filter_by_tag(client: TestClient):
    contacts = [
        {"email": "client@example.com", "name": "Client", "tags": "clients"},
        {"email": "lead@example.com", "name": "Lead", "tags": "leads"},
    ]
    for contact in contacts:
        resp = client.post("/contacts/", json=contact)
        assert resp.status_code == 201

    filtered = client.get("/contacts", params={"tag": "clients"})
    assert filtered.status_code == 200
    results = filtered.json()
    assert len(results) == 1
    assert results[0]["email"] == "client@example.com"


def test_create_template_and_preview(client: TestClient):
    template_payload = {
        "name": "Welcome",
        "subject": "Hello {{ name }}",
        "body_html": "<p>Hi {{ name }}</p>",
        "body_text": "Hi {{ name }}",
    }
    resp = client.post("/templates/", json=template_payload)
    assert resp.status_code == 201
    template = resp.json()

    preview = client.post(
        f"/templates/{template['id']}/preview",
        json={"context": {"name": "Alice"}},
    )
    assert preview.status_code == 200
    rendered = preview.json()
    assert "Alice" in rendered["subject"]
    assert "Alice" in rendered["body_html"]


def test_create_campaign_and_list(client: TestClient):
    account_resp = client.post("/accounts/", json=create_account_payload())
    template_resp = client.post(
        "/templates/",
        json={
            "name": "Promo",
            "subject": "Sale",
            "body_html": "<p>Sale</p>",
            "body_text": "Sale",
        },
    )
    assert account_resp.status_code == 201
    assert template_resp.status_code == 201
    account_id = account_resp.json()["id"]
    template_id = template_resp.json()["id"]

    campaign_payload = {
        "name": "Campaign",
        "account_id": account_id,
        "template_id": template_id,
        "schedule_type": "recurring",
        "schedule_config": {"freq": "daily", "hour": 0, "minute": 0},
        "target_tags": "clients",
        "active": True,
    }

    create_campaign = client.post("/campaigns/", json=campaign_payload)
    assert create_campaign.status_code == 201

    list_resp = client.get("/campaigns/")
    assert list_resp.status_code == 200
    campaigns = list_resp.json()
    assert any(camp["name"] == "Campaign" for camp in campaigns)
