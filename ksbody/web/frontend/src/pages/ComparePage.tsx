import { useEffect, useMemo, useState } from 'react'
import { api, type ApiResponse } from '../lib/api'
import { getHiddenClassificationKeys } from '../lib/classificationKeys'
import { displayParamName } from '../lib/paramName'
import { formatParamGroupLabel } from '../lib/paramBrowse'
import type {
  CompareCatalogPayload,
  CompareParamKey,
  ComparePayload,
  ImportRecord,
} from '../types'
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
type ComparePhase = 'imports' | 'params' | 'results'

function paramKey(fileType: string, paramName: string): string {
  return `${fileType}::${paramName}`
}

function parseParamKey(key: string): CompareParamKey {
  const idx = key.indexOf('::')
  if (idx < 0) {
    return { file_type: '', param_name: key }
  }
  return {
    file_type: key.slice(0, idx),
    param_name: key.slice(idx + 2),
  }
}

export function ComparePage() {
  const [imports, setImports] = useState<ImportRecord[]>([])
  const [selectedProduct, setSelectedProduct] = useState('')
  const [selectedBop, setSelectedBop] = useState('')
  const [selectedWafer, setSelectedWafer] = useState('')
  const [selectedIds, setSelectedIds] = useState<number[]>([])

  const [phase, setPhase] = useState<ComparePhase>('imports')
  const [lockedImportIds, setLockedImportIds] = useState<number[]>([])

  const [catalog, setCatalog] = useState<CompareCatalogPayload | null>(null)
  const [catalogPage, setCatalogPage] = useState(1)
  const [catalogFileType, setCatalogFileType] = useState('')
  const [catalogParamGroup, setCatalogParamGroup] = useState('')
  const [catalogProcessStep, setCatalogProcessStep] = useState('')
  const [catalogSearch, setCatalogSearch] = useState('')
  const [selectedParamKeys, setSelectedParamKeys] = useState<Set<string>>(new Set())

  const [activeSection, setActiveSection] = useState<CompareSection>('params')
  const [compareFileType, setCompareFileType] = useState('')
  const [showAll, setShowAll] = useState(false)
  const [page, setPage] = useState(1)
  const [result, setResult] = useState<ComparePayload | null>(null)

  const [loadingImports, setLoadingImports] = useState(false)
  const [loadingCatalog, setLoadingCatalog] = useState(false)
  const [loadingCompare, setLoadingCompare] = useState(false)
  const [selectingAllFiltered, setSelectingAllFiltered] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    void (async () => {
      setLoadingImports(true)
      setError(null)
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
      } finally {
        setLoadingImports(false)
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

  const selectedIdsKey = useMemo(
    () => [...selectedIds].sort((left, right) => left - right).join(','),
    [selectedIds],
  )
  const lockedIdsKey = useMemo(
    () => [...lockedImportIds].sort((left, right) => left - right).join(','),
    [lockedImportIds],
  )
  const selectedParamKeysKey = useMemo(
    () => Array.from(selectedParamKeys).sort((left, right) => left.localeCompare(right)).join('|'),
    [selectedParamKeys],
  )
  const selectedParamsPayload = useMemo(
    () => Array.from(selectedParamKeys).map((key) => parseParamKey(key)),
    [selectedParamKeys],
  )

  useEffect(() => {
    if (lockedImportIds.length === 0) {
      return
    }
    if (selectedIdsKey === lockedIdsKey) {
      return
    }
    setLockedImportIds([])
    setSelectedParamKeys(new Set())
    setCatalog(null)
    setResult(null)
    setPage(1)
    setCatalogPage(1)
    setPhase('imports')
  }, [lockedIdsKey, lockedImportIds.length, selectedIdsKey])

  useEffect(() => {
    if (phase !== 'params' || lockedImportIds.length < 2) {
      return
    }
    void (async () => {
      setLoadingCatalog(true)
      setError(null)
      try {
        const response = await api.post<ApiResponse<CompareCatalogPayload>>('/compare/params/catalog', {
          import_ids: lockedImportIds,
          file_type: catalogFileType || null,
          param_group: catalogParamGroup || null,
          process_step: catalogProcessStep || null,
          search: catalogSearch || null,
          page: catalogPage,
          page_size: 100,
        })
        setCatalog(response.data.data)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load compare parameter catalog.')
      } finally {
        setLoadingCatalog(false)
      }
    })()
  }, [
    phase,
    lockedIdsKey,
    lockedImportIds,
    catalogFileType,
    catalogParamGroup,
    catalogProcessStep,
    catalogSearch,
    catalogPage,
  ])

  useEffect(() => {
    if (!catalog || !catalogFileType) {
      return
    }
    const fileTypeExists = catalog.facets.file_types.some((entry) => entry.value === catalogFileType)
    if (!fileTypeExists) {
      setCatalogFileType('')
      setCatalogParamGroup('')
      setCatalogProcessStep('')
      setCatalogPage(1)
    }
  }, [catalog, catalogFileType])

  useEffect(() => {
    if (phase !== 'results' || lockedImportIds.length < 2) {
      return
    }
    void (async () => {
      setLoadingCompare(true)
      setError(null)
      try {
        const response = await api.post<ApiResponse<ComparePayload>>('/compare', {
          import_ids: lockedImportIds,
          section: activeSection,
          file_type: activeSection === 'params' && compareFileType ? compareFileType : null,
          selected_params: selectedParamsPayload,
          show_all: showAll,
          page,
          page_size: activeSection === 'params' ? 200 : 100,
        })
        setResult(response.data.data)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Compare request failed.')
      } finally {
        setLoadingCompare(false)
      }
    })()
  }, [
    phase,
    lockedIdsKey,
    lockedImportIds,
    activeSection,
    compareFileType,
    showAll,
    page,
    selectedParamKeysKey,
    selectedParamsPayload,
  ])

  const compareAllMachines = () => {
    setSelectedIds(latestByMachine.map((x) => x.id))
  }

  const beginParameterSelection = () => {
    if (selectedIds.length < 2) {
      return
    }
    setLockedImportIds([...selectedIds].sort((left, right) => left - right))
    setSelectedParamKeys(new Set())
    setCatalog(null)
    setCatalogPage(1)
    setCatalogFileType('')
    setCatalogParamGroup('')
    setCatalogProcessStep('')
    setCatalogSearch('')
    setResult(null)
    setPhase('params')
  }

  const runCompare = () => {
    if (selectedParamKeys.size === 0 || lockedImportIds.length < 2) {
      return
    }
    setActiveSection('params')
    setPage(1)
    setResult(null)
    setPhase('results')
  }

  const selectAllFilteredParams = async () => {
    if (lockedImportIds.length < 2) {
      return
    }
    setSelectingAllFiltered(true)
    setError(null)
    try {
      const keys = new Set<string>()
      let nextPage = 1
      let totalPages = 1
      do {
        const response = await api.post<ApiResponse<CompareCatalogPayload>>('/compare/params/catalog', {
          import_ids: lockedImportIds,
          file_type: catalogFileType || null,
          param_group: catalogParamGroup || null,
          process_step: catalogProcessStep || null,
          search: catalogSearch || null,
          page: nextPage,
          page_size: 500,
        })
        const data = response.data.data
        for (const row of data.rows) {
          keys.add(paramKey(row.file_type, row.param_name))
        }
        totalPages = data.total_pages
        nextPage += 1
      } while (nextPage <= totalPages)
      setSelectedParamKeys(keys)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to select all filtered parameters.')
    } finally {
      setSelectingAllFiltered(false)
    }
  }

  const idToLabel = useMemo(
    () => Object.fromEntries((result?.imports ?? []).map((imp) => [String(imp.id), imp.machine_id])),
    [result],
  )

  const currentSectionLabel =
    compareSections.find((section) => section.key === activeSection)?.label ?? 'Compare Result'

  const facetGroupOptions = useMemo(
    () => (catalogFileType ? catalog?.facets.param_groups_by_file_type[catalogFileType] ?? [] : []),
    [catalog, catalogFileType],
  )
  const facetProcessStepOptions = useMemo(
    () => (catalogFileType ? catalog?.facets.process_steps_by_file_type[catalogFileType] ?? [] : []),
    [catalog, catalogFileType],
  )
  const supportsProcessFilters = catalogFileType === 'PRM'
  const hiddenClassification = useMemo(
    () => getHiddenClassificationKeys(catalogFileType || ''),
    [catalogFileType],
  )

  return (
    <section className="page">
      <header className="page-header">
        <h2>Cross-Machine Compare</h2>
        <p>Select imports, choose parameter scope, then compare with section tabs.</p>
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
      </div>

      <div className="panel">
        <div style={{ display: 'flex', gap: 8, marginBottom: 10, flexWrap: 'wrap' }}>
          <button onClick={compareAllMachines} disabled={loadingImports}>
            Compare all machines
          </button>
          <button className="primary" disabled={selectedIds.length < 2 || loadingImports} onClick={beginParameterSelection}>
            Next: Select parameters
          </button>
          <span className="summary-inline" style={{ marginLeft: 'auto' }}>
            Selected imports: {selectedIds.length}
          </span>
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

      {phase === 'params' ? (
        <>
          <div className="panel">
            <div className="section-heading">
              <div>
                <h3>Parameter Selection</h3>
                <p>Start from file type, then narrow by semantic filters to choose compare scope.</p>
              </div>
              <span className="summary-inline">Selected parameters: {selectedParamKeys.size}</span>
            </div>
            <div className="chip-grid">
              {(catalog?.facets.file_types ?? []).map((option) => (
                <button
                  key={option.value}
                  className={`filter-chip${catalogFileType === option.value ? ' active' : ''}`}
                  onClick={() => {
                    setCatalogFileType(option.value)
                    setCatalogParamGroup('')
                    setCatalogProcessStep('')
                    setCatalogPage(1)
                  }}
                >
                  <span>{option.value}</span>
                  <strong>{option.count}</strong>
                </button>
              ))}
            </div>
          </div>

          <div className="panel">
            <div className="controls" style={{ marginBottom: 10 }}>
              {supportsProcessFilters ? (
                <select
                  value={catalogProcessStep}
                  onChange={(e) => {
                    setCatalogProcessStep(e.target.value)
                    setCatalogPage(1)
                  }}
                >
                  <option value="">All process steps</option>
                  {facetProcessStepOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.value} ({option.count})
                    </option>
                  ))}
                </select>
              ) : null}
              <select
                value={catalogParamGroup}
                onChange={(e) => {
                  setCatalogParamGroup(e.target.value)
                  setCatalogPage(1)
                }}
              >
                <option value="">All groups</option>
                {facetGroupOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {formatParamGroupLabel(option.value)} ({option.count})
                  </option>
                ))}
              </select>
              <input
                value={catalogSearch}
                onChange={(e) => {
                  setCatalogSearch(e.target.value)
                  setCatalogPage(1)
                }}
                placeholder="Search parameter name"
              />
              <button
                onClick={() => {
                  setCatalogParamGroup('')
                  setCatalogProcessStep('')
                  setCatalogSearch('')
                  setCatalogPage(1)
                }}
              >
                Reset filters
              </button>
              <button className="primary" disabled={selectingAllFiltered || loadingCatalog} onClick={() => void selectAllFilteredParams()}>
                {selectingAllFiltered ? 'Selecting all...' : 'Select all filtered'}
              </button>
              <button
                disabled={selectingAllFiltered}
                onClick={() => {
                  setSelectedParamKeys(new Set())
                }}
              >
                Clear selected
              </button>
            </div>

            {loadingCatalog ? <p className="empty">Loading parameter catalog...</p> : null}
            {catalog ? (
              <>
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th />
                        <th>file_type</th>
                        {!hiddenClassification.has('process_step') ? <th>process_step</th> : null}
                        {!hiddenClassification.has('param_group') ? <th>param_group</th> : null}
                        <th>param_name</th>
                        <th>present</th>
                        <th>missing</th>
                      </tr>
                    </thead>
                    <tbody>
                      {catalog.rows.map((row) => {
                        const key = paramKey(row.file_type, row.param_name)
                        return (
                          <tr key={key}>
                            <td>
                              <input
                                type="checkbox"
                                checked={selectedParamKeys.has(key)}
                                onChange={(e) =>
                                  setSelectedParamKeys((prev) => {
                                    const next = new Set(prev)
                                    if (e.target.checked) {
                                      next.add(key)
                                    } else {
                                      next.delete(key)
                                    }
                                    return next
                                  })
                                }
                              />
                            </td>
                            <td>{row.file_type}</td>
                            {!hiddenClassification.has('process_step') ? <td>{row.process_step ?? ''}</td> : null}
                            {!hiddenClassification.has('param_group') ? (
                              <td>{row.param_group ? formatParamGroupLabel(row.param_group) : ''}</td>
                            ) : null}
                            <td>{displayParamName(row.param_name, row.file_type)}</td>
                            <td>{row.present_count}</td>
                            <td>{row.missing_count}</td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </div>
                <div className="pagination-row" style={{ marginTop: 10 }}>
                  <button
                    disabled={catalogPage <= 1 || loadingCatalog}
                    onClick={() => setCatalogPage((prev) => Math.max(1, prev - 1))}
                  >
                    Prev
                  </button>
                  <span>
                    Page {catalog.page} / {catalog.total_pages}
                  </span>
                  <button
                    disabled={catalogPage >= catalog.total_pages || loadingCatalog}
                    onClick={() => setCatalogPage((prev) => Math.min(catalog.total_pages, prev + 1))}
                  >
                    Next
                  </button>
                  <span style={{ marginLeft: 'auto' }}>Rows: {catalog.total_rows}</span>
                </div>
              </>
            ) : null}
          </div>

          <div className="panel pagination-row">
            <button
              onClick={() => {
                setPhase('imports')
              }}
            >
              Back to imports
            </button>
            <button className="primary" disabled={selectedParamKeys.size === 0} onClick={runCompare}>
              Compare selected parameters
            </button>
          </div>
        </>
      ) : null}

      {phase === 'results' ? (
        <>
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

          <div className="panel controls">
            <input
              value={compareFileType}
              onChange={(e) => {
                setCompareFileType(e.target.value)
                setPage(1)
              }}
              placeholder="filter by file_type"
              disabled={activeSection !== 'params'}
            />
            <label style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <input
                type="checkbox"
                checked={showAll}
                onChange={(e) => {
                  setShowAll(e.target.checked)
                  setPage(1)
                }}
              />
              Show all rows
            </label>
            <button
              onClick={() => {
                setPhase('params')
                setResult(null)
              }}
            >
              Back to parameter selection
            </button>
            <span className="summary-inline" style={{ marginLeft: 'auto' }}>
              Selected parameters: {selectedParamKeys.size}
            </span>
          </div>

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
                  <span className="summary-inline">Compared machines: {lockedImportIds.length}</span>
                </div>
                {activeSection === 'params' ? (
                  <GroupedDiffTable
                    rows={result.rows}
                    importIds={lockedImportIds}
                    idToLabel={idToLabel}
                    wireGroupContext={result.wire_group_context}
                  />
                ) : (
                  <DiffTable rows={result.rows} importIds={lockedImportIds} idToLabel={idToLabel} />
                )}
              </div>

              <div className="panel pagination-row">
                <button disabled={page <= 1 || loadingCompare} onClick={() => setPage((prev) => Math.max(1, prev - 1))}>
                  Prev
                </button>
                <span>
                  Page {result.page} / {result.total_pages}
                </span>
                <button
                  disabled={page >= result.total_pages || loadingCompare}
                  onClick={() => setPage((prev) => Math.min(result.total_pages, prev + 1))}
                >
                  Next
                </button>
                <span style={{ marginLeft: 'auto' }}>Rows: {result.total_rows}</span>
              </div>
            </>
          ) : loadingCompare ? (
            <div className="panel">
              <p className="empty">Loading compare results...</p>
            </div>
          ) : null}
        </>
      ) : null}

      {error ? <p className="error-msg">{error}</p> : null}
    </section>
  )
}
