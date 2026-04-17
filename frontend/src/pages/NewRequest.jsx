// src/pages/NewRequest.jsx
import { useState, useEffect } from "react";
import { api } from "../utils/api";
import { useAuth } from "../context/AuthContext";
import { Alert, FormGroup } from "../components/UI";

// ─── Step progress bar ────────────────────────────────────────────────────────
const STEPS = ["Transport Option", "Employee Details", "Application Form", "Review & Submit"];

function StepBar({ current }) {
  return (
    <div className="step-bar">
      {STEPS.map((label, i) => (
        <div
          key={i}
          className={`step-item ${i < current ? "done" : i === current ? "active" : ""}`}
        >
          <div className="step-circle">{i < current ? "✓" : i + 1}</div>
          <div className="step-label">{label}</div>
          {i < STEPS.length - 1 && <div className="step-line" />}
        </div>
      ))}
    </div>
  );
}

// ─── Step 0 – Opt-in ──────────────────────────────────────────────────────────
function StepOptIn({ onYes, onNo }) {
  const [choice, setChoice] = useState(null);
  return (
    <div className="card">
      <div className="section-title">Company Transportation — Opt In</div>
      <p className="step-desc">
        Do you wish to use the company-provided transportation service?
      </p>
      <div className="optin-cards">
        <div
          className={`optin-card ${choice === "yes" ? "selected" : ""}`}
          onClick={() => setChoice("yes")}
        >
          <span className="optin-icon">🚌</span>
          <strong>Yes, I want Bus</strong>
          <p>Open bus selection form</p>
        </div>
        <div
          className={`optin-card optin-no ${choice === "no" ? "selected-no" : ""}`}
          onClick={() => setChoice("no")}
        >
          <span className="optin-icon">🚫</span>
          <strong>No, Not Required</strong>
          <p>No further action needed</p>
        </div>
      </div>
      {choice === "no" && (
        <Alert type="warning">
          You have opted out of company transportation. No action required.
        </Alert>
      )}
      <div className="step-actions">
        <button
          className="btn btn-primary"
          disabled={choice !== "yes"}
          onClick={onYes}
        >
          Continue →
        </button>
        {choice === "no" && (
          <button className="btn btn-outline" onClick={onNo}>
            Back to Home
          </button>
        )}
      </div>
    </div>
  );
}

