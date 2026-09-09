import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { listConfigs } from "@/api/configurations";
import { useWorkflow } from "@/hooks/useWorkflow";
import type { ConfigItem } from "@/types/config";

export default function WorkflowLauncher() {
  const navigate = useNavigate();
  const [selectedConfig, setSelectedConfig] = useState("");
  const [launching, setLaunching] = useState(false);

  const { data: configs = [] } = useQuery({ queryKey: ["configs"], queryFn: listConfigs });
  const { startWorkflow } = useWorkflow();

  const icpConfigs = configs.filter((c: ConfigItem) => c.type === "icp");
  const personaConfigs = configs.filter((c: ConfigItem) => c.type === "persona");
  const scoringConfigs = configs.filter((c: ConfigItem) => c.type === "scoring");

  const handleLaunch = async () => {
    if (!selectedConfig) return;
    setLaunching(true);
    try {
      const wf = await startWorkflow(selectedConfig);
      navigate(`/workflow/${wf.id}`);
    } catch (e) {
      console.error("Failed to start workflow", e);
    } finally {
      setLaunching(false);
    }
  };

  return (
    <div className="space-y-8 max-w-4xl">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-[--text-primary]">Launch Discovery Workflow</h1>
        <p className="text-[--text-secondary] mt-1">Configure your AI agents and start discovering prospects</p>
      </div>

      {/* Config cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* ICP */}
        <div className="rounded-xl p-5 border" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
          <div className="flex items-center gap-2 mb-3">
            <span className="text-lg">🎯</span>
            <h3 className="text-sm font-semibold text-white">ICP Configuration</h3>
          </div>
          <select
            value={selectedConfig}
            onChange={(e) => setSelectedConfig(e.target.value)}
            className="w-full px-3 py-2.5 rounded-lg border text-sm focus:border-[#4f7cff] focus:outline-none"
            style={{ backgroundColor: "var(--bg-secondary)", borderColor: "var(--border)", color: "var(--text-primary)" }}
          >
            <option value="">Select ICP...</option>
            {icpConfigs.map((c: ConfigItem) => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>
        </div>

        {/* Personas */}
        <div className="rounded-xl p-5 border" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
          <div className="flex items-center gap-2 mb-3">
            <span className="text-lg">👥</span>
            <h3 className="text-sm font-semibold text-white">Personas</h3>
          </div>
          <p className="text-xs text-[--text-muted]">{personaConfigs.length} persona(s) configured</p>
          {personaConfigs.slice(0, 2).map((p: ConfigItem) => (
            <div key={p.id} className="mt-2 text-xs px-2 py-1 rounded bg-[--bg-secondary] text-[--text-secondary]">{p.name}</div>
          ))}
        </div>

        {/* Scoring */}
        <div className="rounded-xl p-5 border" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
          <div className="flex items-center gap-2 mb-3">
            <span className="text-lg">📊</span>
            <h3 className="text-sm font-semibold text-white">Scoring Weights</h3>
          </div>
          <p className="text-xs text-[--text-muted]">{scoringConfigs.length} scoring config(s)</p>
        </div>
      </div>

      {/* Agent summary */}
      <div className="rounded-xl p-5 border" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
        <h3 className="text-sm font-semibold text-white mb-3">Agents that will run:</h3>
        <div className="flex flex-wrap gap-2">
          {["🔍 Discovery", "✓ Validation", "👤 Decision Maker", "📧 Enrichment", "📊 Qualification", "💡 Recommendations"].map((agent) => (
            <span key={agent} className="text-xs px-3 py-1.5 rounded-lg bg-[--bg-secondary] text-[--text-secondary] border border-[--border]">
              {agent}
            </span>
          ))}
        </div>
      </div>

      {/* Launch button */}
      <button
        onClick={handleLaunch}
        disabled={!selectedConfig || launching}
        className="w-full py-4 rounded-xl text-base font-semibold bg-[#4f7cff] text-white hover:shadow-[0_0_30px_rgba(79,124,255,0.4)] transition-all disabled:opacity-40 disabled:shadow-none"
      >
        {launching ? (
          <span className="flex items-center justify-center gap-2">
            <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
            Starting...
          </span>
        ) : (
          "🚀 Start Discovery Workflow"
        )}
      </button>
    </div>
  );
}
