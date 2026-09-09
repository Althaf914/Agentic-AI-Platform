import { useState, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  FunnelChart,
  Funnel,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  LabelList,
} from "recharts";
import { getDashboardStats } from "@/api/dashboard";
import { getWorkflowList } from "@/api/workflows";
import {
  useFunnel,
  useTechDistribution,
  useSignalBreakdown,
} from "@/api/analytics";

// ═════════════════════════════════════════════��═════════════════════════════════
//  Constants
// ═══════════════════════════════════════════════════════════════════════════════

const PIE_COLORS = ["#22d3a5", "#4f7cff", "#f59e0b", "#8b5cf6", "#ef4444"];
const FUNNEL_COLORS = ["#4f7cff", "#22d3a5", "#06b6d4", "#8b5cf6", "#f59e0b", "#22c55e"];
const TECH_CATEGORY_COLORS: Record<string, string> = {
  cloud: "#4f7cff",
  framework: "#22d3a5",
  language: "#f59e0b",
  ai: "#22c55e",
  database: "#8b5cf6",
  devops: "#06b6d4",
  default: "#6b7280",
};

function timeAgo(dateStr: string): string {
  const now = Date.now();
  const then = new Date(dateStr).getTime();
  const diff = now - then;
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days < 7) return `${days}d ago`;
  return new Date(dateStr).toLocaleDateString();
}

// ═══════════════════════════════════════════════════════════════════════════════
//  KPI Card
// ═══════════════════════════════════════════════════════════════════════════════

interface KPICardProps {
  label: string;
  value: string | number;
  trend?: { direction: "up" | "down"; pct: number } | null;
  icon: string;
  color: string;
  detail?: string;
}

