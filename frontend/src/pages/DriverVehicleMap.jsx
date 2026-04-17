// src/pages/DriverVehicleMap.jsx
import { useState, useEffect, useCallback } from "react";
import { api } from "../utils/api";
import { Spinner, Alert, FormGroup, EmptyState, ConfirmModal } from "../components/UI";

const VEHICLE_TYPES = ["BUS", "SEDAN", "PREMIUM SEDAN", "SUV", "PREMIUM SUV", "OTHER"];

export default function DriverVehicleMap() {
  const [maps, setMaps]       = useState([]);
  const [drivers, setDrivers] = useState([]);
  const [vehicles, setVehicles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [saving, setSaving]   = useState(false);
  const [error, setError]     = useState("");
  const [success, setSuccess] = useState("");
  const [endMapId, setEndMapId] = useState(null);

  const [form, setForm] = useState({
    vehicle_type: "BUS", vehicle_no: "", driver_id: "",
    begda: new Date().toISOString().split("T")[0], endda: "9999-12-31",
  });
  const [formErrors, setFormErrors] = useState({});

  const load = useCallback(async () => {
    setLoading(true); setError("");
    try {
      const m = await api.listMappings();
      setMaps(m);
      // Drivers & vehicles only needed for the form — load silently
      Promise.all([api.listDrivers(), api.listVehicles()])
        .then(([d, v]) => { setDrivers(d); setVehicles(v); })
        .catch(() => {});
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const filteredVehicles = vehicles.filter(
    (v) => v.VEHICLE_TYPE === form.vehicle_type
  );

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  const validate = () => {
    const e = {};
    if (!form.vehicle_no) e.vehicle_no = "Required";
    if (!form.driver_id)  e.driver_id  = "Required";
    if (!form.begda)      e.begda      = "Required";
    setFormErrors(e);
    return Object.keys(e).length === 0;
  };

  const handleSave = async () => {
    if (!validate()) return;
    setSaving(true); setError("");
    try {
      await api.createMapping(form);
      setSuccess("Mapping created successfully.");
      setShowForm(false);
      setForm({
        vehicle_type: "BUS", vehicle_no: "", driver_id: "",
        begda: new Date().toISOString().split("T")[0], endda: "9999-12-31",
      });
      load();
    } catch (e) {
      setError(e.message);
    } finally {
      setSaving(false);
    }
  };

  const handleEnd = async () => {
    setError("");
    try {
      await api.deleteMapping(endMapId);
      setSuccess("Mapping ended."); setEndMapId(null); load();
    } catch (e) { setError(e.message); setEndMapId(null); }
  };

  const today = new Date().toISOString().split("T")[0];

  return (
    <div className="page">
      <div className="page-header">
        <h2 className="page-title">Driver – Vehicle Mapping</h2>
        {!showForm && (
          <button className="btn btn-primary" onClick={() => setShowForm(true)}>
            ➕ New Mapping
          </button>
        )}
      </div>

      {error   && <Alert type="error"   onClose={() => setError("")}>{error}</Alert>}
      {success && <Alert type="success" onClose={() => setSuccess("")}>{success}</Alert>}

      {showForm && (
        <div className="card" style={{ marginBottom: 20 }}>
          <div className="section-title">Create Driver – Vehicle Mapping</div>
          <div className="form-grid-3">
            <FormGroup label="Vehicle Type" required>
              <select
                value={form.vehicle_type}
                onChange={(e) => {
                  setForm((f) => ({ ...f, vehicle_type: e.target.value, vehicle_no: "" }));
                }}
              >
                {VEHICLE_TYPES.map((t) => <option key={t}>{t}</option>)}
              </select>
            </FormGroup>

            <FormGroup label="Vehicle No" required error={formErrors.vehicle_no}>
              <select value={form.vehicle_no} onChange={set("vehicle_no")}>
                <option value="">— Select Vehicle —</option>
                {filteredVehicles.map((v) => (
                  <option key={v.VEHICLE_NO} value={v.VEHICLE_NO}>
                    {v.VEHICLE_NO} · {v.MAKE} {v.MODEL}
                  </option>
                ))}
              </select>
            </FormGroup>

            <FormGroup label="Driver" required error={formErrors.driver_id}>
              <select value={form.driver_id} onChange={set("driver_id")}>
                <option value="">— Select Driver —</option>
                {drivers.map((d) => (
                  <option key={d.DRIVER_ID} value={d.DRIVER_ID}>
                    {d.DRIVER_NAME} ({d.DRIVER_ID}) · {d.MOBILE_NO1}
                  </option>
                ))}
              </select>
            </FormGroup>

            <FormGroup label="Valid From" required error={formErrors.begda}>
              <input type="date" value={form.begda} onChange={set("begda")} />
            </FormGroup>

            <FormGroup label="Valid To">
              <input type="date" value={form.endda} onChange={set("endda")} />
            </FormGroup>
          </div>

          <div className="form-actions">
            <button className="btn btn-outline" onClick={() => setShowForm(false)}>Cancel</button>
            <button className="btn btn-primary" onClick={handleSave} disabled={saving}>
              {saving ? "Saving…" : "💾 Save Mapping"}
            </button>
          </div>
        </div>
      )}

      {loading ? <Spinner /> : maps.length === 0 ? (
        <div className="card"><EmptyState icon="🔗" message="No mappings found" /></div>
      ) : (
        <div className="card" style={{ padding: 0, overflow: "hidden" }}>
          <table className="data-table">
            <thead>
              <tr>
                <th>Map ID</th>
                <th>Vehicle Type</th>
                <th>Vehicle No</th>
                <th>Driver Name</th>
                <th>Driver ID</th>
                <th>Mobile</th>
                <th>Date Mapped</th>
                <th>Valid From</th>
                <th>Valid To</th>
                <th>Status</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {maps.map((m) => {
                const active = m.ENDDA > today;
                return (
                  <tr key={m.MAP_ID}>
                    <td className="mono-cell" style={{ fontSize: 11 }}>{m.MAP_ID}</td>
                    <td><span className="type-tag">{m.VEHICLE_TYPE}</span></td>
                    <td className="mono-cell">{m.VEHICLE_NO}</td>
                    <td style={{ fontWeight: 600 }}>{m.DRIVER_NAME}</td>
                    <td>{m.DRIVER_ID}</td>
                    <td>{m.MOBILE_NO1}</td>
                    <td>{m.DATE_MAP}</td>
                    <td>{m.BEGDA}</td>
                    <td>{m.ENDDA}</td>
                    <td>
                      <span className={`badge ${active ? "badge-approved" : "badge-rejected"}`}>
                        {active ? "Active" : "Ended"}
                      </span>
                    </td>
                    <td>
                      {active && (
                        <button
                          className="btn btn-outline btn-sm"
                          onClick={() => setEndMapId(m.MAP_ID)}
                          title="End mapping"
                        >
                          ✂️ End
                        </button>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {endMapId && (
        <ConfirmModal
          isOpen={true}
          title="End Mapping"
          message={`End mapping ${endMapId}? The driver will be unlinked from the vehicle.`}
          confirmText="End Mapping"
          onConfirm={handleEnd}
          onCancel={() => setEndMapId(null)}
          isDangerous
        />
      )}
    </div>
  );
}
