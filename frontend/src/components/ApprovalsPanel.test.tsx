import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ApprovalsPanel } from "./ApprovalsPanel";
import { useAuth } from "../auth/AuthContext";
import { api } from "../api/client";
import { adminUser, regularUser } from "../test/testUsers";
import type { ApprovalRequest } from "../api/types";

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

vi.mock("../auth/AuthContext", async () => {
  const actual =
    await vi.importActual<typeof import("../auth/AuthContext")>(
      "../auth/AuthContext",
    );
  return { ...actual, useAuth: vi.fn() };
});

const pendingApproval: ApprovalRequest = {
  id: "approval-1",
  user_id: "user-1",
  action: "delete_file",
  reason: "Cleanup",
  requested_operation: "Delete a file.",
  status: "pending",
  requested_at: "2026-01-01T00:00:00Z",
  reviewed_at: null,
};

function mockAuth(user: typeof regularUser | typeof adminUser) {
  vi.mocked(useAuth).mockReturnValue({
    user,
    loading: false,
    error: null,
    login: vi.fn(),
    register: vi.fn(),
    logout: vi.fn(),
  });
}

describe("ApprovalsPanel", () => {
  beforeEach(() => {
    vi.mocked(api.get).mockReset();
    vi.mocked(api.post).mockReset();
  });

  it("shows own pending approvals for a non-admin user", async () => {
    mockAuth(regularUser);
    vi.mocked(api.get).mockResolvedValueOnce([pendingApproval]);

    render(<ApprovalsPanel />);

    await waitFor(() =>
      expect(screen.getByText("delete_file")).toBeInTheDocument(),
    );
    expect(
      screen.queryByText("Review a request (admin)"),
    ).not.toBeInTheDocument();
  });

  it("shows an empty state when there are no approvals", async () => {
    mockAuth(regularUser);
    vi.mocked(api.get).mockResolvedValueOnce([]);

    render(<ApprovalsPanel />);

    await waitFor(() =>
      expect(
        screen.getByText("No pending approval requests."),
      ).toBeInTheDocument(),
    );
  });

  it("shows the admin review section for an admin user", async () => {
    mockAuth(adminUser);
    vi.mocked(api.get).mockResolvedValueOnce([]);

    render(<ApprovalsPanel />);

    await waitFor(() =>
      expect(
        screen.getByText("Review a request (admin)"),
      ).toBeInTheDocument(),
    );
  });

  it("looks up and approves a request as admin", async () => {
    const user = userEvent.setup();
    mockAuth(adminUser);
    vi.mocked(api.get)
      .mockResolvedValueOnce([]) // /approvals/me
      .mockResolvedValueOnce(pendingApproval) // GET /approvals/{id}
      .mockResolvedValueOnce([]); // /approvals/me refresh after action

    vi.mocked(api.post).mockResolvedValueOnce({
      ...pendingApproval,
      status: "approved",
      reviewed_at: "2026-01-02T00:00:00Z",
    });

    render(<ApprovalsPanel />);

    await waitFor(() =>
      expect(
        screen.getByText("Review a request (admin)"),
      ).toBeInTheDocument(),
    );

    await user.type(
      screen.getByPlaceholderText("Approval ID"),
      "approval-1",
    );
    await user.click(screen.getByText("Look up"));

    await waitFor(() =>
      expect(api.get).toHaveBeenCalledWith("/approvals/approval-1"),
    );
    await waitFor(() =>
      expect(screen.getByText(/Delete a file\./)).toBeInTheDocument(),
    );

    await user.click(screen.getByText("Approve"));

    await waitFor(() =>
      expect(api.post).toHaveBeenCalledWith(
        "/approvals/approval-1/approve",
        { comment: null },
      ),
    );
    await waitFor(() =>
      expect(screen.getAllByText("approved").length).toBeGreaterThan(0),
    );
  });

  it("rejects a request as admin", async () => {
    const user = userEvent.setup();
    mockAuth(adminUser);
    vi.mocked(api.get)
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce(pendingApproval)
      .mockResolvedValueOnce([]);

    vi.mocked(api.post).mockResolvedValueOnce({
      ...pendingApproval,
      status: "rejected",
      reviewed_at: "2026-01-02T00:00:00Z",
    });

    render(<ApprovalsPanel />);

    await waitFor(() =>
      expect(
        screen.getByText("Review a request (admin)"),
      ).toBeInTheDocument(),
    );

    await user.type(
      screen.getByPlaceholderText("Approval ID"),
      "approval-1",
    );
    await user.click(screen.getByText("Look up"));

    await waitFor(() =>
      expect(screen.getByText("Reject")).toBeInTheDocument(),
    );
    await user.click(screen.getByText("Reject"));

    await waitFor(() =>
      expect(api.post).toHaveBeenCalledWith(
        "/approvals/approval-1/reject",
        { comment: null },
      ),
    );
    await waitFor(() =>
      expect(screen.getAllByText("rejected").length).toBeGreaterThan(0),
    );
  });
});
