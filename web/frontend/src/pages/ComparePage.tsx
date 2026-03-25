import React, { useEffect, useMemo, useState } from 'react'
import { api, type ApiResponse } from '../lib/api'
import type { ComparePayload, ImportRecord } from '../types'
import { DiffTable } from '../components/DiffTable'
import { GroupedDiffTable } from '../components/GroupedDiffTable'

export function ComparePage() {
  const [imports, setImports] = useState<ImportRecord[]>([])
  const [selectedProduct, setSelectedProduct] = useState('')
  const [selectedBop, setSelectedBop] = useState('')
  const [selectedWafer, setSelectedWafer] = useState('')
  const [selectedIds, setSelectedIds] = useState<number[]>([])
  const [fileType, setFileType] = useState('')
  const [showAll, setShowAll] = useState(false)
  const [result, setResult] = useState<ComparePayload | null>(null)

  const filteredParams = useMemo(() => {
    if (!result) return []
    if (!fileType) return result.params
    const lower = fileType.toLowerCase()
    return result.params.filter(
      (row) =>
        String(row.file_type ?? '').toLowerCase().includes(lower) ||
        String(row.param_name ?? '').toLowerCase().includes(lower),
    )
  }, [result, fileType])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    void (async () => {
      try {
        // Load enough records to cover all machines; paginate if needed
        let allImports: ImportRecord[] = []
        let page = 1
        const pageSize = 200
        let hasMore = true
        while (hasMore) {
          const response = await api.get<ApiResponse<ImportRecord[]>>('/imports', {
            params: { page, page_size: pageSize },
          })
          allImports = allImports.concat(response.data.data)
          hasMore = allImports.length < response.data.total
          page++
        }
        setImports(allImports)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load import records.')
      }
    })()
  }, [])

  const productOptions = useMemo(() => Array.from(new Set(imports.map((x) => x.product_type))), [imports])
  const bopOptions = useMemo(() => {
    return Array.from(
      new Set(imports.filter((x) => !selectedProduct || x.product_type === selectedProduct).map((x) => x.bop)),
    )
  }, [imports, selectedProduct])
  const waferOptions = useMemo(() => {
    return Array.from(
      new Set(
        imports
          .filter(
            (x) =>
              (!selectedProduct || x.product_type === selectedProduct) &&
              (!selectedBop || x.bop === selectedBop),
          )
          .map((x) => x.wafer_pn),
      ),
    )
  }, [imports, selectedProduct, selectedBop])

  const latestByMachine = useMemo(() => {
    const filtered = imports.filter(
      (x) =>
        (!selectedProduct || x.product_type === selectedProduct) &&
        (!selectedBop || x.bop === selectedBop) &&
        (!selectedWafer || x.wafer_pn === selectedWafer),
    )
    const map = new Map<string, ImportRecord>()
    filtered.forEach((item) => {
      const existing = map.get(item.machine_id)
      if (!existing || (item.import_datetime ?? '') > (existing.import_datetime ?? '')) {
        map.set(item.machine_id, item)
      }
    })
    return Array.from(map.values()).sort((a, b) => a.machine_id.localeCompare(b.machine_id))
  }, [imports, selectedProduct, selectedBop, selectedWafer])

  const compareAllMachines = () => {
    setSelectedIds(latestByMachine.map((x) => x.id))
  }

  const submitCompare = async () => {
    if (selectedIds.length < 2) {
      return
    }
    setLoading(true)
    setError(null)
    try {
      const response = await api.post<ApiResponse<ComparePayload>>('/compare', {
        import_ids: selectedIds,
        file_type: null,
        show_all: showAll,
      })
      setResult(response.data.data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Compare request failed.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="page">
      <header className="page-header">
        <h2>Cross-Machine Compare</h2>
        <p>Select product context, pick machines, and inspect parameter diffs.</p>
      </header>

      <div className="panel controls">
        <select value={selectedProduct} onChange={(e) => setSelectedProduct(e.target.value)}>
          <option value="">Product Type</option>
          {productOptions.map((value) => (
            <option key={value} value={value}>
              {value}
            </option>
          ))}
        </select>
        <select value={selectedBop} onChange={(e) => setSelectedBop(e.target.value)}>
          <option value="">BOP</option>
          {bopOptions.map((value) => (
            <option key={value} value={value}>
              {value}
            </option>
          ))}
        </select>
        <select value={selectedWafer} onChange={(e) => setSelectedWafer(e.target.value)}>
          <option value="">Wafer PN</option>
          {waferOptions.map((value) => (
            <option key={value} value={value}>
              {value}
            </option>
          ))}
        </select>
        <input value={fileType} onChange={(e) => setFileType(e.target.value)} placeholder="filter by file_type or param_name" />
        <label style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <input type="checkbox" checked={showAll} onChange={(e) => setShowAll(e.target.checked)} />
          Show all params
        </label>
      </div>

      <div className="panel">
        <div style={{ display: 'flex', gap: 8, marginBottom: 10 }}>
          <button onClick={compareAllMachines}>Compare all machines</button>
          <button className="primary" disabled={selectedIds.length < 2 || loading} onClick={submitCompare}>
            {loading ? 'Comparing...' : 'Compare selected'}
          </button>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th />
                <th>Machine</th>
                <th>Product Type</th>
                <th>BOP</th>
                <th>Wafer PN</th>
                <th>Recipe Time</th>
              </tr>
            </thead>
            <tbody>
              {latestByMachine.map((item) => (
                <tr key={item.id}>
                  <td>
                    <input
                      type="checkbox"
                      checked={selectedIds.includes(item.id)}
                      onChange={(e) =>
                        setSelectedIds((prev) =>
                          e.target.checked ? Array.from(new Set([...prev, item.id])) : prev.filter((id) => id !== item.id),
                        )
                      }
                    />
                  </td>
                  <td>{item.machine_id}</td>
                  <td>{item.product_type}</td>
                  <td>{item.bop}</td>
                  <td>{item.wafer_pn}</td>
                  <td className="mono">{item.recipe_datetime}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {error ? <p className="error-msg">{error}</p> : null}

      {result ? (() => {
        const idToLabel = Object.fromEntries(result.imports.map((imp) => [String(imp.id), imp.machine_id]))
        const diffCount = (rows: { is_diff: boolean }[]) => rows.filter((r) => r.is_diff).length
        const sections: Array<{ title: string; count: number; content: React.ReactNode }> = [
          {
            title: 'Parameter Diff',
            count: diffCount(filteredParams),
            content: <GroupedDiffTable rows={filteredParams} importIds={selectedIds} idToLabel={idToLabel} />,
          },
          {
            title: 'APP Diff',
            count: diffCount(result.app_spec),
            content: <DiffTable rows={result.app_spec} importIds={selectedIds} idToLabel={idToLabel} />,
          },
          {
            title: 'BSG Diff',
            count: diffCount(result.bsg),
            content: <DiffTable rows={result.bsg} importIds={selectedIds} idToLabel={idToLabel} />,
          },
          {
            title: 'RPM Limits Diff',
            count: diffCount(result.rpm_limits),
            content: <DiffTable rows={result.rpm_limits} importIds={selectedIds} idToLabel={idToLabel} />,
          },
          {
            title: 'RPM Reference Diff',
            count: diffCount(result.rpm_reference),
            content: <DiffTable rows={result.rpm_reference} importIds={selectedIds} idToLabel={idToLabel} />,
          },
        ]
        return (
          <div style={{ display: 'grid', gap: 10 }}>
            {sections.map((section) => (
              <details key={section.title} className="result-section" open={section.count > 0}>
                <summary>
                  <span>{section.title}</span>
                  <span className="grouped-count">{section.count} diff</span>
                </summary>
                <div className="result-section-body">{section.content}</div>
              </details>
            ))}
          </div>
        )
      })() : null}
    </section>
  )
}