// ─── Step 1 – Employee details ────────────────────────────────────────────────
function StepEmployeeDetails({ user, onBehalfOf, setOnBehalfOf, targetEmp, setTargetEmp, onNext, onBack }) {
  const [loading, setLoading]   = useState(false);
  const [err, setErr]           = useState("");
  const [allEmps, setAllEmps]   = useState([]);
  const [showPicker, setShowPicker] = useState(false);
  const [pickerSearch, setPickerSearch] = useState("");

  const handleLookup = async () => {
    setErr("");
    if (onBehalfOf.trim()) {
      // Direct PERNR lookup
      setLoading(true);
      try {
        const emp = await api.getEmployee(onBehalfOf.trim());
        setTargetEmp(emp);
        setShowPicker(false);
      } catch (e) {
        setErr(e.message); setTargetEmp(null);
      } finally { setLoading(false); }
    } else {
      // No PERNR entered — load full list and show picker
      setLoading(true);
      try {
        const emps = await api.listEmployees();
        setAllEmps(emps.filter((e) => e.PERNR !== user.pernr));
        setPickerSearch("");
        setShowPicker(true);
      } catch (e) {
        setErr(e.message);
      } finally { setLoading(false); }
    }
  };

  const selectEmp = (emp) => {
    setOnBehalfOf(emp.PERNR);
    setTargetEmp(emp);
    setShowPicker(false);
  };

  const pickerFiltered = pickerSearch.trim()
    ? allEmps.filter((e) =>
        e.ENAME?.toLowerCase().includes(pickerSearch.toLowerCase()) ||
        e.PERNR?.includes(pickerSearch) ||
        e.DEPARTMENT?.toLowerCase().includes(pickerSearch.toLowerCase())
      )
    : allEmps;

  const displayEmp = targetEmp || user;

  return (
    <div className="card">
      <div className="section-title">Employee Details (Read Only)</div>
      <div className="readonly-grid">
        {[
          ["Employee No",    displayEmp.PERNR || displayEmp.pernr],
          ["Employee Name",  displayEmp.ENAME || displayEmp.ename],
          ["Designation",    displayEmp.DESIGNATION || displayEmp.designation],
          ["Department",     displayEmp.DEPARTMENT  || displayEmp.department],
          ["Residence Addr", displayEmp.STRAS || displayEmp.address],
          ["Date of Application", new Date().toLocaleDateString("en-IN")],
        ].map(([k, v]) => (
          <div key={k} className="readonly-field">
            <span className="ro-label">{k}</span>
            <span className="ro-value">{v || "—"}</span>
          </div>
        ))}
      </div>

      <div className="divider" />
      <div className="section-title" style={{ marginBottom: 8 }}>On Behalf (Optional)</div>
      <p className="step-desc" style={{ marginBottom: 12 }}>
        Leave blank and click Lookup to browse all employees, or enter a PERNR directly.
      </p>
      <div style={{ display: "flex", gap: 10 }}>
        <input
          style={{ flex: 1 }}
          value={onBehalfOf}
          onChange={(e) => { setOnBehalfOf(e.target.value); setShowPicker(false); }}
          placeholder="Enter PERNR or click Lookup to browse"
        />
        <button className="btn btn-outline" onClick={handleLookup} disabled={loading}>
          {loading ? "…" : "🔍 Lookup"}
        </button>
        {targetEmp && (
          <button className="btn btn-outline btn-sm" onClick={() => {
            setTargetEmp(null); setOnBehalfOf(""); setShowPicker(false);
          }}>✕ Clear</button>
        )}
      </div>

      {err && <Alert type="error" onClose={() => setErr("")}>{err}</Alert>}

      {/* Employee picker list */}
      {showPicker && (
        <div style={{ marginTop: 12, border: "1px solid #e5e7eb", borderRadius: 8, overflow: "hidden" }}>
          <div style={{ padding: "8px 12px", background: "#f9fafb", borderBottom: "1px solid #e5e7eb" }}>
            <input
              autoFocus
              style={{ width: "100%", padding: "6px 10px", border: "1px solid #d1d5db", borderRadius: 6, fontSize: 13 }}
              placeholder="🔍  Search by name, PERNR, or department…"
              value={pickerSearch}
              onChange={(e) => setPickerSearch(e.target.value)}
            />
          </div>
          <div style={{ maxHeight: 240, overflowY: "auto" }}>
            {pickerFiltered.length === 0 ? (
              <div style={{ padding: 16, textAlign: "center", color: "#9ca3af", fontSize: 13 }}>No employees found</div>
            ) : pickerFiltered.map((emp) => (
              <div
                key={emp.PERNR}
                onClick={() => selectEmp(emp)}
                style={{
                  padding: "10px 14px", cursor: "pointer", borderBottom: "1px solid #f3f4f6",
                  display: "flex", justifyContent: "space-between", alignItems: "center",
                }}
                onMouseEnter={(e) => e.currentTarget.style.background = "#eff6ff"}
                onMouseLeave={(e) => e.currentTarget.style.background = ""}
              >
                <div>
                  <div style={{ fontWeight: 600, fontSize: 14 }}>{emp.ENAME}</div>
                  <div style={{ fontSize: 12, color: "#6b7280" }}>{emp.DESIGNATION} · {emp.DEPARTMENT}</div>
                </div>
                <div style={{ fontSize: 12, color: "#2563eb", fontFamily: "monospace" }}>{emp.PERNR}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {targetEmp && (
        <div className="on-behalf-tag">
          ✅ Raising on behalf of: <strong>{targetEmp.ENAME}</strong> ({targetEmp.PERNR})
        </div>
      )}

      <div className="step-actions">
        <button className="btn btn-outline" onClick={onBack}>← Back</button>
        <button className="btn btn-primary" onClick={onNext}>Continue →</button>
      </div>
    </div>
  );
}

// ─── Attachment upload helper ─────────────────────────────────────────────────
function AttachmentUpload({ value, onChange, required }) {
  let currentName = null;
  let currentData = null;
  try {
    const obj = JSON.parse(value);
    if (obj.name) { currentName = obj.name; currentData = obj.data; }
  } catch { /* plain text or empty */ }

  const handleFile = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    if (file.size > 2 * 1024 * 1024) {
      alert("File too large. Maximum allowed size is 2 MB.");
      e.target.value = "";
      return;
    }
    const reader = new FileReader();
    reader.onload = () => {
      onChange(JSON.stringify({ name: file.name, data: reader.result }));
    };
    reader.readAsDataURL(file);
  };

  return (
    <div>
      <input
        type="file"
        accept=".pdf,.doc,.docx,.jpg,.jpeg,.png,.gif"
        onChange={handleFile}
        style={{ display: "block", marginBottom: 6 }}
      />
      {required && !currentName && !value && (
        <span style={{ fontSize: 12, color: "var(--danger)" }}>Required</span>
      )}
      {currentName && (
        <span style={{ fontSize: 13, color: "var(--gray-500)" }}>
          Selected:&nbsp;
          {currentData
            ? <a href={currentData} download={currentName} style={{ color: "var(--primary)" }}>{currentName}</a>
            : currentName}
          &nbsp;·&nbsp;
          <button type="button" className="btn btn-outline btn-sm"
            style={{ padding: "1px 8px", fontSize: 12 }}
            onClick={() => onChange("")}>Remove</button>
        </span>
      )}
    </div>
  );
}

// ─── Step 2 – Application Form ────────────────────────────────────────────────
const PASS_TYPES   = ["Bus", "Car", "Deputation/Short term Posting"];
const APP_TYPES    = ["New", "Existing"];
const REASONS      = [
  "Medical Reason (Medical Certificate Mandatory)",
  "Change in Office Address",
  "Change in Residence Address",
  "OS+ 1 Year",
  "Transport Facility is stopped",
  "Eligibility changed due to Promotion",
  "Other Reason",
];

function StepForm({ form, setForm, onNext, onBack, onSaveDraft, saving }) {
  const [routes, setRoutes]   = useState([]);
  const [pickups, setPickups] = useState([]);
  const [errors, setErrors]   = useState({});
  const [draftAlert, setDraftAlert] = useState("");

  useEffect(() => { api.listRoutes().then(setRoutes).catch(console.error); }, []);

  useEffect(() => {
    if (form.route_no) {
      api.listPickups(form.route_no).then(setPickups).catch(console.error);
      setForm((f) => ({ ...f, pick_up_point: "" }));
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
    if (!form.dist_pickup_residence || form.dist_pickup_residence <= 0)
                                    e.dist_pickup_residence = "Enter a valid distance > 0";
    else if (twoDecimal(form.dist_pickup_residence))
                                    e.dist_pickup_residence = "Max 2 decimal places (e.g. 1.25)";
    if (!form.dist_residence_station || form.dist_residence_station <= 0)
                                    e.dist_residence_station = "Enter a valid distance > 0";
    else if (twoDecimal(form.dist_residence_station))
                                    e.dist_residence_station = "Max 2 decimal places (e.g. 1.25)";
    if (!form.effective_date)       e.effective_date = "Required";
    if (needsAttachment && !form.attachment.trim())
                                    e.attachment = "Document attachment is mandatory for this reason";
    setErrors(e);
    return Object.keys(e).length === 0;
  };

  const validateKm = () => {
    const e = {};
    if (form.dist_pickup_residence && twoDecimal(form.dist_pickup_residence))
      e.dist_pickup_residence = "Max 2 decimal places (e.g. 1.25)";
    if (form.dist_residence_station && twoDecimal(form.dist_residence_station))
      e.dist_residence_station = "Max 2 decimal places (e.g. 1.25)";
    setErrors((prev) => ({ ...prev, ...e }));
    return Object.keys(e).length === 0;
  };

  const handleSaveDraft = () => {
    const kmOk = validateKm();
    const attachOk = !(needsAttachment && !form.attachment?.trim());
    if (!attachOk) {
      setErrors((prev) => ({ ...prev, attachment: "Document attachment is mandatory for this reason" }));
    }
    if (!kmOk || !attachOk) {
      setDraftAlert("Please fix the errors above before saving.");
      return;
    }
    setDraftAlert("");
    onSaveDraft();
  };
  const handleNext = () => { if (validate()) onNext(); };

  const medicalRequired = form.reason?.includes("Medical");

  return (
    <div className="card">
      <div className="section-title">Bus Application Form</div>
      {draftAlert && <Alert type="error" onClose={() => setDraftAlert("")}>{draftAlert}</Alert>}

      {medicalRequired && (
        <Alert type="warning">
          ⚕️ Medical Certificate is mandatory for this reason. Please attach it below.
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
          <select value={form.route_no} onChange={set("route_no")}>
            <option value="">— Select Route —</option>
            {routes.map((r) => (
              <option key={r.SEQNR} value={r.SEQNR}>
                Route {r.SEQNR} — {r.ROUTE_FROM}
              </option>
            ))}
          </select>
        </FormGroup>

        <FormGroup label="Pick Up Point" required error={errors.pick_up_point}>
          <select
            value={form.pick_up_point}
            onChange={set("pick_up_point")}
            disabled={!form.route_no}
          >
            <option value="">— Select Pick Up Point —</option>
            {pickups.map((p) => (
              <option key={p.SUB_SEQNR} value={p.PICK_UP_POINT}>
                {p.PICK_UP_POINT}
              </option>
            ))}
          </select>
        </FormGroup>
      </div>

      <div className="form-grid-2">
        <FormGroup label="Nearest Railway Station" required error={errors.nearest_station}>
          <input
            value={form.nearest_station}
            onChange={set("nearest_station")}
            placeholder="e.g. Pune Junction"
          />
        </FormGroup>

        <FormGroup label="Effective Date" required error={errors.effective_date}>
          <input
            type="date"
            value={form.effective_date}
            onChange={set("effective_date")}
            min={new Date().toISOString().split("T")[0]}
          />
        </FormGroup>
      </div>

      <div className="form-grid-2">
        <FormGroup
          label="Distance: Pick Up Point ↔ Residence (KM)"
          required
          error={errors.dist_pickup_residence}
        >
          <input
            type="text" inputMode="decimal"
            value={form.dist_pickup_residence}
            onChange={setKm("dist_pickup_residence")}
            placeholder="e.g. 2.50"
          />
        </FormGroup>

        <FormGroup
          label="Distance: Residence ↔ Nearest Station (KM)"
          required
          error={errors.dist_residence_station}
        >
          <input
            type="text" inputMode="decimal"
            value={form.dist_residence_station}
            onChange={setKm("dist_residence_station")}
            placeholder="e.g. 1.25"
          />
        </FormGroup>
      </div>

      <FormGroup
        label={needsAttachment ? "Attachment (Mandatory)" : "Attachment (Optional)"}
        required={needsAttachment}
        error={errors.attachment}
      >
        <AttachmentUpload
          value={form.attachment}
          onChange={(v) => setForm((f) => ({ ...f, attachment: v }))}
          required={needsAttachment}
        />
      </FormGroup>

      <div className="step-actions">
        <button className="btn btn-outline" onClick={onBack}>← Back</button>
        <button className="btn btn-secondary" onClick={handleSaveDraft} disabled={saving}>
          {saving ? "Saving…" : "💾 Save as Draft"}
        </button>
        <button className="btn btn-primary" onClick={handleNext}>
          Review →
        </button>
      </div>
    </div>
  );
}

// ─── Step 3 – Review ──────────────────────────────────────────────────────────
function StepReview({ form, targetEmp, user, onSubmit, onBack, submitting, routes }) {
  const emp = targetEmp || user;
  const routeLabel = (() => {
    const r = routes.find((r) => r.SEQNR === form.route_no);
    return r ? `Route ${r.SEQNR} — ${r.ROUTE_FROM}` : `Route ${form.route_no}`;
  })();
  const rows = [
    ["Employee",        emp.ENAME || emp.ename],
    ["Pass Type",       form.pass_type],
    ["Application Type",form.application_type],
    ["Reason",          form.reason],
    ["Route",           routeLabel],
    ["Pick Up Point",   form.pick_up_point],
    ["Nearest Station", form.nearest_station],
    ["Dist (Pickup↔Residence)", `${form.dist_pickup_residence} KM`],
    ["Dist (Residence↔Station)",`${form.dist_residence_station} KM`],
    ["Effective Date",  form.effective_date],
    ["Attachment",      (() => { try { const a = JSON.parse(form.attachment); return a.name || "—"; } catch { return form.attachment || "—"; } })()],
  ];

  return (
    <div className="card">
      <div className="section-title">Review & Submit</div>
      <p className="step-desc">Please verify the details below before submitting.</p>

      <div className="review-grid">
        {rows.map(([k, v]) => (
          <div key={k} className="review-row">
            <span className="review-label">{k}</span>
            <span className="review-value">{v}</span>
          </div>
        ))}
      </div>

      <div className="step-actions">
        <button className="btn btn-outline" onClick={onBack}>← Edit</button>
        <button
          className="btn btn-primary"
          onClick={onSubmit}
          disabled={submitting}
        >
          {submitting ? "Submitting…" : "✅ Submit Request"}
        </button>
      </div>
    </div>
  );
}

// ─── Success ──────────────────────────────────────────────────────────────────
function SuccessScreen({ reqid, isDraft, onReset, setPage, onEditDraft }) {
  return (
    <div className="card success-screen">
      <div className="success-icon">{isDraft ? "💾" : "🎉"}</div>
      <h2 className="success-title">{isDraft ? "Draft Saved!" : "Request Submitted!"}</h2>
      <p className="success-sub">
        Your request <strong>{reqid}</strong> has been {isDraft ? "saved as a draft" : "submitted for approval"}.
      </p>
      {!isDraft && (
        <p className="success-sub">The approver will be notified. You can track status in "My Requests".</p>
      )}
      <div className="step-actions" style={{ justifyContent: "center" }}>
        {isDraft && (
          <button className="btn btn-primary" onClick={onEditDraft}>✏️ Edit Draft</button>
        )}
        <button className="btn btn-outline" onClick={onReset}>Create Another</button>
        <button className="btn btn-outline" onClick={() => setPage("my-requests")}>
          My Requests →
        </button>
      </div>
    </div>
  );
}

// ─── Main wizard ─────────────────────────────────────────────────────────────
export default function NewRequest({ setPage }) {
  const { user } = useAuth();

  const [step, setStep]               = useState(0);
  const [onBehalfOf, setOnBehalfOf]   = useState("");
  const [targetEmp, setTargetEmp]     = useState(null);
  const [submitting, setSubmitting]   = useState(false);
  const [saving, setSaving]           = useState(false);
  const [error, setError]             = useState("");
  const [doneReqid, setDoneReqid]     = useState(null);
  const [isDraft, setIsDraft]         = useState(false);
  const [routes, setRoutes]           = useState([]);

  // Load routes once for use in review step
  useEffect(() => { api.listRoutes().then(setRoutes).catch(() => {}); }, []);

  const today = new Date().toISOString().split("T")[0];
  const [form, setForm] = useState({
    pass_type: "Bus", application_type: "New",
    reason: "", route_no: "", pick_up_point: "",
    nearest_station: "", dist_pickup_residence: "",
    dist_residence_station: "", effective_date: today, attachment: "",
  });

  const buildPayload = () => ({
    pernr: targetEmp?.PERNR || user.pernr,
    on_behalf_of: targetEmp ? user.pernr : null,
    pass_type: form.pass_type,
    application_type: form.application_type,
    reason: form.reason,
    route_no: form.route_no,
    pick_up_point: form.pick_up_point,
    nearest_station: form.nearest_station,
    dist_pickup_residence: parseFloat(form.dist_pickup_residence) || 0,
    dist_residence_station: parseFloat(form.dist_residence_station) || 0,
    effective_date: form.effective_date,
    attachment: form.attachment || null,
  });

  const handleSaveDraft = async () => {
    setSaving(true); setError("");
    try {
      const res = await api.createRequest(buildPayload());
      setIsDraft(true);
      setDoneReqid(res.reqid);
    } catch (e) {
      setError(e.message);
    } finally {
      setSaving(false);
    }
  };

  const handleSubmit = async () => {
    setSubmitting(true); setError("");
    try {
      const res = await api.createRequest(buildPayload());
      await api.takeAction(res.reqid, {
        action: "SUBMIT",
        action_by: user.pernr,
        remarks: "Submitted by employee",
      });
      setIsDraft(false);
      setDoneReqid(res.reqid);
    } catch (e) {
      setError(e.message);
    } finally {
      setSubmitting(false);
    }
  };

  const reset = () => {
    setStep(0); setDoneReqid(null); setError(""); setIsDraft(false);
    setOnBehalfOf(""); setTargetEmp(null);
    setForm({
      pass_type: "Bus", application_type: "New",
      reason: "", route_no: "", pick_up_point: "",
      nearest_station: "", dist_pickup_residence: "",
      dist_residence_station: "", effective_date: today, attachment: "",
    });
  };

  if (doneReqid) {
    return (
      <div className="page">
        <SuccessScreen
          reqid={doneReqid}
          isDraft={isDraft}
          onReset={reset}
          setPage={setPage}
          onEditDraft={() => setPage("my-requests")}
        />
      </div>
    );
  }

  return (
    <div className="page">
      <h2 className="page-title" style={{ marginBottom: 20 }}>New Transport Request</h2>
      <StepBar current={step} />
      {error && <Alert type="error" onClose={() => setError("")}>{error}</Alert>}

      {step === 0 && (
        <StepOptIn
          onYes={() => setStep(1)}
          onNo={() => setPage("dashboard")}
        />
      )}
      {step === 1 && (
        <StepEmployeeDetails
          user={user}
          onBehalfOf={onBehalfOf}
          setOnBehalfOf={setOnBehalfOf}
          targetEmp={targetEmp}
          setTargetEmp={setTargetEmp}
          onNext={() => setStep(2)}
          onBack={() => setStep(0)}
        />
      )}
      {step === 2 && (
        <StepForm
          form={form}
          setForm={setForm}
          onNext={() => setStep(3)}
          onBack={() => setStep(1)}
          onSaveDraft={handleSaveDraft}
          saving={saving}
        />
      )}
      {step === 3 && (
        <StepReview
          form={form}
          targetEmp={targetEmp}
          user={user}
          onSubmit={handleSubmit}
          onBack={() => setStep(2)}
          submitting={submitting}
          routes={routes}
        />
      )}
    </div>
  );
}
