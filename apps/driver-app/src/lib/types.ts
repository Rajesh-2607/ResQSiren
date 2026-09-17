export type Severity = 'RED' | 'YELLOW' | 'GREEN'

export interface LatLng {
  lat: number
  lng: number
}

export interface Ambulance {
  id: string
  callsign: string
  lat: number
  lng: number
}

export interface Junction {
  id: string
  name: string
  lat: number
  lng: number
}

export interface Dispatch {
  id: string
  call_id: string
  ambulance_id: string
  hospital_id: string
  severity: Severity
  origin: LatLng
  destination: LatLng
  route: { source: string; distance_km: number; eta_seconds: number; path: LatLng[] }
  eta_seconds: number
  status: string
  signature: string
}

export const SEVERITY_COLOR: Record<Severity, string> = {
  RED: '#dc2626',
  YELLOW: '#d97706',
  GREEN: '#16a34a',
}
