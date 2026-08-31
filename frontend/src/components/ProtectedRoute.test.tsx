import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ProtectedRoute } from "./ProtectedRoute";
import { AuthProvider } from "../auth/AuthContext";
import { api, ApiError, setToken } from "../api/client";
import { regularUser } from "../test/testUsers";

vi.mock("../api/client", async () => {
  const actual =
    await vi.importActual<typeof import("../api/client")>(
      "../api/client",
    );
  return {
    ...actual,
    api: { get: vi.fn(), post: vi.fn() },
  };
});

function renderProtected() {
  return render(
    <MemoryRouter initialEntries={["/dashboard"]}>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<div>login page</div>} />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <div>secret dashboard</div>
              </ProtectedRoute>
            }
          />
        </Routes>
      </AuthProvider>
    </MemoryRouter>,
  );
}

describe("ProtectedRoute", () => {
  beforeEach(() => {
    vi.mocked(api.get).mockReset();
    localStorage.clear();
  });

  it("redirects to /login when unauthenticated", async () => {
    vi.mocked(api.get).mockRejectedValueOnce(
      new ApiError(401, "no session"),
    );

    renderProtected();

    await waitFor(() =>
      expect(screen.getByText("login page")).toBeInTheDocument(),
    );
  });

  it("renders the protected content for an authenticated user", async () => {
    setToken("valid-token");
    vi.mocked(api.get).mockResolvedValueOnce(regularUser);

    renderProtected();

    await waitFor(() =>
      expect(screen.getByText("secret dashboard")).toBeInTheDocument(),
    );
  });
});
