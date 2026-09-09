import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getApprovals, submitApproval } from "@/api/approvals";
import type { ApprovalDecision } from "@/api/approvals";
import type { ApprovalItem, ApprovalStats } from "@/types/approval";
import { useMemo } from "react";

export function useApprovals(status: string = "pending") {
  const queryClient = useQueryClient();

  const approvalsQuery = useQuery({
    queryKey: ["approvals", status],
    queryFn: () => getApprovals(status),
  });

  const submitMutation = useMutation({
    mutationFn: ({
      id,
      decision,
    }: {
      id: string;
      decision: ApprovalDecision;
    }) => submitApproval(id, decision),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["approvals"] });
    },
  });

  const approvals: ApprovalItem[] = approvalsQuery.data ?? [];

  const stats: ApprovalStats = useMemo(() => {
    const all = approvals;
    const pending = all.filter((a) => a.status === "pending").length;
    const approved = all.filter((a) => a.status === "approved").length;
    const rejected = all.filter((a) => a.status === "rejected").length;
    const scored = all.filter((a) => a.qualification_score != null);
    const avgScore = scored.length
      ? Math.round(scored.reduce((s, a) => s + (a.qualification_score ?? 0), 0) / scored.length)
      : 0;
    const highPriority = all.filter(
      (a) => a.priority === "high" && a.status === "pending"
    ).length;
    return { pending, approved, rejected, avgScore, highPriority };
  }, [approvals]);

  return {
    approvals,
    stats,
    isLoading: approvalsQuery.isLoading,
    submitApproval: submitMutation.mutate,
    isSubmitting: submitMutation.isPending,
  };
}
