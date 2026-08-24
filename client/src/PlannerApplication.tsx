import { useCallback, useEffect, useState } from 'react'

import App from './App'
import { AuthenticationApiError, inspectSession, logout, type CurrentAccount } from './api/authentication'
import { advancePlannerAuthGeneration, PLANNER_AUTH_INVALIDATED_EVENT } from './api/plannerFetch'
import { AccountAccessPage } from './pages/AccountAccessPage'
import { AdministratorRecoveryPage } from './pages/AdministratorRecoveryPage'
import { BootstrapPage } from './pages/BootstrapPage'
import { LoginPage } from './pages/LoginPage'
import { PasswordChangePage } from './pages/PasswordChangePage'
import './App.css'

type AuthView = 'checking' | 'login' | 'bootstrap' | 'account-access' | 'recovery' | 'planner' | 'password-change' | 'logout'

function viewForPath(path: string): AuthView | null {
  if (path === '/login/') return 'login'
  if (path === '/bootstrap/') return 'bootstrap'
  if (path === '/account-access/') return 'account-access'
  if (path === '/administrator-recovery/') return 'recovery'
  return null
}

export default function PlannerApplication({ initialPath = window.location.pathname, accountAccessSecret = null, onAccountAccessSecretConsumed }: { initialPath?: string; accountAccessSecret?: string | null; onAccountAccessSecretConsumed?: () => void }) {
  const publicView = viewForPath(initialPath)
  const [view, setView] = useState<AuthView>(publicView ?? 'checking')
  const [account, setAccount] = useState<CurrentAccount | null>(null)
  const [loginMessage, setLoginMessage] = useState<string | undefined>()
  const [logoutPending, setLogoutPending] = useState(false)
  const [logoutFailed, setLogoutFailed] = useState(false)

  const showLogin = useCallback((message?: string) => {
    advancePlannerAuthGeneration()
    setAccount(null); setLoginMessage(message); setView('login')
    window.history.replaceState(window.history.state, '', '/login/')
  }, [])

  useEffect(() => {
    if (publicView) return
    let current = true
    void inspectSession().then((value) => {
      if (current) { setAccount(value); setView('planner') }
    }).catch(() => { if (current) showLogin() })
    return () => { current = false }
  }, [publicView, showLogin])

  useEffect(() => {
    const invalidated = () => showLogin('Ihre Sitzung ist beendet. Melden Sie sich erneut an.')
    globalThis.addEventListener(PLANNER_AUTH_INVALIDATED_EVENT, invalidated)
    return () => globalThis.removeEventListener(PLANNER_AUTH_INVALIDATED_EVENT, invalidated)
  }, [showLogin])

  const performLogout = useCallback(async () => {
    setLogoutPending(true)
    setLogoutFailed(false)
    try {
      await logout()
      showLogin()
    } catch (reason) {
      if (reason instanceof AuthenticationApiError && reason.status === 401) {
        showLogin('Ihre Sitzung ist beendet. Melden Sie sich erneut an.')
        return
      }
      setLogoutPending(false)
      setLogoutFailed(true)
      setView('logout')
    }
  }, [showLogin])

  const beginLogout = useCallback(() => {
    advancePlannerAuthGeneration()
    setAccount(null)
    setView('logout')
    window.history.replaceState(window.history.state, '', '/login/')
    void performLogout()
  }, [performLogout])

  if (view === 'checking') return <main className="auth-layout" aria-busy="true"><p role="status">Sitzung wird geprüft …</p></main>
  if (view === 'login') return <LoginPage message={loginMessage} onAuthenticated={(value) => { advancePlannerAuthGeneration(); setAccount(value); setLoginMessage(undefined); setView('planner'); window.history.replaceState(window.history.state, '', '/') }} />
  if (view === 'bootstrap') return <BootstrapPage onComplete={() => showLogin('Die Systemadministration wurde eingerichtet. Melden Sie sich jetzt an.')} />
  if (view === 'account-access') return <AccountAccessPage accessCredential={accountAccessSecret} onCredentialConsumed={onAccountAccessSecretConsumed} />
  if (view === 'recovery') return <AdministratorRecoveryPage />
  if (view === 'logout') return <main className="auth-layout"><section className="auth-card" aria-labelledby="logout-title" aria-busy={logoutPending || undefined}><h1 id="logout-title">Abmelden</h1>{logoutPending && <p role="status">Abmeldung wird bestätigt …</p>}{logoutFailed && <><p role="alert" className="auth-message">Die Abmeldung konnte nicht bestätigt werden. Ihre Planungsdaten wurden aus dieser Ansicht entfernt. Versuchen Sie die Abmeldung erneut, sobald die Verbindung verfügbar ist.</p><button type="button" onClick={() => void performLogout()}>Abmeldung erneut versuchen</button></>}</section></main>
  if (view === 'password-change') return <PasswordChangePage onCancel={() => setView('planner')} onComplete={() => showLogin('Das Passwort wurde geändert. Melden Sie sich jetzt an.')} />
  if (!account) return <LoginPage onAuthenticated={(value) => { advancePlannerAuthGeneration(); setAccount(value); setView('planner') }} />
  return <App currentAccount={account} onCurrentAccountChange={setAccount} onLogout={beginLogout} onPasswordChange={() => setView('password-change')} />
}
