import { useEffect, useRef, useState, type FormEvent } from 'react'

import { redeemAccountAccess } from '../api/authentication'

export function AccountAccessPage({ accessCredential, onCredentialConsumed }: { accessCredential: string | null; onCredentialConsumed?: () => void }) {
  const [password, setPassword] = useState('')
  const [confirmation, setConfirmation] = useState('')
  const [message, setMessage] = useState<string | null>(null)
  const [complete, setComplete] = useState(false)
  const passwordRef = useRef<HTMLInputElement>(null)
  const resultRef = useRef<HTMLParagraphElement>(null)
  useEffect(() => {
    if (complete) resultRef.current?.focus()
  }, [complete])
  async function submit(event: FormEvent) {
    event.preventDefault(); setMessage(null)
    if (!accessCredential || password !== confirmation) {
      setPassword(''); setConfirmation(''); setMessage(accessCredential ? 'Die Passwörter stimmen nicht überein.' : 'Der Zugang ist nicht verfügbar. Bitten Sie die Systemadministration um einen neuen Zugangslink.'); queueMicrotask(() => passwordRef.current?.focus()); return
    }
    try {
      const submittedCredential = accessCredential
      onCredentialConsumed?.()
      await redeemAccountAccess(submittedCredential, password)
      setPassword(''); setConfirmation(''); setComplete(true); setMessage('Das Passwort wurde festgelegt. Melden Sie sich jetzt an.')
      window.history.replaceState(window.history.state, '', '/account-access/')
    } catch {
      setPassword(''); setConfirmation(''); setMessage('Der Zugang ist nicht verfügbar. Bitten Sie die Systemadministration um einen neuen Zugangslink.'); passwordRef.current?.focus()
    }
  }
  return <main className="auth-layout"><section className="auth-card" aria-labelledby="access-title">
    <h1 id="access-title">Passwort festlegen</h1>
    {message && <p ref={complete ? resultRef : undefined} id="account-access-message" role={complete ? 'status' : 'alert'} tabIndex={complete ? -1 : undefined} className="auth-message">{message}</p>}
    {!complete && <form onSubmit={(event) => void submit(event)}>
      <label>Passwort<input ref={passwordRef} required type="password" minLength={12} maxLength={128} autoComplete="new-password" aria-invalid={!!message} aria-describedby={message ? 'account-access-message' : undefined} value={password} onChange={(event) => setPassword(event.target.value)} /></label>
      <label>Passwort bestätigen<input required type="password" minLength={12} maxLength={128} autoComplete="new-password" aria-invalid={!!message} aria-describedby={message ? 'account-access-message' : undefined} value={confirmation} onChange={(event) => setConfirmation(event.target.value)} /></label>
      <button type="submit">Passwort festlegen</button>
    </form>}
    <a href="/login/">Zur Anmeldung</a>
  </section></main>
}
