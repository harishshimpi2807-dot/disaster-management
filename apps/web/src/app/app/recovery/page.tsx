"use client";

import { FormEvent, useEffect, useState } from "react";
import { Empty, PageHead, Pill } from "@/components/ui";
import { api } from "@/lib/api";
import { fmtDate } from "@/lib/format";

type Row = {
  id: number;
  public_id: string;
  category: string;
  state: string;
  district: string;
  locality: string;
  recovery_pct: number;
  recovery_score: number;
  status: string;
  phase?: string;
  observed_on: string;
};
type Alert = { public_id: string; category: string; locality: string; recovery_pct: number; phase: string };
type Disaster = { id: number; name: string };

export default function RecoveryPage() {
  const [rows, setRows] = useState<Row[] | null>(null);
  const [disasters, setDisasters] = useState<Disaster[]>([]);
  const [filters, setFilters] = useState({ disaster_id: "", state: "", status: "" });
  const [err, setErr] = useState("");
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [form, setForm] = useState({
    disaster_id: "",
    category: "roads",
    state: "",
    district: "",
    locality: "",
    recovery_pct: "40",
    status: "underway",
    phase: "month_1",
    observed_on: "",
    notes: "",
  });

  function load() {
    const p = new URLSearchParams();
    if (filters.disaster_id) p.set("disaster_id", filters.disaster_id);
    if (filters.state) p.set("state", filters.state);
    if (filters.status) p.set("status", filters.status);
    api<Row[]>(`/api/v1/recovery?${p}`).then(setRows).catch((e) => setErr(e.message));
    api<Alert[]>("/api/v1/recovery/alerts/delayed").then(setAlerts).catch(() => setAlerts([]));
  }
  useEffect(() => {
    load();
    api<Disaster[]>("/api/v1/disasters").then(setDisasters);
  }, []);

  async function create(e: FormEvent) {
    e.preventDefault();
    try {
      await api("/api/v1/recovery", {
        method: "POST",
        body: JSON.stringify({ ...form, disaster_id: Number(form.disaster_id), recovery_pct: Number(form.recovery_pct) }),
      });
      load();
    } catch (ex) {
      setErr(ex instanceof Error ? ex.message : "Save failed");
    }
  }

  return (
    <div className="page">
      <PageHead title="Post-disaster recovery" lede="Track locations from pre-disaster baseline → post-disaster → 1 / 3 / 6 months → current." />
      {alerts.length ? (
        <div className="panel" style={{ marginBottom: 16, borderColor: "var(--critical)" }}>
          <h2>Delayed recovery alerts</h2>
          {alerts.map((a) => (
            <p key={a.public_id}>
              {a.public_id} · {a.category} · {a.locality} · {a.recovery_pct}% ({a.phase})
            </p>
          ))}
        </div>
      ) : null}
      <div className="row" style={{ marginBottom: 12 }}>
        <label className="field">
          Disaster
          <select value={filters.disaster_id} onChange={(e) => setFilters({ ...filters, disaster_id: e.target.value })}>
            <option value="">All</option>
            {disasters.map((d) => (
              <option key={d.id} value={d.id}>
                {d.name}
              </option>
            ))}
          </select>
        </label>
        <label className="field">
          State
          <input value={filters.state} onChange={(e) => setFilters({ ...filters, state: e.target.value })} />
        </label>
        <label className="field">
          Status
          <select value={filters.status} onChange={(e) => setFilters({ ...filters, status: e.target.value })}>
            <option value="">All</option>
            {["not_started", "early", "underway", "advanced", "restored", "delayed"].map((s) => (
              <option key={s}>{s}</option>
            ))}
          </select>
        </label>
        <button className="btn ghost" onClick={load}>
          Filter
        </button>
      </div>
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
            Category
            <select value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })}>
              {["buildings", "roads", "agricultural_fields", "infrastructure", "vegetation", "flooded_areas"].map((c) => (
                <option key={c}>{c}</option>
              ))}
            </select>
          </label>
          <label className="field">
            State
            <input required value={form.state} onChange={(e) => setForm({ ...form, state: e.target.value })} />
          </label>
          <label className="field">
            District
            <input required value={form.district} onChange={(e) => setForm({ ...form, district: e.target.value })} />
          </label>
          <label className="field">
            Phase
            <select value={form.phase} onChange={(e) => setForm({ ...form, phase: e.target.value })}>
              {["pre_disaster", "post_disaster", "month_1", "month_3", "month_6", "current"].map((p) => (
                <option key={p}>{p}</option>
              ))}
            </select>
          </label>
          <label className="field">
            Recovery %
            <input type="number" min={0} max={100} value={form.recovery_pct} onChange={(e) => setForm({ ...form, recovery_pct: e.target.value })} />
          </label>
          <label className="field">
            Observed on
            <input type="date" required value={form.observed_on} onChange={(e) => setForm({ ...form, observed_on: e.target.value })} />
          </label>
          <button className="btn">Add observation</button>
        </div>
      </form>
      {err ? <div className="error">{err}</div> : null}
      {!rows ? (
        <div className="loading">Loading recovery series…</div>
      ) : rows.length === 0 ? (
        <Empty title="No recovery observations" body="Add a dated observation for a location and damage category." />
      ) : (
        <div className="panel" style={{ padding: 0 }}>
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Place</th>
                <th>Category</th>
                <th>%</th>
                <th>Score</th>
                <th>Phase</th>
                <th>Status</th>
                <th>Date</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.id}>
                  <td className="mono">{r.public_id}</td>
                  <td>
                    {r.locality || r.district}, {r.state}
                  </td>
                  <td>{r.category}</td>
                  <td className="mono">{r.recovery_pct}</td>
                  <td className="mono">{r.recovery_score}</td>
                  <td className="mono">{r.phase || "—"}</td>
                  <td>
                    <Pill value={r.status} />
                  </td>
                  <td>{fmtDate(r.observed_on)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
