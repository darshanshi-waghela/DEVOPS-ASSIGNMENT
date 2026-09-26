import pytest
from unittest.mock import patch, Mock
import app as app_module

app = app_module.app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    app_module.BOOKINGS.clear()
    with app.test_client() as client:
        yield client


def _fake_response(status_code, json_data):
    resp = Mock()
    resp.status_code = status_code
    resp.json.return_value = json_data
    return resp


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "UP"


@patch("app.requests.put")
@patch("app.requests.get")
def test_create_booking_success(mock_get, mock_put, client):
    mock_get.side_effect = [
        _fake_response(200, {"id": 1, "name": "Aarav Shah"}),
        _fake_response(200, {"id": 1, "name": "Coldplay Live", "available_seats": 100}),
    ]
    mock_put.return_value = _fake_response(200, {"id": 1, "name": "Coldplay Live", "available_seats": 98})

    resp = client.post("/bookings", json={"customer_id": 1, "event_id": 1, "seats": 2})
    assert resp.status_code == 201
    body = resp.get_json()
    assert body["status"] == "CONFIRMED"
    assert body["seats_booked"] == 2
    assert body["customer"]["name"] == "Aarav Shah"


@patch("app.requests.get")
def test_create_booking_customer_not_found(mock_get, client):
    mock_get.side_effect = [_fake_response(404, {})]
    resp = client.post("/bookings", json={"customer_id": 999, "event_id": 1, "seats": 2})
    assert resp.status_code == 404


@patch("app.requests.put")
@patch("app.requests.get")
def test_create_booking_not_enough_seats(mock_get, mock_put, client):
    mock_get.side_effect = [
        _fake_response(200, {"id": 1, "name": "Aarav Shah"}),
        _fake_response(200, {"id": 1, "name": "Coldplay Live", "available_seats": 1}),
    ]
    mock_put.return_value = _fake_response(409, {})

    resp = client.post("/bookings", json={"customer_id": 1, "event_id": 1, "seats": 5})
    assert resp.status_code == 409


def test_create_booking_missing_fields(client):
    resp = client.post("/bookings", json={})
    assert resp.status_code == 400


def test_get_bookings_empty(client):
    resp = client.get("/bookings")
    assert resp.status_code == 200
    assert resp.get_json() == []
