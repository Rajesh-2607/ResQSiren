import { useEffect, useState } from 'react'
import RouteMap from './components/RouteMap'
import { ApiError, dispatchApi, routingApi } from './lib/api'
import { SEVERITY_COLOR } from './lib/types'
import type { Ambulance, Dispatch, Junction } from './lib/types'

const STORAGE_KEY = 'resq-driver-ambulance-id'

function loadStoredAmbulanceId(): string {
  try {
    return localStorage.getItem(STORAGE_KEY) ?? ''
  } catch {
    return ''
  }
}

function storeAmbulanceId(id: string) {
  try {
    localStorage.setItem(STORAGE_KEY, id)
  } catch {
    // storage blocked (private mode etc.) - not fatal, just won't persist
  }
}

export default function App() {
  const [ambulances, setAmbulances] = useState<Ambulance[]>([])
  const [junctions, setJunctions] = useState<Junction[]>([])
  const [ambulanceId, setAmbulanceId] = useState(loadStoredAmbulanceId)
  const [dispatch, setDispatch] = useState<Dispatch | null>(null)
  const [selectedJunction, setSelectedJunction] = useState('')
  const [notice, setNotice] = useState<{ kind: 'success' | 'error'; text: string } | null>(null)
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    routingApi.ambulances().then((v) => setAmbulances(v as Ambulance[]))
    routingApi.junctions().then((v) => {
      const list = v as Junction[]
      setJunctions(list)
      setSelectedJunction((prev) => prev || list[0]?.id || '')
    })
  }, [])

  useEffect(() => {
    if (!ambulanceId) {
      setDispatch(null)
      return
    }

    let cancelled = false

    async function refresh() {
      try {
        const dispatches = (await dispatchApi.listDispatches()) as Dispatch[]
        if (cancelled) return
        const active = dispatches.find((d) => d.ambulance_id === ambulanceId && d.status === 'EN_ROUTE')
        setDispatch(active ?? null)
      } catch {
        // transient network error - keep showing the last known state
      }
    }

    refresh()
    const interval = setInterval(refresh, 4000)
    return () => {
      cancelled = true
      clearInterval(interval)
    }
  }, [ambulanceId])

  function handleAmbulanceChange(id: string) {
    setAmbulanceId(id)
    storeAmbulanceId(id)
    setNotice(null)
  }

  async function reportApproaching() {
    if (!dispatch || !selectedJunction) return
    setBusy(true)
    setNotice(null)
    try {
      await dispatchApi.reportApproaching(dispatch.id, {
        junction_id: selectedJunction,
        eta_seconds: dispatch.eta_seconds,
      })
      setNotice({ kind: 'success', text: 'Approaching ping sent and signed.' })
    } catch (err) {
      setNotice({ kind: 'error', text: err instanceof ApiError ? err.message : 'Failed to send ping' })
    } finally {
      setBusy(false)
    }
  }

  async function markArrived() {
    if (!dispatch) return
    setBusy(true)
    setNotice(null)
    try {
      const updated = (await dispatchApi.markArrived(dispatch.id)) as Dispatch
      setDispatch(updated)
      setNotice({ kind: 'success', text: 'Marked arrived at hospital.' })
    } catch (err) {
      setNotice({ kind: 'error', text: err instanceof ApiError ? err.message : 'Failed to update status' })
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="min-h-screen">
      <header className="bg-gray-900 text-white px-4 py-3">
        <h1 className="font-semibold">resQ Siren - Driver</h1>
      </header>

      <main className="p-4 max-w-md mx-auto space-y-4">
        <div className="bg-white rounded-lg p-4 shadow-sm space-y-2">
          <label className="block text-sm font-medium text-gray-700">Sign in as</label>
          <select
            value={ambulanceId}
            onChange={(e) => handleAmbulanceChange(e.target.value)}
            className="w-full rounded border border-gray-300 px-2 py-1.5 text-sm"
          >
            <option value="">Select ambulance...</option>
            {ambulances.map((a) => (
              <option key={a.id} value={a.id}>
                {a.callsign} ({a.id})
              </option>
            ))}
          </select>
        </div>

        {!ambulanceId && <p className="text-sm text-gray-500 text-center">Select an ambulance to continue.</p>}

        {ambulanceId && !dispatch && (
          <div className="bg-white rounded-lg p-4 shadow-sm text-sm text-gray-500 text-center">
            No active dispatch for this ambulance.
          </div>
        )}

        {dispatch && (
          <>
            <div className="bg-white rounded-lg p-4 shadow-sm space-y-2">
              <div className="flex items-center justify-between">
                <span
                  className="inline-flex items-center gap-1.5 text-sm font-semibold"
                  style={{ color: SEVERITY_COLOR[dispatch.severity] }}
                >
                  <span
                    className="inline-block w-2.5 h-2.5 rounded-full"
                    style={{ background: SEVERITY_COLOR[dispatch.severity] }}
                  />
                  {dispatch.severity}
                </span>
                <span className="text-xs text-gray-500">{dispatch.status}</span>
              </div>
              <p className="text-sm text-gray-700">
                ETA to hospital: <span className="font-medium">{Math.round(dispatch.eta_seconds)}s</span>
              </p>
              <p className="text-xs text-gray-500">Dispatch {dispatch.id.slice(0, 8)}</p>
            </div>

            <div className="bg-white rounded-lg shadow-sm h-64">
              <RouteMap dispatch={dispatch} />
            </div>

            <div className="bg-white rounded-lg p-4 shadow-sm space-y-2">
              <label className="block text-sm font-medium text-gray-700">Report approaching junction</label>
              <div className="flex gap-2">
                <select
                  value={selectedJunction}
                  onChange={(e) => setSelectedJunction(e.target.value)}
                  className="flex-1 rounded border border-gray-300 px-2 py-1.5 text-sm"
                >
                  {junctions.map((j) => (
                    <option key={j.id} value={j.id}>
                      {j.name}
                    </option>
                  ))}
                </select>
                <button
                  onClick={reportApproaching}
                  disabled={busy || dispatch.status !== 'EN_ROUTE'}
                  className="rounded bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
                >
                  Send ping
                </button>
              </div>

              <button
                onClick={markArrived}
                disabled={busy || dispatch.status !== 'EN_ROUTE'}
                className="w-full rounded bg-green-600 py-1.5 text-sm font-medium text-white hover:bg-green-700 disabled:opacity-50"
              >
                Arrived at hospital
              </button>

              {notice && (
                <div
                  className={`text-xs rounded px-2 py-1.5 flex items-center justify-between ${
                    notice.kind === 'success' ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'
                  }`}
                >
                  <span>{notice.text}</span>
                  <button onClick={() => setNotice(null)} className="ml-2 opacity-60 hover:opacity-100">
                    ✕
                  </button>
                </div>
              )}
            </div>
          </>
        )}
      </main>
    </div>
  )
}
