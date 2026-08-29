"use client";

import dynamic from "next/dynamic";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { PageHead, Pill } from "@/components/ui";
import { api } from "@/lib/api";

const MiniMap = dynamic(() => import("@/components/MiniMap"), { ssr: false });

type Claim = {
  id: number;
  public_id: string;
  disaster_id: number;
  farmer_reference: string;
  crop_type: string;
  reported_damage_pct: number;
  estimated_damage_pct: number | null;
  confidence: number | null;
  difference_pct: number | null;
  status: string;
  recommendation: string;
  incident_date: string;
  field_boundary?: GeoJSON.Polygon;
};
type Ev = { id: number; filename: string; latitude?: number; longitude?: number };

export default function ClaimDetail() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [row, setRow] = useState<Claim | null>(null);
  const [ev, setEv] = useState<Ev[]>([]);
  const [err, setErr] = useState("");
  const [msg, setMsg] = useState("");

  function load() {
    api<Claim>(`/api/v1/claims/${id}`).then(setRow).catch((e) => setErr(e.message));
    api<Ev[]>(`/api/v1/evidence?entity_type=claim&entity_id=${id}`).then(setEv).catch(() => setEv([]));
  }
  useEffect(() => {
    load();
  }, [id]);

  async function requestVerify() {
    try {
      const r = await api<{ inspection_id: number; public_id: string }>(`/api/v1/claims/${id}/request-verification`, { method: "POST" });
      setMsg(`Inspection ${r.public_id} assigned. This is not an insurance decision.`);
      router.push(`/app/inspections/${r.inspection_id}`);
    } catch (ex) {
      setErr(ex instanceof Error ? ex.message : "Request failed");
    }
  }

  async function upload(file: File) {
    const fd = new FormData();
    fd.append("file", file);
    fd.append("entity_type", "claim");
    fd.append("entity_id", String(id));
    await api("/api/v1/evidence", { method: "POST", body: fd });
    load();
  }

  if (err && !row) return <div className="page"><div className="error">{err}</div></div>;
  if (!row) return <div className="page"><div className="loading">Loading case…</div></div>;

  return (
    <div className="page">
      <PageHead
        title={row.public_id}
        lede={`${row.farmer_reference} · ${row.crop_type} · incident ${row.incident_date}`}
        actions={
          <button className="btn" onClick={requestVerify}>
            Request field verification
          </button>
        }
      />
      {err ? <div className="error">{err}</div> : null}
      {msg ? <div className="empty">{msg}</div> : null}
      <div className="kpis">
        <div className="kpi">
          <div className="k">Reported</div>
          <div className="v">{row.reported_damage_pct}%</div>
        </div>
        <div className="kpi">
          <div className="k">Estimated</div>
          <div className="v">{row.estimated_damage_pct}%</div>
        </div>
        <div className="kpi">
          <div className="k">Difference</div>
          <div className="v">{row.difference_pct}</div>
        </div>
        <div className="kpi">
          <div className="k">Confidence</div>
          <div className="v">{row.confidence ? Math.round(row.confidence * 100) : "—"}%</div>
        </div>
        <div className="kpi">
          <div className="k">Status</div>
          <div className="v" style={{ fontSize: 16 }}>
            <Pill value={row.status} />
          </div>
        </div>
      </div>
      <div className="grid-2">
        <div className="panel">
          <h2>Verification recommendation</h2>
          <p>{row.recommendation}</p>
          <p className="lede">This is not an approval or rejection of any insurance claim.</p>
          <label className="field">
            Supporting evidence
            <input type="file" accept="image/*,.pdf" onChange={(e) => e.target.files?.[0] && upload(e.target.files[0])} />
          </label>
          {ev.length === 0 ? <p className="lede">No files yet.</p> : ev.map((f) => <p key={f.id} className="mono">{f.filename}</p>)}
        </div>
        <div className="panel" style={{ padding: 0 }}>
          <MiniMap geojson={row.field_boundary || null} />
        </div>
      </div>
    </div>
  );
}
