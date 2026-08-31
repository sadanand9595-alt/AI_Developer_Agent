import { useAuth } from "../auth/AuthContext";
import { TaskPanel } from "../components/TaskPanel";
import { ConversationPanel } from "../components/ConversationPanel";
import { ApprovalsPanel } from "../components/ApprovalsPanel";

export function DashboardPage() {
  const { user, logout } = useAuth();

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>AI Command Center</h1>
        <div className="dashboard-user">
          <span>
            {user?.name} ({user?.email})
            {user?.is_admin && <strong> · admin</strong>}
          </span>
          <button onClick={logout}>Sign out</button>
        </div>
      </header>

      <main className="dashboard-body">
        <TaskPanel />
        <ConversationPanel />
        <ApprovalsPanel />
      </main>
    </div>
  );
}
