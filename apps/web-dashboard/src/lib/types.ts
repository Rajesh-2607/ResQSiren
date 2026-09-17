export type Severity = "RED" | "AMBER" | "GREEN";

export interface GeoJSONLineString {
  type: "LineString";
  coordinates: [number, number][]; // [lng, lat]
}

export interface Route {
  source: "mapbox" | "osrm" | "mock";
  distanceMeters: number;
  durationSeconds: number;
  geometry: GeoJSONLineString | null;
}

export interface ArbitrationEvent {
  junctionId: string;
  winnerDispatchId: string;
  loserDispatchId: string | null;
  reason: string;
}

export interface RerouteEvent {
  id: string;
  hospitalId: string;
  route: Route | null;
}

export interface HospitalRespondedEvent {
  id: string;
  decision: "ACCEPT" | "DECLINE";
  hospitalId: string;
}

export type SymptomCategory = "CARDIAC_OR_UNCONSCIOUS" | "SEVERE_BLEEDING_OR_FRACTURE" | "STABLE_NON_URGENT";

export interface EmergencyResponse {
  callId: string;
  dispatchId: string;
  ambulanceId: string;
  hospitalId: string;
  severity: Severity;
  route: Route | null;
  patientSummary: string | null;
}
