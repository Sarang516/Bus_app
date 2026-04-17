// src/pages/RequestList.jsx
import { useState, useEffect, useCallback } from "react";
import { api } from "../utils/api";
import { useAuth } from "../context/AuthContext";
import { Spinner, Alert, StatusBadge, EmptyState } from "../components/UI";
import RequestDetail from "./RequestDetail";

const STATUS_OPTS = [
  { value: "", label: "All Statuses" },
  { value: "0001", label: "Draft" },
  { value: "0002", label: "Submitted" },
  { value: "0003", label: "Approved" },
  { value: "0004", label: "Rejected" },
  { value: "0005", label: "Vehicle Allotted" },
  { value: "0006", label: "Withdrawn" },
];

export default function RequestList({ title, viewRole, initialStatus = "" }) {
  const { user }  = useAuth();
  const [rows, setRows]         = useState([]);
  const [filtered, setFiltered] = useState([]);
  const [loading, setLoading]   = useState(true);
  const [error, setError]       = useState("");
  const [selected, setSelected] = useState(null);
  const [search, setSearch]     = useState("");
  const [statusF, setStatusF]   = useState(initialStatus);

  const load = useCallback(async () => {
    setLoading(true); setError("");
    try {
      const role = viewRole || user.role;
      const data = await api.listRequests(user.pernr, role);
      setRows(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [user, viewRole]);

  useEffect(() => { load(); }, [load]);

  // Client-side filter
  useEffect(() => {
    let list = rows;
    if (statusF) list = list.filter((r) => r.STATUS === statusF);
    if (search.trim()) {
      const s = search.toLowerCase();
      list = list.filter(
        (r) =>
          r.REQID?.toLowerCase().includes(s) ||
          r.PERNR?.toLowerCase().includes(s) ||
          r.PICK_UP_POINT?.toLowerCase().includes(s) ||
          r.REASON?.toLowerCase().includes(s) ||
          r.PASS_TYPE?.toLowerCase().includes(s)
      );
    }
    setFiltered(list);
  }, [rows, search, statusF]);

  if (selected) {
    return (
      <RequestDetail
        reqid={selected}
        onBack={() => { setSelected(null); load(); }}
      />
    );
  }

  return (
    <div className="page">
      <div className="page-header">
        <h2 className="page-title">{title}</h2>
        <span className="row-count">{filtered.length} record{filtered.length !== 1 ? "s" : ""}</span>
      </div>

      {error && <Alert type="error" onClose={() => setError("")}>{error}</Alert>}

      {/* Filters */}
      <div className="filter-bar">
        <input
          className="filter-search"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="🔍  Search by Request ID, Employee, Route, Reason…"
        />
        <select
          className="filter-select"
          value={statusF}
          onChange={(e) => setStatusF(e.target.value)}
        >
          {STATUS_OPTS.map((o) => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>
        <button className="btn btn-outline btn-sm" onClick={load}>↻ Refresh</button>
      </div>

      {loading ? (
        <Spinner />
      ) : filtered.length === 0 ? (
        <div className="card"><EmptyState icon="📋" message="No requests found" /></div>
      ) : (
        <div className="card" style={{ padding: 0, overflow: "hidden" }}>
          <table className="data-table">
            <thead>
              <tr>
                <th>Request ID</th>
                <th>Emp No</th>
                <th>Pass Type</th>
                <th>Route</th>
                <th>Pick Up Point</th>
                <th>Reason</th>
                <th>Status</th>
                <th>Pending With</th>
                <th>Created On</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((r) => (
                <tr key={r.REQID} className="clickable-row" onClick={() => setSelected(r.REQID)}>
                  <td className="mono-cell">{r.REQID}</td>
                  <td>{r.PERNR}</td>
                  <td>{r.PASS_TYPE}</td>
                  <td>{r.ROUTE_FROM ? `Route ${r.ROUTE_NO} — ${r.ROUTE_FROM}` : `Route ${r.ROUTE_NO}`}</td>
                  <td>{r.PICK_UP_POINT}</td>
                  <td className="truncate-cell">{r.REASON}</td>
                  <td><StatusBadge status={r.STATUS} text={r.STATUS_TEXT} /></td>
                  <td>
                    {r.PENDING_WITH
                      ? <span style={{ fontSize: 12 }}>
                          {r.PENDING_WITH_NAME && <>{r.PENDING_WITH_NAME}<br/></>}
                          <span style={{ color: "#9ca3af" }}>{r.PENDING_WITH}</span>
                        </span>
                      : "—"}
                  </td>
                  <td className="date-cell">{r.REQUEST_CREATION_DATE?.split("T")[0]}</td>
                  <td>
                    <button
                      className="btn btn-outline btn-sm"
                      onClick={(e) => { e.stopPropagation(); setSelected(r.REQID); }}
                    >
                      View
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
