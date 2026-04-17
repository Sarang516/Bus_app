// src/pages/SignUp.jsx
import { useState } from "react";
import { Alert, FormGroup } from "../components/UI";

function PernrDisplay({ pernr, ename, onGoToLogin }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(pernr).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  return (
    <div className="login-page">
      <div className="login-card" style={{ maxWidth: 440 }}>
        {/* Header */}
        <div className="login-header">
          <div className="login-icon" style={{ background: "#dcfce7" }}>✅</div>
          <h1 style={{ color: "#15803d" }}>Account Created!</h1>
          <p>Welcome, <strong>{ename}</strong></p>
        </div>

        {/* PERNR box */}
        <div style={{
          background: "#f0fdf4", border: "2px solid #86efac",
          borderRadius: 12, padding: "20px 20px 16px", marginBottom: 20,
        }}>
          <p style={{ margin: "0 0 10px", fontSize: 13, color: "#166534", fontWeight: 600 }}>
            🎉 Your Employee Number (PERNR)
          </p>

          {/* PERNR + copy row */}
          <div style={{
            display: "flex", alignItems: "center", gap: 10,
            background: "white", border: "1px solid #86efac",
            borderRadius: 8, padding: "10px 14px",
          }}>
            <span style={{
              flex: 1, fontSize: 28, fontWeight: 800,
              color: "#15803d", letterSpacing: 3, fontFamily: "monospace",
            }}>
              {pernr}
            </span>
            <button
              onClick={handleCopy}
              style={{
                background: copied ? "#16a34a" : "#1a56a0",
                color: "white", border: "none", borderRadius: 6,
                padding: "6px 14px", fontSize: 13, fontWeight: 600,
                cursor: "pointer", whiteSpace: "nowrap", transition: "background .2s",
              }}
            >
              {copied ? "✓ Copied!" : "📋 Copy"}
            </button>
          </div>

          <p style={{ margin: "10px 0 0", fontSize: 12, color: "#166534" }}>
            ⚠️ Save this number — you will need it every time you log in.
          </p>
        </div>

        {/* Instructions */}
        <div style={{
          background: "#eff6ff", border: "1px solid #bfdbfe",
          borderRadius: 8, padding: "12px 14px", marginBottom: 20, fontSize: 13,
        }}>
          <p style={{ margin: 0, color: "#1e40af", fontWeight: 600 }}>How to log in:</p>
          <ol style={{ margin: "6px 0 0", paddingLeft: 18, color: "#1d4ed8", lineHeight: 1.8 }}>
            <li>Copy your Employee Number above</li>
            <li>Click <strong>"Go to Login"</strong> below</li>
            <li>Enter your PERNR and the password you just set</li>
          </ol>
        </div>

        <button
          className="btn btn-primary btn-full"
          onClick={onGoToLogin}
        >
          Go to Login →
        </button>
      </div>
    </div>
  );
}

