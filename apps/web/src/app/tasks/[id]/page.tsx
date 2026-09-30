"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { api, TaskOut } from "@/lib/api";
import { StatusBadge, StepItem, HourglassIcon } from "@/components/StatusBadge";

const POLL_INTERVAL = 3000; // 3 seconds

function formatDate(iso: string) {
  return new Intl.DateTimeFormat("en-IN", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  }).format(new Date(iso));
}

export default function TaskDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [task, setTask] = useState<TaskOut | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [cancelling, setCancelling] = useState(false);

  const isActive = (status: string) =>
    ["pending", "planning", "running"].includes(status);

  const fetchTask = useCallback(async () => {
    try {
      const data = await api.getTask(id);
      setTask(data);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load task");
    } finally {
      setLoading(false);
    }
  }, [id]);

  // Poll while active
  useEffect(() => {
    fetchTask();
    const interval = setInterval(() => {
      if (task && !isActive(task.status)) return;
      fetchTask();
    }, POLL_INTERVAL);
    return () => clearInterval(interval);
  }, [fetchTask, task?.status]);

  const handleCancel = async () => {
    if (!task || cancelling) return;
    setCancelling(true);
    try {
      const updated = await api.cancelTask(id);
      setTask(updated);
    } catch (e) {
      alert(e instanceof Error ? e.message : "Cancel failed");
    } finally {
      setCancelling(false);
    }
  };

  if (loading) {
    return (
      <div className="page-container section">
        <div className="skeleton" style={{ height: 40, width: 300, marginBottom: 16 }} />
        <div className="skeleton" style={{ height: 24, width: 200, marginBottom: 32 }} />
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {[...Array(4)].map((_, i) => (
            <div key={i} className="skeleton" style={{ height: 72 }} />
          ))}
        </div>
      </div>
    );
  }

  if (error || !task) {
    return (
      <div className="page-container section">
        <div className="empty-state">
          <div className="empty-state-icon">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="var(--color-clay-error)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
          </div>
          <h3>Task not found</h3>
          <p>{error ?? "This task doesn't exist or was deleted."}</p>
          <Link href="/tasks" className="btn btn-ghost">← Back to tasks</Link>
        </div>
      </div>
    );
  }

  const plan = task.plan as Record<string, unknown> | null;

  return (
    <div className="page-container section">
      {/* Header */}
      <div style={{ marginBottom: "var(--spacing-32)" }} className="animate-in">
        <Link
          href="/tasks"
          style={{ fontSize: "var(--text-body-sm)", color: "var(--color-stone)", textDecoration: "none", display: "inline-flex", alignItems: "center", gap: 4, marginBottom: 16 }}
        >
          ← Tasks
        </Link>
        <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 16, flexWrap: "wrap" }}>
          <div>
            <p className="eyebrow" style={{ marginBottom: 8 }}>Workflow run</p>
            <h1 style={{ fontSize: "var(--text-heading)", letterSpacing: "-0.64px", marginBottom: 12, maxWidth: 700 }}>
              {task.prompt}
            </h1>
            <div style={{ display: "flex", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
              <StatusBadge status={task.status} />
              <span style={{ fontSize: "var(--text-caption)", color: "var(--color-stone)" }}>
                Started {formatDate(task.created_at)}
              </span>
              {task.completed_at && (
                <span style={{ fontSize: "var(--text-caption)", color: "var(--color-stone)" }}>
                  · Completed {formatDate(task.completed_at)}
                </span>
              )}
            </div>
          </div>

          <div style={{ display: "flex", gap: 8, flexShrink: 0 }}>
            {isActive(task.status) && (
              <button
                id="cancel-task-btn"
                className="btn btn-danger btn-sm"
                onClick={handleCancel}
                disabled={cancelling}
              >
                {cancelling ? "Cancelling…" : "Cancel"}
              </button>
            )}
            {task.status === "completed" && task.result_count > 0 && (
              <Link href={`/tasks/${task.id}/results`} className="btn btn-primary btn-sm">
                View {task.result_count} results →
              </Link>
            )}
          </div>
        </div>
      </div>

      {/* Error banner */}
      {task.error_message && (
        <div className="card" style={{ borderColor: "var(--color-clay-error)", marginBottom: 24, background: "rgba(163,64,47,0.04)" }}>
          <p style={{ color: "var(--color-clay-error)", fontWeight: 500, marginBottom: 4 }}>Workflow error</p>
          <p style={{ fontSize: "var(--text-body-sm)", color: "var(--color-graphite)" }}>{task.error_message}</p>
        </div>
      )}

      <div style={{ display: "grid", gridTemplateColumns: plan ? "1fr 340px" : "1fr", gap: "var(--spacing-32)", alignItems: "start" }}>
        {/* Steps */}
        <div>
          <h2 style={{ fontSize: "var(--text-subheading)", fontWeight: 600, marginBottom: 16 }}>
            {task.steps.length > 0 ? "Execution steps" : "Waiting to start…"}
          </h2>

          {task.steps.length === 0 && isActive(task.status) && (
            <div className="card" style={{ textAlign: "center", padding: "var(--spacing-48)" }}>
              <div style={{ display: "flex", justifyContent: "center", marginBottom: 16 }}>
                <HourglassIcon
                  size={40}
                  color="var(--color-electric-cobalt)"
                  className="hourglass-animated"
                />
              </div>
              <p style={{ color: "var(--color-stone)", fontSize: "var(--text-body-sm)" }}>
                {task.status === "pending" ? "Queued — waiting for worker" : "Planning your workflow with Gemini…"}
              </p>
            </div>
          )}

          <div className="step-list">
            {task.steps.map((step) => (
              <StepItem
                key={step.id}
                stepType={step.step_type}
                description={step.description}
                status={step.status}
                sourceUrl={step.source_url}
                errorMessage={step.error_message}
              />
            ))}
          </div>

          {/* Partial-run warning: completed but some steps failed */}
          {task.status === "completed" && task.steps.some((s) => s.status === "failed") && task.result_count > 0 && (
            <div className="card" style={{ borderColor: "var(--color-amber-pending)", background: "rgba(184,132,46,0.04)", marginTop: 16 }}>
              <p style={{ color: "var(--color-amber-pending)", fontWeight: 500, marginBottom: 4 }}>Partial results</p>
              <p style={{ fontSize: "var(--text-body-sm)", color: "var(--color-graphite)" }}>
                {task.steps.filter((s) => s.status === "failed").length} step(s) failed — results shown are from successful sources only.
              </p>
            </div>
          )}

          {task.status === "cancelled" && (
            <div className="card" style={{ borderColor: "var(--color-smoke)", background: "var(--color-warm-canvas)", marginTop: 16, textAlign: "center", padding: "var(--spacing-48)" }}>
              <div style={{ display: "flex", justifyContent: "center", marginBottom: 12 }}>
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="var(--color-stone)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="12" r="10" />
                  <line x1="4.93" y1="4.93" x2="19.07" y2="19.07" />
                </svg>
              </div>
              <h3 style={{ fontSize: "var(--text-subheading)", fontWeight: 600, marginBottom: 8 }}>Run cancelled</h3>
              <p style={{ fontSize: "var(--text-body-sm)", color: "var(--color-stone)" }}>This workflow was cancelled before it completed.</p>
            </div>
          )}

          {task.status === "completed" && task.result_count === 0 && (
            <div className="empty-state" style={{ padding: "var(--spacing-48) 0" }}>
              <div className="empty-state-icon">
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ opacity: 0.6 }}>
                  <rect width="20" height="16" x="2" y="4" rx="2" />
                  <path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7" />
                </svg>
              </div>
              <h3>No results collected</h3>
              <p>The workflow completed but found no extractable records. Try a more specific prompt.</p>
            </div>
          )}
        </div>

        {/* Plan sidebar */}
        {plan && (
          <div>
            <div className="card-dark">
              <p style={{ fontSize: "var(--text-caption)", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", color: "rgba(255,255,255,0.5)", marginBottom: 12 }}>
                Workflow plan
              </p>
              <p style={{ fontSize: "var(--text-body-sm)", fontWeight: 600, color: "#fff", marginBottom: 8 }}>
                {String(plan.title ?? "")}
              </p>
              <p style={{ fontSize: "var(--text-caption)", color: "rgba(255,255,255,0.65)", lineHeight: 1.5, marginBottom: 16 }}>
                {String(plan.description ?? "")}
              </p>
              {Array.isArray(plan.target_sources) && (
                <div>
                  <p style={{ fontSize: "var(--text-caption)", color: "rgba(255,255,255,0.4)", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 8 }}>
                    Sources
                  </p>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                    {(plan.target_sources as string[]).map((s) => (
                      <span key={s} className="badge" style={{ background: "rgba(255,255,255,0.1)", color: "rgba(255,255,255,0.8)" }}>
                        {s}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              {typeof plan.estimated_records === "number" && (
                <p style={{ fontSize: "var(--text-caption)", color: "rgba(255,255,255,0.4)", marginTop: 12 }}>
                  ~{plan.estimated_records} estimated records
                </p>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
