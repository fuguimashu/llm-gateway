const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

function getKey(): string {
  if (typeof window === "undefined") return "";
  return localStorage.getItem("llm_gateway_master_key") ?? "";
}

async function req<T>(
  path: string,
  options: RequestInit = {},
  key?: string,
): Promise<T> {
  const token = key ?? getKey();
  const res = await fetch(`${BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
      ...(options.headers ?? {}),
    },
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`${res.status} ${body}`);
  }
  return res.json() as Promise<T>;
}

// ── Types ─────────────────────────────────────────────────────────────────────

export interface VirtualKey {
  id: string;
  name: string;
  models: string | null;
  created_at: string;
  last_used_at: string | null;
  is_active: boolean;
}

export interface VirtualKeyCreated extends VirtualKey {
  key: string;
}

export interface RequestLog {
  id: number;
  request_id: string;
  virtual_key_id: string | null;
  model: string;
  status: "success" | "error";
  prompt_tokens: number | null;
  completion_tokens: number | null;
  total_tokens: number | null;
  latency_ms: number | null;
  total_latency_ms: number | null;
  error_message: string | null;
  created_at: string;
}

export interface LogsPage {
  items: RequestLog[];
  total: number;
  page: number;
  page_size: number;
}

export interface ModelStatus {
  id: string;
  object: string;
  provider: string;
  available: boolean;
  consecutive_failures: number;
  cooldown_remaining_seconds: number;
}

// ── Health ────────────────────────────────────────────────────────────────────

export async function getHealth() {
  return req<{ status: string }>("/health");
}

// ── Models ────────────────────────────────────────────────────────────────────

export async function getModels() {
  const r = await req<{ data: ModelStatus[] }>("/v1/models");
  return r.data;
}

// ── Virtual Keys ──────────────────────────────────────────────────────────────

export async function listKeys(key?: string) {
  return req<VirtualKey[]>("/v1/keys", {}, key);
}

export async function createKey(name: string, models: string | null) {
  return req<VirtualKeyCreated>("/v1/keys", {
    method: "POST",
    body: JSON.stringify({ name, models }),
  });
}

export async function deleteKey(id: string) {
  return req<void>(`/v1/keys/${id}`, { method: "DELETE" });
}

export async function activateKey(id: string) {
  return req<VirtualKey>(`/v1/keys/${id}/activate`, { method: "POST" });
}

// ── Logs ──────────────────────────────────────────────────────────────────────

export async function getLogs(params: {
  page?: number;
  page_size?: number;
  model?: string;
  status?: string;
}) {
  const q = new URLSearchParams();
  if (params.page) q.set("page", String(params.page));
  if (params.page_size) q.set("page_size", String(params.page_size));
  if (params.model) q.set("model", params.model);
  if (params.status) q.set("status", params.status);
  return req<LogsPage>(`/v1/logs?${q}`);
}

// ── Dashboard Stats (derived from logs) ───────────────────────────────────────

export interface DashboardStats {
  total_requests: number;
  success_rate: number;
  total_tokens: number;
  avg_latency_ms: number;
}

export async function getDashboardStats(): Promise<DashboardStats> {
  // Fetch first 500 logs to compute stats (sufficient for local use)
  const data = await getLogs({ page: 1, page_size: 500 });
  const items = data.items;
  const total = data.total;
  const successes = items.filter((l) => l.status === "success");
  const tokens = items.reduce((s, l) => s + (l.total_tokens ?? 0), 0);
  const latencies = successes
    .map((l) => l.total_latency_ms ?? 0)
    .filter((v) => v > 0);
  const avgLatency =
    latencies.length > 0
      ? Math.round(latencies.reduce((a, b) => a + b, 0) / latencies.length)
      : 0;
  return {
    total_requests: total,
    success_rate: items.length > 0 ? (successes.length / items.length) * 100 : 0,
    total_tokens: tokens,
    avg_latency_ms: avgLatency,
  };
}
