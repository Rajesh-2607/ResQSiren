const DISPATCH_URL = import.meta.env.VITE_DISPATCH_URL ?? 'http://localhost:4101'
const ROUTING_URL = import.meta.env.VITE_ROUTING_URL ?? 'http://localhost:4102'

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
  listDispatches: () => request(DISPATCH_URL, '/dispatch'),
  reportApproaching: (dispatchId: string, body: unknown) =>
    request(DISPATCH_URL, `/dispatch/${dispatchId}/approaching`, {
      method: 'POST',
      body: JSON.stringify(body),
    }),
  markArrived: (dispatchId: string) =>
    request(DISPATCH_URL, `/dispatch/${dispatchId}/arrived`, { method: 'POST' }),
}

export const routingApi = {
  ambulances: () => request(ROUTING_URL, '/ambulances'),
  junctions: () => request(ROUTING_URL, '/junctions'),
}

export { DISPATCH_URL, ROUTING_URL }
