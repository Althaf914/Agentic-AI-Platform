export type WorkflowStatus = "pending" | "running" | "completed" | "failed";
export type AgentStatus = "idle" | "running" | "completed" | "failed" | "skipped";

export interface AgentLog {
  id: string;
  agent_name: string;
  status: AgentStatus;
  error_message?: string;
  started_at?: string;
  completed_at?: string;
}

export interface PlannerLog {
  id: string;
  step_number: number;
  agent_selected: string;
  decision_reasoning: string;
  created_at: string;
}

export interface Workflow {
  id: string;
  status: WorkflowStatus;
  configuration_id: string;
  configuration_name?: string;
  campaign_name?: string;
  campaign_id?: string;
  started_at?: string;
  completed_at?: string;
  created_at: string;
  agent_logs?: AgentLog[];
}

export interface NodeState {
  agent_name: string;
  status: AgentStatus;
}

// ── Agent detail state (per-agent tracking for the viewer) ─────────

export interface AgentDetail {
  name: string;
  status: AgentStatus;
  duration?: number;
  outputSummary?: string;
  companyCount?: number;
  error?: string;
  substepName?: string;
  substepDetail?: string;
  progressPct?: number;
  index: number;
  total: number;
}

// ── Workflow-level stats ──────────────────────────────────────────

export interface WorkflowStats {
  companiesFound: number;
  validated: number;
  rejected: number;
  techAnalyzed: number;
  marketSignals: number;
  highUrgency: number;
  contactsFound: number;
  linkedinConfirmed: number;
  emailsFound: number;
  tierA: number;
  tierB: number;
  tierC: number;
  recommendations: number;
  avgEmailConfidence: number;
  avgCompositeScore: number;
}

// ── Activity feed entries ─────────────────────────────────────────

export type ActivityEventType =
  | "workflow_started"
  | "workflow_completed"
  | "workflow_failed"
  | "agent_started"
  | "agent_completed"
  | "agent_failed"
  | "agent_substep"
  | "company_discovered"
  | "company_validated"
  | "company_rejected"
  | "tech_detected"
  | "contact_found"
  | "qualification_scored"
  | "recommendation_created";

export interface ActivityEntry {
  id: string;
  timestamp: string;
  eventType: ActivityEventType;
  agentName: string;
  payload: Record<string, unknown>;
}

// ── WebSocket event envelope ──────────────────────────────────────

export interface WorkflowEvent {
  event_type: string;
  workflow_id: string;
  agent_name: string;
  data: Record<string, unknown>;
  timestamp: string;
}

// ── Campaign info ─────────────────────────────────────────────────

export interface CampaignInfo {
  name: string;
  strategySummary?: string;
  totalAgents?: number;
  activeAgents?: number;
  skippedAgents?: number;
  reasoning?: string;
}

// ── Discovery company (lightweight for activity list) ─────────────

export interface DiscoveredCompany {
  name: string;
  domain: string;
  sourceQuery?: string;
}

// ── Full results from /workflow/{id}/results ──────────────────────

export interface ContactResult {
  id: string;
  full_name: string;
  role: string;
  email?: string;
  phone?: string;
  linkedin_url?: string;
  confidence_score?: number;
  is_primary_persona: boolean;
}

export interface CompanyResult {
  id: string;
  name: string;
  domain: string;
  industry?: string;
  country?: string;
  city?: string;
  employee_count?: number;
  revenue_range?: string;
  funding_stage?: string;
  tech_stack_json?: string[];
  qualification_score?: number;
  score_breakdown?: Record<string, number>;
  status: string;
  rejection_reason?: string;
  logo_url?: string;
  description?: string;
  growth_rate?: number;
  contacts: ContactResult[];
  created_at?: string;
}

export interface WorkflowResultSummary {
  total_companies: number;
  validated: number;
  rejected: number;
  pending: number;
  with_scores: number;
  with_contacts: number;
  with_recommendations: number;
}

export interface WorkflowResult {
  summary: WorkflowResultSummary;
  companies: CompanyResult[];
  recommendations: any[];
}

// ── Agent card expandable detail ──────────────────────────────────

export interface AgentCardDetail {
  companies?: DiscoveredCompany[];
  validationBreakdown?: { check: string; passed: boolean; detail: string }[];
  topTechnologies?: string[];
  tierDistribution?: { A: number; B: number; C: number };
}
