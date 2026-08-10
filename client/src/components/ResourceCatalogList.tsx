import type { ResourceRecord, ResourceType } from '../api/resourceCatalog'
import { label } from '../config/terminology'

export function ResourceCatalogList({ resourceType, records, onSelect, onRemove, onReactivate }: {
  resourceType: ResourceType
  records: ResourceRecord[]
  onSelect: (record: ResourceRecord) => void
  onRemove?: (record: ResourceRecord) => void
  onReactivate?: (record: ResourceRecord) => void
}) {
  if (records.length === 0) return <div className="empty-state">Keine {label(resourceType === 'rooms' ? 'room.plural' : 'lecturer.plural')} gefunden</div>
  return <ul className="catalog-list resource-catalog-list">{records.map((record) => <li key={record.id}>
    <span><strong>{record.name} · {record.referenceCode}</strong>{'capacity' in record && <small>Kapazität {record.capacity}</small>}</span>
    <span className="catalog-record-actions"><span className="metadata-pill">{record.isActive ? 'Aktiv' : 'Inaktiv'}</span><button type="button" className="secondary-button compact-button" onClick={() => onSelect(record)}>Bearbeiten</button>{record.isActive ? onRemove && <button type="button" className="secondary-button compact-button" onClick={() => onRemove(record)}>Entfernen</button> : onReactivate && <button type="button" className="secondary-button compact-button" onClick={() => onReactivate(record)}>Reaktivieren</button>}</span>
  </li>)}</ul>
}
