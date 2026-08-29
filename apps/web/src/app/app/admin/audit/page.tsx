"use client";

import { useEffect, useState } from "react";
import { Empty, PageHead } from "@/components/ui";
import { api } from "@/lib/api";
import { fmtDate } from "@/lib/format";

type Item = { id: number; actor_id: number | null; action: string; entity_type: string; entity_id: string; created_at: string };

export default function AuditPage() {
  const [items, setItems] = useState<Item[] | null>(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    api<{ items: Item[] }>("/api/v1/audit")
      .then((r) => setItems(r.items))
      .catch((e) => setErr(e.message));
  }, []);

  return (
    <div className="page">
      <PageHead title="Audit log" lede="Immutable operational trail of sign-ins, writes, uploads, exports, and reviews." />
      {err ? <div className="error">{err}</div> : null}
      {!items ? (
        <div className="loading">Loading audit entries…</div>
      ) : items.length === 0 ? (
        <Empty title="No audit entries yet" body="Actions will appear here after the first authenticated write." />
      ) : (
        <div className="panel" style={{ padding: 0 }}>
          <table>
            <thead>
              <tr>
                <th>When</th>
                <th>Actor</th>
                <th>Action</th>
                <th>Entity</th>
              </tr>
            </thead>
            <tbody>
              {items.map((i) => (
                <tr key={i.id}>
                  <td className="mono">{fmtDate(i.created_at)}</td>
                  <td>{i.actor_id ?? "—"}</td>
                  <td>{i.action}</td>
                  <td className="mono">
                    {i.entity_type} {i.entity_id}
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
