"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import { HourglassIcon } from "@/components/StatusBadge";

const EXAMPLE_PROMPTS = [
  "Find 20 Python developer jobs in Bangalore",
  "Collect YC W24 startup names & founders",
  "List AI/ML conferences in 2025 with dates",
  "Find SaaS Series A rounds from Q1 2024",
];

const HOW_STEPS = [
  {
    n: "01",
    title: "Describe in plain English",
    body: "No schema design, no code. Just say what data you need — the AI handles the rest.",
    variant: "card-dark",
  },
  {
    n: "02",
    title: "AI plans & executes",
    body: "Gemini designs the collection workflow. Agents search, fetch, and extract — respecting robots.txt at every step.",
    variant: "card",
  },
  {
    n: "03",
    title: "Verified, source-backed data",
    body: "Every result links to its source URL with a cryptographic attestation — provably not fabricated.",
    variant: "card-accent",
  },
];

export default function HomePage() {
  const router = useRouter();
  const [prompt, setPrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim() || loading) return;
    setLoading(true);
    setError(null);
    try {
      const task = await api.submitTask(prompt.trim());
      router.push(`/tasks/${task.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to submit task");
      setLoading(false);
    }
  };

  const charWarn = prompt.length > 1600;

  return (
    <div className="page-container">
      {/* ── Hero ─────────────────────────────────────────────────────────── */}
      <div className="hero">
        <div className="hero-grid">
          {/* Left: copy + prompt intake */}
          <div>
            <p className="eyebrow hero-eyebrow animate-in">
              Code Cubicle 6.0 · Axiom
            </p>
            <h1 className="hero-title animate-in animate-in-delay-1">
              Collect <em>any</em> data<br />in one sentence
            </h1>
            <p className="hero-sub animate-in animate-in-delay-2">
              Describe what you need in plain English. Axiom autonomously plans a collection
              workflow, executes it against permitted sources, and delivers
              clean, <em style={{ fontFamily: "var(--font-display)", fontStyle: "italic", color: "var(--color-ink-navy)" }}>source-backed</em> structured data with cryptographic proof.
            </p>

            {/* Prompt intake box */}
            <form onSubmit={handleSubmit} className="animate-in animate-in-delay-3">
              <div className="prompt-box">
                <textarea
                  id="prompt-input"
                  placeholder="Describe the data you need… e.g. 'Find 20 Python developer job openings in Bangalore'"
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) handleSubmit(e as unknown as React.FormEvent);
                  }}
                  rows={3}
                  maxLength={2000}
                />

                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 8 }}>
                  <div className="prompt-chips">
                    {EXAMPLE_PROMPTS.map((p) => (
                      <button
                        key={p}
                        type="button"
                        className="prompt-chip"
                        onClick={() => setPrompt(p)}
                      >
                        {p.length > 38 ? p.slice(0, 38) + "…" : p}
                      </button>
                    ))}
                  </div>

                  <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                    {prompt.length > 0 && (
                      <span className={`char-count${charWarn ? " warn" : ""}`}>
                        {prompt.length}/2000
                      </span>
                    )}
                    <button
                      id="submit-prompt-btn"
                      type="submit"
                      className="btn btn-primary"
                      disabled={!prompt.trim() || loading}
                    >
                      {loading ? (
                        <>
                          <HourglassIcon size={14} className="hourglass-animated" />
                          <span>Planning…</span>
                        </>
                      ) : (
                        <>
                          <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                            <polygon points="5 3 19 12 5 21 5 3" />
                          </svg>
                          <span>Run workflow</span>
                        </>
                      )}
                    </button>
                  </div>
                </div>

                {error && (
                  <div style={{ display: "flex", alignItems: "center", gap: 6, color: "var(--color-clay-error)", fontSize: "var(--text-body-sm)" }}>
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                      <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z" />
                      <line x1="12" y1="9" x2="12" y2="13" />
                      <line x1="12" y1="17" x2="12.01" y2="17" />
                    </svg>
                    <span>{error}</span>
                  </div>
                )}
              </div>
              <p style={{ fontSize: "var(--text-caption)", color: "var(--color-stone)", marginTop: 8 }}>
                Cmd+Enter to run · Ctrl+Enter on Windows
              </p>
            </form>
          </div>

          {/* Right: feature cards */}
          <div style={{ display: "flex", flexDirection: "column", gap: 16 }} className="animate-in animate-in-delay-2">
            <div className="card-dark card-hover">
              <div style={{
                display: "inline-flex", alignItems: "center", justifyContent: "center",
                width: 32, height: 32, borderRadius: "50%",
                background: "var(--color-electric-cobalt)", fontSize: 14, marginBottom: 12, fontWeight: 700, color: "#fff",
              }}>1</div>
              <h4 style={{ color: "#fff", marginBottom: 8 }}>Describe in plain English</h4>
              <p style={{ color: "rgba(255,255,255,0.7)", fontSize: "var(--text-body-sm)", lineHeight: 1.6 }}>
                No schema design, no code. Just say what data you need and where it should come from.
              </p>
            </div>

            <div className="card card-hover">
              <div style={{
                display: "inline-flex", alignItems: "center", justifyContent: "center",
                width: 32, height: 32, borderRadius: "50%",
                background: "var(--color-electric-cobalt)", fontSize: 14, marginBottom: 12, fontWeight: 700, color: "#fff",
              }}>2</div>
              <h4 style={{ marginBottom: 8 }}>AI plans &amp; executes</h4>
              <p style={{ fontSize: "var(--text-body-sm)", lineHeight: 1.6 }}>
                Gemini designs the collection workflow. Agents search, fetch, and extract — respecting robots.txt.
              </p>
            </div>

            <div className="card-accent card-hover">
              <div style={{
                display: "inline-flex", alignItems: "center", justifyContent: "center",
                width: 32, height: 32, borderRadius: "50%",
                background: "var(--color-electric-cobalt)", fontSize: 14, marginBottom: 12, fontWeight: 700, color: "#fff",
              }}>3</div>
              <h4 style={{ marginBottom: 8 }}>Verified, source-backed data</h4>
              <p style={{ fontSize: "var(--text-body-sm)", lineHeight: 1.6 }}>
                Every result links to its source URL with a cryptographic attestation — provably not fabricated.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* ── Stats bar ────────────────────────────────────────────────────── */}
      <div className="stats-bar animate-in animate-in-delay-4">
        {[
          { value: "< 60s", label: "Average time to first result" },
          { value: "3-step", label: "Pipeline: search → fetch → extract" },
          { value: "100%", label: "Results source-linked & attestable" },
          { value: "0 code", label: "Required from the user" },
        ].map(({ value, label }) => (
          <div key={label} className="stat-item">
            <div className="stat-value">{value}</div>
            <div className="stat-label">{label}</div>
          </div>
        ))}
      </div>

      {/* ── How it works ─────────────────────────────────────────────────── */}
      <div className="section">
        <p className="eyebrow" style={{ marginBottom: 12 }}>How it works</p>
        <h2 style={{ fontSize: "var(--text-heading)", letterSpacing: "-0.64px", maxWidth: 480 }}>
          From plain-English prompt to{" "}
          <span style={{ fontFamily: "var(--font-display)", fontStyle: "italic", fontWeight: 400, color: "var(--color-electric-cobalt)" }}>structured data</span>{" "}
          in minutes
        </h2>

        <div className="how-steps">
          {HOW_STEPS.map(({ n, title, body, variant }, i) => (
            <div
              key={n}
              className={`${variant} card-hover animate-in`}
              style={{ animationDelay: `${0.1 * (i + 1)}s` }}
            >
              <div className="how-step-number">{n}</div>
              <h4 style={{
                marginBottom: 10,
                color: variant === "card-dark" ? "#fff" : "var(--color-charcoal)",
              }}>{title}</h4>
              <p style={{
                fontSize: "var(--text-body-sm)",
                lineHeight: 1.65,
                color: variant === "card-dark" ? "rgba(255,255,255,0.7)" : "var(--color-graphite)",
              }}>{body}</p>
            </div>
          ))}
        </div>
      </div>

      {/* ── Trust bar (dark CTA) ─────────────────────────────────────────── */}
      <div className="trust-bar animate-in animate-in-delay-3">
        <div>
          <p className="trust-bar-title">
            Every record is traceable to its source
          </p>
          <p className="trust-bar-sub">
            The source inspector shows you the exact URL, fetch timestamp, content hash, and stub attestation for any result — making "trust, but verify" actually possible.
          </p>
        </div>
        <div style={{ display: "flex", gap: 12, flexShrink: 0, flexWrap: "wrap" }}>
          <Link href="/history" className="btn btn-ghost btn-sm" style={{ borderColor: "rgba(255,255,255,0.2)", color: "#fff" }}>
            View history
          </Link>
          <button
            onClick={() => document.getElementById("prompt-input")?.focus()}
            className="btn btn-primary"
          >
            Try it now →
          </button>
        </div>
      </div>

      <div style={{ height: "var(--spacing-80)" }} />
    </div>
  );
}
