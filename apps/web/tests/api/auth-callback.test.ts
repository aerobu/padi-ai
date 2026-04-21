// @vitest-environment node
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { NextRequest } from "next/server";

// Mock global fetch so token exchange doesn't make a real network call
const originalFetch = global.fetch;

describe("Auth0 callback route", () => {
  beforeEach(() => {
    process.env.NEXT_PUBLIC_AUTH0_DOMAIN = "https://test.auth0.com";
    process.env.NEXT_PUBLIC_AUTH0_CLIENT_ID = "test-client";
    process.env.AUTH0_CLIENT_SECRET = "test-secret";
    global.fetch = vi.fn(async () =>
      new Response(JSON.stringify({ access_token: "tok", expires_in: 3600 }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      })
    ) as unknown as typeof fetch;
  });

  afterEach(() => {
    global.fetch = originalFetch;
    vi.clearAllMocks();
    vi.resetModules();
  });

  it("uses Origin header for origin when present (success path)", async () => {
    const { GET } = await import("@/app/api/auth/callback/route");
    const req = new NextRequest(
      "http://test.local/api/auth/callback?code=x&state=/dashboard",
      { headers: { origin: "https://app.example.com" } }
    );
    const res = await GET(req);
    expect(res.status).toBeGreaterThanOrEqual(300);
    expect(res.status).toBeLessThan(400);
    const location = res.headers.get("location")!;
    expect(location).toContain("/dashboard");
    expect(location).toMatch(/^https:\/\/app\.example\.com/);
    expect(res.headers.get("set-cookie")).toContain("auth_token=tok");
  });

  it("falls back to request URL origin when Origin header is missing", async () => {
    const { GET } = await import("@/app/api/auth/callback/route");
    const req = new NextRequest(
      "http://test.local/api/auth/callback?code=x&state=/dashboard"
    );
    const res = await GET(req);
    expect(res.status).toBeGreaterThanOrEqual(300);
    expect(res.status).toBeLessThan(400);
    const location = res.headers.get("location")!;
    expect(location).toContain("/dashboard");
    expect(location).toMatch(/^http:\/\/test\.local/);
    expect(res.headers.get("set-cookie")).toContain("auth_token=tok");
  });

  it("rejects cross-origin state and falls back to /dashboard on our origin", async () => {
    const { GET } = await import("@/app/api/auth/callback/route");
    const req = new NextRequest(
      "http://test.local/api/auth/callback?code=x&state=" +
        encodeURIComponent("https://evil.example.com/pwn"),
      { headers: { origin: "https://app.example.com" } }
    );
    const res = await GET(req);
    const location = res.headers.get("location")!;
    expect(location).not.toContain("evil.example.com");
    expect(location).toContain("app.example.com/dashboard");
  });

  it("redirects to /login on Auth0 error without crashing", async () => {
    const { GET } = await import("@/app/api/auth/callback/route");
    const req = new NextRequest(
      "http://test.local/api/auth/callback?error=access_denied",
      { headers: { origin: "https://app.example.com" } }
    );
    const res = await GET(req);
    expect(res.status).toBeGreaterThanOrEqual(300);
    expect(res.status).toBeLessThan(400);
    expect(res.headers.get("location")).toContain("/login");
    expect(res.headers.get("location")).toContain("error=access_denied");
  });

  it("redirects to /login on missing code without crashing", async () => {
    const { GET } = await import("@/app/api/auth/callback/route");
    const req = new NextRequest(
      "http://test.local/api/auth/callback?state=x"
    );
    const res = await GET(req);
    expect(res.status).toBeGreaterThanOrEqual(300);
    expect(res.status).toBeLessThan(400);
    expect(res.headers.get("location")).toContain("/login");
    expect(res.headers.get("location")).toContain("missing_code");
  });
});
