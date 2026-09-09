import { useQuery } from "@tanstack/react-query";
import { getProspects, getProspectDetail } from "@/api/prospects";
import type { ProspectFilters } from "@/types/prospect";

export function useProspects(filters: ProspectFilters = {}) {
  return useQuery({
    queryKey: ["prospects", filters],
    queryFn: () => getProspects(filters),
  });
}

export function useProspectDetail(companyId: string | null) {
  return useQuery({
    queryKey: ["prospect", companyId],
    queryFn: () => getProspectDetail(companyId!),
    enabled: !!companyId,
  });
}
