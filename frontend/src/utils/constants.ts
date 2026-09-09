export const INDUSTRIES = [
  "SaaS", "Fintech", "HealthTech", "CyberSecurity",
  "EdTech", "HRTech", "Cloud", "DevTools", "AI/ML",
];

export const COUNTRIES = [
  "United States", "United Kingdom", "Canada", "Germany",
  "Israel", "India", "Australia", "Singapore", "Switzerland",
];

export const ROLES = [
  "VP", "Director", "Head", "Chief", "Manager", "Lead",
];

export const DEPARTMENTS = [
  "Engineering", "Sales", "Marketing", "Product",
  "Operations", "Finance", "HR",
];

export const FUNDING_STAGES = [
  "Seed", "Series A", "Series B", "Series C", "Series D", "IPO",
];

export const PRESET_CONFIGS = {
  saas: {
    icp: {
      industry: ["SaaS", "Cloud", "DevTools"],
      countries: ["United States", "United Kingdom", "Canada"],
      min_employees: 50,
      max_employees: 500,
      revenue_range: "$5M-$50M",
      funding_stages: ["Series A", "Series B", "Series C"],
      hiring_keywords: ["backend engineer", "platform engineer", "DevOps"],
      tech_stack: ["Python", "React", "AWS", "Kubernetes"],
    },
    personas: [
      { name: "VP Engineering", role_keywords: ["VP", "Director"], departments: ["Engineering"], linkedin_keywords: ["scaling", "platform"], priority: 1 },
      { name: "CTO", role_keywords: ["CTO", "Chief"], departments: ["Engineering"], linkedin_keywords: ["architecture", "tech strategy"], priority: 2 },
    ],
    scoring: { funding_weight: 0.15, hiring_weight: 0.15, revenue_weight: 0.2, icp_match_weight: 0.25, tech_stack_weight: 0.15, growth_weight: 0.1 },
    color: "#4f7cff",
    icon: "💼",
  },
  staffing: {
    icp: {
      industry: ["HRTech", "Staffing"],
      countries: ["United States", "India", "Australia"],
      min_employees: 20,
      max_employees: 200,
      revenue_range: "$1M-$20M",
      funding_stages: ["Seed", "Series A"],
      hiring_keywords: ["recruiter", "talent acquisition"],
      tech_stack: ["Python", "Ruby", "React"],
    },
    personas: [
      { name: "Head of Talent", role_keywords: ["Head", "Director"], departments: ["HR", "Recruiting"], linkedin_keywords: ["hiring", "talent"], priority: 1 },
    ],
    scoring: { funding_weight: 0.1, hiring_weight: 0.25, revenue_weight: 0.15, icp_match_weight: 0.25, tech_stack_weight: 0.1, growth_weight: 0.15 },
    color: "#a855f7",
    icon: "👥",
  },
  cybersecurity: {
    icp: {
      industry: ["CyberSecurity", "Cloud Security"],
      countries: ["United States", "Israel", "Germany"],
      min_employees: 100,
      max_employees: 1000,
      revenue_range: "$10M-$100M",
      funding_stages: ["Series B", "Series C", "Series D"],
      hiring_keywords: ["security engineer", "threat researcher", "SOC analyst"],
      tech_stack: ["Python", "Go", "Rust", "AWS"],
    },
    personas: [
      { name: "CISO", role_keywords: ["CISO", "VP", "Director"], departments: ["Security", "Engineering"], linkedin_keywords: ["zero trust", "threat"], priority: 1 },
    ],
    scoring: { funding_weight: 0.2, hiring_weight: 0.1, revenue_weight: 0.2, icp_match_weight: 0.2, tech_stack_weight: 0.2, growth_weight: 0.1 },
    color: "#22d3a5",
    icon: "🛡️",
  },
} as const;
