import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'

const SECRET_FRAGMENT = /^#\/([A-Za-z0-9_-]{43})$/

async function bootstrap() {
  const root = createRoot(document.getElementById('root')!)
  if (window.location.pathname === '/lecturer-review/') {
    const match = SECRET_FRAGMENT.exec(window.location.hash)
    const secret = match?.[1] ?? null
    window.history.replaceState(
      window.history.state,
      '',
      `${window.location.pathname}${window.location.search}`,
    )
    const { LecturerReviewPage } = await import(
      './pages/LecturerReviewPage.tsx'
    )
    root.render(
      <StrictMode>
        <LecturerReviewPage secret={secret} />
      </StrictMode>,
    )
    return
  }

  const { default: App } = await import('./App.tsx')
  root.render(
    <StrictMode>
      <App />
    </StrictMode>,
  )
}

void bootstrap()
