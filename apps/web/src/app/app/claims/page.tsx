"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { Empty, PageHead, Pill } from "@/components/ui";
import { api } from "@/lib/api";

type Claim = {
  id: number;
  public_id: string;
  farmer_reference: string;
  crop_type: string;
  reported_damage_pct: number;
  estimated_damage_pct: number | null;
  difference_pct: number | null;
  confidence: number | null;
  status: string;
  recommendation: string;
};
type Disaster = { id: number; name: string };

export default function ClaimsPage() {
  const [rows, setRows] = useState<Claim[] | null>(null);
  const [disasters, setDisasters] = useState<Disaster[]>([]);
  const [q, setQ] = useState("");
  const [err, setErr] = useState("");
  const [form, setForm] = useState({
    disaster_id: "",
    farmer_reference: "",
    crop_type: "Paddy",
    incident_date: "",
    reported_damage_pct: "40",
  });

  function load() {
    const p = q ? `?q=${encodeURIComponent(q)}` : "";
    api<Claim[]>(`/api/v1/claims${p}`).then(setRows).catch((e) => setErr(e.message));
  }

  useEffect(() => {
    load();
    api<Disaster[]>("/api/v1/disasters").then(setDisasters);
  }, []);

  async function create(e: FormEvent) {
    e.preventDefault();
    try {
      await api("/api/v1/claims", {
        method: "POST",
        body: JSON.stringify({
          disaster_id: Number(form.disaster_id),
          farmer_reference: form.farmer_reference,
          crop_type: form.crop_type,
          incident_date: form.incident_date,
          reported_damage_pct: Number(form.reported_damage_pct),
          field_boundary: {
            type: "Polygon",
            coordinates: [
              [
                [73.49, 17.51],
                [73.52, 17.51],
                [73.52, 17.54],
                [73.49, 17.54],
                [73.49, 17.51],
              ],
            ],
          },
        }),
      });
      load();
    } catch (ex) {
      setErr(ex instanceof Error ? ex.message : "Create failed");
    }
  }

  return (
    <div className="page">
      <PageHead
        title="Crop-loss cases"
        lede="Compare reported loss with the remote-sensing estimate. Statuses describe consistency — they are not insurance decisions."
      />
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
            Farmer / case ref
            <input required value={form.farmer_reference} onChange={(e) => setForm({ ...form, farmer_reference: e.target.value })} />
          </label>
          <label className="field">
            Crop
            <input required value={form.crop_type} onChange={(e) => setForm({ ...form, crop_type: e.target.value })} />
          </label>
          <label className="field">
            Incident date
            <input type="date" required value={form.incident_date} onChange={(e) => setForm({ ...form, incident_date: e.target.value })} />
          </label>
          <label className="field">
            Reported damage %
            <input type="number" min={0} max={100} required value={form.reported_damage_pct} onChange={(e) => setForm({ ...form, reported_damage_pct: e.target.value })} />
          </label>
          <button className="btn">Create case</button>
        </div>
      </form>
      <div className="row" style={{ marginBottom: 12 }}>
        <label className="field">
          Search reference
          <input value={q} onChange={(e) => setQ(e.target.value)} />
        </label>
        <button className="btn ghost" onClick={load}>
          Search
        </button>
      </div>
      {err ? <div className="error">{err}</div> : null}
      {!rows ? (
        <div className="loading">Loading cases…</div>
      ) : rows.length === 0 ? (
        <Empty title="No crop-loss cases" body="Create a case to compare reported and estimated damage." />
      ) : (
        <div className="panel" style={{ padding: 0 }}>
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Reference</th>
                <th>Crop</th>
                <th>Reported</th>
                <th>Estimated</th>
                <th>Δ</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.id}>
                  <td className="mono">
                    <Link href={`/app/claims/${r.id}`}>{r.public_id}</Link>
                  </td>
                  <td>{r.farmer_reference}</td>
                  <td>{r.crop_type}</td>
                  <td className="mono">{r.reported_damage_pct}%</td>
                  <td className="mono">{r.estimated_damage_pct ?? "—"}%</td>
                  <td className="mono">{r.difference_pct ?? "—"}</td>
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
