def test_create_and_list_contacts(client):
    payload = {
        "email": "contact@example.com",
        "name": "Example Contact",
        "tags": "news,customer",
    }

    resp = client.post("/contacts/", json=payload)
    assert resp.status_code == 201

    list_resp = client.get("/contacts/?tag=news")
    assert list_resp.status_code == 200
    contacts = list_resp.json()
    assert len(contacts) == 1
    assert contacts[0]["email"] == payload["email"]
