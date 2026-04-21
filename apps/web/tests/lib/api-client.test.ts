import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { apiClient } from "@/lib/api-client";

describe("apiClient auth behavior", () => {
  let fetchMock: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    fetchMock = vi.fn(async () =>
      new Response(JSON.stringify({ ok: true }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      })
    );
    global.fetch = fetchMock as unknown as typeof fetch;
  });

  afterEach(() => {
    vi.clearAllMocks();
    vi.restoreAllMocks();
  });

  it("sends credentials: include so httpOnly auth cookie is attached", async () => {
    await apiClient.getConsentStatus();
    const [, init] = fetchMock.mock.calls[0];
    expect(init.credentials).toBe("include");
  });

  it("does NOT read auth_token from localStorage", async () => {
    const spy = vi.spyOn(Storage.prototype, "getItem");
    await apiClient.getConsentStatus();
    expect(spy).not.toHaveBeenCalledWith("auth_token");
  });

  it("does NOT set Authorization: Bearer header", async () => {
    await apiClient.getConsentStatus();
    const [, init] = fetchMock.mock.calls[0];
    const headers = new Headers(init.headers as HeadersInit);
    expect(headers.get("Authorization")).toBeNull();
  });

  it("sets Content-Type: application/json", async () => {
    await apiClient.getConsentStatus();
    const [, init] = fetchMock.mock.calls[0];
    const headers = new Headers(init.headers as HeadersInit);
    expect(headers.get("Content-Type")).toBe("application/json");
  });

  it("redirects to /login on 401 (client side only)", async () => {
    fetchMock.mockResolvedValueOnce(
      new Response(JSON.stringify({ error: "unauth" }), { status: 401 })
    );
    const assignMock = vi.fn();
    // jsdom/happy-dom exposes window.location — stub assign
    Object.defineProperty(window, "location", {
      value: { ...window.location, assign: assignMock },
      writable: true,
    });
    await expect(apiClient.getConsentStatus()).rejects.toThrow();
    expect(assignMock).toHaveBeenCalledWith("/login");
  });
});
