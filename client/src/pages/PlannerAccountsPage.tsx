import { useCallback, useEffect, useRef, useState, type FormEvent } from 'react'

import {
  AuthenticationApiError,
  createPlannerAccount,
  disablePlannerAccount,
  inspectSession,
  issueReactivationAccess,
  issueResetAccess,
  listPlannerAccounts,
  reissueSetupAccess,
  transferAdministration,
  type CurrentAccount,
  type OneTimeAccess,
  type PlannerAccount,
} from '../api/authentication'
import { AccountActionDialog } from '../components/AccountActionDialog'
import { OneTimeAccessResult } from '../components/OneTimeAccessResult'

type Pending = { kind: 'reset' | 'disable' | 'reactivate' | 'transfer'; account: PlannerAccount }

export function PlannerAccountsPage({
  currentAccount,
  onCurrentAccountChange,
}: {
  currentAccount: CurrentAccount
  onCurrentAccountChange?: (account: CurrentAccount) => void
}) {
  const [accounts, setAccounts] = useState<PlannerAccount[]>([])
  const [error, setError] = useState<string | null>(null)
  const [loginName, setLoginName] = useState('')
  const [displayName, setDisplayName] = useState('')
  const [access, setAccess] = useState<OneTimeAccess | null>(null)
  const [pending, setPending] = useState<Pending | null>(null)
  const [busy, setBusy] = useState(false)
  const operationInFlight = useRef(false)

  const reconcileAuthorityLoss = useCallback(async () => {
    setAccounts([])
    setAccess(null)
    setPending(null)
    onCurrentAccountChange?.({ ...currentAccount, isAdministrator: false })
    try {
      onCurrentAccountChange?.(await inspectSession())
    } catch {
      // A session 401 is handled by the shared authentication invalidation event.
    }
  }, [currentAccount, onCurrentAccountChange])

  const refresh = useCallback(async () => {
    try {
      setAccounts(await listPlannerAccounts())
      setError(null)
    } catch (reason) {
      if (reason instanceof AuthenticationApiError && reason.status === 403) {
        await reconcileAuthorityLoss()
      } else {
        setError('Die Planer-Konten konnten nicht geladen werden.')
      }
    }
  }, [reconcileAuthorityLoss])

  useEffect(() => {
    let current = true
    void listPlannerAccounts()
      .then((items) => {
        if (current) {
          setAccounts(items)
          setError(null)
        }
      })
      .catch((reason) => {
        if (!current) return
        if (reason instanceof AuthenticationApiError && reason.status === 403) {
          void reconcileAuthorityLoss()
        } else {
          setError('Die Planer-Konten konnten nicht geladen werden.')
        }
      })
    return () => { current = false }
  }, [reconcileAuthorityLoss])

  function beginOperation(): boolean {
    if (operationInFlight.current) return false
    operationInFlight.current = true
    setBusy(true)
    setError(null)
    setAccess(null)
    return true
  }

  function finishOperation(): void {
    operationInFlight.current = false
    setBusy(false)
  }

  async function create(event: FormEvent) {
    event.preventDefault()
    if (!beginOperation()) return
    try {
      const result = await createPlannerAccount(loginName, displayName)
      setAccess(result.oneTimeAccess)
      setLoginName('')
      setDisplayName('')
      await refresh()
    } catch (reason) {
      if (reason instanceof AuthenticationApiError && reason.status === 403) {
        await reconcileAuthorityLoss()
      } else {
        setError('Das Planer-Konto konnte nicht erstellt werden.')
      }
    } finally {
      finishOperation()
    }
  }

  async function setup(account: PlannerAccount) {
    if (!beginOperation()) return
    try {
      const result = await reissueSetupAccess(account.id, account.revision)
      setAccess(result.oneTimeAccess)
      await refresh()
    } catch (reason) {
      if (reason instanceof AuthenticationApiError && reason.status === 403) {
        await reconcileAuthorityLoss()
      } else if (reason instanceof AuthenticationApiError && reason.code === 'stale_account') {
        await refresh()
        setError('Das Planer-Konto wurde geändert. Die Ansicht wurde aktualisiert.')
      } else {
        setError('Der Zugang konnte nicht erstellt werden.')
      }
    } finally {
      finishOperation()
    }
  }

  async function confirm() {
    if (!pending || !beginOperation()) return
    const action = pending
    try {
      if (action.kind === 'reset') {
        setAccess((await issueResetAccess(action.account.id, action.account.revision)).oneTimeAccess)
      }
      if (action.kind === 'disable') {
        await disablePlannerAccount(action.account.id, action.account.revision)
      }
      if (action.kind === 'reactivate') {
        setAccess((await issueReactivationAccess(action.account.id, action.account.revision)).oneTimeAccess)
      }
      if (action.kind === 'transfer') {
        const administrator = accounts.find((item) => item.id === currentAccount.id)
        if (!administrator) throw new Error('current administrator is missing')
        const formerAdministrator = await transferAdministration(
          action.account.id,
          action.account.revision,
          administrator.revision,
        )
        setPending(null)
        onCurrentAccountChange?.(formerAdministrator)
        return
      }
      setPending(null)
      await refresh()
    } catch (reason) {
      if (reason instanceof AuthenticationApiError && reason.status === 403) {
        await reconcileAuthorityLoss()
      } else if (reason instanceof AuthenticationApiError && reason.code === 'stale_account') {
        await refresh()
        setError('Das Planer-Konto wurde geändert. Die Ansicht wurde aktualisiert.')
      } else {
        setError('Die Aktion konnte nicht durchgeführt werden. Aktualisieren Sie die Ansicht und versuchen Sie es erneut.')
      }
      setPending(null)
    } finally {
      finishOperation()
    }
  }

  return (
    <section className="planner-accounts-page" aria-labelledby="accounts-title">
      <h1 id="accounts-title">Planer-Konten</h1>
      {error && <p role="alert" className="auth-message">{error}</p>}
      {access && <OneTimeAccessResult access={access} onClose={() => setAccess(null)} />}

      <form className="account-create" onSubmit={(event) => void create(event)}>
        <h2>Planer-Konto erstellen</h2>
        <label>Benutzername<input required maxLength={128} value={loginName} onChange={(event) => setLoginName(event.target.value)} /></label>
        <label>Anzeigename<input required maxLength={200} value={displayName} onChange={(event) => setDisplayName(event.target.value)} /></label>
        <button type="submit" disabled={busy}>Planer-Konto erstellen</button>
      </form>

      <ul className="account-list">
        {accounts.map((account) => (
          <li key={account.id}>
            <div>
              <h2>{account.displayName}</h2>
              <dl>
                <div><dt>Benutzername</dt><dd>{account.loginName}</dd></div>
                <div><dt>Zugriff</dt><dd>{account.accessLevel === 'administrator' ? 'Systemadministration' : 'Planer'}</dd></div>
                <div><dt>Status</dt><dd>{account.state === 'active' ? 'Aktiv' : 'Inaktiv'}</dd></div>
                <div><dt>Erstellt</dt><dd>{new Date(account.createdAt).toLocaleString('de-AT')}</dd></div>
                {account.disabledAt && <div><dt>Deaktiviert</dt><dd>{new Date(account.disabledAt).toLocaleString('de-AT')}</dd></div>}
                {account.reactivatedAt && <div><dt>Reaktiviert</dt><dd>{new Date(account.reactivatedAt).toLocaleString('de-AT')}</dd></div>}
              </dl>
            </div>
            {account.id !== currentAccount.id && (
              <div className="account-actions">
                {account.state === 'inactive' && !account.disabledAt && <button type="button" disabled={busy} onClick={() => void setup(account)}>Zugang erneut erstellen</button>}
                {account.state === 'active' && (
                  <>
                    <button type="button" disabled={busy} onClick={() => setPending({ kind: 'reset', account })}>Zugang zurücksetzen</button>
                    <button type="button" disabled={busy} onClick={() => setPending({ kind: 'disable', account })}>Deaktivieren</button>
                    <button type="button" disabled={busy} onClick={() => setPending({ kind: 'transfer', account })}>Administration übertragen</button>
                  </>
                )}
                {account.state === 'inactive' && account.disabledAt && <button type="button" disabled={busy} onClick={() => setPending({ kind: 'reactivate', account })}>Reaktivieren</button>}
              </div>
            )}
          </li>
        ))}
      </ul>

      {pending && (
        <AccountActionDialog
          title={`${pending.account.displayName}: ${pending.kind === 'reset' ? 'Zugang zurücksetzen' : pending.kind === 'disable' ? 'Deaktivieren' : pending.kind === 'reactivate' ? 'Reaktivieren' : 'Administration übertragen'}`}
          confirmLabel={pending.kind === 'reset' ? 'Zugang zurücksetzen' : pending.kind === 'disable' ? 'Deaktivieren' : pending.kind === 'reactivate' ? 'Reaktivieren' : 'Administration übertragen'}
          busy={busy}
          onCancel={() => setPending(null)}
          onConfirm={() => void confirm()}
        >
          <p>{pending.kind === 'reset' ? 'Das bisherige Passwort und die aktuelle Sitzung werden ungültig.' : pending.kind === 'disable' ? 'Das Konto kann sich danach nicht mehr anmelden.' : pending.kind === 'reactivate' ? 'Es wird ein neuer einmaliger Zugangslink erstellt.' : 'Dieses Konto übernimmt die Systemadministration. Sie bleiben als Planer angemeldet.'}</p>
        </AccountActionDialog>
      )}
    </section>
  )
}
