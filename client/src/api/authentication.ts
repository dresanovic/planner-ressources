import { plannerFetch, type PlannerFetchOptions } from './plannerFetch'

export type CurrentAccount = {
  id: number
  loginName: string
  displayName: string
  isAdministrator: boolean
}

export type PlannerAccount = {
  id: number
  loginName: string
  displayName: string
  accessLevel: 'planner' | 'administrator'
  state: 'active' | 'inactive'
  revision: number
  createdAt: string
  disabledAt: string | null
  reactivatedAt: string | null
}

export type OneTimeAccess = {
  credential: string
  purpose: 'setup' | 'reset' | 'reactivation'
  expiresAt: string
}

export type AccountWithOneTimeAccess = {
  account: PlannerAccount
  oneTimeAccess: OneTimeAccess
}

export class AuthenticationApiError extends Error {
  status: number
  code: string

  constructor(status: number, code: string, message: string) {
    super(message)
    this.status = status
    this.code = code
  }
}

const json = (body: unknown): RequestInit => ({
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(body),
})

function exactObject(value: unknown, keys: string[]): Record<string, unknown> {
  if (typeof value !== 'object' || value === null || Array.isArray(value)) throw new Error('invalid response')
  const record = value as Record<string, unknown>
  const actual = Object.keys(record).sort()
  if (actual.length !== keys.length || actual.some((key, index) => key !== [...keys].sort()[index])) throw new Error('invalid response')
  return record
}

async function request(path: string, init?: PlannerFetchOptions): Promise<unknown> {
  const response = await plannerFetch(path, init)
  if (response.status === 204) return undefined
  const payload = await response.json().catch(() => null)
  if (!response.ok) {
    const safe = exactObject(payload, ['code', 'message'])
    if (typeof safe.code !== 'string' || typeof safe.message !== 'string') throw new Error('invalid response')
    throw new AuthenticationApiError(response.status, safe.code, safe.message)
  }
  return payload
}

function currentAccount(value: unknown): CurrentAccount {
  const record = exactObject(value, ['id', 'loginName', 'displayName', 'isAdministrator'])
  if (typeof record.id !== 'number' || typeof record.loginName !== 'string' || typeof record.displayName !== 'string' || typeof record.isAdministrator !== 'boolean') throw new Error('invalid response')
  return record as CurrentAccount
}

function plannerAccount(value: unknown): PlannerAccount {
  const record = exactObject(value, ['id', 'loginName', 'displayName', 'accessLevel', 'state', 'revision', 'createdAt', 'disabledAt', 'reactivatedAt'])
  if (
    typeof record.id !== 'number' || typeof record.loginName !== 'string' || typeof record.displayName !== 'string'
    || !['planner', 'administrator'].includes(String(record.accessLevel)) || !['active', 'inactive'].includes(String(record.state))
    || typeof record.revision !== 'number' || typeof record.createdAt !== 'string'
    || (record.disabledAt !== null && typeof record.disabledAt !== 'string')
    || (record.reactivatedAt !== null && typeof record.reactivatedAt !== 'string')
  ) throw new Error('invalid response')
  return record as PlannerAccount
}

function issuedAccess(value: unknown): AccountWithOneTimeAccess {
  const record = exactObject(value, ['account', 'oneTimeAccess'])
  const access = exactObject(record.oneTimeAccess, ['credential', 'purpose', 'expiresAt'])
  if (typeof access.credential !== 'string' || access.credential.length !== 43 || !['setup', 'reset', 'reactivation'].includes(String(access.purpose)) || typeof access.expiresAt !== 'string') throw new Error('invalid response')
  return { account: plannerAccount(record.account), oneTimeAccess: access as OneTimeAccess }
}

export async function inspectSession(): Promise<CurrentAccount> {
  return currentAccount(await request('/api/auth/session'))
}

export async function login(loginName: string, password: string): Promise<CurrentAccount> {
  return currentAccount(await request('/api/auth/login', { ...json({ loginName, password }), invalidateOn401: false }))
}

export async function bootstrapAdministrator(startupCredential: string, loginName: string, displayName: string, password: string): Promise<void> {
  await request('/api/auth/bootstrap', { ...json({ startupCredential, loginName, displayName, password }), invalidateOn401: false })
}

export async function redeemAccountAccess(accessCredential: string, password: string): Promise<void> {
  await request('/api/auth/account-access/redemption', { ...json({ accessCredential, password }), invalidateOn401: false })
}

export async function recoverAdministrator(startupCredential: string, password: string): Promise<void> {
  await request('/api/auth/administrator-recovery', { ...json({ startupCredential, password }), invalidateOn401: false })
}

export async function logout(): Promise<void> {
  await request('/api/auth/logout', { method: 'POST' })
}

export async function changePassword(currentPassword: string, newPassword: string): Promise<void> {
  await request('/api/auth/password-change', { ...json({ currentPassword, newPassword }), activity: 'user' })
}

export async function listPlannerAccounts(): Promise<PlannerAccount[]> {
  const record = exactObject(await request('/api/planner-accounts', { activity: 'user' }), ['accounts'])
  if (!Array.isArray(record.accounts)) throw new Error('invalid response')
  return record.accounts.map(plannerAccount)
}

export async function createPlannerAccount(loginName: string, displayName: string): Promise<AccountWithOneTimeAccess> {
  return issuedAccess(await request('/api/planner-accounts', { ...json({ loginName, displayName }), activity: 'user' }))
}

async function accountAction(path: string, expectedRevision: number): Promise<AccountWithOneTimeAccess> {
  return issuedAccess(await request(path, { ...json({ expectedRevision }), activity: 'user' }))
}

export const reissueSetupAccess = (id: number, revision: number) => accountAction(`/api/planner-accounts/${id}/setup-access`, revision)
export const issueResetAccess = (id: number, revision: number) => accountAction(`/api/planner-accounts/${id}/reset-access`, revision)
export const issueReactivationAccess = (id: number, revision: number) => accountAction(`/api/planner-accounts/${id}/reactivation-access`, revision)

export async function disablePlannerAccount(id: number, revision: number): Promise<PlannerAccount> {
  return plannerAccount(await request(`/api/planner-accounts/${id}/disable`, { ...json({ expectedRevision: revision }), activity: 'user' }))
}

export async function transferAdministration(id: number, expectedTargetRevision: number, expectedAdministratorRevision: number): Promise<CurrentAccount> {
  return currentAccount(await request(`/api/planner-accounts/${id}/administrator-transfer`, {
    ...json({ expectedTargetRevision, expectedAdministratorRevision }),
    activity: 'user',
  }))
}
