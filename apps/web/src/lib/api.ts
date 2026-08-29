export const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export type Session = {
  access_token: string;
  role: string;
  full_name: string;
  user_id: number;
};

const KEY = "sentinel.session";

export function getSession(): Session | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem(KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as Session;
  } catch {
    return null;
  }
}

export function setSession(s: Session | null) {
  if (s) localStorage.setItem(KEY, JSON.stringify(s));
  else localStorage.removeItem(KEY);
}

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const session = getSession();
  const headers = new Headers(init.headers);
  if (!(init.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }
  if (session?.access_token) headers.set("Authorization", `Bearer ${session.access_token}`);
  const res = await fetch(`${API_BASE}${path}`, { ...init, headers });
    if (res.status === 401) {
    setSession(null);
    if (typeof window !== "undefined" && window.location.pathname !== "/") {
      window.location.href = "/";
    }
  }
  const text = await res.text();
  const data = text ? JSON.parse(text) : null;
  if (!res.ok) {
    const detail = data?.detail;
    const msg = typeof detail === "string" ? detail : Array.isArray(detail) ? detail.map((d: { msg?: string }) => d.msg).join(", ") : res.statusText;
    throw new ApiError(res.status, msg || "Request failed");
  }
  return data as T;
}
