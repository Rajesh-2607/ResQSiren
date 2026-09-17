import { mockPatientSummary } from '../lib/patientSummary'
import { SEVERITY_COLOR } from '../lib/types'
import type { Call, Dispatch } from '../lib/types'

const SEVERITY_LABEL: Record<string, string> = {
  RED: 'RED - critical',
  YELLOW: 'YELLOW - urgent',
  GREEN: 'GREEN - stable',
}

interface Props {
  dispatch: Dispatch
  call: Call | undefined
}

export default function IncomingCard({ dispatch, call }: Props) {
  const color = SEVERITY_COLOR[dispatch.severity]

  return (
    <div className="bg-white rounded-lg p-4 shadow-sm border-l-4" style={{ borderColor: color }}>
      <div className="flex items-center justify-between">
        <span
          className="text-xs font-semibold px-2 py-0.5 rounded-full text-white"
          style={{ background: color }}
        >
          {SEVERITY_LABEL[dispatch.severity] ?? dispatch.severity}
        </span>
        <span className="text-xs text-gray-500">ETA {Math.round(dispatch.eta_seconds)}s</span>
      </div>

      <p className="mt-2 text-sm font-medium text-gray-900">
        Ambulance {dispatch.ambulance_id}
        {call ? ` - ${call.caller_name}` : ''}
      </p>

      {call && (
        <div className="mt-2 rounded bg-gray-50 p-2 text-xs text-gray-700">
          <p className="font-semibold text-gray-500 mb-1">
            Mock patient summary (no ABHA integration in this build)
          </p>
          <p>{mockPatientSummary(call.symptom, call.severity, call.attendant_consent)}</p>
        </div>
      )}
    </div>
  )
}
