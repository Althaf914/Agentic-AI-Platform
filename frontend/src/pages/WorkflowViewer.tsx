import { useParams, useNavigate } from "react-router-dom";
import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useWorkflowSocket } from "@/hooks/useWorkflowSocket";
import { useWorkflowStore } from "@/store/workflowStore";
import { startWorkflow, getWorkflowStatus } from "@/api/workflows";
import { cn } from "@/utils/cn";
import type { AgentDetail, ActivityEntry, CompanyResult } from "@/types/workflow";

// ─── Agent metadata ──────────────────────────────────────────────────────

const AGENT_META: Record<string, { icon: string; label: string; color: string }> = {
  planner:            { icon: "🧠", label: "Planner", color: "#a855f7" },
  search_strategy:    { icon: "🔍", label: "Search Strategy", color: "#4f7cff" },
  company_discovery:  { icon: "🏢", label: "Company Discovery", color: "#4f7cff" },
  validation:         { icon: "🛡️", label: "Validation", color: "#22d3a5" },
  tech_analysis:      { icon: "⚙️", label: "Tech Analysis", color: "#f59e0b" },
  market_intelligence:{ icon: "📡", label: "Market Intelligence", color: "#06b6d4" },
  decision_maker:     { icon: "👤", label: "Decision Maker", color: "#ec4899" },
  contact_enrichment: { icon: "📧", label: "Contact Enrichment", color: "#06b6d4" },
  qualification:      { icon: "📊", label: "Qualification", color: "#22d3a5" },
  recommendation_memory: { icon: "⭐", label: "Recommendations", color: "#a855f7" },
};

const DEFAULT_META = { icon: "🤖", label: "Agent", color: "#8888aa" };

// ─── Status helpers ──────────────────────────────────────────────────────

const STATUS_ICON: Record<string, string> = {
  idle: "○", running: "◉", completed: "✓", failed: "✗", skipped: "—",
};

const STATUS_COLOR: Record<string, string> = {
  idle: "text-[#55556a]",
  running: "text-[#4f7cff]",
  completed: "text-[#22d3a5]",
  failed: "text-[#ef4444]",
  skipped: "text-[#55556a]",
};

const STATUS_BG: Record<string, string> = {
  idle: "bg-white border-[--border]",
  running: "bg-[#00abe4]/5 border-[#00abe4] shadow-[0_0_15px_rgba(0,171,228,0.15)]",
  completed: "bg-[#10b981]/5 border-[#10b981]",
  failed: "bg-[#ef4444]/5 border-[#ef4444]",
  skipped: "bg-white border-[--border] opacity-60",
};

// ─── Activity event display config ───────────────────────────────────────

const ACTIVITY_CONFIG: Record<string, { icon: string; color: string }> = {
  company_discovered:   { icon: "●", color: "#4f7cff" },
  company_validated:    { icon: "✓", color: "#22d3a5" },
  company_rejected:     { icon: "✗", color: "#ef4444" },
  tech_detected:        { icon: "⚙", color: "#f59e0b" },
  contact_found:        { icon: "👤", color: "#06b6d4" },
  qualification_scored: { icon: "★", color: "#a855f7" },
  recommendation_created:{icon: "⭐", color: "#22d3a5" },
  agent_started:        { icon: "▶", color: "#4f7cff" },
  agent_completed:      { icon: "✓", color: "#22d3a5" },
  agent_failed:         { icon: "⚠", color: "#ef4444" },
  workflow_started:     { icon: "🚀", color: "#4f7cff" },
  workflow_completed:   { icon: "🏁", color: "#22d3a5" },
  workflow_failed:      { icon: "💥", color: "#ef4444" },
};

