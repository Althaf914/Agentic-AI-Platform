import { useState, useCallback, useMemo, useEffect } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { useProspects, useProspectDetail } from "@/hooks/useProspects";
import { getWorkflowList } from "@/api/workflows";
import type { ProspectCompany, ProspectContact, ScoreBreakdown, MarketSignals } from "@/types/prospect";

// ═══════════════════════════════════════════════════════════════════════════════
//  Constants
// ═══════════════════════════════════════════════════════════════════════════════

const TIERS = ["All", "A", "B", "C"] as const;
const SORT_OPTIONS = [
  { value: "score_desc", label: "Score (desc)" },
  { value: "name", label: "Company name" },
  { value: "date", label: "Date discovered" },
] as const;

const DIMENSION_LABELS: Record<string, string> = {
  industry_match: "Industry match",
  location_match: "Location match",
  hiring_signals: "Hiring signals",
  tech_stack_match: "Tech stack match",
  funding_stage: "Funding stage",
  revenue_tier: "Revenue tier",
  employee_range: "Employee range",
  decision_makers_found: "Decision makers",
};

// ═══════════════════════════════════════════════════════════════════════════════
//  Helpers
// ═══════════════════════════════════════════════════════════════════════════════

function getInitials(name: string): string {
  const parts = name.split(" ").filter(Boolean);
  if (parts.length >= 2) return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
  return name.slice(0, 2).toUpperCase();
}

function scoreColor(val: number): string {
  if (val >= 70) return "bg-emerald-500";
  if (val >= 40) return "bg-amber-500";
  return "bg-rose-500";
}

