import { useCallback, useEffect, useState, type FormEvent } from "react";
import { api, ApiError } from "../api/client";
import type { Conversation, Message } from "../api/types";

export function ConversationPanel() {
  const [conversations, setConversations] = useState<
    Conversation[] | null
  >(null);
  const [listError, setListError] = useState<string | null>(null);

  const [newTitle, setNewTitle] = useState("");
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);

  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[] | null>(null);
  const [messagesError, setMessagesError] = useState<string | null>(
    null,
  );

  const [messageContent, setMessageContent] = useState("");
  const [sending, setSending] = useState(false);
  const [sendError, setSendError] = useState<string | null>(null);

  const loadConversations = useCallback(async () => {
    setListError(null);
    try {
      const data = await api.get<Conversation[]>("/conversations");
      setConversations(data);
    } catch (err) {
      setListError(
        err instanceof ApiError
          ? err.message
          : "Could not load conversations.",
      );
    }
  }, []);

  useEffect(() => {
    loadConversations();
  }, [loadConversations]);

  const loadMessages = useCallback(async (conversationId: string) => {
    setMessagesError(null);
    setMessages(null);
    try {
      const data = await api.get<Message[]>(
        `/conversations/${conversationId}/messages`,
      );
      setMessages(data);
    } catch (err) {
      setMessagesError(
        err instanceof ApiError
          ? err.message
          : "Could not load messages.",
      );
    }
  }, []);

  function selectConversation(id: string) {
    setSelectedId(id);
    loadMessages(id);
  }

  async function handleCreate(event: FormEvent) {
    event.preventDefault();
    setCreateError(null);
    setCreating(true);
    try {
      const created = await api.post<Conversation>("/conversations", {
        title: newTitle || null,
      });
      setNewTitle("");
      await loadConversations();
      selectConversation(created.id);
    } catch (err) {
      setCreateError(
        err instanceof ApiError
          ? err.message
          : "Could not create conversation.",
      );
    } finally {
      setCreating(false);
    }
  }

  async function handleSend(event: FormEvent) {
    event.preventDefault();
    if (!selectedId) return;

    setSendError(null);
    setSending(true);
    try {
      await api.post<Message>(
        `/conversations/${selectedId}/messages`,
        { content: messageContent },
      );
      setMessageContent("");
      await loadMessages(selectedId);
    } catch (err) {
      setSendError(
        err instanceof ApiError ? err.message : "Could not send message.",
      );
    } finally {
      setSending(false);
    }
  }

  return (
    <section className="panel conversation-panel">
      <h2>Conversations</h2>

      <form className="inline-form" onSubmit={handleCreate}>
        <input
          type="text"
          placeholder="Title (optional)"
          value={newTitle}
          onChange={(e) => setNewTitle(e.target.value)}
        />
        <button type="submit" disabled={creating}>
          {creating ? "Creating..." : "New conversation"}
        </button>
      </form>
      {createError && <p className="form-error">{createError}</p>}

      {conversations === null && listError === null && (
        <p className="panel-status">Loading conversations...</p>
      )}
      {listError && <p className="form-error">{listError}</p>}
      {conversations !== null && conversations.length === 0 && (
        <p className="panel-status">No conversations yet.</p>
      )}

      <div className="conversation-layout">
        {conversations !== null && conversations.length > 0 && (
          <ul className="conversation-list">
            {conversations.map((c) => (
              <li
                key={c.id}
                className={c.id === selectedId ? "selected" : ""}
                onClick={() => selectConversation(c.id)}
              >
                {c.title ?? "(untitled)"}
                {c.is_archived && (
                  <span className="status status-archived">archived</span>
                )}
              </li>
            ))}
          </ul>
        )}

        {selectedId && (
          <div className="message-view">
            {messagesError && <p className="form-error">{messagesError}</p>}
            {messages === null && messagesError === null && (
              <p className="panel-status">Loading messages...</p>
            )}
            {messages !== null && messages.length === 0 && (
              <p className="panel-status">No messages yet.</p>
            )}
            {messages !== null && messages.length > 0 && (
              <ul className="message-list">
                {messages.map((m) => (
                  <li key={m.id} className={`message-role-${m.role}`}>
                    <strong>{m.role}:</strong> {m.content}
                  </li>
                ))}
              </ul>
            )}

            <form className="inline-form" onSubmit={handleSend}>
              <input
                type="text"
                placeholder="Message"
                value={messageContent}
                onChange={(e) => setMessageContent(e.target.value)}
                required
              />
              <button type="submit" disabled={sending}>
                {sending ? "Sending..." : "Send"}
              </button>
            </form>
            {sendError && <p className="form-error">{sendError}</p>}
          </div>
        )}
      </div>
    </section>
  );
}
