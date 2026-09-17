export class ApiError extends Error {
  status: number;
  detail: unknown;

  constructor(status: number, detail: unknown) {
    super(typeof detail === "string" ? detail : JSON.stringify(detail));
    this.status = status;
    this.detail = detail;
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers);
  headers.set("Content-Type", "application/json");

  const res = await fetch(path, { ...options, headers });
  const text = await res.text();
  const body = text ? JSON.parse(text) : null;

  if (!res.ok) {
    throw new ApiError(res.status, body?.detail ?? body);
  }
  return body as T;
}

export const api = {
  post: <T,>(path: string, body: unknown) =>
    request<T>(path, { method: "POST", body: JSON.stringify(body) }),
  get: <T,>(path: string) => request<T>(path),
};

const DETAIL_MESSAGES: Record<string, string> = {
  UNKNOWN_DISPATCH: "That dispatch ID doesn't exist.",
  NO_AMBULANCE_AVAILABLE: "Every ambulance is currently busy — please call emergency services directly.",
  NO_HOSPITAL_AVAILABLE: "No hospital is available to accept this patient right now.",
  NO_LOCATION: "No location has been reported yet.",
};

export function describeApiError(err: unknown): string {
  if (!(err instanceof ApiError)) return "Something went wrong. Please try again.";

  const { detail } = err;
  if (typeof detail === "string" && DETAIL_MESSAGES[detail]) return DETAIL_MESSAGES[detail];
  if (typeof detail === "string") return detail;

  if (Array.isArray(detail)) {
    // FastAPI/pydantic validation error array: [{loc, msg, type}, ...]
    const messages = detail
      .map((d) => (d && typeof d === "object" && "msg" in d ? String((d as { msg: unknown }).msg) : null))
      .filter(Boolean);
    if (messages.length) return messages.join("; ");
  }

  return `Request failed (${err.status}).`;
}
