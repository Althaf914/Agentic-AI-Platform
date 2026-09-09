import { apiClient } from './client'

export const startWorkflow = async (configId: string) => {
  const res = await apiClient.post('/workflow/start', { configuration_id: configId })
  return res.data // { workflow_id, status }
}

export const getWorkflowStatus = async (workflowId: string) => {
  const res = await apiClient.get(`/workflow/${workflowId}/status`)
  return res.data // { id, status, started_at, completed_at, agent_logs }
}

export const getWorkflowResults = async (workflowId: string) => {
  const res = await apiClient.get(`/workflow/${workflowId}/results`)
  return res.data // { companies, recommendations }
}

export const getWorkflowList = async () => {
  const res = await apiClient.get('/workflows')
  return res.data // list of workflows
}

export const retryAgent = async (workflowId: string, agentName: string) => {
  const res = await apiClient.post(`/workflow/${workflowId}/retry-agent`, { agent_name: agentName })
  return res.data
}
