import { useEffect, useRef, useState } from 'react'

export interface WsMessage<T = unknown> {
  type: string
  payload: T
}

/** Connects to a service's live `/ws` feed and keeps the most recent messages. */
export function useWebSocketFeed(url: string, maxItems = 30) {
  const [messages, setMessages] = useState<WsMessage[]>([])
  const [connected, setConnected] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    let cancelled = false
    let retryTimer: ReturnType<typeof setTimeout>

    function connect() {
      if (cancelled) return
      const ws = new WebSocket(url)
      wsRef.current = ws

      ws.onopen = () => setConnected(true)
      ws.onclose = () => {
        setConnected(false)
        if (!cancelled) retryTimer = setTimeout(connect, 2000)
      }
      ws.onerror = () => ws.close()
      ws.onmessage = (event) => {
        try {
          const parsed = JSON.parse(event.data) as WsMessage
          setMessages((prev) => [parsed, ...prev].slice(0, maxItems))
        } catch {
          // ignore malformed frames
        }
      }
    }

    connect()
    return () => {
      cancelled = true
      clearTimeout(retryTimer)
      wsRef.current?.close()
    }
  }, [url, maxItems])

  return { messages, connected }
}
