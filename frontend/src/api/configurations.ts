import { apiClient } from './client'

export async function saveICP(data: { name: string; config_json: object }) {
  const res = await apiClient.post("/config/icp", { ...data, type: "icp" })
  return res.data
}

export async function savePersona(data: { name: string; config_json: object }) {
  const res = await apiClient.post("/config/persona", { ...data, type: "persona" })
  return res.data
}

export async function saveScoring(data: { name: string; config_json: object }) {
  const res = await apiClient.post("/config/scoring", { ...data, type: "scoring" })
  return res.data
}

export async function listConfigs() {
  const { data } = await apiClient.get("/config/list")
  return data
}

export async function getConfig(id: string) {
  const { data } = await apiClient.get(`/config/${id}`)
  return data
}

export async function deleteConfig(id: string) {
  const { data } = await apiClient.delete(`/config/${id}`)
  return data
}
