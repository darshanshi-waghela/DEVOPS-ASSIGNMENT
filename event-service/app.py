from flask import Flask, jsonify, request, abort

app = Flask(__name__)

# Starts empty - events are created at runtime via POST /events.
EVENTS = {}
next_event_id = 1


@app.route("/")
def home():
    return jsonify(service="event-service", status="running")


@app.route("/health")
def health():
    return jsonify(status="UP"), 200


# ---- Create ----
@app.route("/events", methods=["POST"])
def create_event():
    global next_event_id
    data = request.get_json(force=True, silent=True) or {}
    name = data.get("name")
    venue = data.get("venue")
    date = data.get("date")
    total_seats = data.get("total_seats")

    if not name or not venue or not date or total_seats is None:
        abort(400, description="name, venue, date and total_seats are required")

    event = {
        "id": next_event_id,
        "name": name,
        "venue": venue,
        "date": date,
        "total_seats": total_seats,
        "available_seats": total_seats,
    }
    EVENTS[next_event_id] = event
    next_event_id += 1
    return jsonify(event), 201


# ---- Read (all) ----
@app.route("/events", methods=["GET"])
def get_events():
    return jsonify(list(EVENTS.values()))


# ---- Read (one) ----
@app.route("/events/<int:event_id>", methods=["GET"])
def get_event(event_id):
    event = EVENTS.get(event_id)
    if not event:
        abort(404, description="Event not found")
    return jsonify(event)


# ---- Update (general edits, e.g. name/venue/date) ----
@app.route("/events/<int:event_id>", methods=["PUT"])
def update_event(event_id):
    event = EVENTS.get(event_id)
    if not event:
        abort(404, description="Event not found")

    data = request.get_json(force=True, silent=True) or {}
    for field in ("name", "venue", "date", "total_seats"):
        if field in data:
            event[field] = data[field]

    return jsonify(event)


# ---- Seat reservation (called by booking-service) ----
@app.route("/events/<int:event_id>/reserve", methods=["PUT"])
def reserve_seats(event_id):
    event = EVENTS.get(event_id)
    if not event:
        abort(404, description="Event not found")

    data = request.get_json(force=True, silent=True) or {}
    seats = data.get("seats")
    if seats is None or seats <= 0:
        abort(400, description="'seats' must be a positive number")

    if event["available_seats"] < seats:
        abort(409, description="Not enough available seats")

    event["available_seats"] -= seats
    return jsonify(event)


# ---- Seat release (called when a booking is cancelled) ----
@app.route("/events/<int:event_id>/release", methods=["PUT"])
def release_seats(event_id):
    event = EVENTS.get(event_id)
    if not event:
        abort(404, description="Event not found")

    data = request.get_json(force=True, silent=True) or {}
    seats = data.get("seats")
    if seats is None or seats <= 0:
        abort(400, description="'seats' must be a positive number")

    event["available_seats"] = min(event["total_seats"], event["available_seats"] + seats)
    return jsonify(event)


# ---- Delete ----
@app.route("/events/<int:event_id>", methods=["DELETE"])
def delete_event(event_id):
    event = EVENTS.pop(event_id, None)
    if not event:
        abort(404, description="Event not found")
    return jsonify(message=f"Event {event_id} deleted"), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=6001)
