// ─── Approval status ─────────────────────────────────────────────────────────

export type ApprovalStatus = "pending" | "approved" | "rejected";

// ─── Contact info on approval card ──────────────────────────────────────────

export interface ApprovalContactInfo {
  id: string;
  full_name: string;
  role: string;
  email?: string | null;
  linkedin_url?: string | null;
  linkedin_confirmed: boolean;
  confidence_score: number;
  email_confidence?: number | null;
  email_verified: boolean;
  source?: string | null;
  is_primary_persona: boolean;
}

// ─── Buying committee ───────────────────────────────────────────────────────

export interface ApprovalCommitteePersona {
  id: string;
  full_name: string;
  role: string;
  linkedin_url: string;
  confidence_score: number;
  source: string;
}

export interface ApprovalBuyingCommittee {
  primary_persona?: ApprovalCommitteePersona | null;
  secondary_personas: ApprovalCommitteePersona[];
  influencers: ApprovalCommitteePersona[];
}

// ─── Full approval item (rich, from API) ─────────────────────────────────────

export interface ApprovalItem {
  id: string;
  recommendation_id: string;
  status: ApprovalStatus;
  comment?: string | null;
  rejection_reason?: string | null;
  decided_at?: string | null;

  // Company context
  company_id: string;
  company_name: string;
  company_domain: string;
  company_industry?: string | null;
  company_logo_url?: string | null;

  // Score & tier
  qualification_score?: number | null;
  tier?: string | null;
  score_breakdown?: Record<string, unknown> | null;

  // Recommendation detail
  priority: string;
  reason: string;
  confidence: number;
  outreach_subject?: string | null;
  outreach_template: string;
  linkedin_message?: string | null;
  market_trigger?: string | null;
  talking_points?: string[] | null;
  buying_committee?: ApprovalBuyingCommittee | null;
  outreach_channel?: string | null;
  follow_up_sequence?: Record<string, unknown>[] | null;

  // Contacts
  contacts: ApprovalContactInfo[];

  // Market signals
  market_signals?: Record<string, unknown> | null;

  // Reviewer
  reviewer_name?: string | null;
}

// ─── Approval stats ─────────────────────────────────────────────────────────

export interface ApprovalStats {
  pending: number;
  approved: number;
  rejected: number;
  avgScore: number;
  highPriority: number;
}

// ─── Bulk action ────────────────────────────────────────────────────────────

export type BulkAction = "approve_all_a" | "reject_all_c" | "approve_selected" | "reject_selected";

// ─── Rejection reasons ──────────────────────────────────────────────────────

export const REJECTION_REASONS = [
  { value: "not_in_target_market", label: "Not in target market" },
  { value: "already_customer", label: "Already a customer" },
  { value: "competitor", label: "Competitor" },
  { value: "too_small", label: "Too small" },
  { value: "too_large", label: "Too large" },
  { value: "wrong_geography", label: "Wrong geography" },
  { value: "bad_email_quality", label: "Bad email quality" },
  { value: "other", label: "Other" },
] as const;
