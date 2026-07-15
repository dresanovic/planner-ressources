import type { ResourceRecord, ResourceType } from '../api/resourceCatalog'

export function ResourceCatalogList({ resourceType, records, onSelect, onRemove, onReactivate }: {
  resourceType: ResourceType
  records: ResourceRecord[]
  onSelect: (record: ResourceRecord) => void
  onRemove?: (record: ResourceRecord) => void
  onReactivate?: (record: ResourceRecord) => void
}) {
  if (records.length === 0) return <div className="empty-state">No {resourceType} found</div>
  return <ul className="catalog-list resource-catalog-list">{records.map((record) => <li key={record.id}>
    <span><strong>{record.name} · {record.referenceCode}</strong>{'capacity' in record && <small>Capacity {record.capacity}</small>}</span>
    <span className="catalog-record-actions"><span className="metadata-pill">{record.isActive ? 'Active' : 'Inactive'}</span><button type="button" className="secondary-button compact-button" onClick={() => onSelect(record)}>Edit</button>{record.isActive ? onRemove && <button type="button" className="secondary-button compact-button" onClick={() => onRemove(record)}>Remove</button> : onReactivate && <button type="button" className="secondary-button compact-button" onClick={() => onReactivate(record)}>Reactivate</button>}</span>
  </li>)}</ul>
}
