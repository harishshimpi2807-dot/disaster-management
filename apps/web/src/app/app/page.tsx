"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Empty, PageHead } from "@/components/ui";
import { api } from "@/lib/api";
import { money } from "@/lib/format";

type Overview = {
  total_disasters: number;
  total_affected_area_ha: number;
  estimated_damage_records: number;
  claims_requiring_verification: number;
  high_risk_anomalies: number;
  potential_duplicates: number;
  funds_requested: number;
  funds_allocated?: number;
  funds_monitored: number;
  recovery_percentage: number;
  delayed_recovery_locations: number;
  delayed_allocations: number;
  disasters_by_type: Record<string, number>;
  timeline: { date: string; name: string; severity: string; type: string }[];
  recovery_by_category: Record<string, number>;
  anomaly_by_level: Record<string, number>;
};

export default function OverviewPage() {
  const [data, setData] = useState<Overview | null>(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    api<Overview>("/api/v1/analytics/overview").then(setData).catch((e) => setErr(e.message));
  }, []);

  if (err) return <div className="page"><div className="error">{err}</div></div>;
  if (!data) return <div className="page"><div className="loading">Loading operational picture…</div></div>;

  const kpis = [
    { k: "Active disaster events", v: data.total_disasters, h: "Registered in the system" },
    { k: "Estimated affected area", v: `${data.total_affected_area_ha} ha`, h: "From damage assessments" },
    { k: "Cases needing verification", v: data.claims_requiring_verification, h: "Human review required" },
    { k: "High / critical anomaly risk", v: data.high_risk_anomalies, h: "Not a finding of fraud" },
    { k: "Potential duplicates", v: data.potential_duplicates, h: "Same location / asset / event" },
    { k: "Funds requested", v: money(data.funds_requested), h: "Departmental requirements" },
    { k: "Funds allocated", v: money(data.funds_allocated ?? data.funds_monitored), h: "Released to implementing agencies" },
    { k: "Funds under monitoring", v: money(data.funds_monitored), h: "Tracked interventions" },
    { k: "Mean recovery", v: `${data.recovery_percentage}%`, h: "Observed vs pre-disaster" },
    { k: "Delayed recovery sites", v: data.delayed_recovery_locations, h: "Behind expected trajectory" },
    { k: "Delayed allocations", v: data.delayed_allocations, h: "Observed < planned progress" },
  ];

  return (
    <div className="page">
      <PageHead
        title="Operational picture"
        lede="Five questions: damage, evidence fit, verification queue, utilisation after allocation, and actual recovery. Models recommend; officials decide."
        actions={
          <Link className="btn" href="/app/map">
            Open GIS
          </Link>
        }
      />
      <div className="kpis">
        {kpis.map((x) => (
          <div className="kpi" key={x.k}>
            <div className="k">{x.k}</div>
            <div className="v">{x.v}</div>
            <div className="h">{x.h}</div>
          </div>
        ))}
      </div>
      <div className="grid-3">
        <div className="panel">
          <h2>Disaster timeline</h2>
          {data.timeline.length === 0 ? (
            <Empty title="No events" body="Create a disaster event to begin the lifecycle." />
          ) : (
            <table>
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Event</th>
                  <th>Type</th>
                  <th>Severity</th>
                </tr>
              </thead>
              <tbody>
                {data.timeline.map((t) => (
                  <tr key={t.name + t.date}>
                    <td className="mono">{t.date}</td>
                    <td>{t.name}</td>
                    <td>{t.type}</td>
                    <td>{t.severity}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
        <div>
          <div className="panel">
            <h2>Anomaly risk mix</h2>
            <BarMap data={data.anomaly_by_level} />
          </div>
          <div className="panel">
            <h2>Recovery by category</h2>
            <BarMap data={data.recovery_by_category} suffix="%" />
          </div>
        </div>
      </div>
    </div>
  );
}

function BarMap({ data, suffix = "" }: { data: Record<string, number>; suffix?: string }) {
  const max = Math.max(1, ...Object.values(data));
  const entries = Object.entries(data);
  if (!entries.length) return <Empty title="Nothing to chart" body="Records will appear as cases move through the workflow." />;
  return (
    <div style={{ display: "grid", gap: 10, marginTop: 12 }}>
      {entries.map(([k, v]) => (
        <div key={k}>
          <div style={{ display: "flex", justifyContent: "space-between", fontSize: 13, color: "var(--muted)" }}>
            <span>{k}</span>
            <span className="mono">
              {v}
              {suffix}
            </span>
          </div>
          <div style={{ height: 8, background: "var(--bg)", marginTop: 4 }}>
            <div style={{ width: `${(v / max) * 100}%`, height: "100%", background: "var(--accent)" }} />
          </div>
        </div>
      ))}
    </div>
  );
}
