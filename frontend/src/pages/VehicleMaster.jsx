// src/pages/VehicleMaster.jsx
import { useState, useEffect, useCallback } from "react";
import { api } from "../utils/api";
import { Spinner, Alert, FormGroup, EmptyState, ConfirmModal } from "../components/UI";

const VEHICLE_TYPES = ["BUS", "SEDAN", "PREMIUM SEDAN", "SUV", "PREMIUM SUV", "OTHER"];

// OTHER has no default — user must enter manually
const DEFAULT_CAPACITY = { BUS: 40, SEDAN: 6, "PREMIUM SEDAN": 6, SUV: 7, "PREMIUM SUV": 7, OTHER: "" };

const EMPTY_FORM = {
  vehicle_no: "", vehicle_type: "BUS", vehicle_category: "", make: "", model: "",
  chassis_no: "", engine_no: "", year_regn: "", date_purchase: "", po_number: "",
  cost_purchase: "", agency_name: "", insurance: "", fitness: "", permit: "", tax: "",
  tax_valid_upto: "", ins_valid_upto: "", fitness_valid_upto: "", permit_valid_upto: "",
  vehicle_from_date: new Date().toISOString().split("T")[0],
  vehicle_to_date: "9999-12-31",
  seating_capacity: 40,
};

function VehicleForm({ onSave, onCancel, saving, formError }) {
  const [form, setForm] = useState(EMPTY_FORM);
  const [errors, setErrors] = useState({});
  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  const isOther = form.vehicle_type === "OTHER";

  const validate = () => {
    const errs = {};
    if (!form.vehicle_no)         errs.vehicle_no        = "Required";
    if (!form.vehicle_type)       errs.vehicle_type      = "Required";
    if (isOther && !form.vehicle_category.trim()) errs.vehicle_category = "Required for Other type";
    if (isOther && (!form.seating_capacity || Number(form.seating_capacity) < 1))
                                  errs.seating_capacity  = "Enter valid capacity";
    if (!form.make)               errs.make              = "Required";
    if (!form.model)              errs.model             = "Required";
    if (!form.vehicle_from_date)  errs.vehicle_from_date = "Required";
    if (!form.ins_valid_upto)     errs.ins_valid_upto    = "Required";
    if (!form.fitness_valid_upto) errs.fitness_valid_upto= "Required";
    if (!form.permit_valid_upto)  errs.permit_valid_upto = "Required";
    if (!form.tax_valid_upto)     errs.tax_valid_upto    = "Required";
    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  return (
    <div className="card" style={{ marginBottom: 20 }}>
      <div className="section-title">Add New Vehicle</div>
      {formError && <Alert type="error">{formError}</Alert>}

      <div className="form-section-label">Basic Information</div>
      <div className="form-grid-3">
        <FormGroup label="Vehicle No" required error={errors.vehicle_no}>
          <input value={form.vehicle_no} onChange={set("vehicle_no")} placeholder="MH12AB1234" />
        </FormGroup>
        <FormGroup label="Vehicle Type" required error={errors.vehicle_type}>
          <select
            value={form.vehicle_type}
            onChange={(e) => setForm((f) => ({
              ...f,
              vehicle_type: e.target.value,
              seating_capacity: DEFAULT_CAPACITY[e.target.value] ?? 40,
              vehicle_category: "",   // reset category on type change
            }))}
          >
            {VEHICLE_TYPES.map((t) => <option key={t}>{t}</option>)}
          </select>
        </FormGroup>
        <FormGroup
          label={isOther ? "Vehicle Category (describe vehicle type)" : "Vehicle Category"}
          required={isOther}
          error={errors.vehicle_category}
        >
          <input
            value={form.vehicle_category}
            onChange={set("vehicle_category")}
            placeholder={isOther ? "e.g. Tempo Traveller, Mini Bus, Auto…" : "e.g. Staff Bus"}
          />
        </FormGroup>
        <FormGroup label="Make" required error={errors.make}>
          <input value={form.make} onChange={set("make")} placeholder="TATA / ASHOK LEYLAND" />
        </FormGroup>
        <FormGroup label="Model" required error={errors.model}>
          <input value={form.model} onChange={set("model")} placeholder="Starbus 32" />
        </FormGroup>
        <FormGroup label="Registration Year">
          <input value={form.year_regn} onChange={set("year_regn")} placeholder="2024" maxLength={4} />
        </FormGroup>
        <FormGroup label="Chassis No">
          <input value={form.chassis_no} onChange={set("chassis_no")} />
        </FormGroup>
        <FormGroup label="Engine No">
          <input value={form.engine_no} onChange={set("engine_no")} />
        </FormGroup>
        <FormGroup label="Date of Purchase">
          <input type="date" value={form.date_purchase} onChange={set("date_purchase")} />
        </FormGroup>
        <FormGroup label="PO Number">
          <input value={form.po_number} onChange={set("po_number")} />
        </FormGroup>
        <FormGroup label="Cost of Purchase (₹)">
          <input type="number" value={form.cost_purchase} onChange={set("cost_purchase")} />
        </FormGroup>
        <FormGroup label="Agency Name">
          <input value={form.agency_name} onChange={set("agency_name")} />
        </FormGroup>
        <FormGroup
          label="Seating Capacity (incl. driver)"
          required
          error={errors.seating_capacity}
        >
          <input
            type="number" min="1" max="200"
            value={form.seating_capacity}
            onChange={set("seating_capacity")}
            placeholder={isOther ? "Enter total seats including driver" : ""}
            style={isOther && !form.seating_capacity ? { borderColor: "#f97316" } : {}}
          />
          {isOther && (
            <span style={{ fontSize: 11, color: "#6b7280", marginTop: 3, display: "block" }}>
              Employee capacity = total seats − 1 (driver excluded)
            </span>
          )}
        </FormGroup>
      </div>

      <div className="form-section-label" style={{ marginTop: 8 }}>Compliance & Validity</div>
      <div className="form-grid-3">
        <FormGroup label="Insurance No">
          <input value={form.insurance} onChange={set("insurance")} />
        </FormGroup>
        <FormGroup label="Insurance Valid Upto" required error={errors.ins_valid_upto}>
          <input type="date" value={form.ins_valid_upto} onChange={set("ins_valid_upto")} />
        </FormGroup>
        <div />
        <FormGroup label="Fitness No">
          <input value={form.fitness} onChange={set("fitness")} />
        </FormGroup>
        <FormGroup label="Fitness Valid Upto" required error={errors.fitness_valid_upto}>
          <input type="date" value={form.fitness_valid_upto} onChange={set("fitness_valid_upto")} />
        </FormGroup>
        <div />
        <FormGroup label="Permit No">
          <input value={form.permit} onChange={set("permit")} />
        </FormGroup>
        <FormGroup label="Permit Valid Upto" required error={errors.permit_valid_upto}>
          <input type="date" value={form.permit_valid_upto} onChange={set("permit_valid_upto")} />
        </FormGroup>
        <div />
        <FormGroup label="Tax No">
          <input value={form.tax} onChange={set("tax")} />
        </FormGroup>
        <FormGroup label="Tax Valid Upto" required error={errors.tax_valid_upto}>
          <input type="date" value={form.tax_valid_upto} onChange={set("tax_valid_upto")} />
        </FormGroup>
        <div />
        <FormGroup label="Vehicle From Date" required error={errors.vehicle_from_date}>
          <input type="date" value={form.vehicle_from_date} onChange={set("vehicle_from_date")} />
        </FormGroup>
        <FormGroup label="Vehicle To Date">
          <input type="date" value={form.vehicle_to_date} onChange={set("vehicle_to_date")} />
        </FormGroup>
      </div>

      <div className="form-actions">
        <button className="btn btn-outline" onClick={onCancel}>Cancel</button>
        <button
          className="btn btn-primary"
          onClick={() => { if (validate()) onSave(form); }}
          disabled={saving}
        >
          {saving ? "Saving…" : "💾 Save Vehicle"}
        </button>
      </div>
    </div>
  );
}

export default function VehicleMaster() {
  const [vehicles, setVehicles] = useState([]);
  const [loading, setLoading]   = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [saving, setSaving]     = useState(false);
  const [error, setError]       = useState("");
  const [formError, setFormError] = useState("");
  const [success, setSuccess]   = useState("");
  const [search, setSearch]     = useState("");
  const [typeFilter, setTypeFilter] = useState("");
  const [deactivateId, setDeactivateId] = useState(null); // vehicle_no

  const load = useCallback(async () => {
    setLoading(true);
    try { setVehicles(await api.listVehicles()); }
    catch (e) { setError(e.message); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  const handleSave = async (form) => {
    setSaving(true); setFormError("");
    try {
      await api.createVehicle({
        ...form,
        cost_purchase: form.cost_purchase ? parseFloat(form.cost_purchase) : null,
      });
      setSuccess("Vehicle created successfully."); setShowForm(false); load();
    } catch (e) { setFormError(e.message); }
    finally { setSaving(false); }
  };

  const handleDeactivate = async () => {
    setError("");
    try {
      await api.updateVehicle(deactivateId, { active_flag: "N" });
      setSuccess(`Vehicle ${deactivateId} deactivated.`);
      setDeactivateId(null); load();
    } catch (e) { setError(e.message); setDeactivateId(null); }
  };

  const today = new Date().toISOString().split("T")[0];

  const filtered = vehicles.filter((v) => {
    const matchSearch = !search.trim() || (
      v.VEHICLE_NO?.toLowerCase().includes(search.toLowerCase()) ||
      v.MAKE?.toLowerCase().includes(search.toLowerCase()) ||
      v.MODEL?.toLowerCase().includes(search.toLowerCase())
    );
    const matchType = !typeFilter || v.VEHICLE_TYPE === typeFilter;
    return matchSearch && matchType;
  });

  return (
    <div className="page">
      <div className="page-header">
        <h2 className="page-title">Vehicle Master</h2>
        {!showForm && (
          <button className="btn btn-primary" onClick={() => setShowForm(true)}>
            ➕ Add Vehicle
          </button>
        )}
      </div>

      {error   && <Alert type="error"   onClose={() => setError("")}>{error}</Alert>}
      {success && <Alert type="success" onClose={() => setSuccess("")}>{success}</Alert>}

      {showForm && (
        <VehicleForm
          onSave={handleSave}
          onCancel={() => setShowForm(false)}
          saving={saving}
          formError={formError}
        />
      )}

      <div className="filter-bar">
        <input
          className="filter-search"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="🔍  Search by vehicle no, make, model…"
        />
        <select
          className="filter-select"
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
        >
          <option value="">All Types</option>
          {VEHICLE_TYPES.map((t) => <option key={t}>{t}</option>)}
        </select>
        <button className="btn btn-outline btn-sm" onClick={load}>↻ Refresh</button>
      </div>

      {loading ? <Spinner /> : filtered.length === 0 ? (
        <div className="card"><EmptyState icon="🚗" message="No vehicles found" /></div>
      ) : (
        <div className="card" style={{ padding: 0, overflow: "hidden" }}>
          <table className="data-table">
            <thead>
              <tr>
                <th>Vehicle No</th>
                <th>Type</th>
                <th>Make</th>
                <th>Model</th>
                <th>Year</th>
                <th>Capacity</th>
                <th>Used</th>
                <th>Remaining</th>
                <th>Insurance Exp</th>
                <th>Fitness Exp</th>
                <th>Permit Exp</th>
                <th>Tax Exp</th>
                <th>Status</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((v) => {
                const expired = (d) => d && d < today;
                const anyExpired = expired(v.INS_VALID_UPTO) || expired(v.FITNESS_VALID_UPTO) ||
                                   expired(v.PERMIT_VALID_UPTO) || expired(v.TAX_VALID_UPTO);
                return (
                  <tr key={v.VEHICLE_NO} className={anyExpired ? "row-warning" : ""}>
                    <td className="mono-cell">{v.VEHICLE_NO}</td>
                    <td><span className="type-tag">{v.VEHICLE_TYPE}</span></td>
                    <td>{v.MAKE}</td>
                    <td>{v.MODEL}</td>
                    <td>{v.YEAR_REGN || "—"}</td>
                    <td style={{ textAlign: "center", fontWeight: 600 }}>{v.EMPLOYEE_CAPACITY ?? "—"}</td>
                    <td style={{ textAlign: "center" }}>
                      <span style={{ color: v.USED_CAPACITY > 0 ? "#f97316" : "#9ca3af", fontWeight: 600 }}>
                        {v.USED_CAPACITY ?? 0}
                      </span>
                    </td>
                    <td style={{ textAlign: "center" }}>
                      {(() => {
                        const cap = v.EMPLOYEE_CAPACITY ?? 1;
                        const rem = v.REMAINING_CAPACITY ?? cap;
                        const pct = Math.max(0, Math.round((rem / cap) * 100));
                        const color = pct > 50 ? "#16a34a" : pct > 20 ? "#f97316" : "#dc2626";
                        return (
                          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                            <div style={{ flex: 1, background: "#e5e7eb", borderRadius: 4, height: 8, minWidth: 50 }}>
                              <div style={{ width: `${pct}%`, background: color, borderRadius: 4, height: 8, transition: "width .3s" }} />
                            </div>
                            <span style={{ fontSize: 12, fontWeight: 700, color, minWidth: 24 }}>{rem}</span>
                          </div>
                        );
                      })()}
                    </td>
                    <td style={{ color: expired(v.INS_VALID_UPTO)    ? "var(--danger)" : "inherit" }}>{v.INS_VALID_UPTO    || "—"}</td>
                    <td style={{ color: expired(v.FITNESS_VALID_UPTO) ? "var(--danger)" : "inherit" }}>{v.FITNESS_VALID_UPTO || "—"}</td>
                    <td style={{ color: expired(v.PERMIT_VALID_UPTO)  ? "var(--danger)" : "inherit" }}>{v.PERMIT_VALID_UPTO  || "—"}</td>
                    <td style={{ color: expired(v.TAX_VALID_UPTO)     ? "var(--danger)" : "inherit" }}>{v.TAX_VALID_UPTO     || "—"}</td>
                    <td>
                      <span className={`badge ${v.ACTIVE_FLAG === "Y" ? "badge-approved" : "badge-rejected"}`}>
                        {v.ACTIVE_FLAG === "Y" ? "Active" : "Inactive"}
                      </span>
                    </td>
                    <td>
                      {v.ACTIVE_FLAG === "Y" && (
                        <button
                          className="btn btn-outline btn-sm"
                          onClick={() => setDeactivateId(v.VEHICLE_NO)}
                          title="Deactivate"
                        >
                          🚫
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

      {deactivateId && (
        <ConfirmModal
          isOpen={true}
          title="Deactivate Vehicle"
          message={`Deactivate vehicle ${deactivateId}? It will no longer be available for allotment.`}
          confirmText="Deactivate"
          onConfirm={handleDeactivate}
          onCancel={() => setDeactivateId(null)}
          isDangerous
        />
      )}
    </div>
  );
}
