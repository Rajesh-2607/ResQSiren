import { useMemo, useState } from 'react'
import { ApiError, CONFLICT_URL, conflictApi } from '../lib/api'
import { useWebSocketFeed } from '../lib/useWebSocket'
import { SEVERITY_COLOR } from '../lib/types'
import type { Ambulance, ArbitrationResult, Junction, Severity } from '../lib/types'

interface Props {
  junctions: Junction[]
  ambulances: Ambulance[]
}

const WS_URL = CONFLICT_URL.replace(/^http/, 'ws') + '/ws'

export default function JunctionArbitration({ junctions, ambulances }: Props) {
  const { messages, connected } = useWebSocketFeed(WS_URL, 50)
  const [junctionId, setJunctionId] = useState(junctions[0]?.id ?? '')
  const [severityA, setSeverityA] = useState<Severity>('YELLOW')
  const [severityB, setSeverityB] = useState<Severity>('RED')
  const [triggering, setTriggering] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const latestByJunction = useMemo(() => {
    const map = new Map<string, ArbitrationResult>()
    for (const m of messages) {
      if (m.type !== 'arbitration.result') continue
      const result = m.payload as ArbitrationResult
      if (!map.has(result.junction_id)) map.set(result.junction_id, result)
    }
    return map
  }, [messages])

  async function triggerConvergence() {
    if (ambulances.length < 2) return
    setTriggering(true)
    setError(null)
    try {
      await conflictApi.demoConverge({
        junction_id: junctionId,
        duration_seconds: 20,
        ambulances: [
          { ambulance_id: ambulances[0].id, severity: severityA, initial_eta_seconds: 20 },
          { ambulance_id: ambulances[1].id, severity: severityB, initial_eta_seconds: 22 },
        ],
      })
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Failed to trigger scenario')
    } finally {
      setTriggering(false)
    }
  }

  return (
    <div className="bg-white rounded-lg p-4 shadow-sm space-y-3">
      <div className="flex items-center justify-between">
        <h2 className="font-semibold text-gray-900">Junction arbitration</h2>
        <span className={`text-xs ${connected ? 'text-green-600' : 'text-gray-400'}`}>
          {connected ? '● live' : '○ connecting...'}
        </span>
      </div>

      <div className="flex flex-wrap items-end gap-2 text-xs bg-gray-50 rounded p-2">
        <div>
          <label className="block text-gray-500 mb-0.5">Junction</label>
          <select
            value={junctionId}
            onChange={(e) => setJunctionId(e.target.value)}
            className="rounded border border-gray-300 px-1.5 py-1"
          >
            {junctions.map((j) => (
              <option key={j.id} value={j.id}>
                {j.name}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-gray-500 mb-0.5">Ambulance A</label>
          <select
            value={severityA}
            onChange={(e) => setSeverityA(e.target.value as Severity)}
            className="rounded border border-gray-300 px-1.5 py-1"
          >
            <option value="RED">RED</option>
            <option value="YELLOW">YELLOW</option>
            <option value="GREEN">GREEN</option>
          </select>
        </div>
        <div>
          <label className="block text-gray-500 mb-0.5">Ambulance B</label>
          <select
            value={severityB}
            onChange={(e) => setSeverityB(e.target.value as Severity)}
            className="rounded border border-gray-300 px-1.5 py-1"
          >
            <option value="RED">RED</option>
            <option value="YELLOW">YELLOW</option>
            <option value="GREEN">GREEN</option>
          </select>
        </div>
        <button
          onClick={triggerConvergence}
          disabled={triggering}
          className="rounded bg-indigo-600 px-3 py-1.5 text-white font-medium hover:bg-indigo-700 disabled:opacity-50"
        >
          {triggering ? 'Starting...' : 'Simulate convergence'}
        </button>
      </div>
      {error && <p className="text-xs text-red-600">{error}</p>}

      <div className="space-y-3">
        {junctions.map((j) => {
          const result = latestByJunction.get(j.id)
          const maxScore = Math.max(300, ...(result?.ranked.map((r) => r.score) ?? [0]))
          return (
            <div key={j.id} className="border border-gray-100 rounded p-2">
              <p className="text-xs font-medium text-gray-700">{j.name}</p>
              {!result || result.ranked.length === 0 ? (
                <p className="text-xs text-gray-400">No active claims</p>
              ) : (
                <ul className="space-y-1 mt-1">
                  {result.ranked.map((r, idx) => (
                    <li key={r.dispatch_id} className="text-xs">
                      <div className="flex justify-between">
                        <span>
                          {idx === 0 && '🏆 '}
                          {r.ambulance_id} ({r.severity}) - wait {Math.round(r.wait_seconds)}s
                        </span>
                        <span>{Math.round(r.score)}</span>
                      </div>
                      <div className="h-1.5 rounded bg-gray-100 overflow-hidden">
                        <div
                          className="h-full"
                          style={{
                            width: `${Math.max(0, (r.score / maxScore) * 100)}%`,
                            background: SEVERITY_COLOR[r.severity],
                          }}
                        />
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
