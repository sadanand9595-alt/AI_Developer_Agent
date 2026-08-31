import { afterEach, describe, expect, it, vi } from "vitest";
import { api, ApiError } from "./client";

describe("api client", () => {
  const originalFetch = global.fetch;

  afterEach(() => {
    global.fetch = originalFetch;
  });

  it("throws a distinct ApiError when the server is unreachable", async () => {
    global.fetch = vi.fn().mockRejectedValue(new TypeError("Failed to fetch"));

    await expect(
      api.post("/auth/register", {
        email: "x@example.com",
        name: "X",
        password: "password123",
      }),
    ).rejects.toMatchObject({
      status: 0,
    });
  });

  it("does not confuse a network failure with a normal HTTP error", async () => {
    global.fetch = vi.fn().mockRejectedValue(new TypeError("Failed to fetch"));

    try {
      await api.get("/auth/me");
      expect.unreachable("should have thrown");
    } catch (err) {
      expect(err).toBeInstanceOf(ApiError);
      expect((err as ApiError).message).toMatch(/could not reach/i);
    }
  });

  it("parses a normal HTTP error response as before", async () => {
    global.fetch = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          error: { code: "VALIDATION_ERROR", message: "Bad input." },
        }),
        { status: 400 },
      ),
    );

    await expect(api.get("/tasks")).rejects.toMatchObject({
      status: 400,
      message: "Bad input.",
      code: "VALIDATION_ERROR",
    });
  });
});
