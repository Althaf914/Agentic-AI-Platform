/**
 * Preset campaign configurations for the Discovery Wizard.
 * Each preset auto-fills all 6 steps when selected in Step 1.
 */

export type PresetName = "b2b_saas" | "cybersecurity" | "staffing";

export interface PresetConfig {
  business: {
    description: string;
    product_category: string;
    value_proposition: string;
  };
  geography: {
    countries: string[];
    states: string[];
    cities: string[];
  };
  company_filters: {
    industries: string[];
    min_employees: number;
    max_employees: number;
    funding_stages: string[];
    min_revenue: string;
    max_revenue: string;
    company_age_min_years: number;
    exclude_keywords: string[];
  };
  technology_filters: {
    required_tech: string[];
    nice_to_have_tech: string[];
    exclude_tech: string[];
    cloud_providers: string[];
  };
  hiring_signals: {
    keywords: string[];
    job_titles: string[];
    departments: string[];
  };
  buying_committee: {
    primary_persona: { title: string; seniority: string; department: string };
    secondary_personas: { title: string; seniority: string; department: string }[];
    influencers: string[];
  };
  scoring_weights: {
    industry_match: number;
    location_match: number;
    hiring_signals: number;
    tech_stack_match: number;
    funding_stage: number;
    revenue_tier: number;
    employee_range: number;
    decision_makers_found: number;
  };
}

