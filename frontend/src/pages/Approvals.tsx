import { useState, useMemo, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useApprovals } from "@/hooks/useApprovals";
import OutreachEditor from "@/components/OutreachEditor";
import type {
  ApprovalItem,
  ApprovalStats,
  ApprovalStatus,
  BulkAction,
  ApprovalBuyingCommittee,
} from "@/types/approval";
import { REJECTION_REASONS } from "@/types/approval";

// ═══════════════════════════════════════════════════════════════════════════════
//  Constants
// ═══════════════════════════════════════════════════════════════════════════════

const TIER_COLORS: Record<string, string> = {
  A: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
  B: "bg-amber-500/15 text-amber-400 border-amber-500/30",
  C: "bg-zinc-500/15 text-zinc-400 border-zinc-500/30",
};

const PRIORITY_COLORS: Record<string, string> = {
  high: "text-emerald-400",
  medium: "text-amber-400",
  low: "text-zinc-400",
};

function scoreColor(val: number): string {
  if (val >= 70) return "text-emerald-400";
  if (val >= 40) return "text-amber-400";
  return "text-rose-400";
}

function getInitials(name: string): string {
  const parts = name.split(" ").filter(Boolean);
  if (parts.length >= 2) return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
  return name.slice(0, 2).toUpperCase();
}

// ═══════════════════════════════════════════════════════════════════════════════
//  Stats Bar
// ═══════════════════════════════════════════════════════════════════════════════

