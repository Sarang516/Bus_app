// src/pages/RequestDetail.jsx
import { useState, useEffect, useCallback } from "react";
import { api } from "../utils/api";
import { useAuth } from "../context/AuthContext";
import { Spinner, Alert, StatusBadge, FormGroup } from "../components/UI";

// ─── Constants (mirrored from NewRequest) ─────────────────────────────────────
const PASS_TYPES = ["Bus", "Car", "Deputation/Short term Posting"];
const APP_TYPES  = ["New", "Existing"];
const REASONS    = [
  "Medical Reason (Medical Certificate Mandatory)",
  "Change in Office Address",
  "Change in Residence Address",
  "OS+ 1 Year",
  "Transport Facility is stopped",
  "Eligibility changed due to Promotion",
  "Other Reason",
];

// ─── Attachment helpers ───────────────────────────────────────────────────────
function parseAttachment(value) {
  if (!value) return null;
  try { return JSON.parse(value); } catch {}
  return { name: value }; // plain text fallback
}

function AttachmentView({ value }) {
  const att = parseAttachment(value);
  if (!att) return <span>—</span>;
  // Support both old base64 format and new file_id format
  const href = att.file_id ? api.getFileUrl(att.file_id) : att.data || null;
  if (href) {
    return (
      <a href={href} target="_blank" rel="noreferrer"
        download={!att.file_id ? att.name : undefined}
        style={{ color: "var(--primary)", textDecoration: "underline" }}>
        📎 {att.name}
      </a>
    );
  }
  return <span>{att.name || "—"}</span>;
}

function AttachmentUpload({ value, onChange, required }) {
  const [uploading, setUploading] = useState(false);
  const [uploadErr, setUploadErr] = useState("");

  const att = parseAttachment(value);
  const fileUrl = att?.file_id ? api.getFileUrl(att.file_id) : att?.data || null;

  const handleFile = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    if (file.size > 2 * 1024 * 1024) {
      setUploadErr("File too large. Maximum allowed size is 2 MB.");
      e.target.value = "";
      return;
    }
    setUploadErr("");
    setUploading(true);
    try {
      const result = await api.uploadFile(file);
      onChange(JSON.stringify({ name: result.filename, file_id: result.file_id }));
    } catch (err) {
      setUploadErr(err.message || "Upload failed. Please try again.");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div>
      <input
        type="file"
        accept=".pdf,.doc,.docx,.jpg,.jpeg,.png,.gif"
        onChange={handleFile}
        disabled={uploading}
        style={{ display: "block", marginBottom: 6 }}
      />
      {uploading && <span style={{ fontSize: 12, color: "var(--primary)" }}>Uploading…</span>}
      {uploadErr && <span style={{ fontSize: 12, color: "var(--danger)" }}>{uploadErr}</span>}
      {att?.name && fileUrl && !uploading && (
        <span style={{ fontSize: 13, color: "var(--gray-500)" }}>
          ✅ <a href={fileUrl} target="_blank" rel="noreferrer" style={{ color: "var(--primary)" }}>{att.name}</a>
          &nbsp;·&nbsp;
          <button type="button" className="btn btn-outline btn-sm" style={{ padding: "1px 8px", fontSize: 12 }}
            onClick={() => onChange("")}>Remove</button>
        </span>
      )}
      {att?.name && !fileUrl && !uploading && (
        <span style={{ fontSize: 13, color: "var(--gray-500)" }}>Current: {att.name}</span>
      )}
      {required && !att && !uploading && (
        <span style={{ fontSize: 12, color: "var(--danger)" }}>Required</span>
      )}
    </div>
  );
}

