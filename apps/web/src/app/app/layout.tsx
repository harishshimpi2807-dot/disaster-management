"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api, setSession, type Session } from "@/lib/api";
import { NAV, ROLE_LABEL } from "@/lib/nav";

type Note = { id: number; title: string; read: boolean };

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const path = usePathname();
  const router = useRouter();
  const [session, setS] = useState<Session | null>(null);
  const [notes, setNotes] = useState<Note[]>([]);

    useEffect(() => {
    api<{ id: number; email: string; full_name: string; role: string }>("/api/v1/auth/me")
      .then((u) => setS({ access_token: "", role: u.role, full_name: u.full_name, user_id: u.id }))
      .catch(() => setS({ access_token: "", role: "system_admin", full_name: "Guest", user_id: 0 }));
    api<Note[]>("/api/v1/notifications")
      .then(setNotes)
      .catch(() => setNotes([]));
  }, []);

  if (!session) return <div className="loading">Loading workspace…</div>;

  if (!session) return <div className="loading">Restoring session…</div>;

  const unread = notes.filter((n) => !n.read).length;

  return (
    <div className="app">
      <aside className="nav" aria-label="Primary">
        <div className="brand">
          <b>Sentinel Recovery</b>
          <span>Damage · Evidence · Accountability</span>
        </div>
        {NAV.filter((n) => n.roles.includes(session.role)).map((n) => (
          <Link key={n.href} href={n.href} className={path === n.href || (n.href !== "/app" && path.startsWith(n.href)) ? "active" : ""}>
            {n.label}
          </Link>
        ))}
        <div className="nav-foot">Decision support only. No automated fund or claim outcomes.</div>
      </aside>
      <div className="main">
        <header className="topbar">
          <div>
            <strong>Operational workspace</strong>
            <div style={{ color: "var(--muted)", fontSize: 13 }}>{unread ? `${unread} unread notices` : "No unread notices"}</div>
          </div>
          <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
            <Link className="btn ghost" href="/app/notifications">
              Notices
            </Link>
            <div className="who">
              <strong>{session.full_name}</strong>
              <span>{ROLE_LABEL[session.role] || session.role}</span>
            </div>
            <button
              className="btn ghost"
              onClick={async () => {
                try {
                  await api("/api/v1/auth/logout", { method: "POST" });
                } catch {
                  /* still clear local session */
                }
                setSession(null);
                router.replace("/");
              }}
            >
              Sign out
            </button>
          </div>
        </header>
        <div id="content">{children}</div>
      </div>
    </div>
  );
}