function WorkflowGraph({
  agents,
  expandedAgent,
  setExpandedAgent,
}: {
  agents: AgentDetail[];
  expandedAgent: string | null;
  setExpandedAgent: (name: string | null) => void;
}) {
  const navigate = useNavigate();

  return (
    <div className="rounded-xl border p-4 shadow-sm overflow-x-auto" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
      <div className="flex items-center gap-2 mb-3">
        <span className="text-sm">🌐</span>
        <h4 className="text-xs font-bold text-[--text-primary] uppercase tracking-wider">Agent Execution Graph</h4>
      </div>
      <div className="flex items-center min-w-[900px] py-4 px-2 select-none relative">
        {/* Connection Line */}
        <div className="absolute top-1/2 left-0 right-0 h-0.5 -translate-y-1/2 z-0" style={{ backgroundColor: "var(--border)" }} />

        {agents.map((agent) => {
          const meta = AGENT_META[agent.name] || DEFAULT_META;
          const isActive = agent.status === "running";
          const isCompleted = agent.status === "completed";
          const isFailed = agent.status === "failed";
          const isSkipped = agent.status === "skipped";

          // Node status styles
          const borderStyle =
            isActive ? "border-[#00ABE4] bg-[#00ABE4]/15 text-[#00ABE4] glow-pulse" :
            isCompleted ? "border-[#10B981] bg-[#10B981]/10 text-[#10B981]" :
            isFailed ? "border-[#EF4444] bg-[#EF4444]/10 text-[#EF4444]" :
            isSkipped ? "border-[--border] bg-[--bg-secondary] text-[--text-muted] opacity-60" :
            "border-[--border] bg-[--bg-secondary] text-[--text-muted]";

          return (
            <div key={agent.name} className="flex-1 flex flex-col items-center relative z-10">
              <div
                onClick={() => {
                  setExpandedAgent(expandedAgent === agent.name ? null : agent.name);
                  const el = document.getElementById(`agent-card-${agent.name}`);
                  if (el) el.scrollIntoView({ behavior: "smooth", block: "center" });
                }}
                className={cn(
                  "w-12 h-12 rounded-full border-2 flex items-center justify-center cursor-pointer transition-all duration-200 hover:scale-110",
                  borderStyle
                )}
              >
                <span className="text-xl">{meta.icon}</span>
              </div>
              <span className="text-[10px] font-semibold text-[--text-secondary] mt-2 text-center max-w-[80px] truncate" title={meta.label}>
                {meta.label}
              </span>
              {agent.duration !== undefined && isCompleted && (
                <span className="text-[8px] text-[--text-muted] font-mono mt-0.5">
                  {agent.duration.toFixed(1)}s
                </span>
              )}
              {isActive && (
                <span className="absolute -top-6 text-[8px] bg-[#00ABE4] text-white px-1.5 py-0.5 rounded-full animate-bounce font-medium">
                  active
                </span>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ═════════════════════════════════════════════════════════════════���═══════
// PAGE COMPONENT
// ═════════════════════════════════════════════════════════════════════════

export default function WorkflowViewer() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  // Connect WebSocket (all state flows into the store)
  useWorkflowSocket(id ?? null);

  const {
    agents, campaign, stats, activityFeed, isConnected,
    agentCardDetails, discoveredCompanies,
    results, resultsLoading, fetchResults,
  } = useWorkflowStore();

  const [elapsed, setElapsed] = useState(0);
  const [expandedAgent, setExpandedAgent] = useState<string | null>(null);
  const [workflowStatus, setWorkflowStatus] = useState<"pending" | "running" | "completed" | "failed">("pending");
  const [searchQuery, setSearchQuery] = useState("");
  const [sortField, setSortField] = useState<"name" | "qualification_score" | "status">("qualification_score");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");
  const centerRef = useRef<HTMLDivElement>(null);

  // Load initial status on mount / id change
  useEffect(() => {
    if (!id) return;

    useWorkflowStore.getState().resetWorkflow();

    const initWorkflow = async () => {
      try {
        const data = await getWorkflowStatus(id);
        setWorkflowStatus(data.status);

        // Hydrate timeline cards
        if (data.agent_logs && data.agent_logs.length > 0) {
          const loadedAgents = data.agent_logs.map((log: any, idx: number) => ({
            name: log.agent_name,
            status: log.status,
            duration: log.completed_at && log.started_at
              ? (new Date(log.completed_at).getTime() - new Date(log.started_at).getTime()) / 1000
              : undefined,
            error: log.error_message,
            index: idx,
            total: data.agent_logs.length,
          }));
          useWorkflowStore.getState().setAgents(loadedAgents);
        }

        // Hydrate campaign name
        if (data.campaign_name) {
          useWorkflowStore.getState().setPlannerInfo({
            name: data.campaign_name,
          });
        }

        // Set initial timer if running or completed
        if (data.started_at) {
          const start = new Date(data.started_at).getTime();
          const end = data.completed_at ? new Date(data.completed_at).getTime() : Date.now();
          setElapsed(Math.max(0, Math.floor((end - start) / 1000)));
        }

        // If completed, fetch full results
        if (data.status === "completed") {
          await fetchResults(id);
        }
      } catch (err) {
        console.error("Failed to load initial workflow status:", err);
      }
    };

    initWorkflow();
  }, [id]);

  // Elapsed timer
  useEffect(() => {
    if (workflowStatus !== "running" && workflowStatus !== "pending") return;
    const interval = setInterval(() => setElapsed((e) => e + 1), 1000);
    return () => clearInterval(interval);
  }, [workflowStatus]);

  // Watch for workflow completion
  useEffect(() => {
    if (campaign && workflowStatus === "pending") setWorkflowStatus("running");
  }, [campaign, workflowStatus]);

  // Watch final events
  useEffect(() => {
    const last = activityFeed[0];
    if (last?.eventType === "workflow_completed") {
      setWorkflowStatus("completed");
      if (id) fetchResults(id);
    }
    if (last?.eventType === "workflow_failed") setWorkflowStatus("failed");
  }, [activityFeed]);

  const formatTime = (s: number) => `${Math.floor(s / 60)}m ${s % 60}s`;

  const handleRunAgain = async () => {
    const configId = useWorkflowStore.getState().activeConfigId;
    if (!configId) { navigate("/workflow"); return; }
    try {
      const wf = await startWorkflow(configId);
      navigate(`/workflow/${wf.workflow_id || wf.id}`);
    } catch { navigate("/workflow"); }
  };

  const scrollToAgent = (name: string) => {
    const el = document.getElementById(`agent-card-${name}`);
    el?.scrollIntoView({ behavior: "smooth", block: "center" });
  };

  // ─── COMPLETED VIEW ──────────────────────────────────────────────────

  if (workflowStatus === "completed") {
    return (
      <div className="space-y-6">
        {/* Success banner */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-xl p-6 border bg-[#10b981]/5 border-[#10b981] shadow-[0_0_15px_rgba(16,185,129,0.08)]"
        >
          <h2 className="text-xl font-bold text-[#10b981] mb-2">Discovery Complete</h2>
          <p className="text-sm text-[--text-secondary]">
            Found {stats.companiesFound} companies · {stats.validated} validated ·
            {stats.contactsFound} contacts · {stats.recommendations} recommendations ready
          </p>
          <div className="flex gap-3 mt-4">
            <button
              onClick={() => navigate(`/prospects?workflow_id=${id}`)}
              className="px-5 py-2.5 rounded-lg bg-[#00ABE4] text-white text-sm font-medium hover:bg-[#0093c4] hover:shadow-[0_0_15px_rgba(0,171,228,0.3)] transition-all"
            >
              View All Prospects
            </button>
            <button
              onClick={() => navigate("/approvals")}
              className="px-5 py-2.5 rounded-lg border text-sm font-medium text-[--text-secondary] hover:text-[--accent-blue] transition-all bg-white"
              style={{ borderColor: "var(--border)" }}
            >
              Review Approvals ({stats.recommendations})
            </button>
            <button onClick={handleRunAgain}
              className="px-5 py-2.5 rounded-lg border text-sm text-[--text-muted] hover:text-[--accent-blue] transition-all bg-white"
              style={{ borderColor: "var(--border)" }}
            >
              Run Again
            </button>
          </div>
        </motion.div>

        {/* Workflow Execution Graph */}
        <WorkflowGraph
          agents={agents}
          expandedAgent={expandedAgent}
          setExpandedAgent={setExpandedAgent}
        />

        {/* 2x4 stats grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {[
            { icon: "🏢", label: "Companies Found", value: stats.companiesFound, color: "#4f7cff" },
            { icon: "🛡️", label: "Validated", value: stats.validated, color: "#22d3a5" },
            { icon: "⚙️", label: "Tech Analyzed", value: stats.techAnalyzed, color: "#f59e0b" },
            { icon: "📡", label: "Market Signals", value: stats.marketSignals, color: "#06b6d4" },
            { icon: "👤", label: "Contacts Found", value: stats.contactsFound, color: "#ec4899" },
            { icon: "📧", label: "Emails Found", value: stats.emailsFound, color: "#06b6d4" },
            { icon: "⭐", label: "Tier A Prospects", value: stats.tierA, color: "#a855f7" },
            { icon: "✓", label: "Ready for Review", value: stats.recommendations, color: "#22d3a5" },
          ].map((s) => (
            <motion.div
              key={s.label}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.3 }}
              className="rounded-xl p-4 border text-center"
              style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}
            >
              <span className="text-lg">{s.icon}</span>
              <p className="text-2xl font-bold mt-1" style={{ color: s.color }}>{s.value}</p>
              <p className="text-[10px] text-[--text-muted]">{s.label}</p>
            </motion.div>
          ))}
        </div>

        {/* Company results table */}
        <div className="rounded-xl border overflow-hidden"
          style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
          <div className="flex items-center justify-between px-4 py-3 border-b"
            style={{ borderColor: "var(--border)" }}>
            <h3 className="text-sm font-semibold text-white">
              📋 Company Results ({results?.summary.total_companies || 0})
            </h3>
            <div className="flex items-center gap-2">
              <input
                type="text"
                placeholder="Search companies..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="text-xs px-2.5 py-1.5 rounded-lg border bg-transparent text-[--text-secondary] w-48"
                style={{ borderColor: "var(--border)" }}
              />
              <select
                value={sortField}
                onChange={(e) => setSortField(e.target.value as any)}
                className="text-xs px-2 py-1.5 rounded-lg border bg-transparent text-[--text-secondary]"
                style={{ borderColor: "var(--border)" }}
              >
                <option value="qualification_score">Score</option>
                <option value="name">Name</option>
                <option value="status">Status</option>
              </select>
              <button
                onClick={() => setSortDir((d) => (d === "asc" ? "desc" : "asc"))}
                className="text-xs px-2 py-1.5 rounded-lg border bg-transparent text-[--text-secondary]"
                style={{ borderColor: "var(--border)" }}
              >
                {sortDir === "asc" ? "↑" : "↓"}
              </button>
            </div>
          </div>

          {resultsLoading && (
            <div className="flex items-center justify-center py-12 text-xs text-[--text-muted]">
              Loading results...
            </div>
          )}

          {!resultsLoading && results && (
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b text-[--text-muted]" style={{ borderColor: "var(--border)" }}>
                    <th className="text-left px-4 py-2 font-medium">Company</th>
                    <th className="text-left px-4 py-2 font-medium">Domain</th>
                    <th className="text-left px-4 py-2 font-medium">Industry</th>
                    <th className="text-left px-4 py-2 font-medium">Country</th>
                    <th className="text-right px-4 py-2 font-medium">Employees</th>
                    <th className="text-right px-4 py-2 font-medium">Score</th>
                    <th className="text-center px-4 py-2 font-medium">Status</th>
                    <th className="text-left px-4 py-2 font-medium">Contacts / Emails</th>
                    <th className="text-left px-4 py-2 font-medium">Funding</th>
                  </tr>
                </thead>
                <tbody>
                  {results.companies
                    .filter((c) =>
                      !searchQuery || c.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                      c.domain.toLowerCase().includes(searchQuery.toLowerCase()) ||
                      (c.industry || "").toLowerCase().includes(searchQuery.toLowerCase())
                    )
                    .sort((a, b) => {
                      let cmp = 0;
                      if (sortField === "name") cmp = a.name.localeCompare(b.name);
                      else if (sortField === "qualification_score") cmp = (a.qualification_score || 0) - (b.qualification_score || 0);
                      else cmp = a.status.localeCompare(b.status);
                      return sortDir === "asc" ? cmp : -cmp;
                    })
                    .map((c) => (
                      <CompanyRow key={c.id} company={c} />
                    ))}
                </tbody>
              </table>
            </div>
          )}

          {!resultsLoading && !results && (
            <div className="flex items-center justify-center py-12 text-xs text-[--text-muted]">
              No company data available yet
            </div>
          )}
        </div>

        <div className="flex gap-4 text-xs text-[--text-muted]">
          <span>Duration: {formatTime(elapsed)}</span>
          <span>Agents: {agents.filter((a) => a.status === "completed").length}/{agents.length}</span>
        </div>
      </div>
    );
  }

  // ─── FAILED VIEW ─────────────────────────────────────────────────────

  if (workflowStatus === "failed") {
    const failedAgent = agents.find((a) => a.status === "failed");
    return (
      <div className="space-y-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-xl p-6 border"
          style={{ backgroundColor: "#2e0d0d", borderColor: "#ef4444" }}
        >
          <h2 className="text-xl font-bold text-[#ef4444] mb-2">Workflow Failed</h2>
          {failedAgent && (
            <p className="text-sm text-[--text-secondary]">
              Agent "{failedAgent.name}" failed: {failedAgent.error || "Unknown error"}
            </p>
          )}
          <div className="flex gap-3 mt-4">
            <button onClick={handleRunAgain}
              className="px-5 py-2.5 rounded-lg bg-[#4f7cff] text-white text-sm font-medium transition-all"
            >
              Retry
            </button>
            <button onClick={() => navigate("/workflow")}
              className="px-5 py-2.5 rounded-lg border text-sm text-[--text-secondary] hover:text-white transition-all"
              style={{ borderColor: "var(--border)" }}
            >
              Back to Launcher
            </button>
          </div>
        </motion.div>
      </div>
    );
  }

  // ─── LIVE VIEW ───────────────────────────────────────────────────────

  return (
    <div className="h-full flex flex-col gap-4">
      {/* Top bar */}
      <div className="flex items-center justify-between shrink-0">
        <div className="flex items-center gap-3">
          <span className="text-xs font-mono px-2 py-1 rounded bg-white text-[--text-secondary] border border-[--border] shadow-sm">
            {id?.slice(0, 8)}...
          </span>
          <span className="flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-full bg-[#00abe4]/10 text-[#00abe4] border border-[#00abe4]/30">
            <span className="w-2 h-2 rounded-full bg-[#00abe4] animate-pulse" />
            Running
          </span>
          {isConnected && (
            <span className="text-[10px] text-[#10b981] flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-[#10b981]" /> Live
            </span>
          )}
          <span className="text-xs text-[--text-muted]">{formatTime(elapsed)}</span>
          {campaign && (
            <span className="text-xs text-[--text-secondary] ml-2 font-medium">
              Campaign: {campaign.name}
            </span>
          )}
        </div>
      </div>

      {/* Workflow Execution Graph */}
      <WorkflowGraph
        agents={agents}
        expandedAgent={expandedAgent}
        setExpandedAgent={setExpandedAgent}
      />

      {/* Two-column layout */}
      <div className="flex gap-4 flex-1 min-h-0">
        {/* LEFT: Timeline sidebar */}
        <div className="w-[200px] shrink-0 rounded-xl border overflow-hidden flex flex-col"
          style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
          <div className="px-3 py-2.5 border-b text-xs font-semibold text-[--text-primary] flex items-center gap-2 font-sans"
            style={{ borderColor: "var(--border)" }}>
            <span>⏱</span> Timeline
          </div>
          <div className="flex-1 overflow-y-auto p-2 space-y-0.5">
            {agents.length === 0 && (
              <p className="text-[10px] text-[--text-muted] text-center py-4">Waiting for agents...</p>
            )}
            {agents.map((agent, i) => {
              const meta = AGENT_META[agent.name] || DEFAULT_META;
              return (
                <button
                  key={agent.name}
                  onClick={() => scrollToAgent(agent.name)}
                  className="w-full flex items-center gap-2 px-2 py-1.5 rounded-lg text-left hover:bg-[--bg-card-hover] transition-colors text-xs"
                >
                  <span className={`w-4 text-center text-sm ${STATUS_COLOR[agent.status]}`}>
                    {STATUS_ICON[agent.status]}
                  </span>
                  <span className="flex-1 truncate text-[--text-secondary]">
                    {meta.label}
                  </span>
                  {agent.duration !== undefined && agent.status === "completed" && (
                    <span className="text-[10px] text-[--text-muted] shrink-0 font-mono">
                      {agent.duration.toFixed(1)}s
                    </span>
                  )}
                  {agent.status === "skipped" && (
                    <span className="text-[8px] px-1 py-0.5 rounded bg-[#55556a]/20 text-[#55556a]">Skip</span>
                  )}
                </button>
              );
            })}
          </div>
        </div>

        {/* CENTER: Agent cards (scrollable) */}
        <div ref={centerRef} className="flex-1 overflow-y-auto space-y-3 pr-1">
          {/* Planner reasoning card */}
          {campaign && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="rounded-xl border p-4"
              style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}
            >
              <div className="flex items-center gap-2 mb-2">
                <span className="text-sm">🧠</span>
                <span className="text-xs font-semibold text-[#a855f7]">Planner Strategy</span>
              </div>
              <div className="space-y-1 text-xs text-[--text-secondary]">
                <p>Campaign: {campaign.name}</p>
                {campaign.strategySummary && <p>Strategy: {campaign.strategySummary}</p>}
                {campaign.reasoning && <p>Reason: {campaign.reasoning}</p>}
                <p>Agents: {agents.filter((a) => a.status !== "idle").length} active / {agents.filter((a) => a.status === "skipped").length} skipped</p>
              </div>
            </motion.div>
          )}

          {/* Agent cards */}
          {agents.map((agent) => (
            <AgentCard
              key={agent.name}
              agent={agent}
              isExpanded={expandedAgent === agent.name}
              onToggle={() => setExpandedAgent(expandedAgent === agent.name ? null : agent.name)}
              cardDetail={agentCardDetails[agent.name]}
            />
          ))}

          {/* Empty state */}
          {agents.length === 0 && (
            <div className="flex items-center justify-center h-40 text-xs text-[--text-muted]">
              <motion.div
                animate={{ opacity: [0.3, 1, 0.3] }}
                transition={{ duration: 2, repeat: Infinity }}
                className="text-center"
              >
                <p className="text-lg mb-2">⏳</p>
                <p>Waiting for workflow to start...</p>
              </motion.div>
            </div>
          )}

          {/* Bottom stats bar */}
          <div className="sticky bottom-0 flex items-center justify-around px-6 py-3 rounded-xl border mt-2 shadow-sm"
            style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
            {[
              { icon: "🏢", label: "Found", value: stats.companiesFound, color: "var(--accent-blue)" },
              { icon: "✓", label: "Valid", value: stats.validated, color: "var(--accent-green)" },
              { icon: "✗", label: "Rej", value: stats.rejected, color: "var(--accent-red)" },
              { icon: "👤", label: "Contacts", value: stats.contactsFound, color: "#06b6d4" },
              { icon: "📧", label: "Emails", value: stats.emailsFound, color: "var(--text-primary)" },
              { icon: "⭐", label: "Recs", value: stats.recommendations, color: "var(--accent-purple)" },
            ].map((s) => (
              <div key={s.label} className="text-center flex-1 border-r last:border-r-0" style={{ borderColor: "var(--border)" }}>
                <p className="text-base font-bold" style={{ color: s.color }}>{s.value}</p>
                <p className="text-[10px] text-[--text-muted] font-semibold mt-0.5">{s.icon} {s.label}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* BOTTOM: Live activity feed (full width below, fixed height) */}
      <div className="h-64 shrink-0 rounded-xl border overflow-hidden flex flex-col"
        style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
        <div className="px-4 py-3 border-b text-sm font-semibold text-[--text-primary] flex items-center gap-2"
          style={{ borderColor: "var(--border)" }}>
          <span>⚡</span> Live Activity Logs
          <span className="ml-auto text-xs text-[--text-muted] font-medium">{activityFeed.length} events</span>
        </div>
        <div className="flex-1 overflow-y-auto p-4">
          {activityFeed.length === 0 ? (
            <p className="text-xs text-[--text-muted] text-center py-8">Waiting for events...</p>
          ) : (
            <div className="flex flex-col gap-2">
              <AnimatePresence initial={false}>
                {activityFeed.map((entry) => (
                  <ActivityRow key={entry.id} entry={entry} />
                ))}
              </AnimatePresence>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ═════════════════════════════════════════════════════════════════════════
// AGENT CARD COMPONENT
// ═════════════════════════════════════════════════════════════════════════

function AgentCard({
  agent,
  isExpanded,
  onToggle,
  cardDetail,
}: {
  agent: AgentDetail;
  isExpanded: boolean;
  onToggle: () => void;
  cardDetail?: { topTechnologies?: string[]; tierDistribution?: { A: number; B: number; C: number } };
}) {
  const meta = AGENT_META[agent.name] || DEFAULT_META;
  const statusBg = STATUS_BG[agent.status] || STATUS_BG.idle;

  // Border colors for animations
  const borderColor =
    agent.status === "running" ? meta.color :
    agent.status === "completed" ? "#22d3a5" :
    agent.status === "failed" ? "#ef4444" :
    "var(--border)";

  return (
    <motion.div
      id={`agent-card-${agent.name}`}
      layout
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={cn("rounded-xl border overflow-hidden transition-all", statusBg)}
      style={{ borderColor: agent.status === "running" ? borderColor : undefined }}
    >
      {/* Card header */}
      <div className="flex items-center gap-3 px-4 py-3 cursor-pointer" onClick={onToggle}>
        <span className="text-lg">{meta.icon}</span>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-white truncate">{meta.label}</span>
            <StatusBadge status={agent.status} />
          </div>
          {/* Sub-step detail */}
          {agent.status === "running" && agent.substepDetail && (
            <motion.p
              key={agent.substepName}
              initial={{ opacity: 0, y: -4 }}
              animate={{ opacity: 1, y: 0 }}
              className="text-[10px] text-[--text-secondary] mt-0.5 truncate"
            >
              {agent.substepDetail}
            </motion.p>
          )}
          {/* Completed summary */}
          {agent.status === "completed" && agent.outputSummary && (
            <p className="text-[10px] text-[#22d3a5] mt-0.5">{agent.outputSummary}</p>
          )}
          {/* Error message */}
          {agent.status === "failed" && agent.error && (
            <p className="text-[10px] text-[#ef4444] mt-0.5 truncate">{agent.error}</p>
          )}
        </div>
        {agent.duration !== undefined && (
          <span className="text-[10px] text-[--text-muted] shrink-0">{agent.duration.toFixed(1)}s</span>
        )}
        <span className="text-[10px] text-[--text-muted] shrink-0">{isExpanded ? "▲" : "▼"}</span>
      </div>

      {/* Progress bar (running only) */}
      {agent.status === "running" && (
        <div className="px-4 pb-1">
          <div className="w-full h-1 rounded-full bg-[#1a1a3a] overflow-hidden">
            <motion.div
              className="h-full rounded-full"
              style={{ backgroundColor: meta.color }}
              initial={{ width: 0 }}
              animate={{
                width: agent.progressPct ? `${agent.progressPct}%` : "45%",
              }}
              transition={{ duration: 0.5 }}
            />
          </div>
        </div>
      )}

      {/* Expandable detail section */}
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="px-4 pb-3 pt-1 border-t text-xs"
              style={{ borderColor: "var(--border)" }}>
              {/* Tech analysis detail */}
              {agent.name === "tech_analysis" && cardDetail?.topTechnologies && (
                <div>
                  <p className="text-[--text-muted] mb-1">Top Technologies:</p>
                  <div className="flex flex-wrap gap-1">
                    {cardDetail.topTechnologies.slice(0, 8).map((tech) => (
                      <span key={tech} className="text-[10px] px-1.5 py-0.5 rounded bg-[#f59e0b]/10 text-[#f59e0b] border border-[#f59e0b]/20">
                        {tech}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Qualification detail */}
              {agent.name === "qualification" && cardDetail?.tierDistribution && (
                <div>
                  <p className="text-[--text-muted] mb-1">Tier Distribution:</p>
                  <div className="flex gap-3">
                    <span className="text-[#a855f7]">A: {cardDetail.tierDistribution.A}</span>
                    <span className="text-[#4f7cff]">B: {cardDetail.tierDistribution.B}</span>
                    <span className="text-[--text-muted]">C: {cardDetail.tierDistribution.C}</span>
                  </div>
                </div>
              )}

              {/* Discovery detail */}
              {agent.name === "company_discovery" && (
                <div>
                  <p className="text-[--text-muted] mb-1">Recently Discovered:</p>
                  <p className="text-[10px] text-[--text-secondary]">See activity feed for details</p>
                </div>
              )}

              {/* Default: show output */}
              {agent.outputSummary && agent.name !== "tech_analysis" && agent.name !== "qualification" && (
                <p className="text-[10px] text-[--text-secondary]">{agent.outputSummary}</p>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

// ═════════════════════════════════════════════════════════════════════════
// STATUS BADGE
// ═════════════════════════════════════════════════════════════════════════

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    idle: "bg-[#55556a]/20 text-[#55556a]",
    running: "bg-[#4f7cff]/20 text-[#4f7cff]",
    completed: "bg-[#22d3a5]/20 text-[#22d3a5]",
    failed: "bg-[#ef4444]/20 text-[#ef4444]",
    skipped: "bg-[#55556a]/20 text-[#55556a]",
  };

  return (
    <span className={cn("text-[9px] px-1.5 py-0.5 rounded font-medium", colors[status] || colors.idle)}>
      {status.toUpperCase()}
    </span>
  );
}

// ═════════════════════════════════════════════════════════════════════════
// ACTIVITY ROW
// ═════════════════════════════════════════════════════════════════════════

function ActivityRow({ entry }: { entry: ActivityEntry }) {
  const cfg = ACTIVITY_CONFIG[entry.eventType];
  const meta = AGENT_META[entry.agentName];

  // Format the event-specific message
  const message = formatActivityMessage(entry);

  return (
    <motion.div
      initial={{ opacity: 0, x: -10, height: 0 }}
      animate={{ opacity: 1, x: 0, height: "auto" }}
      exit={{ opacity: 0, height: 0 }}
      transition={{ duration: 0.2 }}
      className="flex items-center gap-3 px-3 py-1.5 rounded-lg text-[13px] hover:bg-[--bg-card-hover] transition-colors"
    >
      <span className="shrink-0 w-4 text-center text-sm" style={{ color: cfg?.color || "white" }}>
        {cfg?.icon || "●"}
      </span>
      <span className="flex-1 leading-normal text-[--text-secondary] min-w-0 font-medium">
        {message}
      </span>
      {meta && (
        <span className="text-[10px] text-[--text-muted] shrink-0 px-2.5 py-0.5 rounded-full border border-[--border] bg-[--bg-secondary]">
          {meta.label}
        </span>
      )}
    </motion.div>
  );
}

// ═════════════════════════════════════════════════════════════════════════
// COMPANY ROW
// ══════════════════════════��══════════════════════════════════════════════

function CompanyRow({ company }: { company: CompanyResult }) {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const statusColor =
    company.status === "validated" ? "#22d3a5" :
    company.status === "rejected" ? "#ef4444" : "#888";

  const primaryContact = company.contacts?.find((c) => c.is_primary_persona);
  const emailList = company.contacts?.filter((c) => c.email).map((c) => c.email) || [];

  return (
    <tr
      onClick={() => navigate(`/prospects/${company.id}`)}
      className="border-t cursor-pointer hover:bg-[--bg-card-hover] transition-colors group"
      style={{ borderColor: "var(--border)" }}
    >
      <td className="px-4 py-2.5 text-white font-medium flex items-center gap-1.5">
        {company.name}
        <span className="text-[10px] text-[#4f7cff] opacity-0 group-hover:opacity-100 transition-opacity">↗</span>
      </td>
      <td className="px-4 py-2.5 text-[--text-secondary]">{company.domain}</td>
      <td className="px-4 py-2.5 text-[--text-secondary]">{company.industry || "—"}</td>
      <td className="px-4 py-2.5 text-[--text-secondary]">{company.country || "—"}</td>
      <td className="px-4 py-2.5 text-right text-[--text-secondary]">
        {company.employee_count ? company.employee_count.toLocaleString() : "—"}
      </td>
      <td className="px-4 py-2.5 text-right">
        {company.qualification_score != null ? (
          <span className="font-bold" style={{
            color: company.qualification_score >= 70 ? "#22d3a5" :
                   company.qualification_score >= 40 ? "#f59e0b" : "#ef4444"
          }}>
            {company.qualification_score.toFixed(0)}
          </span>
        ) : (
          <span className="text-[--text-muted]">—</span>
        )}
      </td>
      <td className="px-4 py-2.5 text-center">
        <span className="text-[10px] px-1.5 py-0.5 rounded font-medium" style={{
          backgroundColor: `${statusColor}20`,
          color: statusColor,
        }}>
          {company.status.toUpperCase()}
        </span>
      </td>
      <td className="px-4 py-2.5">
        {primaryContact ? (
          <div className="text-[--text-secondary]">
            <span className="text-white">{primaryContact.full_name}</span>
            {primaryContact.email && (
              <span className="block text-[10px] text-[#22d3a5]">{primaryContact.email}</span>
            )}
          </div>
        ) : emailList.length > 0 ? (
          <span className="text-[10px] text-[#22d3a5]">{emailList[0]}</span>
        ) : (
          <span className="text-[--text-muted]">—</span>
        )}
        {company.contacts.length > 1 && (
          <span className="text-[10px] text-[--text-muted]">+{company.contacts.length - 1} more</span>
        )}
      </td>
      <td className="px-4 py-2.5 text-[--text-secondary]">{company.funding_stage || "—"}</td>
    </tr>
  );
}

function formatActivityMessage(entry: ActivityEntry): string {
  const { eventType, payload } = entry;
  const d = payload;

  switch (eventType) {
    case "company_discovered":
      return `${d.company_name || "Unknown"} (${d.domain || ""})`;
    case "company_validated":
      return `${d.company_name || "Unknown"} — ${d.checks_passed || 0}/${d.checks_total || 12} checks`;
    case "company_rejected":
      return `${d.company_name || "Unknown"} — ${d.reason || "rejected"}`;
    case "tech_detected": {
      const stack = (d.tech_stack as string[]) || [];
      return `${d.company_name || "Unknown"} — ${stack.join(", ") || "no tech detected"}`;
    }
    case "contact_found": {
      const name = d.contact_name as string;
      const role = d.role as string;
      const source = d.source as string;
      const parts = [name, role ? `(${role})` : ""].filter(Boolean);
      const tags = [];
      if (d.has_email) tags.push("email");
      if (d.has_linkedin) tags.push("LI");
      return `${parts.join(" ")} @ ${d.company_name || ""}${tags.length ? ` [${tags.join(",")}]` : ""}`;
    }
    case "qualification_scored":
      return `${d.company_name || "Unknown"} — ${d.score || 0}/100 (Tier ${d.tier || "?"})`;
    case "recommendation_created":
      return `${d.company_name || "Unknown"} — ${d.priority || "standard"} priority`;
    case "agent_started":
      return `${d.agent_name || entry.agentName} started`;
    case "agent_completed":
      return `${d.agent_name || entry.agentName} done in ${d.duration_seconds || 0}s`;
    case "agent_failed":
      return `${d.agent_name || entry.agentName} failed: ${(d.error as string || "").slice(0, 50)}`;
    case "workflow_started":
      return `Campaign "${d.campaign_name || "Untitled"}" started`;
    case "workflow_completed":
      return `Workflow complete in ${d.duration_seconds || 0}s`;
    case "workflow_failed":
      return `Workflow failed: ${(d.error as string || "").slice(0, 60)}`;
    default:
      return (d.message as string) || `${eventType}`;
  }
}
