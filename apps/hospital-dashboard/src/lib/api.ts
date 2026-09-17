const DISPATCH_URL = import.meta.env.VITE_DISPATCH_URL ?? 'http://localhost:4101'
const ROUTING_URL = import.meta.env.VITE_ROUTING_URL ?? 'http://localhost:4102'
const NOTIFY_URL = import.meta.env.VITE_NOTIFY_URL ?? 'http://localhost:4105'

export class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

async function request<T>(base: string, path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${base}${path}`, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...init?.headers },
  })
  if (!res.ok) {
    const body = await res.text().catch(() => '')
    throw new ApiError(res.status, body || res.statusText)
  }
  if (res.status === 204) return undefined as T
  return res.json() as Promise<T>
}

export const dispatchApi = {
  listCalls: () => request(DISPATCH_URL, '/calls'),
  listDispatches: () => request(DISPATCH_URL, '/dispatch'),
}

export const routingApi = {
  hospitals: () => request(ROUTING_URL, '/hospitals'),
}

export const notifyApi = {
  listNotifications: () => request(NOTIFY_URL, '/notifications'),
}

export { DISPATCH_URL, ROUTING_URL, NOTIFY_URL }