function scoreTextColor(val: number): string {
  if (val >= 70) return "text-emerald-400";
  if (val >= 40) return "text-amber-400";
  return "text-rose-400";
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

function getTopTech(company: ProspectCompany): string[] {
  const detected = company.tech_stack_detected;
  if (!detected) return [];
  const techs: string[] = [];
  if (detected.confirmed) techs.push(...detected.confirmed);
  if (detected.probable) techs.push(...detected.probable);
  return [...new Set(techs)];
}

function getPrimaryContact(company: ProspectCompany): ProspectContact | undefined {
  return company.contacts.find((c) => c.is_primary_persona) ?? company.contacts[0];
}

function formatSignalSummary(signals: MarketSignals | null | undefined): string {
  if (!signals) return "";
  const parts: string[] = [];
  if (signals.funding?.detected && signals.funding.amount) parts.push(`Raised ${signals.funding.amount}`);
  if (signals.hiring?.hiring_surge) parts.push(`Hiring ${signals.hiring.hiring_count_estimate ?? ""} roles`.trim());
  if (signals.expansion?.detected && signals.expansion.new_location) parts.push(`Expanding to ${signals.expansion.new_location}`);
  if (signals.news?.detected && signals.news.headline) parts.push(signals.news.headline);
  return parts.join(" · ");
}

// ═══════════════════════════════════════════════════════════════════════════════
//  Filter Bar
// ═══════════════════════════════════════════════════════════════════════════════

function FilterBar({
  workflowId, onWorkflowChange, workflows, workflowsLoading,
  tier, onTierChange,
  minScore, onMinScoreChange,
  industry, onIndustryChange,
  hasEmail, onHasEmailChange,
  hasSignal, onHasSignalChange,
  sort, onSortChange,
}: {
  workflowId: string; onWorkflowChange: (v: string) => void;
  workflows: { id: string; configuration_name?: string }[] | undefined; workflowsLoading: boolean;
  tier: string; onTierChange: (v: string) => void;
  minScore: number; onMinScoreChange: (v: number) => void;
  industry: string; onIndustryChange: (v: string) => void;
  hasEmail: boolean; onHasEmailChange: (v: boolean) => void;
  hasSignal: boolean; onHasSignalChange: (v: boolean) => void;
  sort: string; onSortChange: (v: string) => void;
}) {
  return (
    <div
      className="rounded-xl border p-4 bg-[--bg-card] space-y-4"
      style={{ borderColor: "var(--border)" }}
    >
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-center">
        {/* Campaign Selector */}
        <div className="flex flex-col gap-1.5 text-left">
          <label className="text-[10px] text-[--text-muted] uppercase tracking-wider font-bold">Campaign / Workflow</label>
          <select
            value={workflowId}
            onChange={(e) => onWorkflowChange(e.target.value)}
            className="text-xs rounded-lg border bg-[--bg-secondary] border-[--border] text-white px-3 py-2 focus:outline-none focus:border-[#4f7cff] w-full"
          >
            <option value="">All campaigns</option>
            {workflowsLoading && <option disabled>Loading...</option>}
            {workflows?.map((w) => (
              <option key={w.id} value={w.id}>{w.configuration_name ?? w.id.slice(0, 8)}</option>
            ))}
          </select>
        </div>

        {/* Industry Search */}
        <div className="flex flex-col gap-1.5 text-left">
          <label className="text-[10px] text-[--text-muted] uppercase tracking-wider font-bold">Industry Keyword</label>
          <input
            placeholder="Search industry..."
            value={industry}
            onChange={(e) => onIndustryChange(e.target.value)}
            className="w-full px-3 py-2 text-xs rounded-lg border bg-[--bg-secondary] border-[--border] text-white placeholder:text-[--text-muted] focus:outline-none focus:border-[#4f7cff]"
          />
        </div>

        {/* Sort Select */}
        <div className="flex flex-col gap-1.5 text-left">
          <label className="text-[10px] text-[--text-muted] uppercase tracking-wider font-bold">Sort By</label>
          <select
            value={sort}
            onChange={(e) => onSortChange(e.target.value)}
            className="text-xs rounded-lg border bg-[--bg-secondary] border-[--border] text-white px-3 py-2 focus:outline-none focus:border-[#4f7cff] w-full"
          >
            {SORT_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>{o.label}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="h-px bg-[--border]" />

      <div className="grid grid-cols-1 md:grid-cols-12 gap-4 items-center">
        {/* Tier Pills: 4 columns */}
        <div className="md:col-span-4 flex items-center gap-2">
          <span className="text-[10px] text-[--text-muted] uppercase tracking-wider font-bold shrink-0">Tier:</span>
          <div className="flex items-center gap-1">
            {TIERS.map((t) => {
              const active = (t === "All" && !tier) || (tier === t);
              const colorMap: Record<string, string> = {
                A: active ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/40" : "",
                B: active ? "bg-amber-500/20 text-amber-400 border-amber-500/40" : "",
                C: active ? "bg-zinc-500/20 text-zinc-400 border-zinc-500/40" : "",
              };
              return (
                <button
                  key={t}
                  onClick={() => onTierChange(t === "All" ? "" : t)}
                  className={`text-[11px] px-3 py-1 rounded-lg border transition-all font-medium
                    ${active
                      ? (colorMap[t] ?? "bg-[#4f7cff]/20 text-[#4f7cff] border-[#4f7cff]/40")
                      : "border-transparent text-[--text-secondary] hover:bg-[--bg-secondary]"
                    }`}
                >
                  {t}
                </button>
              );
            })}
          </div>
        </div>

        {/* Score Slider: 4 columns */}
        <div className="md:col-span-4 flex items-center gap-3">
          <label className="text-[10px] text-[--text-muted] uppercase tracking-wider font-bold shrink-0">Min Score:</label>
          <div className="flex-1 flex items-center gap-2">
            <input
              type="range"
              min={0} max={100} step={5}
              value={minScore}
              onChange={(e) => onMinScoreChange(+e.target.value)}
              className="w-full h-1 accent-[#4f7cff]"
            />
            <span className="text-xs text-white font-bold shrink-0 bg-[--bg-secondary] px-2 py-0.5 rounded border border-[--border]">{minScore}</span>
          </div>
        </div>

        {/* Toggles: 4 columns */}
        <div className="md:col-span-4 flex items-center gap-4 justify-start md:justify-end">
          <label className="flex items-center gap-2 cursor-pointer select-none">
            <input type="checkbox" checked={hasEmail} onChange={(e) => onHasEmailChange(e.target.checked)}
              className="accent-[#4f7cff] w-4 h-4 rounded" />
            <span className="text-xs text-[--text-secondary]">Has email</span>
          </label>
          <label className="flex items-center gap-2 cursor-pointer select-none">
            <input type="checkbox" checked={hasSignal} onChange={(e) => onHasSignalChange(e.target.checked)}
              className="accent-[#4f7cff] w-4 h-4 rounded" />
            <span className="text-xs text-[--text-secondary]">Has signal</span>
          </label>
        </div>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
//  Company List Row
// ═══════════════════════════════════════════════════════════════════════════════

function CompanyRow({
  company, selected, onClick,
}: {
  company: ProspectCompany; selected: boolean; onClick: () => void;
}) {
  const breakdown = company.score_breakdown;
  const tier = breakdown?.tier;
  const badge = tierBadge(tier);
  const score = company.qualification_score ?? 0;
  const contact = getPrimaryContact(company);
  const techPills = getTopTech(company).slice(0, 3);
  const allTech = getTopTech(company);
  const hasSignals = company.market_signals && Object.keys(company.market_signals).length > 0;

  return (
    <div
      onClick={onClick}
      className={`flex items-center gap-3 px-4 py-3 rounded-xl cursor-pointer transition-all border text-left ${
        selected
          ? "bg-[--bg-secondary] border-[#4f7cff] shadow-md shadow-[#4f7cff]/5"
          : "border-[--border] hover:border-[#4f7cff]/30 bg-[--bg-card]"
      }`}
    >
      {/* Logo / Initials */}
      <div className="w-9 h-9 rounded-xl overflow-hidden bg-[--bg-secondary] shrink-0 flex items-center justify-center border border-[--border]">
        {company.logo_url ? (
          <img src={company.logo_url} alt="" className="w-full h-full object-contain"
            onError={(e) => { (e.target as HTMLImageElement).style.display = "none"; }} />
        ) : (
          <span className="text-[11px] font-bold text-[--text-muted]">{getInitials(company.name)}</span>
        )}
      </div>

      {/* Name + domain */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="text-sm font-semibold text-white truncate">{company.name}</span>
          {badge && (
            <span className={`text-[9px] px-1.5 py-0.5 rounded-full border font-semibold ${badge.cls}`}>{badge.label}</span>
          )}
        </div>
        <div className="flex items-center gap-2 mt-1 flex-wrap">
          <span className="text-[11px] text-[--text-muted]">{company.domain}</span>
          {contact && (
            <>
              <span className="text-[11px] text-[--text-muted] font-bold">•</span>
              <span className="text-[11px] text-white font-medium">
                👤 {contact.full_name} <span className="text-[--text-muted]">({contact.role})</span>
              </span>
            </>
          )}
        </div>
      </div>

      {/* Market signal icon */}
      {hasSignals && (
        <span className="text-amber-400 text-xs shrink-0" title="Market signal detected">⚡</span>
      )}

      {/* Tech pills */}
      {techPills.length > 0 && (
        <div className="hidden lg:flex items-center gap-1.5 shrink-0" title={allTech.join(", ")}>
          {techPills.map((t) => (
            <span key={t} className="text-[9px] px-2 py-0.5 rounded bg-[#4f7cff]/10 text-[#4f7cff] border border-[#4f7cff]/20">{t}</span>
          ))}
        </div>
      )}

      {/* Score */}
      <div className="flex items-center gap-3 shrink-0 min-w-[70px]">
        <div className="text-right">
          <span className={`text-sm font-bold ${scoreTextColor(score)}`}>{Math.round(score)}</span>
          <span className="text-[10px] text-[--text-muted]">/100</span>
        </div>
        <div className="w-12 h-1 rounded-full bg-[--bg-secondary] overflow-hidden border border-[--border]">
          <div className={`h-full rounded-full ${scoreColor(score)}`} style={{ width: `${score}%` }} />
        </div>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
//  Score Breakdown (8 horizontal bars)
// ═══════════════════════════════════════════════════════════════════════════════

function ScoreBreakdownSection({ breakdown }: { breakdown: ScoreBreakdown }) {
  const dims = [
    "industry_match", "location_match", "hiring_signals", "tech_stack_match",
    "funding_stage", "revenue_tier", "employee_range", "decision_makers_found",
  ] as const;

  const maxWeight = Math.max(...dims.map((d) => breakdown[d]?.weight ?? 0));

  return (
    <div>
      {/* Overall score */}
      <div className="flex items-end gap-4 mb-4">
        <div className="flex items-baseline gap-1">
          <span className={`text-4xl font-bold ${scoreTextColor(breakdown.composite)}`}>{Math.round(breakdown.composite)}</span>
          <span className="text-lg text-[--text-muted]">/100</span>
        </div>
        {(() => {
          const b = tierBadge(breakdown.tier);
          return b ? <span className={`text-xs px-2 py-0.5 rounded-full border font-semibold ${b.cls}`}>Tier {b.label}</span> : null;
        })()}
      </div>

      {/* 8 bars */}
      <div className="space-y-2.5">
        {dims.map((key) => {
          const dim = breakdown[key];
          if (!dim) return null;
          const pct = dim.weight / maxWeight;
          return (
            <div key={key} className="group relative" title={dim.detail}>
              <div className="flex items-center gap-2 mb-0.5">
                <span className="text-[11px] text-[--text-secondary] w-28 shrink-0">{DIMENSION_LABELS[key] ?? key}</span>
                <span className="text-[10px] text-[--text-muted] ml-auto">
                  <span className={scoreTextColor(dim.score)}>{Math.round(dim.score)}</span>
                  <span className="text-[--text-muted]">/{dim.weight}pts</span>
                </span>
              </div>
              <div className="flex items-center gap-2">
                <div className="flex-1 h-2 rounded-full bg-[--bg-secondary] overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all ${scoreColor(dim.score)}`}
                    style={{ width: `${dim.score}%` }}
                  />
                </div>
                <span className="text-[10px] text-[--text-muted] w-12 text-right">{dim.weighted.toFixed(1)}</span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Strongest / weakest */}
      <div className="mt-4 flex gap-4 text-[11px]">
        {breakdown.strongest_signal && (
          <div className="flex items-center gap-1.5">
            <span className="text-emerald-400">▲</span>
            <span className="text-[--text-muted]">Strongest: <span className="text-[--text-secondary]">{breakdown.strongest_signal}</span></span>
          </div>
        )}
        {breakdown.weakest_signal && (
          <div className="flex items-center gap-1.5">
            <span className="text-red-400">▼</span>
            <span className="text-[--text-muted]">Improve: <span className="text-[--text-secondary]">{breakdown.weakest_signal}</span></span>
          </div>
        )}
      </div>

      {/* LLM reason */}
      {breakdown.reason && (
        <p className="mt-3 text-[11px] text-[--text-muted] italic leading-relaxed">{breakdown.reason}</p>
      )}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
//  Market Intelligence
// ═══════════════════════════════════════════════════════════════════════════════

function MarketSignalsSection({ signals }: { signals: MarketSignals }) {
  const cards: { icon: string; title: string; body: string; color: string }[] = [];

  if (signals.funding?.detected) {
    cards.push({
      icon: "💰",
      title: `Raised ${signals.funding.amount ?? "funding"}`,
      body: [signals.funding.date, signals.funding.investors?.join(", ")].filter(Boolean).join(" · "),
      color: "border-emerald-500/30",
    });
  }
  if (signals.hiring?.detected) {
    cards.push({
      icon: "👥",
      title: `Actively hiring ${signals.hiring.hiring_count_estimate ?? ""} roles`.trim(),
      body: signals.hiring.hiring_surge ? "Hiring surge detected" : "Recruiting",
      color: "border-blue-500/30",
    });
  }
  if (signals.news?.detected) {
    cards.push({
      icon: "📰",
      title: signals.news.headline ?? "Recent news",
      body: signals.news.source ?? "",
      color: "border-purple-500/30",
    });
  }
  if (signals.expansion?.detected) {
    cards.push({
      icon: "🌍",
      title: `Expanding to ${signals.expansion.new_location ?? "new markets"}`,
      body: signals.expansion.timeline ? `Timeline: ${signals.expansion.timeline}` : "",
      color: "border-amber-500/30",
    });
  }
  if (signals.leadership?.detected) {
    cards.push({
      icon: "👤",
      title: `New ${signals.leadership.new_role ?? "leadership"}${signals.leadership.person_name ? `: ${signals.leadership.person_name}` : ""}`,
      body: "Leadership change — new decision makers",
      color: "border-rose-500/30",
    });
  }

  if (cards.length === 0) {
    return <p className="text-[11px] text-[--text-muted] italic">No market signals detected</p>;
  }

  return (
    <div className="flex gap-3 overflow-x-auto pb-2">
      {cards.map((c, i) => (
        <div key={i} className={`shrink-0 w-52 rounded-lg border p-3 ${c.color}`} style={{ backgroundColor: "var(--bg-secondary)" }}>
          <div className="flex items-center gap-2 mb-1">
            <span>{c.icon}</span>
            <span className="text-[11px] font-medium text-white">{c.title}</span>
          </div>
          {c.body && <p className="text-[10px] text-[--text-muted]">{c.body}</p>}
        </div>
      ))}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
//  Technology Stack
// ════════════════════════════════════════════���══════════════════════════════════

function TechStackSection({ company }: { company: ProspectCompany }) {
  const detected = company.tech_stack_detected;
  if (!detected || (!detected.confirmed?.length && !detected.probable?.length)) {
    return <p className="text-[11px] text-[--text-muted] italic">No tech stack detected</p>;
  }

  const groupTech = (techs: string[], label: string) =>
    techs.length > 0 ? (
      <div>
        <p className="text-[10px] text-[--text-muted] uppercase tracking-wider mb-1.5">{label}</p>
        <div className="flex flex-wrap gap-1.5">
          {techs.map((t) => (
            <span key={t} className="text-[10px] px-2 py-0.5 rounded-full bg-[#4f7cff]/10 text-[#4f7cff] border border-[#4f7cff]/20">
              {t}
            </span>
          ))}
        </div>
      </div>
    ) : null;

  const reqMatch = detected.required_match;
  const matchText = reqMatch != null
    ? `Matches ${Math.round(reqMatch * 100)}% of required tech filters`
    : null;

  return (
    <div className="space-y-3">
      <div className="grid grid-cols-2 gap-4">
        {groupTech(detected.confirmed ?? [], "Confirmed stack")}
        {groupTech(detected.probable ?? [], "Probably uses")}
      </div>
      {matchText && (
        <div className="text-[11px] flex items-center gap-1.5">
          <span className={reqMatch! >= 0.5 ? "text-emerald-400" : "text-amber-400"}>
            {reqMatch! >= 0.5 ? "✓" : "○"}
          </span>
          <span className="text-[--text-secondary]">{matchText}</span>
        </div>
      )}
      {detected.excluded_tech_found && (
        <p className="text-[10px] text-red-400">⚠ Excluded technology detected (penalty applied)</p>
      )}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
//  Contacts / Buying Committee
// ═══════════════════════════════════════════════════════════════════════════════

function ContactsSection({ company }: { company: ProspectCompany }) {
  const { contacts, recommendation } = company;
  if (!contacts || contacts.length === 0) {
    return <p className="text-[11px] text-[--text-muted] italic">No contacts found</p>;
  }

  const bc = recommendation?.buying_committee;

  const copyEmail = async (email: string) => {
    try {
      await navigator.clipboard.writeText(email);
    } catch { /* silent */ }
  };

  return (
    <div className="space-y-2.5">
      {/* Committee personas if available */}
      {bc?.primary_persona && (
        <div className="mb-3">
          <p className="text-[10px] text-[--text-muted] uppercase tracking-wider mb-1.5">Primary persona</p>
          <ContactCard contact={bc.primary_persona} isPrimary isCommittee onCopy={copyEmail} />
        </div>
      )}
      {bc?.secondary_personas && bc.secondary_personas.length > 0 && (
        <div className="mb-3">
          <p className="text-[10px] text-[--text-muted] uppercase tracking-wider mb-1.5">Secondary</p>
          {bc.secondary_personas.map((p) => (
            <ContactCard key={p.id} contact={p} isCommittee onCopy={copyEmail} />
          ))}
        </div>
      )}

      {/* Fall back to raw contacts if committee not available */}
      {!bc && contacts.map((c) => (
        <ContactRow key={c.id} contact={c} onCopy={copyEmail} />
      ))}

      {/* Full contacts list (if we showed committee above) */}
      {bc && contacts.length > 0 && (
        <details className="mt-2">
          <summary className="text-[10px] text-[#4f7cff] cursor-pointer hover:underline">
            All {contacts.length} contacts
          </summary>
          <div className="mt-2 space-y-1.5">
            {contacts.map((c) => (
              <ContactRow key={c.id} contact={c} onCopy={copyEmail} />
            ))}
          </div>
        </details>
      )}
    </div>
  );
}

function ContactCard({ contact, isPrimary, isCommittee, onCopy }: {
  contact: { id: string; full_name: string; role: string; linkedin_url?: string; confidence_score: number; source?: string };
  isPrimary?: boolean; isCommittee?: boolean;
  onCopy: (email: string) => void;
}) {
  return (
    <div className="flex items-center gap-2 py-1.5 px-2 rounded-lg" style={{ backgroundColor: "var(--bg-secondary)" }}>
      <div className={`w-7 h-7 rounded-full flex items-center justify-center text-[10px] font-bold shrink-0 ${isPrimary ? "bg-emerald-500/20 text-emerald-400" : "bg-[#4f7cff]/20 text-[#4f7cff]"}`}>
        {getInitials(contact.full_name)}
      </div>
      <div className="flex-1 min-w-0">
        <span className="text-xs text-white font-medium">{contact.full_name}</span>
        <span className="text-[10px] text-[--text-muted] ml-1.5">{contact.role}</span>
      </div>
      <div className="flex items-center gap-1.5">
        {contact.linkedin_url && (
          <a href={contact.linkedin_url} target="_blank" rel="noreferrer"
            className="text-[10px] text-[#0a66c2] hover:underline" title="LinkedIn">in</a>
        )}
        {contact.confidence_score > 0 && (
          <span className={`text-[9px] ${contact.confidence_score >= 0.8 ? "text-emerald-400" : "text-amber-400"}`}>
            ● {Math.round(contact.confidence_score * 100)}%
          </span>
        )}
        {contact.source && (
          <span className="text-[8px] px-1 py-0.5 rounded bg-[--bg-card] text-[--text-muted]">{contact.source}</span>
        )}
      </div>
    </div>
  );
}

function ContactRow({ contact, onCopy }: { contact: ProspectContact; onCopy: (email: string) => void }) {
  return (
    <div className="flex items-center gap-2 py-1 text-[11px]">
      <div className="w-6 h-6 rounded-full bg-[#4f7cff]/20 text-[#4f7cff] flex items-center justify-center text-[9px] font-bold shrink-0">
        {getInitials(contact.full_name)}
      </div>
      <span className="text-white font-medium min-w-[100px]">{contact.full_name}</span>
      <span className="text-[--text-muted] truncate max-w-[100px]">{contact.role}</span>
      {contact.email && (
        <>
          <span className="text-[10px] text-emerald-400 truncate max-w-[130px]">{contact.email}</span>
          <button onClick={() => onCopy(contact.email!)}
            className="text-[9px] text-[#4f7cff] hover:underline shrink-0">Copy</button>
        </>
      )}
      {contact.email_confidence != null && (
        <span className={`text-[9px] ${contact.email_confidence >= 0.8 ? "text-emerald-400" : "text-amber-400"}`}>
          ● {Math.round(contact.email_confidence * 100)}% conf
        </span>
      )}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
//  Recommended Outreach
// ═══════════════════════════════════════════════════════════════════════════════

function OutreachSection({ company }: { company: ProspectCompany }) {
  const rec = company.recommendation;
  if (!rec) return <p className="text-[11px] text-[--text-muted] italic">No recommendation generated</p>;

  const [emailExpanded, setEmailExpanded] = useState(false);
  const [linkedinExpanded, setLinkedinExpanded] = useState(false);

  const copyTemplate = async () => {
    if (!rec.outreach_template) return;
    try {
      await navigator.clipboard.writeText(rec.outreach_template);
    } catch { /* silent */ }
  };

  return (
    <div className="space-y-3">
      {/* Channel recommendation */}
      <div className="flex items-center gap-2">
        <span className="text-[10px] text-[--text-muted] uppercase tracking-wider">Channel:</span>
        <span className="text-xs font-medium text-white">
          {rec.outreach_channel === "linkedin" ? "LinkedIn" : "Email"}
        </span>
        {rec.confidence > 0 && (
          <span className={`text-[10px] ${rec.confidence >= 0.8 ? "text-emerald-400" : "text-amber-400"}`}>
            ({Math.round(rec.confidence * 100)}% confidence)
          </span>
        )}
      </div>

      {/* Market trigger */}
      {rec.market_trigger && (
        <div className="flex items-start gap-2">
          <span className="text-[10px] text-[--text-muted] shrink-0 mt-0.5">🎯</span>
          <p className="text-[11px] text-amber-300 leading-relaxed">
            NOW is a good time because: {rec.market_trigger}
          </p>
        </div>
      )}

      {/* Subject line */}
      {rec.outreach_subject && (
        <div className="rounded-lg p-2.5" style={{ backgroundColor: "var(--bg-secondary)" }}>
          <p className="text-[9px] text-[--text-muted] uppercase tracking-wider mb-0.5">Subject</p>
          <p className="text-xs text-white">{rec.outreach_subject}</p>
        </div>
      )}

      {/* Email preview */}
      {rec.outreach_template && (
        <div>
          <button
            onClick={() => setEmailExpanded(!emailExpanded)}
            className="text-[10px] text-[#4f7cff] hover:underline flex items-center gap-1"
          >
            {emailExpanded ? "Hide" : "Show"} email template {emailExpanded ? "▲" : "▼"}
          </button>
          {emailExpanded && (
            <div className="mt-1.5 p-3 rounded-lg text-[11px] text-[--text-secondary] font-mono whitespace-pre-wrap border border-[--border]"
              style={{ backgroundColor: "var(--bg-secondary)" }}>
              {rec.outreach_template}
            </div>
          )}
        </div>
      )}

      {/* Talking points */}
      {rec.talking_points && rec.talking_points.length > 0 && (
        <div>
          <p className="text-[10px] text-[--text-muted] uppercase tracking-wider mb-1">Talking points</p>
          <ul className="list-disc list-inside space-y-0.5">
            {rec.talking_points.map((pt, i) => (
              <li key={i} className="text-[11px] text-[--text-secondary]">{pt}</li>
            ))}
          </ul>
        </div>
      )}

      {/* LinkedIn message */}
      {rec.linkedin_message && (
        <div>
          <button
            onClick={() => setLinkedinExpanded(!linkedinExpanded)}
            className="text-[10px] text-[#4f7cff] hover:underline flex items-center gap-1"
          >
            {linkedinExpanded ? "Hide" : "Show"} LinkedIn message {linkedinExpanded ? "▲" : "▼"}
          </button>
          {linkedinExpanded && (
            <div className="mt-1.5 p-3 rounded-lg text-[11px] text-[--text-secondary] border border-[--border]"
              style={{ backgroundColor: "var(--bg-secondary)" }}>
              {rec.linkedin_message}
            </div>
          )}
        </div>
      )}

      {/* Suggested action */}
      {rec.suggested_action && (
        <div className="flex items-start gap-2 pt-2 border-t border-[--border]">
          <span className="text-[10px] text-emerald-400 shrink-0 mt-0.5">▶</span>
          <p className="text-[11px] text-[--text-secondary] italic">{rec.suggested_action}</p>
        </div>
      )}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
//  Company Detail Panel (right side)
// ═══════════════════════════════════════════════════════════════════════════════

function DetailPanel({ company }: { company: ProspectCompany }) {
  const navigate = useNavigate();
  const signals = company.market_signals ?? {} as MarketSignals;
  const breakdown = company.score_breakdown;

  const copyTemplate = async () => {
    if (!company.recommendation?.outreach_template) return;
    try {
      await navigator.clipboard.writeText(company.recommendation.outreach_template);
    } catch { /* silent */ }
  };

  return (
    <div className="h-full flex flex-col overflow-hidden">
      {/* Scrollable content */}
      <div className="flex-1 overflow-y-auto space-y-5 px-5 py-4">
        {/* ── SECTION 1: Company header ─────────────────────────────────────── */}
        <div>
          <div className="flex items-start gap-4">
            <div className="w-14 h-14 rounded-xl overflow-hidden bg-[--bg-secondary] shrink-0 flex items-center justify-center">
              {company.logo_url ? (
                <img src={company.logo_url} alt="" className="w-full h-full object-contain"
                  onError={(e) => { (e.target as HTMLImageElement).style.display = "none"; }} />
              ) : (
                <span className="text-lg font-bold text-[--text-muted]">{getInitials(company.name)}</span>
              )}
            </div>
            <div className="flex-1 min-w-0">
              <h2 className="text-xl font-bold text-white">{company.name}</h2>
              <a href={`https://${company.domain}`} target="_blank" rel="noreferrer"
                className="text-xs text-[#4f7cff] hover:underline">{company.domain} ↗</a>
            </div>
          </div>

          {/* Metadata chips */}
          <div className="flex flex-wrap gap-1.5 mt-3">
            {company.industry && <span className="text-[10px] px-2 py-0.5 rounded-full bg-[#4f7cff]/10 text-[#4f7cff]">{company.industry}</span>}
            {company.country && <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400">{company.country}</span>}
            {company.city && <span className="text-[10px] px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-400">{company.city}</span>}
            {company.employee_count != null && <span className="text-[10px] px-2 py-0.5 rounded-full bg-[--bg-secondary] text-[--text-muted]">👥 {company.employee_count.toLocaleString()}</span>}
            {company.funding_stage && <span className="text-[10px] px-2 py-0.5 rounded-full bg-purple-500/10 text-purple-400">{company.funding_stage}</span>}
            {company.revenue_range && <span className="text-[10px] px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-400">💰 {company.revenue_range}</span>}
            {company.domain_age_days != null && <span className="text-[10px] px-2 py-0.5 rounded-full bg-[--bg-secondary] text-[--text-muted]">📅 {company.domain_age_days}d old</span>}
          </div>

          {/* Market signals summary */}
          {formatSignalSummary(signals) && (
            <p className="text-[11px] text-amber-300 mt-2">{formatSignalSummary(signals)}</p>
          )}
        </div>

        {/* ── SECTION 2: Score breakdown ───────────────────────────────────── */}
        <section>
          <SectionTitle title="Score breakdown" />
          {breakdown ? (
            <ScoreBreakdownSection breakdown={breakdown} />
          ) : (
            <p className="text-[11px] text-[--text-muted] italic">Not yet scored</p>
          )}
        </section>

        {/* ── SECTION 3: Market intelligence ───────────────────────────────── */}
        <section>
          <SectionTitle title="Market intelligence" />
          {signals && Object.keys(signals).length > 0 ? (
            <>
              <MarketSignalsSection signals={signals} />
              {signals.trigger_summary && (
                <div className="mt-2 flex items-start gap-2">
                  <span className="text-[10px] text-amber-400 shrink-0 mt-0.5">⚡</span>
                  <p className="text-[11px] text-[--text-secondary]">
                    <span className="font-medium text-white">Market trigger:</span>{' '}
                    {signals.trigger_summary ?? signals.urgency ?? ""}
                  </p>
                </div>
              )}
            </>
          ) : (
            <p className="text-[11px] text-[--text-muted] italic">No market intelligence collected</p>
          )}
        </section>

        {/* ── SECTION 4: Technology stack ──────────────────────────────────── */}
        <section>
          <SectionTitle title="Technology stack" />
          <TechStackSection company={company} />
        </section>

        {/* ── SECTION 5: Contacts / Buying committee ────────────────────────── */}
        <section>
          <SectionTitle title="Contacts & buying committee" />
          <ContactsSection company={company} />
        </section>

        {/* ── SECTION 6: Recommended outreach ──────────────────────────────── */}
        <section>
          <SectionTitle title="Recommended outreach" />
          <OutreachSection company={company} />
        </section>
      </div>

      {/* ── Action buttons (sticky bottom) ──────────────────────────────────── */}
      <div
        className="flex items-center gap-2 px-5 py-3 border-t shrink-0"
        style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)" }}
      >
        <button
          className="px-3 py-1.5 text-xs font-medium rounded-lg bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 hover:bg-emerald-500/30 transition-colors"
        >
          Approve for outreach
        </button>
        <button
          className="px-3 py-1.5 text-xs font-medium rounded-lg bg-red-500/10 text-red-400 border border-red-500/20 hover:bg-red-500/20 transition-colors"
        >
          Reject
        </button>
        <button
          onClick={copyTemplate}
          className="px-3 py-1.5 text-xs rounded-lg border text-[--text-secondary] hover:text-white transition-colors"
          style={{ borderColor: "var(--border)" }}
        >
          Copy email template
        </button>
        <button
          onClick={() => navigate("/approvals")}
          className="px-3 py-1.5 text-xs rounded-lg border text-[#4f7cff] hover:bg-[#4f7cff]/10 transition-colors ml-auto"
          style={{ borderColor: "var(--border)" }}
        >
          Open in approval queue →
        </button>
      </div>
    </div>
  );
}

function SectionTitle({ title }: { title: string }) {
  return (
    <div className="flex items-center gap-2 mb-3">
      <div className="w-0.5 h-4 rounded-full bg-[#4f7cff]" />
      <h3 className="text-xs font-semibold text-white uppercase tracking-wider">{title}</h3>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
//  Main Page
// ═══════════════════════════════════════════════════════════════════════════════

export default function Prospects() {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();

  // ── Filter state ─────────────────────────────────────────────────────────
  const [workflowId, setWorkflowId] = useState(searchParams.get("workflow_id") ?? "");
  const [tier, setTier] = useState("");
  const [minScore, setMinScore] = useState(0);
  const [industry, setIndustry] = useState("");
  const [hasEmail, setHasEmail] = useState(false);
  const [hasSignal, setHasSignal] = useState(false);
  const [sort, setSort] = useState("score_desc");
  // ── Data fetching ────────────────────────────────────────────────────────
  const { data: workflows, isLoading: workflowsLoading } = useQuery({
    queryKey: ["workflows-list"],
    queryFn: getWorkflowList,
  });

  const { data: prospectsData, isLoading } = useProspects({
    workflow_id: workflowId || undefined,
    min_score: minScore > 0 ? minScore : undefined,
    industry: industry || undefined,
    tier: tier || undefined,
    has_email: hasEmail || undefined,
    has_market_signal: hasSignal || undefined,
    sort: sort || undefined,
  });

  const companies = prospectsData?.items ?? [];
  const total = prospectsData?.total_raw ?? 0;

  // ── Sync workflow_id to URL ──────────────────────────────────────────────
  const handleWorkflowChange = useCallback((v: string) => {
    setWorkflowId(v);
    const next = new URLSearchParams(searchParams);
    if (v) {
      next.set("workflow_id", v);
    } else {
      next.delete("workflow_id");
    }
    next.delete("company_id");
    next.delete("selected_id");
    setSearchParams(next);
  }, [searchParams, setSearchParams]);

  const setTierFilter = useCallback((v: string) => {
    setTier(v);
    const next = new URLSearchParams(searchParams);
    next.delete("company_id");
    next.delete("selected_id");
    setSearchParams(next);
  }, [searchParams, setSearchParams]);

  return (
    <div className="h-full flex flex-col gap-3">
      {/* Header */}
      <div className="flex items-center justify-between shrink-0">
        <div>
          <h2 className="text-xl font-bold text-white">Prospects</h2>
          <p className="text-xs text-[--text-muted]">{total} companies discovered</p>
        </div>
      </div>

      {/* Filter bar */}
      <FilterBar
        workflowId={workflowId}
        onWorkflowChange={handleWorkflowChange}
        workflows={workflows}
        workflowsLoading={workflowsLoading}
        tier={tier}
        onTierChange={setTierFilter}
        minScore={minScore}
        onMinScoreChange={setMinScore}
        industry={industry}
        onIndustryChange={setIndustry}
        hasEmail={hasEmail}
        onHasEmailChange={setHasEmail}
        hasSignal={hasSignal}
        onHasSignalChange={setHasSignal}
        sort={sort}
        onSortChange={setSort}
      />

      {/* Main area: full width list */}
      <div className="flex-1 flex flex-col min-h-0 rounded-xl border overflow-hidden"
        style={{ borderColor: "var(--border)" }}>
        <div className="flex-1 overflow-y-auto">
          {isLoading ? (
            <div className="p-6 space-y-3">
              {[1, 2, 3, 4, 5].map((i) => (
                <div key={i} className="h-16 rounded-lg animate-pulse" style={{ backgroundColor: "var(--bg-secondary)" }} />
              ))}
            </div>
          ) : companies.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center p-6">
              <p className="text-sm text-[--text-muted]">No prospects yet</p>
              <p className="text-[11px] text-[--text-muted] mt-1">Start a workflow or adjust filters</p>
            </div>
          ) : (
            <div className="p-4 space-y-2">
              <p className="text-[10px] text-[--text-muted] px-2 pb-1">{companies.length} companies</p>
              <div className="flex flex-col gap-2">
                {companies.map((c) => (
                  <CompanyRow
                    key={c.id}
                    company={c}
                    selected={false}
                    onClick={() => navigate(`/prospects/${c.id}`)}
                  />
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
