import { describe, it, expect, vi, afterEach } from "vitest";
import { api, ApiError, send } from "@/lib/api";
afterEach(() => vi.unstubAllGlobals());
describe("API boundary", () => {
  it("sends same-origin cookies and a CSRF token for mutations", async () => {
    document.cookie = "tl_csrf=testing-token";
    const fetch = vi.fn().mockResolvedValue(new Response(JSON.stringify({ ok: true }), { status: 200 }));
    vi.stubGlobal("fetch", fetch);
    await api("/auth/logout", send("POST"));
    const options = fetch.mock.calls[0][1];
    expect(options.credentials).toBe("include");
    expect(options.headers.get("X-CSRF-Token")).toBe("testing-token");
  });
  it("preserves actionable backend validation messages", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValue(
          new Response(JSON.stringify({ detail: [{ msg: "Review job requirements" }] }), { status: 422 }),
        ),
    );
    await expect(api("/jobs")).rejects.toThrow("Review job requirements");
  });
  it("exposes authorization failures without treating them as empty records", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response(JSON.stringify({ detail: "Please sign in" }), { status: 401 })),
    );
    await expect(api("/resumes")).rejects.toBeInstanceOf(ApiError);
  });
});
