export interface ICPConfig {
  industry: string[];
  countries: string[];
  min_employees: number;
  max_employees: number;
  revenue_range: string;
  funding_stages: string[];
  hiring_keywords: string[];
  tech_stack: string[];
}

export interface PersonaConfig {
  name: string;
  role_keywords: string[];
  departments: string[];
  linkedin_keywords: string[];
  priority: number;
}

export interface ScoringConfig {
  funding_weight: number;
  hiring_weight: number;
  revenue_weight: number;
  icp_match_weight: number;
  tech_stack_weight: number;
  growth_weight: number;
}

export interface ConfigItem {
  id: string;
  name: string;
  type: "icp" | "persona" | "scoring";
  config_json: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}
