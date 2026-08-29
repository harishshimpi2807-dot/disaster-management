"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { PageHead } from "@/components/ui";
import { api } from "@/lib/api";

const box = {
  type: "Polygon",
  coordinates: [
    [
      [73.4, 17.4],
      [73.7, 17.4],
      [73.7, 17.7],
      [73.4, 17.7],
      [73.4, 17.4],
    ],
  ],
};

export default function NewDisaster() {
  const router = useRouter();
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({
    name: "",
    disaster_type: "flood",
    start_date: "",
    end_date: "",
    state: "",
    district: "",
    locality: "",
    severity: "moderate",
    description: "",
    status: "active",
  });

  function set<K extends keyof typeof form>(k: K, v: string) {
    setForm((s) => ({ ...s, [k]: v }));
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setErr("");
    try {
      const created = await api<{ id: number }>("/api/v1/disasters", {
        method: "POST",
        body: JSON.stringify({ ...form, end_date: form.end_date || null, boundary: box }),
      });
      router.push(`/app/disasters/${created.id}`);
    } catch (ex) {
      setErr(ex instanceof Error ? ex.message : "Save failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="page">
      <PageHead title="Register disaster event" lede="A default bounding polygon is stored so the GIS layer has an affected area. Edit coordinates in GIS workflows later." />
      <form className="panel" onSubmit={onSubmit} style={{ display: "grid", gap: 12, maxWidth: 840 }}>
        <div className="grid-2">
          <label className="field">
            Name
            <input required value={form.name} onChange={(e) => set("name", e.target.value)} />
          </label>
          <label className="field">
            Type
            <select value={form.disaster_type} onChange={(e) => set("disaster_type", e.target.value)}>
              {["flood", "cyclone", "landslide", "drought", "earthquake", "wildfire", "other"].map((t) => (
                <option key={t}>{t}</option>
              ))}
            </select>
          </label>
          <label className="field">
            Start date
            <input type="date" required value={form.start_date} onChange={(e) => set("start_date", e.target.value)} />
          </label>
          <label className="field">
            End date
            <input type="date" value={form.end_date} onChange={(e) => set("end_date", e.target.value)} />
          </label>
          <label className="field">
            State
            <input required value={form.state} onChange={(e) => set("state", e.target.value)} />
          </label>
          <label className="field">
            District
            <input required value={form.district} onChange={(e) => set("district", e.target.value)} />
          </label>
          <label className="field">
            Village / locality
            <input value={form.locality} onChange={(e) => set("locality", e.target.value)} />
          </label>
          <label className="field">
            Severity
            <select value={form.severity} onChange={(e) => set("severity", e.target.value)}>
              {["minor", "moderate", "severe", "catastrophic"].map((t) => (
                <option key={t}>{t}</option>
              ))}
            </select>
          </label>
        </div>
        <label className="field">
          Description
          <textarea value={form.description} onChange={(e) => set("description", e.target.value)} />
        </label>
        {err ? <div className="error">{err}</div> : null}
        <button className="btn" disabled={loading}>
          {loading ? "Saving…" : "Create event"}
        </button>
      </form>
    </div>
  );
}
