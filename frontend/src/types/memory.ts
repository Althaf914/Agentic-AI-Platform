export interface MemoryEntry {
  id: string;
  entity_type: "company" | "contact" | "workflow";
  entity_id: string;
  summary: string;
  last_seen?: string | null;
  metadata_json?: Record<string, unknown> | null;
  created_at: string;
}

export interface MemoryTimeline {
  entity_id: string;
  entries: MemoryEntry[];
}

// ─── Search ────────────────────────────────────────────────────────��────────

export interface MemorySearchResult {
  id: string;
  entity_type: string;
  entity_id: string;
  summary: string;
  last_seen?: string | null;
  metadata?: Record<string, unknown> | null;
  distance?: number | null;
  created_at?: string | null;
}

export interface MemorySearchResponse {
  results: MemorySearchResult[];
  query: string;
  total: number;
}

// ─── Duplicate check ──────────────────────────────────────────────────���─────

export interface DuplicateCheckResponse {
  exists: boolean;
  last_seen?: string | null;
  campaign?: string | null;
  was_approved: boolean;
  memory_id?: string | null;
  summary?: string | null;
}

// ─── Status update ──────────────────────────────────────────────────────────

export type OutreachStatus = "outreach_sent" | "replied" | "in_pipeline" | "closed";

export const OUTREACH_STATUS_LABELS: Record<OutreachStatus, string> = {
  outreach_sent: "Outreach sent",
  replied: "Replied",
  in_pipeline: "In pipeline",
  closed: "Closed",
};

export const OUTREACH_STATUS_COLORS: Record<OutreachStatus, string> = {
  outreach_sent: "bg-blue-500/15 text-blue-400",
  replied: "bg-emerald-500/15 text-emerald-400",
  in_pipeline: "bg-amber-500/15 text-amber-400",
  closed: "bg-zinc-500/15 text-zinc-400",
};
