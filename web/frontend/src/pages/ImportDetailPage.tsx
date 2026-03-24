import { useEffect, useMemo, useState } from 'react'
import { useParams } from 'react-router-dom'
import { api, type ApiResponse } from '../lib/api'
import { downloadCsv } from '../lib/csv'
import { ObjectTable } from '../components/ObjectTable'
import type { ParamRow } from '../types'

type GroupedParams = Record<string, ParamRow[]>
type RpmData = {
  limits: Array<Record<string, unknown>>
  reference: Array<Record<string, unknown>>
}

const detailTabs = ['PARAMS', 'APP', 'BSG', 'RPM'] as const

export function ImportDetailPage() {
  const { importId } = useParams<{ importId: string }>()
  const [activeTab, setActiveTab] = useState<(typeof detailTabs)[number]>('PARAMS')
  const [paramSearch, setParamSearch] = useState('')
  const [paramsByType, setParamsByType] = useState<GroupedParams>({})
  const [selectedFileType, setSelectedFileType] = useState('')
  const [selectedGroup, setSelectedGroup] = useState('')
  const [appSpec, setAppSpec] = useState<Record<string, unknown> | null>(null)
  const [bsg, setBsg] = useState<Record<string, Array<Record<string, unknown>>>>({})
  const [rpm, setRpm] = useState<RpmData>({ limits: [], reference: [] })
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!importId) {
      return
    }
    void (async () => {
      setLoading(true)
      try {
        const [paramsRes, appRes, bsgRes, rpmRes] = await Promise.all([
          api.get<ApiResponse<GroupedParams>>(`/imports/${importId}/params`),
          api.get<ApiResponse<Record<string, unknown> | null>>(`/imports/${importId}/app-spec`),
          api.get<ApiResponse<Record<string, Array<Record<string, unknown>>>>>(
            `/imports/${importId}/bsg`,
          ),
          api.get<ApiResponse<RpmData>>(`/imports/${importId}/rpm`),
        ])
        setParamsByType(paramsRes.data.data)
        setAppSpec(appRes.data.data)
        setBsg(bsgRes.data.data)
        setRpm(rpmRes.data.data)
        const fileTypes = Object.keys(paramsRes.data.data)
        setSelectedFileType(fileTypes[0] ?? '')
        setSelectedGroup('')
      } finally {
        setLoading(false)
      }
    })()
  }, [importId])

  const fileTypes = Object.keys(paramsByType)

  // 從 param_name 取分組前綴
  // 格式優先順序：role/pp_body → role；section.key → section；其他 → '(other)'
  function getParamGroup(paramName: string): string {
    if (paramName.includes('/')) return paramName.split('/')[0]
    if (paramName.includes('.')) return paramName.split('.')[0]
    return '(other)'
  }

  const availableGroups = useMemo(() => {
    const rows = paramsByType[selectedFileType] ?? []
    const groups = Array.from(new Set(rows.map((r) => getParamGroup(r.param_name)))).sort()
    return groups
  }, [paramsByType, selectedFileType])

  const filteredRows = useMemo(() => {
    const rows = paramsByType[selectedFileType] ?? []
    const byGroup = selectedGroup ? rows.filter((r) => getParamGroup(r.param_name) === selectedGroup) : rows
    if (!paramSearch.trim()) return byGroup
    const keyword = paramSearch.toLowerCase()
    return byGroup.filter((row) => row.param_name.toLowerCase().includes(keyword))
  }, [paramsByType, selectedFileType, selectedGroup, paramSearch])

  const exportParamsCsv = () => {
    downloadCsv(
      `import_${importId}_${selectedFileType || 'params'}.csv`,
      filteredRows.map((row) => ({ ...row })),
    )
  }

  return (
    <section className="page">
      <header className="page-header">
        <h2>Import Detail #{importId}</h2>
        <p>Parameter groups by file type, with APP/BSG/RPM detail tabs.</p>
      </header>

      <div className="panel tabs">
        {detailTabs.map((tab) => (
          <button key={tab} className={activeTab === tab ? 'active' : ''} onClick={() => setActiveTab(tab)}>
            {tab}
          </button>
        ))}
      </div>

      {loading ? <p className="empty">Loading detail...</p> : null}

      {activeTab === 'PARAMS' ? (
        <div className="panel">
          <div className="controls" style={{ marginBottom: 10 }}>
            <select
              value={selectedFileType}
              onChange={(e) => {
                setSelectedFileType(e.target.value)
                setSelectedGroup('')
              }}
            >
              {fileTypes.map((type) => (
                <option key={type} value={type}>
                  {type}
                </option>
              ))}
            </select>
            <select value={selectedGroup} onChange={(e) => setSelectedGroup(e.target.value)}>
              <option value="">All groups ({(paramsByType[selectedFileType] ?? []).length})</option>
              {availableGroups.map((g) => {
                const count = (paramsByType[selectedFileType] ?? []).filter(
                  (r) => getParamGroup(r.param_name) === g,
                ).length
                return (
                  <option key={g} value={g}>
                    {g} ({count})
                  </option>
                )
              })}
            </select>
            <input
              value={paramSearch}
              onChange={(e) => setParamSearch(e.target.value)}
              placeholder="Search parameter name"
            />
            <button className="primary" onClick={exportParamsCsv}>
              Export CSV
            </button>
          </div>
          <ObjectTable rows={filteredRows.map((row) => ({ ...row }))} />
        </div>
      ) : null}

      {activeTab === 'APP' ? (
        <div className="panel">
          <ObjectTable rows={appSpec ? [appSpec] : []} />
        </div>
      ) : null}

      {activeTab === 'BSG' ? (
        <div className="panel">
          {Object.entries(bsg).length === 0 ? <p className="empty">No BSG rows.</p> : null}
          {Object.entries(bsg).map(([group, rows]) => (
            <div key={group} style={{ marginBottom: 12 }}>
              <h3 style={{ marginBottom: 6 }}>Ball Group {group}</h3>
              <ObjectTable rows={rows} />
            </div>
          ))}
        </div>
      ) : null}

      {activeTab === 'RPM' ? (
        <div className="panel split-2">
          <div>
            <h3 style={{ marginTop: 0 }}>RPM Limits</h3>
            <ObjectTable rows={rpm.limits} />
          </div>
          <div>
            <h3 style={{ marginTop: 0 }}>RPM Reference</h3>
            <ObjectTable rows={rpm.reference} />
          </div>
        </div>
      ) : null}
    </section>
  )
}

