import os
from flask import Flask, jsonify, request, abort
import requests

app = Flask(__name__)

CUSTOMER_SERVICE_URL = os.environ.get("CUSTOMER_SERVICE_URL", "http://customer-service:6002")
EVENT_SERVICE_URL = os.environ.get("EVENT_SERVICE_URL", "http://event-service:6001")

BOOKINGS = {}
next_booking_id = 1


@app.route("/")
def home():
    return jsonify(service="booking-service", status="running")


@app.route("/health")
def health():
    return jsonify(status="UP"), 200


@app.route("/bookings", methods=["POST"])
def create_booking():
    global next_booking_id
    data = request.get_json(force=True, silent=True) or {}
    customer_id = data.get("customer_id")
    event_id = data.get("event_id")
    seats = data.get("seats")

    if customer_id is None or event_id is None or not seats:
        abort(400, description="customer_id, event_id and seats are required")

    # --- Call #1: validate the customer exists ---
    try:
        customer_resp = requests.get(f"{CUSTOMER_SERVICE_URL}/customers/{customer_id}", timeout=5)
    except requests.exceptions.RequestException:
        abort(503, description="customer-service is unavailable")
    if customer_resp.status_code != 200:
        abort(404, description="Customer not found in customer-service")
    customer = customer_resp.json()

    # --- Call #2: check the event exists ---
    try:
        event_resp = requests.get(f"{EVENT_SERVICE_URL}/events/{event_id}", timeout=5)
    except requests.exceptions.RequestException:
        abort(503, description="event-service is unavailable")
    if event_resp.status_code != 200:
        abort(404, description="Event not found in event-service")

    # --- Call #3: reserve the seats (a real WRITE on another service) ---
    try:
        reserve_resp = requests.put(
            f"{EVENT_SERVICE_URL}/events/{event_id}/reserve",
            json={"seats": seats},
            timeout=5,
        )
    except requests.exceptions.RequestException:
        abort(503, description="event-service is unavailable")
    if reserve_resp.status_code == 409:
        abort(409, description="Not enough available seats for this event")
    if reserve_resp.status_code != 200:
        abort(502, description="Failed to reserve seats")
    event = reserve_resp.json()

    booking = {
        "booking_id": next_booking_id,
        "customer": customer,
        "event": event,
        "seats_booked": seats,
        "status": "CONFIRMED",
    }
    BOOKINGS[next_booking_id] = booking
    next_booking_id += 1
    return jsonify(booking), 201


@app.route("/bookings", methods=["GET"])
def get_bookings():
    return jsonify(list(BOOKINGS.values()))


@app.route("/bookings/<int:booking_id>", methods=["GET"])
def get_booking(booking_id):
    booking = BOOKINGS.get(booking_id)
    if not booking:
        abort(404, description="Booking not found")
    return jsonify(booking)


@app.route("/bookings/<int:booking_id>", methods=["DELETE"])
def cancel_booking(booking_id):
    booking = BOOKINGS.get(booking_id)
    if not booking:
        abort(404, description="Booking not found")

    # Give the seats back on event-service before removing the booking.
    try:
        requests.put(
            f"{EVENT_SERVICE_URL}/events/{booking['event']['id']}/release",
            json={"seats": booking["seats_booked"]},
            timeout=5,
        )
    except requests.exceptions.RequestException:
        pass  # best-effort release; booking is still cancelled locally

    del BOOKINGS[booking_id]
    return jsonify(message=f"Booking {booking_id} cancelled, seats released"), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=6003)
