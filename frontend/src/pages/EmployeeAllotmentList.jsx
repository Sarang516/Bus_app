// src/pages/EmployeeAllotmentList.jsx  –  Approver: all employees with bus & driver
import { useState, useEffect, useCallback } from "react";
import { api } from "../utils/api";
import { Spinner, Alert, EmptyState } from "../components/UI";

export default function EmployeeAllotmentList() {
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading]     = useState(true);
  const [error, setError]         = useState("");
  const [search, setSearch]       = useState("");

  const load = useCallback(async () => {
    setLoading(true); setError("");
    try {
      const data = await api.listEmployeesWithAllotment();
      setEmployees(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const filtered = employees.filter((emp) => {
    const q = search.toLowerCase();
    return (
      emp.PERNR.toLowerCase().includes(q) ||
      emp.ENAME.toLowerCase().includes(q) ||
      (emp.DEPARTMENT || "").toLowerCase().includes(q)
    );
  });

  const allotted = filtered.filter((e) => e.ALLOTTED_VEHICLE_NO);
  const pending  = filtered.filter((e) => !e.ALLOTTED_VEHICLE_NO);

  return (
    <div className="page">
      <div className="page-header">
        <h2 className="page-title">Employee Bus Allotment</h2>
        <span className="row-count">{filtered.length} employee(s)</span>
      </div>

      {error && <Alert type="error" onClose={() => setError("")}>{error}</Alert>}

      {/* Search bar */}
      <div className="filter-bar" style={{ marginBottom: 20 }}>
        <input
          className="filter-search"
          placeholder="Search by Employee ID or Name or Department…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{ maxWidth: 400 }}
        />
        {search && (
          <button
            className="btn btn-outline btn-sm"
            onClick={() => setSearch("")}
          >
            Clear
          </button>
        )}
      </div>

      {loading ? <Spinner /> : (
        <>
          {/* Allotted employees */}
          <div style={{ marginBottom: 8 }}>
            <div className="section-heading">
              🚌 Allotted ({allotted.length})
            </div>
            {allotted.length === 0 ? (
              <div className="card">
                <EmptyState icon="🚌" message="No allotted employees found" />
              </div>
            ) : (
              <div className="card" style={{ padding: 0, overflow: "hidden", marginBottom: 24 }}>
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>PERNR</th>
                      <th>Employee Name</th>
                      <th>Designation</th>
                      <th>Department</th>
                      <th>Route</th>
                      <th>Pickup Point</th>
                      <th>Vehicle No</th>
                      <th>Vehicle Type</th>
                      <th>Driver Name</th>
                      <th>Driver Mobile</th>
                    </tr>
                  </thead>
                  <tbody>
                    {allotted.map((emp) => (
                      <tr key={emp.PERNR}>
                        <td className="mono-cell">{emp.PERNR}</td>
                        <td style={{ fontWeight: 600 }}>{emp.ENAME}</td>
                        <td>{emp.DESIGNATION || "—"}</td>
                        <td>{emp.DEPARTMENT  || "—"}</td>
                        <td>
                          <span className="type-tag">Route {emp.ROUTE_NO}</span>
                        </td>
                        <td>{emp.PICK_UP_POINT || "—"}</td>
                        <td className="mono-cell" style={{ color: "#16a34a" }}>
                          {emp.ALLOTTED_VEHICLE_NO}
                        </td>
                        <td>
                          {emp.VEHICLE_TYPE
                            ? <span className="type-tag">{emp.VEHICLE_TYPE}</span>
                            : "—"}
                        </td>
                        <td style={{ fontWeight: 600 }}>{emp.DRIVER_NAME || "—"}</td>
                        <td>{emp.DRIVER_MOBILE || "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Employees without allotment */}
          <div>
            <div className="section-heading">
              ⏳ No Bus Allotted ({pending.length})
            </div>
            {pending.length === 0 ? (
              <div className="card">
                <EmptyState icon="✅" message="All employees have been allotted" />
              </div>
            ) : (
              <div className="card" style={{ padding: 0, overflow: "hidden" }}>
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>PERNR</th>
                      <th>Employee Name</th>
                      <th>Designation</th>
                      <th>Department</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {pending.map((emp) => (
                      <tr key={emp.PERNR}>
                        <td className="mono-cell">{emp.PERNR}</td>
                        <td style={{ fontWeight: 600 }}>{emp.ENAME}</td>
                        <td>{emp.DESIGNATION || "—"}</td>
                        <td>{emp.DEPARTMENT  || "—"}</td>
                        <td>
                          <span className="badge badge-draft">Not Allotted</span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
