// src/pages/EmployeeMaster.jsx  –  Admin: view all employees + add + assign vehicle
import { useState, useEffect, useCallback } from "react";
import { api } from "../utils/api";
import { Spinner, Alert, FormGroup, EmptyState, ConfirmModal } from "../components/UI";

const ROLES = ["EMPLOYEE", "APPROVER", "TRANSPORT_ADMIN"];

const ROLE_BADGE = {
  EMPLOYEE:        "badge-submitted",
  APPROVER:        "badge-approved",
  TRANSPORT_ADMIN: "badge-allotted",
};

// ── Assign modal ──────────────────────────────────────────────────────────────
function AssignModal({ employee, vehicles, vehicleDriverMap, onSave, onCancel, saving, error }) {
  const [vehicleNo, setVehicleNo] = useState("");
  const [remarks,   setRemarks]   = useState("");
  const [errs,      setErrs]      = useState({});

  // Auto-derive the driver from the selected vehicle
  const mappedDriver = vehicleNo ? vehicleDriverMap[vehicleNo] : null;

  const handleVehicleChange = (e) => {
    setVehicleNo(e.target.value);
    setErrs({});
  };

  const validate = () => {
    const e = {};
    if (!vehicleNo)    e.vehicleNo = "Required";
    if (!mappedDriver) e.vehicleNo = "No active driver mapped to this vehicle";
    setErrs(e);
    return Object.keys(e).length === 0;
  };

  return (
    <div style={{
      position: "fixed", inset: 0, background: "rgba(0,0,0,0.45)",
      display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000,
    }}>
      <div className="card" style={{ width: 480, margin: 0, maxHeight: "90vh", overflowY: "auto" }}>
        <div className="section-title">🚌 Assign Vehicle &amp; Driver</div>
        <p style={{ fontSize: 13, color: "#6b7280", marginBottom: 16 }}>
          Assigning to: <strong>{employee.ENAME}</strong> ({employee.PERNR})
        </p>
        {error && <Alert type="error">{error}</Alert>}

        <FormGroup label="Select Vehicle" required error={errs.vehicleNo}>
          <select value={vehicleNo} onChange={handleVehicleChange}>
            <option value="">— Select Vehicle —</option>
            {vehicles.map((v) => (
              <option key={v.VEHICLE_NO} value={v.VEHICLE_NO}>
                {v.VEHICLE_NO} · {v.VEHICLE_TYPE} · {v.MAKE} {v.MODEL}
                {v.REMAINING_CAPACITY != null ? ` (${v.REMAINING_CAPACITY} seats left)` : ""}
              </option>
            ))}
          </select>
        </FormGroup>

        {/* Driver auto-filled from mapping — read-only */}
        <FormGroup label="Driver (auto-assigned from mapping)">
          {mappedDriver ? (
            <div style={{
              padding: "8px 12px", background: "#f0fdf4", border: "1px solid #86efac",
              borderRadius: 6, fontSize: 14,
            }}>
              <strong>{mappedDriver.DRIVER_NAME}</strong>
              <span style={{ color: "#6b7280", marginLeft: 8 }}>
                ({mappedDriver.DRIVER_ID}) · {mappedDriver.MOBILE_NO1}
              </span>
            </div>
          ) : (
            <div style={{
              padding: "8px 12px", background: "#f9fafb", border: "1px solid #e5e7eb",
              borderRadius: 6, fontSize: 13, color: "#9ca3af",
            }}>
              {vehicleNo ? "No active driver mapped to this vehicle" : "Select a vehicle to see its driver"}
            </div>
          )}
        </FormGroup>

        <FormGroup label="Remarks">
          <input value={remarks} onChange={(e) => setRemarks(e.target.value)} placeholder="Optional" />
        </FormGroup>

        <div className="form-actions">
          <button className="btn btn-outline" onClick={onCancel}>Cancel</button>
          <button
            className="btn btn-primary"
            onClick={() => {
              if (validate()) onSave({ vehicle_no: vehicleNo, driver_id: mappedDriver.DRIVER_ID, remarks });
            }}
            disabled={saving || !mappedDriver}
          >
            {saving ? "Assigning…" : "✅ Confirm Assignment"}
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────
export default function EmployeeMaster() {
  const [employees, setEmployees]           = useState([]);
  const [vehicles, setVehicles]             = useState([]);
  const [vehicleDriverMap, setVehicleDriverMap] = useState({});
  const [loading, setLoading]               = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [saving, setSaving]     = useState(false);
  const [error, setError]       = useState("");
  const [success, setSuccess]   = useState("");
  const [search, setSearch]     = useState("");

  const [assignEmp, setAssignEmp]   = useState(null); // employee being assigned
  const [assignError, setAssignError] = useState("");

  const [form, setForm] = useState({
    ename: "", designation: "", department: "", address: "",
    role: "EMPLOYEE", password: "",
  });
  const [formErrors, setFormErrors] = useState({});

  const load = useCallback(async () => {
    setLoading(true); setError("");
    try {
      const [emps, vehs, mappings] = await Promise.all([
        api.listEmployeesWithAllotment(),
        api.listVehicles(),
        api.listActiveMappings(),
      ]);
      setEmployees(emps);

      // Build vehicle→driver lookup from active mappings
      const driverMap = {};
      mappings.forEach((m) => {
        driverMap[m.VEHICLE_NO] = {
          DRIVER_ID:   m.DRIVER_ID,
          DRIVER_NAME: m.DRIVER_NAME,
          MOBILE_NO1:  m.MOBILE_NO1,
        };
      });
      setVehicleDriverMap(driverMap);

      // Only show active vehicles that have an active driver mapping
      const mappedVehicleNos = new Set(Object.keys(driverMap));
      setVehicles(vehs.filter((v) => v.ACTIVE_FLAG === "Y" && mappedVehicleNos.has(v.VEHICLE_NO)));
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  const validate = () => {
    const e = {};
    if (!form.ename.trim())       e.ename    = "Required";
    if (!form.password)           e.password = "Required";
    if (form.password.length < 6) e.password = "Minimum 6 characters";
    setFormErrors(e);
    return Object.keys(e).length === 0;
  };

  const handleSave = async () => {
    if (!validate()) return;
    setSaving(true); setError("");
    try {
      const res = await api.adminAddEmployee({
        ename:       form.ename.trim(),
        designation: form.designation.trim() || null,
        department:  form.department.trim()  || null,
        address:     form.address.trim()     || null,
        role:        form.role,
        password:    form.password,
      });
      setSuccess(`Employee added. PERNR assigned: ${res.pernr}`);
      setShowForm(false);
      setForm({ ename: "", designation: "", department: "", address: "", role: "EMPLOYEE", password: "" });
      load();
    } catch (e) {
      setError(e.message);
    } finally {
      setSaving(false);
    }
  };

  const handleAssign = async ({ vehicle_no, driver_id, remarks }) => {
    setSaving(true); setAssignError("");
    try {
      await api.adminDirectAllot({
        pernr: assignEmp.PERNR,
        vehicle_no,
        driver_id,
        remarks,
      });
      setSuccess(`Vehicle ${vehicle_no} and driver assigned to ${assignEmp.ENAME}.`);
      setAssignEmp(null);
      load();
    } catch (e) {
      setAssignError(e.message);
    } finally {
      setSaving(false);
    }
  };

  const filtered = search.trim()
    ? employees.filter((e) =>
        e.ENAME?.toLowerCase().includes(search.toLowerCase()) ||
        e.PERNR?.includes(search) ||
        e.DEPARTMENT?.toLowerCase().includes(search.toLowerCase())
      )
    : employees;

  return (
    <div className="page">
      <div className="page-header">
        <h2 className="page-title">Employee Master</h2>
        {!showForm && (
          <button className="btn btn-primary" onClick={() => setShowForm(true)}>
            ➕ Add Employee
          </button>
        )}
      </div>

      {error   && <Alert type="error"   onClose={() => setError("")}>{error}</Alert>}
      {success && <Alert type="success" onClose={() => setSuccess("")}>{success}</Alert>}

      {/* ── Add Employee form ─────────────────────────────────────────────── */}
      {showForm && (
        <div className="card" style={{ marginBottom: 20 }}>
          <div className="section-title">Add New Employee</div>
          <div className="form-grid-3">
            <FormGroup label="Full Name" required error={formErrors.ename}>
              <input value={form.ename} onChange={set("ename")} placeholder="e.g. Rahul Sharma" />
            </FormGroup>
            <FormGroup label="Designation">
              <input value={form.designation} onChange={set("designation")} placeholder="e.g. Software Engineer" />
            </FormGroup>
            <FormGroup label="Department">
              <input value={form.department} onChange={set("department")} placeholder="e.g. IT Department" />
            </FormGroup>
            <FormGroup label="Address">
              <input value={form.address} onChange={set("address")} placeholder="e.g. 12 MG Road, Pune" />
            </FormGroup>
            <FormGroup label="Role" required>
              <select value={form.role} onChange={set("role")}>
                {ROLES.map((r) => <option key={r} value={r}>{r}</option>)}
              </select>
            </FormGroup>
            <FormGroup label="Password" required error={formErrors.password}>
              <input type="password" value={form.password} onChange={set("password")} placeholder="Minimum 6 characters" />
            </FormGroup>
          </div>
          <p style={{ fontSize: 12, color: "#6b7280", margin: "4px 0 12px" }}>
            PERNR will be auto-generated on save.
          </p>
          <div className="form-actions">
            <button className="btn btn-outline" onClick={() => { setShowForm(false); setFormErrors({}); }}>Cancel</button>
            <button className="btn btn-primary" onClick={handleSave} disabled={saving}>
              {saving ? "Saving…" : "💾 Save Employee"}
            </button>
          </div>
        </div>
      )}

      {/* ── Search ────────────────────────────────────────────────────────── */}
      <div className="filter-bar">
        <input
          className="filter-search"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="🔍  Search by name, PERNR, or department…"
        />
        <button className="btn btn-outline btn-sm" onClick={load}>↻ Refresh</button>
      </div>

      {/* ── Table ─────────────────────────────────────────────────────────── */}
      {loading ? <Spinner /> : filtered.length === 0 ? (
        <div className="card"><EmptyState icon="👤" message="No employees found" /></div>
      ) : (
        <div className="card" style={{ padding: 0, overflow: "hidden" }}>
          <table className="data-table">
            <thead>
              <tr>
                <th>PERNR</th>
                <th>Name</th>
                <th>Designation</th>
                <th>Department</th>
                <th>Role</th>
                <th>Vehicle Assigned</th>
                <th>Driver Assigned</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((emp) => (
                <tr key={emp.PERNR}>
                  <td className="mono-cell" style={{ fontWeight: 700, color: "#2563eb" }}>{emp.PERNR}</td>
                  <td style={{ fontWeight: 600 }}>{emp.ENAME}</td>
                  <td>{emp.DESIGNATION || "—"}</td>
                  <td>{emp.DEPARTMENT  || "—"}</td>
                  <td>
                    <span className={`badge ${ROLE_BADGE[emp.ROLE] || "badge-draft"}`}>
                      {emp.ROLE}
                    </span>
                  </td>
                  <td>
                    {emp.ALLOTTED_VEHICLE_NO ? (
                      <div>
                        <div style={{ fontWeight: 600, color: "#1a56a0" }}>{emp.ALLOTTED_VEHICLE_NO}</div>
                        <div style={{ fontSize: 11, color: "#6b7280" }}>
                          {emp.VEHICLE_TYPE} · {emp.MAKE} {emp.MODEL}
                        </div>
                      </div>
                    ) : <span style={{ color: "#9ca3af" }}>—</span>}
                  </td>
                  <td>
                    {emp.ALLOTTED_DRIVER_ID ? (
                      <div>
                        <div style={{ fontWeight: 600 }}>{emp.DRIVER_NAME}</div>
                        <div style={{ fontSize: 11, color: "#6b7280" }}>{emp.DRIVER_MOBILE}</div>
                      </div>
                    ) : <span style={{ color: "#9ca3af" }}>—</span>}
                  </td>
                  <td>
                    <button
                      className="btn btn-primary btn-sm"
                      onClick={() => { setAssignEmp(emp); setAssignError(""); }}
                      title="Assign vehicle & driver"
                    >
                      🚌 Assign
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* ── Assign modal ──────────────────────────────────────────────────── */}
      {assignEmp && (
        <AssignModal
          employee={assignEmp}
          vehicles={vehicles}
          vehicleDriverMap={vehicleDriverMap}
          onSave={handleAssign}
          onCancel={() => { setAssignEmp(null); setAssignError(""); }}
          saving={saving}
          error={assignError}
        />
      )}
    </div>
  );
}
