"use client";

import { useEffect, useState } from "react";
import { Empty, PageHead, Pill } from "@/components/ui";
import { api } from "@/lib/api";

type Alert = {
  id: number;
  public_id: string;
  entity_type: string;
  entity_id: number;
  risk_level: string;
  risk_score: number;
  reasons: string[];
  recommended_action: string;
  status: string;
};

export default function AnomaliesPage() {
  const [rows, setRows] = useState<Alert[] | null>(null);
  const [level, setLevel] = useState("");
  const [err, setErr] = useState("");

  function load() {
    const p = level ? `?risk_level=${level}` : "";
    api<Alert[]>(`/api/v1/anomalies${p}`).then(setRows).catch((e) => setErr(e.message));
  }
  useEffect(() => {
    load();
  }, []);

  async function mark(id: number) {
    await api(`/api/v1/anomalies/${id}?status=reviewed`, { method: "PATCH" });
    load();
  }

  return (
    <div className="page">
      <PageHead
        title="Anomaly risk centre"
        lede="Flags describe anomaly risk — unusual amounts, dates, locations, or evidence gaps. They never label a person or organisation as fraudulent."
      />
      <div className="row" style={{ marginBottom: 12 }}>
        <label className="field">
          Risk level
          <select value={level} onChange={(e) => setLevel(e.target.value)}>
            <option value="">All</option>
            {["low", "medium", "high", "critical"].map((x) => (
              <option key={x}>{x}</option>
            ))}
          </select>
        </label>
        <button className="btn ghost" onClick={load}>
          Filter
        </button>
      </div>
      {err ? <div className="error">{err}</div> : null}
      {!rows ? (
        <div className="loading">Loading alerts…</div>
      ) : rows.length === 0 ? (
        <Empty title="No anomaly-risk alerts" body="Alerts appear when claims or fund requirements diverge from evidence patterns." />
      ) : (
        <div style={{ display: "grid", gap: 12 }}>
          {rows.map((r) => (
            <article className="panel" key={r.id}>
              <div style={{ display: "flex", justifyContent: "space-between", gap: 12 }}>
                <div>
                  <div className="mono">{r.public_id}</div>
                  <h2 style={{ marginTop: 6 }}>
                    {r.entity_type} #{r.entity_id}
                  </h2>
                </div>
                <div>
                  <Pill value={r.risk_level} /> <span className="mono">{r.risk_score}</span>
                </div>
              </div>
              <ul>
                {r.reasons.map((x) => (
                  <li key={x}>{x}</li>
                ))}
              </ul>
              <p>{r.recommended_action}</p>
              {r.status === "open" ? (
                <button className="btn ghost" onClick={() => mark(r.id)}>
                  Mark reviewed
                </button>
              ) : (
                <span style={{ color: "var(--muted)" }}>Reviewed</span>
              )}
            </article>
          ))}
        </div>
      )}
    </div>
  );
}
