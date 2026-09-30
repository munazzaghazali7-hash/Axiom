"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { api, ResultOut, ResultWithSource, type ResultsPage as ResultsPageData } from "@/lib/api";

// ── Source Inspector Panel ─────────────────────────────────────────────────────
function SourcePanel({
  result,
  panelLoading,
  onClose,
}: {
  result: ResultWithSource | null;
  panelLoading: boolean;
  onClose: () => void;
}) {
  const source = result?.source;

  return (
    <div className={`source-panel ${(result || panelLoading) ? "open" : ""}`}>
      <div className="source-panel-header">
        <div>
          <p className="eyebrow" style={{ marginBottom: 4 }}>Source Inspector</p>
          {source && (
            <p style={{ fontSize: "var(--text-caption)", color: "var(--color-stone)", maxWidth: 300, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
              {source.url}
            </p>
          )}
        </div>
        <button
          id="close-source-panel-btn"
          onClick={onClose}
          style={{ background: "none", border: "none", cursor: "pointer", fontSize: 20, color: "var(--color-stone)", lineHeight: 1 }}
        >
          ×
        </button>
      </div>

      <div className="source-panel-body">
        {panelLoading && (
          <div style={{ display: "flex", flexDirection: "column", gap: 12, padding: "var(--spacing-24) 0" }}>
            <div className="skeleton" style={{ height: 20, width: "60%" }} />
            <div className="skeleton" style={{ height: 80 }} />
            <div className="skeleton" style={{ height: 20, width: "40%" }} />
            <div className="skeleton" style={{ height: 60 }} />
          </div>
        )}

        {!panelLoading && !result && (
          <div className="empty-state" style={{ padding: "var(--spacing-48) 0" }}>
            <div className="empty-state-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ opacity: 0.6 }}>
                <circle cx="11" cy="11" r="8" />
                <path d="m21 21-4.35-4.35" />
              </svg>
            </div>
            <p style={{ color: "var(--color-stone)" }}>Click any row to inspect its source</p>
          </div>
        )}

        {!panelLoading && result && (
          <>
            {/* Structured data */}
            <div style={{ marginBottom: "var(--spacing-24)" }}>
              <p className="eyebrow" style={{ marginBottom: 12 }}>Extracted data</p>
              <div className="card" style={{ padding: "var(--spacing-16)" }}>
                {Object.entries(result.structured_data).map(([k, v]) => (
                  <div key={k} style={{ display: "flex", gap: 12, padding: "6px 0", borderBottom: "1px solid var(--color-cream-border)" }}>
                    <span style={{ fontSize: "var(--text-caption)", fontWeight: 700, color: "var(--color-stone)", width: 110, flexShrink: 0, textTransform: "uppercase", letterSpacing: "0.06em", paddingTop: 1 }}>{k}</span>
                    <span style={{ fontSize: "var(--text-body-sm)", color: "var(--color-charcoal)", wordBreak: "break-word" }}>
                      {v == null ? <em style={{ color: "var(--color-stone)" }}>null</em> : String(v)}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Source info */}
            {source && (
              <div style={{ marginBottom: "var(--spacing-24)" }}>
                <p className="eyebrow" style={{ marginBottom: 12 }}>Source</p>
                <div className="card" style={{ padding: "var(--spacing-16)" }}>
                  <div style={{ marginBottom: 8 }}>
                    <a
                      href={source.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      style={{ fontSize: "var(--text-body-sm)", color: "var(--color-electric-cobalt)", wordBreak: "break-all" }}
                    >
                      {source.url}
                    </a>
                  </div>
                  <p style={{ fontSize: "var(--text-caption)", color: "var(--color-stone)" }}>
                    Fetched: {new Date(source.fetched_at).toLocaleString("en-IN")}
                  </p>
                  <p style={{ fontSize: "var(--text-caption)", color: "var(--color-stone)", marginTop: 4 }}>
                    Content hash: <code style={{ fontSize: 11, background: "var(--color-warm-canvas)", padding: "1px 4px", borderRadius: 4 }}>{source.content_hash.slice(0, 16)}…</code>
                  </p>
                  {source.robots_txt_allowed && (
                    <p style={{ fontSize: "var(--text-caption)", color: "var(--color-sage-success)", marginTop: 4, display: "inline-flex", alignItems: "center", gap: 5 }}>
                      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                        <polyline points="20 6 9 17 4 12" />
                      </svg>
                      robots.txt compliant
                    </p>
                  )}
                </div>
              </div>
            )}

            {/* Attestation */}
            {source?.attestation && (
              <div>
                <p className="eyebrow" style={{ marginBottom: 12 }}>Attestation</p>
                <div className="attestation-block">
                  {/* Header badge */}
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16 }}>
                    <span
                      className="verified-badge"
                      style={{
                        fontSize: "var(--text-body-sm)",
                        padding: "6px 14px",
                        gap: 8,
                        background: source.attestation.verified
                          ? "rgba(59,122,87,0.12)"
                          : "rgba(184,132,46,0.12)",
                        color: source.attestation.verified
                          ? "var(--color-sage-success)"
                          : "var(--color-amber-pending)",
                        display: "inline-flex",
                        alignItems: "center",
                      }}
                    >
                      {source.attestation.verified ? (
                        <>
                          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                            <polyline points="20 6 9 17 4 12" />
                          </svg>
                          <span>TEE-Ready Stub</span>
                        </>
                      ) : (
                        <>
                          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="spinner" aria-hidden="true">
                            <path d="M21 12a9 9 0 1 1-6.219-8.56" />
                          </svg>
                          <span>Stub Pending</span>
                        </>
                      )}
                    </span>
                    <span style={{
                      fontSize: "var(--text-caption)",
                      color: "var(--color-ink-navy)",
                      opacity: 0.5,
                      fontFamily: "monospace",
                    }}>
                      {source.attestation.signer}
                    </span>
                  </div>

                  {/* Explanation */}
                  <p style={{ fontSize: "var(--text-caption)", color: "var(--color-ink-navy)", lineHeight: 1.6, opacity: 0.7, marginBottom: 16 }}>
                    Each source is hashed at fetch time. The extracted_hash ties the record to the raw content. In production, this runs inside an AWS Nitro Enclave — hardware-signed and verifiable. The architecture is TEE-ready.
                  </p>

                  {/* Content hash */}
                  <p style={{ fontSize: "var(--text-caption)", color: "var(--color-ink-navy)", marginBottom: 4, fontWeight: 600 }}>Content hash (SHA-256 of raw page)</p>
                  <div className="attestation-hash">{source.attestation.content_hash}</div>

                  {/* Extracted hash */}
                  <p style={{ fontSize: "var(--text-caption)", color: "var(--color-ink-navy)", marginTop: 12, marginBottom: 4, fontWeight: 600 }}>Extracted hash (SHA-256 of structured record)</p>
                  <div className="attestation-hash">{source.attestation.extracted_hash}</div>

                  {/* Attestation document */}
                  {source.attestation.attestation_document && Object.keys(source.attestation.attestation_document).length > 0 && (
                    <>
                      <p style={{ fontSize: "var(--text-caption)", color: "var(--color-ink-navy)", marginTop: 12, marginBottom: 4, fontWeight: 600 }}>Attestation document</p>
                      <div className="attestation-hash" style={{ whiteSpace: "pre-wrap", maxHeight: 160, overflowY: "auto" }}>
                        {JSON.stringify(source.attestation.attestation_document, null, 2)}
                      </div>
                    </>
                  )}
                </div>
              </div>
            )}

            {/* No source */}
            {!source && (
              <div style={{ marginTop: "var(--spacing-16)" }}>
                <div className="card" style={{ textAlign: "center", padding: "var(--spacing-24)", borderColor: "var(--color-smoke)" }}>
                  <p style={{ fontSize: "var(--text-body-sm)", color: "var(--color-stone)" }}>Source data not available for this record.</p>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

// ── Results Table ──────────────────────────────────────────────────────────────
export default function ResultsPage() {
  const { id } = useParams<{ id: string }>();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [data, setData] = useState<ResultsPageData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedResult, setSelectedResult] = useState<ResultWithSource | null>(null);
  const [panelLoading, setPanelLoading] = useState(false);
  const [exporting, setExporting] = useState<"csv" | "json" | null>(null);

  // Debounce search
  useEffect(() => {
    const t = setTimeout(() => setDebouncedSearch(search), 350);
    return () => clearTimeout(t);
  }, [search]);

  useEffect(() => {
    setPage(1);
  }, [debouncedSearch]);

  const fetchResults = useCallback(async () => {
    setLoading(true);
    try {
      const result = await api.getResults(id, page, 25, debouncedSearch || undefined);
      setData(result);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load results");
    } finally {
      setLoading(false);
    }
  }, [id, page, debouncedSearch]);

  useEffect(() => { fetchResults(); }, [fetchResults]);

  const handleRowClick = async (result: ResultOut) => {
    setPanelLoading(true);
    try {
      const withSource = await api.getResultSource(result.id);
      setSelectedResult(withSource);
    } catch {
      setSelectedResult({ ...result, source: null });
    } finally {
      setPanelLoading(false);
    }
  };

  const handleExport = async (format: "csv" | "json") => {
    setExporting(format);
    try {
      const blob = await api.exportDataset(id, format);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `results-${id.slice(0, 8)}.${format}`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      alert(e instanceof Error ? e.message : "Export failed");
    } finally {
      setExporting(null);
    }
  };

  // Collect all column keys from first page of results
  const allKeys = data?.items.length
    ? Array.from(new Set(data.items.flatMap((r) => Object.keys(r.structured_data)))).slice(0, 8)
    : [];

  const totalPages = data ? Math.ceil(data.total / 25) : 0;

  return (
    <div style={{ display: "flex" }}>
      {/* Main content */}
      <div
        style={{
          flex: 1,
          minWidth: 0,
          transition: "margin-right 0.25s",
          marginRight: selectedResult ? 420 : 0,
        }}
      >
        <div className="page-container section">
          {/* Header */}
          <div style={{ marginBottom: "var(--spacing-32)" }}>
            <Link
              href={`/tasks/${id}`}
              style={{ fontSize: "var(--text-body-sm)", color: "var(--color-stone)", textDecoration: "none", display: "inline-flex", alignItems: "center", gap: 4, marginBottom: 16 }}
            >
              ← Run monitor
            </Link>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: 12 }}>
              <div>
                <p className="eyebrow" style={{ marginBottom: 8 }}>Results</p>
                <h1 style={{ fontSize: "var(--text-heading)", letterSpacing: "-0.64px" }}>
                  {data ? `${data.total} record${data.total !== 1 ? "s" : ""}` : "Results"}
                </h1>
              </div>
              <div style={{ display: "flex", gap: 8 }}>
                <button
                  id="export-csv-btn"
                  className="btn btn-ghost btn-sm"
                  onClick={() => handleExport("csv")}
                  disabled={exporting !== null}
                >
                  {exporting === "csv" ? "Exporting…" : "Export CSV"}
                </button>
                <button
                  id="export-json-btn"
                  className="btn btn-ghost btn-sm"
                  onClick={() => handleExport("json")}
                  disabled={exporting !== null}
                >
                  {exporting === "json" ? "Exporting…" : "Export JSON"}
                </button>
              </div>
            </div>
          </div>

          {/* Search */}
          <div className="search-row">
            <input
              id="results-search-input"
              type="text"
              className="input"
              placeholder="Search results…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              style={{ maxWidth: 360 }}
            />
            {search && (
              <button className="btn btn-ghost btn-sm" onClick={() => setSearch("")}>Clear</button>
            )}
          </div>

          {/* Table */}
          {loading && (
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              {[...Array(6)].map((_, i) => (
                <div key={i} className="skeleton" style={{ height: 48 }} />
              ))}
            </div>
          )}

          {error && (
            <div className="empty-state">
              <div className="empty-state-icon">
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="var(--color-clay-error)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="12" r="10" />
                  <line x1="12" y1="8" x2="12" y2="12" />
                  <line x1="12" y1="16" x2="12.01" y2="16" />
                </svg>
              </div>
              <h3>Failed to load results</h3>
              <p>{error}</p>
            </div>
          )}

          {!loading && !error && data && data.items.length === 0 && (
            <div className="empty-state">
              <div className="empty-state-icon">
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ opacity: 0.6 }}>
                  <rect width="20" height="16" x="2" y="4" rx="2" />
                  <path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7" />
                </svg>
              </div>
              <h3>{search ? "No matching results" : "No results yet"}</h3>
              <p>{search ? "Try a different search term." : "The workflow hasn't produced any results yet."}</p>
            </div>
          )}

          {!loading && data && data.items.length > 0 && (
            <div className="results-table-container">
              <table className="results-table">
                <thead>
                  <tr>
                    {allKeys.map((k) => (
                      <th key={k}>{k.replace(/_/g, " ")}</th>
                    ))}
                    <th>Source</th>
                  </tr>
                </thead>
                <tbody>
                  {data.items.map((result) => (
                    <tr
                      key={result.id}
                      onClick={() => handleRowClick(result)}
                      style={{
                        background: selectedResult?.id === result.id ? "var(--color-lavender-mist)" : undefined,
                      }}
                    >
                      {allKeys.map((k) => (
                        <td key={k} title={String(result.structured_data[k] ?? "")}>
                          {result.structured_data[k] == null ? (
                            <span style={{ color: "var(--color-stone)" }}>—</span>
                          ) : (
                            String(result.structured_data[k]).slice(0, 60)
                          )}
                        </td>
                      ))}
                      <td>
                        <span style={{ color: "var(--color-electric-cobalt)", fontSize: "var(--text-caption)" }}>
                          View →
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>

              {/* Pagination */}
              <div className="pagination">
                <p className="pagination-info">
                  {(page - 1) * 25 + 1}–{Math.min(page * 25, data.total)} of {data.total}
                </p>
                <div style={{ display: "flex", gap: 8 }}>
                  <button
                    className="btn btn-ghost btn-sm"
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    disabled={page === 1}
                  >
                    ← Prev
                  </button>
                  <button
                    className="btn btn-ghost btn-sm"
                    onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                    disabled={page >= totalPages}
                  >
                    Next →
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Source Inspector */}
      <SourcePanel result={selectedResult} panelLoading={panelLoading} onClose={() => setSelectedResult(null)} />
    </div>
  );
}
