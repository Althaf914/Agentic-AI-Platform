import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { getWorkflowList } from "@/api/workflows";
import type { Workflow } from "@/types/workflow";

const STATUS_BADGE: Record<string, string> = {
  pending: "bg-amber-500/10 text-amber-500 border border-amber-500/20",
  running: "bg-[#00abe4]/10 text-[#00abe4] border border-[#00abe4]/20",
  completed: "bg-emerald-500/10 text-emerald-500 border border-emerald-500/20",
  failed: "bg-red-500/10 text-red-500 border border-red-500/20",
};

export default function WorkflowHistory() {
  const { data: workflows = [], isLoading } = useQuery({
    queryKey: ["workflows"],
    queryFn: getWorkflowList,
  });

  if (isLoading) {
    return (
      <div className="space-y-4 py-12 flex flex-col items-center justify-center">
        <div className="w-8 h-8 border-2 border-[--accent-blue] border-t-transparent rounded-full animate-spin" />
        <p className="text-xs text-[--text-muted]">Loading history...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-[--text-primary]">Workflow History</h1>
        <p className="text-xs text-[--text-muted] mt-0.5">
          Audit trail of all prospect discovery campaigns executed by the AI agents
        </p>
      </div>

      <div className="rounded-xl border overflow-hidden shadow-sm" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="text-left text-[10px] text-[--text-muted] uppercase tracking-wider border-b border-[--border]" style={{ backgroundColor: "var(--bg-secondary)" }}>
                <th className="py-3 px-4 font-semibold">Configuration / Campaign</th>
                <th className="py-3 px-4 font-semibold">Status</th>
                <th className="py-3 px-4 font-semibold">Started</th>
                <th className="py-3 px-4 font-semibold">Completed</th>
                <th className="py-3 px-4 font-semibold text-right">Action</th>
              </tr>
            </thead>
            <tbody>
              {workflows.map((wf: Workflow) => (
                <tr key={wf.id} className="border-b border-[--border] hover:bg-[--bg-secondary] transition-colors last:border-b-0">
                  <td className="py-3.5 px-4">
                    <div className="flex flex-col">
                      <span className="font-semibold text-white text-sm">
                        {wf.configuration_name ?? `Workflow ${wf.id.slice(0, 8)}`}
                      </span>
                      <span className="text-[10px] text-[--text-muted] font-mono mt-0.5">
                        ID: {wf.id}
                      </span>
                    </div>
                  </td>
                  <td className="py-3.5 px-4">
                    <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${STATUS_BADGE[wf.status] || STATUS_BADGE.pending}`}>
                      {wf.status.toUpperCase()}
                    </span>
                  </td>
                  <td className="py-3.5 px-4 text-[--text-secondary] font-medium">
                    {wf.started_at ? new Date(wf.started_at).toLocaleString() : "—"}
                  </td>
                  <td className="py-3.5 px-4 text-[--text-secondary] font-medium">
                    {wf.completed_at ? new Date(wf.completed_at).toLocaleString() : "—"}
                  </td>
                  <td className="py-3.5 px-4 text-right">
                    <Link
                      to={`/workflow/${wf.id}`}
                      className="px-3 py-1.5 rounded-lg border text-xs font-semibold text-[--text-secondary] hover:text-[--accent-blue] hover:border-[--accent-blue]/40 bg-[--bg-card] transition-all inline-block hover:shadow-sm"
                      style={{ borderColor: "var(--border)" }}
                    >
                      View Run Details →
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      
      {workflows.length === 0 && (
        <div className="text-center py-12 border rounded-xl" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
          <p className="text-lg mb-1">🕐</p>
          <p className="text-xs text-[--text-muted]">No workflows have been executed yet</p>
        </div>
      )}
    </div>
  );
}
