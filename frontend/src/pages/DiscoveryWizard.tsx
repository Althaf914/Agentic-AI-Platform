import { useState, useRef, useEffect, useCallback, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { useWizardStore, type PrimaryPersona } from "@/store/wizardStore";
import { PRESETS, type PresetName } from "@/data/presets";
import { apiClient } from "@/api/client";

// ═══════════════════════════════════════════════════════════════════════════════
// Types
// ═══════════════════════════════════════════════════════════════════════════════

interface SelectOption {
  label: string;
  value: string;
}

// ═══════════════════════════════════════════════════════════════════════════════
// Constants
// ═══════════════════════════════════════════════════════════════════════════════

const STEPS = [
  { label: "Business", desc: "Domain" },
  { label: "Geography", desc: "Target regions" },
  { label: "Company", desc: "Firmographics" },
  { label: "Technology", desc: "Tech stack" },
  { label: "Committee", desc: "Buying team" },
  { label: "Scoring", desc: "Weights & Launch" },
];

const PRODUCT_CATEGORIES: SelectOption[] = [
  { label: "AI Platform", value: "ai_platform" },
  { label: "HR Software", value: "hr_software" },
  { label: "Security Tool", value: "security_tool" },
  { label: "DevOps Tool", value: "devops_tool" },
  { label: "Sales Intelligence", value: "sales_intelligence" },
  { label: "Marketing Platform", value: "marketing_platform" },
  { label: "Finance Tool", value: "finance_tool" },
  { label: "Other", value: "other" },
];

const DOMAIN_PRESETS: { value: PresetName | ""; label: string; desc: string }[] = [
  { value: "b2b_saas", label: "B2B SaaS", desc: "AI / SaaS / Cloud" },
  { value: "cybersecurity", label: "Cybersecurity", desc: "InfoSec / Compliance" },
  { value: "staffing", label: "Staffing", desc: "HR / Recruiting" },
  { value: "", label: "Custom", desc: "Build from scratch" },
];

const COUNTRIES: SelectOption[] = [
  { label: "United States", value: "US" },
  { label: "United Kingdom", value: "UK" },
  { label: "Canada", value: "Canada" },
  { label: "Australia", value: "Australia" },
  { label: "Germany", value: "Germany" },
  { label: "France", value: "France" },
  { label: "Israel", value: "Israel" },
  { label: "India", value: "India" },
  { label: "Singapore", value: "Singapore" },
  { label: "Netherlands", value: "Netherlands" },
  { label: "Sweden", value: "Sweden" },
  { label: "Brazil", value: "Brazil" },
];

const US_STATES: SelectOption[] = [
  { label: "California", value: "California" },
  { label: "New York", value: "New York" },
  { label: "Texas", value: "Texas" },
  { label: "Illinois", value: "Illinois" },
  { label: "Massachusetts", value: "Massachusetts" },
  { label: "Washington", value: "Washington" },
  { label: "Virginia", value: "Virginia" },
  { label: "Colorado", value: "Colorado" },
  { label: "Florida", value: "Florida" },
  { label: "Georgia", value: "Georgia" },
];

const FUNDING_STAGES: SelectOption[] = [
  { label: "Pre-seed", value: "Pre-seed" },
  { label: "Seed", value: "Seed" },
  { label: "Series A", value: "Series A" },
  { label: "Series B", value: "Series B" },
  { label: "Series C", value: "Series C" },
  { label: "Series D+", value: "Series D+" },
  { label: "Public", value: "Public" },
  { label: "Bootstrapped", value: "Bootstrapped" },
];

const EMPLOYEE_PRESETS = [
  { label: "1-50", min: 1, max: 50 },
  { label: "50-200", min: 50, max: 200 },
  { label: "200-1000", min: 200, max: 1000 },
  { label: "1000+", min: 1000, max: 10000 },
];

const COMMON_TECH = [
  "Python", "React", "AWS", "Azure", "GCP", "Docker", "Kubernetes",
  "OpenAI", "Anthropic", "Salesforce", "HubSpot", "PostgreSQL",
  "MongoDB", "Redis", "GraphQL", "TypeScript", "Go", "Rust", "Kafka",
];

const CLOUD_PROVIDERS = ["AWS", "Azure", "GCP", "Multi-cloud"];

const SENIORITY_OPTIONS: SelectOption[] = [
  { label: "C-Suite", value: "C-Suite" },
  { label: "VP", value: "VP" },
  { label: "Director", value: "Director" },
  { label: "Manager", value: "Manager" },
  { label: "Individual Contributor", value: "Individual Contributor" },
];

const DEPARTMENT_OPTIONS: SelectOption[] = [
  { label: "Engineering", value: "Engineering" },
  { label: "Product", value: "Product" },
  { label: "Sales", value: "Sales" },
  { label: "Marketing", value: "Marketing" },
  { label: "HR", value: "HR" },
  { label: "Finance", value: "Finance" },
  { label: "Security", value: "Security" },
];

const COMMITTEE_SUGGESTIONS: Record<string, { primary: PrimaryPersona; secondary: PrimaryPersona[]; influencers: string[] }> = {
  ai_platform: {
    primary: { title: "CTO", seniority: "C-Suite", department: "Engineering" },
    secondary: [
      { title: "Head of AI", seniority: "VP", department: "Engineering" },
      { title: "VP Engineering", seniority: "VP", department: "Engineering" },
    ],
    influencers: ["Lead Architect", "Engineering Manager", "Data Science Lead"],
  },
  hr_software: {
    primary: { title: "CHRO", seniority: "C-Suite", department: "HR" },
    secondary: [
      { title: "Head of Talent", seniority: "Director", department: "HR" },
      { title: "HR Director", seniority: "Director", department: "HR" },
    ],
    influencers: ["Talent Acquisition Lead", "HR Operations Manager", "People Ops"],
  },
  security_tool: {
    primary: { title: "CISO", seniority: "C-Suite", department: "Security" },
    secondary: [
      { title: "VP Security", seniority: "VP", department: "Security" },
      { title: "Security Architect", seniority: "Director", department: "Security" },
    ],
    influencers: ["IT Director", "Network Engineer", "Compliance Manager"],
  },
  devops_tool: {
    primary: { title: "VP Engineering", seniority: "VP", department: "Engineering" },
    secondary: [
      { title: "DevOps Manager", seniority: "Manager", department: "Engineering" },
      { title: "CTO", seniority: "C-Suite", department: "Engineering" },
    ],
    influencers: ["Senior DevOps Engineer", "Platform Engineer", "Infrastructure Lead"],
  },
  sales_intelligence: {
    primary: { title: "VP Sales", seniority: "VP", department: "Sales" },
    secondary: [
      { title: "Head of Revenue Operations", seniority: "Director", department: "Sales" },
      { title: "CRO", seniority: "C-Suite", department: "Sales" },
    ],
    influencers: ["Sales Director", "Revenue Operations Manager", "SDR Team Lead"],
  },
  marketing_platform: {
    primary: { title: "CMO", seniority: "C-Suite", department: "Marketing" },
    secondary: [
      { title: "VP Marketing", seniority: "VP", department: "Marketing" },
      { title: "Head of Demand Gen", seniority: "Director", department: "Marketing" },
    ],
    influencers: ["Marketing Director", "Growth Lead", "Marketing Ops Manager"],
  },
  finance_tool: {
    primary: { title: "CFO", seniority: "C-Suite", department: "Finance" },
    secondary: [
      { title: "VP Finance", seniority: "VP", department: "Finance" },
      { title: "Finance Director", seniority: "Director", department: "Finance" },
    ],
    influencers: ["Controller", "FP&A Manager", "Treasury Lead"],
  },
  other: {
    primary: { title: "CEO", seniority: "C-Suite", department: "Executive" },
    secondary: [],
    influencers: [],
  },
};

const REVENUE_SUFFIXES = ["K", "M", "B"];

// ═══════════════════════════════════════════════════════════════════════════════
// Utility sub-components
// ═══════════════════════════════════════════════════════════════════════════════

function cn(...classes: (string | boolean | undefined | null)[]) {
  return classes.filter(Boolean).join(" ");
}

function TagInput({
  tags,
  onChange,
  suggestions,
  placeholder,
}: {
  tags: string[];
  onChange: (t: string[]) => void;
  suggestions?: string[];
  placeholder?: string;
}) {
  const [input, setInput] = useState("");
  const [showDropdown, setShowDropdown] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const filtered = useMemo(() => {
    if (!suggestions || !input.trim()) return [];
    const lower = input.toLowerCase();
    return suggestions.filter(
      (s) => s.toLowerCase().includes(lower) && !tags.includes(s)
    );
  }, [suggestions, input, tags]);

  const addTag = useCallback(
    (tag: string) => {
      const trimmed = tag.trim();
      if (trimmed && !tags.includes(trimmed)) {
        onChange([...tags, trimmed]);
      }
      setInput("");
      setShowDropdown(false);
      inputRef.current?.focus();
    },
    [tags, onChange]
  );

  const removeTag = useCallback(
    (tag: string) => {
      onChange(tags.filter((t) => t !== tag));
    },
    [tags, onChange]
  );

  return (
    <div className="relative">
      <div
        className="flex flex-wrap gap-1.5 p-2 rounded-lg border min-h-[42px] cursor-text"
        style={{ backgroundColor: "var(--bg-secondary)", borderColor: "var(--border)" }}
        onClick={() => inputRef.current?.focus()}
      >
        {tags.map((tag) => (
          <span
            key={tag}
            className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium"
            style={{ backgroundColor: "rgba(79,124,255,0.15)", color: "#4f7cff" }}
          >
            {tag}
            <button
              type="button"
              onClick={(e) => { e.stopPropagation(); removeTag(tag); }}
              className="hover:opacity-70"
            >
              ✕
            </button>
          </span>
        ))}
        <input
          ref={inputRef}
          value={input}
          onChange={(e) => { setInput(e.target.value); setShowDropdown(true); }}
          onKeyDown={(e) => {
            if (e.key === "Enter") { e.preventDefault(); addTag(input); }
            if (e.key === "Backspace" && !input && tags.length) removeTag(tags[tags.length - 1]);
            if (e.key === "Escape") setShowDropdown(false);
          }}
          onBlur={() => setTimeout(() => setShowDropdown(false), 200)}
          placeholder={tags.length ? "" : placeholder || "Type and press Enter..."}
          className="flex-1 min-w-[120px] bg-transparent text-sm outline-none placeholder-gray-500"
        />
      </div>
      {showDropdown && filtered.length > 0 && (
        <div
          className="absolute z-20 mt-1 w-full rounded-lg border shadow-lg max-h-48 overflow-y-auto"
          style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}
        >
          {filtered.map((s) => (
            <button
              key={s}
              type="button"
              onMouseDown={(e) => e.preventDefault()}
              onClick={() => addTag(s)}
              className="w-full text-left px-3 py-2 text-sm hover:opacity-80 transition-colors"
              style={{ color: "var(--text-primary)" }}
            >
              {s}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

function MultiSelect({
  options,
  selected,
  onChange,
  placeholder,
}: {
  options: SelectOption[];
  selected: string[];
  onChange: (v: string[]) => void;
  placeholder?: string;
}) {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const filtered = options.filter((o) =>
    o.label.toLowerCase().includes(search.toLowerCase())
  );

  const toggle = (value: string) => {
    if (selected.includes(value)) {
      onChange(selected.filter((v) => v !== value));
    } else {
      onChange([...selected, value]);
    }
  };

  return (
    <div className="relative" ref={ref}>
      <div
        className="flex items-center flex-wrap gap-1 p-2 rounded-lg border min-h-[42px] cursor-pointer"
        style={{ backgroundColor: "var(--bg-secondary)", borderColor: "var(--border)" }}
        onClick={() => setOpen(!open)}
      >
        {selected.length === 0 && (
          <span className="text-sm text-gray-500">{placeholder || "Select..."}</span>
        )}
        {selected.map((v) => {
          const opt = options.find((o) => o.value === v);
          return (
            <span
              key={v}
              className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium"
              style={{ backgroundColor: "rgba(79,124,255,0.15)", color: "#4f7cff" }}
            >
              {opt?.label || v}
              <button
                type="button"
                onClick={(e) => { e.stopPropagation(); toggle(v); }}
                className="hover:opacity-70"
              >
                ✕
              </button>
            </span>
          );
        })}
      </div>
      {open && (
        <div
          className="absolute z-20 mt-1 w-full rounded-lg border shadow-lg"
          style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}
        >
          <div className="p-2 border-b" style={{ borderColor: "var(--border)" }}>
            <input
              autoFocus
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search..."
              className="w-full px-3 py-1.5 rounded-md text-sm outline-none"
              style={{ backgroundColor: "var(--bg-secondary)", color: "var(--text-primary)" }}
            />
          </div>
          <div className="max-h-48 overflow-y-auto p-1">
            {filtered.map((o) => (
              <label
                key={o.value}
                className="flex items-center gap-2 px-3 py-2 rounded-md text-sm cursor-pointer hover:opacity-80"
                style={{ color: "var(--text-primary)" }}
              >
                <input
                  type="checkbox"
                  checked={selected.includes(o.value)}
                  onChange={() => toggle(o.value)}
                  className="rounded"
                />
                {o.label}
              </label>
            ))}
            {filtered.length === 0 && (
              <p className="text-sm text-gray-500 text-center py-3">No options found</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function StepIndicator({ current }: { current: number }) {
  return (
    <div className="flex items-center justify-center gap-0 mb-8">
      {STEPS.map((step, i) => {
        const isComplete = i < current;
        const isCurrent = i === current;
        return (
          <div key={i} className="flex items-center">
            <div className="flex flex-col items-center">
              <div
                className={cn(
                  "w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold transition-all duration-300 border-2",
                  isComplete && "border-green-500 bg-green-500/20 text-green-400",
                  isCurrent && "border-[#4f7cff] bg-[#4f7cff]/20 text-[#4f7cff] shadow-[0_0_12px_rgba(79,124,255,0.3)]",
                  !isComplete && !isCurrent && "border-gray-600 text-gray-500"
                )}
              >
                {isComplete ? "✓" : i + 1}
              </div>
              <span
                className={cn(
                  "text-[10px] mt-1.5 font-medium transition-colors",
                  isCurrent ? "text-[#4f7cff]" : "text-gray-500"
                )}
              >
                {step.label}
              </span>
            </div>
            {i < STEPS.length - 1 && (
              <div
                className={cn(
                  "w-12 md:w-20 h-0.5 mx-2 mt-[-18px] transition-colors",
                  i < current ? "bg-green-500" : "bg-gray-700"
                )}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}

function SliderField({
  label,
  value,
  onChange,
  min = 0,
  max = 100,
}: {
  label: string;
  value: number;
  onChange: (v: number) => void;
  min?: number;
  max?: number;
}) {
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-sm">
        <span style={{ color: "var(--text-secondary)" }}>{label}</span>
        <span className="font-mono font-medium text-white">{value}</span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full h-2 rounded-lg appearance-none cursor-pointer accent-[#4f7cff]"
        style={{
          background: `linear-gradient(to right, #4f7cff ${value}%, #2a2a3a ${value}%)`,
        }}
      />
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// Steps
// ═══════════════════════════════════════════════════════════════════════════════

function Step1Business() {
  const { stepData, setStepData, applyPreset, setCampaignName, campaignName } = useWizardStore();
  const data = stepData.step1_business;

  const handlePreset = (presetName: string) => {
    setStepData("step1_business", { domain_preset: presetName });
    if (presetName && presetName !== "" && presetName in PRESETS) {
      const preset = PRESETS[presetName as PresetName];
      setCampaignName(preset.label);
      applyPreset({
        step2_geography: {
          countries: preset.config.geography.countries,
          states: preset.config.geography.states,
          cities: preset.config.geography.cities,
          remote_ok: false,
        },
        step3_company_filters: {
          industries: preset.config.company_filters.industries,
          min_employees: preset.config.company_filters.min_employees,
          max_employees: preset.config.company_filters.max_employees,
          funding_stages: preset.config.company_filters.funding_stages,
          min_revenue: preset.config.company_filters.min_revenue,
          max_revenue: preset.config.company_filters.max_revenue,
          company_age_year: preset.config.company_filters.company_age_min_years,
          exclude_keywords: preset.config.company_filters.exclude_keywords,
        },
        step4_technology: {
          required_tech: preset.config.technology_filters.required_tech,
          nice_to_have_tech: preset.config.technology_filters.nice_to_have_tech,
          exclude_tech: preset.config.technology_filters.exclude_tech,
          cloud_providers: preset.config.technology_filters.cloud_providers,
        },
        step5_committee: {
          primary_persona: preset.config.buying_committee.primary_persona,
          secondary_personas: preset.config.buying_committee.secondary_personas,
          influencers: preset.config.buying_committee.influencers,
        },
        step6_scoring: { ...preset.config.scoring_weights },
      });
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-white mb-1">Campaign Name</h2>
        <p className="text-xs mb-3" style={{ color: "var(--text-secondary)" }}>
          Give your campaign a memorable name
        </p>
        <input
          value={campaignName}
          onChange={(e) => setCampaignName(e.target.value)}
          placeholder="e.g. Q3 SaaS Prospecting"
          className="w-full px-4 py-2.5 rounded-lg border text-sm focus:border-[#4f7cff] focus:outline-none"
          style={{ backgroundColor: "var(--bg-secondary)", borderColor: "var(--border)", color: "var(--text-primary)" }}
        />
      </div>

      {/* Domain Preset */}
      <div>
        <h2 className="text-lg font-semibold text-white mb-1">Domain Preset</h2>
        <p className="text-xs mb-3" style={{ color: "var(--text-secondary)" }}>
          Select a preset to auto-fill the wizard, or choose Custom to build from scratch
        </p>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {DOMAIN_PRESETS.map((preset) => (
            <button
              key={preset.label}
              type="button"
              onClick={() => handlePreset(preset.value)}
              className={cn(
                "p-4 rounded-xl border-2 text-left transition-all",
                data.domain_preset === preset.value
                  ? "border-[#4f7cff] shadow-[0_0_12px_rgba(79,124,255,0.2)]"
                  : "border-transparent hover:border-gray-600"
              )}
              style={{ backgroundColor: "var(--bg-card)" }}
            >
              <div className="font-medium text-sm text-white">{preset.label}</div>
              <div className="text-xs mt-1" style={{ color: "var(--text-secondary)" }}>{preset.desc}</div>
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        <div>
          <label className="block text-sm font-medium mb-1.5 text-white">Product Category</label>
          <select
            value={data.product_category}
            onChange={(e) => setStepData("step1_business", { product_category: e.target.value })}
            className="w-full px-4 py-2.5 rounded-lg border text-sm focus:border-[#4f7cff] focus:outline-none"
            style={{ backgroundColor: "var(--bg-secondary)", borderColor: "var(--border)", color: "var(--text-primary)" }}
          >
            <option value="">Select a category...</option>
            {PRODUCT_CATEGORIES.map((c) => (
              <option key={c.value} value={c.value}>{c.label}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium mb-1.5 text-white">Value Proposition</label>
          <input
            value={data.value_proposition}
            onChange={(e) => setStepData("step1_business", { value_proposition: e.target.value })}
            placeholder="e.g. Reduce prospecting time by 80%"
            className="w-full px-4 py-2.5 rounded-lg border text-sm focus:border-[#4f7cff] focus:outline-none"
            style={{ backgroundColor: "var(--bg-secondary)", borderColor: "var(--border)", color: "var(--text-primary)" }}
          />
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium mb-1.5 text-white">What does your product do?</label>
        <textarea
          value={data.description}
          onChange={(e) => setStepData("step1_business", { description: e.target.value })}
          rows={2}
          placeholder="Describe your product and the problem it solves..."
          className="w-full px-4 py-2.5 rounded-lg border text-sm focus:border-[#4f7cff] focus:outline-none resize-none"
          style={{ backgroundColor: "var(--bg-secondary)", borderColor: "var(--border)", color: "var(--text-primary)" }}
        />
      </div>
    </div>
  );
}

function Step2Geography() {
  const { stepData, setStepData } = useWizardStore();
  const data = stepData.step2_geography;
  const hasUS = data.countries.includes("US");

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-white mb-1">Target Geography</h2>
        <p className="text-xs mb-3" style={{ color: "var(--text-secondary)" }}>
          Where are your ideal prospects located?
        </p>
      </div>

      <div>
        <label className="block text-sm font-medium mb-1.5 text-white">Countries</label>
        <MultiSelect
          options={COUNTRIES}
          selected={data.countries}
          onChange={(v) => setStepData("step2_geography", { countries: v })}
          placeholder="Search and select countries..."
        />
      </div>

      {hasUS && (
        <div>
          <label className="block text-sm font-medium mb-1.5 text-white">US States</label>
          <MultiSelect
            options={US_STATES}
            selected={data.states}
            onChange={(v) => setStepData("step2_geography", { states: v })}
            placeholder="Select US states..."
          />
        </div>
      )}

      <div>
        <label className="block text-sm font-medium mb-1.5 text-white">Cities</label>
        <TagInput
          tags={data.cities}
          onChange={(v) => setStepData("step2_geography", { cities: v })}
          placeholder="Type city name and press Enter..."
          suggestions={["San Francisco", "New York", "Austin", "Chicago", "London", "Berlin", "Tel Aviv", "Sydney", "Toronto", "Bangalore"]}
        />
      </div>

      <label className="flex items-center gap-3 cursor-pointer">
        <input
          type="checkbox"
          checked={data.remote_ok}
          onChange={(e) => setStepData("step2_geography", { remote_ok: e.target.checked })}
          className="w-5 h-5 rounded accent-[#4f7cff]"
        />
        <span className="text-sm text-white">Remote-first companies OK</span>
      </label>
    </div>
  );
}

function Step3CompanyFilters() {
  const { stepData, setStepData } = useWizardStore();
  const data = stepData.step3_company_filters;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-white mb-1">Company Filters</h2>
        <p className="text-xs mb-3" style={{ color: "var(--text-secondary)" }}>
          Define the firmographic profile of your target companies
        </p>
      </div>

      <div>
        <label className="block text-sm font-medium mb-1.5 text-white">Industries</label>
        <TagInput
          tags={data.industries}
          onChange={(v) => setStepData("step3_company_filters", { industries: v })}
          suggestions={["SaaS", "Cloud", "AI", "Fintech", "Healthtech", "Cybersecurity", "HR", "Staffing", "Enterprise Software", "Developer Tools", "Compliance", "Defense"]}
          placeholder="Search or type industry..."
        />
      </div>

      {/* Employee Range */}
      <div>
        <div className="flex justify-between items-center mb-2">
          <label className="text-sm font-medium text-white">Employee Range</label>
          <span className="text-xs text-white font-mono">{data.min_employees} – {data.max_employees}</span>
        </div>
        <div className="flex gap-2 mb-3 flex-wrap">
          {EMPLOYEE_PRESETS.map((p) => (
            <button
              key={p.label}
              type="button"
              onClick={() => setStepData("step3_company_filters", { min_employees: p.min, max_employees: p.max })}
              className={cn(
                "px-3 py-1 rounded-lg text-xs font-medium border transition-colors",
                data.min_employees === p.min && data.max_employees === p.max
                  ? "border-[#4f7cff] text-[#4f7cff]"
                  : "border-gray-600 text-gray-400 hover:border-gray-500"
              )}
              style={{ backgroundColor: "var(--bg-secondary)" }}
            >
              {p.label}
            </button>
          ))}
        </div>
        <div className="space-y-2">
          <div>
            <span className="text-[10px]" style={{ color: "var(--text-secondary)" }}>Min</span>
            <input
              type="range"
              min={1}
              max={10000}
              value={data.min_employees}
              onChange={(e) => {
                const v = Number(e.target.value);
                setStepData("step3_company_filters", {
                  min_employees: Math.min(v, data.max_employees),
                });
              }}
              className="w-full h-2 rounded-lg appearance-none cursor-pointer accent-[#4f7cff]"
              style={{
                background: `linear-gradient(to right, #4f7cff ${(data.min_employees / 10000) * 100}%, #2a2a3a ${(data.min_employees / 10000) * 100}%)`,
              }}
            />
          </div>
          <div>
            <span className="text-[10px]" style={{ color: "var(--text-secondary)" }}>Max</span>
            <input
              type="range"
              min={1}
              max={10000}
              value={data.max_employees}
              onChange={(e) => {
                const v = Number(e.target.value);
                setStepData("step3_company_filters", {
                  max_employees: Math.max(v, data.min_employees),
                });
              }}
              className="w-full h-2 rounded-lg appearance-none cursor-pointer accent-[#4f7cff]"
              style={{
                background: `linear-gradient(to right, #4f7cff ${(data.max_employees / 10000) * 100}%, #2a2a3a ${(data.max_employees / 10000) * 100}%)`,
              }}
            />
          </div>
        </div>
      </div>

      {/* Funding Stages */}
      <div>
        <label className="block text-sm font-medium mb-1.5 text-white">Funding Stage</label>
        <div className="flex flex-wrap gap-2">
          {FUNDING_STAGES.map((stage) => (
            <button
              key={stage.value}
              type="button"
              onClick={() => {
                const next = data.funding_stages.includes(stage.value)
                  ? data.funding_stages.filter((s) => s !== stage.value)
                  : [...data.funding_stages, stage.value];
                setStepData("step3_company_filters", { funding_stages: next });
              }}
              className={cn(
                "px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors",
                data.funding_stages.includes(stage.value)
                  ? "border-[#4f7cff] text-[#4f7cff] bg-[#4f7cff]/10"
                  : "border-gray-600 text-gray-400 hover:border-gray-500"
              )}
            >
              {stage.label}
            </button>
          ))}
        </div>
      </div>

      {/* Revenue Range */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium mb-1.5 text-white">Min Revenue</label>
          <input
            value={data.min_revenue}
            onChange={(e) => setStepData("step3_company_filters", { min_revenue: e.target.value })}
            placeholder="$0"
            className="w-full px-4 py-2.5 rounded-lg border text-sm focus:border-[#4f7cff] focus:outline-none"
            style={{ backgroundColor: "var(--bg-secondary)", borderColor: "var(--border)", color: "var(--text-primary)" }}
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1.5 text-white">Max Revenue</label>
          <input
            value={data.max_revenue}
            onChange={(e) => setStepData("step3_company_filters", { max_revenue: e.target.value })}
            placeholder="$500M+"
            className="w-full px-4 py-2.5 rounded-lg border text-sm focus:border-[#4f7cff] focus:outline-none"
            style={{ backgroundColor: "var(--bg-secondary)", borderColor: "var(--border)", color: "var(--text-primary)" }}
          />
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium mb-1.5 text-white">Company Age — Founded After Year</label>
        <input
          type="number"
          value={data.company_age_year || ""}
          onChange={(e) => setStepData("step3_company_filters", { company_age_year: Number(e.target.value) })}
          placeholder="e.g. 2015"
          className="w-full max-w-[200px] px-4 py-2.5 rounded-lg border text-sm focus:border-[#4f7cff] focus:outline-none"
          style={{ backgroundColor: "var(--bg-secondary)", borderColor: "var(--border)", color: "var(--text-primary)" }}
        />
      </div>

      <div>
        <label className="block text-sm font-medium mb-1.5 text-white">Exclude Keywords</label>
        <TagInput
          tags={data.exclude_keywords}
          onChange={(v) => setStepData("step3_company_filters", { exclude_keywords: v })}
          placeholder='e.g. "consulting", "agency", "staffing"'
          suggestions={["consulting", "agency", "staffing", "outsourcing", "temp agency", "MSSP"]}
        />
      </div>
    </div>
  );
}

function Step4Technology() {
  const { stepData, setStepData } = useWizardStore();
  const data = stepData.step4_technology;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-white mb-1">Technology Filters</h2>
        <p className="text-xs mb-3" style={{ color: "var(--text-secondary)" }}>
          What technologies should (or shouldn't) your target companies use?
        </p>
      </div>

      <div>
        <label className="block text-sm font-medium mb-1.5 text-white">Required Technologies</label>
        <TagInput
          tags={data.required_tech}
          onChange={(v) => setStepData("step4_technology", { required_tech: v })}
          suggestions={COMMON_TECH}
          placeholder="Search or type tech..."
        />
      </div>

      <div>
        <label className="block text-sm font-medium mb-1.5 text-white">Nice-to-Have Technologies</label>
        <TagInput
          tags={data.nice_to_have_tech}
          onChange={(v) => setStepData("step4_technology", { nice_to_have_tech: v })}
          suggestions={COMMON_TECH}
          placeholder="Search or type tech..."
        />
      </div>

      <div>
        <label className="block text-sm font-medium mb-1.5 text-white">Exclude Technologies</label>
        <TagInput
          tags={data.exclude_tech}
          onChange={(v) => setStepData("step4_technology", { exclude_tech: v })}
          placeholder='e.g. "COBOL", "mainframe"'
          suggestions={["COBOL", "mainframe", "Legacy PeopleSoft", "ColdFusion", "PHP", "ASP.NET WebForms"]}
        />
      </div>

      <div>
        <label className="block text-sm font-medium mb-1.5 text-white">Cloud Providers</label>
        <div className="flex flex-wrap gap-2">
          {CLOUD_PROVIDERS.map((provider) => (
            <button
              key={provider}
              type="button"
              onClick={() => {
                const next = data.cloud_providers.includes(provider)
                  ? data.cloud_providers.filter((p) => p !== provider)
                  : [...data.cloud_providers, provider];
                setStepData("step4_technology", { cloud_providers: next });
              }}
              className={cn(
                "px-4 py-2 rounded-lg text-sm font-medium border transition-colors",
                data.cloud_providers.includes(provider)
                  ? "border-[#4f7cff] text-[#4f7cff] bg-[#4f7cff]/10"
                  : "border-gray-600 text-gray-400 hover:border-gray-500"
              )}
            >
              {provider}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

function Step5Committee() {
  const { stepData, setStepData } = useWizardStore();
  const data = stepData.step5_committee;
  const productCategory = useWizardStore((s) => s.stepData.step1_business.product_category);

  const applySuggestion = () => {
    const suggestion = COMMITTEE_SUGGESTIONS[productCategory];
    if (!suggestion) return;
    setStepData("step5_committee", {
      primary_persona: suggestion.primary,
      secondary_personas: suggestion.secondary,
      influencers: suggestion.influencers,
    });
  };

  const updatePrimary = (field: keyof PrimaryPersona, value: string) => {
    setStepData("step5_committee", {
      primary_persona: { ...data.primary_persona, [field]: value },
    });
  };

  const updateSecondary = (index: number, field: keyof PrimaryPersona, value: string) => {
    const updated = [...data.secondary_personas];
    updated[index] = { ...updated[index], [field]: value };
    setStepData("step5_committee", { secondary_personas: updated });
  };

  const addSecondary = () => {
    if (data.secondary_personas.length < 3) {
      setStepData("step5_committee", {
        secondary_personas: [
          ...data.secondary_personas,
          { title: "", seniority: "", department: "" },
        ],
      });
    }
  };

  const removeSecondary = (index: number) => {
    setStepData("step5_committee", {
      secondary_personas: data.secondary_personas.filter((_, i) => i !== index),
    });
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-white mb-1">Buying Committee</h2>
          <p className="text-xs" style={{ color: "var(--text-secondary)" }}>
            Who are the decision-makers you need to reach?
          </p>
        </div>
        {productCategory && productCategory in COMMITTEE_SUGGESTIONS && (
          <button
            type="button"
            onClick={applySuggestion}
            className="px-3 py-1.5 rounded-lg text-xs font-medium border border-[#4f7cff] text-[#4f7cff] hover:bg-[#4f7cff]/10 transition-colors"
          >
            ✨ Auto-suggest
          </button>
        )}
      </div>

      {/* Primary Persona */}
      <div
        className="rounded-xl p-5 border"
        style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}
      >
        <h3 className="text-sm font-semibold text-white mb-4">⭐ Primary Persona</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-xs font-medium mb-1.5" style={{ color: "var(--text-secondary)" }}>Title</label>
            <input
              value={data.primary_persona.title}
              onChange={(e) => updatePrimary("title", e.target.value)}
              placeholder="e.g. CTO"
              className="w-full px-3 py-2 rounded-lg border text-sm focus:border-[#4f7cff] focus:outline-none"
              style={{ backgroundColor: "var(--bg-secondary)", borderColor: "var(--border)", color: "var(--text-primary)" }}
            />
          </div>
          <div>
            <label className="block text-xs font-medium mb-1.5" style={{ color: "var(--text-secondary)" }}>Seniority</label>
            <select
              value={data.primary_persona.seniority}
              onChange={(e) => updatePrimary("seniority", e.target.value)}
              className="w-full px-3 py-2 rounded-lg border text-sm focus:border-[#4f7cff] focus:outline-none"
              style={{ backgroundColor: "var(--bg-secondary)", borderColor: "var(--border)", color: "var(--text-primary)" }}
            >
              <option value="">Select...</option>
              {SENIORITY_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium mb-1.5" style={{ color: "var(--text-secondary)" }}>Department</label>
            <select
              value={data.primary_persona.department}
              onChange={(e) => updatePrimary("department", e.target.value)}
              className="w-full px-3 py-2 rounded-lg border text-sm focus:border-[#4f7cff] focus:outline-none"
              style={{ backgroundColor: "var(--bg-secondary)", borderColor: "var(--border)", color: "var(--text-primary)" }}
            >
              <option value="">Select...</option>
              {DEPARTMENT_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Secondary Personas */}
      {data.secondary_personas.map((persona, i) => (
        <div
          key={i}
          className="rounded-xl p-5 border relative"
          style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}
        >
          <button
            type="button"
            onClick={() => removeSecondary(i)}
            className="absolute top-3 right-3 text-gray-500 hover:text-red-400 text-xs"
          >
            ✕ Remove
          </button>
          <h3 className="text-sm font-semibold text-white mb-4">Secondary Persona #{i + 1}</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-medium mb-1.5" style={{ color: "var(--text-secondary)" }}>Title</label>
              <input
                value={persona.title}
                onChange={(e) => updateSecondary(i, "title", e.target.value)}
                placeholder="e.g. VP Engineering"
                className="w-full px-3 py-2 rounded-lg border text-sm focus:border-[#4f7cff] focus:outline-none"
                style={{ backgroundColor: "var(--bg-secondary)", borderColor: "var(--border)", color: "var(--text-primary)" }}
              />
            </div>
            <div>
              <label className="block text-xs font-medium mb-1.5" style={{ color: "var(--text-secondary)" }}>Seniority</label>
              <select
                value={persona.seniority}
                onChange={(e) => updateSecondary(i, "seniority", e.target.value)}
                className="w-full px-3 py-2 rounded-lg border text-sm focus:border-[#4f7cff] focus:outline-none"
                style={{ backgroundColor: "var(--bg-secondary)", borderColor: "var(--border)", color: "var(--text-primary)" }}
              >
                <option value="">Select...</option>
                {SENIORITY_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium mb-1.5" style={{ color: "var(--text-secondary)" }}>Department</label>
              <select
                value={persona.department}
                onChange={(e) => updateSecondary(i, "department", e.target.value)}
                className="w-full px-3 py-2 rounded-lg border text-sm focus:border-[#4f7cff] focus:outline-none"
                style={{ backgroundColor: "var(--bg-secondary)", borderColor: "var(--border)", color: "var(--text-primary)" }}
              >
                <option value="">Select...</option>
                {DEPARTMENT_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </div>
          </div>
        </div>
      ))}

      {data.secondary_personas.length < 3 && (
        <button
          type="button"
          onClick={addSecondary}
          className="w-full py-3 rounded-xl border-2 border-dashed text-sm font-medium transition-colors"
          style={{ borderColor: "var(--border)", color: "var(--text-secondary)" }}
        >
          + Add Secondary Persona
        </button>
      )}

      {/* Influencers */}
      <div>
        <label className="block text-sm font-medium mb-1.5 text-white">Influencers</label>
        <TagInput
          tags={data.influencers}
          onChange={(v) => setStepData("step5_committee", { influencers: v })}
          placeholder="e.g. Engineering Manager"
          suggestions={["Engineering Manager", "Senior Developer", "Lead Architect", "Product Manager", "Data Science Lead", "IT Director", "Compliance Manager"]}
        />
      </div>
    </div>
  );
}

function Step6Scoring() {
  const { stepData, setStepData, campaignName } = useWizardStore();
  const data = stepData.step6_scoring;
  const [launching, setLaunching] = useState(false);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const total = data.industry_match + data.location_match + data.hiring_signals +
    data.tech_stack_match + data.funding_stage + data.revenue_tier +
    data.employee_range + data.decision_makers_found;

  const isComplete = total === 100 && campaignName.trim().length > 0;

  const updateWeight = (key: keyof typeof data, value: number) => {
    setStepData("step6_scoring", { [key]: Math.max(0, Math.min(100, value)) });
  };

  const handleLaunch = async () => {
    if (!isComplete) return;
    setLaunching(true);
    setError("");

    try {
      const payload = {
        name: campaignName,
        status: "active",
        domain: stepData.step1_business.domain_preset || "custom",
        wizard_step_completed: 6,
        config_json: {
          business: {
            description: stepData.step1_business.description,
            product_category: stepData.step1_business.product_category,
            value_proposition: stepData.step1_business.value_proposition,
          },
          geography: {
            countries: stepData.step2_geography.countries,
            states: stepData.step2_geography.states,
            cities: stepData.step2_geography.cities,
          },
          company_filters: {
            industries: stepData.step3_company_filters.industries,
            min_employees: stepData.step3_company_filters.min_employees,
            max_employees: stepData.step3_company_filters.max_employees,
            funding_stages: stepData.step3_company_filters.funding_stages,
            min_revenue: stepData.step3_company_filters.min_revenue,
            max_revenue: stepData.step3_company_filters.max_revenue,
            company_age_min_years: stepData.step3_company_filters.company_age_year,
            exclude_keywords: stepData.step3_company_filters.exclude_keywords,
          },
          technology_filters: {
            required_tech: stepData.step4_technology.required_tech,
            nice_to_have_tech: stepData.step4_technology.nice_to_have_tech,
            exclude_tech: stepData.step4_technology.exclude_tech,
            cloud_providers: stepData.step4_technology.cloud_providers,
          },
          hiring_signals: {
            keywords: [],
            job_titles: [],
            departments: [],
          },
          buying_committee: {
            primary_persona: stepData.step5_committee.primary_persona,
            secondary_personas: stepData.step5_committee.secondary_personas,
            influencers: stepData.step5_committee.influencers,
          },
          scoring_weights: {
            industry_match: stepData.step6_scoring.industry_match,
            location_match: stepData.step6_scoring.location_match,
            hiring_signals: stepData.step6_scoring.hiring_signals,
            tech_stack_match: stepData.step6_scoring.tech_stack_match,
            funding_stage: stepData.step6_scoring.funding_stage,
            revenue_tier: stepData.step6_scoring.revenue_tier,
            employee_range: stepData.step6_scoring.employee_range,
            decision_makers_found: stepData.step6_scoring.decision_makers_found,
          },
        },
      };

      const { data: campaign } = await apiClient.post("/campaigns", payload);
      const { data: workflow } = await apiClient.post("/workflow/start", {
        campaign_id: campaign.id,
      });

      navigate(`/workflow/${workflow.workflow_id || workflow.id}`);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to launch campaign";
      setError(msg);
    } finally {
      setLaunching(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-white mb-1">Scoring Preferences</h2>
        <p className="text-xs mb-3" style={{ color: "var(--text-secondary)" }}>
          Set how much each dimension contributes to the overall company score
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Sliders */}
        <div className="space-y-2">
          <SliderField label="Industry Match" value={data.industry_match} onChange={(v) => updateWeight("industry_match", v)} />
          <SliderField label="Location Match" value={data.location_match} onChange={(v) => updateWeight("location_match", v)} />
          <SliderField label="Hiring Signals" value={data.hiring_signals} onChange={(v) => updateWeight("hiring_signals", v)} />
          <SliderField label="Tech Stack Match" value={data.tech_stack_match} onChange={(v) => updateWeight("tech_stack_match", v)} />
          <SliderField label="Funding Stage" value={data.funding_stage} onChange={(v) => updateWeight("funding_stage", v)} />
          <SliderField label="Revenue Tier" value={data.revenue_tier} onChange={(v) => updateWeight("revenue_tier", v)} />
          <SliderField label="Employee Range" value={data.employee_range} onChange={(v) => updateWeight("employee_range", v)} />
          <SliderField label="Decision Makers Found" value={data.decision_makers_found} onChange={(v) => updateWeight("decision_makers_found", v)} />

          {/* Total indicator */}
          <div
            className={cn(
              "mt-4 p-4 rounded-xl text-center font-bold text-lg transition-colors border",
              total === 100
                ? "border-green-500/30 text-green-400 bg-green-500/10"
                : "border-red-500/30 text-red-400 bg-red-500/10"
            )}
          >
            Total: {total} / 100
            {total !== 100 && <span className="block text-xs font-normal mt-1">Weights must sum to exactly 100</span>}
          </div>
        </div>

        {/* Preview Card */}
        <div>
          <h3 className="text-sm font-semibold text-white mb-3">Campaign Preview</h3>
          <div
            className="rounded-xl p-5 border space-y-3 text-sm"
            style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}
          >
            <div>
              <span className="text-xs" style={{ color: "var(--text-secondary)" }}>Campaign</span>
              <p className="text-white font-medium">{campaignName || "Unnamed Campaign"}</p>
            </div>
            <div>
              <span className="text-xs" style={{ color: "var(--text-secondary)" }}>Product Category</span>
              <p className="text-white">{PRODUCT_CATEGORIES.find((c) => c.value === stepData.step1_business.product_category)?.label || "Not set"}</p>
            </div>
            <div>
              <span className="text-xs" style={{ color: "var(--text-secondary)" }}>Geography</span>
              <p className="text-white">
                {stepData.step2_geography.countries.length} countries
                {stepData.step2_geography.cities.length > 0 && `, ${stepData.step2_geography.cities.length} cities`}
              </p>
            </div>
            <div>
              <span className="text-xs" style={{ color: "var(--text-secondary)" }}>Target Industries</span>
              <div className="flex flex-wrap gap-1 mt-1">
                {stepData.step3_company_filters.industries.slice(0, 3).map((ind) => (
                  <span key={ind} className="px-2 py-0.5 rounded text-[10px] font-medium bg-gray-700 text-gray-300">{ind}</span>
                ))}
                {stepData.step3_company_filters.industries.length > 3 && (
                  <span className="px-2 py-0.5 rounded text-[10px] font-medium bg-gray-700 text-gray-300">+{stepData.step3_company_filters.industries.length - 3}</span>
                )}
              </div>
            </div>
            <div>
              <span className="text-xs" style={{ color: "var(--text-secondary)" }}>Employee Range</span>
              <p className="text-white">{stepData.step3_company_filters.min_employees} – {stepData.step3_company_filters.max_employees}</p>
            </div>
            <div>
              <span className="text-xs" style={{ color: "var(--text-secondary)" }}>Primary Persona</span>
              <p className="text-white">{stepData.step5_committee.primary_persona.title || "Not set"}</p>
            </div>
            <div>
              <span className="text-xs" style={{ color: "var(--text-secondary)" }}>Total Score Weight</span>
              <p className={cn("font-bold", total === 100 ? "text-green-400" : "text-red-400")}>{total}/100</p>
            </div>
          </div>
        </div>
      </div>

      {/* Launch Button */}
      <div className="pt-4 border-t" style={{ borderColor: "var(--border)" }}>
        {error && (
          <p className="text-sm text-red-400 mb-3 text-center">{error}</p>
        )}
        <button
          type="button"
          onClick={handleLaunch}
          disabled={!isComplete || launching}
          className={cn(
            "w-full py-4 rounded-xl font-bold text-lg transition-all",
            isComplete && !launching
              ? "bg-[#4f7cff] text-white hover:shadow-[0_0_30px_rgba(79,124,255,0.5)]"
              : "bg-gray-700 text-gray-500 cursor-not-allowed"
          )}
        >
          {launching ? (
            <span className="flex items-center justify-center gap-2">
              <span className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              Launching...
            </span>
          ) : (
            "🚀 Launch Campaign"
          )}
        </button>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// Page Component
// ═══════════════════════════════════════════════════════════════════════════════

const stepVariants = {
  enter: (dir: number) => ({
    x: dir > 0 ? 300 : -300,
    opacity: 0,
  }),
  center: {
    x: 0,
    opacity: 1,
  },
  exit: (dir: number) => ({
    x: dir > 0 ? -300 : 300,
    opacity: 0,
  }),
};

export default function DiscoveryWizard() {
  const { currentStep, nextStep, prevStep } = useWizardStore();
  const [direction, setDirection] = useState(0);

  const handleNext = () => {
    setDirection(1);
    nextStep();
  };

  const handlePrev = () => {
    setDirection(-1);
    prevStep();
  };

  const stepComponents = [
    Step1Business,
    Step2Geography,
    Step3CompanyFilters,
    Step4Technology,
    Step5Committee,
    Step6Scoring,
  ];

  const CurrentStepComponent = stepComponents[currentStep];

  return (
    <div className="max-w-4xl mx-auto py-8 px-4">
      {/* Page Header */}
      <div className="mb-8 text-center">
        <h1 className="text-2xl font-bold text-white">Discovery Wizard</h1>
        <p className="text-sm mt-1" style={{ color: "var(--text-secondary)" }}>
          Step {currentStep + 1} of 6 — {STEPS[currentStep].desc}
        </p>
      </div>

      {/* Step Indicator */}
      <StepIndicator current={currentStep} />

      {/* Step Content */}
      <div className="relative min-h-[400px]">
        <AnimatePresence mode="wait" custom={direction}>
          <motion.div
            key={currentStep}
            custom={direction}
            variants={stepVariants}
            initial="enter"
            animate="center"
            exit="exit"
            transition={{ duration: 0.25, ease: "easeInOut" }}
          >
            <div
              className="rounded-xl p-6 border"
              style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}
            >
              <CurrentStepComponent />
            </div>
          </motion.div>
        </AnimatePresence>
      </div>

      {/* Navigation Footer */}
      <div className="flex items-center justify-between mt-8">
        <button
          type="button"
          onClick={handlePrev}
          disabled={currentStep === 0}
          className={cn(
            "px-6 py-2.5 rounded-lg text-sm font-medium transition-all border",
            currentStep === 0
              ? "border-gray-700 text-gray-600 cursor-not-allowed"
              : "border-gray-600 text-gray-300 hover:border-[#4f7cff] hover:text-[#4f7cff]"
          )}
        >
          ← Back
        </button>

        <div className="flex gap-1">
          {STEPS.map((_, i) => (
            <div
              key={i}
              className={cn(
                "w-2 h-2 rounded-full transition-all",
                i === currentStep ? "bg-[#4f7cff] w-6" : i < currentStep ? "bg-green-500" : "bg-gray-600"
              )}
            />
          ))}
        </div>

        {currentStep < 5 && (
          <button
            type="button"
            onClick={handleNext}
            className="px-6 py-2.5 rounded-lg text-sm font-medium bg-[#4f7cff] text-white hover:shadow-[0_0_20px_rgba(79,124,255,0.4)] transition-all"
          >
            Next →
          </button>
        )}
        {currentStep === 5 && (
          <div />
        )}
      </div>
    </div>
  );
}
