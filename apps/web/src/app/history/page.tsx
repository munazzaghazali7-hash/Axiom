"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { api, TaskListItem } from "@/lib/api";
import { StatusBadge } from "@/components/StatusBadge";

function formatDate(iso: string) {
  return new Intl.DateTimeFormat("en-IN", {
    month: "short", day: "numeric", hour: "2-digit", minute: "2-digit",
  }).format(new Date(iso));
}

function formatDuration(created: string, completed: string | null | undefined) {
  if (!completed) return null;
  const ms = new Date(completed).getTime() - new Date(created).getTime();
  if (ms < 60000) return `${Math.round(ms / 1000)}s`;
  return `${Math.round(ms / 60000)}m`;
}

export default function HistoryPage() {
  const router = useRouter();
  const [datasets, setDatasets] = useState<TaskListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [rerunning, setRerunning] = useState<string | null>(null);  // dataset id being re-run

  const handleReRun = async (ds: TaskListItem) => {
    if (rerunning) return;
    setRerunning(ds.id);
    try {
      const newTask = await api.reRunTask(ds.prompt);
      router.push(`/tasks/${newTask.id}`);
    } catch (e) {
      alert(e instanceof Error ? e.message : "Re-run failed");
      setRerunning(null);
    }
  };

  useEffect(() => {
    api.listDatasets()
      .then(setDatasets)
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load"))
      .finally(() => setLoading(false));
  }, []);

  const completed = datasets.filter((d) => d.status === "completed");
  const totalRecords = completed.reduce((sum, d) => sum + (d.result_count ?? 0), 0);

  return (
    <div className="page-container section">
      {/* Header */}
      <div
        style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", marginBottom: "var(--spacing-48)", flexWrap: "wrap", gap: 16 }}
        className="animate-in"
      >
        <div>
          <p className="eyebrow" style={{ marginBottom: 8 }}>Workflow history</p>
          <h1 style={{ fontSize: "var(--text-heading)", letterSpacing: "-0.64px", marginBottom: 8 }}>
            Past workflows
          </h1>
          {!loading && datasets.length > 0 && (
            <p style={{ fontSize: "var(--text-body-sm)", color: "var(--color-stone)" }}>
              {completed.length} completed run{completed.length !== 1 ? "s" : ""} · {totalRecords.toLocaleString()} total records
            </p>
          )}
        </div>
        <Link href="/" className="btn btn-primary" style={{ flexShrink: 0 }}>
          + New workflow
        </Link>
      </div>

      {/* Loading skeletons */}
      {loading && (
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {[...Array(5)].map((_, i) => (
            <div key={i} className="skeleton animate-in" style={{ height: 80, borderRadius: 16, animationDelay: `${i * 0.06}s` }} />
          ))}
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="card" style={{ borderColor: "var(--color-clay-error)", background: "rgba(163,64,47,0.04)", textAlign: "center" }}>
          <p style={{ color: "var(--color-clay-error)", fontWeight: 500, marginBottom: 4 }}>Failed to load history</p>
          <p style={{ fontSize: "var(--text-body-sm)", color: "var(--color-graphite)" }}>{error}</p>
        </div>
      )}

      {/* Empty state */}
      {!loading && !error && datasets.length === 0 && (
        <div className="empty-state animate-in">
          <div className="empty-state-icon">
            <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" style={{ opacity: 0.6 }} aria-hidden="true">
              <path d="M4 20h16a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.93a2 2 0 0 1-1.66-.9l-.82-1.2A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13c0 1.1.9 2 2 2Z" />
            </svg>
          </div>
          <h3>No completed workflows yet</h3>
          <p>Completed workflow runs will appear here so you can revisit results and re-run them.</p>
          <Link href="/" className="btn btn-primary">Run your first workflow</Link>
        </div>
      )}

      {/* Dataset list */}
      {!loading && datasets.length > 0 && (
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {datasets.map((ds, i) => {
            const duration = formatDuration(ds.created_at, ds.completed_at);
            return (
              <div
                key={ds.id}
                className="card card-shadow history-card animate-in"
                style={{ animationDelay: `${i * 0.04}s` }}
              >
                {/* Left: prompt + metadata */}
                <div style={{ flex: 1, minWidth: 0 }}>
                  <p style={{
                    fontWeight: 500,
                    fontSize: "var(--text-body-sm)",
                    marginBottom: 8,
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    whiteSpace: "nowrap",
                    color: "var(--color-charcoal)",
                  }}>
                    {ds.prompt}
                  </p>
                  <div style={{ display: "flex", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
                    <StatusBadge status={ds.status} />
                    {ds.result_count > 0 && (
                      <span style={{ fontSize: "var(--text-caption)", color: "var(--color-stone)" }}>
                        {ds.result_count.toLocaleString()} record{ds.result_count !== 1 ? "s" : ""}
                      </span>
                    )}
                    {duration && (
                      <span style={{ fontSize: "var(--text-caption)", color: "var(--color-stone)", display: "inline-flex", alignItems: "center", gap: 4 }}>
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                          <circle cx="12" cy="12" r="10" />
                          <polyline points="12 6 12 12 16 14" />
                        </svg>
                        {duration}
                      </span>
                    )}
                    {ds.completed_at && (
                      <span style={{ fontSize: "var(--text-caption)", color: "var(--color-stone)" }}>
                        {formatDate(ds.completed_at)}
                      </span>
                    )}
                  </div>
                </div>

                {/* Right: actions */}
                <div style={{ display: "flex", gap: 8, flexShrink: 0 }}>
                  {ds.result_count > 0 && (
                    <Link
                      href={`/tasks/${ds.id}/results`}
                      className="btn btn-primary btn-sm"
                      style={{ display: "inline-flex", alignItems: "center", gap: 6 }}
                    >
                      <span>Results</span>
                      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                        <polyline points="9 18 15 12 9 6" />
                      </svg>
                    </Link>
                  )}
                  <Link href={`/tasks/${ds.id}`} className="btn btn-ghost btn-sm">
                    Run log
                  </Link>
                  <button
                    className="btn btn-ghost btn-sm"
                    onClick={() => handleReRun(ds)}
                    disabled={rerunning === ds.id}
                    title="Re-run this workflow with the same prompt"
                    style={{ display: "inline-flex", alignItems: "center", justifyContent: "center", minWidth: 32 }}
                  >
                    {rerunning === ds.id ? (
                      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="spinner" aria-hidden="true">
                        <path d="M21 12a9 9 0 1 1-6.219-8.56" />
                      </svg>
                    ) : (
                      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                        <path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8" />
                        <path d="M3 3v5h5" />
                        <path d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16" />
                        <path d="M16 16h5v5" />
                      </svg>
                    )}
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
