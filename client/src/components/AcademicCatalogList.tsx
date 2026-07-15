import type { CatalogAudit } from '../api/academicCatalog'

type NamedRecord = CatalogAudit & { id: number; name: string }

export function AcademicCatalogList({ records, emptyLabel, onEdit, onDelete, onLifecycle }: { records: NamedRecord[]; emptyLabel: string; onEdit?: (record: NamedRecord) => void; onDelete?: (record: NamedRecord) => void; onLifecycle?: (record: NamedRecord) => void }) {
  if (records.length === 0) return <div className="empty-state">{emptyLabel}</div>
  return (
    <ul className="catalog-list">
      {records.map((record) => (
        <li key={record.id}>
          <span>{record.name}</span>
          <span className="catalog-record-actions"><span className="metadata-pill">{record.isActive ? 'Active' : 'Inactive'}</span>{onEdit && <button type="button" className="secondary-button compact-button" onClick={() => onEdit(record)}>Edit</button>}{onLifecycle && <button type="button" className="secondary-button compact-button" onClick={() => onLifecycle(record)}>{record.isActive ? 'Archive' : 'Reactivate'}</button>}{onDelete && <button type="button" className="secondary-button compact-button" onClick={() => onDelete(record)}>Delete</button>}</span>
        </li>
      ))}
    </ul>
  )
}
