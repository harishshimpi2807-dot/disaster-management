"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Empty, PageHead, Pill } from "@/components/ui";
import { api } from "@/lib/api";
import { fmtDate } from "@/lib/format";

type Disaster = {
  id: number;
  public_id: string;
  name: string;
  disaster_type: string;
  start_date: string;
  state: string;
  district: string;
  severity: string;
  status: string;
};

export default function DisastersPage() {
  const [rows, setRows] = useState<Disaster[] | null>(null);
  const [q, setQ] = useState("");
  const [type, setType] = useState("");
  const [err, setErr] = useState("");

  function load() {
    const p = new URLSearchParams();
    if (q) p.set("q", q);
    if (type) p.set("disaster_type", type);
    api<Disaster[]>(`/api/v1/disasters?${p}`)
      .then(setRows)
      .catch((e) => setErr(e.message));
  }

  useEffect(() => {
    load();
  }, []);

  return (
    <div className="page">
      <PageHead
        title="Disaster events"
        lede="Register events, draw affected-area polygons, and track status from draft through monitoring."
        actions={
          <Link className="btn" href="/app/disasters/new">
            Register event
          </Link>
        }
      />
      <div className="row" style={{ marginBottom: 16 }}>
        <label className="field">
          Search
          <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Name, ID, district" />
        </label>
        <label className="field">
          Type
          <select value={type} onChange={(e) => setType(e.target.value)}>
            <option value="">All</option>
            {["flood", "cyclone", "landslide", "drought", "earthquake", "wildfire", "other"].map((t) => (
              <option key={t}>{t}</option>
            ))}
          </select>
        </label>
        <button className="btn ghost" onClick={load}>
          Filter
        </button>
      </div>
      {err ? <div className="error">{err}</div> : null}
      {!rows ? (
        <div className="loading">Loading events…</div>
      ) : rows.length === 0 ? (
        <Empty title="No matching events" body="Adjust filters or register a disaster event." />
      ) : (
        <div className="panel" style={{ padding: 0 }}>
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Name</th>
                <th>Type</th>
                <th>Region</th>
                <th>Start</th>
                <th>Severity</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.id}>
                  <td className="mono">
                    <Link href={`/app/disasters/${r.id}`}>{r.public_id}</Link>
                  </td>
                  <td>
                    <Link href={`/app/disasters/${r.id}`}>{r.name}</Link>
                  </td>
                  <td>{r.disaster_type}</td>
                  <td>
                    {r.district}, {r.state}
                  </td>
                  <td>{fmtDate(r.start_date)}</td>
                  <td>
                    <Pill value={r.severity} />
                  </td>
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