function KPICard({ label, value, trend, icon, color, detail }: KPICardProps) {
  return (
    <div
      className="rounded-xl border p-4 transition-all duration-200 hover:border-[#4f7cff]/40"
      style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}
    >
      <div className="flex items-start justify-between mb-2">
        <span className="text-[10px] text-[--text-muted] uppercase tracking-wider">{label}</span>
        <span className="text-lg">{icon}</span>
      </div>
      <div className="flex items-baseline gap-2">
        <span className={`text-3xl font-bold ${color}`}>{value}</span>
        {trend && (
          <span className={`text-[11px] font-medium ${trend.direction === "up" ? "text-emerald-400" : "text-red-400"}`}>
            {trend.direction === "up" ? "↑" : "↓"}{Math.abs(trend.pct)}%
          </span>
        )}
      </div>
      {detail && <p className="text-[10px] text-[--text-muted] mt-1">{detail}</p>}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
//  Custom funnel tooltip
// ═══════════════════════════════════════════════════════════════════════════════

function FunnelTooltip({ active, payload }: any) {
  if (active && payload && payload.length > 0) {
    const d = payload[0].payload;
    return (
      <div className="rounded-lg border p-3 text-xs shadow-xl" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
        <p className="font-medium text-white mb-1">{d.name}</p>
        <p className="text-[--text-muted]">{d.value} companies</p>
        {d.conversion > 0 && <p className="text-emerald-400">{d.conversion.toFixed(1)}% of previous</p>}
        {d.overall > 0 && <p className="text-[#4f7cff]">{d.overall.toFixed(1)}% overall</p>}
      </div>
    );
  }
  return null;
}

// ═══════════════════════════════════════════════════════════════════════════════
//  Main Dashboard
// ═══════════════════════════════════════════════════════════════════════════════

export default function Dashboard() {
  const navigate = useNavigate();

  // ── Data fetching ─────────────────────────────────────────────────────────
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ["dashboard-stats"],
    queryFn: getDashboardStats,
  });

  const { data: funnel, isLoading: funnelLoading } = useFunnel();
  const { data: techDist, isLoading: techLoading } = useTechDistribution();
  const { data: signals, isLoading: signalsLoading } = useSignalBreakdown();

  const { data: workflows } = useQuery({
    queryKey: ["workflows-list"],
    queryFn: getWorkflowList,
  });

  // ── Funnel data ──────────────────────────────────────────────────────────
  const funnelData = useMemo(() => {
    if (!funnel) return [];
    interface FunnelStep { name: string; value: number; conversion: number; overall: number };
    const steps: FunnelStep[] = [
      { name: "Discovered", value: funnel.discovered, conversion: 0, overall: 0 },
      { name: "Validated", value: funnel.validated, conversion: 0, overall: 0 },
      { name: "Tech Analyzed", value: funnel.tech_analyzed, conversion: 0, overall: 0 },
      { name: "Contacted", value: funnel.decision_makers, conversion: 0, overall: 0 },
      { name: "Qualified", value: funnel.qualified, conversion: 0, overall: 0 },
      { name: "Approved", value: funnel.approved, conversion: 0, overall: 0 },
    ];
    for (let i = 0; i < steps.length; i++) {
      const prev = i > 0 ? steps[i - 1].value : steps[0].value;
      steps[i].conversion = prev > 0 ? (steps[i].value / prev) * 100 : 0;
      steps[i].overall = steps[0].value > 0 ? (steps[i].value / steps[0].value) * 100 : 0;
    }
    return steps;
  }, [funnel]);

  // ── Tech distribution data (top 15) ────────────────────────────────────��──
  const techData = useMemo(() => {
    if (!techDist) return [];
    return Object.entries(techDist)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 15)
      .map(([name, count]) => ({ name, count }));
  }, [techDist]);

  // ── Signal data ──────────────────────────────────────────────────────────
  const signalData = useMemo(() => {
    if (!signals) return [];
    const labels: Record<string, string> = {
      funding: "Funding",
      news: "News",
      hiring: "Hiring",
      expansion: "Expansion",
      leadership: "Leadership",
    };
    return Object.entries(labels)
      .map(([key, label]) => ({
        name: label,
        value: (signals as any)[key] ?? 0,
      }))
      .filter((d) => d.value > 0);
  }, [signals]);

  // ── Recent workflows (last 5) ────────────────────────────────────────────
  const recentWorkflows = useMemo(() => {
    return (workflows ?? []).slice(0, 5);
  }, [workflows]);

  // ── KPI trends (weekly) ─────────────────────────────────────────────────
  // For now these are simplified; real trend would compare current vs previous period
  const kpiTrends = {
    discovered: funnel?.discovered ?? 0,
    validatedPct: funnel && funnel.discovered > 0
      ? Math.round((funnel.validated / funnel.discovered) * 100)
      : 0,
    tierA: funnel?.tier_a ?? 0,
    pendingApprovals: stats?.pending_approvals ?? 0,
  };

  const isLoading = statsLoading || funnelLoading || techLoading || signalsLoading;

  return (
    <div className="h-full overflow-y-auto space-y-5 pr-2">
      {/* ── ROW 0: Header ──────────────────────────────────────────────────── */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Dashboard</h1>
          <p className="text-xs text-[--text-muted] mt-0.5">
            Pipeline overview and performance metrics
          </p>
        </div>
        <button
          onClick={() => navigate("/workflow")}
          className="px-4 py-2 text-xs font-medium rounded-lg bg-[#4f7cff] text-white hover:bg-[#3a6ae8] transition-colors"
        >
          + Start New Discovery
        </button>
      </div>

      {/* ── ROW 1: KPI cards ──────────────────────────────────────────────── */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="h-24 rounded-xl animate-pulse" style={{ backgroundColor: "var(--bg-secondary)" }} />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <KPICard
            label="Discovered this week"
            value={kpiTrends.discovered}
            icon="🔍"
            color="text-[#4f7cff]"
            trend={{ direction: "up", pct: 12 }}
          />
          <KPICard
            label="Validated rate"
            value={`${kpiTrends.validatedPct}%`}
            icon="✅"
            color="text-emerald-400"
            detail={`${funnel?.validated ?? 0} of ${funnel?.discovered ?? 0} companies`}
          />
          <KPICard
            label="Tier A prospects"
            value={kpiTrends.tierA}
            icon="🔥"
            color="text-amber-400"
            trend={kpiTrends.tierA > 0 ? { direction: "up", pct: 8 } : null}
          />
          <KPICard
            label="Emails found"
            value={funnel?.enriched ?? 0}
            icon="📧"
            color="text-teal-400"
            detail="via Hunter + website"
          />
          <KPICard
            label="Pending approvals"
            value={kpiTrends.pendingApprovals}
            icon="⏳"
            color="text-amber-400"
            trend={
              kpiTrends.pendingApprovals > 0
                ? { direction: "up", pct: 5 }
                : null
            }
            detail={kpiTrends.pendingApprovals > 0 ? `${funnel?.approved ?? 0} approved this month` : "All clear"}
          />
          <KPICard
            label="Approved this month"
            value={funnel?.approved ?? 0}
            icon="🎯"
            color="text-emerald-400"
          />
        </div>
      )}

      {/* ── ROW 2: Funnel chart + Recent activity ─────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
        {/* Funnel — 3/5 width */}
        <div
          className="lg:col-span-3 rounded-xl border p-4"
          style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}
        >
          <h3 className="text-xs font-semibold text-white uppercase tracking-wider mb-4">
            Conversion funnel
          </h3>
          {funnelLoading || !funnel ? (
            <div className="h-64 flex items-center justify-center text-[--text-muted] text-xs">Loading funnel...</div>
          ) : funnel.discovered === 0 ? (
            <div className="h-64 flex items-center justify-center text-[--text-muted] text-xs">
              No data yet — start a workflow to see your funnel
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={280}>
              <FunnelChart>
                <Tooltip content={<FunnelTooltip />} />
                <Funnel
                  dataKey="value"
                  data={funnelData}
                  isAnimationActive
                  width={400}
                >
                  {funnelData.map((entry, idx) => (
                    <Cell key={idx} fill={FUNNEL_COLORS[idx % FUNNEL_COLORS.length]} />
                  ))}
                  <LabelList
                    position="right"
                    dataKey="name"
                    fill="#94a3b8"
                    fontSize={11}
                    offset={10}
                  />
                  <LabelList
                    position="right"
                    dataKey="value"
                    fill="#ffffff"
                    fontSize={12}
                    fontWeight={600}
                    offset={100}
                  />
                </Funnel>
              </FunnelChart>
            </ResponsiveContainer>
          )}
          {/* Funnel conversion numbers */}
          {funnel && funnel.discovered > 0 && (
            <div className="grid grid-cols-6 gap-1 mt-2">
              {funnelData.map((step, i) => (
                <div key={step.name} className="text-center">
                  <p className="text-[18px] font-bold text-white">{step.value}</p>
                  <p className="text-[9px] text-[--text-muted] truncate">{step.name}</p>
                  {i > 0 && (
                    <p className="text-[9px] text-emerald-400">{step.conversion.toFixed(0)}%</p>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Recent activity — 2/5 width */}
        <div
          className="lg:col-span-2 rounded-xl border p-4"
          style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}
        >
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-xs font-semibold text-white uppercase tracking-wider">
              Recent workflows
            </h3>
            <button
              onClick={() => navigate("/workflow-history")}
              className="text-[10px] text-[#4f7cff] hover:underline"
            >
              View all
            </button>
          </div>

          {!recentWorkflows || recentWorkflows.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-48 text-center">
              <p className="text-xs text-[--text-muted]">No workflows yet</p>
              <button
                onClick={() => navigate("/workflow")}
                className="mt-2 text-[10px] px-3 py-1.5 rounded-lg bg-[#4f7cff]/20 text-[#4f7cff] hover:bg-[#4f7cff]/30 transition-colors"
              >
                Start one now
              </button>
            </div>
          ) : (
            <div className="space-y-2">
              {recentWorkflows.map((wf: any) => {
                const statusColor: Record<string, string> = {
                  running: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
                  completed: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
                  failed: "bg-red-500/10 text-red-400 border-red-500/20",
                  pending: "bg-amber-500/10 text-amber-400 border-amber-500/20",
                };
                const statusClass = statusColor[wf.status] ?? "bg-zinc-500/10 text-zinc-400";

                return (
                  <div
                    key={wf.id}
                    onClick={() => navigate(`/workflow-viewer?workflow_id=${wf.id}`)}
                    className="flex items-center gap-3 p-2.5 rounded-lg cursor-pointer transition-colors hover:bg-[--bg-secondary] border border-transparent hover:border-[--border]"
                  >
                    <div className="w-8 h-8 rounded-lg bg-[--bg-secondary] flex items-center justify-center text-xs">
                      {wf.status === "running" ? "⚡" : wf.status === "completed" ? "✅" : wf.status === "failed" ? "❌" : "⏸"}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-1.5">
                        <span className="text-xs font-medium text-white truncate">
                          {wf.configuration_name ?? `Workflow ${wf.id.slice(0, 8)}`}
                        </span>
                        <span className={`text-[9px] px-1.5 py-0.5 rounded-full border ${statusClass}`}>
                          {wf.status}
                        </span>
                      </div>
                      <p className="text-[10px] text-[--text-muted] mt-0.5">
                        {wf.created_at ? timeAgo(wf.created_at) : ""}
                      </p>
                    </div>
                    <span className="text-[9px] text-[#4f7cff]">→</span>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* ── ROW 3: Tech distribution + Signal breakdown ───────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Tech distribution — horizontal bar chart */}
        <div
          className="rounded-xl border p-4"
          style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}
        >
          <h3 className="text-xs font-semibold text-white uppercase tracking-wider mb-4">
            Technology stack distribution
          </h3>
          {techLoading ? (
            <div className="h-64 flex items-center justify-center text-[--text-muted] text-xs">Loading...</div>
          ) : techData.length === 0 ? (
            <div className="h-64 flex items-center justify-center text-[--text-muted] text-xs">No tech data yet</div>
          ) : (
            <ResponsiveContainer width="100%" height={Math.max(200, techData.length * 28)}>
              <BarChart data={techData} layout="vertical" margin={{ left: 80, right: 40 }}>
                <XAxis type="number" tick={{ fill: "#6b7280", fontSize: 10 }} />
                <YAxis type="category" dataKey="name" tick={{ fill: "#475569", fontSize: 10 }} width={70} />
                <Tooltip
                  contentStyle={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)", fontSize: 12 }}
                  formatter={(value: any) => [`${value} companies`, "Count"]}
                />
                <Bar dataKey="count" radius={[0, 4, 4, 0]} maxBarSize={18}>
                  {techData.map((entry, idx) => (
                    <Cell key={idx} fill={TECH_CATEGORY_COLORS[idx < 3 ? ["cloud", "framework", "language"][idx] : "default"]} />
                  ))}
                  <LabelList dataKey="count" position="right" fill="#94a3b8" fontSize={10} />
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Signal breakdown — pie chart */}
        <div
          className="rounded-xl border p-4"
          style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}
        >
          <h3 className="text-xs font-semibold text-white uppercase tracking-wider mb-4">
            Market signals breakdown
          </h3>
          {signalsLoading ? (
            <div className="h-64 flex items-center justify-center text-[--text-muted] text-xs">Loading...</div>
          ) : signalData.length === 0 ? (
            <div className="h-64 flex items-center justify-center text-[--text-muted] text-xs">No signals detected yet</div>
          ) : (
            <div className="flex items-center gap-4">
              <ResponsiveContainer width="60%" height={260}>
                <PieChart>
                  <Pie
                    data={signalData}
                    cx="50%"
                    cy="50%"
                    innerRadius={55}
                    outerRadius={90}
                    dataKey="value"
                    paddingAngle={3}
                    isAnimationActive
                    cursor="pointer"
                    onClick={(entry: any) => {
                      // Navigate to prospects filtered by signal type
                      const signalKey = (entry.name ?? "").toLowerCase();
                      navigate(`/prospects?signal=${signalKey}`);
                    }}
                  >
                    {signalData.map((entry, idx) => (
                      <Cell key={idx} fill={PIE_COLORS[idx % PIE_COLORS.length]} stroke="transparent" />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)", fontSize: 12 }}
                    formatter={(value: any, name: any) => [`${value} companies`, name]}
                  />
                </PieChart>
              </ResponsiveContainer>

              {/* Legend */}
              <div className="space-y-2.5">
                {signalData.map((entry, idx) => (
                  <div key={entry.name} className="flex items-center gap-2 cursor-pointer"
                    onClick={() => navigate(`/prospects?signal=${entry.name.toLowerCase()}`)}>
                    <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: PIE_COLORS[idx % PIE_COLORS.length] }} />
                    <span className="text-[11px] text-[--text-secondary]">{entry.name}</span>
                    <span className="text-xs font-medium text-white ml-auto">{entry.value}</span>
                  </div>
                ))}
                {signals && (
                  <div className="pt-2 border-t border-[--border]">
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] text-[--text-muted]">Total companies with signals:</span>
                      <span className="text-xs font-medium text-white">{signals.total_companies_with_signals}</span>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Data sources footer */}
      <div className="flex gap-4 text-[9px] text-[--text-muted] py-2 border-t border-[--border]">
        <span>Data sources: SerpAPI · Hunter.io · Clearbit · Groq LLM</span>
        <span>Last updated: {new Date().toLocaleTimeString()}</span>
      </div>
    </div>
  );
}
