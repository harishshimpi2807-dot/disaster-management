"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Empty, PageHead } from "@/components/ui";
import { api } from "@/lib/api";
import { fmtDate } from "@/lib/format";

type Note = { id: number; title: string; body: string; link: string; read: boolean; created_at: string };

export default function NotificationsPage() {
  const [rows, setRows] = useState<Note[] | null>(null);

  function load() {
    api<Note[]>("/api/v1/notifications").then(setRows);
  }
  useEffect(() => {
    load();
  }, []);

  async function read(id: number) {
    await api(`/api/v1/notifications/${id}/read`, { method: "POST" });
    load();
  }

  return (
    <div className="page">
      <PageHead title="Notices" lede="Assignment, delay, anomaly-risk, and potential-duplicate alerts for your role." />
      {!rows ? (
        <div className="loading">Loading notices…</div>
      ) : rows.length === 0 ? (
        <Empty title="Inbox empty" body="You will be notified when inspections are assigned or high-risk flags appear." />
      ) : (
        <div style={{ display: "grid", gap: 10 }}>
          {rows.map((n) => (
            <article className="panel" key={n.id} style={{ opacity: n.read ? 0.65 : 1 }}>
              <h2>{n.title}</h2>
              <p>{n.body}</p>
              <p className="mono">{fmtDate(n.created_at)}</p>
              <div className="row">
                {n.link ? <Link className="btn" href={n.link}>Open</Link> : null}
                {!n.read ? (
                  <button className="btn ghost" onClick={() => read(n.id)}>
                    Mark read
                  </button>
                ) : null}
              </div>
            </article>
          ))}
        </div>
      )}
    </div>
  );
}
