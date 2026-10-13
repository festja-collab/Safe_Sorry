import { storage } from "@/src/utils/storage";

export const TOKEN_KEY = "safe_sorry_token";
const BASE = `${process.env.EXPO_PUBLIC_BACKEND_URL}/api`;

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

export async function api<T>(path: string, opts: { method?: string; body?: unknown } = {}): Promise<T> {
  const token = await storage.secureGet<string | null>(TOKEN_KEY, null);
  const res = await fetch(BASE + path, {
    method: opts.method ?? "GET",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: opts.body !== undefined ? JSON.stringify(opts.body) : undefined,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const d = (data as any)?.detail;
    const msg = typeof d === "string" ? d : Array.isArray(d) ? "Please check your details and try again" : "Something went wrong";
    throw new ApiError(msg, res.status);
  }
  return data as T;
}

export type User = { id: string; email: string; name: string; role: "client" | "adviser"; is_firm_admin: boolean; adviser_code: string | null };

export type AdviserProfile = {
  id: string;
  name: string;
  title: string;
  bio: string;
  photo_url: string;
  phone: string;
  calendly_url: string;
  email: string;
  adviser_code: string | null;
  firm_name: string;
  fca_number: string;
  principal_name: string;
  principal_fca_number: string;
};

export type LeadStatus = "new" | "contacted" | "closed";
export type Lead = {
  id: string;
  name: string;
  email: string;
  phone: string;
  preferred_time: string;
  message: string;
  status: LeadStatus;
  created_at: string;
  assessment_id: string | null;
  summary?: { headline: string; protected_pct: number; life_gap: number } | null;
  assessment?: Assessment | null;
};

export function timeAgo(iso: string) {
  const mins = Math.round((Date.now() - new Date(iso).getTime()) / 60000);
  if (mins < 60) return `${Math.max(1, mins)}m ago`;
  const h = Math.round(mins / 60);
  if (h < 24) return `${h}h ago`;
  return `${Math.round(h / 24)}d ago`;
}

export type Gap = { need: number; have: number; gap: number; monthly?: boolean };
export type Impact = { icon: string; title: string; body: string; tone: "error" | "warning" | "success" | "info" };
export type Milestone = { month: number; label: string; kind: "child" | "home" | "runout"; date: string; funded: boolean };

export type Results = {
  headline: string;
  has_dependants: boolean;
  runway_months: number | null;
  runway_label: string;
  runout_date: string | null;
  illness_runway_months: number | null;
  illness_runway_label: string;
  monthly_gap_death: number;
  monthly_gap_illness: number;
  protected_pct: number;
  debts_cleared: boolean;
  gaps: { life: Gap; income: Gap; critical: Gap };
  impacts: Impact[];
  milestones: Milestone[];
  child_names: string[];
};

export type Story = { title: string; paragraphs: string[]; closing: string };

export type Assessment = {
  id: string;
  inputs: Record<string, any>;
  results: Results;
  story: Story | null;
  created_at: string;
};

export type AssessmentSummary = {
  id: string;
  created_at: string;
  headline: string;
  runway_label: string;
  runway_months: number | null;
  protected_pct: number;
  life_gap: number;
  has_dependants: boolean;
};

export type ArticleSummary = { slug: string; category: string; title: string; excerpt: string; read_minutes: number };
export type Article = ArticleSummary & { body: string[] };

export function gbp(n: number | null | undefined) {
  const v = Math.round(n ?? 0);
  return "£" + String(Math.abs(v)).replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

export function niceDate(iso: string) {
  const d = new Date(iso);
  const m = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][d.getMonth()];
  return `${d.getDate()} ${m} ${d.getFullYear()}`;
}
