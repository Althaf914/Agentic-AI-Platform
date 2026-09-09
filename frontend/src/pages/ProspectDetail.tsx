import { useParams, useNavigate } from "react-router-dom";
import { useState } from "react";
import { useProspectDetail } from "@/hooks/useProspects";
import type { ProspectCompany, ProspectContact, ScoreBreakdown, MarketSignals } from "@/types/prospect";

// ═══════════════════════════════════════════════════════════════════════════════
//  Helpers & Styling Constants
// ═══════════════════════════════════════════════════════════════════════════════

const DIMENSION_LABELS: Record<string, string> = {
  industry_match: "Industry Match",
  location_match: "Location Match",
  hiring_signals: "Hiring Signals",
  tech_stack_match: "Tech Stack Match",
  funding_stage: "Funding Stage",
  revenue_tier: "Revenue Tier",
  employee_range: "Employee Range",
  decision_makers_found: "Decision Makers",
};

function getInitials(name: string): string {
  const parts = name.split(" ").filter(Boolean);
  if (parts.length >= 2) return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
  return name.slice(0, 2).toUpperCase();
}

function scoreColor(val: number): string {
  if (val >= 80) return "bg-emerald-500";
  if (val >= 60) return "bg-amber-500";
  return "bg-red-500";
}

function scoreTextColor(val: number): string {
  if (val >= 80) return "text-emerald-400";
  if (val >= 60) return "text-amber-400";
  return "text-red-400";
}

