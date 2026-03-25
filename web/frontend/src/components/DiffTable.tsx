import type { CompareRow } from '../types'
import { displayParamName } from '../lib/paramName'

type DiffTableProps = {
  rows: CompareRow[]
  importIds: number[]
  idToLabel?: Record<string, string>
}

export function DiffTable({ rows, importIds, idToLabel }: DiffTableProps) {
  if (rows.length === 0) {
    return <p className="empty">No comparison rows.</p>
  }

  const HIDDEN_KEYS = new Set(['values', 'is_diff', 'stage', 'category', 'param_group'])
  const metaKeys = Object.keys(rows[0]).filter((key) => !HIDDEN_KEYS.has(key))

  const renderCell = (row: CompareRow, key: string) => {
    if (key === 'param_name') {
      return displayParamName(String(row[key] ?? ''), String(row.file_type ?? ''))
    }
    return String(row[key] ?? '')
  }

  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            {metaKeys.map((key) => (
              <th key={key}>{key}</th>
            ))}
            {importIds.map((id) => (
              <th key={id}>{idToLabel?.[String(id)] ?? `Import #${id}`}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, idx) => (
            <tr key={`row-${idx}`} className={row.is_diff ? 'diff-row' : ''}>
              {metaKeys.map((key) => (
                <td key={`${idx}-${key}`}>{renderCell(row, key)}</td>
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
