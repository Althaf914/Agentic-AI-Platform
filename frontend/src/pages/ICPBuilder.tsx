import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { saveICP, listConfigs, deleteConfig } from "@/api/configurations";
import type { ConfigItem } from "@/types/config";

export default function ICPBuilder() {
  const queryClient = useQueryClient();
  const [name, setName] = useState("");
  const [industries, setIndustries] = useState("");
  const [countries, setCountries] = useState("");
  const [locations, setLocations] = useState("");
  const [minEmp, setMinEmp] = useState(10);
  const [maxEmp, setMaxEmp] = useState(500);
  const [revenueRange, setRevenueRange] = useState("");
  const [fundingStages, setFundingStages] = useState("");
  const [techStack, setTechStack] = useState("");
  const [hiringKeywords, setHiringKeywords] = useState("");
  const [growthIndicators, setGrowthIndicators] = useState("");

  const { data: configs = [] } = useQuery({
    queryKey: ["configs"],
    queryFn: listConfigs,
  });

  const icpConfigs = configs.filter((c: ConfigItem) => c.type === "icp");

  const saveMutation = useMutation({
    mutationFn: saveICP,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["configs"] });
      setName("");
    },
  });

  const handleSave = () => {
    saveMutation.mutate({
      name,
      config_json: {
        industries: industries.split(",").map((s: string) => s.trim()).filter(Boolean),
        countries: countries.split(",").map((s: string) => s.trim()).filter(Boolean),
        locations: locations.split(",").map((s: string) => s.trim()).filter(Boolean),
        min_employees: minEmp,
        max_employees: maxEmp,
        revenue_range: revenueRange,
        funding_stages: fundingStages.split(",").map((s: string) => s.trim()).filter(Boolean),
        tech_stack: techStack.split(",").map((s: string) => s.trim()).filter(Boolean),
        hiring_keywords: hiringKeywords.split(",").map((s: string) => s.trim()).filter(Boolean),
        growth_indicators: growthIndicators.split(",").map((s: string) => s.trim()).filter(Boolean),
      },
    });
  };

  return (
    <div className="space-y-6">
      <div className="rounded-xl p-6 space-y-4 border" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
        <h3 className="font-semibold text-[--text-primary]">New ICP Configuration</h3>

        <div>
          <label className="block text-xs font-medium text-[--text-secondary] mb-1.5">Configuration Name</label>
          <input value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. B2B SaaS - US West Coast"
            className="w-full px-3 py-2.5 rounded-lg border text-sm focus:border-[#4f7cff] focus:outline-none"
            style={{ backgroundColor: "var(--bg-secondary)", borderColor: "var(--border)", color: "var(--text-primary)" }} />
        </div>

        <div>
          <label className="block text-xs font-medium text-[--text-secondary] mb-1.5">Industries</label>
          <input value={industries} onChange={(e) => setIndustries(e.target.value)} placeholder="SaaS, Fintech, HealthTech"
            className="w-full px-3 py-2.5 rounded-lg border text-sm focus:border-[#4f7cff] focus:outline-none"
            style={{ backgroundColor: "var(--bg-secondary)", borderColor: "var(--border)", color: "var(--text-primary)" }} />
        </div>

        <div>
          <label className="block text-xs font-medium text-[--text-secondary] mb-1.5">Countries</label>
          <input value={countries} onChange={(e) => setCountries(e.target.value)} placeholder="US, UK, Canada"
            className="w-full px-3 py-2.5 rounded-lg border text-sm focus:border-[#4f7cff] focus:outline-none"
            style={{ backgroundColor: "var(--bg-secondary)", borderColor: "var(--border)", color: "var(--text-primary)" }} />
        </div>

        <div>
          <label className="block text-xs font-medium text-[--text-secondary] mb-1.5">Target Locations (cities / regions)</label>
          <input value={locations} onChange={(e) => setLocations(e.target.value)} placeholder="e.g. San Francisco, New York, Austin, Bangalore"
            className="w-full px-3 py-2.5 rounded-lg border text-sm focus:border-[#4f7cff] focus:outline-none"
            style={{ backgroundColor: "var(--bg-secondary)", borderColor: "var(--border)", color: "var(--text-primary)" }} />
          <p className="text-[10px] text-[--text-muted] mt-1">Adding locations improves search accuracy significantly</p>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-xs text-[--text-secondary] mb-1.5">Min Employees</label>
            <input type="number" value={minEmp} onChange={(e) => setMinEmp(+e.target.value)}
              className="w-full px-3 py-2.5 rounded-lg border text-sm focus:border-[#4f7cff] focus:outline-none"
              style={{ backgroundColor: "var(--bg-secondary)", borderColor: "var(--border)", color: "var(--text-primary)" }} />
          </div>
          <div>
            <label className="block text-xs text-[--text-secondary] mb-1.5">Max Employees</label>
            <input type="number" value={maxEmp} onChange={(e) => setMaxEmp(+e.target.value)}
              className="w-full px-3 py-2.5 rounded-lg border text-sm focus:border-[#4f7cff] focus:outline-none"
              style={{ backgroundColor: "var(--bg-secondary)", borderColor: "var(--border)", color: "var(--text-primary)" }} />
          </div>
        </div>

        <div>
          <label className="block text-xs font-medium text-[--text-secondary] mb-1.5">Revenue Range</label>
          <input value={revenueRange} onChange={(e) => setRevenueRange(e.target.value)} placeholder="$5M-$50M"
            className="w-full px-3 py-2.5 rounded-lg border text-sm focus:border-[#4f7cff] focus:outline-none"
            style={{ backgroundColor: "var(--bg-secondary)", borderColor: "var(--border)", color: "var(--text-primary)" }} />
        </div>

        <div>
          <label className="block text-xs font-medium text-[--text-secondary] mb-1.5">Funding Stages</label>
          <input value={fundingStages} onChange={(e) => setFundingStages(e.target.value)} placeholder="Seed, Series A, Series B"
            className="w-full px-3 py-2.5 rounded-lg border text-sm focus:border-[#4f7cff] focus:outline-none"
            style={{ backgroundColor: "var(--bg-secondary)", borderColor: "var(--border)", color: "var(--text-primary)" }} />
        </div>

        <div>
          <label className="block text-xs font-medium text-[--text-secondary] mb-1.5">Tech Stack</label>
          <input value={techStack} onChange={(e) => setTechStack(e.target.value)} placeholder="Python, React, AWS, Kubernetes"
            className="w-full px-3 py-2.5 rounded-lg border text-sm focus:border-[#4f7cff] focus:outline-none"
            style={{ backgroundColor: "var(--bg-secondary)", borderColor: "var(--border)", color: "var(--text-primary)" }} />
        </div>

        <div>
          <label className="block text-xs font-medium text-[--text-secondary] mb-1.5">Hiring Keywords</label>
          <input value={hiringKeywords} onChange={(e) => setHiringKeywords(e.target.value)} placeholder="engineer, product manager, growth"
            className="w-full px-3 py-2.5 rounded-lg border text-sm focus:border-[#4f7cff] focus:outline-none"
            style={{ backgroundColor: "var(--bg-secondary)", borderColor: "var(--border)", color: "var(--text-primary)" }} />
        </div>

        <div>
          <label className="block text-xs font-medium text-[--text-secondary] mb-1.5">Growth Indicators</label>
          <input value={growthIndicators} onChange={(e) => setGrowthIndicators(e.target.value)} placeholder="recently funded, hiring surge, new product launch"
            className="w-full px-3 py-2.5 rounded-lg border text-sm focus:border-[#4f7cff] focus:outline-none"
            style={{ backgroundColor: "var(--bg-secondary)", borderColor: "var(--border)", color: "var(--text-primary)" }} />
          <p className="text-[10px] text-[--text-muted] mt-1">Keywords that signal a company is actively growing</p>
        </div>

        <button onClick={handleSave} disabled={!name || saveMutation.isPending}
          className="w-full py-3 rounded-lg bg-[#4f7cff] text-white font-medium hover:shadow-[0_0_20px_rgba(79,124,255,0.4)] transition-all disabled:opacity-40">
          {saveMutation.isPending ? "Saving..." : "Save ICP Configuration"}
        </button>
      </div>

      {/* Saved ICPs */}
      <div className="space-y-2">
        <h3 className="text-sm font-semibold text-[--text-primary]">Saved ICPs ({icpConfigs.length})</h3>
        {icpConfigs.map((c: ConfigItem) => (
          <div key={c.id} className="rounded-lg p-3 border flex justify-between items-center"
            style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
            <span className="text-sm text-white">{c.name}</span>
            <button onClick={() => deleteConfig(c.id).then(() => queryClient.invalidateQueries({ queryKey: ["configs"] }))}
              className="text-xs text-[--accent-red] hover:underline">Delete</button>
          </div>
        ))}
      </div>
    </div>
  );
}
