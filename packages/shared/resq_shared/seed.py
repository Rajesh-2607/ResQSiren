"""Static demo seed data shared across services (Chennai-area coordinates).

A hackathon demo needs the same ambulances/hospitals/junctions to exist
consistently in dispatch, routing, and conflict-resolution without a shared
database. Keeping it here (rather than duplicated per service) is the
single source of truth.
"""

HOSPITALS = [
    {"id": "hosp-1", "name": "Apollo Hospital, Greams Road", "lat": 13.0604, "lng": 80.2496},
    {"id": "hosp-2", "name": "Rajiv Gandhi Govt. General Hospital", "lat": 13.0878, "lng": 80.2785},
    {"id": "hosp-3", "name": "Fortis Malar Hospital, Adyar", "lat": 13.0067, "lng": 80.2570},
    {"id": "hosp-4", "name": "MIOT International", "lat": 13.0138, "lng": 80.1866},
    {"id": "hosp-5", "name": "Sri Ramachandra Medical Centre", "lat": 13.0418, "lng": 80.1548},
]

AMBULANCES = [
    {"id": "amb-1", "callsign": "Ambulance 1", "lat": 13.0827, "lng": 80.2707},
    {"id": "amb-2", "callsign": "Ambulance 2", "lat": 13.0500, "lng": 80.2121},
    {"id": "amb-3", "callsign": "Ambulance 3", "lat": 13.0339, "lng": 80.2619},
    {"id": "amb-4", "callsign": "Ambulance 4", "lat": 13.0012, "lng": 80.2565},
]

JUNCTIONS = [
    {"id": "jn-1", "name": "Kathipara Junction", "lat": 13.0186, "lng": 80.2006},
    {"id": "jn-2", "name": "Gemini Flyover", "lat": 13.0604, "lng": 80.2585},
    {"id": "jn-3", "name": "Anna Nagar Roundtana", "lat": 13.0850, "lng": 80.2101},
]


def hospital_by_id(hospital_id: str) -> dict | None:
    return next((h for h in HOSPITALS if h["id"] == hospital_id), None)


def ambulance_by_id(ambulance_id: str) -> dict | None:
    return next((a for a in AMBULANCES if a["id"] == ambulance_id), None)


def junction_by_id(junction_id: str) -> dict | None:
    return next((j for j in JUNCTIONS if j["id"] == junction_id), None)
