"use client";

import { FormEvent, useState } from "react";
import { api, setSession } from "@/lib/api";
import { ROLE_LABEL } from "@/lib/nav";

export default function LoginPage() {
  const [email, setEmail] = useState("gov@sentinel.gov");
  const [password, setPassword] = useState("ChangeMe!Gov12");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const s = await api<{ access_token: string; role: string; full_name: string; user_id: number }>("/api/v1/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      setSession(s);
      const home =
        s.role === "field_officer" ? "/app/inspections" : s.role === "auditor" ? "/app/anomalies" : s.role === "agri_officer" ? "/app/claims" : "/app";
      window.location.href = home;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sign-in failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="login">
      <section className="login-visual">
        <div>
          <b style={{ letterSpacing: "0.18em", textTransform: "uppercase", color: "var(--accent)", fontSize: 12 }}>National disaster intelligence</b>
          <h1 style={{ marginTop: 18 }}>Evidence before money. Recovery after allocation.</h1>
          <p className="lede" style={{ color: "var(--text)" }}>
            Sentinel Recovery is a decision-support platform. Models produce risk scores, damage estimates, and verification recommendations.
            Authorised officials make every financial decision.
          </p>
        </div>
        <ol className="accounts" style={{ paddingLeft: 18 }}>
          <li>What was damaged?</li>
          <li>Does the report match evidence?</li>
          <li>Which cases need human verification?</li>
          <li>What happened after funds moved?</li>
          <li>Has the area recovered?</li>
        </ol>
      </section>
      <section className="login-form">
        <h2>Official sign-in</h2>
        <p className="lede">Use an authorised departmental account. All access is audited.</p>
        <form onSubmit={onSubmit} className="panel" style={{ display: "grid", gap: 14 }}>
          <label className="field">
            Official email
            <input type="email" autoComplete="username" value={email} onChange={(e) => setEmail(e.target.value)} required />
          </label>
          <label className="field">
            Password
            <input type="password" autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} required minLength={8} />
          </label>
          {error ? <div className="error">{error}</div> : null}
          <button className="btn" disabled={loading} type="submit">
            {loading ? "Checking credentials…" : "Enter workspace"}
          </button>
        </form>
        <p className="hint">Demonstration accounts (change passwords in production)</p>
        <div className="accounts">
          gov@sentinel.gov · ChangeMe!Gov12 — {ROLE_LABEL.gov_admin}
          <br />
          field@sentinel.gov · ChangeMe!Field12 — field
          <br />
          agri@sentinel.gov · ChangeMe!Agri12 — agriculture
          <br />
          audit@sentinel.gov · ChangeMe!Audit12 — auditor
          <br />
          admin@sentinel.gov · ChangeMe!Admin12 — system
        </div>
      </section>
    </div>
  );
}
