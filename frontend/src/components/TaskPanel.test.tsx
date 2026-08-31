import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { TaskPanel } from "./TaskPanel";
import { api, ApiError } from "../api/client";
import type { Task } from "../api/types";

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

const baseTask: Task = {
  id: "task-1",
  user_id: "user-1",
  title: "Existing task",
  description: "d",
  status: "pending",
  priority: 0,
  retry_count: 0,
  created_at: "2026-01-01T00:00:00Z",
  started_at: null,
  completed_at: null,
};

describe("TaskPanel", () => {
  beforeEach(() => {
    vi.mocked(api.get).mockReset();
    vi.mocked(api.post).mockReset();
  });

  it("shows an empty state when there are no tasks", async () => {
    vi.mocked(api.get).mockResolvedValueOnce([]);

    render(<TaskPanel />);

    await waitFor(() =>
      expect(screen.getByText("No tasks yet.")).toBeInTheDocument(),
    );
  });

  it("shows an error state when the list fails to load", async () => {
    vi.mocked(api.get).mockRejectedValueOnce(
      new ApiError(500, "Server exploded."),
    );

    render(<TaskPanel />);

    await waitFor(() =>
      expect(screen.getByText("Server exploded.")).toBeInTheDocument(),
    );
  });

  it("renders tasks and creates a new one", async () => {
    const user = userEvent.setup();
    vi.mocked(api.get)
      .mockResolvedValueOnce([baseTask])
      .mockResolvedValueOnce([
        baseTask,
        { ...baseTask, id: "task-2", title: "New task" },
      ]);
    vi.mocked(api.post).mockResolvedValueOnce({
      ...baseTask,
      id: "task-2",
      title: "New task",
    });

    render(<TaskPanel />);

    await waitFor(() =>
      expect(screen.getByText("Existing task")).toBeInTheDocument(),
    );

    await user.type(screen.getByPlaceholderText("Title"), "New task");
    await user.type(
      screen.getByPlaceholderText("Description"),
      "New description",
    );
    await user.click(screen.getByText("Create task"));

    await waitFor(() =>
      expect(api.post).toHaveBeenCalledWith("/tasks", {
        title: "New task",
        description: "New description",
        priority: 0,
      }),
    );
    await waitFor(() =>
      expect(screen.getByText("New task")).toBeInTheDocument(),
    );
  });

  it("starts a pending task", async () => {
    const user = userEvent.setup();
    vi.mocked(api.get)
      .mockResolvedValueOnce([baseTask])
      .mockResolvedValueOnce([{ ...baseTask, status: "running" }]);
    vi.mocked(api.post).mockResolvedValueOnce({
      ...baseTask,
      status: "running",
    });

    render(<TaskPanel />);

    await waitFor(() =>
      expect(screen.getByText("Start")).toBeInTheDocument(),
    );

    await user.click(screen.getByText("Start"));

    await waitFor(() =>
      expect(api.post).toHaveBeenCalledWith("/tasks/task-1/start"),
    );
    await waitFor(() =>
      expect(screen.getByText("running")).toBeInTheDocument(),
    );
  });
});
