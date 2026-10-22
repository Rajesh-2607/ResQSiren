// Origin of the resQ Siren API.
//
// Left empty in development: Vite's dev proxy forwards /emergency, /dispatch
// and /socket.io to the local API, so relative requests are same-origin.
// In production the frontend is served from a different host than the API
// (e.g. Vercel + Render), so VITE_API_BASE_URL must point at the API.
export const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/+$/, "");
