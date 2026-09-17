export type Severity = 'RED' | 'YELLOW' | 'GREEN'

export interface LatLng {
  lat: number
  lng: number
}

export interface Hospital {
  id: string
  name: string
  lat: number
  lng: number
}

export interface Call {
  id: string
  caller_name: string
  phone: string
  symptom: string
  severity: Severity
  location: LatLng
  attendant_consent: boolean
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

export interface NotificationEntry {
  channel: string
  dispatch_id: string | null
  subject: string
  body: string
  ts: string
}

export const SEVERITY_COLOR: Record<Severity, string> = {
  RED: '#dc2626',
  YELLOW: '#d97706',
  GREEN: '#16a34a',
}
