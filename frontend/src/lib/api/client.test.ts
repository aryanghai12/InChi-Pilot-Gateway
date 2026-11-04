import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { apiFetch, getCookie } from "./client";
import { ApiError } from "./types";

describe("getCookie", () => {
  beforeEach(() => {
    // Clear cookies in jsdom
    document.cookie.split(";").forEach((c) => {
      const eq = c.indexOf("=");
      const name = eq > -1 ? c.substring(0, eq).trim() : c.trim();
      if (name) {
        document.cookie = `${name}=;expires=Thu, 01 Jan 1970 00:00:00 GMT;path=/`;
      }
    });
  });

  it("extracts cookie by name", () => {
    document.cookie = "csrftoken=test-token-123; other=value";
    expect(getCookie("csrftoken")).toBe("test-token-123");
  });

  it("returns null if cookie does not exist", () => {
    document.cookie = "other=value";
    expect(getCookie("csrftoken")).toBeNull();
  });
});

describe("apiFetch", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
    document.cookie = "csrftoken=valid-csrf-token";
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("sends credentials same-origin and attaches X-CSRFToken on POST requests", async () => {
    const mockFetch = vi.mocked(fetch).mockResolvedValueOnce(
      new Response(JSON.stringify({ success: true }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      })
    );

    const res = await apiFetch<{ success: boolean }>("/api/v1/test/", {
      method: "POST",
      body: JSON.stringify({ name: "test" }),
    });

    expect(res).toEqual({ success: true });
    expect(mockFetch).toHaveBeenCalledTimes(1);

    const callArgs = mockFetch.mock.calls[0];
    const options = callArgs[1] as RequestInit;
    expect(options.credentials).toBe("same-origin");

    const headers = options.headers as Headers;
    expect(headers.get("X-CSRFToken")).toBe("valid-csrf-token");
    expect(headers.get("Content-Type")).toBe("application/json");
  });

  it("parses structured error response and throws ApiError", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          code: "permission_denied",
          message: "You do not have permission to view this resource.",
          field_errors: { email: ["Invalid domain"] },
          correlation_id: "corr-123",
        }),
        {
          status: 403,
          headers: { "Content-Type": "application/json" },
        }
      )
    );

    await expect(apiFetch("/api/v1/forbidden/")).rejects.toThrow(ApiError);

    try {
      await apiFetch("/api/v1/forbidden/");
    } catch (err) {
      if (err instanceof ApiError) {
        expect(err.status).toBe(403);
        expect(err.code).toBe("permission_denied");
        expect(err.correlationId).toBe("corr-123");
        expect(err.fieldErrors).toEqual({ email: ["Invalid domain"] });
      }
    }
  });

  it("retries once when receiving 403 csrf_failed", async () => {
    const mockFetch = vi
      .mocked(fetch)
      // First call fails with csrf_failed
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            code: "csrf_failed",
            message: "CSRF token missing or incorrect.",
          }),
          { status: 403, headers: { "Content-Type": "application/json" } }
        )
      )
      // Second call is ensureCsrfToken: GET /api/v1/auth/csrf/
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ detail: "CSRF cookie set" }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        })
      )
      // Third call is the retried request which succeeds
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ retried: true }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        })
      );

    const result = await apiFetch<{ retried: boolean }>("/api/v1/action/", {
      method: "POST",
    });

    expect(result).toEqual({ retried: true });
    expect(mockFetch).toHaveBeenCalledTimes(3);
  });
});
