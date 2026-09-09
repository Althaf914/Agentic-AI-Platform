import { useState, useEffect, useMemo, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { listMemory, updateMemoryStatus } from "@/api/memory";
import { useMemorySearchGet } from "@/hooks/useMemory";
import type { MemoryEntry, OutreachStatus, MemorySearchResult } from "@/types/memory";
import { OUTREACH_STATUS_LABELS, OUTREACH_STATUS_COLORS } from "@/types/memory";

// ═══════════════════════════════════════════════════════════════════════════════
//  Constants / Helpers
// ═══════════════════════════════════════════════════════════════════════════════

type Tab = "timeline" | "search";

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-US", {
    month: "short", day: "numeric", year: "numeric",
  });
}

function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  if (days < 7) return `${days}d ago`;
  return formatDate(iso);
}

/** Group entries into weekly buckets. */
function groupByWeek(entries: MemoryEntry[]): { label: string; entries: MemoryEntry[] }[] {
  const groups: { label: string; ts: number; entries: MemoryEntry[] }[] = [];
  const now = new Date();
  const oneWeek = 7 * 24 * 60 * 60 * 1000;

  for (const e of entries) {
    const d = new Date(e.created_at);
    const diff = now.getTime() - d.getTime();
    let label: string;

    if (diff < oneWeek) label = "This week";
    else if (diff < 2 * oneWeek) label = "Last week";
    else {
      const month = d.toLocaleDateString("en-US", { month: "long", year: "numeric" });
      label = month;
    }
    const existing = groups.find((g) => g.label === label);
    if (existing) existing.entries.push(e);
    else groups.push({ label, ts: d.getTime(), entries: [e] });
  }

  groups.sort((a, b) => b.ts - a.ts);
  return groups.map(({ label, entries }) => ({ label, entries }));
}

function getInitials(name: string): string {
  const parts = name.split(" ").filter(Boolean);
  if (parts.length >= 2) {
    return `${parts[0][0]}${parts[parts.length - 1][0]}`.toUpperCase();
  }
  return name.slice(0, 2).toUpperCase();
}

function extractDomain(summary: string): string {
  const match = summary.match(/([a-z0-9]([a-z0-9-]*[a-z0-9])?\.)+[a-z]{2,}/i);
  return match ? match[0] : "";
}

