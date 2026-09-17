import { useEffect, useRef, useState } from "react";
import { LiveMap } from "../components/LiveMap";
import { api, describeApiError } from "../lib/api";
import { LOCATION_PRESETS } from "../lib/locations";
import { getSocket } from "../lib/socket";
import type {
  ArbitrationEvent,
  EmergencyResponse,
  HospitalRespondedEvent,
  RerouteEvent,
  SymptomCategory,
} from "../lib/types";

const SYMPTOM_OPTIONS: { value: SymptomCategory; title: string; detail: string; color: string }[] = [
  {
    value: "CARDIAC_OR_UNCONSCIOUS",
    title: "Chest pain, unconscious, severe trauma",
    detail: "Life-threatening — send help immediately",
    color: "border-red-300 bg-red-50 hover:bg-red-100 text-red-900",
  },
  {
    value: "SEVERE_BLEEDING_OR_FRACTURE",
    title: "Serious injury, heavy bleeding, fracture",
    detail: "Urgent, needs care soon",
    color: "border-amber-300 bg-amber-50 hover:bg-amber-100 text-amber-900",
  },
  {
    value: "STABLE_NON_URGENT",
    title: "Stable, non-urgent transport",
    detail: "No immediate danger",
    color: "border-emerald-300 bg-emerald-50 hover:bg-emerald-100 text-emerald-900",
  },
];

type Step = "symptom" | "location" | "submitting" | "status" | "error";

