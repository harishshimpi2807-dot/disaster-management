"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { Empty, PageHead, Pill } from "@/components/ui";
import { api, getSession } from "@/lib/api";

type Row = {
  id: number;
  public_id: string;
  case_type: string;
  case_id: number;
  status: string;
  required_actions: string;
  assigned_to_id: number;
};
type User = { id: number; full_name: string; role: string };
type Disaster = { id: number; name: string };
type Claim = { id: number; public_id: string };

export default function InspectionsPage() {
  const [rows, setRows] = useState<Row[] | null>(null);
  const [users, setUsers] = useState<User[]>([]);
  const [disasters, setDisasters] = useState<Disaster[]>([]);
  const [claims, setClaims] = useState<Claim[]>([]);
  const [err, setErr] = useState("");
  const role = getSession()?.role;
  const [form, setForm] = useState({ disaster_id: "", case_id: "", assigned_to_id: "", required_actions: "Photograph site, confirm boundary, record verified damage." });

  function load() {
    api<Row[]>("/api/v1/inspections").then(setRows).catch((e) => setErr(e.message));
  }
  useEffect(() => {
    load();
    api<Disaster[]>("/api/v1/disasters").then(setDisasters);
    api<Claim[]>("/api/v1/claims").then(setClaims);
    api<User[]>("/api/v1/users").then(setUsers).catch(() => setUsers([]));
  }, []);

  async function assign(e: FormEvent) {
    e.preventDefault();
    try {
      await api("/api/v1/inspections", {
        method: "POST",
        body: JSON.stringify({
          disaster_id: Number(form.disaster_id),
          case_type: "claim",
          case_id: Number(form.case_id),
          assigned_to_id: Number(form.assigned_to_id),
          required_actions: form.required_actions,
          location: { type: "Point", coordinates: [73.5, 17.52] },
        }),
      });
      load();
    } catch (ex) {
      setErr(ex instanceof Error ? ex.message : "Assign failed");
    }
  }

  const officers = users.filter((u) => u.role === "field_officer");

  return (
    <div className="page">
      <PageHead title="Field verification" lede="Assigned inspections with maps, reported vs estimated damage, anomaly risk, and potential-duplicate warnings." />
      {role !== "field_officer" ? (
        <form className="panel" onSubmit={assign} style={{ marginBottom: 16 }}>
          <div className="row">
            <label className="field">
              Disaster
              <select required value={form.disaster_id} onChange={(e) => setForm({ ...form, disaster_id: e.target.value })}>
                <option value="">Select</option>
                {disasters.map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.name}
                  </option>
                ))}
              </select>
            </label>
            <label className="field">
              Crop-loss case
              <select required value={form.case_id} onChange={(e) => setForm({ ...form, case_id: e.target.value })}>
                <option value="">Select</option>
                {claims.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.public_id}
                  </option>
                ))}
              </select>
            </label>
            <label className="field">
              Field officer
              <select required value={form.assigned_to_id} onChange={(e) => setForm({ ...form, assigned_to_id: e.target.value })}>
                <option value="">Select</option>
                {officers.map((u) => (
                  <option key={u.id} value={u.id}>
                    {u.full_name}
                  </option>
                ))}
              </select>
            </label>
            <button className="btn">Assign inspection</button>
          </div>
        </form>
      ) : null}
      {err ? <div className="error">{err}</div> : null}
      {!rows ? (
        <div className="loading">Loading inspections…</div>
      ) : rows.length === 0 ? (
        <Empty title="No inspections" body="Government or agricultural officers assign field verification from this screen." />
      ) : (
        <div className="panel" style={{ padding: 0 }}>
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Case</th>
                <th>Actions</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.id}>
                  <td className="mono">
                    <Link href={`/app/inspections/${r.id}`}>{r.public_id}</Link>
                  </td>
                  <td>
                    {r.case_type} #{r.case_id}
                  </td>
                  <td>{r.required_actions}</td>
                  <td>
                    <Pill value={r.status} />
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
