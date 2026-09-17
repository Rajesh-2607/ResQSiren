import { useState } from 'react'
import { ApiError, dispatchApi } from '../lib/api'
import type { Call, Dispatch } from '../lib/types'
import { SEVERITY_COLOR } from '../lib/types'

interface Props {
  calls: Call[]
  dispatches: Dispatch[]
  onDispatched: (dispatch: Dispatch) => void
}

export default function CallsPanel({ calls, dispatches, onDispatched }: Props) {
  const [dispatching, setDispatching] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const dispatchedCallIds = new Set(dispatches.map((d) => d.call_id))

  async function handleDispatch(callId: string) {
    setDispatching(callId)
    setError(null)
    try {
      const dispatch = (await dispatchApi.createDispatch({ call_id: callId })) as Dispatch
      onDispatched(dispatch)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Failed to dispatch')
    } finally {
      setDispatching(null)
    }
  }

  return (
    <div className="bg-white rounded-lg p-4 shadow-sm space-y-2">
      <h2 className="font-semibold text-gray-900">Calls</h2>
      {error && <p className="text-sm text-red-600">{error}</p>}
      {calls.length === 0 && <p className="text-sm text-gray-500">No calls logged yet.</p>}
      <ul className="space-y-2 max-h-64 overflow-y-auto">
        {calls.map((call) => {
          const dispatch = dispatches.find((d) => d.call_id === call.id)
          return (
            <li key={call.id} className="flex items-center justify-between gap-2 text-sm border-b border-gray-100 pb-2">
              <div>
                <span
                  className="inline-block w-2 h-2 rounded-full mr-2"
                  style={{ background: SEVERITY_COLOR[call.severity] }}
                />
                <span className="font-medium">{call.caller_name}</span>
                <span className="text-gray-500"> - {call.symptom.replaceAll('_', ' ')}</span>
              </div>
              {dispatch ? (
                <span className="text-xs text-gray-500 shrink-0">
                  amb {dispatch.ambulance_id} - ETA {Math.round(dispatch.eta_seconds)}s
                </span>
              ) : (
                <button
                  onClick={() => handleDispatch(call.id)}
                  disabled={dispatching === call.id || dispatchedCallIds.has(call.id)}
                  className="shrink-0 rounded bg-gray-900 px-2 py-1 text-xs text-white hover:bg-gray-700 disabled:opacity-50"
                >
                  {dispatching === call.id ? 'Dispatching...' : 'Dispatch'}
                </button>
              )}
            </li>
          )
        })}
      </ul>
    </div>
  )
}