export const PRESETS: Record<PresetName, { label: string; description: string; config: PresetConfig }> = {
  b2b_saas: {
    label: "B2B SaaS",
    description: "AI-driven SaaS platforms selling to other SaaS, Cloud, and DevTool companies",
    config: {
      business: {
        description: "AI-powered platform that automates sales workflows and lead enrichment for B2B companies using machine learning.",
        product_category: "ai_platform",
        value_proposition: "Reduce manual prospecting time by 80% with AI-driven lead scoring and intent data.",
      },
      geography: {
        countries: ["US", "UK", "Canada"],
        states: ["California", "New York", "Texas", "Illinois"],
        cities: ["San Francisco", "New York", "Austin", "Chicago", "London"],
      },
      company_filters: {
        industries: ["SaaS", "Cloud", "Developer Tools", "Enterprise Software"],
        min_employees: 50,
        max_employees: 2000,
        funding_stages: ["Series A", "Series B", "Series C"],
        min_revenue: "$1M",
        max_revenue: "$500M",
        company_age_min_years: 2,
        exclude_keywords: ["outsourcing", "consulting", "agency"],
      },
      technology_filters: {
        required_tech: ["Python", "React", "AWS", "Kubernetes", "PostgreSQL"],
        nice_to_have_tech: ["TensorFlow", "PyTorch", "Snowflake", "Databricks"],
        exclude_tech: ["PHP", "ColdFusion", "ASP.NET WebForms"],
        cloud_providers: ["AWS", "GCP", "Azure"],
      },
      hiring_signals: {
        keywords: ["machine learning", "AI", "data science", "engineering", "growth"],
        job_titles: ["Software Engineer", "Data Scientist", "ML Engineer", "VP Engineering", "CTO"],
        departments: ["Engineering", "Data", "Product"],
      },
      buying_committee: {
        primary_persona: { title: "CTO", seniority: "C-Suite", department: "Engineering" },
        secondary_personas: [
          { title: "VP Engineering", seniority: "VP", department: "Engineering" },
          { title: "Head of Product", seniority: "Director", department: "Product" },
        ],
        influencers: ["Lead Architect", "Engineering Manager", "Data Science Lead"],
      },
      scoring_weights: {
        industry_match: 25,
        location_match: 10,
        hiring_signals: 15,
        tech_stack_match: 15,
        funding_stage: 15,
        revenue_tier: 5,
        employee_range: 10,
        decision_makers_found: 5,
      },
    },
  },
  cybersecurity: {
    label: "Cybersecurity",
    description: "Security platforms targeting InfoSec, Compliance, and Network Security teams",
    config: {
      business: {
        description: "Next-gen cloud security platform providing zero-trust network access, threat detection, and compliance automation.",
        product_category: "security_tool",
        value_proposition: "Detect and respond to threats in under 5 minutes with AI-powered security orchestration.",
      },
      geography: {
        countries: ["US", "UK", "Germany", "Israel"],
        states: ["California", "Virginia", "Texas", "New York"],
        cities: ["Tel Aviv", "San Francisco", "Arlington", "Austin", "London", "Berlin"],
      },
      company_filters: {
        industries: ["Cybersecurity", "InfoSec", "Network Security", "Compliance", "Defense"],
        min_employees: 50,
        max_employees: 5000,
        funding_stages: ["Seed", "Series A", "Series B"],
        min_revenue: "$1M",
        max_revenue: "$200M",
        company_age_min_years: 1,
        exclude_keywords: ["penetration testing only", "MSSP"],
      },
      technology_filters: {
        required_tech: ["SIEM", "Zero Trust", "Cloud Security", "IDP"],
        nice_to_have_tech: ["SOAR", "EDR", "XDR", "CASB"],
        exclude_tech: ["Legacy AV", "On-premise only"],
        cloud_providers: ["AWS", "Azure", "GCP"],
      },
      hiring_signals: {
        keywords: ["security", "CISO", "compliance", "threat detection", "incident response"],
        job_titles: ["CISO", "Security Engineer", "SOC Analyst", "Compliance Manager", "Security Architect"],
        departments: ["Security", "Compliance", "IT", "Engineering"],
      },
      buying_committee: {
        primary_persona: { title: "CISO", seniority: "C-Suite", department: "Security" },
        secondary_personas: [
          { title: "VP Security", seniority: "VP", department: "Security" },
          { title: "Compliance Officer", seniority: "Director", department: "Compliance" },
        ],
        influencers: ["Security Architect", "IT Director", "Network Engineer"],
      },
      scoring_weights: {
        industry_match: 25,
        location_match: 10,
        hiring_signals: 15,
        tech_stack_match: 15,
        funding_stage: 15,
        revenue_tier: 5,
        employee_range: 10,
        decision_makers_found: 5,
      },
    },
  },
  staffing: {
    label: "Staffing",
    description: "HR tech and recruiting platforms targeting talent acquisition teams",
    config: {
      business: {
        description: "AI-driven recruitment and talent acquisition platform matching candidates to roles using NLP and behavioral analytics.",
        product_category: "hr_software",
        value_proposition: "Fill roles 3x faster with AI-powered candidate matching and automated interview scheduling.",
      },
      geography: {
        countries: ["US", "UK", "Canada", "Australia"],
        states: ["California", "New York", "Illinois", "Texas"],
        cities: ["New York", "San Francisco", "Chicago", "Sydney", "Austin", "London"],
      },
      company_filters: {
        industries: ["HR", "Recruiting", "Staffing", "Talent Management", "Workforce Solutions"],
        min_employees: 10,
        max_employees: 500,
        funding_stages: ["Seed", "Series A"],
        min_revenue: "$100K",
        max_revenue: "$50M",
        company_age_min_years: 1,
        exclude_keywords: ["manual staffing", "temp agency only"],
      },
      technology_filters: {
        required_tech: ["ATS", "Salesforce", "LinkedIn", "HRIS"],
        nice_to_have_tech: ["Greenhouse", "Lever", "Workday", "BambooHR"],
        exclude_tech: ["Legacy PeopleSoft", "Homegrown ATS"],
        cloud_providers: ["AWS", "GCP"],
      },
      hiring_signals: {
        keywords: ["recruiter", "talent acquisition", "HR", "people operations", "hiring manager"],
        job_titles: ["Head of Talent", "Recruiter", "HR Manager", "Talent Director", "People Ops Lead"],
        departments: ["HR", "Talent Acquisition", "People Operations"],
      },
      buying_committee: {
        primary_persona: { title: "Head of Talent", seniority: "Director", department: "HR" },
        secondary_personas: [
          { title: "CEO", seniority: "C-Suite", department: "Executive" },
          { title: "HR Operations Manager", seniority: "Manager", department: "HR" },
        ],
        influencers: ["VP People", "Recruiting Team Lead", "Hiring Manager"],
      },
      scoring_weights: {
        industry_match: 25,
        location_match: 10,
        hiring_signals: 15,
        tech_stack_match: 15,
        funding_stage: 15,
        revenue_tier: 5,
        employee_range: 10,
        decision_makers_found: 5,
      },
    },
  },
};
