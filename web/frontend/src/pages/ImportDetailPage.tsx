import { useEffect, useMemo, useState } from 'react'
import { useParams } from 'react-router-dom'
import { api, type ApiResponse } from '../lib/api'
import { downloadCsv } from '../lib/csv'
import { displayParamName, prmSegmentGroup } from '../lib/paramName'
import { ObjectTable } from '../components/ObjectTable'
import type { CountOption, ImportDetailSummary, ParamFacets, ParamRow } from '../types'

type RpmData = {
  limits: Array<Record<string, unknown>>
  reference: Array<Record<string, unknown>>
}

type SegmentSection = {
  label: string
  count: number
  rows: Array<Record<string, string | number>>
}

type SegmentPage = {
  sections: SegmentSection[]
  rowCount: number
}

type ParamFilterState = {
  paramGroup: string
  stage: string
  category: string
  family: string
  feature: string
  search: string
}

const detailTabs = ['PARAMS', 'APP', 'BSG', 'RPM'] as const
const PARAM_PAGE_SIZE = 100
const PRM_SEGMENT_PAGE_SIZE = 96

function formatParamGroupLabel(value: string) {
  const wireMatch = /^wire_(\d+)$/.exec(value)
  if (wireMatch) {
    return `Bond Group ${wireMatch[1]}`
  }
  if (value === 'parms') {
    return 'Param Group 1'
  }
  const parmsMatch = /^parms_(\d+)$/.exec(value)
  if (parmsMatch) {
    return `Param Group ${parmsMatch[1]}`
  }
  return value
}

function formatStageLabel(value: string) {
  if (value === 'bond1') return 'Bond1'
  if (value === 'bond2') return 'Bond2'
  if (value === 'bump') return 'Bump'
  if (value === 'bits_other') return 'BITS / Other'
  if (value === 'quick_adjust') return 'Quick Adjust'
  return value
}

function humanizeSemanticLabel(value: string) {
  return value
    .split('_')
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ')
}

function toParamTableRows(rows: ParamRow[]) {
  return rows.map((row) => ({
    file_type: row.file_type,
    param_group: row.param_group ? formatParamGroupLabel(row.param_group) : '',
    stage: row.stage ? formatStageLabel(row.stage) : '',
    category: row.category ? humanizeSemanticLabel(row.category) : '',
    family: row.family ? humanizeSemanticLabel(row.family) : '',
    feature: row.feature ? humanizeSemanticLabel(row.feature) : '',
    instance: row.instance ?? '',
    tunable: row.tunable == null ? '' : row.tunable ? 'Yes' : 'No',
    description: row.description ?? '',
    param_name: displayParamName(row.param_name, row.file_type),
    param_value: row.param_value ?? '',
    unit: row.unit ?? '',
    min_value: row.min_value ?? '',
    max_value: row.max_value ?? '',
    default_value: row.default_value ?? '',
  }))
}

function compareSegmentLabel(left: string, right: string) {
  if (left === right) {
    return 0
  }
  if (left === 'General') {
    return 1
  }
  if (right === 'General') {
    return -1
  }
  const leftMatch = /^Seg (\d+)$/i.exec(left)
  const rightMatch = /^Seg (\d+)$/i.exec(right)
  if (leftMatch && rightMatch) {
    return Number(leftMatch[1]) - Number(rightMatch[1])
  }
  return left.localeCompare(right)
}

function matchesSearch(row: ParamRow, search: string) {
  if (!search.trim()) {
    return true
  }
  const term = search.trim().toLowerCase()
  return displayParamName(row.param_name, row.file_type).toLowerCase().includes(term)
}

function matchesFilters(row: ParamRow, filters: ParamFilterState, skip?: keyof ParamFilterState) {
  if (skip !== 'paramGroup' && filters.paramGroup && row.param_group !== filters.paramGroup) {
    return false
  }
  if (skip !== 'family' && filters.family && row.family !== filters.family) {
    return false
  }
  if (skip !== 'feature' && filters.feature && row.feature !== filters.feature) {
    return false
  }
  if (skip !== 'stage' && filters.stage && row.stage !== filters.stage) {
    return false
  }
  if (skip !== 'category' && filters.category && row.category !== filters.category) {
    return false
  }
  if (skip !== 'search' && !matchesSearch(row, filters.search)) {
    return false
  }
  return true
}

