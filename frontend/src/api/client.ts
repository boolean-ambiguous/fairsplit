import type { ExpenseCreate, Group, GroupDetail } from './types'

export class ApiError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.status = status
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const resp = await fetch(`/api${path}`, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...init?.headers },
  })
  if (!resp.ok) {
    const body = await resp.json().catch(() => ({ detail: resp.statusText }))
    const detail =
      typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail)
    throw new ApiError(detail, resp.status)
  }
  return resp.json() as Promise<T>
}

export const api = {
  listGroups: () => request<Group[]>('/groups'),
  createGroup: (name: string) =>
    request<Group>('/groups', { method: 'POST', body: JSON.stringify({ name }) }),
  getGroup: (groupId: string) => request<GroupDetail>(`/groups/${groupId}`),
  addMember: (groupId: string, name: string) =>
    request<GroupDetail>(`/groups/${groupId}/members`, {
      method: 'POST',
      body: JSON.stringify({ name }),
    }),
  addExpense: (groupId: string, body: ExpenseCreate) =>
    request<GroupDetail>(`/groups/${groupId}/expenses`, {
      method: 'POST',
      body: JSON.stringify(body),
    }),
}
