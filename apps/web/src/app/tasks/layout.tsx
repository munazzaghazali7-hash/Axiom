import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Tasks — Axiom",
  description: "View and manage all your data collection workflows",
};

export default function TasksLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
