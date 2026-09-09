// ─── Contact ────────────────────────────────────────────────────────────────

export interface ProspectContact {
  id: string;
  full_name: string;
  role: string;
  department?: string | null;
  email?: string | null;
  phone?: string | null;
  linkedin_url?: string | null;
  linkedin_confirmed: boolean;
  confidence_score: number;
  source?: string | null;             // linkedin_serpapi | hunter_match | generated | website | formula
  is_primary_persona: boolean;
  email_confidence?: number | null;
  email_source?: string | null;       // website | hunter_domain | hunter_individual | formula
  email_verified: boolean;
  phone_type?: string | null;         // real | estimated
  enrichment_score?: number | null;
}

// ─── Score breakdown (8‑dimension) ──────────────────────────────────────────

export interface DimensionScore {
  score: number;
  weight: number;    // stored as percentage (e.g. 25)
  weighted: number;  // score * weight/100
  detail: string;
}

export interface ScoreBreakdown {
  industry_match: DimensionScore;
  location_match: DimensionScore;
  hiring_signals: DimensionScore;
  tech_stack_match: DimensionScore;
  funding_stage: DimensionScore;
  revenue_tier: DimensionScore;
  employee_range: DimensionScore;
  decision_makers_found: DimensionScore;

  composite: number;
  tier: string;          // "A" | "B" | "C" | "discard"
  reason?: string;
  strongest_signal?: string;
  weakest_signal?: string;
}

// ─── Market signals ─────────────────────────────────────────────────────────

export interface FundingSignal {
  detected: boolean;
  amount?: string;
  date?: string;
  investors?: string[];
}

export interface HiringSignal {
  detected: boolean;
  hiring_surge?: boolean;
  hiring_count_estimate?: number;
  roles?: string[];
}

export interface NewsSignal {
  detected: boolean;
  headline?: string;
  source?: string;
  url?: string;
}

export interface ExpansionSignal {
  detected: boolean;
  new_location?: string;
  timeline?: string;
}

export interface LeadershipSignal {
  detected: boolean;
  new_role?: string;
  person_name?: string;
}

export interface MarketSignals {
  urgency?: string;       // high | medium | low
  trigger_summary?: string;
  funding?: FundingSignal;
  hiring?: HiringSignal;
  news?: NewsSignal;
  expansion?: ExpansionSignal;
  leadership?: LeadershipSignal;
}

// ─── Tech stack detected ────────────────────────────────────────────────────

export interface TechStackDetected {
  confirmed?: string[];
  probable?: string[];
  required_match?: number;
  nice_to_have_match?: number;
  excluded_tech_found?: boolean;
}

// ─── Buying committee (from recommendation) ─────────────────────────────────

export interface CommitteePersona {
  id: string;
  full_name: string;
  role: string;
  linkedin_url: string;
  confidence_score: number;
  source: string;
}

export interface BuyingCommittee {
  primary_persona: CommitteePersona | null;
  secondary_personas: CommitteePersona[];
  influencers: CommitteePersona[];
}

// ─── Follow‑up touch ────────────────────────────────────────────────────────

export interface FollowUpTouch {
  touch: number;
  channel: string;
  day: number;
  subject: string;
  message: string;
}

// ─── Recommendation ─────────────────────────────────────────────────────────

export interface ProspectRecommendation {
  id: string;
  priority: string;              // high | medium | low
  reason: string;
  suggested_action: string;
  outreach_template: string;
  outreach_subject?: string | null;
  linkedin_message?: string | null;
  confidence: number;
  buying_committee?: BuyingCommittee | null;
  talking_points?: string[] | null;
  market_trigger?: string | null;
  outreach_channel?: string | null;
  follow_up_sequence?: FollowUpTouch[] | null;
}

// ─── Company (prospect) ─────────────────────────────────────────────────────

export interface ProspectCompany {
  id: string;
  name: string;
  domain: string;
  industry?: string | null;
  country?: string | null;
  city?: string | null;
  employee_count?: number | null;
  revenue_range?: string | null;
  funding_stage?: string | null;
  qualification_score?: number | null;
  status: string;                // pending | validated | rejected
  description?: string | null;
  logo_url?: string | null;
  linkedin_url?: string | null;
  domain_age_days?: number | null;
  hiring_signal_score?: number | null;
  has_linkedin: boolean;
  source?: string | null;
  growth_rate?: number | null;

  // JSON columns
  tech_stack_detected?: TechStackDetected | null;
  market_signals?: MarketSignals | null;
  score_breakdown?: ScoreBreakdown | null;
  validation_details?: Record<string, unknown> | null;
  metadata_json?: Record<string, unknown> | null;

  // Nested relations
  contacts: ProspectContact[];
  recommendation?: ProspectRecommendation | null;
}

// ─── Paginated response ─────────────────────────────────────────────────────

export interface PaginatedProspects {
  items: ProspectCompany[];
  total: number;
  total_raw: number;
  page: number;
  limit: number;
}

// ─── API filter params ──────────────────────────────────────────────────────

export interface ProspectFilters {
  workflow_id?: string;
  min_score?: number;
  industry?: string;
  status?: string;
  tier?: string;          // "A" | "B" | "C"
  has_email?: boolean;
  has_market_signal?: boolean;
  page?: number;
  limit?: number;
  sort?: string;          // score_desc | name | date
}
