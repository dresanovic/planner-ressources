export type ProblemTone = 'blocking' | 'warning'
export type ProblemCategory =
  | 'validation'
  | 'stale'
  | 'connectivity'
  | 'permission'
  | 'unexpected'

export type ProblemAction = {
  label: string
  onClick?: () => void
  href?: string
}

export type UserProblem = {
  key: string
  tone: ProblemTone
  title: string
  details: string[]
  fieldId?: string
  action?: ProblemAction
}

export type ProblemContext = {
  action: string
  item?: string
  inputPreserved?: boolean
  outcomeUnknown?: boolean
  safeRetry?: () => void
}

export function fieldProblem(
  fieldId: string,
  fieldLabel: string,
  expectation: string,
): UserProblem {
  return {
    key: `field-${fieldId}`,
    tone: 'blocking',
    title: `${fieldLabel} korrigieren`,
    details: [
      `Die Eingabe blockiert das Fortsetzen. Erwartet wird ${expectation}.`,
      'Ihre übrigen Eingaben bleiben erhalten.',
    ],
    fieldId,
  }
}

export function operationProblem(
  category: Exclude<ProblemCategory, 'validation'>,
  context: ProblemContext,
  _unsafeCause?: unknown,
): UserProblem {
  void _unsafeCause
  const affected = context.item ? ` für „${context.item}“` : ''
  const preserved = context.inputPreserved
    ? 'Ihre Eingaben bleiben in diesem Formular erhalten.'
    : undefined
  const base = {
    key: `${category}-${context.action}-${context.item ?? 'allgemein'}`,
    tone: 'blocking' as const,
    title: `${context.action} nicht möglich`,
  }

  if (category === 'stale') {
    return {
      ...base,
      details: [
        `Der aktuelle Datensatz${affected} wurde zwischenzeitlich aktualisiert.`,
        preserved,
        'Laden Sie den aktuellen Stand neu, prüfen Sie die Werte und wiederholen Sie die Aktion erst danach.',
      ].filter((detail): detail is string => Boolean(detail)),
    }
  }
  if (category === 'permission') {
    return {
      ...base,
      details: [
        `Für „${context.action}“${affected} fehlt die erforderliche Berechtigung.`,
        preserved,
        'Prüfen Sie den Datensatz ohne Änderung oder wenden Sie sich an eine zuständige planende Person.',
      ].filter((detail): detail is string => Boolean(detail)),
    }
  }
  if (category === 'connectivity') {
    const ambiguous = context.outcomeUnknown
      ? 'Wegen der unterbrochenen Verbindung ist das Ergebnis unbekannt. Laden und prüfen Sie den aktuellen Stand, bevor Sie die Aktion wiederholen.'
      : 'Die Verbindung zum Dienst konnte nicht hergestellt werden.'
    return {
      ...base,
      details: [ambiguous, preserved].filter((detail): detail is string => Boolean(detail)),
      action:
        !context.outcomeUnknown && context.safeRetry
          ? { label: 'Erneut versuchen', onClick: context.safeRetry }
          : undefined,
    }
  }
  return {
    ...base,
    details: [
      `Die genaue Ursache für „${context.action}“${affected} ist nicht verfügbar.`,
      preserved,
      context.outcomeUnknown
        ? 'Laden und prüfen Sie den aktuellen Stand, bevor Sie die Aktion wiederholen.'
        : 'Versuchen Sie es später erneut oder laden Sie den aktuellen Stand neu.',
    ].filter((detail): detail is string => Boolean(detail)),
    action:
      !context.outcomeUnknown && context.safeRetry
        ? { label: 'Erneut versuchen', onClick: context.safeRetry }
        : undefined,
  }
}

export function safeReasonText(code: string, context = 'Datensatz'): string {
  const normalized = code.toUpperCase()
  if (normalized.includes('STALE') || normalized.includes('REVISION')) return `${context}: Die Daten wurden zwischenzeitlich geändert. Laden Sie den aktuellen Stand und prüfen Sie ihn vor einem weiteren Versuch.`
  if (normalized.includes('CAPACITY')) return `${context}: Die verfügbare Kapazität reicht nicht aus. Wählen Sie eine geeignete Ressource oder passen Sie die Zuordnung an.`
  if (normalized.includes('CONFLICT') || normalized.includes('OVERLAP') || normalized.includes('OCCUPIED')) return `${context}: Es besteht eine zeitliche Überschneidung oder die benötigte Ressource ist bereits belegt. Prüfen und ändern Sie einen der betroffenen Termine.`
  if (normalized.includes('HOLIDAY')) return `${context}: Ein betroffener Termin liegt auf einem Feiertag. Prüfen Sie das Datum und behalten oder ändern Sie den Termin bewusst.`
  if (normalized.includes('FINAL_TEACHING_SESSION_MISSING')) return `${context}: Der letzte Lehrtermin fehlt. Speichern Sie zuerst den vollständigen Lehrplan und bereiten Sie die Prüfung danach erneut vor.`
  if (normalized.includes('ACTIVE_EXAM')) return `${context}: Es besteht bereits eine aktive Prüfung. Bearbeiten oder löschen Sie diese Prüfung, bevor Sie eine neue erzeugen.`
  if (normalized.includes('PERMISSION') || normalized.includes('FORBIDDEN')) return `${context}: Die Aktion ist mit der aktuellen Berechtigung nicht möglich. Wenden Sie sich an eine zuständige planende Person.`
  return `${context}: Die Aktion konnte nicht abgeschlossen werden. Die genaue Ursache ist nicht verfügbar; prüfen Sie den aktuellen Stand vor einem weiteren Versuch.`
}
