import { useState } from "react";
import type { ICPConfig } from "@/types/config";
import { INDUSTRIES, COUNTRIES, FUNDING_STAGES } from "@/utils/constants";

interface ICPFormProps {
  defaultValues?: Partial<ICPConfig>;
  onSave: (data: ICPConfig) => void;
}

export default function ICPForm({ defaultValues, onSave }: ICPFormProps) {
  const [industry, setIndustry] = useState<string[]>(defaultValues?.industry || []);
  const [countries, setCountries] = useState<string[]>(defaultValues?.countries || []);
  const [minEmp, setMinEmp] = useState(defaultValues?.min_employees ?? 10);
  const [maxEmp, setMaxEmp] = useState(defaultValues?.max_employees ?? 500);
  const [revenueRange, setRevenueRange] = useState(defaultValues?.revenue_range ?? "");
  const [fundingStages, setFundingStages] = useState<string[]>(defaultValues?.funding_stages || []);
  const [hiringKeywords, setHiringKeywords] = useState(defaultValues?.hiring_keywords?.join(", ") ?? "");
  const [techStack, setTechStack] = useState(defaultValues?.tech_stack?.join(", ") ?? "");

  const toggleItem = (list: string[], setList: (v: string[]) => void, item: string) => {
    setList(list.includes(item) ? list.filter((i) => i !== item) : [...list, item]);
  };

  const handleSave = () => {
    onSave({
      industry,
      countries,
      min_employees: minEmp,
      max_employees: maxEmp,
      revenue_range: revenueRange,
      funding_stages: fundingStages,
      hiring_keywords: hiringKeywords.split(",").map((s) => s.trim()).filter(Boolean),
      tech_stack: techStack.split(",").map((s) => s.trim()).filter(Boolean),
    });
  };

  return (
    <div className="space-y-4">
      {/* Industries */}
      <div>
        <label className="block text-xs font-medium text-foreground mb-1">Industries</label>
        <div className="flex flex-wrap gap-1.5">{INDUSTRIES.map((i) => (<button key={i} onClick={() => toggleItem(industry, setIndustry, i)} className={`text-xs px-2 py-1 rounded-md border ${industry.includes(i) ? "bg-primary text-primary-foreground border-primary" : "border-input text-muted-foreground hover:bg-accent"}`}>{i}</button>))}</div>
      </div>
      {/* Countries */}
      <div>
        <label className="block text-xs font-medium text-foreground mb-1">Countries</label>
        <div className="flex flex-wrap gap-1.5">{COUNTRIES.map((c) => (<button key={c} onClick={() => toggleItem(countries, setCountries, c)} className={`text-xs px-2 py-1 rounded-md border ${countries.includes(c) ? "bg-primary text-primary-foreground border-primary" : "border-input text-muted-foreground hover:bg-accent"}`}>{c}</button>))}</div>
      </div>
      {/* Employees */}
      <div className="grid grid-cols-2 gap-3">
        <div><label className="block text-xs text-muted-foreground mb-1">Min Employees</label><input type="number" value={minEmp} onChange={(e) => setMinEmp(+e.target.value)} className="w-full px-2 py-1.5 text-sm border border-input rounded-md bg-background" /></div>
        <div><label className="block text-xs text-muted-foreground mb-1">Max Employees</label><input type="number" value={maxEmp} onChange={(e) => setMaxEmp(+e.target.value)} className="w-full px-2 py-1.5 text-sm border border-input rounded-md bg-background" /></div>
      </div>
      {/* Revenue */}
      <div><label className="block text-xs font-medium text-foreground mb-1">Revenue Range</label><input value={revenueRange} onChange={(e) => setRevenueRange(e.target.value)} placeholder="$5M-$50M" className="w-full px-3 py-1.5 text-sm border border-input rounded-md bg-background" /></div>
      {/* Funding */}
      <div>
        <label className="block text-xs font-medium text-foreground mb-1">Funding Stages</label>
        <div className="flex flex-wrap gap-1.5">{FUNDING_STAGES.map((f) => (<button key={f} onClick={() => toggleItem(fundingStages, setFundingStages, f)} className={`text-xs px-2 py-1 rounded-md border ${fundingStages.includes(f) ? "bg-primary text-primary-foreground border-primary" : "border-input text-muted-foreground hover:bg-accent"}`}>{f}</button>))}</div>
      </div>
      {/* Keywords */}
      <div><label className="block text-xs font-medium text-foreground mb-1">Hiring Keywords</label><input value={hiringKeywords} onChange={(e) => setHiringKeywords(e.target.value)} placeholder="Comma separated" className="w-full px-3 py-1.5 text-sm border border-input rounded-md bg-background" /></div>
      <div><label className="block text-xs font-medium text-foreground mb-1">Tech Stack</label><input value={techStack} onChange={(e) => setTechStack(e.target.value)} placeholder="Python, React, AWS..." className="w-full px-3 py-1.5 text-sm border border-input rounded-md bg-background" /></div>
      <button onClick={handleSave} className="w-full py-2 bg-primary text-primary-foreground rounded-md text-sm font-medium hover:opacity-90">Save ICP</button>
    </div>
  );
}
