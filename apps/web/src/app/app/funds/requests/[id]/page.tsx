"use client";

import dynamic from "next/dynamic";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { PageHead, Pill } from "@/components/ui";
import { api } from "@/lib/api";
import { money } from "@/lib/format";

const MiniMap = dynamic(() => import("@/components/MiniMap"), { ssr: false });

type Row = {
  id: number;
  public_id: string;
  department: string;
  location_label: string;
  damage_category: string;
  reported_damage: string;
  requested_amount: number;
  evidence_consistency: number | null;
  confidence: number | null;
  recommendation: string;
  status: string;
  geometry?: GeoJSON.Polygon;
};
type Ev = { id: number; filename: string };

export default function FundRequestDetail() {
  const { id } = useParams<{ id: string }>();
  const [row, setRow] = useState<Row | null>(null);
  const [ev, setEv] = useState<Ev[]>([]);
  const [err, setErr] = useState("");

  function load() {
    api<Row>(`/api/v1/fund-requests/${id}`).then(setRow).catch((e) => setErr(e.message));
    api<Ev[]>(`/api/v1/evidence?entity_type=fund_request&entity_id=${id}`).then(setEv).catch(() => setEv([]));
  }
  useEffect(() => {
    load();
  }, [id]);

  async function upload(file: File) {
    const fd = new FormData();
    fd.append("file", file);
    fd.append("entity_type", "fund_request");
    fd.append("entity_id", String(id));
    await api("/api/v1/evidence", { method: "POST", body: fd });
    load();
  }

  if (err && !row) return <div className="page"><div className="error">{err}</div></div>;
  if (!row) return <div className="page"><div className="loading">Loading fund requirement…</div></div>;

  return (
    <div className="page">
      <PageHead title={row.public_id} lede={`${row.department} · ${row.location_label}`} />
      <div className="kpis">
        <div className="kpi">
          <div className="k">Requested</div>
          <div className="v">{money(row.requested_amount)}</div>
        </div>
        <div className="kpi">
          <div className="k">Evidence consistency</div>
          <div className="v">{row.evidence_consistency ?? "—"}</div>
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
          <h2>Reported damage</h2>
          <p>{row.reported_damage}</p>
          <h2>Recommendation</h2>
          <p>{row.recommendation}</p>
          <p className="lede">Officials remain responsible for any funding decision.</p>
          <label className="field">
            Supporting documents
            <input type="file" accept="image/*,.pdf" onChange={(e) => e.target.files?.[0] && upload(e.target.files[0])} />
          </label>
          {ev.map((f) => (
            <p key={f.id} className="mono">
              {f.filename}
            </p>
          ))}
        </div>
        <div className="panel" style={{ padding: 0 }}>
          <MiniMap geojson={row.geometry || null} />
        </div>
      </div>
    </div>
  );
}
