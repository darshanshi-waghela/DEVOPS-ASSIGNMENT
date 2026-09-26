import pytest
from app import app, CUSTOMERS


@pytest.fixture
def client():
    app.config["TESTING"] = True
    CUSTOMERS.clear()
    with app.test_client() as client:
        yield client


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "UP"


def test_get_customers_empty(client):
    resp = client.get("/customers")
    assert resp.status_code == 200
    assert resp.get_json() == []


def test_create_customer(client):
    resp = client.post("/customers", json={"name": "Aarav Shah", "email": "aarav@example.com", "phone": "9999999999"})
    assert resp.status_code == 201
    body = resp.get_json()
    assert body["name"] == "Aarav Shah"
    assert "id" in body


def test_create_customer_missing_fields(client):
    resp = client.post("/customers", json={"name": "Only Name"})
    assert resp.status_code == 400


def test_get_customer_found(client):
    created = client.post("/customers", json={"name": "Priya Mehta", "email": "priya@example.com"}).get_json()
    resp = client.get(f"/customers/{created['id']}")
    assert resp.status_code == 200
    assert resp.get_json()["name"] == "Priya Mehta"


def test_get_customer_not_found(client):
    resp = client.get("/customers/999")
    assert resp.status_code == 404


def test_update_customer(client):
    created = client.post("/customers", json={"name": "Rohan", "email": "rohan@example.com"}).get_json()
    resp = client.put(f"/customers/{created['id']}", json={"phone": "8888888888"})
    assert resp.status_code == 200
    assert resp.get_json()["phone"] == "8888888888"


def test_delete_customer(client):
    created = client.post("/customers", json={"name": "Temp", "email": "temp@example.com"}).get_json()
    resp = client.delete(f"/customers/{created['id']}")
    assert resp.status_code == 200
    resp2 = client.get(f"/customers/{created['id']}")
    assert resp2.status_code == 404


def test_delete_customer_not_found(client):
    resp = client.delete("/customers/999")
    assert resp.status_code == 404
