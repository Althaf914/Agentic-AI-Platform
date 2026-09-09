import { apiClient } from './client'

export async function login(email: string, password: string) {
  const { data } = await apiClient.post('/auth/login', { email, password })
  return data
}

export async function register(email: string, password: string, role: string) {
  const { data } = await apiClient.post('/auth/register', { email, password, role })
  return data
}
