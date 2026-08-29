"use client";

import { FormEvent, useEffect, useState } from "react";
import { PageHead } from "@/components/ui";
import { api } from "@/lib/api";

type Setting = { key: string; value: string };
type Rule = { id: number; name: string; event_type: string; min_risk: string; enabled: boolean };

export default function SettingsPage() {
  const [settings, setSettings] = useState<Setting[]>([]);
  const [rules, setRules] = useState<Rule[]>([]);
  const [key, setKey] = useState("anomaly_high_threshold");
  const [value, setValue] = useState("65");
  const [err, setErr] = useState("");

  function load() {
    api<Setting[]>("/api/v1/settings").then(setSettings).catch((e) => setErr(e.message));
    api<Rule[]>("/api/v1/notification-rules").then(setRules).catch(() => setRules([]));
  }
  useEffect(() => {
    load();
  }, []);

  async function save(e: FormEvent) {
    e.preventDefault();
    try {
      await api("/api/v1/settings", { method: "PUT", body: JSON.stringify({ key, value }) });
      load();
    } catch (ex) {
      setErr(ex instanceof Error ? ex.message : "Save failed");
    }
  }

  return (
    <div className="page">
      <PageHead title="System parameters" lede="Thresholds and notification rules. Changing them is an audited administrative action." />
      {err ? <div className="error">{err}</div> : null}
      <form className="panel" onSubmit={save} style={{ marginBottom: 16 }}>
        <div className="row">
          <label className="field">
            Key
            <input value={key} onChange={(e) => setKey(e.target.value)} />
          </label>
          <label className="field">
            Value
            <input value={value} onChange={(e) => setValue(e.target.value)} />
          </label>
          <button className="btn">Save parameter</button>
        </div>
      </form>
      <div className="grid-2">
        <div className="panel">
          <h2>Current keys</h2>
          <table>
            <tbody>
              {settings.map((s) => (
                <tr key={s.key}>
                  <td className="mono">{s.key}</td>
                  <td>{s.value}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="panel">
          <h2>Notification rules</h2>
          {rules.map((r) => (
            <p key={r.id}>
              {r.name} · {r.event_type} ≥ {r.min_risk} · {r.enabled ? "on" : "off"}
            </p>
          ))}
        </div>
      </div>
    </div>
  );
}
