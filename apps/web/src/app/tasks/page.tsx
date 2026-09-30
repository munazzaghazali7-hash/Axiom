"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { api, TaskListItem } from "@/lib/api";
import { StatusBadge } from "@/components/StatusBadge";

function formatDate(iso: string) {
  return new Intl.DateTimeFormat("en-IN", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(iso));
}

function TaskCard({ task }: { task: TaskListItem }) {
  return (
    <Link href={`/tasks/${task.id}`} style={{ textDecoration: "none" }}>
      <div
        className="card card-shadow"
        style={{
          display: "flex",
          alignItems: "flex-start",
          justifyContent: "space-between",
          gap: 16,
          cursor: "pointer",
          transition: "transform 0.15s, box-shadow 0.15s",
          borderColor: task.status === "running" || task.status === "planning"
            ? "var(--color-amber-pending)"
            : undefined,
        }}
        onMouseEnter={(e) => {
          (e.currentTarget as HTMLElement).style.transform = "translateY(-2px)";
          (e.currentTarget as HTMLElement).style.boxShadow = "0 8px 32px rgba(12,23,84,0.12)";
        }}
        onMouseLeave={(e) => {
          (e.currentTarget as HTMLElement).style.transform = "";
          (e.currentTarget as HTMLElement).style.boxShadow = "";
        }}
      >
        <div style={{ flex: 1, minWidth: 0 }}>
          <p
            style={{
              fontSize: "var(--text-body-sm)",
              fontWeight: 500,
              color: "var(--color-charcoal)",
              marginBottom: 8,
              overflow: "hidden",
              textOverflow: "ellipsis",
              whiteSpace: "nowrap",
            }}
          >
            {task.prompt}
          </p>
          <div style={{ display: "flex", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
            <StatusBadge status={task.status} />
            {task.result_count > 0 && (
              <span style={{ fontSize: "var(--text-caption)", color: "var(--color-stone)" }}>
                {task.result_count} record{task.result_count !== 1 ? "s" : ""}
              </span>
            )}
            <span style={{ fontSize: "var(--text-caption)", color: "var(--color-stone)" }}>
              {formatDate(task.created_at)}
            </span>
          </div>
        </div>
        <span style={{ color: "var(--color-stone)", flexShrink: 0, marginTop: 2, display: "flex", alignItems: "center" }}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <polyline points="9 18 15 12 9 6" />
          </svg>
        </span>
      </div>
    </Link>
  );
}

export default function TasksPage() {
  const [tasks, setTasks] = useState<TaskListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const ACTIVE_STATUSES = new Set(["pending", "planning", "running"]);
  const hasActive = tasks.some((t) => ACTIVE_STATUSES.has(t.status));

  const loadTasks = useCallback(async () => {
    try {
      const data = await api.listTasks();
      setTasks(data);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load tasks");
    } finally {
      setLoading(false);
    }
  }, []);

  // Initial load
  useEffect(() => {
    loadTasks();
  }, [loadTasks]);

  // Poll while any task is active
  useEffect(() => {
    if (!hasActive) return;
    const interval = setInterval(loadTasks, 5000);
    return () => clearInterval(interval);
  }, [hasActive, loadTasks]);

  return (
    <div className="page-container section">
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "var(--spacing-32)" }} className="animate-in">
        <div>
          <p className="eyebrow" style={{ marginBottom: 8 }}>Workflows</p>
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <h1 style={{ fontSize: "var(--text-heading)", letterSpacing: "-0.64px" }}>Tasks</h1>
            {hasActive && (
              <span style={{ display: "inline-flex", alignItems: "center", gap: 4, fontSize: "var(--text-caption)", fontWeight: 600, color: "var(--color-amber-pending)" }}>
                <span style={{ width: 6, height: 6, borderRadius: "50%", background: "currentColor", animation: "pulse-dot 1.2s infinite", display: "inline-block" }} />
                Live
              </span>
            )}
          </div>
        </div>
        <Link href="/" className="btn btn-primary">
          + New workflow
        </Link>
      </div>

      {loading && (
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {[...Array(4)].map((_, i) => (
            <div key={i} className="skeleton" style={{ height: 80, borderRadius: 16 }} />
          ))}
        </div>
      )}

      {error && (
        <div className="card" style={{ borderColor: "var(--color-clay-error)", textAlign: "center" }}>
          <p style={{ color: "var(--color-clay-error)" }}>Failed to load tasks: {error}</p>
          <p style={{ fontSize: "var(--text-body-sm)", color: "var(--color-stone)", marginTop: 4 }}>
            Is the API running on localhost:8000?
          </p>
        </div>
      )}

      {!loading && !error && tasks.length === 0 && (
        <div className="empty-state">
          <div className="empty-state-icon">
            <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" style={{ opacity: 0.6 }} aria-hidden="true">
              <rect width="8" height="4" x="8" y="2" rx="1" ry="1" />
              <path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2" />
              <path d="M9 12h6" />
              <path d="M9 16h6" />
            </svg>
          </div>
          <h3>No workflows yet</h3>
          <p>Submit your first data request from the home page to get started.</p>
          <Link href="/" className="btn btn-primary">
            Run your first workflow
          </Link>
        </div>
      )}

      {!loading && tasks.length > 0 && (
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {tasks.map((task, i) => (
            <div key={task.id} className="animate-in" style={{ animationDelay: `${i * 0.04}s` }}>
              <TaskCard task={task} />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