function extractCompanyName(summary: string): string {
  const firstLine = summary.split("\n")[0];
  
  // Try matching: "Discovered and processed SkillForge (skillforge.io)..."
  const discMatch = firstLine.match(/Discovered\s+and\s+processed\s+([^(\n.]+)/i);
  if (discMatch && discMatch[1]) {
    const name = discMatch[1].trim();
    const parenIndex = name.indexOf("(");
    if (parenIndex !== -1) {
      return name.slice(0, parenIndex).trim();
    }
    return name;
  }
  
  const name = firstLine.replace(/^(Approved outreach for|Memory written for)\s+/i, "").trim();
  const parenIndex = name.indexOf("(");
  if (parenIndex !== -1) {
    return name.slice(0, parenIndex).trim();
  }
  return name || "Unknown";
}

function extractScore(meta: Record<string, unknown> | null | undefined): number | null {
  if (!meta) return null;
  const score = meta.score ?? meta.qualification_score;
  return score != null ? Number(score) : null;
}

function extractTier(meta: Record<string, unknown> | null | undefined): string | null {
  if (!meta) return null;
  return (meta.tier as string) ?? null;
}

function tierBadge(tier: string | null): { label: string; cls: string } | null {
  if (!tier || tier === "discard") return null;
  const map: Record<string, { label: string; cls: string }> = {
    A: { label: "A", cls: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30" },
    B: { label: "B", cls: "bg-amber-500/15 text-amber-400 border-amber-500/30" },
    C: { label: "C", cls: "bg-zinc-500/15 text-zinc-400 border-zinc-500/30" },
  };
  return map[tier] ?? null;
}

function getOutreachStatus(meta: Record<string, unknown> | null | undefined): OutreachStatus | null {
  if (!meta) return null;
  return (meta.outreach_status as OutreachStatus) ?? null;
}

// ═══════════════════════════════════════════════════════════════════════════════
//  Status badge with dropdown
// ════════��══════════════════════════════════════════════════════════════════════

function StatusBadge({ memoryId, currentStatus, onUpdate }: {
  memoryId: string;
  currentStatus: OutreachStatus | null;
  onUpdate: (id: string, status: OutreachStatus) => void;
}) {
  const [open, setOpen] = useState(false);
  const statuses: OutreachStatus[] = ["outreach_sent", "replied", "in_pipeline", "closed"];

  const display = currentStatus ? OUTREACH_STATUS_LABELS[currentStatus] : "Set status";
  const color = currentStatus ? OUTREACH_STATUS_COLORS[currentStatus] : "bg-zinc-500/10 text-zinc-400";

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(!open)}
        className={`text-[9px] px-2 py-0.5 rounded-full border font-medium transition-colors ${color}`}
      >
        {display} ▼
      </button>
      {open && (
        <>
          <div className="fixed inset-0 z-10" onClick={() => setOpen(false)} />
          <div className="absolute right-0 top-full mt-1 z-20 rounded-lg border py-1 shadow-xl min-w-[130px]"
            style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
            {statuses.map((s) => (
              <button
                key={s}
                onClick={() => { onUpdate(memoryId, s); setOpen(false); }}
                className={`w-full text-left px-3 py-1.5 text-[10px] transition-colors hover:bg-[--bg-secondary] ${
                  s === currentStatus ? "text-white font-medium" : "text-[--text-secondary]"
                }`}
              >
                {OUTREACH_STATUS_LABELS[s]}
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
//  Timeline entry card
// ═══════════════════════════════════════════════════════════════════════════════

function TimelineCard({ entry, onStatusUpdate, onClick }: {
  entry: MemoryEntry;
  onStatusUpdate: (id: string, status: OutreachStatus) => void;
  onClick: () => void;
}) {
  const meta = entry.metadata_json ?? {};
  const summary = entry.summary;
  const domain = extractDomain(summary);
  const companyName = extractCompanyName(summary);
  const score = extractScore(meta);
  const tier = extractTier(meta);
  const badge = tierBadge(tier);
  const status = getOutreachStatus(meta);
  const campaignName = (meta.campaign ?? meta.campaign_name ?? "") as string;
  const trigger = (meta.market_trigger ?? meta.trigger_summary ?? "") as string;

  return (
    <div
      onClick={onClick}
      className="rounded-xl border p-3.5 transition-all duration-200 hover:border-[#4f7cff]/40 cursor-pointer"
      style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}
    >
      <div className="flex items-start gap-3">
        <div className="w-9 h-9 rounded-lg bg-[#4f7cff]/20 text-[#4f7cff] flex items-center justify-center text-xs font-bold shrink-0">
          {getInitials(companyName)}
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-sm font-semibold text-white">{companyName}</span>
            {badge && <span className={`text-[9px] px-1.5 py-0.5 rounded-full border font-semibold ${badge.cls}`}>{badge.label}</span>}
            {score != null && (
              <span className={`text-xs font-bold ${score >= 80 ? "text-emerald-400" : score >= 60 ? "text-amber-400" : "text-red-400"}`}>
                {Math.round(score)}
              </span>
            )}
            <span className="ml-auto"><StatusBadge memoryId={entry.id} currentStatus={status} onUpdate={onStatusUpdate} /></span>
          </div>

          <div className="flex items-center gap-2 mt-1">
            {domain && (
              <a href={`https://${domain}`} target="_blank" rel="noreferrer"
                className="text-[10px] text-[#4f7cff] hover:underline" onClick={(e) => e.stopPropagation()}>
                {domain} ↗
              </a>
            )}
            {campaignName && <span className="text-[10px] text-[--text-muted]">from {campaignName}</span>}
            <span className="text-[10px] text-[--text-muted] ml-auto">{timeAgo(entry.created_at)}</span>
          </div>

          {trigger && (
            <div className="mt-1.5 flex items-start gap-1.5">
              <span className="text-[10px] text-amber-400 shrink-0">⚡</span>
              <p className="text-[10px] text-amber-300/80 leading-relaxed line-clamp-2">{trigger}</p>
            </div>
          )}

          {summary && (
            <p className="text-[10px] text-[--text-muted] mt-1 line-clamp-1">{summary.slice(0, 150)}</p>
          )}
        </div>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
//  Search result card
// ═══════════════════════════════════════��═══════════════════════════════════════

function SearchResultCard({ result }: { result: MemorySearchResult }) {
  const meta = result.metadata ?? {};
  const summary = result.summary;
  const domain = extractDomain(summary);
  const companyName = extractCompanyName(summary);
  const score = extractScore(meta);
  const tier = extractTier(meta);
  const badge = tierBadge(tier);
  const campaignName = (meta.campaign ?? meta.campaign_name ?? "") as string;
  const distance = result.distance;
  const similarityPct = distance != null ? Math.round((1 - distance) * 100) : null;

  return (
    <div
      className="rounded-xl border p-4 transition-all duration-200 hover:border-[#4f7cff]/40"
      style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}
    >
      <div className="flex items-start gap-3">
        {similarityPct != null && (
          <div className="shrink-0 w-10 h-10 rounded-full flex items-center justify-center text-xs font-bold border-2"
            style={{
              borderColor: similarityPct >= 80 ? "#22d3a5" : similarityPct >= 60 ? "#f59e0b" : "#6b7280",
              color: similarityPct >= 80 ? "#22d3a5" : similarityPct >= 60 ? "#f59e0b" : "#6b7280",
            }}>
            {similarityPct}%
          </div>
        )}

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-sm font-semibold text-white">{companyName}</span>
            {badge && <span className={`text-[9px] px-1.5 py-0.5 rounded-full border font-semibold ${badge.cls}`}>{badge.label}</span>}
            {score != null && (
              <span className={`text-xs font-bold ${score >= 80 ? "text-emerald-400" : "text-amber-400"}`}>{Math.round(score)}</span>
            )}
          </div>
          {domain && (
            <a href={`https://${domain}`} target="_blank" rel="noreferrer"
              className="text-[10px] text-[#4f7cff] hover:underline">{domain} ↗</a>
          )}

          <div className="mt-2 rounded-lg px-3 py-2 text-[10px] leading-relaxed" style={{ backgroundColor: "var(--bg-secondary)" }}>
            <span className="text-emerald-400 font-medium">Matched because:</span>{' '}
            <span className="text-[--text-secondary]">{summary.slice(0, 200)}</span>
          </div>

          <div className="flex items-center gap-3 mt-2 text-[10px] text-[--text-muted]">
            {campaignName && <span>Campaign: {campaignName}</span>}
            {result.last_seen && <span>Approved: {formatDate(result.last_seen)}</span>}
          </div>
        </div>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
//  Main Page
// ═══════════════════════════════════════════════════════════════════════════════

export default function Memory() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [tab, setTab] = useState<Tab>("timeline");
  const [searchQuery, setSearchQuery] = useState("");
  const [debouncedQuery, setDebouncedQuery] = useState("");
  const [selectedEntry, setSelectedEntry] = useState<MemoryEntry | null>(null);

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedQuery(searchQuery), 300);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  const { data: allEntries, isLoading: timelineLoading } = useQuery({
    queryKey: ["memory-list"],
    queryFn: () => listMemory(100),
    refetchInterval: 30_000,
  });

  const { data: searchData, isLoading: searchLoading } = useMemorySearchGet(debouncedQuery);

  const companyEntries = useMemo(() => {
    return (allEntries ?? []).filter((e) => e.entity_type === "company");
  }, [allEntries]);

  const timelineGroups = useMemo(() => groupByWeek(companyEntries), [companyEntries]);

  const statusMutation = useMutation({
    mutationFn: ({ memoryId, status }: { memoryId: string; status: OutreachStatus }) =>
      updateMemoryStatus(memoryId, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["memory-list"] });
    },
  });

  const handleStatusUpdate = useCallback((id: string, status: OutreachStatus) => {
    statusMutation.mutate({ memoryId: id, status });
  }, [statusMutation]);

  const examples = [
    "cloud infrastructure startup Series B",
    "AI company hiring machine learning engineers",
    "security tool enterprise 500 employees",
  ];

  return (
    <div className="h-full flex flex-col gap-4">
      <div className="flex items-center justify-between shrink-0">
        <h2 className="text-xl font-bold text-white">Memory</h2>
        <div className="flex gap-2">
          <button
            onClick={() => setTab("timeline")}
            className={`px-3 py-1.5 text-xs rounded-lg border transition-all ${
              tab === "timeline"
                ? "bg-[#4f7cff]/20 text-[#4f7cff] border-[#4f7cff]/40"
                : "border-[--border] text-[--text-secondary] hover:text-white"
            }`}
          >
            Timeline ({companyEntries.length})
          </button>
          <button
            onClick={() => setTab("search")}
            className={`px-3 py-1.5 text-xs rounded-lg border transition-all ${
              tab === "search"
                ? "bg-[#4f7cff]/20 text-[#4f7cff] border-[#4f7cff]/40"
                : "border-[--border] text-[--text-secondary] hover:text-white"
            }`}
          >
            Search
          </button>
        </div>
      </div>

      {/* ── TAB 1: Timeline ───────────────────────────────────────────────── */}
      {tab === "timeline" && (
        <div className="flex-1 flex gap-4 min-h-0">
          <div className="flex-1 overflow-y-auto space-y-4 pr-2">
            {timelineLoading ? (
              <div className="space-y-3">
                {[1, 2, 3, 4].map((i) => (
                  <div key={i} className="h-24 rounded-xl animate-pulse" style={{ backgroundColor: "var(--bg-secondary)" }} />
                ))}
              </div>
            ) : companyEntries.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-48 text-center">
                <p className="text-sm text-[--text-muted]">No memory entries yet</p>
                <p className="text-[11px] text-[--text-muted] mt-1">Approved companies appear here with outreach details</p>
                <button onClick={() => navigate("/workflow")}
                  className="mt-3 text-xs px-3 py-1.5 rounded-lg bg-[#4f7cff]/20 text-[#4f7cff] hover:bg-[#4f7cff]/30 transition-colors">
                  Start a workflow →
                </button>
              </div>
            ) : (
              timelineGroups.map((group) => (
                <div key={group.label}>
                  <h3 className="text-[11px] font-semibold text-[--text-muted] uppercase tracking-wider mb-2">{group.label}</h3>
                  <div className="space-y-2">
                    {group.entries.map((entry) => (
                      <TimelineCard key={entry.id} entry={entry} onStatusUpdate={handleStatusUpdate} onClick={() => setSelectedEntry(entry)} />
                    ))}
                  </div>
                </div>
              ))
            )}
          </div>

          {selectedEntry && (
            <div className="w-96 shrink-0 rounded-xl border flex flex-col overflow-hidden animate-in slide-in-from-right duration-250" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
              <div className="px-4 py-3 border-b flex items-center justify-between" style={{ borderColor: "var(--border)" }}>
                <h3 className="text-xs font-semibold text-white uppercase tracking-wider">Memory Details</h3>
                <button onClick={() => setSelectedEntry(null)} className="text-xs text-[--text-muted] hover:text-white p-1">✕</button>
              </div>
              <div className="flex-1 overflow-y-auto p-4 space-y-4 text-xs">
                <div>
                  <p className="text-[10px] text-[--text-muted] uppercase tracking-wider mb-1 font-bold">Summary</p>
                  <p className="text-[11px] text-[--text-secondary] leading-relaxed bg-[--bg-secondary] p-3 rounded-lg border border-[--border]">
                    {selectedEntry.summary}
                  </p>
                </div>
                {selectedEntry.metadata_json && (
                  <div>
                    <p className="text-[10px] text-[--text-muted] uppercase tracking-wider mb-1.5 font-bold font-sans">Metadata Properties</p>
                    <div className="rounded-lg border border-[--border] overflow-hidden">
                      <div className="divide-y divide-[--border] text-[10px]">
                        {Object.entries(selectedEntry.metadata_json).map(([k, v]) => (
                          <div key={k} className="flex px-3 py-2 bg-[--bg-card] hover:bg-[--bg-secondary] transition-colors">
                            <span className="text-[10px] text-[--text-muted] w-24 shrink-0 font-medium">{k}</span>
                            <span className="text-[10px] text-[--text-secondary] break-all flex-1">
                              {typeof v === "object" ? JSON.stringify(v) : String(v)}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
                {selectedEntry.metadata_json && (
                  <div className="rounded-lg px-3 py-2 bg-amber-500/10 border border-amber-500/20">
                    <div className="flex items-start gap-2">
                      <span className="text-amber-400 text-xs">⚠️</span>
                      <p className="text-[10px] text-amber-300/90 leading-normal">
                        This company is already in memory. Future workflows will flag it as a duplicate.
                      </p>
                    </div>
                  </div>
                )}
                <div>
                  <p className="text-[10px] text-[--text-muted] uppercase tracking-wider mb-1 font-bold">Timeline Details</p>
                  <div className="text-[10px] text-[--text-secondary] space-y-1">
                    <p>Created: <span className="text-white">{formatDate(selectedEntry.created_at)}</span></p>
                    {selectedEntry.last_seen && <p>Last seen: <span className="text-white">{formatDate(selectedEntry.last_seen)}</span></p>}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ── TAB 2: Semantic Search ────────────────────────────────────────── */}
      {tab === "search" && (
        <div className="flex-1 overflow-y-auto space-y-4 pr-2">
          <div className="sticky top-0 z-10" style={{ backgroundColor: "var(--bg-page)" }}>
            <div className="relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-[--text-muted]">🔍</span>
              <input type="text" value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search companies by description, tech stack, or industry..."
                className="w-full pl-10 pr-4 py-3 text-sm rounded-xl border bg-[--bg-card] border-[--border] text-white placeholder:text-[--text-muted] focus:outline-none focus:border-[#4f7cff]"
                autoFocus />
            </div>
            {!searchQuery && (
              <div className="flex items-center gap-2 mt-2">
                <span className="text-[10px] text-[--text-muted]">Try:</span>
                {examples.map((ex) => (
                  <button key={ex} onClick={() => setSearchQuery(ex)}
                    className="text-[10px] px-2.5 py-1 rounded-lg border border-[--border] text-[--text-secondary] hover:text-white hover:border-[#4f7cff]/40 transition-colors">
                    {ex}
                  </button>
                ))}
              </div>
            )}
          </div>

          <div className="space-y-3">
            {searchQuery && debouncedQuery.length < 2 && (
              <p className="text-xs text-[--text-muted] text-center py-8">Type at least 2 characters to search</p>
            )}
            {searchLoading && (
              <div className="space-y-3">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="h-28 rounded-xl animate-pulse" style={{ backgroundColor: "var(--bg-secondary)" }} />
                ))}
              </div>
            )}
            {searchData && searchData.results.length === 0 && debouncedQuery.length >= 2 && (
              <div className="text-center py-12">
                <p className="text-sm text-[--text-muted]">No results for "{debouncedQuery}"</p>
                <p className="text-[10px] text-[--text-muted] mt-1">Try different keywords or a broader search</p>
              </div>
            )}
            {searchData && searchData.results.length > 0 && (
              <>
                <p className="text-[11px] text-[--text-muted]">Found {searchData.total} result{searchData.total !== 1 ? "s" : ""} for "{searchData.query}"</p>
                <div className="space-y-3">
                  {searchData.results.map((r) => <SearchResultCard key={r.id} result={r} />)}
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
