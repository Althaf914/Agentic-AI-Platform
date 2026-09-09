import type { AgentLog } from "@/types/workflow";

interface ActivityFeedProps {
  entries: AgentLog[];
}

const STATUS_ICONS: Record<string, string> = {
  idle: "⏸",
  running: "⏳",
  completed: "✅",
  failed: "❌",
};

const AGENT_COLORS: Record<string, string> = {
  company_discovery: "bg-blue-100 text-blue-700",
  validation: "bg-cyan-100 text-cyan-700",
  decision_maker: "bg-indigo-100 text-indigo-700",
  contact_enrichment: "bg-teal-100 text-teal-700",
  qualification: "bg-amber-100 text-amber-700",
  recommendation_memory: "bg-emerald-100 text-emerald-700",
};

export default function ActivityFeed({ entries }: ActivityFeedProps) {
  if (!entries.length) {
    return <p className="text-xs text-muted-foreground text-center py-4">No recent activity</p>;
  }

  return (
    <div className="bg-card border border-border rounded-lg">
      <div className="px-4 py-2 border-b border-border">
        <h4 className="text-sm font-semibold text-foreground">Recent Activity</h4>
      </div>
      <div className="max-h-[320px] overflow-y-auto divide-y divide-border">
        {entries.map((entry) => (
          <div key={entry.id} className="px-4 py-2 flex items-center gap-2">
            <span>{STATUS_ICONS[entry.status] || "•"}</span>
            <span className={`text-[10px] px-1.5 py-0.5 rounded font-medium ${AGENT_COLORS[entry.agent_name] || "bg-gray-100 text-gray-700"}`}>
              {entry.agent_name}
            </span>
            <span className="text-xs text-muted-foreground flex-1 truncate">{entry.status}</span>
            <span className="text-[10px] text-muted-foreground shrink-0">
              {entry.started_at ? new Date(entry.started_at).toLocaleTimeString() : "—"}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