function StatsBar({
  stats,
  activeTab,
  setActiveTab,
}: {
  stats: ApprovalStats;
  activeTab: string;
  setActiveTab: (tab: "pending" | "approved" | "rejected") => void;
}) {
  return (
    <div
      className="flex items-center gap-2 px-4 py-2 rounded-xl border text-xs bg-[--bg-card] shadow-sm flex-wrap"
      style={{ borderColor: "var(--border)" }}
    >
      <span className="text-[--text-secondary] font-semibold mr-2">Approval Queue</span>
      <div className="w-px h-4 bg-[--border] hidden md:block" />

      {/* Tabs */}
      <div className="flex items-center gap-1">
        <button
          onClick={() => setActiveTab("pending")}
          className={`px-3 py-1.5 rounded-lg border font-medium transition-all ${
            activeTab === "pending"
              ? "bg-amber-500/10 text-amber-500 border-amber-500/30 shadow-sm font-semibold"
              : "border-transparent text-[--text-secondary] hover:bg-[--bg-card-hover]"
          }`}
        >
          ⏳ Pending ({stats.pending})
        </button>

        <button
          onClick={() => setActiveTab("approved")}
          className={`px-3 py-1.5 rounded-lg border font-medium transition-all ${
            activeTab === "approved"
              ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30 shadow-sm font-semibold"
              : "border-transparent text-[--text-secondary] hover:bg-[--bg-card-hover]"
          }`}
        >
          ✅ Approved ({stats.approved})
        </button>

        <button
          onClick={() => setActiveTab("rejected")}
          className={`px-3 py-1.5 rounded-lg border font-medium transition-all ${
            activeTab === "rejected"
              ? "bg-rose-500/10 text-rose-400 border-rose-500/30 shadow-sm font-semibold"
              : "border-transparent text-[--text-secondary] hover:bg-[--bg-card-hover]"
          }`}
        >
          ❌ Rejected ({stats.rejected})
        </button>
      </div>

      <div className="w-px h-4 bg-[--border] hidden md:block" />
      <span className="text-[--text-secondary] ml-auto">Avg score: <span className="text-[--text-primary] font-bold">{stats.avgScore}</span></span>
      <div className="w-px h-4 bg-[--border] hidden md:block" />
      <span className="text-[--text-secondary]">High priority: <span className="text-amber-500 font-bold">{stats.highPriority}</span></span>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
//  Rejection Modal
// ════════════════════════════════════════════��══════════════════════════════════

function RejectModal({
  companyName,
  onSubmit,
  onClose,
}: {
  companyName: string;
  onSubmit: (reason: string, note: string) => void;
  onClose: () => void;
}) {
  const [reason, setReason] = useState("");
  const [note, setNote] = useState("");

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}>
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="w-full max-w-md rounded-xl border p-5 shadow-xl"
        style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}
      >
        <h3 className="text-sm font-semibold text-white mb-1">Reject {companyName}</h3>
        <p className="text-[11px] text-[--text-muted] mb-4">
          This feeds back to improve future qualification scoring.
        </p>

        <label className="text-[10px] text-[--text-muted] uppercase tracking-wider mb-1.5 block">Reason *</label>
        <select
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          className="w-full px-3 py-2 text-xs rounded-lg border bg-[--bg-secondary] border-[--border] text-white focus:outline-none focus:border-red-400 mb-3"
        >
          <option value="">Select a reason...</option>
          {REJECTION_REASONS.map((r) => (
            <option key={r.value} value={r.value}>{r.label}</option>
          ))}
        </select>

        <label className="text-[10px] text-[--text-muted] uppercase tracking-wider mb-1.5 block">Note (optional)</label>
        <textarea
          value={note}
          onChange={(e) => setNote(e.target.value)}
          placeholder="Additional notes for the sales team..."
          rows={3}
          className="w-full px-3 py-2 text-xs rounded-lg border bg-[--bg-secondary] border-[--border] text-white placeholder:text-[--text-muted] resize-none focus:outline-none focus:border-red-400 mb-4"
        />

        <div className="flex items-center gap-2 justify-end">
          <button onClick={onClose}
            className="px-3 py-1.5 text-xs rounded-lg border border-[--border] text-[--text-secondary] hover:text-white transition-colors">
            Cancel
          </button>
          <button
            onClick={() => onSubmit(reason, note)}
            disabled={!reason}
            className="px-4 py-1.5 text-xs font-medium rounded-lg bg-red-500 text-white hover:bg-red-600 transition-colors disabled:opacity-40"
          >
            Confirm Reject
          </button>
        </div>
      </motion.div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
//  Pending Card (full detail)
// ═══════════════════════════════════════════════════════════════════════════════

function PendingCard({
  item,
  onApprove,
  onReject,
  isSubmitting,
}: {
  item: ApprovalItem;
  onApprove: (id: string, data: ApproveData) => void;
  onReject: (id: string, reason: string, note: string) => void;
  isSubmitting: boolean;
}) {
  const [expanded, setExpanded] = useState(false);
  const [showApproveFlow, setShowApproveFlow] = useState(false);
  const [showRejectFlow, setShowRejectFlow] = useState(false);
  const [emailExpanded, setEmailExpanded] = useState(false);
  const [comment, setComment] = useState("");
  const [channel, setChannel] = useState<"email" | "linkedin" | "both">("email");
  const [schedule, setSchedule] = useState<"now" | "later">("now");
  const [scheduleDate, setScheduleDate] = useState("");
  const [editingEmail, setEditingEmail] = useState(false);

  const breakdown = item.score_breakdown as Record<string, unknown> | null;
  const tier = item.tier;

  // Top 3 winning dimensions (highest score)
  const topDims = useMemo(() => {
    if (!breakdown) return [];
    const dims = [
      { key: "industry_match", label: "Industry", score: (breakdown.industry_match as Record<string, number>)?.score ?? 0 },
      { key: "tech_stack_match", label: "Tech", score: (breakdown.tech_stack_match as Record<string, number>)?.score ?? 0 },
      { key: "funding_stage", label: "Funding", score: (breakdown.funding_stage as Record<string, number>)?.score ?? 0 },
      { key: "hiring_signals", label: "Hiring", score: (breakdown.hiring_signals as Record<string, number>)?.score ?? 0 },
      { key: "location_match", label: "Location", score: (breakdown.location_match as Record<string, number>)?.score ?? 0 },
      { key: "employee_range", label: "Size", score: (breakdown.employee_range as Record<string, number>)?.score ?? 0 },
      { key: "revenue_tier", label: "Revenue", score: (breakdown.revenue_tier as Record<string, number>)?.score ?? 0 },
      { key: "decision_makers_found", label: "Deciders", score: (breakdown.decision_makers_found as Record<string, number>)?.score ?? 0 },
    ];
    return dims.sort((a, b) => b.score - a.score).slice(0, 3);
  }, [breakdown]);

  const primaryContact = item.contacts.find((c) => c.is_primary_persona) ?? item.contacts[0];
  const secondaryContacts = item.contacts.filter((c) => !c.is_primary_persona || c.id !== primaryContact?.id).slice(0, 3);

  // Buying committee secondary list
  const committeeSummary = useMemo(() => {
    const bc = item.buying_committee as ApprovalBuyingCommittee | null;
    if (!bc) return "";
    const names: string[] = [];
    if (bc.secondary_personas?.length) {
      bc.secondary_personas.forEach((p) => {
        const role = p.role?.replace(/^(VP|Director|Head|Chief|Manager)\s+/i, "") ?? "";
        names.push(role ? `${p.role}` : p.full_name);
      });
    }
    if (bc.influencers?.length) {
      bc.influencers.slice(0, 2).forEach((p) => {
        names.push(`${p.full_name} (influencer)`);
      });
    }
    if (names.length === 0 && secondaryContacts.length > 0) {
      secondaryContacts.forEach((c) => names.push(c.role));
    }
    return names.length ? `Also target: ${names.join(", ")}` : "";
  }, [item.buying_committee, secondaryContacts]);

  // Email preview first 2 lines
  const emailPreviewLines = useMemo(() => {
    return item.outreach_template?.split("\n").slice(0, 2).join("\n") ?? "";
  }, [item.outreach_template]);

  const handleConfirmApprove = () => {
    onApprove(item.id, {
      comment,
      channel,
      scheduled_at: schedule === "later" ? scheduleDate : "now",
    });
  };

  const tierBadge = tier && TIER_COLORS[tier]
    ? <span className={`text-[9px] px-1.5 py-0.5 rounded-full border font-semibold ${TIER_COLORS[tier]}`}>{tier}</span>
    : null;

  return (
    <motion.div
      layout
      className="rounded-xl border overflow-hidden text-left"
      style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}
    >
      {/* ── Main card body (always visible) ────────────────────────────────── */}
      <div className="p-4">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-start">
          {/* LEFT COLUMN: Company details & Contact: 7 cols */}
          <div className="lg:col-span-7 space-y-4">
            {/* Logo, name, score */}
            <div className="flex items-start justify-between gap-3">
              <div className="flex items-center gap-3">
                {/* Logo / initial */}
                <div className="w-10 h-10 rounded-xl overflow-hidden bg-[--bg-secondary] shrink-0 flex items-center justify-center border border-[--border]">
                  {item.company_logo_url ? (
                    <img src={item.company_logo_url} alt="" className="w-full h-full object-contain"
                      onError={(e) => { (e.target as HTMLImageElement).style.display = "none"; }} />
                  ) : (
                    <span className="text-xs font-bold text-[--text-muted]">{getInitials(item.company_name)}</span>
                  )}
                </div>
                <div>
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-base font-semibold text-white">{item.company_name}</span>
                    {tierBadge}
                    <span className={`text-[10px] font-medium px-2 py-0.5 rounded bg-[--bg-secondary] border border-[--border] ${PRIORITY_COLORS[item.priority] ?? ""}`}>
                      {item.priority === "high" ? "🔥" : item.priority === "medium" ? "●" : "○"} {item.priority}
                    </span>
                  </div>
                  <div className="flex items-center gap-2 mt-1 text-xs">
                    <span className="text-[11px] text-[--text-muted]">{item.company_domain}</span>
                    <span className="text-[--text-muted]">•</span>
                    {item.company_industry && <span className="text-[#4f7cff] font-semibold text-[11px]">{item.company_industry}</span>}
                  </div>
                </div>
              </div>
              
              {/* Score */}
              {item.qualification_score != null && (
                <div className="text-right shrink-0 bg-[--bg-secondary] border border-[--border] px-3 py-1 rounded-xl">
                  <span className={`text-lg font-bold ${scoreColor(item.qualification_score)}`}>{Math.round(item.qualification_score)}</span>
                  <span className="text-[10px] text-[--text-muted]">/100</span>
                </div>
              )}
            </div>

            {/* Score breakdown dimensions */}
            {topDims.length > 0 && (
              <div className="flex items-center gap-2 flex-wrap">
                {topDims.map((d) => (
                  <span key={d.key} className={`text-[9px] px-2 py-0.5 rounded-full ${scoreColor(d.score).replace("text-", "bg-")}/10 ${scoreColor(d.score)} border border-[--border]`}>
                    {d.label} {Math.round(d.score)}
                  </span>
                ))}
              </div>
            )}

            {/* Primary Contact Profile Card */}
            {primaryContact && (
              <div className="rounded-xl border border-[--border] p-3.5 bg-[--bg-secondary]/40 space-y-2">
                <p className="text-[9px] text-[--text-muted] uppercase tracking-wider font-bold">Primary Contact Profile</p>
                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 rounded-full bg-[#4f7cff]/20 text-[#4f7cff] flex items-center justify-center text-xs font-bold shrink-0">
                    {getInitials(primaryContact.full_name)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-xs font-semibold text-white">{primaryContact.full_name}</span>
                      {primaryContact.linkedin_url && (
                        <a href={primaryContact.linkedin_url} target="_blank" rel="noreferrer"
                          className="text-[9px] px-1.5 py-0.5 rounded bg-[#0a66c2]/10 text-[#0077b5] font-semibold border border-[#0a66c2]/20 hover:bg-[#0a66c2]/20 transition-colors">LinkedIn</a>
                      )}
                    </div>
                    <p className="text-[11px] text-[--text-muted] mt-0.5">{primaryContact.role}</p>
                    {primaryContact.email && (
                      <div className="flex items-center gap-2 mt-1.5 text-[11px] flex-wrap">
                        <span className="text-[#00ABE4] truncate font-medium">{primaryContact.email}</span>
                        <span className={`text-[9px] px-1.5 py-0.2 rounded-full font-medium ${
                          (primaryContact.email_confidence ?? 0) >= 0.8 
                            ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" 
                            : "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                        }`}>
                          ✓ {Math.round((primaryContact.email_confidence ?? 0) * 100)}% verified
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}
            
            {committeeSummary && (
              <p className="text-[10px] text-[--text-muted] italic bg-[--bg-secondary]/20 px-3 py-1.5 rounded-lg border border-[--border] border-dashed font-sans">{committeeSummary}</p>
            )}
          </div>

          {/* RIGHT COLUMN: Triggers, outreach and actions: 5 cols */}
          <div className="lg:col-span-5 space-y-4">
            {/* Market trigger */}
            {item.market_trigger && (
              <div className="rounded-xl px-3 py-2.5 bg-amber-500/10 border border-amber-500/20">
                <div className="flex items-start gap-2">
                  <span className="text-amber-400 text-sm mt-0.5">⚡</span>
                  <div>
                    <span className="text-[9px] text-amber-400 uppercase tracking-wider font-bold block mb-0.5">Market Trigger Signal</span>
                    <p className="text-[11px] text-amber-300 leading-relaxed font-medium">{item.market_trigger}</p>
                  </div>
                </div>
              </div>
            )}

            {/* Outreach template collapse */}
            {item.outreach_template && (
              <div className="rounded-xl border border-[--border] p-3 bg-[--bg-secondary]/20">
                <button
                  onClick={() => setEmailExpanded(!emailExpanded)}
                  className="text-[11px] text-[#00ABE4] hover:underline flex items-center justify-between w-full"
                >
                  <span className="font-semibold text-[--text-secondary]">📧 Outreach Template Preview</span>
                  <span>{emailExpanded ? "Hide ▲" : "Show ▼"}</span>
                </button>
                {emailExpanded && (
                  <div className="mt-2 p-2.5 rounded-lg text-[11px] text-[--text-secondary] font-mono whitespace-pre-wrap border border-[--border] bg-[--bg-card] max-h-48 overflow-y-auto">
                    {item.outreach_template}
                  </div>
                )}
              </div>
            )}

            {/* Actions panel */}
            <div className="flex items-center gap-2 pt-2 border-t border-[--border]">
              <button
                onClick={() => { setShowApproveFlow(!showApproveFlow); setShowRejectFlow(false); }}
                disabled={isSubmitting}
                className="flex-1 px-3 py-2 text-xs font-semibold rounded-lg bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 hover:bg-emerald-500/30 transition-colors disabled:opacity-40"
              >
                ✓ Approve
              </button>
              <button
                onClick={() => { setShowRejectFlow(true); setShowApproveFlow(false); }}
                disabled={isSubmitting}
                className="flex-1 px-3 py-2 text-xs font-semibold rounded-lg border border-rose-500/30 text-rose-400 hover:bg-rose-500/10 transition-colors disabled:opacity-40"
              >
                ✗ Reject
              </button>
              <button
                onClick={() => setExpanded(!expanded)}
                className="px-3 py-2 text-xs rounded-lg border border-[--border] text-[--text-secondary] hover:text-white transition-colors"
              >
                {expanded ? "Less ↑" : "More ↓"}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* ── Approve flow (expanded in-place) ───────────────────────────────── */}
      <AnimatePresence>
        {showApproveFlow && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="border-t overflow-hidden"
            style={{ borderColor: "var(--border)" }}
          >
            <div className="p-4 space-y-3" style={{ backgroundColor: "var(--bg-secondary)" }}>
              {/* Email editor */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[10px] text-[--text-muted] uppercase tracking-wider">Outreach template</span>
                  <button
                    onClick={() => setEditingEmail(!editingEmail)}
                    className={`text-[10px] px-2 py-0.5 rounded transition-colors ${editingEmail ? "bg-[#4f7cff]/20 text-[#4f7cff]" : "text-[--text-muted] hover:text-white"}`}
                  >
                    {editingEmail ? "Done editing" : "Edit"}
                  </button>
                </div>
                <OutreachEditor
                  subject={item.outreach_subject ?? ""}
                  body={item.outreach_template}
                  variables={[
                    { key: "{{first_name}}", label: "First name" },
                    { key: "{{company_name}}", label: "Company name" },
                    { key: "{{market_trigger}}", label: "Market trigger" },
                    { key: "{{sender_name}}", label: "Sender name" },
                  ]}
                  readOnly={!editingEmail}
                />
              </div>

              {/* Comment */}
              <div>
                <label className="text-[10px] text-[--text-muted] uppercase tracking-wider mb-1 block">Notes for sales rep</label>
                <textarea
                  value={comment}
                  onChange={(e) => setComment(e.target.value)}
                  placeholder="Key context, talking points, or objections to address..."
                  rows={2}
                  className="w-full px-3 py-2 text-xs rounded-lg border bg-[--bg-card] border-[--border] text-white placeholder:text-[--text-muted] resize-none focus:outline-none focus:border-emerald-500"
                />
              </div>

              {/* Channel selector */}
              <div className="flex items-center gap-3">
                <label className="text-[10px] text-[--text-muted] uppercase tracking-wider">Channel</label>
                {(["email", "linkedin", "both"] as const).map((c) => (
                  <button
                    key={c}
                    onClick={() => setChannel(c)}
                    className={`text-[10px] px-2.5 py-1 rounded-lg border transition-colors ${
                      channel === c
                        ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/30"
                        : "border-[--border] text-[--text-secondary] hover:text-white"
                    }`}
                  >
                    {c === "email" ? "Email" : c === "linkedin" ? "LinkedIn" : "Both"}
                  </button>
                ))}

                <div className="w-px h-4 bg-[--border]" />

                {/* Schedule */}
                <label className="text-[10px] text-[--text-muted] uppercase tracking-wider">Schedule</label>
                <button
                  onClick={() => setSchedule("now")}
                  className={`text-[10px] px-2 py-1 rounded-lg border transition-colors ${
                    schedule === "now"
                      ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/30"
                      : "border-[--border] text-[--text-secondary]"
                  }`}
                >
                  Send now
                </button>
                <button
                  onClick={() => setSchedule("later")}
                  className={`text-[10px] px-2 py-1 rounded-lg border transition-colors ${
                    schedule === "later"
                      ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/30"
                      : "border-[--border] text-[--text-secondary]"
                  }`}
                >
                  Schedule
                </button>
                {schedule === "later" && (
                  <input
                    type="date"
                    value={scheduleDate}
                    onChange={(e) => setScheduleDate(e.target.value)}
                    className="px-2 py-1 text-[10px] rounded-lg border bg-[--bg-card] border-[--border] text-white"
                  />
                )}
              </div>

              {/* Confirm */}
              <div className="flex items-center gap-2 justify-end pt-2 border-t border-[--border]">
                <button
                  onClick={() => setShowApproveFlow(false)}
                  className="px-3 py-1.5 text-[11px] rounded-lg border border-[--border] text-[--text-secondary] hover:text-white"
                >
                  Cancel
                </button>
                <button
                  onClick={handleConfirmApprove}
                  disabled={isSubmitting}
                  className="px-4 py-1.5 text-[11px] font-medium rounded-lg bg-emerald-500 text-white hover:bg-emerald-600 transition-colors disabled:opacity-40"
                >
                  {isSubmitting ? "Approving..." : "Confirm Approve"}
                </button>
              </div>
            </div>
          </motion.div>
        )}

        {/* ── Reject flow (modal) ─────────────────────────────────────────── */}
        {showRejectFlow && (
          <RejectModal
            companyName={item.company_name}
            onSubmit={(reason, note) => onReject(item.id, reason, note)}
            onClose={() => setShowRejectFlow(false)}
          />
        )}
      </AnimatePresence>

      {/* ── Expanded detail (More button) ──────────────────────────────────── */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="border-t overflow-hidden"
            style={{ borderColor: "var(--border)" }}
          >
            <div className="p-4 space-y-3 text-xs" style={{ backgroundColor: "var(--bg-secondary)" }}>
              {/* Talking points */}
              {item.talking_points && item.talking_points.length > 0 && (
                <div>
                  <p className="text-[10px] text-[--text-muted] uppercase tracking-wider mb-1">Talking points</p>
                  <ul className="list-disc list-inside space-y-0.5">
                    {item.talking_points.map((pt, i) => (
                      <li key={i} className="text-[11px] text-[--text-secondary]">{pt}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* LinkedIn message */}
              {item.linkedin_message && (
                <div>
                  <p className="text-[10px] text-[--text-muted] uppercase tracking-wider mb-1">LinkedIn message</p>
                  <div className="p-2.5 rounded-lg border border-[--border] text-[11px] text-[--text-secondary]"
                    style={{ backgroundColor: "var(--bg-card)" }}>
                    {item.linkedin_message}
                  </div>
                </div>
              )}

              {/* Confidence */}
              <div className="flex items-center gap-3 text-[10px] text-[--text-muted]">
                <span>Confidence: <span className="text-white">{(item.confidence * 100).toFixed(0)}%</span></span>
                <span>Channel: <span className="text-white">{item.outreach_channel ?? "email"}</span></span>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
//  Decision Card (approved / rejected — collapsed)
// ═══════════════════════════════════════════════════════════════════════════════

function DecisionCard({ item }: { item: ApprovalItem }) {
  const [expanded, setExpanded] = useState(false);
  const [emailExpanded, setEmailExpanded] = useState(false);
  
  const isApproved = item.status === "approved";
  const tier = item.tier;
  const tierBadge = tier && TIER_COLORS[tier]
    ? <span className={`text-[9px] px-1.5 py-0.5 rounded-full border font-semibold ${TIER_COLORS[tier]}`}>{tier}</span>
    : null;

  const dateStr = item.decided_at
    ? new Date(item.decided_at).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })
    : "";

  const primaryContact = useMemo(() => {
    return item.contacts?.find((c) => c.is_primary_persona);
  }, [item.contacts]);

  const secondaryContacts = useMemo(() => {
    return item.contacts?.filter((c) => !c.is_primary_persona) || [];
  }, [item.contacts]);

  const topDims = useMemo(() => {
    if (!item.score_breakdown) return [];
    return Object.entries(item.score_breakdown)
      .map(([k, v]) => ({ key: k, label: k.replace(/_/g, " "), score: Number(v) }))
      .sort((a, b) => b.score - a.score)
      .slice(0, 3);
  }, [item.score_breakdown]);

  const committeeSummary = useMemo(() => {
    const bc = item.buying_committee;
    if (!bc) return "";
    const names: string[] = [];
    if (bc.secondary_personas?.length) {
      bc.secondary_personas.forEach((p) => {
        const role = p.role?.replace(/^(VP|Director|Head|Chief|Manager)\s+/i, "") ?? "";
        names.push(role ? `${p.role}` : p.full_name);
      });
    }
    if (bc.influencers?.length) {
      bc.influencers.slice(0, 2).forEach((p) => {
        names.push(`${p.full_name} (influencer)`);
      });
    }
    if (names.length === 0 && secondaryContacts.length > 0) {
      secondaryContacts.forEach((c) => names.push(c.role));
    }
    return names.length ? `Also target: ${names.join(", ")}` : "";
  }, [item.buying_committee, secondaryContacts]);

  return (
    <motion.div
      layout
      className="rounded-xl border overflow-hidden text-left"
      style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}
    >
      {/* ── Main card body (always visible) ────────────────────────────────── */}
      <div className="p-4 space-y-3">
        {/* Row 1: Tier badge + priority + score */}
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-center gap-2">
            {/* Logo / initial */}
            <div className="w-8 h-8 rounded-lg overflow-hidden bg-[--bg-secondary] shrink-0 flex items-center justify-center">
              {item.company_logo_url ? (
                <img src={item.company_logo_url} alt="" className="w-full h-full object-contain"
                  onError={(e) => { (e.target as HTMLImageElement).style.display = "none"; }} />
              ) : (
                <span className="text-[10px] font-bold text-[--text-muted]">{getInitials(item.company_name)}</span>
              )}
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <span className="text-sm font-semibold text-white">{item.company_name}</span>
                {tierBadge}
                <span className={`text-[10px] font-medium ${PRIORITY_COLORS[item.priority] ?? ""}`}>
                  {item.priority === "high" ? "🔥" : item.priority === "medium" ? "●" : "○"} {item.priority}
                </span>
              </div>
              <div className="flex items-center gap-2 mt-0.5">
                <span className="text-[10px] text-[--text-muted]">{item.company_domain}</span>
                {item.company_industry && <span className="text-[10px] text-[#4f7cff]">{item.company_industry}</span>}
              </div>
            </div>
          </div>
          {/* Score */}
          {item.qualification_score != null && (
            <div className="text-right shrink-0">
              <span className={`text-lg font-bold ${scoreColor(item.qualification_score)}`}>{Math.round(item.qualification_score)}</span>
              <span className="text-[10px] text-[--text-muted]">/100</span>
            </div>
          )}
        </div>

        {/* Row 2: Mini breakdown */}
        {topDims.length > 0 && (
          <div className="flex items-center gap-2">
            {topDims.map((d) => (
              <span key={d.key} className={`text-[9px] px-1.5 py-0.5 rounded-full ${scoreColor(d.score).replace("text-", "bg-")}/10 ${scoreColor(d.score)}`}>
                {d.label} {Math.round(d.score)}
              </span>
            ))}
          </div>
        )}

        {/* Row 3: Market trigger */}
        {item.market_trigger && (
          <div className="rounded-lg px-3 py-2 bg-amber-500/10 border border-amber-500/20">
            <div className="flex items-start gap-2">
              <span className="text-amber-400 text-xs mt-0.5">⚡</span>
              <p className="text-[11px] text-amber-300 leading-relaxed">{item.market_trigger}</p>
            </div>
          </div>
        )}

        {/* Row 4: Primary contact */}
        {primaryContact && (
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-full bg-[#4f7cff]/20 text-[#4f7cff] flex items-center justify-center text-[9px] font-bold shrink-0">
              {getInitials(primaryContact.full_name)}
            </div>
            <span className="text-xs text-white font-medium">{primaryContact.full_name}</span>
            <span className="text-[10px] text-[--text-muted]">{primaryContact.role}</span>
            {primaryContact.linkedin_url && (
              <a href={primaryContact.linkedin_url} target="_blank" rel="noreferrer"
                className="text-[9px] px-1.5 py-0.5 rounded bg-[#0a66c2]/20 text-[#0a66c2] font-medium">in</a>
            )}
            {primaryContact.email && (
              <span className={`text-[10px] ${(primaryContact.email_confidence ?? 0) >= 0.8 ? "text-emerald-400" : "text-amber-400"}`}>
                ● {Math.round((primaryContact.email_confidence ?? 0) * 100)}%
              </span>
            )}
          </div>
        )}

        {/* Row 5: Buying committee summary */}
        {committeeSummary && (
          <p className="text-[10px] text-[--text-muted] italic">{committeeSummary}</p>
        )}

        {/* Row 6: Outreach preview (collapsed) */}
        {item.outreach_template && (
          <div>
            <button
              onClick={() => setEmailExpanded(!emailExpanded)}
              className="text-[10px] text-[#4f7cff] hover:underline flex items-center gap-1"
            >
              {emailExpanded ? "Hide" : "Show"} outreach preview {emailExpanded ? "▲" : "▼"}
            </button>
            {emailExpanded && (
              <div className="mt-1.5 p-3 rounded-lg text-[11px] text-[--text-secondary] font-mono whitespace-pre-wrap border border-[--border]"
                style={{ backgroundColor: "var(--bg-secondary)" }}>
                {item.outreach_template}
              </div>
            )}
          </div>
        )}

        {/* Row 7: Decision Details badge */}
        {isApproved ? (
          <div className="rounded-lg p-3 bg-emerald-500/10 border border-emerald-500/20 text-xs">
            <div className="flex items-start gap-2">
              <span className="text-emerald-400 text-sm mt-0.5">✅</span>
              <div>
                <p className="font-semibold text-emerald-400 text-[12px]">Outreach Approved</p>
                <p className="text-[11px] text-[--text-secondary] mt-0.5">
                  Approved {item.reviewer_name ? `by ${item.reviewer_name}` : ""} {dateStr ? `on ${dateStr}` : ""}
                  {item.outreach_channel && ` via ${item.outreach_channel}`}
                </p>
                {item.comment && (
                  <div className="mt-2 text-[11px] text-[--text-secondary] bg-[--bg-secondary] p-2.5 rounded-lg border border-[--border] whitespace-pre-wrap">
                    <span className="text-[10px] text-[--text-muted] block uppercase font-bold mb-1">Notes for rep:</span>
                    {item.comment}
                  </div>
                )}
              </div>
            </div>
          </div>
        ) : (
          <div className="rounded-lg p-3 bg-rose-500/10 border border-rose-500/20 text-xs">
            <div className="flex items-start gap-2">
              <span className="text-rose-400 text-sm mt-0.5">❌</span>
              <div>
                <p className="font-semibold text-rose-400 text-[12px]">Outreach Rejected</p>
                <p className="text-[11px] text-[--text-secondary] mt-0.5">
                  Rejected {dateStr ? `on ${dateStr}` : ""}
                  {item.rejection_reason && ` for reason: "${item.rejection_reason.replace(/_/g, ' ')}"`}
                </p>
                {item.comment && (
                  <div className="mt-2 text-[11px] text-[--text-secondary] bg-[--bg-secondary] p-2.5 rounded-lg border border-[--border] whitespace-pre-wrap">
                    <span className="text-[10px] text-[--text-muted] block uppercase font-bold mb-1">Comments:</span>
                    {item.comment}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* ── Toggle details button ── */}
        <div className="flex justify-end pt-1">
          <button
            onClick={() => setExpanded(!expanded)}
            className="px-3 py-1.5 text-[11px] rounded-lg border border-[--border] text-[--text-secondary] hover:text-white transition-colors"
          >
            {expanded ? "Less ↑" : "More ↓"}
          </button>
        </div>
      </div>

      {/* ── Expanded detail (More button) ──────────────────────────────────── */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="border-t overflow-hidden"
            style={{ borderColor: "var(--border)" }}
          >
            <div className="p-4 space-y-3 text-xs" style={{ backgroundColor: "var(--bg-secondary)" }}>
              {/* Talking points */}
              {item.talking_points && item.talking_points.length > 0 && (
                <div>
                  <p className="text-[10px] text-[--text-muted] uppercase tracking-wider mb-1">Talking points</p>
                  <ul className="list-disc list-inside space-y-0.5">
                    {item.talking_points.map((pt, i) => (
                      <li key={i} className="text-[11px] text-[--text-secondary]">{pt}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* LinkedIn message */}
              {item.linkedin_message && (
                <div>
                  <p className="text-[10px] text-[--text-muted] uppercase tracking-wider mb-1">LinkedIn message</p>
                  <div className="p-2.5 rounded-lg border border-[--border] text-[11px] text-[--text-secondary]"
                    style={{ backgroundColor: "var(--bg-card)" }}>
                    {item.linkedin_message}
                  </div>
                </div>
              )}

              {/* Confidence */}
              <div className="flex items-center gap-3 text-[10px] text-[--text-muted]">
                <span>Confidence: <span className="text-white">{(item.confidence * 100).toFixed(0)}%</span></span>
                <span>Channel: <span className="text-white">{item.outreach_channel ?? "email"}</span></span>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

// ═════════════════════════════════════════════════════════════════════════════���═
//  Kanban Column
// ═══════════════════════════════════════════════════════════════════════════════

interface ApproveData {
  comment: string;
  channel: "email" | "linkedin" | "both";
  scheduled_at: string;
}

// ═══════════════════════════════════════════════════════════════════════════════
//  Main Page
// ═══════════════════════════════════════════════════════════════════════════════

export default function Approvals() {
  const { approvals, stats, isLoading, submitApproval, isSubmitting } = useApprovals("all");
  const [viewMode, setViewMode] = useState<"kanban" | "list">("kanban");
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [activeTab, setActiveTab] = useState<"pending" | "approved" | "rejected">("pending");

  // Split into columns
  const pending = useMemo(() => approvals.filter((a) => a.status === "pending"), [approvals]);
  const approved = useMemo(() => approvals.filter((a) => a.status === "approved"), [approvals]);
  const rejected = useMemo(() => approvals.filter((a) => a.status === "rejected"), [approvals]);

  const filteredListItems = useMemo(() => {
    return approvals.filter((a) => a.status === activeTab);
  }, [approvals, activeTab]);

  // ── Approve handler ───────────────────────────────────────────────────────
  const handleApprove = useCallback((id: string, data: ApproveData) => {
    submitApproval({
      id,
      decision: {
        status: "approved",
        comment: data.comment,
        channel: data.channel,
        scheduled_at: data.scheduled_at,
      },
    });
  }, [submitApproval]);

  // ── Reject handler ────────────────────────────────────────────────────────
  const handleReject = useCallback((id: string, reason: string, note: string) => {
    submitApproval({
      id,
      decision: {
        status: "rejected",
        rejection_reason: reason,
        comment: note,
      },
    });
  }, [submitApproval]);

  // ── Bulk actions ───────────────────────────────────────────────────────────
  const handleBulkAction = useCallback((action: BulkAction) => {
    switch (action) {
      case "approve_all_a": {
        const tierA = pending.filter((a) => a.tier === "A");
        tierA.forEach((a) => {
          submitApproval({
            id: a.id,
            decision: { status: "approved" },
          });
        });
        break;
      }
      case "reject_all_c": {
        const tierC = pending.filter((a) => a.tier === "C");
        tierC.forEach((a) => {
          submitApproval({
            id: a.id,
            decision: { status: "rejected", rejection_reason: "not_in_target_market" },
          });
        });
        break;
      }
      case "approve_selected": {
        selectedIds.forEach((id) => {
          submitApproval({ id, decision: { status: "approved" } });
        });
        setSelectedIds(new Set());
        break;
      }
      case "reject_selected": {
        selectedIds.forEach((id) => {
          submitApproval({ id, decision: { status: "rejected", rejection_reason: "not_in_target_market" } });
        });
        setSelectedIds(new Set());
        break;
      }
    }
  }, [pending, selectedIds, submitApproval]);

  const toggleSelect = useCallback((id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }, []);

  return (
    <div className="h-full flex flex-col gap-3">
      {/* Stats bar */}
      <StatsBar stats={stats} activeTab={activeTab} setActiveTab={setActiveTab} />

      {/* View toggle + bulk actions */}
      <div className="flex items-center justify-between shrink-0">
        <div className="flex items-center gap-2">
          <button
            onClick={() => setViewMode("kanban")}
            className={`px-3 py-1.5 text-xs rounded-lg border transition-all ${
              viewMode === "kanban"
                ? "bg-[#4f7cff]/20 text-[#4f7cff] border-[#4f7cff]/40"
                : "border-[--border] text-[--text-secondary] hover:text-white"
            }`}
          >
            Card View
          </button>
          <button
            onClick={() => setViewMode("list")}
            className={`px-3 py-1.5 text-xs rounded-lg border transition-all ${
              viewMode === "list"
                ? "bg-[#4f7cff]/20 text-[#4f7cff] border-[#4f7cff]/40"
                : "border-[--border] text-[--text-secondary] hover:text-white"
            }`}
          >
            Table View
          </button>
        </div>

        {/* Bulk actions */}
        <div className="flex items-center gap-2">
          {/* Select all checkbox for pending */}
          {selectedIds.size > 0 && (
            <span className="text-[10px] text-[--text-muted]">{selectedIds.size} selected</span>
          )}

          <button
            onClick={() => handleBulkAction("approve_all_a")}
            disabled={isSubmitting || pending.filter((a) => a.tier === "A").length === 0}
            className="px-2.5 py-1 text-[10px] rounded-lg bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 hover:bg-emerald-500/30 transition-colors disabled:opacity-30"
          >
            Approve all Tier A
          </button>
          <button
            onClick={() => handleBulkAction("reject_all_c")}
            disabled={isSubmitting || pending.filter((a) => a.tier === "C").length === 0}
            className="px-2.5 py-1 text-[10px] rounded-lg bg-rose-500/10 text-rose-400 border border-rose-500/20 hover:bg-rose-500/20 transition-colors disabled:opacity-30"
          >
            Reject all Tier C
          </button>

          {selectedIds.size > 0 && (
            <>
              <button
                onClick={() => handleBulkAction("approve_selected")}
                className="px-2.5 py-1 text-[10px] rounded-lg bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
              >
                Approve selected
              </button>
              <button
                onClick={() => handleBulkAction("reject_selected")}
                className="px-2.5 py-1 text-[10px] rounded-lg bg-rose-500/10 text-rose-400 border border-rose-500/20"
              >
                Reject selected
              </button>
              <button
                onClick={() => setSelectedIds(new Set())}
                className="px-2.5 py-1 text-[10px] text-[--text-muted] hover:text-white"
              >
                Clear
              </button>
            </>
          )}
        </div>
      </div>

      {/* Loading */}
      {isLoading && (
        <div className="flex-1 space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-32 rounded-xl animate-pulse" style={{ backgroundColor: "var(--bg-secondary)" }} />
          ))}
        </div>
      )}

      {/* Cards View */}
      {!isLoading && viewMode === "kanban" && (
        <div className="flex-1 overflow-y-auto space-y-4 pr-1">
          {activeTab === "pending" && (
            <div className="space-y-4">
              {pending.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-20 border rounded-xl" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
                  <p className="text-2xl mb-2">⏳</p>
                  <p className="text-xs text-[--text-muted]">No pending prospects</p>
                </div>
              ) : (
                pending.map((item) => (
                  <PendingCard
                    key={item.id}
                    item={item}
                    onApprove={handleApprove}
                    onReject={handleReject}
                    isSubmitting={isSubmitting}
                  />
                ))
              )}
            </div>
          )}
          {activeTab === "approved" && (
            <div className="space-y-4">
              {approved.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-20 border rounded-xl" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
                  <p className="text-2xl mb-2">✅</p>
                  <p className="text-xs text-[--text-muted]">No approved prospects</p>
                </div>
              ) : (
                approved.map((item) => (
                  <DecisionCard key={item.id} item={item} />
                ))
              )}
            </div>
          )}
          {activeTab === "rejected" && (
            <div className="space-y-4">
              {rejected.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-20 border rounded-xl" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
                  <p className="text-2xl mb-2">❌</p>
                  <p className="text-xs text-[--text-muted]">No rejected prospects</p>
                </div>
              ) : (
                rejected.map((item) => (
                  <DecisionCard key={item.id} item={item} />
                ))
              )}
            </div>
          )}
        </div>
      )}

      {/* List view */}
      {!isLoading && viewMode === "list" && (
        <div className="flex-1 overflow-y-auto space-y-1 rounded-xl border"
          style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
          <table className="w-full text-xs">
            <thead>
              <tr className="text-[10px] text-[--text-muted] uppercase tracking-wider border-b border-[--border]">
                <th className="text-left px-3 py-2 w-8">
                  <input type="checkbox"
                    onChange={(e) => {
                      if (e.target.checked) setSelectedIds(new Set(pending.map((a) => a.id)));
                      else setSelectedIds(new Set());
                    }}
                    checked={selectedIds.size === pending.length && pending.length > 0}
                    className="accent-[#4f7cff]"
                  />
                </th>
                <th className="text-left px-3 py-2">Company</th>
                <th className="text-left px-3 py-2">Tier</th>
                <th className="text-left px-3 py-2">Score</th>
                <th className="text-left px-3 py-2">Priority</th>
                <th className="text-left px-3 py-2">Status</th>
                <th className="text-right px-3 py-2">Decided</th>
              </tr>
            </thead>
            <tbody>
              {filteredListItems.length === 0 ? (
                <tr><td colSpan={7} className="text-center py-12 text-[--text-muted]">No approvals found</td></tr>
              ) : (
                filteredListItems.map((a) => (
                  <tr key={a.id} className="border-b border-[--border] hover:bg-[--bg-secondary] transition-colors">
                    {a.status === "pending" ? (
                      <td className="px-3 py-2">
                        <input type="checkbox" checked={selectedIds.has(a.id)}
                          onChange={() => toggleSelect(a.id)} className="accent-[#4f7cff]" />
                      </td>
                    ) : <td className="px-3 py-2" />}
                    <td className="px-3 py-2">
                      <span className="text-white font-medium">{a.company_name}</span>
                      <span className="text-[--text-muted] ml-2">{a.company_domain}</span>
                    </td>
                    <td className="px-3 py-2">
                      {a.tier && TIER_COLORS[a.tier]
                        ? <span className={`text-[9px] px-1.5 py-0.5 rounded-full border font-semibold ${TIER_COLORS[a.tier]}`}>{a.tier}</span>
                        : <span className="text-[--text-muted]">—</span>}
                    </td>
                    <td className={`px-3 py-2 font-medium ${scoreColor(a.qualification_score ?? 0)}`}>
                      {a.qualification_score != null ? Math.round(a.qualification_score) : "—"}
                    </td>
                    <td className="px-3 py-2">
                      <span className={`text-[10px] ${PRIORITY_COLORS[a.priority] ?? ""}`}>{a.priority}</span>
                    </td>
                    <td className="px-3 py-2">
                      <span className={`text-[9px] px-1.5 py-0.5 rounded-full font-medium ${
                        a.status === "approved" ? "bg-emerald-500/15 text-emerald-400"
                        : a.status === "rejected" ? "bg-rose-500/15 text-rose-400"
                        : "bg-amber-500/15 text-amber-400"
                      }`}>{a.status}</span>
                    </td>
                    <td className="px-3 py-2 text-right text-[--text-muted]">
                      {a.decided_at ? new Date(a.decided_at).toLocaleDateString() : "—"}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
