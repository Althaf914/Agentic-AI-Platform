import { apiClient } from './client'
import type { ProspectFilters, PaginatedProspects, ProspectCompany } from '@/types/prospect'

export async function getProspects(params: ProspectFilters = {}) {
  const { data } = await apiClient.get<PaginatedProspects>("/prospects", { params })
  return data
}

export async function getProspectDetail(companyId: string) {
  const { data } = await apiClient.get<ProspectCompany>(`/prospects/${companyId}`)
  return data
}
