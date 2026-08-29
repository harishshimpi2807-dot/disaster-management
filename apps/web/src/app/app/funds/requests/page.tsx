"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { Empty, PageHead, Pill } from "@/components/ui";
import { api } from "@/lib/api";
import { money } from "@/lib/format";

type Row = {
  id: number;
  public_id: string;
  department: string;
  location_label: string;
  requested_amount: number;
  evidence_consistency: number | null;
  confidence: number | null;
  status: string;
  recommendation: string;
};
type Disaster = { id: number; name: string };

export default function FundRequests() {
  const [rows, setRows] = useState<Row[] | null>(null);
  const [disasters, setDisasters] = useState<Disaster[]>([]);
  const [err, setErr] = useState("");
  const [form, setForm] = useState({
    disaster_id: "",
    department: "",
    location_label: "",
    damage_category: "roads",
    reported_damage: "",
    requested_amount: "",
  });

  function load() {
    api<Row[]>("/api/v1/fund-requests").then(setRows).catch((e) => setErr(e.message));
  }
  useEffect(() => {
    load();
    api<Disaster[]>("/api/v1/disasters").then(setDisasters);
  }, []);

  async function create(e: FormEvent) {
    e.preventDefault();
    try {
      await api("/api/v1/fund-requests", {
        method: "POST",
        body: JSON.stringify({ ...form, disaster_id: Number(form.disaster_id), requested_amount: Number(form.requested_amount) }),
      });
      load();
    } catch (ex) {
      setErr(ex instanceof Error ? ex.message : "Save failed");
    }
  }

  return (
    <div className="page">
      <PageHead title="Fund requirements" lede="Compare departmental requests with geospatial evidence. The platform never releases or denies funds." />
      <form className="panel" onSubmit={create} style={{ marginBottom: 16 }}>
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
            Department
            <input required value={form.department} onChange={(e) => setForm({ ...form, department: e.target.value })} />
          </label>
          <label className="field">
            Location
            <input required value={form.location_label} onChange={(e) => setForm({ ...form, location_label: e.target.value })} />
          </label>
          <label className="field">
            Category
            <select value={form.damage_category} onChange={(e) => setForm({ ...form, damage_category: e.target.value })}>
              {["buildings", "roads", "agricultural_fields", "infrastructure", "flooded_areas", "vegetation", "critical_facilities"].map((c) => (
                <option key={c}>{c}</option>
              ))}
            </select>
          </label>
          <label className="field">
            Amount (INR)
            <input type="number" min={1} required value={form.requested_amount} onChange={(e) => setForm({ ...form, requested_amount: e.target.value })} />
          </label>
        </div>
        <label className="field">
          Reported damage
          <textarea required value={form.reported_damage} onChange={(e) => setForm({ ...form, reported_damage: e.target.value })} />
        </label>
        <button className="btn">Submit requirement</button>
      </form>
      {err ? <div className="error">{err}</div> : null}
      {!rows ? (
        <div className="loading">Loading…</div>
      ) : rows.length === 0 ? (
        <Empty title="No fund requirements" body="Submit a departmental requirement to generate an evidence-consistency score." />
      ) : (
        <div className="panel" style={{ padding: 0 }}>
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Department</th>
                <th>Amount</th>
                <th>Consistency</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.id}>
                  <td className="mono">
                    <Link href={`/app/funds/requests/${r.id}`}>{r.public_id}</Link>
                  </td>
                  <td>
                    {r.department}
                    <div style={{ color: "var(--muted)", fontSize: 12 }}>{r.location_label}</div>
                  </td>
                  <td className="mono">{money(r.requested_amount)}</td>
                  <td className="mono">{r.evidence_consistency ?? "—"}</td>
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
