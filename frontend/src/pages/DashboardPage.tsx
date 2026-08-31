import { useAuth } from "../auth/AuthContext";

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
        <p>Signed in. Task, conversation, and approval panels land next.</p>
      </main>
    </div>
  );
}
