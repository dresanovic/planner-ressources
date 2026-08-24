import { useRef, useState, type FormEvent } from 'react'

import { bootstrapAdministrator } from '../api/authentication'

const FAILURE = 'Der Startzugang ist nicht verfügbar. Prüfen Sie die bereitgestellten Zugangsdaten oder wenden Sie sich an den Infrastruktur-Betrieb.'

export function BootstrapPage({ onComplete }: { onComplete: () => void }) {
  const [startupCredential, setStartupCredential] = useState('')
  const [loginName, setLoginName] = useState('')
  const [displayName, setDisplayName] = useState('')
  const [password, setPassword] = useState('')
  const [confirmation, setConfirmation] = useState('')
  const [message, setMessage] = useState<string | null>(null)
  const passwordRef = useRef<HTMLInputElement>(null)

  async function submit(event: FormEvent) {
    event.preventDefault()
    setMessage(null)
    if (password !== confirmation) {
      setStartupCredential(''); setPassword(''); setConfirmation(''); setMessage('Die Passwörter stimmen nicht überein.'); queueMicrotask(() => passwordRef.current?.focus()); return
    }
    try {
      await bootstrapAdministrator(startupCredential, loginName, displayName, password)
      setStartupCredential(''); setPassword(''); setConfirmation('')
      onComplete()
    } catch {
      setStartupCredential(''); setPassword(''); setConfirmation(''); setMessage(FAILURE); passwordRef.current?.focus()
    }
  }

  return <main className="auth-layout"><section className="auth-card" aria-labelledby="bootstrap-title">
    <h1 id="bootstrap-title">Erste Systemadministration einrichten</h1>
    {message && <p id="bootstrap-error" role="alert" className="auth-message">{message}</p>}
    <form onSubmit={(event) => void submit(event)}>
      <label>Startzugang<input required type="password" autoComplete="off" aria-invalid={!!message} aria-describedby={message ? 'bootstrap-error' : undefined} value={startupCredential} onChange={(event) => setStartupCredential(event.target.value)} /></label>
      <label>Benutzername<input required maxLength={128} autoComplete="username" value={loginName} onChange={(event) => setLoginName(event.target.value)} /></label>
      <label>Anzeigename<input required maxLength={200} value={displayName} onChange={(event) => setDisplayName(event.target.value)} /></label>
      <label>Passwort<input ref={passwordRef} required type="password" minLength={12} maxLength={128} autoComplete="new-password" aria-invalid={!!message} aria-describedby={message ? 'bootstrap-error' : undefined} value={password} onChange={(event) => setPassword(event.target.value)} /></label>
      <label>Passwort bestätigen<input required type="password" minLength={12} maxLength={128} autoComplete="new-password" aria-invalid={!!message} aria-describedby={message ? 'bootstrap-error' : undefined} value={confirmation} onChange={(event) => setConfirmation(event.target.value)} /></label>
      <button type="submit">Systemadministration einrichten</button>
    </form>
    <a href="/login/">Zur Anmeldung</a>
  </section></main>
}
