// Named-locality fallback for when browser geolocation is denied/unavailable.
// Same coordinates as the backend's AMBULANCES home-bases (app/routing/service.py)
// so demo requests land near a real ambulance.
export const LOCATION_PRESETS: { label: string; lat: number; lng: number }[] = [
  { label: "Anna Nagar", lat: 13.085, lng: 80.2101 },
  { label: "T Nagar", lat: 13.0418, lng: 80.2341 },
  { label: "Velachery", lat: 12.9756, lng: 80.2207 },
  { label: "Adyar", lat: 13.0067, lng: 80.257 },
  { label: "Egmore", lat: 13.0732, lng: 80.2609 },
];
