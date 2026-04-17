// src/pages/DriverMaster.jsx
import { useState, useEffect, useCallback } from "react";
import { api } from "../utils/api";
import { Spinner, Alert, FormGroup, EmptyState, ConfirmModal } from "../components/UI";

const EMPTY_FORM = {
  driver_id: "", driver_name: "", mobile_no1: "", mobile_no2: "",
  address: "", dob: "", dl_no: "", valid_upto: "",
  begda: new Date().toISOString().split("T")[0], endda: "9999-12-31",
};


function DriverForm({ initial, onSave, onCancel, saving, error }) {
  const [form, setForm] = useState(initial || EMPTY_FORM);
  const [errors, setErrors] = useState({});
  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  const validate = () => {
    const e = {};
    if (!form.driver_name) e.driver_name = "Required";
    if (!form.mobile_no1 || !/^\d{10,}$/.test(form.mobile_no1))
                           e.mobile_no1  = "Enter valid 10-digit mobile number";
    if (!form.dl_no)       e.dl_no       = "Required";
    if (!form.valid_upto)  e.valid_upto  = "Required";
    if (!form.dob)         e.dob         = "Required";
    if (!form.begda)       e.begda       = "Required";
    setErrors(e);
    return Object.keys(e).length === 0;
  };

  const handleSave = () => { if (validate()) onSave(form); };

  return (
    <div className="card" style={{ marginBottom: 20 }}>
      <div className="section-title">{initial ? "Edit Driver" : "Add New Driver"}</div>
      {error && <Alert type="error">{error}</Alert>}
      <div className="form-grid-3">
        <FormGroup label="Driver ID">
          <input
            value={form.driver_id}
            onChange={set("driver_id")}
            placeholder="Auto-generated (e.g. DRV005)"
            disabled={!!initial}
          />
          <span style={{ fontSize: 11, color: "#6b7280", marginTop: 3, display: "block" }}>
            Leave blank to auto-assign
          </span>
        </FormGroup>
        <FormGroup label="Driver Name" required error={errors.driver_name}>
          <input value={form.driver_name} onChange={set("driver_name")} />
        </FormGroup>
        <FormGroup label="Mobile No 1" required error={errors.mobile_no1}>
          <input value={form.mobile_no1} onChange={set("mobile_no1")} maxLength={15} />
        </FormGroup>
        <FormGroup label="Mobile No 2">
          <input value={form.mobile_no2} onChange={set("mobile_no2")} maxLength={15} />
        </FormGroup>
        <FormGroup label="Driving Licence No" required error={errors.dl_no}>
          <input value={form.dl_no} onChange={set("dl_no")} />
        </FormGroup>
        <FormGroup label="DL Valid Upto" required error={errors.valid_upto}>
          <input type="date" value={form.valid_upto} onChange={set("valid_upto")} />
        </FormGroup>
        <FormGroup label="Date of Birth" required error={errors.dob}>
          <input type="date" value={form.dob} onChange={set("dob")} />
        </FormGroup>
        <FormGroup label="Valid From" required error={errors.begda}>
          <input type="date" value={form.begda} onChange={set("begda")} />
        </FormGroup>
        <FormGroup label="Valid To">
          <input type="date" value={form.endda} onChange={set("endda")} />
        </FormGroup>
        <FormGroup label="Address" style={{ gridColumn: "1/-1" }}>
          <input value={form.address} onChange={set("address")} />
        </FormGroup>
      </div>
      <div className="form-actions">
        <button className="btn btn-outline" onClick={onCancel}>Cancel</button>
        <button className="btn btn-primary" onClick={handleSave} disabled={saving}>
          {saving ? "Saving…" : "💾 Save Driver"}
        </button>
      </div>
    </div>
  );
}

