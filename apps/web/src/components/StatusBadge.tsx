import type { RunStatus } from "@/lib/api";

const LABELS: Record<RunStatus, string> = {
  pending: "Pending",
  planning: "Planning",
  running: "Running",
  completed: "Completed",
  failed: "Failed",
  cancelled: "Cancelled",
};

export function StatusBadge({ status }: { status: RunStatus }) {
  return (
    <span className={`badge badge-${status}`}>
      <span className="badge-dot" />
      {LABELS[status]}
    </span>
  );
}

function SearchIcon() {
  return (
    <svg
      width="13"
      height="13"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <circle cx="11" cy="11" r="8" />
      <path d="m21 21-4.35-4.35" />
    </svg>
  );
}

function ExtractIcon() {
  return (
    <svg
      width="13"
      height="13"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2.2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d="M12 5a3 3 0 1 0-5.997.125 4 4 0 0 0-2.526 5.77 4 4 0 0 0 .556 6.588A4 4 0 1 0 12 18Z" />
      <path d="M12 5a3 3 0 1 1 5.997.125 4 4 0 0 1 2.526 5.77 4 4 0 0 1-.556 6.588A4 4 0 1 1 12 18Z" />
      <path d="M12 5v13" />
    </svg>
  );
}

function FetchIcon() {
  return (
    <svg
      width="13"
      height="13"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2.2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
      <polyline points="7 10 12 15 17 10" />
      <line x1="12" x2="12" y1="15" y2="3" />
    </svg>
  );
}

export function StepTypeIcon({ type }: { type: string }) {
  const norm = type.toLowerCase();
  if (norm === "search") return <SearchIcon />;
  if (norm === "extract") return <ExtractIcon />;
  if (norm === "fetch") return <FetchIcon />;
  return null;
}

export function HourglassIcon({
  size = 18,
  color = "currentColor",
  className = "",
}: {
  size?: number;
  color?: string;
  className?: string;
}) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke={color}
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
    >
      <path d="M5 22h14" />
      <path d="M5 2h14" />
      <path d="M17 22v-4.172a2 2 0 0 0-.586-1.414L12 12l-4.414 4.414A2 2 0 0 0 7 17.828V22" />
      <path d="M7 2v4.172a2 2 0 0 0 .586 1.414L12 12l4.414-4.414A2 2 0 0 0 17 6.172V2" />
    </svg>
  );
}

export function StepStatusIcon({ status }: { status: string }) {
  switch (status) {
    case "completed":
      return (
        <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <polyline points="20 6 9 17 4 12" />
        </svg>
      );
    case "running":
      return (
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="spinner" aria-hidden="true">
          <path d="M21 12a9 9 0 1 1-6.219-8.56" />
        </svg>
      );
    case "failed":
      return (
        <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <line x1="18" y1="6" x2="6" y2="18" />
          <line x1="6" y1="6" x2="18" y2="18" />
        </svg>
      );
    case "skipped":
      return (
        <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <line x1="5" y1="12" x2="19" y2="12" />
        </svg>
      );
    case "pending":
    default:
      return (
        <svg width="8" height="8" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" aria-hidden="true">
          <circle cx="12" cy="12" r="8" />
        </svg>
      );
  }
}

interface StepItemProps {
  stepType: string;
  description: string;
  status: string;
  sourceUrl?: string | null;
  errorMessage?: string | null;
}

export function StepItem({ stepType, description, status, sourceUrl, errorMessage }: StepItemProps) {
  return (
    <div className={`step-item ${status}`}>
      <div className={`step-icon step-icon-${status}`}>
        <StepStatusIcon status={status} />
      </div>
      <div className="step-body">
        <div className="step-type-label">
          <span>{stepType}</span>
          <StepTypeIcon type={stepType} />
        </div>
        <div className="step-description">{description}</div>
        {sourceUrl && (
          <div className="step-url">{sourceUrl}</div>
        )}
        {errorMessage && (
          <div style={{ fontSize: "var(--text-caption)", color: "var(--color-clay-error)", marginTop: 4 }}>
            {errorMessage}
          </div>
        )}
      </div>
    </div>
  );
}
