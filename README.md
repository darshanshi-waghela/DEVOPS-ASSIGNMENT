# Ticket Booking Microservices Project

A 3-microservice ticket booking application demonstrating a complete DevOps
pipeline: version control, CI, Docker containerization, and CD.

## Architecture

```
        POST /bookings {customer_id, event_id, seats}
                        |
                        v
                +------------------+
                | booking-service  | :6003
                +------------------+
                 |                |
     GET /customers/<id>    GET /events/<id>
        |                        |
        v                    PUT /events/<id>/reserve  (writes back!)
+------------------+        +----------------+
| customer-service |        | event-service  |
|      :6002       |        |     :6001      |
+------------------+        +----------------+
```

- **event-service** - owns events (name, venue, date, total seats, available
  seats). Full CRUD, plus `/reserve` and `/release` endpoints used by
  booking-service to adjust seat counts.
- **customer-service** - owns customer records (name, email, phone). Full
  CRUD.
- **booking-service** - exposes `POST /bookings`. To confirm a booking it:
  1. Calls customer-service to confirm the customer exists
  2. Calls event-service to confirm the event exists
  3. Calls event-service's `/reserve` endpoint to actually **decrease the
     available seat count** - a real write on another service, not just a
     read. Cancelling a booking (`DELETE /bookings/<id>`) calls `/release` to
     give the seats back.

This is a stronger proof of inter-service communication than a simple
read-only lookup, since one service is genuinely changing another service's
data over the network.

## Running locally with Docker

```bash
docker compose up --build
```

## Demo flow

```bash
# 1. Create an event
curl -X POST http://localhost:6001/events -H "Content-Type: application/json" -d "{\"name\": \"Coldplay Live\", \"venue\": \"DY Patil Stadium\", \"date\": \"2026-12-01\", \"total_seats\": 100}"

# 2. Create a customer
curl -X POST http://localhost:6002/customers -H "Content-Type: application/json" -d "{\"name\": \"Aarav Shah\", \"email\": \"aarav@example.com\", \"phone\": \"9999999999\"}"

# 3. Book tickets
curl -X POST http://localhost:6003/bookings -H "Content-Type: application/json" -d "{\"customer_id\": 1, \"event_id\": 1, \"seats\": 5}"

# 4. Check the event - available_seats has dropped from 100 to 95
curl http://localhost:6001/events/1

# 5. Cancel the booking - seats are returned
curl -X DELETE http://localhost:6003/bookings/1
curl http://localhost:6001/events/1
```

PowerShell equivalent for step 3:
```powershell
Invoke-WebRequest -Uri http://localhost:6003/bookings -Method POST -ContentType "application/json" -Body '{"customer_id": 1, "event_id": 1, "seats": 5}'
```

## Running tests directly

```bash
cd event-service && pip install -r requirements.txt && pytest
cd customer-service && pip install -r requirements.txt && pytest
cd booking-service && pip install -r requirements.txt && pytest
```

## CI/CD Pipeline

Same structure as the earlier microservices project: Checkout -> Test (x3) ->
Build Docker Images -> Deploy, defined in the `Jenkinsfile`. Update the `git`
URL in the Checkout stage to your own repository before running it in
Jenkins.

## Syllabus mapping

| Unit | Covered by |
|---|---|
| I - Version control | Git repo, Plan->Code->Build->Test->Deploy flow |
| II - CI, artifact management | Jenkinsfile: automated test + build per service, images tagged by build number |
| III - CD, environment management | Deploy stage; `CUSTOMER_SERVICE_URL`/`EVENT_SERVICE_URL` env vars |
| IV - Containerization | One Dockerfile per service, Docker Compose network, service discovery by name |
| V - Monitoring (extension) | Each service exposes `/health` |
