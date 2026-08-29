export const ROLE_LABEL: Record<string, string> = {
  system_admin: "System administrator",
  gov_admin: "Government administrator",
  field_officer: "Field officer",
  agri_officer: "Agricultural / insurance officer",
  auditor: "Auditor / reviewer",
};

export type NavItem = { href: string; label: string; roles: string[] };

const ALL = Object.keys(ROLE_LABEL);

export const NAV: NavItem[] = [
  { href: "/app", label: "Overview", roles: ALL },
  { href: "/app/map", label: "GIS intelligence", roles: ALL },
  { href: "/app/disasters", label: "Disasters", roles: ["system_admin", "gov_admin", "agri_officer", "auditor"] },
  { href: "/app/assessments", label: "Damage assessment", roles: ["system_admin", "gov_admin", "agri_officer", "auditor"] },
  { href: "/app/claims", label: "Crop-loss cases", roles: ["system_admin", "gov_admin", "agri_officer", "auditor"] },
  { href: "/app/funds/requests", label: "Fund requirements", roles: ["system_admin", "gov_admin", "auditor"] },
  { href: "/app/funds/allocations", label: "Fund utilisation", roles: ["system_admin", "gov_admin", "auditor"] },
  { href: "/app/anomalies", label: "Anomaly risk", roles: ["system_admin", "gov_admin", "agri_officer", "auditor"] },
  { href: "/app/duplicates", label: "Potential duplicates", roles: ["system_admin", "gov_admin", "agri_officer", "auditor"] },
  { href: "/app/inspections", label: "Field verification", roles: ALL },
  { href: "/app/recovery", label: "Recovery", roles: ["system_admin", "gov_admin", "auditor"] },
  { href: "/app/reports", label: "Reports", roles: ["system_admin", "gov_admin", "agri_officer", "auditor"] },
  { href: "/app/admin/users", label: "Users", roles: ["system_admin"] },
  { href: "/app/admin/settings", label: "Parameters", roles: ["system_admin"] },
  { href: "/app/admin/audit", label: "Audit log", roles: ["system_admin", "auditor"] },
];

export function can(role: string, href: string) {
  const item = NAV.find((n) => n.href === href);
  return item ? item.roles.includes(role) : false;
}
