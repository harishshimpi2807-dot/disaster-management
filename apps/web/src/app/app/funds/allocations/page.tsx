"use client";

import { FormEvent, useEffect, useState } from "react";
import { Empty, PageHead, Pill } from "@/components/ui";
import { api } from "@/lib/api";
import { money } from "@/lib/format";

type Row = {
  id: number;
  public_id: string;
  purpose: string;
  amount: number;
  implementing_agency: string;
  status: string;
  planned_progress_pct: number;
  observed_progress_pct: number;
  location_label: string;
};
type Disaster = { id: number; name: string };

export default function Allocations() {
  const [rows, setRows] = useState<Row[] | null>(null);
  const [disasters, setDisasters] = useState<Disaster[]>([]);
  const [err, setErr] = useState("");
  const [form, setForm] = useState({
    disaster_id: "",
    purpose: "",
    amount: "",
    allocating_authority: "State Relief Commissioner",
    implementing_agency: "",
    location_label: "",
    allocated_on: "",
    expected_completion: "",
    planned_progress_pct: "40",
    observed_progress_pct: "10",
  });

  function load() {
    api<Row[]>("/api/v1/fund-allocations").then(setRows).catch((e) => setErr(e.message));
  }
  useEffect(() => {
    load();
    api<Disaster[]>("/api/v1/disasters").then(setDisasters);
  }, []);

  async function create(e: FormEvent) {
    e.preventDefault();
    try {
      await api("/api/v1/fund-allocations", {
        method: "POST",
        body: JSON.stringify({
          ...form,
          disaster_id: Number(form.disaster_id),
          amount: Number(form.amount),
          planned_progress_pct: Number(form.planned_progress_pct),
          observed_progress_pct: Number(form.observed_progress_pct),
          expected_completion: form.expected_completion || null,
        }),
      });
      load();
    } catch (ex) {
      setErr(ex instanceof Error ? ex.message : "Save failed");
    }
  }

  async function attach(id: number, file: File) {
    const fd = new FormData();
    fd.append("file", file);
    fd.append("entity_type", "allocation");
    fd.append("entity_id", String(id));
    await api("/api/v1/evidence", { method: "POST", body: fd });
  }

  return (
    <div className="page">
      <PageHead title="Fund utilisation" lede="Allocation → intervention → observed progress. Delayed alerts fire when observed progress lags the plan." />
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
            Purpose
            <input required value={form.purpose} onChange={(e) => setForm({ ...form, purpose: e.target.value })} />
          </label>
          <label className="field">
            Amount
            <input type="number" min={1} required value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })} />
          </label>
          <label className="field">
            Agency
            <input required value={form.implementing_agency} onChange={(e) => setForm({ ...form, implementing_agency: e.target.value })} />
          </label>
          <label className="field">
            Location
            <input required value={form.location_label} onChange={(e) => setForm({ ...form, location_label: e.target.value })} />
          </label>
          <label className="field">
            Allocated on
            <input type="date" required value={form.allocated_on} onChange={(e) => setForm({ ...form, allocated_on: e.target.value })} />
          </label>
          <label className="field">
            Planned %
            <input type="number" value={form.planned_progress_pct} onChange={(e) => setForm({ ...form, planned_progress_pct: e.target.value })} />
          </label>
          <label className="field">
            Observed %
            <input type="number" value={form.observed_progress_pct} onChange={(e) => setForm({ ...form, observed_progress_pct: e.target.value })} />
          </label>
          <button className="btn">Record allocation</button>
        </div>
      </form>
      {err ? <div className="error">{err}</div> : null}
      {!rows ? (
        <div className="loading">Loading…</div>
      ) : rows.length === 0 ? (
        <Empty title="No allocations" body="Record an allocation to start utilisation monitoring." />
      ) : (
        <div className="panel" style={{ padding: 0 }}>
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Purpose</th>
                <th>Amount</th>
                <th>Plan / observed</th>
                <th>Status</th>
                <th>Evidence</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.id}>
                  <td className="mono">{r.public_id}</td>
                  <td>
                    {r.purpose}
                    <div style={{ color: "var(--muted)", fontSize: 12 }}>{r.implementing_agency}</div>
                  </td>
                  <td className="mono">{money(r.amount)}</td>
                  <td className="mono">
                    {r.planned_progress_pct}% / {r.observed_progress_pct}%
                  </td>
                  <td>
                    <Pill value={r.status} />
                  </td>
                  <td>
                    <input type="file" accept="image/*,.pdf" aria-label={`Evidence for ${r.public_id}`} onChange={(e) => e.target.files?.[0] && attach(r.id, e.target.files[0])} />
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
