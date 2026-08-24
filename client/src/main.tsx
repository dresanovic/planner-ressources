import { StrictMode } from 'react'
import { createRoot, type Root } from 'react-dom/client'
import './index.css'
import { fetchAndInitializeTerminology } from './config/terminology'

const SECRET_FRAGMENT = /^#\/([A-Za-z0-9_-]{43})$/

type ApplicationLoaders = {
  loadPlanner: () => Promise<{ default: React.ComponentType<{ initialPath?: string; accountAccessSecret?: string | null; onAccountAccessSecretConsumed?: () => void }> }>
  loadLecturerReview: () => Promise<{ LecturerReviewPage: React.ComponentType<{ secret: string | null }> }>
}

const defaultLoaders: ApplicationLoaders = {
  loadPlanner: () => import('./PlannerApplication.tsx'),
  loadLecturerReview: () => import('./pages/LecturerReviewPage.tsx'),
}

export async function renderApplication(root: Root, lecturerReview: boolean, lecturerSecret: string | null, loaders: ApplicationLoaders = defaultLoaders, initialAccountAccessSecret: string | null = null): Promise<void> {
  let accountAccessSecret = initialAccountAccessSecret

  function renderPlanner(App: React.ComponentType<{ initialPath?: string; accountAccessSecret?: string | null; onAccountAccessSecretConsumed?: () => void }>) {
    root.render(
      <StrictMode>
        <App
          initialPath={window.location.pathname}
          accountAccessSecret={accountAccessSecret}
          onAccountAccessSecretConsumed={() => {
            accountAccessSecret = null
            renderPlanner(App)
          }}
        />
      </StrictMode>,
    )
  }

  async function loadAndRender() {
    try {
      if (lecturerReview) {
        const { LecturerReviewPage } = await loaders.loadLecturerReview()
        root.render(<StrictMode><LecturerReviewPage secret={lecturerSecret} /></StrictMode>)
      } else {
        const { default: App } = await loaders.loadPlanner()
        renderPlanner(App)
      }
    } catch {
      root.render(<main className="bootstrap-error" role="alert"><h1>Anwendung konnte nicht geladen werden</h1><p>Die Bezeichnungen wurden geladen, aber die Anwendungsoberfläche ist vorübergehend nicht verfügbar.</p><button type="button" onClick={() => void loadAndRender()}>Anwendung erneut laden</button></main>)
    }
  }
  await loadAndRender()
}

async function bootstrap() {
  const root = createRoot(document.getElementById('root')!)
  const lecturerReview = window.location.pathname === '/lecturer-review/'
  const accountAccess = window.location.pathname === '/account-access/'
  let lecturerSecret: string | null = null
  let accountAccessSecret: string | null = null
  if (lecturerReview || accountAccess) {
    const match = SECRET_FRAGMENT.exec(window.location.hash)
    if (lecturerReview) lecturerSecret = match?.[1] ?? null
    if (accountAccess) accountAccessSecret = match?.[1] ?? null
    window.history.replaceState(
      window.history.state,
      '',
      `${window.location.pathname}${window.location.search}`,
    )
  }

  async function loadTerminologyAndRender() {
    try {
      await fetchAndInitializeTerminology()
    } catch {
      root.render(
        <main className="bootstrap-error" role="alert">
          <h1>Bezeichnungen konnten nicht geladen werden</h1>
          <p>Die Anwendung kann ohne die geprüften Bezeichnungen nicht sicher angezeigt werden. Prüfen Sie die Verbindung und versuchen Sie das Laden erneut.</p>
          <button type="button" onClick={() => void loadTerminologyAndRender()}>Erneut versuchen</button>
        </main>,
      )
      return
    }
    await renderApplication(root, lecturerReview, lecturerSecret, defaultLoaders, accountAccessSecret)
  }

  await loadTerminologyAndRender()
}

void bootstrap()
