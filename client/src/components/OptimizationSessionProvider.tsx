import { useContext, useState, type ReactNode } from 'react'
import { OptimizationSessionContext } from '../hooks/optimizationSession'
import { useOptimizationOperation } from '../hooks/useOptimizationOperation'

function Session({ children }: { children: ReactNode }) {
  const operation = useOptimizationOperation()
  const [openRequest, setOpenRequest] = useState(0)
  return <OptimizationSessionContext.Provider value={{ operation, openRequest, requestOpen: () => setOpenRequest(value => value + 1) }}>
    {children}
  </OptimizationSessionContext.Provider>
}

// Standalone planning screens share the same lifetime rules as the full app.
export function OptimizationSessionProvider({ children }: { children: ReactNode }) {
  const existing = useContext(OptimizationSessionContext)
  return existing ? children : <Session>{children}</Session>
}
