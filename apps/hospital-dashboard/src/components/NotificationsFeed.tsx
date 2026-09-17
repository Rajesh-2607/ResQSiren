import { useWebSocketFeed } from '../lib/useWebSocket'
import type { NotificationEntry } from '../lib/types'

const NOTIFY_URL = (import.meta.env.VITE_NOTIFY_URL ?? 'http://localhost:4105').replace(/^http/, 'ws') + '/ws'

export default function NotificationsFeed() {
  const { messages, connected } = useWebSocketFeed(NOTIFY_URL, 20)
  const hospitalAlerts = messages.filter((m) => {
    if (m.type !== 'notification.sent') return false
    const payload = m.payload as NotificationEntry
    return payload.channel === 'hospital'
  })

  return (
    <div className="bg-white rounded-lg p-4 shadow-sm space-y-2">
      <div className="flex items-center justify-between">
        <h2 className="font-semibold text-gray-900 text-sm">Advance alerts</h2>
        <span className={`text-xs ${connected ? 'text-green-600' : 'text-gray-400'}`}>
          {connected ? '● live' : '○ connecting...'}
        </span>
      </div>
      {hospitalAlerts.length === 0 && <p className="text-xs text-gray-400">No advance alerts yet.</p>}
      <ul className="space-y-2 max-h-48 overflow-y-auto text-xs">
        {hospitalAlerts.map((m, i) => {
          const n = m.payload as NotificationEntry
          return (
            <li key={`${n.subject}-${i}`} className="border-b border-gray-100 pb-1">
              <p className="font-medium">{n.subject}</p>
              <p className="text-gray-500">{n.body}</p>
            </li>
          )
        })}
      </ul>
    </div>
  )
}
