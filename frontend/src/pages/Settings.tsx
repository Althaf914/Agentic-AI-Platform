import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/api/client";

const STATUS_BADGE: Record<string, { bg: string; text: string; label: string }> = {
  connected: { bg: "bg-[#22d3a5]/10", text: "text-[#22d3a5]", label: "✅ Connected" },
  not_configured: { bg: "bg-[#f59e0b]/10", text: "text-[#f59e0b]", label: "⚠️ Not Configured" },
  error: { bg: "bg-[#ef4444]/10", text: "text-[#ef4444]", label: "❌ Error" },
};

const SUBSYSTEM_META: Record<string, { icon: string; name: string }> = {
  postgresql: { icon: "🐘", name: "PostgreSQL" },
  redis: { icon: "🔴", name: "Redis" },
  chromadb: { icon: "🧠", name: "ChromaDB" },
  groq_llm: { icon: "🤖", name: "Groq LLM" },
  serpapi: { icon: "🔍", name: "SerpAPI" },
  hunter_io: { icon: "📧", name: "Hunter.io" },
};

export default function Settings() {
  const [tab, setTab] = useState<"status" | "keys" | "scoring">("status");

  const { data: health, isLoading } = useQuery({
    queryKey: ["platform-health"],
    queryFn: async () => {
      const { data } = await apiClient.get("/platform/health");
      return data;
    },
  });

  const tabs = [
    { key: "status", label: "Platform Status" },
    { key: "keys", label: "API Keys" },
    { key: "scoring", label: "Scoring Weights" },
  ] as const;

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Tabs */}
      <div className="flex gap-2">
        {tabs.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`px-4 py-2 rounded-lg text-xs font-medium transition-all ${
              tab === t.key
                ? "bg-[#4f7cff]/20 text-[#4f7cff] border border-[#4f7cff]/40"
                : "text-[--text-secondary] border border-[--border] hover:border-[--border-accent]"
            }`}
            style={{ backgroundColor: tab !== t.key ? "var(--bg-card)" : undefined }}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Platform Status Tab */}
      {tab === "status" && (
        <div className="space-y-6">
          <div>
            <h3 className="text-sm font-semibold text-white mb-1">Subsystem Health</h3>
            <p className="text-[10px] text-[--text-muted]">
              Real-time status of all platform dependencies
            </p>
          </div>

          {isLoading ? (
            <p className="text-[--text-muted]">Checking subsystems...</p>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {health?.subsystems &&
                Object.entries(health.subsystems).map(([key, sub]: [string, any]) => {
                  const meta = SUBSYSTEM_META[key] || { icon: "•", name: key };
                  const badge = STATUS_BADGE[sub.status] || STATUS_BADGE.error;

                  return (
                    <div
                      key={key}
                      className="rounded-xl p-4 border"
                      style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <span className="text-lg">{meta.icon}</span>
                          <span className="text-sm font-medium text-white">{meta.name}</span>
                        </div>
                        <span className={`text-[10px] px-2 py-0.5 rounded-full ${badge.bg} ${badge.text}`}>
                          {badge.label}
                        </span>
                      </div>
                      <p className="text-[11px] text-[--text-secondary]">{sub.message}</p>
                      {sub.model && (
                        <p className="text-[9px] text-[--text-muted] mt-1">Model: {sub.model}</p>
                      )}
                    </div>
                  );
                })}
            </div>
          )}

          {health?.use_mock_data && (
            <div className="rounded-lg p-3 border border-[#f59e0b]/30 bg-[#f59e0b]/5">
              <p className="text-xs text-[#f59e0b]">
                ⚠️ USE_MOCK_DATA is enabled — all agents will use mock data regardless of API keys
              </p>
            </div>
          )}
        </div>
      )}

      {/* API Keys Tab */}
      {tab === "keys" && (
        <div className="space-y-4">
          <div>
            <h3 className="text-sm font-semibold text-white mb-1">Configured API Keys</h3>
            <p className="text-[10px] text-[--text-muted]">
              Keys are read from backend/.env — edit that file to update
            </p>
          </div>

          {health?.keys &&
            Object.entries(health.keys).map(([key, value]: [string, any]) => (
              <div
                key={key}
                className="flex items-center justify-between rounded-lg p-3 border"
                style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}
              >
                <span className="text-xs font-mono text-[--text-secondary]">{key}</span>
                <span
                  className={`text-[10px] px-2 py-0.5 rounded-full ${
                    value === "not_configured"
                      ? "bg-[#f59e0b]/10 text-[#f59e0b]"
                      : "bg-[#22d3a5]/10 text-[#22d3a5]"
                  }`}
                >
                  {value === "not_configured" ? "Not configured" : value}
                </span>
              </div>
            ))}

          <div className="rounded-lg p-4 border border-[--border] mt-4" style={{ backgroundColor: "var(--bg-secondary)" }}>
            <p className="text-xs text-[--text-secondary] mb-2">How to add keys:</p>
            <pre className="text-[10px] text-[--text-muted] font-mono">
{`1. Edit: backend/.env
2. Add your keys:
   GROQ_API_KEY=gsk_...      (free at console.groq.com)
   SERPAPI_KEY=...            (free at serpapi.com)
   HUNTER_API_KEY=...         (free at hunter.io)
3. Restart backend server`}
            </pre>
          </div>
        </div>
      )}

      {/* Scoring Weights Tab */}
      {tab === "scoring" && (
        <div className="space-y-4">
          <div>
            <h3 className="text-sm font-semibold text-white mb-1">Qualification Scoring Weights</h3>
            <p className="text-[10px] text-[--text-muted]">
              These weights are applied per-workflow via the scoring configuration
            </p>
          </div>
          <div className="rounded-xl p-5 border space-y-3" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
            {[
              { label: "Funding Stage", default: 20 },
              { label: "Hiring Signals", default: 20 },
              { label: "Revenue", default: 15 },
              { label: "ICP Match", default: 25 },
              { label: "Tech Stack", default: 10 },
              { label: "Growth", default: 10 },
            ].map((w) => (
              <div key={w.label}>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-[--text-secondary]">{w.label}</span>
                  <span className="text-white">{w.default}%</span>
                </div>
                <div className="h-2 bg-[--bg-secondary] rounded-full overflow-hidden">
                  <div className="h-full bg-[#4f7cff] rounded-full" style={{ width: `${w.default}%` }} />
                </div>
              </div>
            ))}
            <p className="text-[9px] text-[--text-muted] pt-2">
              Total: 100% — Edit per-workflow in the ICP configuration scoring section
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
