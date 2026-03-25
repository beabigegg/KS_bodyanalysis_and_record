import { useEffect, useMemo, useState } from 'react'
import { useParams } from 'react-router-dom'
import { api, type ApiResponse } from '../lib/api'
import { downloadCsv } from '../lib/csv'
import { ObjectTable } from '../components/ObjectTable'
import type { ImportDetailSummary, ParamFacets, ParamPage, ParamRow } from '../types'

type RpmData = {
  limits: Array<Record<string, unknown>>
  reference: Array<Record<string, unknown>>
}

const detailTabs = ['PARAMS', 'APP', 'BSG', 'RPM'] as const

function toParamTableRows(rows: ParamRow[]) {
  return rows.map((row) => ({
    file_type: row.file_type,
    param_group: row.param_group ?? '',
    stage: row.stage ?? '',
    category: row.category ?? '',
    param_name: row.param_name,
    param_value: row.param_value ?? '',
    unit: row.unit ?? '',
    min_value: row.min_value ?? '',
    max_value: row.max_value ?? '',
    default_value: row.default_value ?? '',
  }))
}

export function ImportDetailPage() {
  const { importId } = useParams<{ importId: string }>()
  const [activeTab, setActiveTab] = useState<(typeof detailTabs)[number]>('PARAMS')
  const [summary, setSummary] = useState<ImportDetailSummary | null>(null)
  const [facets, setFacets] = useState<ParamFacets | null>(null)
  const [selectedFileType, setSelectedFileType] = useState('')
  const [selectedParamGroup, setSelectedParamGroup] = useState('')
  const [selectedStage, setSelectedStage] = useState('')
  const [selectedCategory, setSelectedCategory] = useState('')
  const [paramSearch, setParamSearch] = useState('')
  const [paramsPage, setParamsPage] = useState<ParamPage | null>(null)
  const [paramsTotal, setParamsTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [appSpec, setAppSpec] = useState<Record<string, unknown> | null | undefined>(undefined)
  const [bsg, setBsg] = useState<Record<string, Array<Record<string, unknown>>> | undefined>(undefined)
  const [rpm, setRpm] = useState<RpmData | undefined>(undefined)
  const [summaryLoading, setSummaryLoading] = useState(false)
  const [paramsLoading, setParamsLoading] = useState(false)
  const [sectionLoading, setSectionLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!importId) {
      return
    }

    setSummaryLoading(true)
    setError('')
    setSummary(null)
    setFacets(null)
    setParamsPage(null)
    setParamsTotal(0)
    setSelectedFileType('')
    setSelectedParamGroup('')
    setSelectedStage('')
    setSelectedCategory('')
    setParamSearch('')
    setPage(1)
    setAppSpec(undefined)
    setBsg(undefined)
    setRpm(undefined)

    void (async () => {
      try {
        const [summaryRes, facetsRes] = await Promise.all([
          api.get<ApiResponse<ImportDetailSummary>>(`/imports/${importId}/summary`),
          api.get<ApiResponse<ParamFacets>>(`/imports/${importId}/param-facets`),
        ])
        setSummary(summaryRes.data.data)
        setFacets(facetsRes.data.data)
        setSelectedFileType(facetsRes.data.data.file_types[0]?.value ?? '')
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : 'Failed to load import detail')
      } finally {
        setSummaryLoading(false)
      }
    })()
  }, [importId])

  useEffect(() => {
    if (!importId || activeTab !== 'PARAMS' || !facets) {
      return
    }

    setParamsLoading(true)
    setError('')
    void (async () => {
      try {
        const response = await api.get<ApiResponse<ParamPage>>(`/imports/${importId}/params`, {
          params: {
            file_type: selectedFileType || undefined,
            param_group: selectedParamGroup || undefined,
            stage: selectedStage || undefined,
            category: selectedCategory || undefined,
            search: paramSearch || undefined,
            page,
            page_size: 100,
          },
        })
        setParamsPage(response.data.data)
        setParamsTotal(response.data.total)
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : 'Failed to load parameter rows')
      } finally {
        setParamsLoading(false)
      }
    })()
  }, [
    activeTab,
    facets,
    importId,
    page,
    paramSearch,
    selectedCategory,
    selectedFileType,
    selectedParamGroup,
    selectedStage,
  ])

  useEffect(() => {
    if (!importId || activeTab === 'PARAMS') {
      return
    }

    if (activeTab === 'APP' && appSpec !== undefined) {
      return
    }
    if (activeTab === 'BSG' && bsg !== undefined) {
      return
    }
    if (activeTab === 'RPM' && rpm !== undefined) {
      return
    }

    setSectionLoading(true)
    setError('')
    void (async () => {
      try {
        if (activeTab === 'APP') {
          const response = await api.get<ApiResponse<Record<string, unknown> | null>>(
            `/imports/${importId}/app-spec`,
          )
          setAppSpec(response.data.data)
        } else if (activeTab === 'BSG') {
          const response = await api.get<ApiResponse<Record<string, Array<Record<string, unknown>>>>>(
            `/imports/${importId}/bsg`,
          )
          setBsg(response.data.data)
        } else if (activeTab === 'RPM') {
          const response = await api.get<ApiResponse<RpmData>>(`/imports/${importId}/rpm`)
          setRpm(response.data.data)
        }
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : `Failed to load ${activeTab} detail`)
      } finally {
        setSectionLoading(false)
      }
    })()
  }, [activeTab, appSpec, bsg, importId, rpm])

  const fileTypes = facets?.file_types ?? []
  const fileTypeGroups = facets?.param_groups_by_file_type[selectedFileType] ?? []
  const fileTypeStages = facets?.stages_by_file_type[selectedFileType] ?? []
  const fileTypeCategories = facets?.categories_by_file_type[selectedFileType] ?? []
  const paramRows = useMemo(() => toParamTableRows(paramsPage?.rows ?? []), [paramsPage])

  const resetParamFilters = () => {
    setSelectedParamGroup('')
    setSelectedStage('')
    setSelectedCategory('')
    setParamSearch('')
    setPage(1)
  }

  const exportParamsCsv = async () => {
    if (!importId) {
      return
    }

    const rows: ParamRow[] = []
    let exportPage = 1
    let totalPages = 1
    do {
      const response = await api.get<ApiResponse<ParamPage>>(`/imports/${importId}/params`, {
        params: {
          file_type: selectedFileType || undefined,
          param_group: selectedParamGroup || undefined,
          stage: selectedStage || undefined,
          category: selectedCategory || undefined,
          search: paramSearch || undefined,
          page: exportPage,
          page_size: 500,
        },
      })
      rows.push(...response.data.data.rows)
      totalPages = response.data.data.total_pages
      exportPage += 1
    } while (exportPage <= totalPages)

    downloadCsv(
      `import_${importId}_${selectedFileType || 'params'}.csv`,
      toParamTableRows(rows),
    )
  }

  return (
    <section className="page">
      <header className="page-header">
        <h2>Import Detail #{importId}</h2>
        <p>Summary-first recipe browsing with incremental loading by section.</p>
      </header>

      {summaryLoading ? <p className="empty">Loading import detail...</p> : null}
      {error ? <p className="error-msg">{error}</p> : null}

      {summary ? (
        <div className="panel">
          <div className="summary-grid">
            <article className="summary-card">
              <span className="summary-label">Browsable Params</span>
              <strong>{summary.params_total}</strong>
            </article>
            <article className="summary-card">
              <span className="summary-label">File Types</span>
              <strong>{summary.file_types.length}</strong>
            </article>
            <article className="summary-card">
              <span className="summary-label">APP Spec</span>
              <strong>{summary.sections.has_app_spec ? 'Yes' : 'No'}</strong>
            </article>
            <article className="summary-card">
              <span className="summary-label">BSG Rows</span>
              <strong>{summary.sections.bsg_rows}</strong>
            </article>
            <article className="summary-card">
              <span className="summary-label">RPM Limits</span>
              <strong>{summary.sections.rpm_limits}</strong>
            </article>
            <article className="summary-card">
              <span className="summary-label">RPM Reference</span>
              <strong>{summary.sections.rpm_reference}</strong>
            </article>
          </div>
        </div>
      ) : null}

      <div className="panel tabs">
        {detailTabs.map((tab) => (
          <button key={tab} className={activeTab === tab ? 'active' : ''} onClick={() => setActiveTab(tab)}>
            {tab}
          </button>
        ))}
      </div>

      {activeTab === 'PARAMS' ? (
        <>
          <div className="panel">
            <div className="section-heading">
              <div>
                <h3>File Type Overview</h3>
                <p>Start from a file type, then narrow by semantic group instead of scanning the full recipe.</p>
              </div>
              <span className="summary-inline">Filtered rows: {paramsTotal}</span>
            </div>
            <div className="chip-grid">
              {fileTypes.map((option) => (
                <button
                  key={option.value}
                  className={`filter-chip${selectedFileType === option.value ? ' active' : ''}`}
                  onClick={() => {
                    setSelectedFileType(option.value)
                    setSelectedParamGroup('')
                    setSelectedStage('')
                    setSelectedCategory('')
                    setPage(1)
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
              <select
                value={selectedFileType}
                onChange={(e) => {
                  setSelectedFileType(e.target.value)
                  setSelectedParamGroup('')
                  setSelectedStage('')
                  setSelectedCategory('')
                  setPage(1)
                }}
              >
                {fileTypes.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.value} ({option.count})
                  </option>
                ))}
              </select>
              <select
                value={selectedParamGroup}
                onChange={(e) => {
                  setSelectedParamGroup(e.target.value)
                  setPage(1)
                }}
              >
                <option value="">All groups</option>
                {fileTypeGroups.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.value} ({option.count})
                  </option>
                ))}
              </select>
              <select
                value={selectedStage}
                onChange={(e) => {
                  setSelectedStage(e.target.value)
                  setPage(1)
                }}
              >
                <option value="">All stages</option>
                {fileTypeStages.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.value} ({option.count})
                  </option>
                ))}
              </select>
              <select
                value={selectedCategory}
                onChange={(e) => {
                  setSelectedCategory(e.target.value)
                  setPage(1)
                }}
              >
                <option value="">All categories</option>
                {fileTypeCategories.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.value} ({option.count})
                  </option>
                ))}
              </select>
              <input
                value={paramSearch}
                onChange={(e) => {
                  setParamSearch(e.target.value)
                  setPage(1)
                }}
                placeholder="Search parameter name"
              />
              <button onClick={resetParamFilters}>Reset filters</button>
              <button className="primary" onClick={() => void exportParamsCsv()}>
                Export filtered CSV
              </button>
            </div>
            {paramsLoading ? <p className="empty">Loading parameter rows...</p> : null}
            <ObjectTable rows={paramRows} />
          </div>

          <div className="panel pagination-row">
            <button disabled={page <= 1} onClick={() => setPage((prev) => Math.max(1, prev - 1))}>
              Prev
            </button>
            <span>
              Page {paramsPage?.page ?? page} / {paramsPage?.total_pages ?? 1}
            </span>
            <button
              disabled={page >= (paramsPage?.total_pages ?? 1)}
              onClick={() => setPage((prev) => Math.min(paramsPage?.total_pages ?? 1, prev + 1))}
            >
              Next
            </button>
            <span style={{ marginLeft: 'auto' }}>
              Showing {paramsPage?.rows.length ?? 0} of {paramsTotal}
            </span>
          </div>
        </>
      ) : null}

      {activeTab === 'APP' ? (
        <div className="panel">
          {sectionLoading && appSpec === undefined ? <p className="empty">Loading APP detail...</p> : null}
          <ObjectTable rows={appSpec ? [appSpec] : []} />
        </div>
      ) : null}

      {activeTab === 'BSG' ? (
        <div className="panel">
          {sectionLoading && bsg === undefined ? <p className="empty">Loading BSG detail...</p> : null}
          {Object.entries(bsg ?? {}).length === 0 ? <p className="empty">No BSG rows.</p> : null}
          {Object.entries(bsg ?? {}).map(([group, rows]) => (
            <div key={group} style={{ marginBottom: 12 }}>
              <h3 style={{ marginBottom: 6 }}>Ball Group {group}</h3>
              <ObjectTable rows={rows} />
            </div>
          ))}
        </div>
      ) : null}

      {activeTab === 'RPM' ? (
        <div className="panel split-2">
          {sectionLoading && rpm === undefined ? <p className="empty">Loading RPM detail...</p> : null}
          <div>
            <h3 style={{ marginTop: 0 }}>RPM Limits</h3>
            <ObjectTable rows={rpm?.limits ?? []} />
          </div>
          <div>
            <h3 style={{ marginTop: 0 }}>RPM Reference</h3>
            <ObjectTable rows={rpm?.reference ?? []} />
          </div>
        </div>
      ) : null}
    </section>
  )
}
