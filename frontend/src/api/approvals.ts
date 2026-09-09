import { apiClient } from './client'
import type { ApprovalItem } from '@/types/approval'

export interface ApprovalDecision {
  status: "approved" | "rejected"
  comment?: string
  rejection_reason?: string
  channel?: "email" | "linkedin" | "both"
  scheduled_at?: string
  edited_template?: string
  edited_subject?: string
}

export async function getApprovals(status: string = "pending") {
  const { data } = await apiClient.get<ApprovalItem[]>("/approvals", { params: { status } })
  return data
}

export async function submitApproval(
  approvalId: string,
  decision: ApprovalDecision
) {
  const { data } = await apiClient.post<ApprovalItem>(`/approvals/${approvalId}`, decision)
  return data
}
