import { createContext, useContext } from 'react'
import type { useOptimizationOperation } from './useOptimizationOperation'

export type OptimizationSession = {
  operation: ReturnType<typeof useOptimizationOperation>
  openRequest: number
  requestOpen: () => void
}

export const OptimizationSessionContext = createContext<OptimizationSession | null>(null)

export function useOptimizationSession() {
  const session = useContext(OptimizationSessionContext)
  if (!session) throw new Error('OptimizationSessionProvider is required')
  return session
}
