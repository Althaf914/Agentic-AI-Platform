import { create } from "zustand";
import type {
  AgentStatus,
  AgentDetail,
  WorkflowStats,
  ActivityEntry,
  ActivityEventType,
  CampaignInfo,
  DiscoveredCompany,
  AgentCardDetail,
  WorkflowResult,
} from "@/types/workflow";
import { getWorkflowResults } from "@/api/workflows";

interface WorkflowState {
  // ── Connection ──
  isConnected: boolean;

  // ── Workflow identity ──
  activeWorkflowId: string | null;
  activeConfigId: string | null;

  // ── Campaign info (from workflow_started / planner) ──
  campaign: CampaignInfo | null;

  // ── Agent details (one per agent, ordered) ──
  agents: AgentDetail[];

  // ��─ Live activity feed (reverse chrono, max 50) ──
  activityFeed: ActivityEntry[];

  // ── Workflow stats ──
  stats: WorkflowStats;

  // ── Per-agent expandable detail ──
  agentCardDetails: Record<string, AgentCardDetail>;

  // ── Per-agent company lists (last 5 per agent) ──
  discoveredCompanies: DiscoveredCompany[];

  // ── Cumulative event counts ──
  totalCompaniesFound: number;
  totalContactsFound: number;
  totalEmailsFound: number;

  // ── Internal helper ──
  _addActivity: (eventType: ActivityEventType, agentName: string, data: Record<string, unknown>) => void;

  // ── Actions ──
  setConnected: (v: boolean) => void;
  setActiveWorkflow: (id: string | null, configId?: string) => void;
  resetWorkflow: () => void;
  setAgents: (agents: AgentDetail[]) => void;

  // ── Event handlers ──
  handleWorkflowStarted: (data: Record<string, unknown>) => void;
  handleAgentStarted: (agentName: string, data: Record<string, unknown>) => void;
  handleAgentSubstep: (agentName: string, data: Record<string, unknown>) => void;
  handleAgentCompleted: (agentName: string, data: Record<string, unknown>) => void;
  handleAgentFailed: (agentName: string, data: Record<string, unknown>) => void;
  handleCompanyDiscovered: (data: Record<string, unknown>) => void;
  handleCompanyValidated: (data: Record<string, unknown>) => void;
  handleCompanyRejected: (data: Record<string, unknown>) => void;
  handleTechDetected: (data: Record<string, unknown>) => void;
  handleContactFound: (data: Record<string, unknown>) => void;
  handleQualificationScored: (data: Record<string, unknown>) => void;
  handleRecommendationCreated: (data: Record<string, unknown>) => void;
  handleWorkflowCompleted: (data: Record<string, unknown>) => void;
  handleWorkflowFailed: (data: Record<string, unknown>) => void;

  // ── Planner info ──
  setPlannerInfo: (campaign: CampaignInfo) => void;

  // ── Full results (fetched from API after completion) ──
  results: WorkflowResult | null;
  resultsLoading: boolean;
  fetchResults: (workflowId: string) => Promise<void>;
}

let activityCounter = 0;

const DEFAULT_STATS: WorkflowStats = {
  companiesFound: 0,
  validated: 0,
  rejected: 0,
  techAnalyzed: 0,
  marketSignals: 0,
  highUrgency: 0,
  contactsFound: 0,
  linkedinConfirmed: 0,
  emailsFound: 0,
  tierA: 0,
  tierB: 0,
  tierC: 0,
  recommendations: 0,
  avgEmailConfidence: 0,
  avgCompositeScore: 0,
};

