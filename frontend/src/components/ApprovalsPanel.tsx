import { useCallback, useEffect, useState, type FormEvent } from "react";
import { useAuth } from "../auth/AuthContext";
import { api, ApiError } from "../api/client";
import type { ApprovalRequest } from "../api/types";

export function ApprovalsPanel() {
  const { user } = useAuth();

  const [myApprovals, setMyApprovals] = useState<ApprovalRequest[] | null>(
    null,
  );
  const [listError, setListError] = useState<string | null>(null);

  const loadMyApprovals = useCallback(async () => {
    setListError(null);
    try {
      const data = await api.get<ApprovalRequest[]>("/approvals/me");
      setMyApprovals(data);
    } catch (err) {
      setListError(
        err instanceof ApiError
          ? err.message
          : "Could not load approvals.",
      );
    }
  }, []);

  useEffect(() => {
    loadMyApprovals();
  }, [loadMyApprovals]);

  // -- Admin review: the API has no "list all pending" endpoint for
  // admins, only GET /approvals/{id} (owner or admin) and
  // /approvals/me (caller's own requests). So an admin reviews a
  // specific request by ID.
  const [lookupId, setLookupId] = useState("");
  const [lookupError, setLookupError] = useState<string | null>(null);
  const [lookupLoading, setLookupLoading] = useState(false);
  const [reviewed, setReviewed] = useState<ApprovalRequest | null>(null);
  const [comment, setComment] = useState("");
  const [actionInProgress, setActionInProgress] = useState<
    "approve" | "reject" | null
  >(null);
  const [actionError, setActionError] = useState<string | null>(null);

  async function handleLookup(event: FormEvent) {
    event.preventDefault();
    setLookupError(null);
    setActionError(null);
    setReviewed(null);
    setLookupLoading(true);
    try {
      const approval = await api.get<ApprovalRequest>(
        `/approvals/${lookupId}`,
      );
      setReviewed(approval);
    } catch (err) {
      setLookupError(
        err instanceof ApiError ? err.message : "Approval not found.",
      );
    } finally {
      setLookupLoading(false);
    }
  }

  async function handleAction(action: "approve" | "reject") {
    if (!reviewed) return;

    setActionError(null);
    setActionInProgress(action);
    try {
      const updated = await api.post<ApprovalRequest>(
        `/approvals/${reviewed.id}/${action}`,
        { comment: comment || null },
      );
      setReviewed(updated);
      setComment("");
      await loadMyApprovals();
    } catch (err) {
      setActionError(
        err instanceof ApiError
          ? err.message
          : `Could not ${action} the request.`,
      );
    } finally {
      setActionInProgress(null);
    }
  }

  return (
    <section className="panel approvals-panel">
      <h2>Approvals</h2>

      <h3>My requests</h3>
      {myApprovals === null && listError === null && (
        <p className="panel-status">Loading approvals...</p>
      )}
      {listError && <p className="form-error">{listError}</p>}
      {myApprovals !== null && myApprovals.length === 0 && (
        <p className="panel-status">No pending approval requests.</p>
      )}
      {myApprovals !== null && myApprovals.length > 0 && (
        <ul className="approval-list">
          {myApprovals.map((a) => (
            <li key={a.id}>
              <strong>{a.action}</strong> &mdash; {a.reason}
              <span className={`status status-${a.status}`}>
                {a.status}
              </span>
            </li>
          ))}
        </ul>
      )}

      {user?.is_admin && (
        <div className="admin-review">
          <h3>Review a request (admin)</h3>
          <form className="inline-form" onSubmit={handleLookup}>
            <input
              type="text"
              placeholder="Approval ID"
              value={lookupId}
              onChange={(e) => setLookupId(e.target.value)}
              required
            />
            <button type="submit" disabled={lookupLoading}>
              {lookupLoading ? "Looking up..." : "Look up"}
            </button>
          </form>
          {lookupError && <p className="form-error">{lookupError}</p>}

          {reviewed && (
            <div className="reviewed-approval">
              <p>
                <strong>{reviewed.action}</strong> &mdash;{" "}
                {reviewed.requested_operation}
              </p>
              <p>{reviewed.reason}</p>
              <p>
                Status:{" "}
                <span className={`status status-${reviewed.status}`}>
                  {reviewed.status}
                </span>
              </p>

              {reviewed.status === "pending" && (
                <>
                  <input
                    type="text"
                    placeholder="Comment (optional)"
                    value={comment}
                    onChange={(e) => setComment(e.target.value)}
                  />
                  <div className="approval-actions">
                    <button
                      onClick={() => handleAction("approve")}
                      disabled={actionInProgress !== null}
                    >
                      {actionInProgress === "approve"
                        ? "Approving..."
                        : "Approve"}
                    </button>
                    <button
                      onClick={() => handleAction("reject")}
                      disabled={actionInProgress !== null}
                    >
                      {actionInProgress === "reject"
                        ? "Rejecting..."
                        : "Reject"}
                    </button>
                  </div>
                </>
              )}
              {actionError && <p className="form-error">{actionError}</p>}
            </div>
          )}
        </div>
      )}
    </section>
  );
}