export default function SignUp({ onBack }) {
  const [form, setForm] = useState({
    ename: "", designation: "", department: "", address: "",
    email: "", mobile_no: "", profile_photo: null,
    password: "", confirmPassword: "",
  });
  const [errors, setErrors]       = useState({});
  const [apiError, setApiError]   = useState("");
  const [loading, setLoading]     = useState(false);
  const [done, setDone]           = useState(null);
  const [photoPreview, setPhotoPreview] = useState(null);

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  const handlePhotoChange = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    if (file.size > 500 * 1024) {
      setErrors((prev) => ({ ...prev, profile_photo: "Image must be under 500 KB" }));
      return;
    }
    const reader = new FileReader();
    reader.onload = (ev) => {
      setPhotoPreview(ev.target.result);
      setForm((f) => ({ ...f, profile_photo: ev.target.result }));
      setErrors((prev) => ({ ...prev, profile_photo: "" }));
    };
    reader.readAsDataURL(file);
  };

  const validate = () => {
    const e = {};
    if (!form.ename.trim())       e.ename    = "Full name is required";
    if (!form.password)           e.password = "Password is required";
    if (form.password.length < 6) e.password = "Password must be at least 6 characters";
    if (form.password !== form.confirmPassword) e.confirmPassword = "Passwords do not match";
    setErrors(e);
    return Object.keys(e).length === 0;
  };

  const handleSubmit = async () => {
    if (!validate()) return;
    setLoading(true); setApiError("");
    try {
      const res = await fetch("/api/auth/register", {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ename:         form.ename.trim(),
          designation:   form.designation.trim()  || null,
          department:    form.department.trim()    || null,
          address:       form.address.trim()       || null,
          email:         form.email.trim()         || null,
          mobile_no:     form.mobile_no.trim()     || null,
          profile_photo: form.profile_photo        || null,
          password:      form.password,
        }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Registration failed.");
      }
      const data = await res.json();
      setDone({ pernr: data.pernr, ename: data.ename });
    } catch (err) {
      setApiError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (done) {
    return <PernrDisplay pernr={done.pernr} ename={done.ename} onGoToLogin={onBack} />;
  }

  return (
    <div className="login-page">
      <div className="login-card" style={{ maxWidth: 520 }}>
        <div className="login-header">
          <div className="login-icon">🚌</div>
          <h1>Create Account</h1>
          <p>Bus Transportation Booking System</p>
        </div>

        {apiError && <Alert type="error" onClose={() => setApiError("")}>{apiError}</Alert>}

        {/* Profile photo */}
        <div style={{ display: "flex", alignItems: "center", gap: 16, marginBottom: 16 }}>
          <div style={{
            width: 72, height: 72, borderRadius: "50%", background: "#e5e7eb",
            border: "2px dashed #9ca3af", display: "flex", alignItems: "center",
            justifyContent: "center", overflow: "hidden", flexShrink: 0,
          }}>
            {photoPreview
              ? <img src={photoPreview} alt="Preview" style={{ width: "100%", height: "100%", objectFit: "cover" }} />
              : <span style={{ fontSize: 28 }}>👤</span>}
          </div>
          <div style={{ flex: 1 }}>
            <label style={{ fontSize: 13, fontWeight: 600, color: "#374151", display: "block", marginBottom: 4 }}>
              Profile Photo <span style={{ fontWeight: 400, color: "#6b7280" }}>(optional)</span>
            </label>
            <input type="file" accept="image/*" onChange={handlePhotoChange} style={{ fontSize: 12 }} />
            {errors.profile_photo && <span style={{ color: "var(--danger)", fontSize: 12 }}>{errors.profile_photo}</span>}
            <div style={{ fontSize: 11, color: "#9ca3af", marginTop: 2 }}>Max 500 KB · JPG, PNG</div>
          </div>
        </div>

        <FormGroup label="Full Name" required error={errors.ename}>
          <input value={form.ename} onChange={set("ename")} placeholder="e.g. Rahul Sharma" />
        </FormGroup>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
          <FormGroup label="Designation">
            <input value={form.designation} onChange={set("designation")} placeholder="e.g. Software Engineer" />
          </FormGroup>
          <FormGroup label="Department">
            <input value={form.department} onChange={set("department")} placeholder="e.g. IT Department" />
          </FormGroup>
          <FormGroup label="Email">
            <input type="email" value={form.email} onChange={set("email")} placeholder="rahul@company.com" />
          </FormGroup>
          <FormGroup label="Mobile No">
            <input value={form.mobile_no} onChange={set("mobile_no")} placeholder="9876543210" maxLength={15} />
          </FormGroup>
        </div>

        <FormGroup label="Address">
          <input value={form.address} onChange={set("address")} placeholder="e.g. 12 MG Road, Pune" />
        </FormGroup>

        <FormGroup label="Password" required error={errors.password}>
          <input type="password" value={form.password} onChange={set("password")} placeholder="Minimum 6 characters" />
        </FormGroup>

        <FormGroup label="Confirm Password" required error={errors.confirmPassword}>
          <input
            type="password" value={form.confirmPassword} onChange={set("confirmPassword")}
            placeholder="Re-enter password"
            onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
          />
        </FormGroup>

        <button className="btn btn-primary btn-full" onClick={handleSubmit} disabled={loading} style={{ marginTop: 8 }}>
          {loading ? "Creating account…" : "Create Account →"}
        </button>

        <p style={{ textAlign: "center", marginTop: 16, fontSize: 13, color: "#6b7280" }}>
          Already have an account?{" "}
          <button onClick={onBack} style={{ background: "none", border: "none", color: "#2563eb", cursor: "pointer", fontWeight: 600, padding: 0 }}>
            Sign In
          </button>
        </p>
      </div>
    </div>
  );
}
