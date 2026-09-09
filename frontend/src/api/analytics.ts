import { useQuery } from "@tanstack/react-query";
import { apiClient } from "./client";

// ─── Types ─────────────────────────────────────────────────────────────────���─

export interface FunnelMetrics {
  discovered: number;
  validated: number;
  rejected: number;
  tech_analyzed: number;
  decision_makers: number;
  enriched: number;
  qualified: number;
  tier_a: number;
  tier_b: number;
  tier_c: number;
  tier_discard: number;
  approved: number;
}

export interface TopCompany {
  id: string;
  name: string;
  domain: string;
  industry: string | null;
  country: string | null;
  qualification_score: number | null;
  tier: string | null;
  status: string;
  funding_stage: string | null;
  employee_count: number | null;
  market_signals_count: number;
}

export type TechDistribution = Record<string, number>;

export interface SignalBreakdown {
  funding: number;
  news: number;
  hiring: number;
  expansion: number;
  leadership: number;
  total_companies_with_signals: number;
}

// ─── API functions ───────────────────────────────────────────────────────────

async function getFunnel(workflowId?: string) {
  const params = workflowId ? { workflow_id: workflowId } : {};
  const { data } = await apiClient.get<FunnelMetrics>("/analytics/funnel", { params });
  return data;
}

async function getTopCompanies(limit = 10) {
  const { data } = await apiClient.get<TopCompany[]>("/analytics/top-companies", {
    params: { limit },
  });
  return data;
}

async function getTechDistribution() {
  const { data } = await apiClient.get<TechDistribution>("/analytics/tech-distribution");
  return data;
}

async function getSignalBreakdown() {
  const { data } = await apiClient.get<SignalBreakdown>("/analytics/signal-breakdown");
  return data;
}

// ─── React Query hooks ───────────────────────────────────────────────────────

const STALE_TIME = 5 * 60 * 1000; // 5 minutes for dashboard

export function useFunnel(workflowId?: string) {
  return useQuery({
    queryKey: ["analytics", "funnel", workflowId],
    queryFn: () => getFunnel(workflowId),
    staleTime: STALE_TIME,
  });
}

export function useTopCompanies(limit = 10) {
  return useQuery({
    queryKey: ["analytics", "top-companies", limit],
    queryFn: () => getTopCompanies(limit),
    staleTime: STALE_TIME,
  });
}

export function useTechDistribution() {
  return useQuery({
    queryKey: ["analytics", "tech-distribution"],
    queryFn: getTechDistribution,
    staleTime: STALE_TIME,
  });
}

export function useSignalBreakdown() {
  return useQuery({
    queryKey: ["analytics", "signal-breakdown"],
    queryFn: getSignalBreakdown,
    staleTime: STALE_TIME,
  });
}
