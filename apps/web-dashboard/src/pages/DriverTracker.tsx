import { useRef, useState } from "react";
import { useParams } from "react-router-dom";
import { api, describeApiError } from "../lib/api";

// The demo's stand-in for the still-unbuilt native driver app: open this
// link on the phone playing "the ambulance" and it relays real browser GPS
// to the caller's live map via POST /dispatch/{id}/location.
export function DriverTracker() {
  const { dispatchId } = useParams<{ dispatchId: string }>();
  const [sharing, setSharing] = useState(false);
  const [lastSent, setLastSent] = useState<{ lat: number; lng: number } | null>(null);
  const [arrivedAt, setArrivedAt] = useState<string | null>(null);
  const [arriving, setArriving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const watchIdRef = useRef<number | null>(null);
  const lastSentAtRef = useRef(0);

  function startSharing() {
    if (!dispatchId || !navigator.geolocation) return;
    setError(null);
    setSharing(true);
    watchIdRef.current = navigator.geolocation.watchPosition(
      (pos) => {
        const now = Date.now();
        if (now - lastSentAtRef.current < 3000) return; // throttle to ~1 update / 3s
        lastSentAtRef.current = now;
        const lat = pos.coords.latitude;
        const lng = pos.coords.longitude;
        api
          .post(`/dispatch/${dispatchId}/location`, { lat, lng })
          .then(() => setLastSent({ lat, lng }))
          .catch((err) => setError(describeApiError(err)));
      },
      (err) => setError(err.message),
      { enableHighAccuracy: true, maximumAge: 2000 },
    );
  }

  function stopSharing() {
    if (watchIdRef.current !== null) navigator.geolocation.clearWatch(watchIdRef.current);
    watchIdRef.current = null;
    setSharing(false);
  }

  async function markArrived() {
    if (!dispatchId) return;
    setError(null);
    setArriving(true);
    try {
      const res = await api.post<{ pickedUpAt: string }>(`/dispatch/${dispatchId}/arrived`, {});
      setArrivedAt(res.pickedUpAt);
    } catch (err) {
      setError(describeApiError(err));
    } finally {
      setArriving(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-900 p-6">
      <div className="w-full max-w-sm space-y-4 rounded-xl bg-white p-6 text-center shadow">
        <p className="text-sm text-slate-500">resQ Siren — Driver</p>
        <h1 className="text-lg font-semibold text-slate-900">
          Dispatch <span className="font-mono text-sm">{dispatchId?.slice(0, 8)}</span>
        </h1>
        <p className="text-sm text-slate-500">
          Sharing your location lets the patient see the ambulance approach live on the map.
        </p>

        {!sharing ? (
          <button onClick={startSharing} className="w-full rounded bg-red-600 py-3 font-semibold text-white hover:bg-red-500">
            Share my location
          </button>
        ) : (
          <button onClick={stopSharing} className="w-full rounded bg-slate-700 py-3 font-semibold text-white hover:bg-slate-600">
            Stop sharing
          </button>
        )}

        {sharing && (
          <p className="text-xs text-emerald-600">
            {lastSent ? `Last sent: ${lastSent.lat.toFixed(4)}, ${lastSent.lng.toFixed(4)}` : "Waiting for GPS…"}
          </p>
        )}

        <div className="border-t border-slate-200 pt-4">
          <button
            onClick={markArrived}
            disabled={arriving || !!arrivedAt}
            className="w-full rounded bg-emerald-600 py-3 font-semibold text-white hover:bg-emerald-500 disabled:opacity-50"
          >
            {arrivedAt ? "Patient picked up ✓" : arriving ? "Marking arrived…" : "Arrived — patient picked up"}
          </button>
          <p className="mt-2 text-xs text-slate-500">
            Confirms pickup and sends the hospital a detailed report — response time, patient summary, and an
            updated ETA from your current position.
          </p>
        </div>

        {error && <p className="text-xs text-red-600">{error}</p>}
      </div>
    </div>
  );
}
