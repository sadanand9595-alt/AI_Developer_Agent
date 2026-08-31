import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ConversationPanel } from "./ConversationPanel";
import { api, ApiError } from "../api/client";
import type { Conversation, Message } from "../api/types";

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

const conversation: Conversation = {
  id: "convo-1",
  user_id: "user-1",
  title: "My conversation",
  is_archived: false,
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
};

const message: Message = {
  id: "msg-1",
  conversation_id: "convo-1",
  role: "user",
  content: "Hello there",
  tool_name: null,
  created_at: "2026-01-01T00:00:00Z",
};

describe("ConversationPanel", () => {
  beforeEach(() => {
    vi.mocked(api.get).mockReset();
    vi.mocked(api.post).mockReset();
  });

  it("shows an empty state when there are no conversations", async () => {
    vi.mocked(api.get).mockResolvedValueOnce([]);

    render(<ConversationPanel />);

    await waitFor(() =>
      expect(
        screen.getByText("No conversations yet."),
      ).toBeInTheDocument(),
    );
  });

  it("creates a new conversation and selects it", async () => {
    const user = userEvent.setup();
    vi.mocked(api.get)
      .mockResolvedValueOnce([]) // initial list
      .mockResolvedValueOnce([conversation]) // list after create
      .mockResolvedValueOnce([]); // messages for the new selection
    vi.mocked(api.post).mockResolvedValueOnce(conversation);

    render(<ConversationPanel />);

    await waitFor(() =>
      expect(
        screen.getByText("No conversations yet."),
      ).toBeInTheDocument(),
    );

    await user.type(
      screen.getByPlaceholderText("Title (optional)"),
      "My conversation",
    );
    await user.click(screen.getByText("New conversation"));

    await waitFor(() =>
      expect(api.post).toHaveBeenCalledWith("/conversations", {
        title: "My conversation",
      }),
    );
    await waitFor(() =>
      expect(screen.getByText("No messages yet.")).toBeInTheDocument(),
    );
  });

  it("selects a conversation and loads its messages", async () => {
    const user = userEvent.setup();
    vi.mocked(api.get)
      .mockResolvedValueOnce([conversation]) // list conversations
      .mockResolvedValueOnce([message]); // list messages

    render(<ConversationPanel />);

    await waitFor(() =>
      expect(screen.getByText("My conversation")).toBeInTheDocument(),
    );

    await user.click(screen.getByText("My conversation"));

    await waitFor(() =>
      expect(
        api.get,
      ).toHaveBeenCalledWith("/conversations/convo-1/messages"),
    );
    await waitFor(() =>
      expect(screen.getByText(/Hello there/)).toBeInTheDocument(),
    );
  });

  it("sends a message and refreshes the message list", async () => {
    const user = userEvent.setup();
    vi.mocked(api.get)
      .mockResolvedValueOnce([conversation])
      .mockResolvedValueOnce([]) // initial empty messages
      .mockResolvedValueOnce([message]); // after send
    vi.mocked(api.post).mockResolvedValueOnce(message);

    render(<ConversationPanel />);

    await waitFor(() =>
      expect(screen.getByText("My conversation")).toBeInTheDocument(),
    );
    await user.click(screen.getByText("My conversation"));

    await waitFor(() =>
      expect(screen.getByText("No messages yet.")).toBeInTheDocument(),
    );

    await user.type(
      screen.getByPlaceholderText("Message"),
      "Hello there",
    );
    await user.click(screen.getByText("Send"));

    await waitFor(() =>
      expect(api.post).toHaveBeenCalledWith(
        "/conversations/convo-1/messages",
        { content: "Hello there" },
      ),
    );
    await waitFor(() =>
      expect(screen.getByText(/Hello there/)).toBeInTheDocument(),
    );
  });

  it("surfaces the archived-conversation error from the API", async () => {
    const user = userEvent.setup();
    vi.mocked(api.get)
      .mockResolvedValueOnce([{ ...conversation, is_archived: true }])
      .mockResolvedValueOnce([]);
    vi.mocked(api.post).mockRejectedValueOnce(
      new ApiError(
        400,
        "Cannot add a message to an archived conversation.",
      ),
    );

    render(<ConversationPanel />);

    await waitFor(() =>
      expect(screen.getByText("My conversation")).toBeInTheDocument(),
    );
    await user.click(screen.getByText("My conversation"));
    await waitFor(() =>
      expect(screen.getByText("No messages yet.")).toBeInTheDocument(),
    );

    await user.type(screen.getByPlaceholderText("Message"), "x");
    await user.click(screen.getByText("Send"));

    await waitFor(() =>
      expect(
        screen.getByText(
          "Cannot add a message to an archived conversation.",
        ),
      ).toBeInTheDocument(),
    );
  });
});
