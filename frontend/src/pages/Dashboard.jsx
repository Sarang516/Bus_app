// src/pages/Dashboard.jsx
import { useState, useEffect } from "react";
import { api } from "../utils/api";
import { useAuth } from "../context/AuthContext";
import { Spinner, Alert } from "../components/UI";

const StatCard = ({ icon, label, value, color, bg, onClick }) => (
  <div
    className="stat-card"
    onClick={onClick}
    style={{ cursor: onClick ? "pointer" : "default" }}
  >
    <div className="stat-icon" style={{ background: bg }}>
      <span style={{ fontSize: 22 }}>{icon}</span>
    </div>
    <div>
      <div className="stat-value" style={{ color }}>{value}</div>
      <div className="stat-label">{label}</div>
    </div>
  </div>
);

export default function Dashboard({ setPage }) {
  const { user } = useAuth();
  const [stats, setStats]     = useState(null);
  const [myStats, setMyStats] = useState(null);
  const [error, setError]     = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const calls = user.role === "EMPLOYEE"
      ? [Promise.resolve(null), api.getMyDashboard(user.pernr)]
      : [api.getDashboard(),    api.getMyDashboard(user.pernr)];

    Promise.all(calls)
      .then(([s, m]) => { setStats(s); setMyStats(m); })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [user.pernr, user.role]);

  if (loading) return <Spinner />;

  // Determine which request page to use based on role
  const reqPage = user.role === "APPROVER"        ? "all-requests"
                : user.role === "TRANSPORT_ADMIN" ? "vehicle-allotment"
                : "my-requests";

  const globalCards = stats ? [
    { icon: "📋", label: "Total Requests",  value: stats.total_requests, color: "#1a56a0", bg: "#e8f0fb", onClick: () => setPage(reqPage, "") },
    { icon: "⏳", label: "Pending Approval",value: stats.submitted,       color: "#b45309", bg: "#fef3c7", onClick: () => setPage(user.role === "EMPLOYEE" ? "my-requests" : "pending-approval", "0002") },
    { icon: "✅", label: "Approved",         value: stats.approved,        color: "#166534", bg: "#dcfce7", onClick: () => setPage(reqPage, "0003") },
    { icon: "🚌", label: "Allotted",         value: stats.allotted,        color: "#0369a1", bg: "#e0f2fe", onClick: () => setPage(reqPage, "0005") },
    ...(user.role === "TRANSPORT_ADMIN" ? [
      { icon: "🚗", label: "Active Vehicles", value: stats.active_vehicles, color: "#7c3aed", bg: "#ede9fe", onClick: () => setPage("vehicle-master") },
      { icon: "👤", label: "Active Drivers",  value: stats.active_drivers,  color: "#be185d", bg: "#fce7f3", onClick: () => setPage("driver-master") },
    ] : []),
  ] : [];

  const myCards = myStats ? [
    { icon: "📝", label: "My Drafts",    value: myStats.my_draft,    color: "#374151", bg: "#f3f4f6", onClick: () => setPage("my-requests", "0001") },
    { icon: "📤", label: "My Submitted", value: myStats.my_pending,  color: "#b45309", bg: "#fef3c7", onClick: () => setPage("my-requests", "0002") },
    { icon: "✅", label: "My Approved",  value: myStats.my_approved, color: "#166534", bg: "#dcfce7", onClick: () => setPage("my-requests", "0003") },
    { icon: "❌", label: "My Rejected",  value: myStats.my_rejected, color: "#991b1b", bg: "#fee2e2", onClick: () => setPage("my-requests", "0004") },
  ] : [];

  return (
    <div className="page">
      {error && <Alert type="error">{error}</Alert>}

      {/* Welcome */}
      <div className="welcome-banner">
        <div>
          <h2 className="welcome-title">Welcome back, {user.ename} 👋</h2>
          <p className="welcome-sub">{user.designation} · {user.department}</p>
        </div>
        {user.role === "EMPLOYEE" && (
          <button className="btn btn-primary" onClick={() => setPage("new-request")}>
            ➕ New Request
          </button>
        )}
      </div>

      {/* My summary (for employees) */}
      {user.role === "EMPLOYEE" && (
        <>
          <h3 className="section-heading">My Requests</h3>
          <div className="stat-grid stat-grid-4">
            {myCards.map((c) => (
              <StatCard key={c.label} {...c} />
            ))}
          </div>
        </>
      )}

      {/* Global summary — only for Approver / Transport Admin */}
      {user.role !== "EMPLOYEE" && (
        <>
          <h3 className="section-heading">Organisation Overview</h3>
          <div className="stat-grid stat-grid-3">
            {globalCards.map((c) => (
              <StatCard key={c.label} {...c} />
            ))}
          </div>
        </>
      )}

      {/* Quick Actions */}
      <div className="card" style={{ marginTop: 4 }}>
        <div className="section-title">Quick Actions</div>
        <div className="quick-actions">
          {user.role === "EMPLOYEE" && (
            <>
              <button className="btn btn-primary" onClick={() => setPage("new-request")}>📝 Apply for Bus Pass</button>
              <button className="btn btn-outline" onClick={() => setPage("my-requests")}>📋 View My Requests</button>
            </>
          )}
          {user.role === "APPROVER" && (
            <>
              <button className="btn btn-primary" onClick={() => setPage("pending-approval")}>⏳ Review Pending Approvals</button>
              <button className="btn btn-outline" onClick={() => setPage("all-requests")}>📁 View All Requests</button>
            </>
          )}
          {user.role === "TRANSPORT_ADMIN" && (
            <>
              <button className="btn btn-primary" onClick={() => setPage("vehicle-allotment")}>🚌 Allot Vehicles</button>
              <button className="btn btn-outline" onClick={() => setPage("driver-master")}>👤 Manage Drivers</button>
              <button className="btn btn-outline" onClick={() => setPage("vehicle-master")}>🚗 Manage Vehicles</button>
              <button className="btn btn-outline" onClick={() => setPage("driver-vehicle-map")}>🔗 Driver-Vehicle Map</button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
