# resQ Siren — Smart Ambulance Corridor

**Smart India Hackathon 2026 — Problem Statement ID 25132**
Theme: Miscellaneous · Category: Software

## Problem

Ambulances lose 15–20 critical minutes navigating Indian traffic. Existing
"green corridor" efforts rely on manual police coordination or basic vehicle
detection, and they break down exactly when it matters most, because they have
three structural gaps:

1. **No severity awareness** — every ambulance is treated the same, whether
   it's carrying a cardiac arrest patient or a stable transfer.
2. **No conflict resolution** — systems assume one ambulance at a time; real
   cities have multiple emergencies converging on the same junction.
3. **No verification** — signal-priority requests can't be authenticated,
   leaving them open to spoofing and misuse.

## Solution, in one line

A dispatcher-triggered, severity-weighted, authenticated traffic corridor
that dynamically routes ambulances and arbitrates between competing
emergencies at shared junctions. Severity is generated once at call intake
and drives every downstream decision — routing, signal alerts, priority, and
post-trip performance tracking.

## Core design principle

The platform is **event-driven, not request/response**. A junction doesn't
ask a service what to do — it subscribes to a stream of signed "ambulance
approaching" events, and a small arbitration engine decides who gets
priority. This is what makes conflict resolution and spoof-resistance
possible; a request/response model can't express "two ambulances just
claimed the same junction."

## Architecture

```
                        ┌─────────────────────────────────────────┐
                        │            resQ Siren platform           │
                        │                                          │
   Call intake ──────►  │  ┌────────────┐  ┌──────────┐  ┌───────┐ │  ──────► Signals
   (108/112)            │  │Client apps │  │Data&state│  │ Core  │ │           & hospitals
                        │  │            │◄─┤          │◄─┤services│ │
                        │  └────────────┘  └──────────┘  └───────┘ │
                        │                        ▲            │    │
                        │                        └── events ──┘    │
                        └─────────────────────────────────────────┘
```

### Client apps
- Dispatcher console (web) — call intake, severity assignment, live map
- Ambulance driver app (mobile) — turn-by-turn routing, one-tap status
- Hospital ER dashboard — advance alerts with severity + ABHA summary
- Police / traffic officer terminal — junction status, manual override

### Core services (event-driven)
- **Dispatch service** — call intake, severity scoring (Red/Yellow/Green),
  signs each dispatch record
- **Conflict resolution engine** — the differentiator. See below.
- **Routing service** — fastest-path calculation, re-routes on live traffic
- **Signal command service** — verifies signatures, emits pre-emption
  commands to the (mocked, then real) ITMS layer
- **Notification service** — hospital alerts, police alerts, public notices

### Data & state
- **PostgreSQL** — trips, dispatch records, ABHA consent tokens, audit log
- **Redis** — live geospatial positions, active junction claims (short-lived)

### External integrations
- ABHA (consent-gated health record access)
- Maps/routing provider (Google Maps or OSRM self-hosted fallback)
- Mock ITMS junction service now → pluggable adapter for real hardware later
- Firebase Cloud Messaging + Twilio SMS for notifications

## Conflict resolution — the core algorithm

When two or more ambulances claim the same junction within a short window:

```
score = severity_weight × 100 + wait_seconds
```

- Red > Yellow > Green by default, regardless of arrival order
- A lower-severity ambulance that has waited long enough eventually
  outranks a fresh higher-severity claim — this prevents starvation
- The highest score gets the pre-emption; others are queued and re-scored
  every tick until they clear or win

## Authentication & consent

- **Dispatch signing**: every dispatch record is HMAC-signed the moment
  severity is assigned. The signal command service checks this signature
  against the dispatch record before emitting anything to ITMS — an
  unsigned or spoofed "approaching" ping is rejected outright.
- **ABHA consent**: captured at call intake via an explicit dispatcher
  toggle ("attendant consent given"), which mints a short-lived ABHA
  access token. No toggle → no health record fetch. Routing and priority
  work identically either way.

## Tech stack

