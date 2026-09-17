import { SEVERITY_COLOR } from '../lib/types'
import type { Dispatch } from '../lib/types'

interface Props {
  dispatches: Dispatch[]
}

export default function ArrivedList({ dispatches }: Props) {
  const recent = dispatches.slice(0, 10)

  return (
    <div className="bg-white rounded-lg p-4 shadow-sm">
      <h2 className="font-semibold text-gray-900 text-sm mb-2">Recently arrived</h2>
      {recent.length === 0 ? (
        <p className="text-xs text-gray-400">None yet.</p>
      ) : (
        <ul className="space-y-1 text-xs">
          {recent.map((d) => (
            <li key={d.id} className="flex items-center gap-2 text-gray-600">
              <span
                className="inline-block w-2 h-2 rounded-full"
                style={{ background: SEVERITY_COLOR[d.severity] }}
              />
              Ambulance {d.ambulance_id} arrived (dispatch {d.id.slice(0, 8)})
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
