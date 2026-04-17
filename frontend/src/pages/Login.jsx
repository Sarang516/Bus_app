// src/pages/Login.jsx
import { useState } from "react";
import { useAuth } from "../context/AuthContext";
import { Alert } from "../components/UI";
import SignUp from "./SignUp";

export default function Login() {
  const { login } = useAuth();
  const [pernr, setPernr]       = useState("");
  const [password, setPassword] = useState("");
  const [error, setError]       = useState("");
  const [loading, setLoading]   = useState(false);
  const [showSignUp, setShowSignUp] = useState(false);

  if (showSignUp) {
    return <SignUp onBack={() => setShowSignUp(false)} />;
  }

  const handleLogin = async () => {
    if (!pernr.trim()) { setError("Employee Number is required."); return; }
    setLoading(true); setError("");
    try {
      await login(pernr.trim(), password);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-header">
          <div className="login-icon">🚌</div>
          <h1>Bus Booking System</h1>
          <p>Official Employee Transportation</p>
        </div>

        {error && <Alert type="error" onClose={() => setError("")}>{error}</Alert>}

        <div className="form-group">
          <label>Employee Number (PERNR)</label>
          <input
            value={pernr}
            onChange={(e) => setPernr(e.target.value)}
            placeholder="e.g. 10000001"
            onKeyDown={(e) => e.key === "Enter" && handleLogin()}
          />
        </div>

        <div className="form-group">
          <label>Password</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Password"
            onKeyDown={(e) => e.key === "Enter" && handleLogin()}
          />
        </div>

        <button
          className="btn btn-primary btn-full"
          onClick={handleLogin}
          disabled={loading}
        >
          {loading ? "Signing in…" : "Sign In →"}
        </button>

        <p style={{ textAlign: "center", marginTop: 16, fontSize: 13, color: "#6b7280" }}>
          New employee?{" "}
          <button
            onClick={() => setShowSignUp(true)}
            style={{
              background: "none", border: "none", color: "#2563eb",
              cursor: "pointer", fontWeight: 600, padding: 0,
            }}
          >
            Create an account
          </button>
        </p>
      </div>
    </div>
  );
}
