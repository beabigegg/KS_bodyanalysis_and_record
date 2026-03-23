type ObjectTableProps = {
  rows: Array<Record<string, unknown>>
}

export function ObjectTable({ rows }: ObjectTableProps) {
  if (rows.length === 0) {
    return <p className="empty">No data.</p>
  }
  const headers = Array.from(
    rows.reduce((set, row) => {
      Object.keys(row).forEach((key) => set.add(key))
      return set
    }, new Set<string>()),
  )

  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            {headers.map((header) => (
              <th key={header}>{header}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, idx) => (
            <tr key={idx}>
              {headers.map((header) => (
                <td key={`${idx}-${header}`}>{String(row[header] ?? '')}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