export const useWorkflowStore = create<WorkflowState>((set, get) => ({
  // ── Initial state ──
  isConnected: false,
  activeWorkflowId: null,
  activeConfigId: null,
  campaign: null,
  agents: [],
  activityFeed: [],
  stats: { ...DEFAULT_STATS },
  agentCardDetails: {},
  discoveredCompanies: [],
  totalCompaniesFound: 0,
  totalContactsFound: 0,
  totalEmailsFound: 0,
  results: null,
  resultsLoading: false,

  setConnected: (v) => set({ isConnected: v }),

  setActiveWorkflow: (id, configId) =>
    set({ activeWorkflowId: id, activeConfigId: configId ?? null }),

  setAgents: (agents) => set({ agents }),

  resetWorkflow: () =>
    set({
      campaign: null,
      agents: [],
      activityFeed: [],
      stats: { ...DEFAULT_STATS },
      agentCardDetails: {},
      discoveredCompanies: [],
      totalCompaniesFound: 0,
      totalContactsFound: 0,
      totalEmailsFound: 0,
      results: null,
      resultsLoading: false,
    }),

  setPlannerInfo: (campaign) => set({ campaign }),

  fetchResults: async (workflowId) => {
    set({ resultsLoading: true });
    try {
      const data = await getWorkflowResults(workflowId);
      const companies = data.companies || [];
      const recommendations = data.recommendations || [];
      
      const stats = {
        companiesFound: companies.length,
        validated: companies.filter((c: any) => c.status === "validated").length,
        rejected: companies.filter((c: any) => c.status === "rejected").length,
        techAnalyzed: companies.filter((c: any) => c.tech_stack_json && c.tech_stack_json.length > 0).length,
        marketSignals: companies.filter((c: any) => c.growth_rate != null || c.funding_stage).length,
        highUrgency: companies.filter((c: any) => c.qualification_score != null && c.qualification_score >= 70).length,
        contactsFound: companies.reduce((acc: number, c: any) => acc + (c.contacts?.length || 0), 0),
        linkedinConfirmed: companies.reduce((acc: number, c: any) => acc + (c.contacts?.filter((ct: any) => ct.linkedin_url).length || 0), 0),
        emailsFound: companies.reduce((acc: number, c: any) => acc + (c.contacts?.filter((ct: any) => ct.email).length || 0), 0),
        tierA: companies.filter((c: any) => c.qualification_score != null && c.qualification_score >= 70).length,
        tierB: companies.filter((c: any) => c.qualification_score != null && c.qualification_score >= 40 && c.qualification_score < 70).length,
        tierC: companies.filter((c: any) => c.qualification_score != null && c.qualification_score < 40).length,
        recommendations: recommendations.length,
        avgEmailConfidence: (() => {
          const scored = companies.flatMap((c: any) => c.contacts || []).filter((ct: any) => ct.confidence_score != null);
          return scored.length ? scored.reduce((acc: number, ct: any) => acc + (ct.confidence_score || 0), 0) / scored.length : 0;
        })(),
        avgCompositeScore: (() => {
          const scored = companies.filter((c: any) => c.qualification_score != null);
          return scored.length ? scored.reduce((acc: number, c: any) => acc + (c.qualification_score || 0), 0) / scored.length : 0;
        })()
      };

      set({
        results: data as WorkflowResult,
        resultsLoading: false,
        stats,
        totalCompaniesFound: stats.companiesFound,
        totalContactsFound: stats.contactsFound,
        totalEmailsFound: stats.emailsFound
      });
    } catch {
      set({ resultsLoading: false });
    }
  },

  // ── Event handlers ──

  handleWorkflowStarted: (data) => {
    const campaign: CampaignInfo = {
      name: (data.campaign_name as string) || "Untitled",
      totalAgents: (data.total_agents as number) || 0,
    };
    set({ campaign });
    get()._addActivity("workflow_started", "workflow", {
      ...data,
      message: "Workflow started",
    });
  },

  handleAgentStarted: (agentName, data) => {
    set((s) => {
      const existing = s.agents.find((a) => a.name === agentName);
      const detail: AgentDetail = {
        name: agentName,
        status: "running",
        index: (data.agent_index as number) || s.agents.length,
        total: (data.total_agents as number) || s.agents.length,
      };
      const agents = existing
        ? s.agents.map((a) => (a.name === agentName ? { ...a, ...detail } : a))
        : [...s.agents, detail];
      return { agents };
    });
    get()._addActivity("agent_started", agentName, data);
  },

  handleAgentSubstep: (agentName, data) => {
    set((s) => ({
      agents: s.agents.map((a) =>
        a.name === agentName
          ? {
              ...a,
              substepName: data.substep_name as string,
              substepDetail: data.substep_detail as string,
              progressPct: (data.progress_pct as number) ?? a.progressPct,
            }
          : a
      ),
    }));
  },

  handleAgentCompleted: (agentName, data) => {
    set((s) => ({
      agents: s.agents.map((a) =>
        a.name === agentName
          ? {
              ...a,
              status: "completed" as AgentStatus,
              duration: (data.duration_seconds as number) || a.duration,
              outputSummary: (data.output_summary as string) || a.outputSummary,
              companyCount: (data.company_count as number) || a.companyCount,
            }
          : a
      ),
    }));
    get()._addActivity("agent_completed", agentName, data);
  },

  handleAgentFailed: (agentName, data) => {
    set((s) => ({
      agents: s.agents.map((a) =>
        a.name === agentName
          ? {
              ...a,
              status: "failed" as AgentStatus,
              error: (data.error as string) || a.error,
            }
          : a
      ),
    }));
    get()._addActivity("agent_failed", agentName, data);
  },

  handleCompanyDiscovered: (data) => {
    const name = data.company_name as string;
    const domain = data.domain as string;
    const co: DiscoveredCompany = { name, domain, sourceQuery: data.source_query as string };
    set((s) => ({
      discoveredCompanies: [co, ...s.discoveredCompanies].slice(0, 200),
      totalCompaniesFound: s.totalCompaniesFound + 1,
      stats: { ...s.stats, companiesFound: s.stats.companiesFound + 1 },
    }));
    get()._addActivity("company_discovered", "company_discovery", data);
  },

  handleCompanyValidated: (data) => {
    set((s) => ({
      stats: {
        ...s.stats,
        validated: s.stats.validated + 1,
        ...(data.checks_passed ? { avgCompositeScore: (data.checks_passed as number) / (data.checks_total as number) * 100 } : {}),
      },
    }));
    get()._addActivity("company_validated", "validation", data);
  },

  handleCompanyRejected: (data) => {
    set((s) => ({
      stats: { ...s.stats, rejected: s.stats.rejected + 1 },
    }));
    get()._addActivity("company_rejected", "validation", data);
  },

  handleTechDetected: (data) => {
    const companyName = data.company_name as string;
    const techStack = (data.tech_stack as string[]) || [];
    const matchScore = (data.match_score as number) || 0;

    set((s) => {
      const existing = s.agentCardDetails["tech_analysis"] || { topTechnologies: [] };
      const allTech = [...(existing.topTechnologies || []), ...techStack];
      // Keep top 10 unique
      const topTechnologies = [...new Set(allTech)].slice(0, 10);
      return {
        agentCardDetails: {
          ...s.agentCardDetails,
          tech_analysis: { ...existing, topTechnologies },
        },
        stats: { ...s.stats, techAnalyzed: s.stats.techAnalyzed + 1 },
      };
    });
    get()._addActivity("tech_detected", "tech_analysis", data);
  },

  handleContactFound: (data) => {
    const hasEmail = data.has_email === true;
    const hasLinkedin = data.has_linkedin === true;
    const source = data.source as string;
    set((s) => ({
      totalContactsFound: s.totalContactsFound + 1,
      stats: {
        ...s.stats,
        contactsFound: s.stats.contactsFound + 1,
        linkedinConfirmed: s.stats.linkedinConfirmed + (hasLinkedin ? 1 : 0),
        emailsFound: s.stats.emailsFound + (hasEmail ? 1 : 0),
      },
    }));
    get()._addActivity("contact_found", "decision_maker", data);
  },

  handleQualificationScored: (data) => {
    const tier = data.tier as string;
    set((s) => {
      const stats = { ...s.stats };
      if (tier === "A") stats.tierA += 1;
      else if (tier === "B") stats.tierB += 1;
      else if (tier === "C") stats.tierC += 1;
      stats.avgCompositeScore = (stats.avgCompositeScore * (stats.tierA + stats.tierB + stats.tierC - 1) + (data.score as number || 0)) / Math.max(stats.tierA + stats.tierB + stats.tierC, 1);

      // Store tier distribution in card detail
      const existing = s.agentCardDetails["qualification"] || {};
      const tierDist = existing.tierDistribution || { A: 0, B: 0, C: 0 };
      if (tier === "A") tierDist.A += 1;
      else if (tier === "B") tierDist.B += 1;
      else if (tier === "C") tierDist.C += 1;

      return {
        stats,
        agentCardDetails: {
          ...s.agentCardDetails,
          qualification: { ...existing, tierDistribution: tierDist },
        },
      };
    });
    get()._addActivity("qualification_scored", "qualification", data);
  },

  handleRecommendationCreated: (data) => {
    set((s) => ({
      stats: { ...s.stats, recommendations: s.stats.recommendations + 1 },
    }));
    get()._addActivity("recommendation_created", "recommendation_memory", data);
  },

  handleWorkflowCompleted: (data) => {
    const statsData = (data.stats as Record<string, number>) || {};
    set((s) => ({
      stats: {
        ...s.stats,
        ...statsData,
      },
    }));
    get()._addActivity("workflow_completed", "workflow", data);
  },

  handleWorkflowFailed: (data) => {
    get()._addActivity("workflow_failed", "workflow", data);
  },

  // ── Activity feed helper ──

  _addActivity(eventType: ActivityEventType, agentName: string, data: Record<string, unknown>) {
    const entry: ActivityEntry = {
      id: `act-${++activityCounter}`,
      timestamp: (data.timestamp as string) || new Date().toISOString(),
      eventType,
      agentName,
      payload: data,
    };
    set((s) => ({
      activityFeed: [entry, ...s.activityFeed].slice(0, 50),
    }));
  },
}));
