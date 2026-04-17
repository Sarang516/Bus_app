// src/pages/Profile.jsx
import { useState } from "react";
import { useAuth } from "../context/AuthContext";
import { api } from "../utils/api";
import { Alert, FormGroup } from "../components/UI";

function Avatar({ photo, name, size = 80 }) {
  return (
    <div style={{
      width: size, height: size, borderRadius: "50%",
      background: photo ? "transparent" : "#1a56a0",
      border: "3px solid #e5e7eb", overflow: "hidden",
      display: "flex", alignItems: "center", justifyContent: "center",
      flexShrink: 0,
    }}>
      {photo
        ? <img src={photo} alt={name} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
        : <span style={{ color: "white", fontWeight: 700, fontSize: size * 0.4 }}>
            {name?.charAt(0)?.toUpperCase() || "U"}
          </span>
      }
    </div>
  );
}

export default function Profile() {
  const { user, updateUser } = useAuth();

  const [editing, setEditing]   = useState(false);
  const [saving, setSaving]     = useState(false);
  const [success, setSuccess]   = useState("");
  const [error, setError]       = useState("");

  const [form, setForm] = useState({
    ename:        user?.ename        || "",
    designation:  user?.designation  || "",
    department:   user?.department   || "",
    address:      user?.address      || "",
    email:        user?.email        || "",
    mobile_no:    user?.mobile_no    || "",
    profile_photo: user?.profile_photo || null,
  });
  const [photoPreview, setPhotoPreview] = useState(user?.profile_photo || null);

  const [pwForm, setPwForm] = useState({ current_password: "", new_password: "", confirm_password: "" });
  const [pwErrors, setPwErrors] = useState({});
  const [changingPw, setChangingPw] = useState(false);

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));
  const setPw = (k) => (e) => setPwForm((f) => ({ ...f, [k]: e.target.value }));

  const handlePhotoChange = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    if (file.size > 500 * 1024) { setError("Image must be under 500 KB"); return; }
    const reader = new FileReader();
    reader.onload = (ev) => {
      setPhotoPreview(ev.target.result);
      setForm((f) => ({ ...f, profile_photo: ev.target.result }));
    };
    reader.readAsDataURL(file);
  };

  const handleSave = async () => {
    if (!form.ename.trim()) { setError("Name is required."); return; }
    setSaving(true); setError(""); setSuccess("");
    try {
      const res = await api.updateEmployeeProfile(user.pernr, {
        ename:        form.ename.trim()       || undefined,
        designation:  form.designation.trim() || null,
        department:   form.department.trim()  || null,
        address:      form.address.trim()     || null,
        email:        form.email.trim()       || null,
        mobile_no:    form.mobile_no.trim()   || null,
        profile_photo: form.profile_photo     || null,
      });
      updateUser({
        ename:         res.ename,
        designation:   res.designation,
        department:    res.department,
        address:       res.address,
        email:         res.email,
        mobile_no:     res.mobile_no,
        profile_photo: res.profile_photo,
      });
      setSuccess("Profile updated successfully.");
      setEditing(false);
    } catch (e) {
      setError(e.message);
    } finally {
      setSaving(false);
    }
  };

  const handlePasswordChange = async () => {
    const e = {};
    if (!pwForm.current_password)    e.current_password = "Required";
    if (!pwForm.new_password)        e.new_password = "Required";
    if (pwForm.new_password.length < 6) e.new_password = "Minimum 6 characters";
    if (pwForm.new_password !== pwForm.confirm_password) e.confirm_password = "Passwords do not match";
    setPwErrors(e);
    if (Object.keys(e).length > 0) return;

    setSaving(true); setError(""); setSuccess("");
    try {
      await api.updateEmployeeProfile(user.pernr, {
        current_password: pwForm.current_password,
        new_password:     pwForm.new_password,
      });
      setSuccess("Password changed successfully.");
      setChangingPw(false);
      setPwForm({ current_password: "", new_password: "", confirm_password: "" });
    } catch (e) {
      setError(e.message);
    } finally {
      setSaving(false);
    }
  };

  const cancelEdit = () => {
    setEditing(false);
    setForm({
      ename:        user?.ename        || "",
      designation:  user?.designation  || "",
      department:   user?.department   || "",
      address:      user?.address      || "",
      email:        user?.email        || "",
      mobile_no:    user?.mobile_no    || "",
      profile_photo: user?.profile_photo || null,
    });
    setPhotoPreview(user?.profile_photo || null);
    setError("");
  };

  const roleLabel = { EMPLOYEE: "Employee", APPROVER: "Approver", TRANSPORT_ADMIN: "Transport Admin" };

  return (
    <div className="page">
      <div className="page-header">
        <h2 className="page-title">My Profile</h2>
        {!editing && !changingPw && (
          <button className="btn btn-primary" onClick={() => setEditing(true)}>✏️ Edit Profile</button>
        )}
      </div>

      {error   && <Alert type="error"   onClose={() => setError("")}>{error}</Alert>}
      {success && <Alert type="success" onClose={() => setSuccess("")}>{success}</Alert>}

      {/* ── Profile card ─────────────────────────────────────────────────── */}
      {!editing && !changingPw && (
        <div className="card">
          <div style={{ display: "flex", alignItems: "center", gap: 24, marginBottom: 24 }}>
            <Avatar photo={user?.profile_photo} name={user?.ename} size={96} />
            <div>
              <div style={{ fontSize: 22, fontWeight: 700, color: "#111827" }}>{user?.ename}</div>
              <div style={{ fontSize: 14, color: "#6b7280", marginTop: 2 }}>{user?.designation || "—"}</div>
              <span style={{
                display: "inline-block", marginTop: 6, padding: "2px 10px",
                background: "#dbeafe", color: "#1e40af", borderRadius: 12,
                fontSize: 12, fontWeight: 600,
              }}>
                {roleLabel[user?.role] || user?.role}
              </span>
            </div>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px 32px" }}>
            {[
              ["Employee No (PERNR)", user?.pernr],
              ["Department",          user?.department || "—"],
              ["Email",               user?.email      || "—"],
              ["Mobile No",           user?.mobile_no  || "—"],
              ["Address",             user?.address    || "—"],
            ].map(([label, value]) => (
              <div key={label} style={{ padding: "8px 0", borderBottom: "1px solid #f3f4f6" }}>
                <div style={{ fontSize: 11, color: "#9ca3af", fontWeight: 600, textTransform: "uppercase", letterSpacing: 0.5 }}>{label}</div>
                <div style={{ fontSize: 14, color: "#111827", marginTop: 2 }}>{value}</div>
              </div>
            ))}
          </div>

          <div style={{ marginTop: 20 }}>
            <button className="btn btn-outline btn-sm" onClick={() => setChangingPw(true)}>🔒 Change Password</button>
          </div>
        </div>
      )}

      {/* ── Edit form ────────────────────────────────────────────────────── */}
      {editing && (
        <div className="card">
          <div className="section-title">Edit Profile</div>

          {/* Photo upload */}
          <div style={{ display: "flex", alignItems: "center", gap: 20, marginBottom: 20 }}>
            <Avatar photo={photoPreview} name={form.ename} size={80} />
            <div>
              <label style={{ fontSize: 13, fontWeight: 600, color: "#374151", display: "block", marginBottom: 4 }}>
                Profile Photo
              </label>
              <input type="file" accept="image/*" onChange={handlePhotoChange} style={{ fontSize: 12 }} />
              <div style={{ fontSize: 11, color: "#9ca3af", marginTop: 2 }}>Max 500 KB · JPG, PNG</div>
              {form.profile_photo && (
                <button
                  className="btn btn-outline btn-sm"
                  style={{ marginTop: 6, fontSize: 11 }}
                  onClick={() => { setPhotoPreview(null); setForm((f) => ({ ...f, profile_photo: null })); }}
                >
                  Remove photo
                </button>
              )}
            </div>
          </div>

          <div className="form-grid-3">
            <FormGroup label="Full Name" required>
              <input value={form.ename} onChange={set("ename")} />
            </FormGroup>
            <FormGroup label="Designation">
              <input value={form.designation} onChange={set("designation")} />
            </FormGroup>
            <FormGroup label="Department">
              <input value={form.department} onChange={set("department")} />
            </FormGroup>
            <FormGroup label="Email">
              <input type="email" value={form.email} onChange={set("email")} placeholder="your@email.com" />
            </FormGroup>
            <FormGroup label="Mobile No">
              <input value={form.mobile_no} onChange={set("mobile_no")} placeholder="9876543210" maxLength={15} />
            </FormGroup>
            <FormGroup label="Address" style={{ gridColumn: "1/-1" }}>
              <input value={form.address} onChange={set("address")} />
            </FormGroup>
          </div>

          <div className="form-actions">
            <button className="btn btn-outline" onClick={cancelEdit}>Cancel</button>
            <button className="btn btn-primary" onClick={handleSave} disabled={saving}>
              {saving ? "Saving…" : "💾 Save Changes"}
            </button>
          </div>
        </div>
      )}

      {/* ── Change password form ─────────────────────────────────────────── */}
      {changingPw && (
        <div className="card" style={{ maxWidth: 420 }}>
          <div className="section-title">Change Password</div>
          <FormGroup label="Current Password" required error={pwErrors.current_password}>
            <input type="password" value={pwForm.current_password} onChange={setPw("current_password")} />
          </FormGroup>
          <FormGroup label="New Password" required error={pwErrors.new_password}>
            <input type="password" value={pwForm.new_password} onChange={setPw("new_password")} placeholder="Minimum 6 characters" />
          </FormGroup>
          <FormGroup label="Confirm New Password" required error={pwErrors.confirm_password}>
            <input type="password" value={pwForm.confirm_password} onChange={setPw("confirm_password")} />
          </FormGroup>
          <div className="form-actions">
            <button className="btn btn-outline" onClick={() => { setChangingPw(false); setPwErrors({}); setError(""); }}>Cancel</button>
            <button className="btn btn-primary" onClick={handlePasswordChange} disabled={saving}>
              {saving ? "Saving…" : "🔒 Update Password"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
