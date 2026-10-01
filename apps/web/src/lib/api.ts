/**
 * API client — thin wrapper around fetch() for the FastAPI backend.
 * All API calls go through here. Base URL from NEXT_PUBLIC_API_URL env var.
 */

const BASE =
  process.env.NEXT_PUBLIC_API_URL ||
  (typeof window !== "undefined" ? "/api/proxy" : "http://127.0.0.1:8001");

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const url = `${BASE}${path}`;
  let res: Response;

  try {
    res = await fetch(url, {
      headers: { "Content-Type": "application/json", ...init?.headers },
      ...init,
    });
  } catch (err) {
    // If browser fetch fails (e.g. cross-port Safari restriction or IPv6 mismatch), retry via Next.js proxy rewrite
    if (typeof window !== "undefined" && !url.startsWith("/api/proxy")) {
      try {
        res = await fetch(`/api/proxy${path}`, {
          headers: { "Content-Type": "application/json", ...init?.headers },
          ...init,
        });
      } catch {
        throw err;
      }
    } else {
      throw err;
    }
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail ?? `API error ${res.status}`);
  }
  return res.json() as Promise<T>;
}

// ── Types ──────────────────────────────────────────────────────────────────────

export type RunStatus = "pending" | "planning" | "running" | "completed" | "failed" | "cancelled";
export type StepStatus = "pending" | "running" | "completed" | "failed" | "skipped";

export interface StepOut {
  id: string;
  step_id: string;
  step_type: string;
  description: string;
  status: StepStatus;
  source_url: string | null;
  error_message: string | null;
  started_at: string | null;
  finished_at: string | null;
}

export interface TaskOut {
  id: string;
  prompt: string;
  status: RunStatus;
  result_count: number;
  created_at: string;
  completed_at: string | null;
  error_message: string | null;
  plan: Record<string, unknown> | null;
  steps: StepOut[];
}

export interface TaskListItem {
  id: string;
  prompt: string;
  status: RunStatus;
  result_count: number;
  created_at: string;
  completed_at: string | null;
}

export interface ResultOut {
  id: string;
  run_id: string;
  source_id: string;
  schema_version: string;
  structured_data: Record<string, unknown>;
  validated: boolean;
  dedup_group_id: string | null;
}

export interface AttestationOut {
  id: string;
  content_hash: string;
  extracted_hash: string;
  signer: string;
  verified: boolean;
  attestation_document: Record<string, unknown>;
}

export interface SourceOut {
  id: string;
  url: string;
  fetched_at: string;
  content_hash: string;
  robots_txt_allowed: boolean;
  attestation: AttestationOut | null;
}

export interface ResultWithSource extends ResultOut {
  source: SourceOut | null;
}

export interface ResultsPage {
  items: ResultOut[];
  total: number;
  page: number;
  page_size: number;
}

// ── API functions ──────────────────────────────────────────────────────────────

export const api = {
  // Tasks
  submitTask: (prompt: string, hints?: Record<string, unknown>) =>
    apiFetch<TaskOut>("/tasks", {
      method: "POST",
      body: JSON.stringify({ prompt, hints: hints ?? {} }),
    }),

  listTasks: (limit = 50) =>
    apiFetch<TaskListItem[]>(`/tasks?limit=${limit}`),

  getTask: (id: string) =>
    apiFetch<TaskOut>(`/tasks/${id}`),

  cancelTask: (id: string) =>
    apiFetch<TaskOut>(`/tasks/${id}/cancel`, { method: "POST" }),

  // Results
  getResults: (taskId: string, page = 1, pageSize = 25, search?: string) => {
    const params = new URLSearchParams({
      page: String(page),
      page_size: String(pageSize),
    });
    if (search) params.set("search", search);
    return apiFetch<ResultsPage>(`/tasks/${taskId}/results?${params}`);
  },

  getResultSource: (resultId: string) =>
    apiFetch<ResultWithSource>(`/results/${resultId}/source`),

  // Datasets / history
  listDatasets: () =>
    apiFetch<TaskListItem[]>("/datasets"),

  // Re-run a completed workflow with the same prompt
  reRunTask: (prompt: string) =>
    apiFetch<TaskOut>("/tasks", {
      method: "POST",
      body: JSON.stringify({ prompt, hints: {} }),
    }),

  // Export — returns a blob
  exportDataset: async (taskId: string, format: "csv" | "json") => {
    const res = await fetch(`${BASE}/datasets/${taskId}/export`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ format }),
    });
    if (!res.ok) throw new Error(`Export failed: ${res.statusText}`);
    return res.blob();
  },
};
