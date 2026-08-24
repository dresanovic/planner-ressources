import { useEffect, useRef, useState, type FormEvent } from 'react'
import { recoverAdministrator } from '../api/authentication'

export function AdministratorRecoveryPage() {
  const [credential, setCredential] = useState(''); const [password, setPassword] = useState(''); const [confirmation, setConfirmation] = useState(''); const [message, setMessage] = useState<string | null>(null); const [complete, setComplete] = useState(false)
  const credentialRef = useRef<HTMLInputElement>(null)
  const resultRef = useRef<HTMLParagraphElement>(null)
  useEffect(() => { if (complete) resultRef.current?.focus() }, [complete])
  async function submit(event: FormEvent) {
    event.preventDefault(); setMessage(null)
    if (password !== confirmation) { setCredential(''); setPassword(''); setConfirmation(''); setMessage('Die Passwörter stimmen nicht überein.'); queueMicrotask(() => credentialRef.current?.focus()); return }
    try { await recoverAdministrator(credential, password); setCredential(''); setPassword(''); setConfirmation(''); setComplete(true); setMessage('Das Passwort wurde festgelegt. Melden Sie sich jetzt an.') }
    catch { setCredential(''); setPassword(''); setConfirmation(''); setMessage('Der Startzugang ist nicht verfügbar. Prüfen Sie die bereitgestellten Zugangsdaten oder wenden Sie sich an den Infrastruktur-Betrieb.'); queueMicrotask(() => credentialRef.current?.focus()) }
  }
  return <main className="auth-layout"><section className="auth-card"><h1>Systemadministration wiederherstellen</h1>{message && <p ref={complete ? resultRef : undefined} id="recovery-message" role={complete ? 'status' : 'alert'} tabIndex={complete ? -1 : undefined} className="auth-message">{message}</p>}{!complete && <form onSubmit={(event) => void submit(event)}><label>Startzugang<input ref={credentialRef} required type="password" autoComplete="off" aria-invalid={!!message} aria-describedby={message ? 'recovery-message' : undefined} value={credential} onChange={(event) => setCredential(event.target.value)} /></label><label>Neues Passwort<input required type="password" minLength={12} maxLength={128} autoComplete="new-password" aria-invalid={!!message} aria-describedby={message ? 'recovery-message' : undefined} value={password} onChange={(event) => setPassword(event.target.value)} /></label><label>Passwort bestätigen<input required type="password" minLength={12} maxLength={128} autoComplete="new-password" aria-invalid={!!message} aria-describedby={message ? 'recovery-message' : undefined} value={confirmation} onChange={(event) => setConfirmation(event.target.value)} /></label><button type="submit">Passwort wiederherstellen</button></form>}<a href="/login/">Zur Anmeldung</a></section></main>
}
