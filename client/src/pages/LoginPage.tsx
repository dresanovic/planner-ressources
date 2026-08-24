import { useEffect, useRef, useState, type FormEvent } from 'react'

import { login, type CurrentAccount } from '../api/authentication'

const GENERIC_FAILURE = 'Die Anmeldung war nicht möglich. Prüfen Sie Ihre Angaben und versuchen Sie es erneut. Wenn Sie weiterhin keinen Zugang haben, wenden Sie sich an die Systemadministration.'

export function LoginPage({ message, onAuthenticated }: { message?: string; onAuthenticated: (account: CurrentAccount) => void }) {
  const [loginName, setLoginName] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(message ?? null)
  const [submitting, setSubmitting] = useState(false)
  const errorRef = useRef<HTMLParagraphElement>(null)
  const passwordRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (message) errorRef.current?.focus()
  }, [message])

  async function submit(event: FormEvent) {
    event.preventDefault()
    setSubmitting(true)
    setError(null)
    try {
      onAuthenticated(await login(loginName, password))
    } catch {
      setPassword('')
      setError(GENERIC_FAILURE)
      queueMicrotask(() => passwordRef.current?.focus())
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <main className="auth-layout">
      <section className="auth-card" aria-labelledby="login-title">
        <h1 id="login-title">Anmelden</h1>
        {error && <p ref={errorRef} id="login-error" className="auth-message" role="alert" tabIndex={-1}>{error}</p>}
        <form onSubmit={(event) => void submit(event)}>
          <label>Benutzername<input autoComplete="username" required maxLength={128} value={loginName} onChange={(event) => setLoginName(event.target.value)} /></label>
          <label>Passwort<input ref={passwordRef} type="password" autoComplete="current-password" required maxLength={128} aria-invalid={!!error} aria-describedby={error ? 'login-error' : undefined} value={password} onChange={(event) => setPassword(event.target.value)} /></label>
          <button type="submit" disabled={submitting}>{submitting ? 'Anmeldung läuft …' : 'Anmelden'}</button>
        </form>
        <nav className="auth-links" aria-label="Weitere Zugangswege">
          <a href="/bootstrap/">Erste Systemadministration einrichten</a>
          <a href="/administrator-recovery/">Systemadministration wiederherstellen</a>
        </nav>
      </section>
    </main>
  )
}
