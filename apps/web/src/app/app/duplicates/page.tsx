"use client";

import { useEffect, useState } from "react";
import { Empty, PageHead, Pill } from "@/components/ui";
import { api } from "@/lib/api";

type Row = {
  id: number;
  public_id: string;
  left_type: string;
  left_id: number;
  right_type: string;
  right_id: number;
  similarity: number;
  matching_factors: string[];
  review_status: string;
};

export default function DuplicatesPage() {
  const [rows, setRows] = useState<Row[] | null>(null);
  const [err, setErr] = useState("");

  function load() {
    api<Row[]>("/api/v1/duplicates").then(setRows).catch((e) => setErr(e.message));
  }
  useEffect(() => {
    load();
  }, []);

  async function setStatus(id: number, review_status: string) {
    await api(`/api/v1/duplicates/${id}?review_status=${review_status}`, { method: "PATCH" });
    load();
  }

  return (
    <div className="page">
      <PageHead
        title="Potential duplicate compensation"
        lede="Pairs that share location, asset, disaster, or reference. Treat as related records for review — never as proof of wrongdoing."
      />
      {err ? <div className="error">{err}</div> : null}
      {!rows ? (
        <div className="loading">Loading matches…</div>
      ) : rows.length === 0 ? (
        <Empty title="No potential duplicates" body="Matches appear when new claims or fund requests overlap existing records." />
      ) : (
        <div style={{ display: "grid", gap: 12 }}>
          {rows.map((r) => (
            <article className="panel" key={r.id}>
              <div className="mono">{r.public_id}</div>
              <h2 style={{ marginTop: 6 }}>
                {r.left_type} #{r.left_id} ↔ {r.right_type} #{r.right_id}
              </h2>
              <p>
                Similarity <span className="mono">{r.similarity}</span> · <Pill value={r.review_status} />
              </p>
              <ul>
                {r.matching_factors.map((f) => (
                  <li key={f}>{f}</li>
                ))}
              </ul>
              <div className="row">
                <button className="btn ghost" onClick={() => setStatus(r.id, "under_review")}>
                  Under review
                </button>
                <button className="btn ghost" onClick={() => setStatus(r.id, "dismissed")}>
                  Dismiss as unrelated
                </button>
                <button className="btn ghost" onClick={() => setStatus(r.id, "confirmed_related")}>
                  Confirm related records
                </button>
              </div>
            </article>
          ))}
        </div>
      )}
    </div>
  );
}
