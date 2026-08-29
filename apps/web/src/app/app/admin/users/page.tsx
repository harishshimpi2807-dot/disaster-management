"use client";

import { FormEvent, useEffect, useState } from "react";
import { Empty, PageHead, Pill } from "@/components/ui";
import { api } from "@/lib/api";
import { ROLE_LABEL } from "@/lib/nav";

type User = { id: number; email: string; full_name: string; role: string; agency: string; is_active: boolean };

export default function UsersPage() {
  const [rows, setRows] = useState<User[] | null>(null);
  const [err, setErr] = useState("");
  const [form, setForm] = useState({ email: "", full_name: "", password: "", role: "field_officer", agency: "" });

  function load() {
    api<User[]>("/api/v1/users").then(setRows).catch((e) => setErr(e.message));
  }
  useEffect(() => {
    load();
  }, []);

  async function create(e: FormEvent) {
    e.preventDefault();
    try {
      await api("/api/v1/users", { method: "POST", body: JSON.stringify(form) });
      setForm({ email: "", full_name: "", password: "", role: "field_officer", agency: "" });
      load();
    } catch (ex) {
      setErr(ex instanceof Error ? ex.message : "Create failed");
    }
  }

  return (
    <div className="page">
      <PageHead title="Users and roles" lede="Least-privilege accounts. Password changes and role updates are written to the audit log." />
      <form className="panel" onSubmit={create} style={{ marginBottom: 16 }}>
        <div className="row">
          <label className="field">
            Name
            <input required value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} />
          </label>
          <label className="field">
            Email
            <input type="email" required value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
          </label>
          <label className="field">
            Password
            <input type="password" required minLength={10} value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} />
          </label>
          <label className="field">
            Role
            <select value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}>
              {Object.keys(ROLE_LABEL).map((r) => (
                <option key={r} value={r}>
                  {ROLE_LABEL[r]}
                </option>
              ))}
            </select>
          </label>
          <button className="btn">Create user</button>
        </div>
      </form>
      {err ? <div className="error">{err}</div> : null}
      {!rows ? (
        <div className="loading">Loading users…</div>
      ) : rows.length === 0 ? (
        <Empty title="No users" body="Unexpected — seed should have created demonstration accounts." />
      ) : (
        <div className="panel" style={{ padding: 0 }}>
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>Email</th>
                <th>Role</th>
                <th>Agency</th>
                <th>Active</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.id}>
                  <td>{r.full_name}</td>
                  <td className="mono">{r.email}</td>
                  <td>{ROLE_LABEL[r.role]}</td>
                  <td>{r.agency}</td>
                  <td>
                    <Pill value={r.is_active ? "active" : "inactive"} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
