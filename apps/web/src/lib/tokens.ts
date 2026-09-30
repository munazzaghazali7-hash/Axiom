/**
 * Design system tokens from DESIGN.md
 * Used across the entire frontend — no ad-hoc hex values in components.
 */

export const colors = {
  inkNavy: "#0c1754",
  electricCobalt: "#2545ff",
  charcoal: "#171417",
  warmCanvas: "#f9f8f6",
  paperWhite: "#ffffff",
  creamBorder: "#f0e9e1",
  graphite: "#222222",
  stone: "#969696",
  smoke: "#cccccc",
  lavenderMist: "#eaebf8",
  // Status
  sageSuccess: "#3b7a57",
  amberPending: "#b8842e",
  clayError: "#a3402f",
} as const;

export const statusColor = {
  pending: colors.amberPending,
  planning: colors.electricCobalt,
  running: colors.amberPending,
  completed: colors.sageSuccess,
  failed: colors.clayError,
  cancelled: colors.stone,
} as const;

export const statusLabel = {
  pending: "Pending",
  planning: "Planning",
  running: "Running",
  completed: "Completed",
  failed: "Failed",
  cancelled: "Cancelled",
} as const;

export type RunStatus = keyof typeof statusColor;
