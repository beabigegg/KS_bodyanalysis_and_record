import type { CompareRow } from '../types'

type DiffTableProps = {
  rows: CompareRow[]
  importIds: number[]
}

export function DiffTable({ rows, importIds }: DiffTableProps) {
  if (rows.length === 0) {
    return <p className="empty">No comparison rows.</p>
  }

  const metaKeys = Object.keys(rows[0]).filter((key) => key !== 'values' && key !== 'is_diff')

  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            {metaKeys.map((key) => (
              <th key={key}>{key}</th>
            ))}
            {importIds.map((id) => (
              <th key={id}>Import #{id}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, idx) => (
            <tr key={`${idx}-${String(row[metaKeys[0]])}`} className={row.is_diff ? 'diff-row' : ''}>
              {metaKeys.map((key) => (
                <td key={`${idx}-${key}`}>{String(row[key] ?? '')}</td>
              ))}
              {importIds.map((id) => (
                <td key={`${idx}-${id}`}>{String(row.values[String(id)] ?? '')}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

