import pytest
from app import app, EVENTS


@pytest.fixture
def client():
    app.config["TESTING"] = True
    EVENTS.clear()
    with app.test_client() as client:
        yield client


def _create_event(client, total_seats=100):
    return client.post(
        "/events",
        json={"name": "Coldplay Live", "venue": "DY Patil Stadium", "date": "2026-12-01", "total_seats": total_seats},
    ).get_json()


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "UP"


def test_get_events_empty(client):
    resp = client.get("/events")
    assert resp.status_code == 200
    assert resp.get_json() == []


def test_create_event(client):
    event = _create_event(client)
    assert event["name"] == "Coldplay Live"
    assert event["available_seats"] == 100


def test_create_event_missing_fields(client):
    resp = client.post("/events", json={"name": "Only Name"})
    assert resp.status_code == 400


def test_get_event_not_found(client):
    resp = client.get("/events/999")
    assert resp.status_code == 404


def test_update_event(client):
    event = _create_event(client)
    resp = client.put(f"/events/{event['id']}", json={"venue": "Wankhede Stadium"})
    assert resp.status_code == 200
    assert resp.get_json()["venue"] == "Wankhede Stadium"


def test_reserve_seats_success(client):
    event = _create_event(client, total_seats=50)
    resp = client.put(f"/events/{event['id']}/reserve", json={"seats": 5})
    assert resp.status_code == 200
    assert resp.get_json()["available_seats"] == 45


def test_reserve_seats_not_enough(client):
    event = _create_event(client, total_seats=3)
    resp = client.put(f"/events/{event['id']}/reserve", json={"seats": 10})
    assert resp.status_code == 409


def test_release_seats(client):
    event = _create_event(client, total_seats=50)
    client.put(f"/events/{event['id']}/reserve", json={"seats": 5})
    resp = client.put(f"/events/{event['id']}/release", json={"seats": 5})
    assert resp.status_code == 200
    assert resp.get_json()["available_seats"] == 50


def test_delete_event(client):
    event = _create_event(client)
    resp = client.delete(f"/events/{event['id']}")
    assert resp.status_code == 200
    resp2 = client.get(f"/events/{event['id']}")
    assert resp2.status_code == 404
