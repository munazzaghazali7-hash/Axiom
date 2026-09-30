"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export function NavBar() {
  const pathname = usePathname();

  return (
    <nav className="navbar">
      <div className="navbar-inner">
        <Link href="/" className="navbar-logo" style={{ textDecoration: "none" }}>
          <span className="logo-dot" />
          Axiom
        </Link>

        <div className="navbar-links">
          <Link
            href="/tasks"
            className={`nav-link ${pathname.startsWith("/tasks") ? "active" : ""}`}
          >
            Tasks
          </Link>
          <Link
            href="/history"
            className={`nav-link ${pathname === "/history" ? "active" : ""}`}
          >
            History
          </Link>
          <Link href="/" className="btn btn-primary btn-sm">
            Run workflow
          </Link>
        </div>
      </div>
    </nav>
  );
}