function tierBadge(tier: string | undefined): { label: string; cls: string } | null {
  if (!tier || tier === "discard") return null;
  const map: Record<string, { label: string; cls: string }> = {
    A: { label: "A", cls: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30" },
    B: { label: "B", cls: "bg-amber-500/15 text-amber-400 border-amber-500/30" },
    C: { label: "C", cls: "bg-zinc-500/15 text-zinc-400 border-zinc-500/30" },
  };
  return map[tier] ?? null;
}

export default function ProspectDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: company, isLoading, error } = useProspectDetail(id ?? null);

  const [emailExpanded, setEmailExpanded] = useState(true);
  const [linkedinExpanded, setLinkedinExpanded] = useState(false);
  const [sequenceExpanded, setSequenceExpanded] = useState(false);

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-center py-20">
        <div className="w-10 h-10 border-4 border-[#4f7cff] border-t-transparent rounded-full animate-spin mb-4" />
        <p className="text-sm text-[--text-muted]">Loading company profile...</p>
      </div>
    );
  }

  if (error || !company) {
    return (
      <div className="p-6 text-center">
        <p className="text-red-400 mb-4">Failed to load company detail or company not found.</p>
        <button
          onClick={() => navigate(-1)}
          className="px-4 py-2 rounded-lg bg-[--bg-secondary] text-white border border-[--border] hover:bg-[--bg-card-hover]"
        >
          Go Back
        </button>
      </div>
    );
  }

  const signals = company.market_signals ?? ({} as MarketSignals);
  const breakdown = company.score_breakdown;
  const rec = company.recommendation;

  const copyText = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
    } catch {
      /* silent */
    }
  };

  const statusColor =
    company.status === "validated" ? "#22d3a5" :
    company.status === "rejected" ? "#ef4444" : "#888";

  return (
    <div className="space-y-6 max-w-7xl mx-auto px-4 pb-12">
      {/* ── TOP BAR / NAVIGATION ── */}
      <div className="flex items-center justify-between border-b pb-4 border-[--border]">
        <button
          onClick={() => navigate(-1)}
          className="flex items-center gap-2 text-xs font-semibold text-[--text-secondary] hover:text-white transition-colors"
        >
          <span>←</span> Back
        </button>
        <div className="flex gap-2">
          <span
            className="text-xs px-2.5 py-0.5 rounded font-semibold border"
            style={{
              backgroundColor: `${statusColor}20`,
              color: statusColor,
              borderColor: `${statusColor}40`,
            }}
          >
            {company.status.toUpperCase()}
          </span>
        </div>
      </div>

      {/* ── HEADER SECTION ── */}
      <div className="flex items-start gap-5 bg-[--bg-card] border border-[--border] rounded-xl p-6 relative overflow-hidden">
        {/* Glow decoration */}
        <div className="absolute top-0 right-0 w-64 h-64 bg-[#4f7cff]/5 rounded-full filter blur-3xl pointer-events-none" />

        <div className="w-16 h-16 rounded-xl overflow-hidden bg-[--bg-secondary] shrink-0 flex items-center justify-center border border-[--border]">
          {company.logo_url ? (
            <img
              src={company.logo_url}
              alt=""
              className="w-full h-full object-contain"
              onError={(e) => {
                (e.target as HTMLImageElement).style.display = "none";
              }}
            />
          ) : (
            <span className="text-xl font-bold text-[--text-muted]">
              {getInitials(company.name)}
            </span>
          )}
        </div>

        <div className="flex-1 min-w-0">
          <h1 className="text-2xl font-bold text-white leading-tight">{company.name}</h1>
          <div className="flex items-center gap-4 mt-1">
            <a
              href={`https://${company.domain}`}
              target="_blank"
              rel="noreferrer"
              className="text-xs text-[#4f7cff] hover:underline flex items-center gap-1 font-mono"
            >
              {company.domain} <span className="text-[10px]">↗</span>
            </a>
            {company.linkedin_url && (
              <a
                href={company.linkedin_url}
                target="_blank"
                rel="noreferrer"
                className="text-xs text-[#0a66c2] hover:underline flex items-center gap-0.5"
              >
                LinkedIn <span className="text-[10px]">↗</span>
              </a>
            )}
          </div>

          {/* Metadata Grid */}
          <div className="flex flex-wrap gap-2 mt-4">
            {company.industry && (
              <span className="text-xs px-2.5 py-1 rounded-lg bg-[#4f7cff]/10 text-[#4f7cff] border border-[#4f7cff]/20">
                {company.industry}
              </span>
            )}
            {company.country && (
              <span className="text-xs px-2.5 py-1 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                📍 {company.country} {company.city ? `· ${company.city}` : ""}
              </span>
            )}
            {company.employee_count != null && (
              <span className="text-xs px-2.5 py-1 rounded-lg bg-[--bg-secondary] text-[--text-secondary] border border-[--border]">
                👥 {company.employee_count.toLocaleString()} Employees
              </span>
            )}
            {company.funding_stage && (
              <span className="text-xs px-2.5 py-1 rounded-lg bg-purple-500/10 text-purple-400 border border-purple-500/20">
                🚀 {company.funding_stage}
              </span>
            )}
            {company.revenue_range && (
              <span className="text-xs px-2.5 py-1 rounded-lg bg-blue-500/10 text-blue-400 border border-blue-500/20">
                💰 {company.revenue_range} Revenue
              </span>
            )}
            {company.domain_age_days != null && (
              <span className="text-xs px-2.5 py-1 rounded-lg bg-[--bg-secondary] text-[--text-muted] border border-[--border]">
                📅 Domain: {company.domain_age_days}d old
              </span>
            )}
          </div>

          {company.description && (
            <p className="mt-4 text-xs text-[--text-secondary] leading-relaxed max-w-4xl">
              {company.description}
            </p>
          )}
        </div>
      </div>

      {/* ── MAIN CONTENT GRID ── */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* LEFT COLUMN (5/12): Scorecard & Tech Stack */}
        <div className="space-y-6 lg:col-span-5">
          {/* Scorecard Panel */}
          <div
            className="rounded-xl border p-5 space-y-4"
            style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}
          >
            <div className="flex items-center gap-2 mb-2">
              <div className="w-0.5 h-4 rounded-full bg-[#4f7cff]" />
              <h3 className="text-xs font-semibold text-white uppercase tracking-wider">
                Score Breakdown
              </h3>
            </div>

            {breakdown ? (
              <div className="space-y-4">
                <div className="flex items-end gap-3">
                  <div className="flex items-baseline gap-1">
                    <span
                      className={`text-4xl font-bold ${scoreTextColor(breakdown.composite)}`}
                    >
                      {Math.round(breakdown.composite)}
                    </span>
                    <span className="text-sm text-[--text-muted]">/100</span>
                  </div>
                  {(() => {
                    const b = tierBadge(breakdown.tier);
                    return b ? (
                      <span
                        className={`text-[10px] px-2 py-0.5 rounded-full border font-semibold ${b.cls}`}
                      >
                        Tier {b.label}
                      </span>
                    ) : null;
                  })()}
                </div>

                <div className="space-y-3 pt-2">
                  {(
                    [
                      "industry_match",
                      "location_match",
                      "hiring_signals",
                      "tech_stack_match",
                      "funding_stage",
                      "revenue_tier",
                      "employee_range",
                      "decision_makers_found",
                    ] as const
                  ).map((key) => {
                    const dim = breakdown[key];
                    if (!dim) return null;
                    return (
                      <div key={key} className="group relative" title={dim.detail}>
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-xs text-[--text-secondary] truncate">
                            {DIMENSION_LABELS[key] ?? key}
                          </span>
                          <span className="text-[10px] text-[--text-muted] ml-auto">
                            <span className={scoreTextColor(dim.score)}>
                              {Math.round(dim.score)}
                            </span>
                            <span>/{dim.weight}pts</span>
                          </span>
                        </div>
                        <div className="flex items-center gap-2">
                          <div className="flex-1 h-1.5 rounded-full bg-[--bg-secondary] overflow-hidden">
                            <div
                              className={`h-full rounded-full transition-all ${scoreColor(dim.score)}`}
                              style={{ width: `${dim.score}%` }}
                            />
                          </div>
                          <span className="text-[10px] text-[--text-muted] w-8 text-right font-mono">
                            {dim.weighted.toFixed(1)}
                          </span>
                        </div>
                      </div>
                    );
                  })}
                </div>

                {/* Signals summaries */}
                <div className="border-t border-[--border] pt-3 flex flex-col gap-2 text-xs">
                  {breakdown.strongest_signal && (
                    <div className="flex items-start gap-1.5">
                      <span className="text-emerald-400 mt-0.5">▲</span>
                      <span className="text-[--text-muted]">
                        Strongest:{" "}
                        <span className="text-[--text-secondary]">
                          {breakdown.strongest_signal}
                        </span>
                      </span>
                    </div>
                  )}
                  {breakdown.weakest_signal && (
                    <div className="flex items-start gap-1.5">
                      <span className="text-red-400 mt-0.5">▼</span>
                      <span className="text-[--text-muted]">
                        Improve:{" "}
                        <span className="text-[--text-secondary]">
                          {breakdown.weakest_signal}
                        </span>
                      </span>
                    </div>
                  )}
                </div>

                {breakdown.reason && (
                  <div className="border-t border-[--border] pt-3">
                    <p className="text-[11px] text-[--text-muted] italic leading-relaxed">
                      {breakdown.reason}
                    </p>
                  </div>
                )}
              </div>
            ) : (
              <p className="text-xs text-[--text-muted] italic">No score breakdown available</p>
            )}
          </div>

          {/* Tech Stack Panel */}
          <div
            className="rounded-xl border p-5 space-y-4"
            style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}
          >
            <div className="flex items-center gap-2">
              <div className="w-0.5 h-4 rounded-full bg-[#4f7cff]" />
              <h3 className="text-xs font-semibold text-white uppercase tracking-wider">
                Technology Stack
              </h3>
            </div>

            {company.tech_stack_detected &&
            (company.tech_stack_detected.confirmed?.length ||
              company.tech_stack_detected.probable?.length) ? (
              <div className="space-y-4">
                {company.tech_stack_detected.confirmed &&
                  company.tech_stack_detected.confirmed.length > 0 && (
                    <div>
                      <p className="text-[10px] text-[--text-muted] uppercase tracking-wider mb-2">
                        Confirmed Technologies
                      </p>
                      <div className="flex flex-wrap gap-1.5">
                        {company.tech_stack_detected.confirmed.map((tech) => (
                          <span
                            key={tech}
                            className="text-xs px-2.5 py-0.5 rounded-full bg-[#4f7cff]/10 text-[#4f7cff] border border-[#4f7cff]/20"
                          >
                            {tech}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                {company.tech_stack_detected.probable &&
                  company.tech_stack_detected.probable.length > 0 && (
                    <div>
                      <p className="text-[10px] text-[--text-muted] uppercase tracking-wider mb-2">
                        Probable Technologies
                      </p>
                      <div className="flex flex-wrap gap-1.5">
                        {company.tech_stack_detected.probable.map((tech) => (
                          <span
                            key={tech}
                            className="text-xs px-2.5 py-0.5 rounded-full bg-zinc-500/10 text-[--text-secondary] border border-[--border]"
                          >
                            {tech}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                {company.tech_stack_detected.required_match != null && (
                  <div className="text-xs flex items-center gap-1.5 border-t border-[--border] pt-3">
                    <span
                      className={
                        company.tech_stack_detected.required_match >= 0.5
                          ? "text-emerald-400"
                          : "text-amber-400"
                      }
                    >
                      {company.tech_stack_detected.required_match >= 0.5 ? "✓" : "○"}
                    </span>
                    <span className="text-[--text-secondary]">
                      Matches{" "}
                      {Math.round(company.tech_stack_detected.required_match * 100)}%
                      of required ICP tech stack filters
                    </span>
                  </div>
                )}
              </div>
            ) : (
              <p className="text-xs text-[--text-muted] italic">No technology profile detected</p>
            )}
          </div>
        </div>

        {/* RIGHT COLUMN (7/12): Contacts, Signals & Recommended Outreach */}
        <div className="space-y-6 lg:col-span-7">
          {/* Contacts & Buying Committee */}
          <div
            className="rounded-xl border p-5 space-y-4"
            style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}
          >
            <div className="flex items-center gap-2">
              <div className="w-0.5 h-4 rounded-full bg-[#4f7cff]" />
              <h3 className="text-xs font-semibold text-white uppercase tracking-wider">
                Contacts & Buying Committee
              </h3>
            </div>

            {company.contacts && company.contacts.length > 0 ? (
              <div className="space-y-4">
                {rec?.buying_committee?.primary_persona ? (
                  <div>
                    <p className="text-[10px] text-[--text-muted] uppercase tracking-wider mb-2">
                      Primary Contact (CEO / Key Persona)
                    </p>
                    <CommitteeCard
                      contact={rec.buying_committee.primary_persona}
                      isPrimary
                      onCopy={copyText}
                    />
                  </div>
                ) : (
                  // Fallback: Show first primary contact from raw contacts if available
                  company.contacts.filter((c) => c.is_primary_persona).map((c) => (
                    <div key={c.id}>
                      <p className="text-[10px] text-[--text-muted] uppercase tracking-wider mb-2">
                        Primary Contact
                      </p>
                      <RawContactCard contact={c} isPrimary onCopy={copyText} />
                    </div>
                  ))
                )}

                {rec?.buying_committee?.secondary_personas &&
                  rec.buying_committee.secondary_personas.length > 0 && (
                    <div>
                      <p className="text-[10px] text-[--text-muted] uppercase tracking-wider mb-2">
                        Secondary Buying Committee (e.g. CFO / VP)
                      </p>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        {rec.buying_committee.secondary_personas.map((persona) => (
                          <CommitteeCard
                            key={persona.id}
                            contact={persona}
                            onCopy={copyText}
                          />
                        ))}
                      </div>
                    </div>
                  )}

                {/* Expandable list for all other enriched contacts */}
                <details className="group border-t border-[--border] pt-3">
                  <summary className="text-xs text-[#4f7cff] font-medium cursor-pointer hover:underline list-none flex items-center justify-between">
                    <span>All discovered contacts ({company.contacts.length})</span>
                    <span className="text-[10px] transition-transform group-open:rotate-180">
                      ▼
                    </span>
                  </summary>
                  <div className="mt-3 space-y-2 max-h-60 overflow-y-auto pr-2">
                    {company.contacts.map((c) => (
                      <RawContactCard key={c.id} contact={c} onCopy={copyText} />
                    ))}
                  </div>
                </details>
              </div>
            ) : (
              <p className="text-xs text-[--text-muted] italic">No contacts found at this company</p>
            )}
          </div>

          {/* Market Intelligence */}
          <div
            className="rounded-xl border p-5 space-y-4"
            style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}
          >
            <div className="flex items-center gap-2">
              <div className="w-0.5 h-4 rounded-full bg-[#4f7cff]" />
              <h3 className="text-xs font-semibold text-white uppercase tracking-wider">
                Market Intelligence & Signals
              </h3>
            </div>

            {signals && Object.keys(signals).length > 0 ? (
              <div className="space-y-4">
                {signals.urgency && (
                  <div className="flex items-center gap-3">
                    <span className="text-xs text-[--text-muted]">Urgency Tier:</span>
                    <span
                      className={`text-xs px-2 py-0.5 rounded font-semibold uppercase ${
                        signals.urgency === "high"
                          ? "bg-rose-500/10 text-rose-400 border border-rose-500/20 animate-pulse"
                          : "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                      }`}
                    >
                      {signals.urgency}
                    </span>
                  </div>
                )}

                {signals.trigger_summary && (
                  <div className="p-3.5 rounded-lg bg-[--bg-secondary] border border-[--border] text-xs leading-relaxed text-[--text-secondary]">
                    <span className="text-amber-400 mr-1.5 font-bold">⚡ Key Trigger:</span>
                    {signals.trigger_summary}
                  </div>
                )}

                {/* Individual signals scroll */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2">
                  {signals.funding?.detected && (
                    <div className="p-3 rounded-lg border border-emerald-500/20 bg-emerald-500/5">
                      <div className="flex items-center gap-2 mb-1.5">
                        <span className="text-sm">💰</span>
                        <span className="text-xs font-semibold text-emerald-400">Funding</span>
                      </div>
                      <p className="text-xs text-white">Raised {signals.funding.amount ?? "investment"}</p>
                      {signals.funding.date && (
                        <p className="text-[10px] text-[--text-muted] mt-1">Date: {signals.funding.date}</p>
                      )}
                      {signals.funding.investors && signals.funding.investors.length > 0 && (
                        <p className="text-[10px] text-[--text-muted] mt-0.5 truncate">
                          Investors: {signals.funding.investors.join(", ")}
                        </p>
                      )}
                    </div>
                  )}

                  {signals.hiring?.detected && (
                    <div className="p-3 rounded-lg border border-blue-500/20 bg-blue-500/5">
                      <div className="flex items-center gap-2 mb-1.5">
                        <span className="text-sm">👥</span>
                        <span className="text-xs font-semibold text-blue-400">Hiring</span>
                      </div>
                      <p className="text-xs text-white">
                        Hiring {signals.hiring.hiring_count_estimate ?? ""} roles
                      </p>
                      {signals.hiring.hiring_surge && (
                        <p className="text-[10px] text-emerald-400 font-semibold mt-1">
                          🔥 Hiring Surge Detected
                        </p>
                      )}
                    </div>
                  )}

                  {signals.news?.detected && (
                    <div className="p-3 rounded-lg border border-purple-500/20 bg-purple-500/5 col-span-1 md:col-span-2">
                      <div className="flex items-center gap-2 mb-1.5">
                        <span className="text-sm">📰</span>
                        <span className="text-xs font-semibold text-purple-400">News</span>
                      </div>
                      <p className="text-xs text-white font-medium">{signals.news.headline}</p>
                      {signals.news.source && (
                        <p className="text-[10px] text-[--text-muted] mt-1">
                          Source: {signals.news.source}
                        </p>
                      )}
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <p className="text-xs text-[--text-muted] italic">No active market signals recorded</p>
            )}
          </div>

          {/* Recommended Outreach */}
          <div
            className="rounded-xl border p-5 space-y-4"
            style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}
          >
            <div className="flex items-center gap-2">
              <div className="w-0.5 h-4 rounded-full bg-[#4f7cff]" />
              <h3 className="text-xs font-semibold text-white uppercase tracking-wider">
                Outreach Strategy & Templates
              </h3>
            </div>

            {rec ? (
              <div className="space-y-4">
                <div className="flex items-center gap-4 text-xs">
                  <div>
                    <span className="text-[--text-muted] mr-2">Best Channel:</span>
                    <span className="font-semibold text-white uppercase bg-[--bg-secondary] border border-[--border] px-2 py-0.5 rounded">
                      {rec.outreach_channel === "linkedin" ? "LinkedIn Note" : "Email"}
                    </span>
                  </div>
                  {rec.confidence > 0 && (
                    <div>
                      <span className="text-[--text-muted] mr-2">Score Confidence:</span>
                      <span className="text-emerald-400 font-bold">
                        {Math.round(rec.confidence * 100)}%
                      </span>
                    </div>
                  )}
                </div>

                {rec.market_trigger && (
                  <div className="p-3.5 rounded-lg bg-[--bg-secondary] text-xs text-amber-300 leading-relaxed">
                    <span className="text-xs">🎯 Hook:</span> {rec.market_trigger}
                  </div>
                )}

                {/* Subject Line */}
                {rec.outreach_subject && (
                  <div className="p-3 rounded-lg bg-[--bg-secondary] border border-[--border] space-y-1">
                    <div className="flex items-center justify-between">
                      <span className="text-[9px] text-[--text-muted] uppercase tracking-wider font-semibold">
                        Subject Line
                      </span>
                      <button
                        onClick={() => copyText(rec.outreach_subject || "")}
                        className="text-[10px] text-[#4f7cff] hover:underline"
                      >
                        Copy
                      </button>
                    </div>
                    <p className="text-xs text-white">{rec.outreach_subject}</p>
                  </div>
                )}

                {/* Cold Email Preview */}
                {rec.outreach_template && (
                  <div className="border border-[--border] rounded-lg overflow-hidden">
                    <button
                      onClick={() => setEmailExpanded(!emailExpanded)}
                      className="w-full flex items-center justify-between px-3 py-2 bg-[--bg-secondary] text-xs text-white font-medium border-b border-[--border] focus:outline-none"
                    >
                      <span>📧 Cold Email Draft</span>
                      <span>{emailExpanded ? "▲" : "▼"}</span>
                    </button>
                    {emailExpanded && (
                      <div className="p-3 space-y-2 relative">
                        <button
                          onClick={() => copyText(rec.outreach_template || "")}
                          className="absolute top-2 right-2 text-[10px] px-2 py-1 rounded bg-[--bg-card] border border-[--border] text-[#4f7cff] hover:text-white hover:bg-[#4f7cff]/20 transition-all font-sans"
                        >
                          Copy Draft
                        </button>
                        <pre className="text-xs text-[--text-secondary] font-mono whitespace-pre-wrap leading-relaxed pr-12 pt-2">
                          {rec.outreach_template}
                        </pre>
                      </div>
                    )}
                  </div>
                )}

                {/* LinkedIn message Preview */}
                {rec.linkedin_message && (
                  <div className="border border-[--border] rounded-lg overflow-hidden">
                    <button
                      onClick={() => setLinkedinExpanded(!linkedinExpanded)}
                      className="w-full flex items-center justify-between px-3 py-2 bg-[--bg-secondary] text-xs text-white font-medium border-b border-[--border] focus:outline-none"
                    >
                      <span>💬 LinkedIn Connection Note</span>
                      <span>{linkedinExpanded ? "▲" : "▼"}</span>
                    </button>
                    {linkedinExpanded && (
                      <div className="p-3 relative">
                        <button
                          onClick={() => copyText(rec.linkedin_message || "")}
                          className="absolute top-2 right-2 text-[10px] px-2 py-1 rounded bg-[--bg-card] border border-[--border] text-[#4f7cff] hover:text-white hover:bg-[#4f7cff]/20 transition-all font-sans"
                        >
                          Copy
                        </button>
                        <p className="text-xs text-[--text-secondary] pr-12 pt-2 font-mono whitespace-pre-wrap leading-relaxed">
                          {rec.linkedin_message}
                        </p>
                      </div>
                    )}
                  </div>
                )}

                {/* 3-Touch Follow-up Sequence */}
                {rec.follow_up_sequence && rec.follow_up_sequence.length > 0 && (
                  <div className="border border-[--border] rounded-lg overflow-hidden">
                    <button
                      onClick={() => setSequenceExpanded(!sequenceExpanded)}
                      className="w-full flex items-center justify-between px-3 py-2 bg-[--bg-secondary] text-xs text-white font-medium border-b border-[--border] focus:outline-none"
                    >
                      <span>🔄 3-Touch Follow-up Sequence</span>
                      <span>{sequenceExpanded ? "▲" : "▼"}</span>
                    </button>
                    {sequenceExpanded && (
                      <div className="p-3 space-y-4">
                        {rec.follow_up_sequence.map((touch) => (
                          <div key={touch.touch} className="border-l-2 border-[#4f7cff] pl-3 py-0.5">
                            <div className="flex items-center justify-between mb-1.5">
                              <span className="text-xs font-semibold text-white">
                                Touch {touch.touch}: {touch.channel.toUpperCase()} (Day {touch.day})
                              </span>
                              <button
                                onClick={() => copyText(touch.message)}
                                className="text-[10px] text-[#4f7cff] hover:underline"
                              >
                                Copy Msg
                              </button>
                            </div>
                            {touch.subject && (
                              <p className="text-[10px] text-[--text-muted] font-sans mb-1">
                                Sub: {touch.subject}
                              </p>
                            )}
                            <pre className="text-xs text-[--text-secondary] font-mono whitespace-pre-wrap leading-relaxed">
                              {touch.message}
                            </pre>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* Talking Points */}
                {rec.talking_points && rec.talking_points.length > 0 && (
                  <div>
                    <p className="text-[10px] text-[--text-muted] uppercase tracking-wider mb-2">
                      Outreach Talking Points
                    </p>
                    <ul className="list-disc list-inside space-y-1 text-xs text-[--text-secondary] pl-1.5">
                      {rec.talking_points.map((pt, i) => (
                        <li key={i} className="leading-relaxed">
                          {pt}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Suggested Action */}
                {rec.suggested_action && (
                  <div className="flex items-start gap-2 pt-3 border-t border-[--border] text-xs">
                    <span className="text-emerald-400 mt-0.5">▶</span>
                    <p className="text-[--text-secondary] italic">
                      <span className="font-semibold text-white uppercase tracking-wider text-[10px] not-italic mr-1.5">
                        Next Action:
                      </span>
                      {rec.suggested_action}
                    </p>
                  </div>
                )}
              </div>
            ) : (
              <p className="text-xs text-[--text-muted] italic">
                No personalized recommendations generated
              </p>
            )}
          </div>
        </div>
      </div>

      {/* ── FOOTER ACTIONS ── */}
      <div
        className="flex items-center justify-start gap-3 p-4 border rounded-xl"
        style={{
          borderColor: "var(--border)",
          backgroundColor: "var(--bg-card)",
        }}
      >
        <button className="px-5 py-2 text-xs font-semibold rounded-lg bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 hover:bg-emerald-500/30 transition-colors shadow-sm">
          Approve for outreach
        </button>
        <button className="px-5 py-2 text-xs font-semibold rounded-lg bg-red-500/10 text-red-400 border border-red-500/20 hover:bg-red-500/20 transition-colors shadow-sm">
          Reject Prospect
        </button>
        {rec?.outreach_template && (
          <button
            onClick={() => copyText(rec.outreach_template || "")}
            className="px-4 py-2 text-xs rounded-lg border text-[--text-secondary] hover:text-white transition-colors"
            style={{ borderColor: "var(--border)" }}
          >
            Copy Email Draft
          </button>
        )}
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
//  Internal Component: Committee Persona Card
// ═══════════════════════════════════════════════════════════════════════════════

function CommitteeCard({
  contact,
  isPrimary,
  onCopy,
}: {
  contact: {
    id: string;
    full_name: string;
    role: string;
    linkedin_url?: string;
    confidence_score: number;
    source?: string;
    email?: string | null;
  };
  isPrimary?: boolean;
  onCopy: (txt: string) => void;
}) {
  return (
    <div
      className="flex items-center gap-3 py-2 px-3 rounded-lg border"
      style={{ backgroundColor: "var(--bg-secondary)", borderColor: "var(--border)" }}
    >
      <div
        className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold shrink-0 ${
          isPrimary
            ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
            : "bg-[#4f7cff]/20 text-[#4f7cff] border border-[#4f7cff]/30"
        }`}
      >
        {getInitials(contact.full_name)}
      </div>

      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-1.5">
          <span className="text-xs text-white font-medium truncate">{contact.full_name}</span>
          {contact.linkedin_url && (
            <a
              href={contact.linkedin_url}
              target="_blank"
              rel="noreferrer"
              className="text-[10px] text-[#0a66c2] hover:underline shrink-0"
              title="LinkedIn profile"
            >
              in ↗
            </a>
          )}
        </div>
        <p className="text-[10px] text-[--text-muted] truncate">{contact.role}</p>
        {contact.email && (
          <div className="flex items-center gap-1.5 mt-0.5">
            <span className="text-[9px] text-[#22d3a5] font-mono truncate">{contact.email}</span>
            <button
              onClick={() => onCopy(contact.email!)}
              className="text-[8px] text-[#4f7cff] hover:underline"
            >
              Copy
            </button>
          </div>
        )}
      </div>

      <div className="flex flex-col items-end justify-center gap-1 shrink-0">
        {contact.confidence_score > 0 && (
          <span
            className={`text-[9px] font-semibold ${
              contact.confidence_score >= 0.8 ? "text-emerald-400" : "text-amber-400"
            }`}
          >
            ● {Math.round(contact.confidence_score * 100)}%
          </span>
        )}
        {contact.source && (
          <span className="text-[7px] px-1 py-0.5 rounded bg-[--bg-card] text-[--text-muted] uppercase border border-[--border]">
            {contact.source.replace(/_/g, " ").slice(0, 10)}
          </span>
        )}
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
//  Internal Component: Raw Contact Row/Card
// ═══════════════════════════════════════════════════════════════════════════════

function RawContactCard({
  contact,
  isPrimary,
  onCopy,
}: {
  contact: ProspectContact;
  isPrimary?: boolean;
  onCopy: (txt: string) => void;
}) {
  return (
    <div
      className="flex items-center gap-3 py-2 px-3 rounded-lg border"
      style={{ backgroundColor: "var(--bg-secondary)", borderColor: "var(--border)" }}
    >
      <div
        className={`w-7 h-7 rounded-full flex items-center justify-center text-[10px] font-bold shrink-0 ${
          isPrimary || contact.is_primary_persona
            ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
            : "bg-[#4f7cff]/20 text-[#4f7cff] border border-[#4f7cff]/30"
        }`}
      >
        {getInitials(contact.full_name)}
      </div>

      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-1.5">
          <span className="text-xs text-white font-medium truncate">{contact.full_name}</span>
          {contact.linkedin_url && (
            <a
              href={contact.linkedin_url}
              target="_blank"
              rel="noreferrer"
              className="text-[10px] text-[#0a66c2] hover:underline"
            >
              in ↗
            </a>
          )}
        </div>
        <p className="text-[10px] text-[--text-muted] truncate">{contact.role}</p>

        {contact.email && (
          <div className="flex items-center gap-1.5 mt-0.5">
            <span className="text-[9px] text-[#22d3a5] font-mono truncate">{contact.email}</span>
            <button
              onClick={() => onCopy(contact.email!)}
              className="text-[8px] text-[#4f7cff] hover:underline shrink-0"
            >
              Copy
            </button>
          </div>
        )}
      </div>

      <div className="flex flex-col items-end gap-1 shrink-0 text-right">
        {contact.email_confidence != null && (
          <span
            className={`text-[8px] font-semibold ${
              contact.email_confidence >= 0.8 ? "text-emerald-400" : "text-amber-400"
            }`}
          >
            {Math.round(contact.email_confidence * 100)}% conf
          </span>
        )}
        {contact.source && (
          <span className="text-[7px] px-1 py-0.5 rounded bg-[--bg-card] text-[--text-muted] uppercase border border-[--border]">
            {contact.source.replace(/_/g, " ").slice(0, 10)}
          </span>
        )}
      </div>
    </div>
  );
}
