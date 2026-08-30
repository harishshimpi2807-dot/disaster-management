"use client";

import { useState } from "react";
import { PageHead } from "@/components/ui";
import { API_BASE } from "@/lib/api";

export default function ReportsPage() {
  const [err, setErr] = useState("");

  async function open(kind: string) {
    setErr("");
    try {
      const res = await fetch(`${API_BASE}/api/v1/reports/export?kind=${kind}`);
      if (!res.ok) throw new Error("Export failed");
      const b = await res.blob();
      const url = URL.createObjectURL(b);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${kind}.csv`;
      a.click();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Export failed");
    }
  }

  return (
    <div className="page">
      <PageHead title="Reports" lede="Exports are audited. Use them for review packs, not as automated determinations." />
      {err ? <div className="error">{err}</div> : null}
      <div className="grid-2">
        {[
          ["anomalies", "Anomaly-risk register"],
          ["duplicates", "Potential duplicate pairs"],
          ["funds", "Fund requirements"],
          ["claims", "Crop-loss cases"],
        ].map(([k, l]) => (
          <div className="panel" key={k}>
            <h2>{l}</h2>
            <p className="lede">CSV download of current records.</p>
            <button className="btn" onClick={() => open(k)}>
              Export {k}
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
