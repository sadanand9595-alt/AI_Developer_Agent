import { useCallback, useEffect, useState, type FormEvent } from "react";
import { api, ApiError } from "../api/client";
import type { Task } from "../api/types";

export function TaskPanel() {
  const [tasks, setTasks] = useState<Task[] | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);

  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [priority, setPriority] = useState(0);
  const [creating, setCreating] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const [startingId, setStartingId] = useState<string | null>(null);
  const [startError, setStartError] = useState<string | null>(null);

  const loadTasks = useCallback(async () => {
    setLoadError(null);
    try {
      const data = await api.get<Task[]>("/tasks");
      setTasks(data);
    } catch (err) {
      setLoadError(
        err instanceof ApiError ? err.message : "Could not load tasks.",
      );
    }
  }, []);

  useEffect(() => {
    loadTasks();
  }, [loadTasks]);

  async function handleCreate(event: FormEvent) {
    event.preventDefault();
    setFormError(null);
    setCreating(true);
    try {
      await api.post<Task>("/tasks", {
        title,
        description,
        priority,
      });
      setTitle("");
      setDescription("");
      setPriority(0);
      await loadTasks();
    } catch (err) {
      setFormError(
        err instanceof ApiError ? err.message : "Could not create task.",
      );
    } finally {
      setCreating(false);
    }
  }

  async function handleStart(taskId: string) {
    setStartError(null);
    setStartingId(taskId);
    try {
      await api.post<Task>(`/tasks/${taskId}/start`);
      await loadTasks();
    } catch (err) {
      setStartError(
        err instanceof ApiError ? err.message : "Could not start task.",
      );
    } finally {
      setStartingId(null);
    }
  }

  return (
    <section className="panel">
      <h2>Tasks</h2>

      <form className="inline-form" onSubmit={handleCreate}>
        <input
          type="text"
          placeholder="Title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          required
        />
        <input
          type="text"
          placeholder="Description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          required
        />
        <input
          type="number"
          min={0}
          value={priority}
          onChange={(e) => setPriority(Number(e.target.value))}
          title="Priority"
        />
        <button type="submit" disabled={creating}>
          {creating ? "Creating..." : "Create task"}
        </button>
      </form>
      {formError && <p className="form-error">{formError}</p>}
      {startError && <p className="form-error">{startError}</p>}

      {tasks === null && loadError === null && (
        <p className="panel-status">Loading tasks...</p>
      )}
      {loadError && <p className="form-error">{loadError}</p>}
      {tasks !== null && tasks.length === 0 && (
        <p className="panel-status">No tasks yet.</p>
      )}

      {tasks !== null && tasks.length > 0 && (
        <table className="task-table">
          <thead>
            <tr>
              <th>Title</th>
              <th>Status</th>
              <th>Priority</th>
              <th>Created</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {tasks.map((task) => (
              <tr key={task.id}>
                <td>{task.title}</td>
                <td>
                  <span className={`status status-${task.status}`}>
                    {task.status}
                  </span>
                </td>
                <td>{task.priority}</td>
                <td>{new Date(task.created_at).toLocaleString()}</td>
                <td>
                  {task.status === "pending" && (
                    <button
                      onClick={() => handleStart(task.id)}
                      disabled={startingId === task.id}
                    >
                      {startingId === task.id ? "Starting..." : "Start"}
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
