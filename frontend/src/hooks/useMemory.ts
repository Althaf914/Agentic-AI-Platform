import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  searchMemory,
  searchMemoryGet,
  getTimeline,
  checkDuplicate,
  updateMemoryStatus,
} from "@/api/memory";
import type { OutreachStatus } from "@/types/memory";

export function useMemorySearch() {
  return useMutation({
    mutationFn: ({ query, topK }: { query: string; topK?: number }) =>
      searchMemory(query, topK),
  });
}

export function useMemorySearchGet(q: string, limit = 20, campaignId?: string) {
  return useQuery({
    queryKey: ["memory-search", q, limit, campaignId],
    queryFn: () => searchMemoryGet(q, limit, campaignId),
    enabled: q.length >= 2,
    staleTime: 30_000,
  });
}

export function useMemoryTimeline(entityId: string | null) {
  return useQuery({
    queryKey: ["memory-timeline", entityId],
    queryFn: () => getTimeline(entityId!),
    enabled: !!entityId,
  });
}

export function useDuplicateCheck(domain: string | null) {
  return useQuery({
    queryKey: ["memory-duplicate", domain],
    queryFn: () => checkDuplicate(domain!),
    enabled: !!domain,
    staleTime: 60_000,
  });
}

export function useUpdateMemoryStatus() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ memoryId, status }: { memoryId: string; status: OutreachStatus }) =>
      updateMemoryStatus(memoryId, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["memory"] });
    },
  });
}