export function EmergencyRequest() {
  const [step, setStep] = useState<Step>("symptom");
  const [symptom, setSymptom] = useState<SymptomCategory | null>(null);
  const [locating, setLocating] = useState(false);
  const [geoDenied, setGeoDenied] = useState(false);
  const [coords, setCoords] = useState<{ lat: number; lng: number } | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const [result, setResult] = useState<EmergencyResponse | null>(null);
  const [hospitalId, setHospitalId] = useState<string | null>(null);
  const [hospitalResponse, setHospitalResponse] = useState<"PENDING" | "ACCEPTED" | "DECLINED">("PENDING");
  const [route, setRoute] = useState<EmergencyResponse["route"] | null>(null);
  const [ambulancePosition, setAmbulancePosition] = useState<[number, number] | null>(null);
  const [pickedUpAt, setPickedUpAt] = useState<string | null>(null);
  const [feed, setFeed] = useState<string[]>([]);

  const dispatchIdRef = useRef<string | null>(null);

  function pushFeed(line: string) {
    setFeed((prev) => [line, ...prev].slice(0, 12));
  }

  useEffect(() => {
    if (step !== "status" || !result) return;
    const socket = getSocket();
    const myId = result.dispatchId;

    const onArbitration = (event: ArbitrationEvent) => {
      if (event.winnerDispatchId === myId) pushFeed(`Clearing traffic ahead — junction ${event.junctionId}`);
    };
    const onHospitalResponded = (event: HospitalRespondedEvent) => {
      if (event.id !== myId) return;
      if (event.decision === "ACCEPT") {
        setHospitalResponse("ACCEPTED");
        pushFeed(`${event.hospitalId} has accepted you`);
      } else {
        pushFeed(`${event.hospitalId} couldn't accept — finding another hospital…`);
      }
    };
    const onRerouted = (event: RerouteEvent) => {
      if (event.id !== myId) return;
      setHospitalId(event.hospitalId);
      setHospitalResponse("PENDING");
      setRoute(event.route);
      pushFeed(`Now heading to ${event.hospitalId}`);
    };
    const onLocation = (event: { dispatchId: string; lat: number; lng: number }) => {
      if (event.dispatchId !== myId) return;
      setAmbulancePosition([event.lat, event.lng]);
    };
    const onArrived = (event: { id: string; pickedUpAt: string }) => {
      if (event.id !== myId) return;
      setPickedUpAt(event.pickedUpAt);
      pushFeed("Ambulance has arrived and picked up the patient");
    };

    socket.on("arbitration:decided", onArbitration);
    socket.on("hospital:responded", onHospitalResponded);
    socket.on("dispatch:rerouted", onRerouted);
    socket.on("location:update", onLocation);
    socket.on("dispatch:arrived", onArrived);
    return () => {
      socket.off("arbitration:decided", onArbitration);
      socket.off("hospital:responded", onHospitalResponded);
      socket.off("dispatch:rerouted", onRerouted);
      socket.off("location:update", onLocation);
      socket.off("dispatch:arrived", onArrived);
    };
  }, [step, result]);

  function chooseSymptom(value: SymptomCategory) {
    setSymptom(value);
    setStep("location");
    setLocating(true);
    if (!navigator.geolocation) {
      setLocating(false);
      setGeoDenied(true);
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setCoords({ lat: pos.coords.latitude, lng: pos.coords.longitude });
        setLocating(false);
      },
      () => {
        setLocating(false);
        setGeoDenied(true);
      },
      { timeout: 8000 },
    );
  }

  async function submit() {
    if (!symptom || !coords) return;
    setStep("submitting");
    setErrorMessage(null);
    try {
      const res = await api.post<EmergencyResponse>("/emergency", {
        symptom,
        lat: coords.lat,
        lng: coords.lng,
      });
      setResult(res);
      setHospitalId(res.hospitalId);
      setRoute(res.route);
      dispatchIdRef.current = res.dispatchId;
      pushFeed(`${res.ambulanceId} dispatched to you`);
      setStep("status");
    } catch (err) {
      setErrorMessage(describeApiError(err));
      setStep("error");
    }
  }

  return (
    <div className="min-h-screen bg-slate-100">
      <header className="bg-red-600 px-6 py-4 text-white">
        <p className="text-sm text-red-100">resQ Siren</p>
        <h1 className="text-lg font-semibold">Get help now</h1>
      </header>

      <main className="mx-auto max-w-2xl p-6">
        {step === "symptom" && (
          <div className="space-y-4">
            <h2 className="text-xl font-semibold text-slate-900">What's happening?</h2>
            <div className="space-y-3">
              {SYMPTOM_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => chooseSymptom(opt.value)}
                  className={`w-full rounded-xl border-2 p-5 text-left shadow-sm transition ${opt.color}`}
                >
                  <p className="text-lg font-bold">{opt.title}</p>
                  <p className="text-sm opacity-80">{opt.detail}</p>
                </button>
              ))}
            </div>
          </div>
        )}

        {step === "location" && (
          <div className="space-y-4">
            <h2 className="text-xl font-semibold text-slate-900">Where are you?</h2>
            {locating && <p className="text-slate-500">Finding your location…</p>}
            {coords && !locating && (
              <div className="rounded-lg border border-emerald-300 bg-emerald-50 p-4 text-emerald-900">
                Location found ({coords.lat.toFixed(4)}, {coords.lng.toFixed(4)})
              </div>
            )}
            {geoDenied && (
              <div className="space-y-2">
                <p className="text-sm text-slate-500">
                  Couldn't get your location automatically. Pick the closest area:
                </p>
                <div className="grid grid-cols-2 gap-2">
                  {LOCATION_PRESETS.map((p) => (
                    <button
                      key={p.label}
                      onClick={() => setCoords({ lat: p.lat, lng: p.lng })}
                      className={`rounded border px-3 py-2 text-sm ${
                        coords?.lat === p.lat ? "border-slate-900 bg-slate-900 text-white" : "border-slate-300 bg-white"
                      }`}
                    >
                      {p.label}
                    </button>
                  ))}
                </div>
              </div>
            )}
            <button
              disabled={!coords}
              onClick={submit}
              className="w-full rounded bg-red-600 py-3 text-lg font-bold text-white hover:bg-red-500 disabled:opacity-40"
            >
              Send help
            </button>
          </div>
        )}

        {step === "submitting" && <p className="text-lg text-slate-600">Dispatching the nearest ambulance…</p>}

        {step === "error" && (
          <div className="space-y-4">
            <p className="rounded border border-red-300 bg-red-50 p-4 text-red-800">{errorMessage}</p>
            <button onClick={() => setStep("symptom")} className="rounded bg-slate-900 px-4 py-2 text-white">
              Try again
            </button>
          </div>
        )}

        {step === "status" && result && coords && hospitalId && (
          <div className="space-y-4">
            <div className="rounded-xl border border-emerald-300 bg-emerald-50 p-4">
              <p className="text-lg font-bold text-emerald-900">
                {pickedUpAt ? `${result.ambulanceId} has picked you up` : `${result.ambulanceId} is on the way`}
              </p>
              <p className="text-sm text-emerald-800">
                Severity <span className="font-semibold">{result.severity}</span> · Heading to{" "}
                <span className="font-semibold">{hospitalId}</span> (
                {hospitalResponse === "ACCEPTED" ? "confirmed" : "awaiting confirmation"})
              </p>
              {route && (
                <p className="text-sm text-emerald-800">
                  {(route.distanceMeters / 1000).toFixed(1)} km · ETA ~{Math.round(route.durationSeconds / 60)} min
                </p>
              )}
              {pickedUpAt && (
                <p className="text-sm font-semibold text-emerald-900">
                  ✓ Picked up at {new Date(pickedUpAt).toLocaleTimeString()} — a detailed report was sent to the hospital
                </p>
              )}
            </div>

            {route && (
              <LiveMap
                origin={[coords.lat, coords.lng]}
                destination={
                  route.geometry
                    ? [
                        route.geometry.coordinates[route.geometry.coordinates.length - 1][1],
                        route.geometry.coordinates[route.geometry.coordinates.length - 1][0],
                      ]
                    : [coords.lat, coords.lng]
                }
                routeGeometry={route.geometry}
                ambulancePosition={ambulancePosition}
              />
            )}

            {result.patientSummary && (
              <div className="rounded-lg border border-slate-200 bg-white p-4">
                <p className="text-xs font-semibold uppercase text-slate-400">Sent to the hospital</p>
                <p className="text-sm text-slate-700">{result.patientSummary}</p>
              </div>
            )}

            <div className="rounded-lg border border-slate-200 bg-white p-4">
              <p className="mb-2 text-xs font-semibold uppercase text-slate-400">What's happening</p>
              <ul className="space-y-1 text-sm text-slate-700">
                {feed.map((line, i) => (
                  <li key={i}>{line}</li>
                ))}
              </ul>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
