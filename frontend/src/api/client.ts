import type {
  Dashboard,
  DashboardRange,
  Expense,
  ExpenseCreate,
  Group,
  GroupCreate,
  GroupDetail,
  GroupUpdate,
  Member,
  SettlementCreate,
  User,
} from './types'

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
    credentials: 'include',
    headers: { 'Content-Type': 'application/json', ...init?.headers },
  })
  if (!resp.ok) {
    const body = await resp.json().catch(() => ({ detail: resp.statusText }))
    const detail =
      typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail)
    throw new ApiError(detail, resp.status)
  }
  if (resp.status === 204) return undefined as T
  return resp.json() as Promise<T>
}

export const api = {
  // auth
  signup: (email: string) =>
    request<{ message: string }>('/auth/signup', {
      method: 'POST',
      body: JSON.stringify({ email }),
    }),
  verify: (token: string) =>
    request<User>('/auth/verify', { method: 'POST', body: JSON.stringify({ token }) }),
  setName: (name: string) =>
    request<User>('/auth/name', { method: 'POST', body: JSON.stringify({ name }) }),
  me: () => request<User>('/auth/me'),
  updateMe: (body: { name?: string; theme?: 'dark' | 'light' }) =>
    request<User>('/auth/me', { method: 'PATCH', body: JSON.stringify(body) }),
  logout: () => request<{ ok: boolean }>('/auth/logout', { method: 'POST' }),

  // groups
  listGroups: () => request<Group[]>('/groups'),
  createGroup: (body: GroupCreate) =>
    request<Group>('/groups', { method: 'POST', body: JSON.stringify(body) }),
  getGroup: (groupId: string) => request<GroupDetail>(`/groups/${groupId}`),
  updateGroup: (groupId: string, body: GroupUpdate) =>
    request<GroupDetail>(`/groups/${groupId}`, { method: 'PATCH', body: JSON.stringify(body) }),
  addMember: (groupId: string, name: string, email?: string) =>
    request<GroupDetail>(`/groups/${groupId}/members`, {
      method: 'POST',
      body: JSON.stringify({ name, email }),
    }),
  renameMember: (groupId: string, memberId: string, name: string) =>
    request<GroupDetail>(`/groups/${groupId}/members/${memberId}`, {
      method: 'PATCH',
      body: JSON.stringify({ name }),
    }),
  removeMember: (groupId: string, memberId: string) =>
    request<GroupDetail>(`/groups/${groupId}/members/${memberId}`, { method: 'DELETE' }),

  // expenses
  addExpense: (groupId: string, body: ExpenseCreate) =>
    request<GroupDetail>(`/groups/${groupId}/expenses`, {
      method: 'POST',
      body: JSON.stringify(body),
    }),
  updateExpense: (groupId: string, expenseId: string, body: ExpenseCreate) =>
    request<GroupDetail>(`/groups/${groupId}/expenses/${expenseId}`, {
      method: 'PATCH',
      body: JSON.stringify(body),
    }),
  deleteExpense: (groupId: string, expenseId: string) =>
    request<GroupDetail>(`/groups/${groupId}/expenses/${expenseId}`, { method: 'DELETE' }),

  // settlements
  recordSettlement: (groupId: string, body: SettlementCreate) =>
    request<GroupDetail>(`/groups/${groupId}/settlements`, {
      method: 'POST',
      body: JSON.stringify(body),
    }),

  // dashboard
  getDashboard: (range: DashboardRange) =>
    request<Dashboard>(`/dashboard?range=${range}`),
}

export type { Member, Expense }
