import { useWebSocketFeed } from '../lib/useWebSocket'
import type { SignalPreemption } from '../lib/types'

const SIGNAL_URL = (import.meta.env.VITE_SIGNAL_URL ?? 'http://localhost:4104').replace(/^http/, 'ws') + '/ws'

export default function SignalLog() {
  const { messages, connected } = useWebSocketFeed(SIGNAL_URL, 20)
  const preemptions = messages.filter((m) => m.type === 'signal.preemption')

  return (
    <div className="bg-white rounded-lg p-4 shadow-sm space-y-2">
      <div className="flex items-center justify-between">
        <h2 className="font-semibold text-gray-900">Mock ITMS signal log</h2>
        <span className={`text-xs ${connected ? 'text-green-600' : 'text-gray-400'}`}>
          {connected ? '● live' : '○ connecting...'}
        </span>
      </div>
      {preemptions.length === 0 && <p className="text-xs text-gray-400">No signal commands yet.</p>}
      <ul className="space-y-1 max-h-48 overflow-y-auto font-mono text-xs">
        {preemptions.map((m, i) => {
          const p = m.payload as SignalPreemption
          return (
            <li key={`${p.ts}-${i}`} className="text-gray-700">
              [{new Date(p.ts).toLocaleTimeString()}] {p.message}
            </li>
          )
        })}
      </ul>
    </div>
  )
}
