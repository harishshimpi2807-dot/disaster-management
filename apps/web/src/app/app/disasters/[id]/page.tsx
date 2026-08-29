"use client";

import Link from "next/link";
import dynamic from "next/dynamic";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { PageHead, Pill } from "@/components/ui";
import { api } from "@/lib/api";
import { fmtDate, money } from "@/lib/format";

const MiniMap = dynamic(() => import("@/components/MiniMap"), { ssr: false });

type Dossier = {
  disaster: {
    id: number;
    public_id: string;
    name: string;
    disaster_type: string;
    start_date: string;
    end_date?: string;
    state: string;
    district: string;
    locality: string;
    severity: string;
    status: string;
    description: string;
    boundary?: GeoJSON.Polygon;
  };
  assessments: { id: number; public_id: string; category: string; severity: string; estimated_area_ha: number; confidence: number }[];
  claims: { id: number; public_id: string; status: string; reported_damage_pct: number; estimated_damage_pct: number }[];
  fund_requests: { id: number; public_id: string; department: string; requested_amount: number; status: string }[];
  allocations: { id: number; public_id: string; purpose: string; status: string; observed_progress_pct: number; planned_progress_pct: number }[];
  recovery: { id: number; public_id: string; category: string; phase: string; recovery_pct: number; status: string }[];
  inspections: { id: number; public_id: string; status: string; case_type: string }[];
  anomalies: { id: number; public_id: string; risk_level: string; risk_score: number }[];
  imagery: { id: number; phase: string; filename: string }[];
};

export default function DisasterDetail() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [data, setData] = useState<Dossier | null>(null);
  const [err, setErr] = useState("");
  const [desc, setDesc] = useState("");

  function load() {
    api<Dossier>(`/api/v1/disasters/${id}/dossier`)
      .then((d) => {
        setData(d);
        setDesc(d.disaster.description);
      })
      .catch((e) => setErr(e.message));
  }
  useEffect(() => {
    load();
  }, [id]);

  async function save() {
    if (!data) return;
    const d = data.disaster;
    try {
      await api(`/api/v1/disasters/${id}`, {
        method: "PATCH",
        body: JSON.stringify({
          name: d.name,
          disaster_type: d.disaster_type,
          start_date: d.start_date,
          end_date: d.end_date || null,
          state: d.state,
          district: d.district,
          locality: d.locality,
          severity: d.severity,
          description: desc,
          status: d.status,
          boundary: d.boundary,
        }),
      });
      load();
    } catch (ex) {
      setErr(ex instanceof Error ? ex.message : "Save failed");
    }
  }

  async function archive() {
    if (!confirm("Archive this event? It remains in the audit trail but leaves the active list.")) return;
    await api(`/api/v1/disasters/${id}`, { method: "DELETE" });
    router.push("/app/disasters");
  }

  if (err && !data) return <div className="page"><div className="error">{err}</div></div>;
  if (!data) return <div className="page"><div className="loading">Loading event dossier…</div></div>;
  const d = data.disaster;

  return (
    <div className="page">
      <PageHead
        title={d.name}
        lede={`${d.public_id} · ${d.district}, ${d.state}`}
        actions={
          <div className="row">
            <Link className="btn" href="/app/map">
              Open GIS
            </Link>
            <button className="btn danger" onClick={archive}>
              Archive event
            </button>
          </div>
        }
      />
      {err ? <div className="error">{err}</div> : null}
      <div className="grid-2">
        <div className="panel">
          <p>
            <Pill value={d.disaster_type} /> <Pill value={d.severity} /> <Pill value={d.status} />
          </p>
          <p className="mono" style={{ color: "var(--muted)" }}>
            {fmtDate(d.start_date)} — {d.end_date ? fmtDate(d.end_date) : "ongoing"} · {d.locality}
          </p>
          <label className="field">
            Narrative
            <textarea value={desc} onChange={(e) => setDesc(e.target.value)} />
          </label>
          <button className="btn" onClick={save}>
            Save description
          </button>
        </div>
        <div className="panel" style={{ padding: 0 }}>
          <MiniMap geojson={d.boundary || null} />
        </div>
      </div>
      <Section title="Damage assessments" empty="No assessments. Run analysis from Damage assessment.">
        {data.assessments.map((a) => (
          <tr key={a.id}>
            <td className="mono">{a.public_id}</td>
            <td>{a.category}</td>
            <td>
              <Pill value={a.severity} />
            </td>
            <td className="mono">{a.estimated_area_ha} ha</td>
          </tr>
        ))}
      </Section>
      <Section title="Crop-loss cases" empty="No claims linked.">
        {data.claims.map((c) => (
          <tr key={c.id}>
            <td className="mono">
              <Link href={`/app/claims/${c.id}`}>{c.public_id}</Link>
            </td>
            <td>
              <Pill value={c.status} />
            </td>
            <td className="mono">
              {c.reported_damage_pct}% / {c.estimated_damage_pct}%
            </td>
          </tr>
        ))}
      </Section>
      <Section title="Fund requirements" empty="No fund requirements.">
        {data.fund_requests.map((f) => (
          <tr key={f.id}>
            <td className="mono">
              <Link href={`/app/funds/requests/${f.id}`}>{f.public_id}</Link>
            </td>
            <td>{f.department}</td>
            <td className="mono">{money(f.requested_amount)}</td>
            <td>
              <Pill value={f.status} />
            </td>
          </tr>
        ))}
      </Section>
      <div className="grid-2">
        <Section title="Inspections" empty="None assigned.">
          {data.inspections.map((i) => (
            <tr key={i.id}>
              <td className="mono">
                <Link href={`/app/inspections/${i.id}`}>{i.public_id}</Link>
              </td>
              <td>
                <Pill value={i.status} />
              </td>
            </tr>
          ))}
        </Section>
        <Section title="Anomaly risk" empty="No alerts.">
          {data.anomalies.map((a) => (
            <tr key={a.id}>
              <td className="mono">{a.public_id}</td>
              <td>
                <Pill value={a.risk_level} />
              </td>
              <td className="mono">{a.risk_score}</td>
            </tr>
          ))}
        </Section>
      </div>
    </div>
  );
}

function Section({ title, empty, children }: { title: string; empty: string; children: React.ReactNode }) {
  const rows = Array.isArray(children) ? children : [children];
  const has = rows.filter(Boolean).length > 0;
  return (
    <div className="panel" style={{ padding: 0, marginTop: 12 }}>
      <h2 style={{ padding: "14px 16px 0" }}>{title}</h2>
      {has ? (
        <table>
          <tbody>{children}</tbody>
        </table>
      ) : (
        <p className="lede" style={{ padding: 16 }}>
          {empty}
        </p>
      )}
    </div>
  );
}
