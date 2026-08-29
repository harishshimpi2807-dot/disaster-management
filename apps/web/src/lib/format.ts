export function money(n: number) {
  return new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(n);
}

export function fmtDate(v?: string | null) {
  if (!v) return "—";
  return new Intl.DateTimeFormat("en-IN", { day: "2-digit", month: "short", year: "numeric" }).format(new Date(v));
}

export function statusTone(status: string) {
  const s = status.toLowerCase();
  if (["critical", "catastrophic", "high_anomaly_risk", "significant_discrepancy_detected", "delayed"].some((x) => s.includes(x) || s === x)) return "critical";
  if (["high", "severe", "requires", "discrepancy", "needs"].some((x) => s.includes(x))) return "warn";
  if (["consistent", "restored", "completed", "advanced", "low"].some((x) => s.includes(x))) return "ok";
  if (["underway", "early", "monitoring", "progress"].some((x) => s.includes(x))) return "recover";
  return "info";
}

export function labelize(s: string) {
  return s.replaceAll("_", " ");
}
