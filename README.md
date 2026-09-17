# resQ Siren — Smart Ambulance Corridor

SIH 2026 Problem Statement 25132. The product: **"I tell ResQ what happened and where I am. ResQ
takes care of getting the ambulance to me, getting me to the right hospital, showing me what is
happening, and helping the ambulance get there as quickly as possible."**

Open `http://localhost:5173/` — no login — pick what's wrong, share your location, and resQ Siren:
auto-picks the nearest available ambulance and nearest hospital, HMAC-signs the dispatch,
computes the real fastest route, generates a patient summary for the receiving hospital, and
shows you a live map with the ambulance's real GPS position as it approaches. If the hospital
can't take the patient, it auto-reroutes to the next-nearest one and updates your screen live —
no page refresh, no phone call. Severity-weighted signal pre-emption at contested junctions still
runs underneath this exactly as before.

The frontend is now caller-only by design — `/` (Emergency Request) and `/driver/:dispatchId`
(GPS-share page) are the only two pages. The backend's staff API surface (JWT login, dispatcher/
police/hospital roles, manual call+dispatch creation, junction pre-emption, hospital accept/
decline) is unchanged and still fully tested — it's just no longer fronted by a dashboard UI; see
"The original staff-triggered flow" below for exercising it directly.

| Layer | Stack |
|---|---|
| Backend framework | **FastAPI** (Python) |
| Database | **PostgreSQL** via SQLAlchemy (async) — `hospitals`, `calls`, `dispatches`, `trips` |
| Cache / live state | **Redis** — per-junction pre-emption claims, live ambulance GPS pings (30s TTL) |
| Real-time | **Socket.IO** (`python-socketio`, ASGI-mounted alongside FastAPI) |
| Auth | **JWT** (role-based: dispatcher/police/hospital/admin) **+ HMAC** dispatch-record signing — the public caller/driver endpoints are intentionally unauthenticated, same as calling 108 needs no account |
| Maps & routing | **OSRM** (public demo server by default, self-hostable), Mapbox Directions API wrapper |
| Patient summary | **Gemini API** (`gemini-2.5-flash`) — generates the ER handoff brief, falls back to a deterministic template if no key is set |
| Notifications | Twilio (SMS) wired to dispatch; **SMTP email** (patient report auto-sent to the assigned hospital's contact address on dispatch/reroute); Firebase Cloud Messaging (push) — see stub note below |
| Live GPS | Browser `navigator.geolocation` (both the caller's page and a driver-tracker page), relayed via Redis + Socket.IO, rendered with **Leaflet** + OpenStreetMap tiles |
| Infra | Dockerfile + docker-compose (Postgres, Redis, API), GitHub Actions CI |
| Web dashboard | React + Vite + TypeScript + Tailwind, `socket.io-client` |

JWT and HMAC do two different jobs:
- **JWT** authenticates a human hitting the staff API directly (`POST /auth/login`) and carries their role — dispatcher/police/hospital/admin. No dashboard fronts this anymore; it's exercised via `curl` (see below).
- **HMAC** authenticates a `Dispatch` record itself, so a junction can verify a signal-priority request really traces back to a real, unmodified dispatch — independent of who's logged in. This is what stops signal-request spoofing from the problem statement.

## Run it (Docker)

```bash
docker compose up --build
# Postgres on 5432, Redis on 6379, API on 4000
```

## Run the API locally without Docker

```bash
cd apps/api
python -m venv .venv
./.venv/Scripts/activate   # or `source .venv/bin/activate` on macOS/Linux
pip install -r requirements.txt
cp .env.example .env       # make sure Postgres and Redis are running and .env points at them
uvicorn app.main:app --reload --port 4000
```

## Run the web dashboard

```bash
cd apps/web-dashboard
npm install
npm run dev
# http://localhost:5173/            — public caller flow ("Get help now")
# http://localhost:5173/driver/<id> — public driver GPS-share page for a dispatch
```
There is no staff UI — the dispatcher/police/hospital-facing API endpoints below are exercised
directly with `curl`.

## The caller flow, verified live

```bash
# Public, no auth — "I tell ResQ what happened and where I am"
curl -X POST localhost:4000/emergency -H "Content-Type: application/json" \
  -d '{"symptom":"CARDIAC_OR_UNCONSCIOUS","lat":13.0850,"lng":80.2101,"notes":"55yo male, sudden collapse"}'
# -> auto-picks nearest available ambulance + nearest hospital, HMAC-signs the
#    dispatch, computes a real Mapbox/OSRM route, generates a patient summary,
#    returns {callId, dispatchId, ambulanceId, hospitalId, severity, route, patientSummary}

# A second request from the same spot correctly skips the now-busy ambulance
# (confirmed: picked AMB-02 after the first took AMB-01)

# Driver shares real GPS -> caller's open map marker moves live (confirmed in
# two browser tabs: opening /driver/<dispatchId>, sharing location, and
# watching the marker move on the caller's page with zero refresh)
curl -X POST localhost:4000/dispatch/<dispatchId>/location -d '{"lat":13.05,"lng":80.24}'

# Hospital declines -> auto-reroutes to the next-nearest hospital, recomputes
# the route, and the caller's open status page updates live (confirmed: the
# page re-rendered "<hospital A> couldn't accept — finding another
# hospital..." then "Now heading to <hospital B>" with a new route on the
# map, no refresh)
curl -X POST localhost:4000/dispatch/<dispatchId>/respond -H "Authorization: Bearer <hospital JWT>" \
  -d '{"decision":"DECLINE"}'

# Frees the ambulance back up for the next emergency
curl -X POST localhost:4000/dispatch/<dispatchId>/complete -H "Authorization: Bearer <staff JWT>"
```

## The original staff-triggered flow, still verified (no dashboard fronts this — `curl` only)

```bash
TOKEN=$(curl -sS -X POST localhost:4000/auth/login -H "Content-Type: application/json" \
  -d '{"username":"disp1","role":"dispatcher"}' | python -c "import sys,json;print(json.load(sys.stdin)['access_token'])")

curl -X POST localhost:4000/calls -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" \
  -d '{"location":"Anna Nagar","originLat":13.0850,"originLng":80.2101,"hospitalId":"<hospitalId — see GET /routing/hospitals>","severity":"RED","notes":"cardiac arrest"}'

curl -X POST localhost:4000/dispatch -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" \
  -d '{"ambulanceId":"AMB-01","severity":"RED","hospitalId":"<hospitalId>","callId":"<id from above>"}'

curl -X POST localhost:4000/junctions/J2/preempt -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" \
  -d '{"dispatchId":"<id from above>","etaSeconds":20}'
# A second, lower-severity dispatch requesting the same junction within the
# ~5s arbitration window loses — reason: HIGHER_SEVERITY — logged to Postgres.

curl localhost:4000/trips/<dispatchId> -H "Authorization: Bearer $TOKEN"
```

RED beat AMBER on a contested junction (`reason: HIGHER_SEVERITY`), a forged/unknown dispatch ID
was rejected (`UNKNOWN_DISPATCH`), and trip rows had `junctionsCleared`/`arbitrationsInvolved`
jsonb columns populated — confirmed via `psql`. The `arbitration:decided`/`junction:state`
Socket.IO events themselves were confirmed emitting live (there's no dashboard rendering them
anymore — the earlier staff Police console this was verified on was removed once the caller flow
made it redundant; a Socket.IO client or `read_network_requests`-style tooling is how you'd watch
these events today).

## What's real vs. stubbed

**Fully working, tested against live infra:**
- Auth (JWT issuance + role claim, `apps/api/app/auth/`)
- **Public emergency intake** (`apps/api/app/emergency/`) — symptom picklist → deterministic severity mapping, nearest-*available*-ambulance selection (excludes ambulances on an `ACTIVE` dispatch — confirmed a second request correctly skips a busy one), nearest-hospital selection, all via real haversine distance over a seeded `hospitals` Postgres table and a static `AMBULANCES` fleet (`app/routing/service.py`)
- **Patient summary generation** (`apps/api/app/emergency/summary_service.py`) — calls Gemini (`gemini-2.5-flash`) for a short ER handoff brief from the structured intake; falls back to a deterministic template if `GEMINI_API_KEY` is unset, same resilience pattern as routing/notify
- **Emailed hospital report** (`apps/api/app/notify/service.py::send_email`, wired from `dispatch/service.py`) — whenever a hospital is assigned or reassigned, the patient summary + ambulance/severity/ETA is emailed to that hospital's seeded contact address via SMTP; no-ops with a logged warning if `SMTP_*` isn't configured; confirmed live with real SMTP credentials configured — see the safety note below on the seed contact data
- **Hospital accept/decline + auto-reroute** (`POST /dispatch/{id}/respond`) — decline picks the next-nearest hospital (excluding every hospital already declined for that trip), recomputes the route, re-emails the new hospital, and re-emits — confirmed live end-to-end in two browser tabs
- **Live ambulance GPS** — a public driver-tracker page (`/driver/:dispatchId`) shares real `navigator.geolocation` via `POST /dispatch/{id}/location`, relayed through Redis (30s TTL) and Socket.IO's `location:update`, rendered as a moving marker on a real Leaflet/OpenStreetMap map — confirmed live: opened the driver page in one tab, the caller's map marker moved in another, zero refresh
- Call intake, dispatch creation + HMAC signing (Postgres-backed, `apps/api/app/calls/`, `apps/api/app/dispatch/`)
- Junction pre-emption + severity/ETA arbitration (Redis-backed state, Postgres-verified signatures, `apps/api/app/junctions/`)
- Trip logging (Postgres jsonb, `apps/api/app/trips/`)
- **Fastest-route computation** (`apps/api/app/routing/`) — every dispatch computes a real driving route (distance, duration, turn-by-turn geometry). Uses Mapbox Directions when `MAPBOX_TOKEN` is set (confirmed live — `source: "mapbox"`), falling back to OSRM's public routing server (confirmed live — `source: "osrm"`), falling back to a deterministic mock only if neither responds.
- **SMS alerts via Twilio** (`apps/api/app/notify/service.py`) — set `TWILIO_ACCOUNT_SID` / `TWILIO_AUTH_TOKEN` / `TWILIO_FROM_NUMBER` and pass `notifyPhone` on `POST /dispatch`; runs off the event loop (`asyncio.to_thread`), a send failure is caught and logged rather than failing the dispatch
- Socket.IO layer (`dispatch:created`, `dispatch:rerouted`, `hospital:responded`, `location:update`, `junction:state`, `arbitration:decided` — all confirmed emitting and rendering live)
- Web dashboard (`apps/web-dashboard`) — public Emergency Request + Driver Tracker pages, all live-updating via Socket.IO. This is the entire frontend now — see "Removed" below.

**Still stubbed / broken:**
- `apps/api/app/notify/service.py::send_push` (FCM) — calls Google's *legacy* FCM HTTP endpoint, which **Google decommissioned in June 2024**. Setting `FCM_SERVER_KEY` will not make this work — needs rewriting against the FCM HTTP v1 API (service account JSON + OAuth2). Not wired into any endpoint either.
- No native driver app (`apps/driver-app`) — the web-based `/driver/:dispatchId` page is this demo's stand-in.

**Removed:** the Dispatcher/Police/Hospital staff dashboards and `/login` were deliberately deleted
from `apps/web-dashboard` once the caller flow made manual staff-driven entry redundant for this
demo (`AuthContext`, `authStore`, `AppShell`, `SeverityBadge`, `JunctionCard`, `TripTimeline` went
with them — nothing else referenced them). The backend endpoints they drove are untouched and
still covered by the `curl` flow above; only the UI is gone. Rebuilding a staff console is a matter
of re-adding pages that call the existing, working API — no backend work required.

**Safety note on hospital contact details:** the seeded `hospitals` rows are fictional demo
entities, not real hospitals, and every seed row intentionally shares one real test inbox for
`email` — the point of this seed set is to let the report-email feature be verified end to end by
whoever owns that inbox. Never repeat this pattern with a real hospital's name paired with contact
details that aren't actually that hospital's own — for a real deployment, `email`/`phone` must be
each hospital's genuine, verified contact, sourced from a real registry, not seeded in code.

**Important — running via Docker:** `docker-compose.yml` uses `env_file: apps/api/.env` for the `api` service (falls back to defaults if the file doesn't exist), overriding only `DATABASE_URL`/`REDIS_URL` to point at the in-network `postgres`/`redis` hostnames. Fill in `apps/api/.env` (copy from `.env.example`) — `docker compose up --build` picks it up automatically.

## Tests

```bash
cd apps/api
pytest
# arbitration.py (severity/ETA tiebreak), hmac_util.py (sign/verify + tamper
# detection), and haversine/nearest-selection + symptom->severity mapping
```

## Next pieces

- Swap `Base.metadata.create_all` in `apps/api/app/main.py` for real Alembic migrations before anything beyond hackathon demo use
- `router.project-osrm.org` is OSRM's free public demo instance — fine for a demo, but rate-limited and "not for production use" per OSRM's own terms; swap `OSRM_BASE_URL` for a self-hosted `osrm-backend` container before any real deployment
- The tiny 5-hospital / 5-ambulance seed fleet is demo-scale — a real deployment pulls both from live registries instead of `app/routing/service.py`'s static seed data, with each hospital's own real contact details rather than one shared demo inbox
- No staff UI exists to drive the dispatcher/police/hospital endpoints interactively anymore (see "Removed" above) — reintroduce pages only if a staff-facing demo is needed again; the API underneath is unchanged
