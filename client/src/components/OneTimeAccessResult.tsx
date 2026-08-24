import { useEffect, useRef, useState } from 'react'
import type { OneTimeAccess } from '../api/authentication'

export function OneTimeAccessResult({ access, onClose }: { access: OneTimeAccess; onClose: () => void }) {
  const [status, setStatus] = useState('Der Zugangslink wurde erstellt.')
  const inputRef = useRef<HTMLInputElement>(null)
  const titleRef = useRef<HTMLHeadingElement>(null)
  const link = `${window.location.origin}/account-access/#/${access.credential}`
  useEffect(() => { titleRef.current?.focus() }, [access.credential])
  async function copy() {
    try { await navigator.clipboard.writeText(link); setStatus('Der Zugangslink wurde kopiert.') }
    catch { inputRef.current?.select(); setStatus('Kopieren war nicht möglich. Markieren und kopieren Sie den Zugangslink manuell.') }
  }
  return <section className="one-time-access" aria-labelledby="one-time-access-title"><h2 ref={titleRef} id="one-time-access-title" tabIndex={-1}>Einmaliger Zugangslink</h2><p>Dieser Link wird nur jetzt angezeigt und ist bis {new Date(access.expiresAt).toLocaleString('de-AT')} gültig.</p><label>Zugangslink<input ref={inputRef} readOnly value={link} onFocus={(event) => event.currentTarget.select()} /></label><p role="status">{status}</p><div className="auth-actions"><button type="button" onClick={() => void copy()}>Link kopieren</button><button type="button" onClick={onClose}>Schließen</button></div></section>
}
