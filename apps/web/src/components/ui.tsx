"use client";

import { labelize, statusTone } from "@/lib/format";

export function Pill({ value }: { value: string }) {
  return <span className={`pill ${statusTone(value)}`}>{labelize(value)}</span>;
}

export function PageHead({ title, lede, actions }: { title: string; lede?: string; actions?: React.ReactNode }) {
  return (
    <div style={{ display: "flex", justifyContent: "space-between", gap: 16, alignItems: "flex-start", marginBottom: 8 }}>
      <div>
        <h1>{title}</h1>
        {lede ? <p className="lede">{lede}</p> : null}
      </div>
      {actions}
    </div>
  );
}

export function Empty({ title, body }: { title: string; body: string }) {
  return (
    <div className="empty">
      <strong style={{ color: "var(--text)" }}>{title}</strong>
      <p style={{ margin: "8px 0 0" }}>{body}</p>
    </div>
  );
}
