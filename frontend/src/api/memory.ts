import { apiClient } from './client'
import type {
  MemoryEntry,
  MemorySearchResponse,
  DuplicateCheckResponse,
  OutreachStatus,
} from '@/types/memory'

export async function searchMemory(query: string, topK: number = 5) {
  const { data } = await apiClient.post<MemoryEntry[]>("/memory/search", { query, top_k: topK })
  return data
}

export async function searchMemoryGet(q: string, limit = 20, campaignId?: string) {
  const params: Record<string, string | number> = { q, limit }
  if (campaignId) params.campaign_id = campaignId
  const { data } = await apiClient.get<MemorySearchResponse>("/memory/search", { params })
  return data
}

export async function getTimeline(entityId: string) {
  const { data } = await apiClient.get<MemoryEntry[]>(`/memory/timeline/${entityId}`)
  return data
}

export async function listMemory(limit = 50) {
  const { data } = await apiClient.get<MemoryEntry[]>("/memory", { params: { limit } })
  return data
}

export async function checkDuplicate(domain: string) {
  const { data } = await apiClient.get<DuplicateCheckResponse>("/memory/check-duplicate", {
    params: { domain },
  })
  return data
}

export async function updateMemoryStatus(memoryId: string, status: OutreachStatus) {
  const { data } = await apiClient.put(`/memory/${memoryId}/status`, { status })
  return data
}
