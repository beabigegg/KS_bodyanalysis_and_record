export function downloadCsv(filename: string, rows: Array<Record<string, unknown>>): void {
  if (rows.length === 0) {
    return
  }
  const keys = Array.from(
    rows.reduce((set, row) => {
      Object.keys(row).forEach((key) => set.add(key))
      return set
    }, new Set<string>()),
  )

  const escape = (value: unknown): string => {
    if (value === null || value === undefined) {
      return ''
    }
    const raw = String(value).replace(/"/g, '""')
    return `"${raw}"`
  }

  const lines = [
    keys.map((k) => `"${k.replace(/"/g, '""')}"`).join(','),
    ...rows.map((row) => keys.map((key) => escape(row[key])).join(',')),
  ]
  const blob = new Blob([lines.join('\n')], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