export default function DriverMaster() {
  const [drivers, setDrivers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editRow, setEditRow]   = useState(null);
  const [deleteId, setDeleteId] = useState(null);   // { id, name }

  const [saving, setSaving]     = useState(false);
  const [error, setError]       = useState("");
  const [success, setSuccess]   = useState("");
  const [search, setSearch]     = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    try { setDrivers(await api.listDrivers()); }
    catch (e) { setError(e.message); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  const handleCreate = async (form) => {
    setSaving(true); setError("");
    try {
      const res = await api.createDriver(form);
      setSuccess(`Driver created successfully. Driver ID: ${res.driver_id}`);
      setShowForm(false); load();
    } catch (e) { setError(e.message); }
    finally { setSaving(false); }
  };

  const handleDelete = async () => {
    setError("");
    try {
      await api.deleteDriver(deleteId.id);
      setSuccess(`Driver "${deleteId.name}" deleted successfully.`);
      setDeleteId(null); load();
    } catch (e) {
      setError(e.message);
      setDeleteId(null);
    }
  };

  const filtered = search.trim()
    ? drivers.filter((d) =>
        d.DRIVER_NAME?.toLowerCase().includes(search.toLowerCase()) ||
        d.DRIVER_ID?.toLowerCase().includes(search.toLowerCase()) ||
        d.MOBILE_NO1?.includes(search)
      )
    : drivers;

  return (
    <div className="page">
      <div className="page-header">
        <h2 className="page-title">Driver Master</h2>
        {!showForm && (
          <button className="btn btn-primary" onClick={() => { setShowForm(true); setEditRow(null); }}>
            ➕ Add Driver
          </button>
        )}
      </div>

      {error   && <Alert type="error"   onClose={() => setError("")}>{error}</Alert>}
      {success && <Alert type="success" onClose={() => setSuccess("")}>{success}</Alert>}

      {showForm && (
        <DriverForm
          initial={editRow}
          onSave={handleCreate}
          onCancel={() => { setShowForm(false); setEditRow(null); }}
          saving={saving}
          error=""
        />
      )}

      <div className="filter-bar">
        <input
          className="filter-search"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="🔍  Search by name, ID, or mobile…"
        />
        <button className="btn btn-outline btn-sm" onClick={load}>↻ Refresh</button>
      </div>

      {loading ? <Spinner /> : filtered.length === 0 ? (
        <div className="card"><EmptyState icon="👤" message="No drivers found" /></div>
      ) : (
        <div className="card" style={{ padding: 0, overflow: "hidden" }}>
          <table className="data-table">
            <thead>
              <tr>
                <th>Driver ID</th>
                <th>Name</th>
                <th>Mobile 1</th>
                <th>Mobile 2</th>
                <th>DL No</th>
                <th>DL Valid Upto</th>
                <th>DOB</th>
                <th>Valid From</th>
                <th>Valid To</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((d) => {
                const dlExpired = d.VALID_UPTO < new Date().toISOString().split("T")[0];
                return (
                  <tr key={d.DRIVER_ID}>
                    <td className="mono-cell">{d.DRIVER_ID}</td>
                    <td style={{ fontWeight: 600 }}>{d.DRIVER_NAME}</td>
                    <td>{d.MOBILE_NO1}</td>
                    <td>{d.MOBILE_NO2 || "—"}</td>
                    <td>{d.DL_NO}</td>
                    <td>
                      <span style={{ color: dlExpired ? "var(--danger)" : "inherit" }}>
                        {d.VALID_UPTO}
                        {dlExpired && " ⚠️"}
                      </span>
                    </td>
                    <td>{d.DOB}</td>
                    <td>{d.BEGDA}</td>
                    <td>{d.ENDDA}</td>
                    <td>
                      <button
                        className="btn btn-danger btn-sm"
                        onClick={() => setDeleteId({ id: d.DRIVER_ID, name: d.DRIVER_NAME })}
                        title="Delete driver"
                      >
                        🗑 Delete
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {deleteId && (
        <ConfirmModal
          isOpen={true}
          title="Delete Driver"
          message={`Delete driver "${deleteId.name}" (${deleteId.id})? This cannot be undone. Note: drivers with an active vehicle mapping cannot be deleted.`}
          onConfirm={handleDelete}
          onCancel={() => setDeleteId(null)}
          isDangerous
        />
      )}
    </div>
  );
}
