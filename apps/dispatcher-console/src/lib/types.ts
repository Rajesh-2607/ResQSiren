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

export interface ArbitrationRankEntry {
  dispatch_id: string
  ambulance_id: string
  severity: Severity
  score: number
  wait_seconds: number
}

export interface ArbitrationResult {
  junction_id: string
  winner_dispatch_id: string | null
  ranked: ArbitrationRankEntry[]
  ts: string
}

export interface SignalPreemption {
  junction_id: string
  dispatch_id: string
  action: string
  message: string
  ts: string
}

export interface NotificationEntry {
  channel: string
  dispatch_id: string | null
  subject: string
  body: string
  ts: string
}

export const SYMPTOMS: { value: string; label: string }[] = [
  { value: 'cardiac_arrest', label: 'Cardiac arrest' },
  { value: 'not_breathing', label: 'Not breathing' },
  { value: 'severe_bleeding', label: 'Severe bleeding' },
  { value: 'unconscious', label: 'Unconscious' },
  { value: 'stroke_symptoms', label: 'Stroke symptoms' },
  { value: 'chest_pain', label: 'Chest pain' },
  { value: 'breathing_difficulty', label: 'Breathing difficulty' },
  { value: 'fracture', label: 'Fracture' },
  { value: 'high_fever', label: 'High fever' },
  { value: 'stable_transfer', label: 'Stable transfer' },
  { value: 'routine_checkup', label: 'Routine checkup' },
  { value: 'minor_injury', label: 'Minor injury' },
]

export const SEVERITY_COLOR: Record<Severity, string> = {
  RED: '#dc2626',
  YELLOW: '#d97706',
  GREEN: '#16a34a',
}
