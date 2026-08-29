"use client";

import dynamic from "next/dynamic";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { PageHead, Pill } from "@/components/ui";
import { api } from "@/lib/api";

const MiniMap = dynamic(() => import("@/components/MiniMap"), { ssr: false });

type Ev = { id: number; filename: string };
type Detail = {
  id: number;
  public_id: string;
  status: string;
  required_actions: string;
  observations: string;
  verified_damage: string;
  arrived_at?: string;
  context: { claim?: Record<string, string | number>; assessment?: Record<string, string | number> };
  anomaly_alerts: { public_id: string; risk_level: string; risk_score: number; reasons: string[] }[];
  potential_duplicates: { public_id: string; similarity: number; matching_factors: string[] }[];
  location?: GeoJSON.Point | GeoJSON.Polygon;
};

export default function InspectionDetail() {
  const { id } = useParams<{ id: string }>();
  const [row, setRow] = useState<Detail | null>(null);
  const [obs, setObs] = useState("");
  const [verified, setVerified] = useState("");
  const [ev, setEv] = useState<Ev[]>([]);
  const [err, setErr] = useState("");
  const [lat, setLat] = useState<number | null>(null);
  const [lng, setLng] = useState<number | null>(null);

  function load() {
    api<Detail>(`/api/v1/inspections/${id}`).then((d) => {
      setRow(d);
      setObs(d.observations);
      setVerified(d.verified_damage);
    }).catch((e) => setErr(e.message));
    api<Ev[]>(`/api/v1/evidence?entity_type=inspection&entity_id=${id}`).then(setEv).catch(() => setEv([]));
  }
  useEffect(() => {
    load();
  }, [id]);

  async function patch(status?: string) {
    try {
      await api(`/api/v1/inspections/${id}`, {
        method: "PATCH",
        body: JSON.stringify({
          status,
          observations: obs,
          verified_damage: verified,
          location: lat && lng ? { type: "Point", coordinates: [lng, lat] } : undefined,
        }),
      });
      load();
    } catch (ex) {
      setErr(ex instanceof Error ? ex.message : "Update failed");
    }
  }

  async function upload(file: File) {
    const fd = new FormData();
    fd.append("file", file);
    fd.append("entity_type", "inspection");
    fd.append("entity_id", String(id));
    if (lat) fd.append("latitude", String(lat));
    if (lng) fd.append("longitude", String(lng));
    await api("/api/v1/evidence", { method: "POST", body: fd });
    load();
  }

  function geo() {
    navigator.geolocation?.getCurrentPosition((p) => {
      setLat(p.coords.latitude);
      setLng(p.coords.longitude);
    });
  }

  if (err && !row) return <div className="page"><div className="error">{err}</div></div>;
  if (!row) return <div className="page"><div className="loading">Loading inspection…</div></div>;

  return (
    <div className="page">
      <PageHead title={row.public_id} lede="Mark arrival, capture geotagged evidence, record observations, and submit for review." />
      {err ? <div className="error">{err}</div> : null}
      <div className="grid-2">
        <div className="panel">
          <p>
            <Pill value={row.status} />
          </p>
          <h2>Required actions</h2>
          <p>{row.required_actions}</p>
          {row.context.claim ? (
            <p>
              Reported {String(row.context.claim.reported_damage_pct)}% · Estimated {String(row.context.claim.estimated_damage_pct)}% ·{" "}
              <Pill value={String(row.context.claim.status)} />
            </p>
          ) : null}
          <h2>Anomaly risk</h2>
          {row.anomaly_alerts.length === 0 ? <p style={{ color: "var(--muted)" }}>No linked alerts.</p> : row.anomaly_alerts.map((a) => (
            <p key={a.public_id}>
              {a.public_id} · {a.risk_level} ({a.risk_score}) — {a.reasons.join("; ")}
            </p>
          ))}
          <h2>Potential duplicates</h2>
          {row.potential_duplicates.length === 0 ? <p style={{ color: "var(--muted)" }}>None linked.</p> : row.potential_duplicates.map((d) => (
            <p key={d.public_id}>
              {d.public_id} · similarity {d.similarity}
            </p>
          ))}
        </div>
        <div className="panel" style={{ display: "grid", gap: 12 }}>
          <button className="btn ghost" type="button" onClick={geo}>
            Capture GPS
          </button>
          <p className="mono">
            {lat && lng ? `${lat.toFixed(5)}, ${lng.toFixed(5)}` : "No GPS yet"}
          </p>
          <button className="btn ghost" type="button" onClick={() => patch("en_route")}>
            Start inspection / en route
          </button>
          <button className="btn" type="button" onClick={() => patch("arrived")}>
            Mark arrival
          </button>
          <label className="field">
            Geotagged photograph
            <input type="file" accept="image/*" capture="environment" onChange={(e) => e.target.files?.[0] && upload(e.target.files[0])} />
          </label>
          <label className="field">
            Observations
            <textarea value={obs} onChange={(e) => setObs(e.target.value)} />
          </label>
          <label className="field">
            Verified damage
            <textarea value={verified} onChange={(e) => setVerified(e.target.value)} />
          </label>
          <div className="row">
            <button className="btn ghost" type="button" onClick={() => patch("in_progress")}>
              Save progress
            </button>
            <button className="btn ghost" type="button" onClick={() => patch("needs_further_investigation")}>
              Request further investigation
            </button>
            <button className="btn" type="button" onClick={() => patch("ready_for_review")}>
              Submit for review
            </button>
          </div>
          {ev.length ? (
            <div>
              <h2>Uploaded evidence</h2>
              {ev.map((f) => (
                <p key={f.id} className="mono">
                  {f.filename}
                </p>
              ))}
            </div>
          ) : null}
        </div>
        <div className="panel" style={{ padding: 0, minHeight: 240 }}>
          <MiniMap geojson={row.location || (lat && lng ? { type: "Point", coordinates: [lng, lat] } : null)} center={lng && lat ? [lng, lat] : [73.5, 17.52]} zoom={11} />
        </div>
      </div>
    </div>
  );
}
