from flask import Flask, jsonify, request, abort

app = Flask(__name__)

# Starts empty - customers are created at runtime via POST /customers.
CUSTOMERS = {}
next_customer_id = 1


@app.route("/")
def home():
    return jsonify(service="customer-service", status="running")


@app.route("/health")
def health():
    return jsonify(status="UP"), 200


# ---- Create ----
@app.route("/customers", methods=["POST"])
def create_customer():
    global next_customer_id
    data = request.get_json(force=True, silent=True) or {}
    name = data.get("name")
    email = data.get("email")
    phone = data.get("phone")

    if not name or not email:
        abort(400, description="'name' and 'email' are required")

    customer = {"id": next_customer_id, "name": name, "email": email, "phone": phone}
    CUSTOMERS[next_customer_id] = customer
    next_customer_id += 1
    return jsonify(customer), 201


# ---- Read (all) ----
@app.route("/customers", methods=["GET"])
def get_customers():
    return jsonify(list(CUSTOMERS.values()))


# ---- Read (one) ----
@app.route("/customers/<int:customer_id>", methods=["GET"])
def get_customer(customer_id):
    customer = CUSTOMERS.get(customer_id)
    if not customer:
        abort(404, description="Customer not found")
    return jsonify(customer)


# ---- Update ----
@app.route("/customers/<int:customer_id>", methods=["PUT"])
def update_customer(customer_id):
    customer = CUSTOMERS.get(customer_id)
    if not customer:
        abort(404, description="Customer not found")

    data = request.get_json(force=True, silent=True) or {}
    for field in ("name", "email", "phone"):
        if field in data:
            customer[field] = data[field]

    return jsonify(customer)


# ---- Delete ----
@app.route("/customers/<int:customer_id>", methods=["DELETE"])
def delete_customer(customer_id):
    customer = CUSTOMERS.pop(customer_id, None)
    if not customer:
        abort(404, description="Customer not found")
    return jsonify(message=f"Customer {customer_id} deleted"), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=6002)
