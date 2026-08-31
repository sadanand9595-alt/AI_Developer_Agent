import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { AuthProvider, useAuth } from "./AuthContext";
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

function Consumer() {
  const { user, loading, logout } = useAuth();
  return (
    <div>
      <span data-testid="loading">{String(loading)}</span>
      <span data-testid="user">{user ? user.email : "none"}</span>
      <button onClick={logout}>logout</button>
    </div>
  );
}

describe("AuthContext", () => {
  beforeEach(() => {
    vi.mocked(api.get).mockReset();
    vi.mocked(api.post).mockReset();
    localStorage.clear();
  });

  it("loads the current user when a valid token is stored", async () => {
    setToken("valid-token");
    vi.mocked(api.get).mockResolvedValueOnce(regularUser);

    render(
      <AuthProvider>
        <Consumer />
      </AuthProvider>,
    );

    await waitFor(() =>
      expect(screen.getByTestId("loading")).toHaveTextContent("false"),
    );
    expect(screen.getByTestId("user")).toHaveTextContent(
      regularUser.email,
    );
    expect(api.get).toHaveBeenCalledWith("/auth/me");
  });

  it("clears the session when /auth/me fails on mount", async () => {
    setToken("stale-token");
    vi.mocked(api.get).mockRejectedValueOnce(
      new ApiError(401, "Could not validate credentials."),
    );

    render(
      <AuthProvider>
        <Consumer />
      </AuthProvider>,
    );

    await waitFor(() =>
      expect(screen.getByTestId("loading")).toHaveTextContent("false"),
    );
    expect(screen.getByTestId("user")).toHaveTextContent("none");
    expect(localStorage.getItem("access_token")).toBeNull();
  });

  it("logs out when an api:unauthorized event fires", async () => {
    setToken("valid-token");
    vi.mocked(api.get).mockResolvedValueOnce(regularUser);

    render(
      <AuthProvider>
        <Consumer />
      </AuthProvider>,
    );

    await waitFor(() =>
      expect(screen.getByTestId("user")).toHaveTextContent(
        regularUser.email,
      ),
    );

    window.dispatchEvent(new CustomEvent("api:unauthorized"));

    await waitFor(() =>
      expect(screen.getByTestId("user")).toHaveTextContent("none"),
    );
    expect(localStorage.getItem("access_token")).toBeNull();
  });

  it("logs out via the logout() call", async () => {
    setToken("valid-token");
    vi.mocked(api.get).mockResolvedValueOnce(regularUser);

    render(
      <AuthProvider>
        <Consumer />
      </AuthProvider>,
    );

    await waitFor(() =>
      expect(screen.getByTestId("user")).toHaveTextContent(
        regularUser.email,
      ),
    );

    await userEvent.click(screen.getByText("logout"));

    expect(screen.getByTestId("user")).toHaveTextContent("none");
    expect(localStorage.getItem("access_token")).toBeNull();
  });
});