| Layer | Choice |
|---|---|
| Frontend | React.js + Tailwind CSS |
| Mobile | React Native / Flutter (driver app) |
| Backend | Node.js (NestJS) or FastAPI |
| Real-time | Socket.IO / WebSockets |
| Auth | JWT (session) + HMAC (dispatch signing) |
| Database | PostgreSQL (persistent), Redis (live geospatial + claims) |
| Maps & routing | Google Maps / Mapbox API, OSRM self-hosted fallback |
| Signal integration | Mock ITMS junction service now, RFID/GPS-geofence later |
| Notifications | Firebase Cloud Messaging, Twilio SMS |
| Hosting & CI/CD | Vercel / Render / Supabase, GitHub Actions |

## Repo structure

This repo now holds two tracks. **`apps/api` + `apps/web-dashboard`** is a
working FastAPI monolith + citizen-request web app (call intake, severity,
routing, arbitration, HMAC signing, and notifications all in one service —
see its own `docker-compose.yml` at the repo root). **Everything below** is
the microservice architecture this document originally sketched, built as a
separate track alongside it — same ideas, split into real services:

```
resq-siren/
├── apps/
│   ├── api/                     # v1 monolith (FastAPI + Socket.IO)
│   ├── web-dashboard/           # v1 citizen request + driver tracker (React)
│   ├── dispatcher-console/      # v2 dispatcher web app (React)
│   ├── driver-app/              # v2 minimal driver web app (React)
│   └── hospital-dashboard/      # v2 hospital ER dashboard (React)
├── services/                    # v2 only
│   ├── dispatch/                # intake, severity scoring, signing
│   ├── conflict-resolution/     # junction arbitration engine
│   ├── routing/                 # path optimization
│   ├── signal-command/          # signature verification + mock ITMS
│   └── notifications/           # notification log (mocked; no real FCM/Twilio yet)
├── packages/
│   └── shared/                  # v2: types, HMAC utils, severity constants, event bus
├── infra/
│   └── docker-compose.yml       # v2: postgres, redis, all 5 services
├── docker-compose.yml           # v1: postgres, redis, api
└── docs/
    └── architecture.md          # v2 architecture, event flow, run instructions
```

Full run instructions, the event contract, and the trust-boundary design for
the v2 platform are in [`docs/architecture.md`](docs/architecture.md).

## Getting started

### v2 platform (microservices)

```bash
# backend: postgres, redis, and all 5 services
docker compose -f infra/docker-compose.yml up -d --build

# frontends (each needs its own install once)
cd apps/dispatcher-console && cp .env.example .env && npm install && npm run dev   # :5180
cd apps/driver-app          && cp .env.example .env && npm install && npm run dev   # :5181
cd apps/hospital-dashboard  && cp .env.example .env && npm install && npm run dev   # :5182
```

See [`docs/architecture.md`](docs/architecture.md) for the demo scenario
(triggering two ambulances converging on a junction) and local non-Docker dev.

### v1 monolith

```bash
docker compose up -d          # postgres, redis, api on :4000
cd apps/web-dashboard && npm install && npm run dev
```

## Demo plan (for judging)

The single most convincing moment: trigger two ambulances converging on one
junction live and show the dashboard re-rank them and grant only one.

1. Seed 3–4 fake ambulances with GPS replay scripts (CSV of lat/lng played
   back on a timer) so the live map moves during the demo
2. Mock ITMS as a lightweight WebSocket service that logs
   `"signal pre-empted at junction X"` — the point is proving the
   auth/arbitration logic runs, not controlling real traffic lights
3. Walk through: call intake → severity tag → live routing → two
   ambulances hit the same junction → conflict resolution engine ranks
   them → signed signal command → hospital gets advance alert

## Build phases

1. **Phase 1 — Core loop**: call intake, severity scoring, single-ambulance
   routing, mock signal pre-emption (no conflict resolution yet)
2. **Phase 2 — Conflict resolution**: junction claims in Redis, scoring
   algorithm, queued arbitration
3. **Phase 3 — Trust layer**: HMAC dispatch signing, signature verification
   at the signal command service
4. **Phase 4 — Consent & records**: ABHA token flow, hospital advance
   alerts with patient summary
5. **Phase 5 — Demo polish**: GPS replay seed data, live dashboard,
   trip logging for the "log & learn" loop

## Team

resQ Siren — Smart India Hackathon 2026, PS ID 25132
