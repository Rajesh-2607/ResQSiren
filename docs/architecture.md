# resQ Siren — Platform Architecture (v2)

This is the microservice implementation of the architecture described in the
root `README.md`, built as a separate track from the existing monolithic
prototype in `apps/api` + `apps/web-dashboard` (which is untouched and still
works on its own — see "Relationship to the v1 prototype" below).

## Layout

```
packages/shared/            # resq_shared: HMAC signing, severity constants,
                             # event schemas, Redis pub/sub wrapper, DB/WS helpers
services/
  dispatch/                 # call intake, severity scoring, dispatch creation, signing
  routing/                  # nearest-ambulance/hospital lookup, route calc (OSRM or mock)
  conflict-resolution/      # the arbitration engine — the differentiator
  signal-command/           # HMAC verification + mock ITMS pre-emption
  notifications/            # hospital/police/public alerts (mocked, logged)
apps/
  dispatcher-console/       # dispatcher's web UI — the demo centerpiece
  driver-app/                # minimal web stand-in for the ambulance driver app
  hospital-dashboard/        # minimal ER dashboard
infra/
  docker-compose.yml        # postgres, redis, and all 5 backend services
```

## Event-driven design

Per the README's core design principle, services publish facts on a shared
Redis pub/sub bus rather than calling each other to ask "what should I do":

```
dispatch  --dispatch.created-->  notifications (hospital alert)

driver / demo simulator
   --POST /signal/approaching (HMAC-signed)-->  signal-command
        signal-command verifies signature, rejects if invalid
        --ambulance.approaching.verified-->  conflict-resolution

conflict-resolution (ticks every 1s per junction)
   scores claims: score = severity_weight*100 + wait_seconds
   --arbitration.result-->  signal-command (emits mock ITMS preempt command)
   --arbitration.result-->  notifications (police + public alerts)
```

Channel names live in `resq_shared.events.Channels`. Every event is a typed
Pydantic model in `resq_shared/events.py` — that's the wire contract between
services.

### Why `+ wait_seconds`, not `-`

The root README's algorithm section states `score = severity_weight × 100 −
wait_seconds`. Taken literally, that formula makes a claim's score *fall* the
longer it waits — the opposite of the anti-starvation behavior the same
section describes ("a lower-severity ambulance that has waited long enough
eventually outranks a fresh higher-severity claim"). This implementation
uses `+ wait_seconds` to actually match that stated behavior — see
`resq_shared/severity.py:score_for` and the unit tests in
`services/conflict-resolution/tests/test_arbitration.py`.

### Trust boundary

`dispatch` and `signal-command` share `DISPATCH_HMAC_SECRET`. Only a service
holding that secret can produce a signature `signal-command` accepts —
that's what "an unsigned or spoofed ping is rejected outright" means in
practice. The driver-app never holds this secret itself: it calls
`POST /dispatch/{id}/approaching` on the *dispatch* service (its own trusted
backend), which signs the ping server-side before forwarding it to
signal-command. `services/conflict-resolution/app/demo.py` does the same
thing for the scripted demo scenario, standing in for a real driver unit.

## Running it

### Backend (Docker)

```bash
docker compose -f infra/docker-compose.yml up -d --build
```

Brings up Postgres (`localhost:5433`), Redis (`localhost:6380`), and all five
services on `localhost:4101`–`4105`. Check `GET /health` on each.

### Frontends (local dev servers)

Each app needs its own `npm install` once, then `npm run dev`:

```bash
cd apps/dispatcher-console && cp .env.example .env && npm install && npm run dev   # :5180
cd apps/driver-app          && cp .env.example .env && npm install && npm run dev   # :5181
cd apps/hospital-dashboard  && cp .env.example .env && npm install && npm run dev   # :5182
```

### Running the demo scenario

The dispatcher console's "Junction arbitration" panel has a **Simulate
convergence** control that does this for you. To trigger it directly:

```bash
curl -X POST http://localhost:4103/demo/converge -H "Content-Type: application/json" -d '{
  "junction_id": "jn-1",
  "duration_seconds": 20,
  "ambulances": [
    {"ambulance_id": "amb-1", "severity": "YELLOW", "initial_eta_seconds": 20},
    {"ambulance_id": "amb-2", "severity": "RED", "initial_eta_seconds": 22}
  ]
}'
```

Watch `GET http://localhost:4104/signal/log` (or the dispatcher console's
"Mock ITMS signal log" panel) for the pre-emption decision, and
`GET http://localhost:4105/notifications` for the resulting police/public
alerts.

### Local (non-Docker) backend dev

```bash
py -m venv .venv-platform
.venv-platform/Scripts/pip install -e packages/shared
.venv-platform/Scripts/pip install -r services/<name>/requirements.txt
cd services/<name> && cp .env.example .env
../../.venv-platform/Scripts/uvicorn app.main:app --reload --port <its port>
```

Repeat per service, or run several in separate terminals. Postgres/Redis
still need to come from `docker compose -f infra/docker-compose.yml up -d
postgres redis` (or your own local instances on the ports in each
`.env.example`).

### Tests

```bash
.venv-platform/Scripts/pytest services/conflict-resolution/tests/ -v
```

## Relationship to the v1 prototype

`apps/api` (FastAPI monolith) and `apps/web-dashboard` (citizen request +
driver tracker pages) already implement a working version of the core loop
and are unrelated to this platform — different ports (4000 vs 4101-4105),
different Postgres database, no shared code. Both can run at the same time
without conflicting. This platform is the microservice architecture
described in the README's "Suggested repo structure" and "Architecture"
sections, built out as a separate track rather than a rewrite of v1.

## Known gaps (out of scope for this pass)

- No real ABHA, Twilio, or FCM integration — `notifications` logs everything
  instead of sending it (see `services/notifications/app/senders.py`).
- No native mobile driver app — `apps/driver-app` is a web page.
- No Alembic migrations — each service creates its own Postgres schema and
  tables on startup via `create_all` (matches the v1 prototype's approach).
- `routing` falls back to straight-line distance unless `ROUTING_OSRM_BASE_URL`
  points at a real OSRM server.
