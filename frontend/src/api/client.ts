const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

export class ApiError extends Error {
  status: number;
  code: string | undefined;

  constructor(status: number, message: string, code?: string) {
    super(message);
    this.status = status;
    this.code = code;
  }
}

function getToken(): string | null {
  return localStorage.getItem("access_token");
}

export function setToken(token: string | null): void {
  if (token) {
    localStorage.setItem("access_token", token);
  } else {
    localStorage.removeItem("access_token");
  }
}

async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const token = getToken();
  const headers = new Headers(options.headers);
  headers.set("Content-Type", "application/json");
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      headers,
    });
  } catch {
    // fetch() itself throws (not an HTTP error response) when the
    // server is unreachable -- wrong port, not running, DNS/network
    // failure, or a CORS preflight rejection. Without this, that
    // exception propagated uncaught past every caller's
    // `err instanceof ApiError` check, so it fell through to a
    // generic hardcoded string (e.g. "Registration failed.")
    // identical to what a real validation error shows, hiding the
    // actual cause (server unreachable) from the user.
    throw new ApiError(
      0,
      `Could not reach the server at ${API_BASE_URL}. Check that it is running and reachable.`,
    );
  }

  if (response.status === 204) {
    return undefined as T;
  }

  const body = await response.json().catch(() => null);

  if (!response.ok) {
    // FastAPI errors are either {"detail": "..."} (HTTPException,
    // used for auth/authorization failures) or
    // {"error": {"code", "message"}} (the app's ValueError/
    // IntegrityError handlers). Normalize both into ApiError.
    const message =
      body?.error?.message ??
      (typeof body?.detail === "string"
        ? body.detail
        : "Request failed.");

    // A 401 from any *protected* endpoint means the stored token
    // is missing/invalid/expired -- broadcast so AuthContext can
    // log out and ProtectedRoute can redirect, instead of leaving
    // every panel stuck showing its own "could not load" error
    // forever. /auth/login's own 401 (wrong password) is a normal
    // form-validation outcome, not a session expiry, so it's
    // excluded.
    if (response.status === 401 && path !== "/auth/login") {
      window.dispatchEvent(new CustomEvent("api:unauthorized"));
    }

    throw new ApiError(response.status, message, body?.error?.code);
  }

  return body as T;
}

export const api = {
  get: <T>(path: string) => request<T>(path, { method: "GET" }),
  post: <T>(path: string, data?: unknown) =>
    request<T>(path, {
      method: "POST",
      body: data !== undefined ? JSON.stringify(data) : undefined,
    }),
};
