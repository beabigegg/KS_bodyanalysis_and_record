import { useEffect, useMemo, useState } from 'react'
import { api, type ApiResponse } from '../lib/api'
import type { ComparePayload, ImportRecord } from '../types'
import { DiffTable } from '../components/DiffTable'
import { GroupedDiffTable } from '../components/GroupedDiffTable'

const compareSections = [
  { key: 'params', label: 'Parameter Diff' },
  { key: 'app_spec', label: 'APP Diff' },
  { key: 'bsg', label: 'BSG Diff' },
  { key: 'rpm_limits', label: 'RPM Limits Diff' },
  { key: 'rpm_reference', label: 'RPM Reference Diff' },
] as const

type CompareSection = (typeof compareSections)[number]['key']

export function ComparePage() {
  const [imports, setImports] = useState<ImportRecord[]>([])
  const [selectedProduct, setSelectedProduct] = useState('')
  const [selectedBop, setSelectedBop] = useState('')
  const [selectedWafer, setSelectedWafer] = useState('')
  const [selectedIds, setSelectedIds] = useState<number[]>([])
  const [fileType, setFileType] = useState('')
  const [showAll, setShowAll] = useState(false)
  const [activeSection, setActiveSection] = useState<CompareSection>('params')
  const [page, setPage] = useState(1)
  const [result, setResult] = useState<ComparePayload | null>(null)
  const [submittedIds, setSubmittedIds] = useState<number[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    void (async () => {
      try {
        let allImports: ImportRecord[] = []
        let nextPage = 1
        const pageSize = 200
        let hasMore = true
        while (hasMore) {
          const response = await api.get<ApiResponse<ImportRecord[]>>('/imports', {
            params: { page: nextPage, page_size: pageSize },
          })
          allImports = allImports.concat(response.data.data)
          hasMore = allImports.length < response.data.total
          nextPage += 1
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

  const fetchCompareSection = async (importIds: number[], section: CompareSection, nextPage: number) => {
    if (importIds.length < 2) {
      return
    }
    setLoading(true)
    setError(null)
    try {
      const response = await api.post<ApiResponse<ComparePayload>>('/compare', {
        import_ids: importIds,
        section,
        file_type: section === 'params' && fileType ? fileType : null,
        show_all: showAll,
        page: nextPage,
        page_size: section === 'params' ? 200 : 100,
      })
      setResult(response.data.data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Compare request failed.')
    } finally {
      setLoading(false)
    }
  }

  const submitCompare = async () => {
    if (selectedIds.length < 2) {
      return
    }
    setSubmittedIds(selectedIds)
    setPage(1)
    await fetchCompareSection(selectedIds, activeSection, 1)
  }

  useEffect(() => {
    if (submittedIds.length < 2) {
      return
    }
    void fetchCompareSection(submittedIds, activeSection, page)
  }, [activeSection, page])

  const currentImportIds = submittedIds.length >= 2 ? submittedIds : selectedIds
  const idToLabel = useMemo(
    () => Object.fromEntries((result?.imports ?? []).map((imp) => [String(imp.id), imp.machine_id])),
    [result],
  )

  const currentSectionLabel =
    compareSections.find((section) => section.key === activeSection)?.label ?? 'Compare Result'

  return (
    <section className="page">
      <header className="page-header">
        <h2>Cross-Machine Compare</h2>
        <p>Browse one diff section at a time so large compares stay responsive.</p>
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
        <input
          value={fileType}
          onChange={(e) => setFileType(e.target.value)}
          placeholder="filter by file_type"
          disabled={activeSection !== 'params'}
        />
        <label style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <input type="checkbox" checked={showAll} onChange={(e) => setShowAll(e.target.checked)} />
          Show all params
        </label>
      </div>

      <div className="panel">
        <div style={{ display: 'flex', gap: 8, marginBottom: 10, flexWrap: 'wrap' }}>
          <button onClick={compareAllMachines}>Compare all machines</button>
          <button className="primary" disabled={selectedIds.length < 2 || loading} onClick={() => void submitCompare()}>
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

      {submittedIds.length >= 2 ? (
        <div className="panel tabs">
          {compareSections.map((section) => (
            <button
              key={section.key}
              className={activeSection === section.key ? 'active' : ''}
              onClick={() => {
                setActiveSection(section.key)
                setPage(1)
              }}
            >
              {section.label}
            </button>
          ))}
        </div>
      ) : null}

      {error ? <p className="error-msg">{error}</p> : null}

      {result ? (
        <>
          <div className="panel">
            <div className="section-heading">
              <div>
                <h3>{currentSectionLabel}</h3>
                <p>
                  Showing page {result.page} / {result.total_pages} for {result.total_rows} rows.
                </p>
              </div>
              <span className="summary-inline">
                Compared machines: {currentImportIds.length}
              </span>
            </div>
            {activeSection === 'params' ? (
              <GroupedDiffTable
                rows={result.rows}
                importIds={currentImportIds}
                idToLabel={idToLabel}
                wireGroupContext={result.wire_group_context}
              />
            ) : (
              <DiffTable rows={result.rows} importIds={currentImportIds} idToLabel={idToLabel} />
            )}
          </div>

          <div className="panel pagination-row">
            <button disabled={page <= 1 || loading} onClick={() => setPage((prev) => Math.max(1, prev - 1))}>
              Prev
            </button>
            <span>
              Page {result.page} / {result.total_pages}
            </span>
            <button
              disabled={page >= result.total_pages || loading}
              onClick={() => setPage((prev) => Math.min(result.total_pages, prev + 1))}
            >
              Next
            </button>
            <span style={{ marginLeft: 'auto' }}>Rows: {result.total_rows}</span>
          </div>
        </>
      ) : null}
    </section>
  )
}