// ─── Edit Draft Form ──────────────────────────────────────────────────────────
function EditDraftForm({ req, onSaved, onCancel }) {
  const [form, setForm] = useState({
    pass_type:              req.PASS_TYPE              || PASS_TYPES[0],
    application_type:       req.APPLICATION_TYPE       || APP_TYPES[0],
    reason:                 req.REASON                 || "",
    route_no:               req.ROUTE_NO               || "",
    pick_up_point:          req.PICK_UP_POINT          || "",
    nearest_station:        req.NEAREST_STATION        || "",
    dist_pickup_residence:  req.DIST_PICKUP_RESIDENCE  || "",
    dist_residence_station: req.DIST_RESIDENCE_STATION || "",
    effective_date:         req.EFFECTIVE_DATE         || "",
    attachment:             req.ATTACHMENT             || "",
  });
  const [routes,  setRoutes]  = useState([]);
  const [pickups, setPickups] = useState([]);
  const [errors,  setErrors]  = useState({});
  const [saving,  setSaving]  = useState(false);
  const [saveErr, setSaveErr] = useState("");

  useEffect(() => { api.listRoutes().then(setRoutes).catch(console.error); }, []);

  useEffect(() => {
    if (form.route_no) {
      api.listPickups(form.route_no).then(setPickups).catch(console.error);
    }
  }, [form.route_no]);

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));
  const twoDecimal = (v) => v && !/^\d+(\.\d{1,2})?$/.test(String(v).trim());
  const needsAttachment = form.reason?.includes("Medical") || form.reason?.includes("Change in");

  const setKm = (k) => (e) => {
    const v = e.target.value;
    setForm((f) => ({ ...f, [k]: v }));
    if (v && twoDecimal(v)) {
      setErrors((err) => ({ ...err, [k]: "Max 2 decimal places (e.g. 1.25)" }));
    } else {
      setErrors((err) => { const n = { ...err }; delete n[k]; return n; });
    }
  };

  const validate = () => {
    const e = {};
    if (!form.reason)               e.reason = "Required";
    if (!form.route_no)             e.route_no = "Required";
    if (!form.pick_up_point)        e.pick_up_point = "Required";
    if (!form.nearest_station)      e.nearest_station = "Required";
    if (!form.dist_pickup_residence || Number(form.dist_pickup_residence) <= 0)
                                    e.dist_pickup_residence = "Enter a valid distance > 0";
    else if (twoDecimal(form.dist_pickup_residence))
                                    e.dist_pickup_residence = "Max 2 decimal places (e.g. 1.25)";
    if (!form.dist_residence_station || Number(form.dist_residence_station) <= 0)
                                    e.dist_residence_station = "Enter a valid distance > 0";
    else if (twoDecimal(form.dist_residence_station))
                                    e.dist_residence_station = "Max 2 decimal places (e.g. 1.25)";
    if (!form.effective_date)       e.effective_date = "Required";
    if (needsAttachment && !form.attachment)
                                    e.attachment = "Document attachment is mandatory for this reason";
    setErrors(e);
    return Object.keys(e).length === 0;
  };

  const handleSave = async () => {
    if (!validate()) {
      const msgs = [];
      if (twoDecimal(form.dist_pickup_residence) || twoDecimal(form.dist_residence_station))
        msgs.push("Distance fields: Max 2 decimal places (e.g. 1.25)");
      if (needsAttachment && !form.attachment)
        msgs.push("Attachment is mandatory for the selected reason");
      setSaveErr(msgs.length ? msgs.join(" · ") : "Please fill all required fields before saving.");
      return;
    }
    setSaving(true); setSaveErr("");
    try {
      await api.updateRequest(req.REQID, { ...form, pernr: req.PERNR });
      onSaved();
    } catch (e) {
      setSaveErr(e.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="card" style={{ marginBottom: 16 }}>
      <div className="section-title">✏️ Edit Draft Request</div>

      {saveErr && <Alert type="error" onClose={() => setSaveErr("")}>{saveErr}</Alert>}

      {needsAttachment && !form.attachment && (
        <Alert type="warning">
          ⚕️ An attachment is mandatory for the selected reason.
        </Alert>
      )}

      <div className="form-grid-2">
        <FormGroup label="Pass Type" required>
          <select value={form.pass_type} onChange={set("pass_type")}>
            {PASS_TYPES.map((t) => <option key={t}>{t}</option>)}
          </select>
        </FormGroup>
        <FormGroup label="Application Type" required>
          <select value={form.application_type} onChange={set("application_type")}>
            {APP_TYPES.map((t) => <option key={t}>{t}</option>)}
          </select>
        </FormGroup>
      </div>

      <FormGroup label="Reason for Application" required error={errors.reason}>
        <select value={form.reason} onChange={set("reason")}>
          <option value="">— Select Reason —</option>
          {REASONS.map((r) => <option key={r}>{r}</option>)}
        </select>
      </FormGroup>

      <div className="form-grid-2">
        <FormGroup label="Route" required error={errors.route_no}>
          <select value={form.route_no} onChange={(e) => {
            setForm((f) => ({ ...f, route_no: e.target.value, pick_up_point: "" }));
          }}>
            <option value="">— Select Route —</option>
            {routes.map((r) => (
              <option key={r.SEQNR} value={r.SEQNR}>
                Route {r.SEQNR} — {r.ROUTE_FROM}
              </option>
            ))}
          </select>
        </FormGroup>
        <FormGroup label="Pick Up Point" required error={errors.pick_up_point}>
          <select value={form.pick_up_point} onChange={set("pick_up_point")} disabled={!form.route_no}>
            <option value="">— Select Pick Up Point —</option>
            {pickups.map((p) => (
              <option key={p.SUB_SEQNR} value={p.PICK_UP_POINT}>{p.PICK_UP_POINT}</option>
            ))}
          </select>
        </FormGroup>
      </div>

      <div className="form-grid-2">
        <FormGroup label="Nearest Railway / Metro Station" required error={errors.nearest_station}>
          <input value={form.nearest_station} onChange={set("nearest_station")} placeholder="e.g. Hinjewadi" />
        </FormGroup>
        <FormGroup label="Effective Date" required error={errors.effective_date}>
          <input type="date" value={form.effective_date} onChange={set("effective_date")} />
        </FormGroup>
      </div>

      <div className="form-grid-2">
        <FormGroup label="Distance: Pickup ↔ Residence (KM)" required error={errors.dist_pickup_residence}>
          <input
            type="text" inputMode="decimal"
            value={form.dist_pickup_residence}
            onChange={setKm("dist_pickup_residence")}
            placeholder="e.g. 2.50"
          />
        </FormGroup>
        <FormGroup label="Distance: Residence ↔ Station (KM)" required error={errors.dist_residence_station}>
          <input
            type="text" inputMode="decimal"
            value={form.dist_residence_station}
            onChange={setKm("dist_residence_station")}
            placeholder="e.g. 1.25"
          />
        </FormGroup>
      </div>

      <FormGroup label="Attachment / Document" required={needsAttachment} error={errors.attachment}>
        <AttachmentUpload
          value={form.attachment}
          onChange={(v) => setForm((f) => ({ ...f, attachment: v }))}
          required={needsAttachment}
        />
      </FormGroup>

      <div className="action-btns">
        <button className="btn btn-primary" onClick={handleSave} disabled={saving}>
          {saving ? "Saving…" : "💾 Save Draft"}
        </button>
        <button className="btn btn-outline" onClick={onCancel} disabled={saving}>
          Cancel
        </button>
      </div>
    </div>
  );
}

// ─── Info row ─────────────────────────────────────────────────────────────────
function InfoRow({ label, value, highlight }) {
  return (
    <div className="info-row">
      <span className="info-label">{label}</span>
      <span className={`info-value ${highlight ? "info-highlight" : ""}`}>
        {value || "—"}
      </span>
    </div>
  );
}

// ─── Activity timeline ────────────────────────────────────────────────────────
const actionColors = {
  CREATE:   "#6b7280",
  SUBMIT:   "#1a56a0",
  APPROVE:  "#16a34a",
  REJECT:   "#dc2626",
  ALLOT:    "#0ea5e9",
  WITHDRAW: "#9ca3af",
};

function Timeline({ logs }) {
  if (!logs || logs.length === 0) {
    return <p style={{ color: "var(--gray-400)", fontSize: 14 }}>No activity yet.</p>;
  }
  return (
    <div className="timeline">
      {logs.map((log, i) => (
        <div key={i} className="tl-item">
          <div
            className="tl-dot"
            style={{ background: actionColors[log.REQUEST_TYPE] || "#1a56a0" }}
          />
          <div className="tl-content">
            <div className="tl-header">
              <span className="tl-action">{log.REQUEST_TYPE}</span>
              <span className="tl-by">by {log.ACTION_BY_NAME || log.ACTION_BY}</span>
              <StatusBadge status={log.NEW_REQUEST_STATUS} text={log.NEW_STATUS_TEXT} />
            </div>
            <div className="tl-date">{log.ACTION_ON?.split("T")[0]}</div>
            {log.REMARKS && (
              <div className="tl-remarks">"{log.REMARKS}"</div>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

// ─── Action panel ─────────────────────────────────────────────────────────────
function ActionPanel({ req, user, vehicles, vehicleDriverMap, onActionDone, setError }) {
  const [remarks, setRemarks]       = useState("");
  const [selVehicle, setSelVehicle] = useState("");
  const [loading, setLoading]       = useState(false);

  const status = req.STATUS;
  const canSubmit   = status === "0001" && req.PERNR === user.pernr;
  const canApprove  = status === "0002" && user.role === "APPROVER";
  const canAllot    = status === "0003" && user.role === "TRANSPORT_ADMIN";
  const canWithdraw = ["0001","0002","0003"].includes(status) && user.role === "TRANSPORT_ADMIN";

  if (!canSubmit && !canApprove && !canAllot && !canWithdraw) return null;

  // Auto-derive driver from selected vehicle
  const mappedDriver = selVehicle ? vehicleDriverMap[selVehicle] : null;

  const doAction = async (action) => {
    if (action === "ALLOT" && (!selVehicle || !mappedDriver)) {
      setError("Please select a vehicle with an active driver mapping.");
      return;
    }
    setLoading(true); setError("");
    try {
      await api.takeAction(req.REQID, {
        action,
        action_by: user.pernr,
        remarks:    remarks    || undefined,
        vehicle_no: selVehicle || undefined,
        driver_id:  mappedDriver?.DRIVER_ID || undefined,
      });
      onActionDone();
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card action-panel">
      <div className="section-title">
        {canSubmit   && "Submit for Approval"}
        {canApprove  && "Approval Decision"}
        {canAllot    && "Vehicle Allotment"}
        {canWithdraw && !canAllot && "Withdraw Request"}
      </div>

      {/* Single remarks field — shown for all actions */}
      <FormGroup label="Remarks">
        {canAllot ? (
          <input
            value={remarks}
            onChange={(e) => setRemarks(e.target.value)}
            placeholder="Allotment remarks (optional)"
          />
        ) : (
          <textarea
            rows={2}
            value={remarks}
            onChange={(e) => setRemarks(e.target.value)}
            placeholder="Optional remarks…"
            style={{ resize: "vertical" }}
          />
        )}
      </FormGroup>

      {canAllot && (
        <>
          <FormGroup label="Select Vehicle" required>
            <select value={selVehicle} onChange={(e) => setSelVehicle(e.target.value)}>
              <option value="">— Select Vehicle —</option>
              {vehicles.map((v) => (
                <option key={v.VEHICLE_NO} value={v.VEHICLE_NO}>
                  {v.VEHICLE_NO} · {v.VEHICLE_TYPE} · {v.MAKE} {v.MODEL}
                  {v.REMAINING_CAPACITY != null ? ` · ${v.REMAINING_CAPACITY} seats left` : ""}
                </option>
              ))}
            </select>
          </FormGroup>

          <FormGroup label="Driver (auto-assigned from mapping)">
            {mappedDriver ? (
              <div style={{
                padding: "8px 12px", background: "#f0fdf4",
                border: "1px solid #86efac", borderRadius: 6, fontSize: 14,
              }}>
                <strong>{mappedDriver.DRIVER_NAME}</strong>
                <span style={{ color: "#6b7280", marginLeft: 8 }}>
                  ({mappedDriver.DRIVER_ID}) · {mappedDriver.MOBILE_NO1}
                </span>
              </div>
            ) : (
              <div style={{
                padding: "8px 12px", background: "#f9fafb",
                border: "1px solid #e5e7eb", borderRadius: 6,
                fontSize: 13, color: "#9ca3af",
              }}>
                {selVehicle ? "No active driver mapped to this vehicle" : "Select a vehicle to see its driver"}
              </div>
            )}
          </FormGroup>
        </>
      )}

      <div className="action-btns">
        {canSubmit && (
          <button className="btn btn-primary" onClick={() => doAction("SUBMIT")} disabled={loading}>
            📤 Submit for Approval
          </button>
        )}
        {canWithdraw && (
          <button className="btn btn-outline" onClick={() => doAction("WITHDRAW")} disabled={loading}>
            ↩ Withdraw
          </button>
        )}
        {canApprove && (
          <>
            <button className="btn btn-success" onClick={() => doAction("APPROVE")} disabled={loading}>
              ✅ Approve
            </button>
            <button className="btn btn-danger" onClick={() => doAction("REJECT")} disabled={loading}>
              ❌ Reject
            </button>
          </>
        )}
        {canAllot && (
          <button
            className="btn btn-primary"
            onClick={() => doAction("ALLOT")}
            disabled={loading || !selVehicle || !mappedDriver}
          >
            {loading ? "Allotting…" : "🚌 Allot Vehicle & Driver"}
          </button>
        )}
      </div>
    </div>
  );
}

// ─── Main component ───────────────────────────────────────────────────────────
export default function RequestDetail({ reqid, onBack }) {
  const { user }  = useAuth();
  const [req, setReq]                       = useState(null);
  const [vehicles, setVehicles]             = useState([]);
  const [vehicleDriverMap, setVehicleDriverMap] = useState({});
  const [loading, setLoading]               = useState(true);
  const [error, setError]                   = useState("");
  const [editing, setEditing]               = useState(false);

  const load = useCallback(async () => {
    setLoading(true); setError("");
    try {
      const r = await api.getRequest(reqid);
      setReq(r);
      // Load vehicles + active mappings in background — only needed for allotment
      Promise.all([api.listVehicles(), api.listActiveMappings()])
        .then(([v, mappings]) => {
          const driverMap = {};
          mappings.forEach((m) => {
            driverMap[m.VEHICLE_NO] = {
              DRIVER_ID:   m.DRIVER_ID,
              DRIVER_NAME: m.DRIVER_NAME,
              MOBILE_NO1:  m.MOBILE_NO1,
            };
          });
          setVehicleDriverMap(driverMap);
          // Only vehicles with an active driver mapping
          const mapped = new Set(Object.keys(driverMap));
          setVehicles(v.filter((veh) => veh.ACTIVE_FLAG === "Y" && mapped.has(veh.VEHICLE_NO)));
        })
        .catch(() => {});
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [reqid]);

  useEffect(() => { load(); }, [load]);

  if (loading) return <Spinner />;
  if (!req)    return <Alert type="error">{error || "Request not found."}</Alert>;

  const emp = req.EMPLOYEE || {};

  return (
    <div className="page">
      {/* Header */}
      <div className="detail-header">
        <div className="detail-header-left">
          <button className="btn btn-outline btn-sm" onClick={onBack}>← Back</button>
          <h2 className="page-title">{req.REQID}</h2>
          <StatusBadge status={req.STATUS} text={req.STATUS_TEXT} />
          {req.STATUS === "0001" && req.PERNR === user.pernr && !editing && (
            <button className="btn btn-outline btn-sm" onClick={() => setEditing(true)}>
              ✏️ Edit Draft
            </button>
          )}
        </div>
        <div className="detail-meta">
          Created: {req.REQUEST_CREATION_DATE?.split("T")[0]}
          {req.PENDING_WITH && (
            <> · Pending with: {req.PENDING_WITH_NAME ? `${req.PENDING_WITH_NAME} (${req.PENDING_WITH})` : req.PENDING_WITH}</>
          )}
        </div>
      </div>

      {error && <Alert type="error" onClose={() => setError("")}>{error}</Alert>}

      {editing && (
        <EditDraftForm
          req={req}
          onSaved={() => { setEditing(false); load(); }}
          onCancel={() => setEditing(false)}
        />
      )}

      <div className="detail-grid">
        {/* Left column */}
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          {/* Employee */}
          <div className="card">
            <div className="section-title">👤 Employee Information</div>
            <InfoRow label="Employee No"   value={emp.PERNR} />
            <InfoRow label="Name"          value={emp.ENAME} />
            <InfoRow label="Designation"   value={emp.DESIGNATION} />
            <InfoRow label="Department"    value={emp.DEPARTMENT} />
            <InfoRow label="Address"       value={emp.STRAS} />
            {req.REQUEST_CREATED_BY !== req.PERNR && (
              <InfoRow
                label="Raised By"
                value={`${req.REQUEST_CREATED_BY} (on behalf)`}
                highlight
              />
            )}
          </div>

          {/* Request details */}
          <div className="card">
            <div className="section-title">📋 Request Details</div>
            <InfoRow label="Pass Type"        value={req.PASS_TYPE} />
            <InfoRow label="Application Type" value={req.APPLICATION_TYPE} />
            <InfoRow label="Reason"           value={req.REASON} />
            <InfoRow label="Route"            value={req.ROUTE_FROM ? `Route ${req.ROUTE_NO} — ${req.ROUTE_FROM}` : `Route ${req.ROUTE_NO}`} />
            <InfoRow label="Pick Up Point"    value={req.PICK_UP_POINT} />
            <InfoRow label="Nearest Station"  value={req.NEAREST_STATION} />
            <InfoRow label="Dist (Pickup ↔ Residence)"  value={req.DIST_PICKUP_RESIDENCE ? `${req.DIST_PICKUP_RESIDENCE} KM` : "—"} />
            <InfoRow label="Dist (Residence ↔ Station)" value={req.DIST_RESIDENCE_STATION ? `${req.DIST_RESIDENCE_STATION} KM` : "—"} />
            <InfoRow label="Effective Date"   value={req.EFFECTIVE_DATE} />
            <div className="info-row">
              <span className="info-label">Attachment</span>
              <span className="info-value"><AttachmentView value={req.ATTACHMENT} /></span>
            </div>
            {req.REMARKS && <InfoRow label="Remarks" value={req.REMARKS} highlight />}
          </div>

          {/* Allotment info */}
          {req.STATUS === "0005" && req.ALLOTTED_VEHICLE_NO && (
            <div className="card allotment-card">
              <div className="section-title">🚌 Vehicle Allotment</div>
              <InfoRow label="Vehicle No"   value={req.ALLOTTED_VEHICLE_NO} highlight />
              {req.VEHICLE_INFO && (
                <>
                  <InfoRow label="Type/Make"  value={`${req.VEHICLE_INFO.VEHICLE_TYPE} · ${req.VEHICLE_INFO.MAKE} ${req.VEHICLE_INFO.MODEL}`} />
                </>
              )}
              <InfoRow label="Driver ID"    value={req.ALLOTTED_DRIVER_ID} highlight />
              {req.DRIVER_INFO && (
                <>
                  <InfoRow label="Driver Name"  value={req.DRIVER_INFO.DRIVER_NAME} />
                  <InfoRow label="Driver Mobile" value={req.DRIVER_INFO.MOBILE_NO1} />
                </>
              )}
            </div>
          )}
        </div>

        {/* Right column */}
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          {/* Action panel */}
          <ActionPanel
            req={req}
            user={user}
            vehicles={vehicles}
            vehicleDriverMap={vehicleDriverMap}
            onActionDone={load}
            setError={setError}
          />

          {/* Activity log */}
          <div className="card">
            <div className="section-title">🕐 Activity Log</div>
            <Timeline logs={req.LOGS} />
          </div>
        </div>
      </div>
    </div>
  );
}
