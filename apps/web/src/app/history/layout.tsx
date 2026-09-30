import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "History — Axiom",
  description: "Browse past data collection workflows and revisit their results",
};

export default function HistoryLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
