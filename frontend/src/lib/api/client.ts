import { ApiError, ApiErrorPayload } from "./types";

/**
 * Extracts a cookie value by name from document.cookie
 */
export function getCookie(name: string): string | null {
  if (typeof document === "undefined") {
    return null;
  }
  const match = document.cookie.match(new RegExp(`(^|;\\s*)(${name})=([^;]*)`));
  return match ? decodeURIComponent(match[3]) : null;
}

interface FetchOptions extends RequestInit {
  _isCsrfRetry?: boolean;
}

/**
 * Ensures CSRF token is fetched and set in the cookie
 */
export async function ensureCsrfToken(): Promise<void> {
  try {
    await fetch("/api/v1/auth/csrf/", {
      method: "GET",
      credentials: "same-origin",
    });
  } catch (err) {
    // If backend isn't ready or network drops, don't throw unhandled rejection here
    console.warn("Could not refresh CSRF cookie:", err);
  }
}

/**
 * Standard apiFetch wrapper
 * ARCHITECTURE.md §7:
 * - Credentials: same-origin
 * - Attaches X-CSRFToken from csrftoken cookie
 * - Only 401 with code 'not_authenticated' redirects to /login?next=...
 * - 403 'csrf_failed' triggers one silent refresh of CSRF token and retries request
 * - 403 'permission_denied' surfaces structured error without logging user out
 */
export async function apiFetch<T = unknown>(
  url: string,
  options: FetchOptions = {}
): Promise<T> {
  const method = (options.method || "GET").toUpperCase();
  const headers = new Headers(options.headers || {});

  // For state-mutating requests, attach X-CSRFToken header if not already present
  if (["POST", "PUT", "PATCH", "DELETE"].includes(method)) {
    const csrfToken = getCookie("csrftoken");
    if (csrfToken && !headers.has("X-CSRFToken")) {
      headers.set("X-CSRFToken", csrfToken);
    }
  }

  // Set default Content-Type to JSON if body is a string and not form-data
  if (options.body && typeof options.body === "string" && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(url, {
    ...options,
    method,
    headers,
    credentials: "same-origin",
  });

  // Handle successful response (2xx)
  if (response.ok) {
    if (response.status === 204) {
      return null as T;
    }
    const contentType = response.headers.get("Content-Type") || "";
    if (contentType.includes("application/json")) {
      return (await response.json()) as T;
    }
    return (await response.text()) as unknown as T;
  }

  // Parse structured error payload
  let errorPayload: Partial<ApiErrorPayload> = {};
  try {
    errorPayload = await response.json();
  } catch {
    errorPayload = {
      code: "http_error",
      message: response.statusText || `Request failed with status ${response.status}`,
    };
  }

  const apiError = new ApiError(response.status, errorPayload);

  // CSRF token failure retry: 403 with code "csrf_failed"
  if (response.status === 403 && apiError.code === "csrf_failed" && !options._isCsrfRetry) {
    await ensureCsrfToken();
    return apiFetch<T>(url, { ...options, _isCsrfRetry: true });
  }

  // Session expiry / unauthenticated: 401 with code "not_authenticated"
  if (response.status === 401 && apiError.code === "not_authenticated") {
    if (typeof window !== "undefined" && !window.location.pathname.startsWith("/login")) {
      const returnUrl = encodeURIComponent(window.location.pathname + window.location.search);
      // eslint-disable-next-line @next/next/no-location-assign-relative-destination
      window.location.href = `/login?next=${returnUrl}`;
    }
  }

  throw apiError;
}
