import type { CatalogAudit } from '../api/academicCatalog'
import type { ReactNode } from 'react'

type NamedRecord = CatalogAudit & { id: number; name: string }

export function AcademicCatalogList({ records, emptyLabel, renderMetadata, onEdit, onDelete, onLifecycle, onCopy, groupBy }: { records: NamedRecord[]; emptyLabel: string; renderMetadata?: (record: NamedRecord) => ReactNode; onEdit?: (record: NamedRecord) => void; onDelete?: (record: NamedRecord) => void; onLifecycle?: (record: NamedRecord) => void; onCopy?: (record: NamedRecord, origin: HTMLButtonElement) => void; groupBy?: (record: NamedRecord) => string }) {
  if (records.length === 0) return <div className="empty-state">{emptyLabel}</div>
  if (groupBy) {
    const groups = new Map<string, NamedRecord[]>()
    for (const record of records) {
      const name = groupBy(record)
      groups.set(name, [...(groups.get(name) ?? []), record])
    }
    return <div>{[...groups].map(([name, items]) => <section key={name} aria-label={name}><h3>{name}</h3><AcademicCatalogList records={items} emptyLabel={emptyLabel} renderMetadata={renderMetadata} onEdit={onEdit} onDelete={onDelete} onLifecycle={onLifecycle} onCopy={onCopy} /></section>)}</div>
  }
  return (
    <ul className="catalog-list">
      {records.map((record) => (
        <li key={record.id}>
          <span>{record.name}{renderMetadata?.(record)}</span>
          <span className="catalog-record-actions"><span className="metadata-pill">{record.isActive ? 'Aktiv' : 'Inaktiv'}</span>{onEdit && <button type="button" className="secondary-button compact-button" onClick={() => onEdit(record)}>Bearbeiten</button>}{onCopy && <button type="button" className="secondary-button compact-button" onClick={(event) => onCopy(record,event.currentTarget)}>Kopieren</button>}{onLifecycle && <button type="button" className="secondary-button compact-button" onClick={() => onLifecycle(record)}>{record.isActive ? 'Archivieren' : 'Reaktivieren'}</button>}{onDelete && <button type="button" className="secondary-button compact-button" onClick={() => onDelete(record)}>Löschen</button>}</span>
        </li>
      ))}
    </ul>
  )
}
