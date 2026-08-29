"use client";

import { FormEvent, useEffect, useState } from "react";
import { Empty, PageHead, Pill } from "@/components/ui";
import { api } from "@/lib/api";

type Disaster = { id: number; name: string };
type Assessment = {
  id: number;
  public_id: string;
  disaster_id: number;
  category: string;
  severity: string;
  estimated_area_ha: number;
  confidence: number;
  analyzed_at?: string;
  notes: string;
};
type ImageRow = { id: number; phase: string; filename: string };

export default function AssessmentsPage() {
  const [rows, setRows] = useState<Assessment[] | null>(null);
  const [disasters, setDisasters] = useState<Disaster[]>([]);
  const [images, setImages] = useState<ImageRow[]>([]);
  const [disasterId, setDisasterId] = useState("");
  const [notes, setNotes] = useState("");
  const [before, setBefore] = useState("");
  const [after, setAfter] = useState("");
  const [job, setJob] = useState<string>("");
  const [err, setErr] = useState("");

  function load() {
    api<Assessment[]>("/api/v1/assessments").then(setRows).catch((e) => setErr(e.message));
  }

  useEffect(() => {
    load();
    api<Disaster[]>("/api/v1/disasters").then(setDisasters);
    api<ImageRow[]>("/api/v1/imagery").then(setImages);
  }, []);

  async function upload(phase: string, file: File) {
    const fd = new FormData();
    fd.append("file", file);
    fd.append("phase", phase);
    if (disasterId) fd.append("disaster_id", disasterId);
    await api("/api/v1/imagery", { method: "POST", body: fd });
    setImages(await api<ImageRow[]>("/api/v1/imagery"));
  }

  async function analyze(e: FormEvent) {
    e.preventDefault();
    setErr("");
    try {
      const r = await api<{ job_id: number; status: string }>("/api/v1/assessments/analyze", {
        method: "POST",
        body: JSON.stringify({
          disaster_id: Number(disasterId),
          notes,
          before_image_id: before ? Number(before) : null,
          after_image_id: after ? Number(after) : null,
        }),
      });
      setJob(`Job ${r.job_id} ${r.status}. Refresh in a few seconds for detected change classes.`);
      setTimeout(load, 1200);
    } catch (ex) {
      setErr(ex instanceof Error ? ex.message : "Analysis failed");
    }
  }

  return (
    <div className="page">
      <PageHead
        title="AI-assisted damage assessment"
        lede="Upload before/after imagery, register metadata, and run the analysis job. The default provider is a replaceable heuristic service — not an autonomous decision."
      />
      <form className="panel" onSubmit={analyze} style={{ display: "grid", gap: 12, marginBottom: 16 }}>
        <div className="grid-2">
          <label className="field">
            Disaster
            <select required value={disasterId} onChange={(e) => setDisasterId(e.target.value)}>
              <option value="">Select</option>
              {disasters.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name}
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            Notes
            <input value={notes} onChange={(e) => setNotes(e.target.value)} />
          </label>
          <label className="field">
            Before imagery
            <select value={before} onChange={(e) => setBefore(e.target.value)}>
              <option value="">None</option>
              {images.filter((i) => i.phase === "before").map((i) => (
                <option key={i.id} value={i.id}>
                  {i.filename} (#{i.id})
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            After imagery
            <select value={after} onChange={(e) => setAfter(e.target.value)}>
              <option value="">None</option>
              {images.filter((i) => i.phase === "after").map((i) => (
                <option key={i.id} value={i.id}>
                  {i.filename} (#{i.id})
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            Upload before
            <input type="file" accept="image/*,.pdf,.json" onChange={(e) => e.target.files?.[0] && upload("before", e.target.files[0])} />
          </label>
          <label className="field">
            Upload after
            <input type="file" accept="image/*,.pdf,.json" onChange={(e) => e.target.files?.[0] && upload("after", e.target.files[0])} />
          </label>
        </div>
        {err ? <div className="error">{err}</div> : null}
        {job ? <div className="empty">{job}</div> : null}
        <button className="btn">Run analysis workflow</button>
      </form>
      {!rows ? (
        <div className="loading">Loading assessments…</div>
      ) : rows.length === 0 ? (
        <Empty title="No assessments yet" body="Trigger an analysis against a disaster AOI to populate categories, area, severity, and confidence." />
      ) : (
        <div className="panel" style={{ padding: 0 }}>
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Category</th>
                <th>Severity</th>
                <th>Area (ha)</th>
                <th>Confidence</th>
                <th>Analysed</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.id}>
                  <td className="mono">{r.public_id}</td>
                  <td>{r.category}</td>
                  <td>
                    <Pill value={r.severity} />
                  </td>
                  <td className="mono">{r.estimated_area_ha}</td>
                  <td className="mono">{Math.round(r.confidence * 100)}%</td>
                  <td>{r.analyzed_at ? r.analyzed_at.slice(0, 19).replace("T", " ") : "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
