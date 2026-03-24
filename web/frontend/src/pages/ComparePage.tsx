import { useEffect, useMemo, useState } from 'react'
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
  const [loading, setLoading] = useState(false)

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
      } catch {
        // silent
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
    try {
      const response = await api.post<ApiResponse<ComparePayload>>('/compare', {
        import_ids: selectedIds,
        file_type: fileType || null,
        show_all: showAll,
      })
      setResult(response.data.data)
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
        <input value={fileType} onChange={(e) => setFileType(e.target.value)} placeholder="file_type (optional)" />
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
                <th>Import ID</th>
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
                  <td>{item.id}</td>
                  <td className="mono">{item.recipe_datetime}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {result ? (
        <div className="panel">
          <h3 style={{ marginTop: 0 }}>Parameter Diff</h3>
          <GroupedDiffTable rows={result.params} importIds={selectedIds} />
          <h3>APP Diff</h3>
          <DiffTable rows={result.app_spec} importIds={selectedIds} />
          <h3>BSG Diff</h3>
          <DiffTable rows={result.bsg} importIds={selectedIds} />
          <h3>RPM Limits Diff</h3>
          <DiffTable rows={result.rpm_limits} importIds={selectedIds} />
          <h3>RPM Reference Diff</h3>
          <DiffTable rows={result.rpm_reference} importIds={selectedIds} />
        </div>
      ) : null}
    </section>
  )
}