function buildFacetOptions(
  rows: ParamRow[],
  key: 'param_group' | 'stage' | 'category' | 'family' | 'feature',
): CountOption[] {
  const counts = new Map<string, number>()
  for (const row of rows) {
    const value = row[key]
    if (!value) {
      continue
    }
    counts.set(value, (counts.get(value) ?? 0) + 1)
  }
  return Array.from(counts.entries())
    .sort(([left], [right]) => left.localeCompare(right))
    .map(([value, count]) => ({ value, count }))
}

function clampPage(page: number, totalPages: number) {
  return Math.min(Math.max(1, page), Math.max(1, totalPages))
}

export function ImportDetailPage() {
  const { importId } = useParams<{ importId: string }>()
  const [activeTab, setActiveTab] = useState<(typeof detailTabs)[number]>('PARAMS')
  const [summary, setSummary] = useState<ImportDetailSummary | null>(null)
  const [facets, setFacets] = useState<ParamFacets | null>(null)
  const [selectedFileType, setSelectedFileType] = useState('')
  const [selectedParamGroup, setSelectedParamGroup] = useState('')
  const [selectedFamily, setSelectedFamily] = useState('')
  const [selectedFeature, setSelectedFeature] = useState('')
  const [selectedStage, setSelectedStage] = useState('')
  const [selectedCategory, setSelectedCategory] = useState('')
  const [paramSearch, setParamSearch] = useState('')
  const [sourceRows, setSourceRows] = useState<ParamRow[]>([])
  const [page, setPage] = useState(1)
  const [appSpec, setAppSpec] = useState<Record<string, unknown> | null | undefined>(undefined)
  const [bsg, setBsg] = useState<Record<string, Array<Record<string, unknown>>> | undefined>(undefined)
  const [rpm, setRpm] = useState<RpmData | undefined>(undefined)
  const [summaryLoading, setSummaryLoading] = useState(false)
  const [paramsLoading, setParamsLoading] = useState(false)
  const [sectionLoading, setSectionLoading] = useState(false)
  const [error, setError] = useState('')
  const supportsProcessFilters = selectedFileType === 'PRM'
  const filters = useMemo<ParamFilterState>(
    () => ({
      paramGroup: selectedParamGroup,
      family: selectedFamily,
      feature: selectedFeature,
      stage: selectedStage,
      category: selectedCategory,
      search: paramSearch,
    }),
    [paramSearch, selectedCategory, selectedFeature, selectedFamily, selectedParamGroup, selectedStage],
  )

  useEffect(() => {
    if (!importId) {
      return
    }

    setSummaryLoading(true)
    setError('')
    setSummary(null)
    setFacets(null)
    setSourceRows([])
    setSelectedFileType('')
    setSelectedParamGroup('')
    setSelectedFamily('')
    setSelectedFeature('')
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
    if (!importId || activeTab !== 'PARAMS' || !selectedFileType) {
      return
    }

    setParamsLoading(true)
    setError('')
    setSourceRows([])
    void (async () => {
      try {
        const rows: ParamRow[] = []
        let fetchPage = 1
        let totalPages = 1
        do {
          const response = await api.get<ApiResponse<{ rows: ParamRow[]; total_pages: number }>>(
            `/imports/${importId}/params`,
            {
              params: {
                file_type: selectedFileType,
                page: fetchPage,
                page_size: 500,
              },
            },
          )
          rows.push(...response.data.data.rows)
          totalPages = response.data.data.total_pages
          fetchPage += 1
        } while (fetchPage <= totalPages)
        setSourceRows(rows)
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : 'Failed to load parameter rows')
      } finally {
        setParamsLoading(false)
      }
    })()
  }, [activeTab, importId, selectedFileType])

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
          const response = await api.get<ApiResponse<Record<string, Array<Record<string, unknown>>>>>((
            `/imports/${importId}/bsg`
          ))
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
  const filteredRows = useMemo(
    () => sourceRows.filter((row) => matchesFilters(row, filters)),
    [filters, sourceRows],
  )
  const groupOptions = useMemo(
    () => buildFacetOptions(sourceRows.filter((row) => matchesFilters(row, filters, 'paramGroup')), 'param_group'),
    [filters, sourceRows],
  )
  const familyOptions = useMemo(
    () =>
      supportsProcessFilters
        ? buildFacetOptions(sourceRows.filter((row) => matchesFilters(row, filters, 'family')), 'family')
        : [],
    [filters, sourceRows, supportsProcessFilters],
  )
  const featureOptions = useMemo(
    () =>
      supportsProcessFilters
        ? buildFacetOptions(sourceRows.filter((row) => matchesFilters(row, filters, 'feature')), 'feature')
        : [],
    [filters, sourceRows, supportsProcessFilters],
  )
  const stageOptions = useMemo(
    () =>
      supportsProcessFilters
        ? buildFacetOptions(sourceRows.filter((row) => matchesFilters(row, filters, 'stage')), 'stage')
        : [],
    [filters, sourceRows, supportsProcessFilters],
  )
  const categoryOptions = useMemo(
    () =>
      supportsProcessFilters
        ? buildFacetOptions(sourceRows.filter((row) => matchesFilters(row, filters, 'category')), 'category')
        : [],
    [filters, sourceRows, supportsProcessFilters],
  )

  useEffect(() => {
    if (selectedParamGroup && !groupOptions.some((option) => option.value === selectedParamGroup)) {
      setSelectedParamGroup('')
      setPage(1)
    }
  }, [groupOptions, selectedParamGroup])

  useEffect(() => {
    if (selectedFamily && !familyOptions.some((option) => option.value === selectedFamily)) {
      setSelectedFamily('')
      setPage(1)
    }
  }, [familyOptions, selectedFamily])

  useEffect(() => {
    if (selectedFeature && !featureOptions.some((option) => option.value === selectedFeature)) {
      setSelectedFeature('')
      setPage(1)
    }
  }, [featureOptions, selectedFeature])

  useEffect(() => {
    if (selectedStage && !stageOptions.some((option) => option.value === selectedStage)) {
      setSelectedStage('')
      setPage(1)
    }
  }, [selectedStage, stageOptions])

  useEffect(() => {
    if (selectedCategory && !categoryOptions.some((option) => option.value === selectedCategory)) {
      setSelectedCategory('')
      setPage(1)
    }
  }, [categoryOptions, selectedCategory])

  const isPrmSegmentedView = selectedFileType === 'PRM'
  const prmSegmentSections = useMemo(() => {
    if (!isPrmSegmentedView) {
      return []
    }
    const groups = new Map<string, ParamRow[]>()
    for (const row of filteredRows) {
      const label = prmSegmentGroup(row.param_name, row.file_type) ?? 'General'
      const bucket = groups.get(label)
      if (bucket) {
        bucket.push(row)
      } else {
        groups.set(label, [row])
      }
    }
    return Array.from(groups.entries())
      .sort(([left], [right]) => compareSegmentLabel(left, right))
      .map(([label, rows]) => ({
        label,
        count: rows.length,
        rows: toParamTableRows(rows),
      }))
  }, [filteredRows, isPrmSegmentedView])
  const prmSegmentPages = useMemo(() => {
    if (!isPrmSegmentedView) {
      return []
    }
    const pages: SegmentPage[] = []
    let currentSections: SegmentSection[] = []
    let currentRowCount = 0
    for (const section of prmSegmentSections) {
      if (currentSections.length > 0 && currentRowCount + section.count > PRM_SEGMENT_PAGE_SIZE) {
        pages.push({ sections: currentSections, rowCount: currentRowCount })
        currentSections = []
        currentRowCount = 0
      }
      currentSections.push(section)
      currentRowCount += section.count
    }
    if (currentSections.length > 0) {
      pages.push({ sections: currentSections, rowCount: currentRowCount })
    }
    if (pages.length === 0) {
      pages.push({ sections: [], rowCount: 0 })
    }
    return pages
  }, [isPrmSegmentedView, prmSegmentSections])
  const nonPrmTotalPages = Math.max(1, Math.ceil(filteredRows.length / PARAM_PAGE_SIZE))
  const normalizedPage = clampPage(page, isPrmSegmentedView ? prmSegmentPages.length : nonPrmTotalPages)
  const pagedRows = useMemo(() => {
    if (isPrmSegmentedView) {
      return []
    }
    const start = (normalizedPage - 1) * PARAM_PAGE_SIZE
    return filteredRows.slice(start, start + PARAM_PAGE_SIZE)
  }, [filteredRows, isPrmSegmentedView, normalizedPage])
  const paramRows = useMemo(() => toParamTableRows(pagedRows), [pagedRows])
  const activePrmSegmentPage = isPrmSegmentedView
    ? prmSegmentPages[normalizedPage - 1] ?? { sections: [], rowCount: 0 }
    : null
  const currentTotalPages = isPrmSegmentedView ? Math.max(1, prmSegmentPages.length) : nonPrmTotalPages
  const currentShownCount = isPrmSegmentedView ? activePrmSegmentPage?.rowCount ?? 0 : pagedRows.length

  useEffect(() => {
    if (page !== normalizedPage) {
      setPage(normalizedPage)
    }
  }, [normalizedPage, page])

  const resetParamFilters = () => {
    setSelectedParamGroup('')
    setSelectedFamily('')
    setSelectedFeature('')
    setSelectedStage('')
    setSelectedCategory('')
    setParamSearch('')
    setPage(1)
  }

  const exportParamsCsv = () => {
    if (!importId) {
      return
    }
    downloadCsv(
      `import_${importId}_${selectedFileType || 'params'}.csv`,
      toParamTableRows(filteredRows),
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
              <span className="summary-inline">Filtered rows: {filteredRows.length}</span>
            </div>
            <div className="chip-grid">
              {fileTypes.map((option) => (
                <button
                  key={option.value}
                  className={`filter-chip${selectedFileType === option.value ? ' active' : ''}`}
                  onClick={() => {
                    setSelectedFileType(option.value)
                    setSelectedParamGroup('')
                    setSelectedFamily('')
                    setSelectedFeature('')
                    setSelectedStage('')
                    setSelectedCategory('')
                    setParamSearch('')
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
                value={selectedParamGroup}
                onChange={(e) => {
                  setSelectedParamGroup(e.target.value)
                  setPage(1)
                }}
              >
                <option value="">All groups</option>
                {groupOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {formatParamGroupLabel(option.value)} ({option.count})
                  </option>
                ))}
              </select>
              {supportsProcessFilters ? (
                <select
                  value={selectedFamily}
                  onChange={(e) => {
                    setSelectedFamily(e.target.value)
                    setPage(1)
                  }}
                >
                  <option value="">All families</option>
                  {familyOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {humanizeSemanticLabel(option.value)} ({option.count})
                    </option>
                  ))}
                </select>
              ) : null}
              {supportsProcessFilters ? (
                <select
                  value={selectedFeature}
                  onChange={(e) => {
                    setSelectedFeature(e.target.value)
                    setPage(1)
                  }}
                >
                  <option value="">All features</option>
                  {featureOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {humanizeSemanticLabel(option.value)} ({option.count})
                    </option>
                  ))}
                </select>
              ) : null}
              {supportsProcessFilters ? (
                <select
                  value={selectedStage}
                  onChange={(e) => {
                    setSelectedStage(e.target.value)
                    setPage(1)
                  }}
                >
                  <option value="">All process stages</option>
                  {stageOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {formatStageLabel(option.value)} ({option.count})
                    </option>
                  ))}
                </select>
              ) : null}
              {supportsProcessFilters ? (
                <select
                  value={selectedCategory}
                  onChange={(e) => {
                    setSelectedCategory(e.target.value)
                    setPage(1)
                  }}
                >
                  <option value="">All parameter classes</option>
                  {categoryOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {humanizeSemanticLabel(option.value)} ({option.count})
                    </option>
                  ))}
                </select>
              ) : null}
              <input
                value={paramSearch}
                onChange={(e) => {
                  setParamSearch(e.target.value)
                  setPage(1)
                }}
                placeholder="Search parameter name"
              />
              <button onClick={resetParamFilters}>Reset filters</button>
              <button className="primary" onClick={exportParamsCsv}>
                Export filtered CSV
              </button>
            </div>
            {paramsLoading ? <p className="empty">Loading parameter rows...</p> : null}
            {isPrmSegmentedView ? (
              <div className="segment-groups">
                {activePrmSegmentPage?.sections.length === 0 ? <ObjectTable rows={[]} /> : null}
                {activePrmSegmentPage?.sections.map((section) => (
                  <section key={section.label} className="segment-group">
                    <div className="segment-group-header">
                      <h3>{section.label}</h3>
                      <span>{section.count} rows</span>
                    </div>
                    <ObjectTable rows={section.rows} />
                  </section>
                ))}
              </div>
            ) : (
              <ObjectTable rows={paramRows} />
            )}
          </div>

          <div className="panel pagination-row">
            <button disabled={normalizedPage <= 1} onClick={() => setPage((prev) => Math.max(1, prev - 1))}>
              Prev
            </button>
            <span>
              Page {normalizedPage} / {currentTotalPages}
            </span>
            <button
              disabled={normalizedPage >= currentTotalPages}
              onClick={() => setPage((prev) => Math.min(currentTotalPages, prev + 1))}
            >
              Next
            </button>
            <span style={{ marginLeft: 'auto' }}>
              Showing {currentShownCount} of {filteredRows.length}
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
