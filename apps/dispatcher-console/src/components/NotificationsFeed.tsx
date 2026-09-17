import { useWebSocketFeed } from '../lib/useWebSocket'
import type { NotificationEntry } from '../lib/types'

const NOTIFY_URL = (import.meta.env.VITE_NOTIFY_URL ?? 'http://localhost:4105').replace(/^http/, 'ws') + '/ws'

const CHANNEL_LABEL: Record<string, string> = {
  hospital: '🏥 Hospital',
  police: '🚓 Police',
  public: '📢 Public',
}

export default function NotificationsFeed() {
  const { messages, connected } = useWebSocketFeed(NOTIFY_URL, 20)
  const notifications = messages.filter((m) => m.type === 'notification.sent')

  return (
    <div className="bg-white rounded-lg p-4 shadow-sm space-y-2">
      <div className="flex items-center justify-between">
        <h2 className="font-semibold text-gray-900">Notifications</h2>
        <span className={`text-xs ${connected ? 'text-green-600' : 'text-gray-400'}`}>
          {connected ? '● live' : '○ connecting...'}
        </span>
      </div>
      {notifications.length === 0 && <p className="text-xs text-gray-400">No notifications yet.</p>}
      <ul className="space-y-2 max-h-48 overflow-y-auto text-xs">
        {notifications.map((m, i) => {
          const n = m.payload as NotificationEntry
          return (
            <li key={`${n.subject}-${i}`} className="border-b border-gray-100 pb-1">
              <p className="font-medium">
                {CHANNEL_LABEL[n.channel] ?? n.channel} - {n.subject}
              </p>
              <p className="text-gray-500">{n.body}</p>
            </li>
          )
        })}
      </ul>
    </div>
  )
}
