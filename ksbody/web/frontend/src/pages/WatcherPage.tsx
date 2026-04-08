import { useEffect, useMemo, useState } from 'react'
import { api, type ApiResponse } from '../lib/api'

type WatchPathStatus = {
  path: string
  available?: boolean
  accessible?: boolean
  file_count: number
}

type WatcherStatusResponse = {
  running: boolean
  watch_paths: WatchPathStatus[]
}

type DiskUsageRow = {
  path?: string
  mount_path?: string
  total?: number
  total_bytes?: number
  used?: number
  used_bytes?: number
  free?: number
  free_bytes?: number
  usage_percent: number
  accessible?: boolean
}

type StatsWindow = {
  total: number
  processed?: number
  success?: number
  failed: number
  skipped: number
  success_rate?: number
}

type WatcherStats = {
  today: StatsWindow
  this_week: StatsWindow
}

type WatcherEvent = {
  id: number
  source_file: string
  event_type: string
  error_message: string | null
  event_datetime: string | null
}

type WatcherFile = {
  path: string
  size: number
  mtime: string
  status: string
  parsed_at: string | null
  error_message: string | null
}

type ReparseTask = {
  id: number
  source_file: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  error_message: string | null
  created_at: string | null
  started_at: string | null
  completed_at: string | null
}

type CleanupConfig = {
  enabled: boolean
  threshold_percent: number
  last_run_at: string | null
  updated_at?: string | null
}

type CleanupLogRow = {
  id: number
  source_file: string
  file_size_bytes: number
  file_mtime: string | null
  deleted_at: string | null
  trigger: string
}

const filePageSize = 20
const eventPageSize = 20
const cleanupLogPageSize = 20

function asPercent(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return '-'
  return `${value.toFixed(1)}%`
}

function toMb(bytes: number | null | undefined): string {
  if (bytes == null) return '-'
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

export function WatcherPage() {
  const [status, setStatus] = useState<WatcherStatusResponse | null>(null)
  const [diskUsage, setDiskUsage] = useState<DiskUsageRow[]>([])
  const [stats, setStats] = useState<WatcherStats | null>(null)
  const [events, setEvents] = useState<WatcherEvent[]>([])
  const [eventsTotal, setEventsTotal] = useState(0)
  const [eventsPage, setEventsPage] = useState(1)

  const [files, setFiles] = useState<WatcherFile[]>([])
  const [filesTotal, setFilesTotal] = useState(0)
  const [filesPage, setFilesPage] = useState(1)
  const [fileStatusFilter, setFileStatusFilter] = useState('')
  const [watchPathFilter, setWatchPathFilter] = useState('')
  const [selectedFiles, setSelectedFiles] = useState<Set<string>>(new Set())
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)

  const [reparseTasks, setReparseTasks] = useState<ReparseTask[]>([])
  const [taskPollIds, setTaskPollIds] = useState<number[]>([])

  const [cleanupConfig, setCleanupConfig] = useState<CleanupConfig | null>(null)
  const [thresholdInput, setThresholdInput] = useState('80')
  const [cleanupError, setCleanupError] = useState('')
  const [cleanupLogs, setCleanupLogs] = useState<CleanupLogRow[]>([])
  const [cleanupLogTotal, setCleanupLogTotal] = useState(0)
  const [cleanupLogPage, setCleanupLogPage] = useState(1)
  const [cleanupTriggerFilter, setCleanupTriggerFilter] = useState('')

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const watchPaths = useMemo(() => status?.watch_paths ?? [], [status])

  async function fetchDashboard() {
    setLoading(true)
    setError('')
    try {
      const [statusRes, diskRes, statsRes] = await Promise.all([
        api.get<WatcherStatusResponse>('/watcher/status'),
        api.get<{ data: DiskUsageRow[] }>('/watcher/disk-usage'),
        api.get<WatcherStats>('/watcher/stats'),
      ])
      setStatus(statusRes.data)
      setDiskUsage(diskRes.data.data ?? [])
      setStats(statsRes.data)
    } catch {
      setError('Failed to load watcher dashboard data.')
    } finally {
      setLoading(false)
    }
  }

  async function fetchEvents(page = eventsPage) {
    const response = await api.get<ApiResponse<WatcherEvent[]>>('/watcher/events', {
      params: {
        page,
        page_size: eventPageSize,
      },
    })
    setEvents(response.data.data)
    setEventsTotal(response.data.total)
  }

  async function fetchFiles(page = filesPage) {
    const response = await api.get<ApiResponse<WatcherFile[]>>('/watcher/files', {
      params: {
        page,
        page_size: filePageSize,
        status_filter: fileStatusFilter || undefined,
        path_filter: watchPathFilter || undefined,
      },
    })
    setFiles(response.data.data)
    setFilesTotal(response.data.total)
  }

  async function fetchCleanupConfig() {
    const response = await api.get<CleanupConfig>('/watcher/cleanup/config')
    setCleanupConfig(response.data)
    setThresholdInput(String(response.data.threshold_percent))
  }

  async function fetchCleanupLog(page = cleanupLogPage) {
    const response = await api.get<ApiResponse<CleanupLogRow[]>>('/watcher/cleanup/log', {
      params: {
        page,
        page_size: cleanupLogPageSize,
        trigger_filter: cleanupTriggerFilter || undefined,
      },
    })
    setCleanupLogs(response.data.data)
    setCleanupLogTotal(response.data.total)
  }

  useEffect(() => {
    void fetchDashboard()
    void fetchEvents(1)
    void fetchFiles(1)
    void fetchCleanupConfig()
    void fetchCleanupLog(1)
  }, [])

  useEffect(() => {
    setEventsPage(1)
    void fetchEvents(1)
  }, [])

  useEffect(() => {
    setFilesPage(1)
    setSelectedFiles(new Set())
    void fetchFiles(1)
  }, [fileStatusFilter, watchPathFilter])

  useEffect(() => {
    setCleanupLogPage(1)
    void fetchCleanupLog(1)
  }, [cleanupTriggerFilter])

  useEffect(() => {
    if (taskPollIds.length === 0) return

    let cancelled = false
    const intervalId = window.setInterval(async () => {
      if (cancelled) return
      const response = await api.get<{ data: ReparseTask[] }>('/watcher/reparse', {
        params: { task_ids: taskPollIds.join(',') },
      })
      const tasks = response.data.data ?? []
      if (!cancelled) {
        setReparseTasks(tasks)
      }
      const hasActive = tasks.some((t) => t.status === 'pending' || t.status === 'running')
      if (!hasActive) {
        setTaskPollIds([])
        void fetchFiles()
      }
    }, 5000)

    return () => {
      cancelled = true
      window.clearInterval(intervalId)
    }
  }, [taskPollIds, filesPage, fileStatusFilter, watchPathFilter])

  const allSelectedOnPage = files.length > 0 && files.every((f) => selectedFiles.has(f.path))

  function toggleSelectOnPage() {
    if (allSelectedOnPage) {
      setSelectedFiles((prev) => {
        const next = new Set(prev)
        files.forEach((file) => next.delete(file.path))
        return next
      })
      return
    }
    setSelectedFiles((prev) => {
      const next = new Set(prev)
      files.forEach((file) => next.add(file.path))
      return next
    })
  }

  function toggleSelectFile(path: string) {
    setSelectedFiles((prev) => {
      const next = new Set(prev)
      if (next.has(path)) next.delete(path)
      else next.add(path)
      return next
    })
  }

  async function handleReparse() {
    const sourceFiles = Array.from(selectedFiles)
    if (sourceFiles.length === 0) return

    const response = await api.post<{ task_ids: number[] }>('/watcher/reparse', { source_files: sourceFiles })
    setTaskPollIds(response.data.task_ids ?? [])
    setSelectedFiles(new Set())
  }

  function openDeleteDialog() {
    const sourceFiles = Array.from(selectedFiles)
    if (sourceFiles.length === 0) return
    setDeleteDialogOpen(true)
  }

  async function confirmDeleteSelected() {
    const sourceFiles = Array.from(selectedFiles)
    if (sourceFiles.length === 0) return
    await api.request({ method: 'DELETE', url: '/watcher/files', data: { source_files: sourceFiles } })
    setSelectedFiles(new Set())
    setDeleteDialogOpen(false)
    void fetchFiles()
    void fetchCleanupLog()
  }

  function handleDownload(path: string) {
    window.open(`/api/watcher/files/download?path=${encodeURIComponent(path)}`, '_blank')
  }

  function handleBatchDownload() {
    const sourceFiles = Array.from(selectedFiles)
    sourceFiles.forEach((path) => {
      window.open(`/api/watcher/files/download?path=${encodeURIComponent(path)}`, '_blank')
    })
  }

  async function handleSaveCleanupConfig() {
    setCleanupError('')
    const threshold = Number(thresholdInput)
    if (!Number.isInteger(threshold) || threshold < 1 || threshold > 99) {
      setCleanupError('Threshold must be an integer between 1 and 99.')
      return
    }
    await api.put('/watcher/cleanup/config', {
      enabled: Boolean(cleanupConfig?.enabled),
      threshold_percent: threshold,
    })
    await fetchCleanupConfig()
  }

  const filesTotalPages = Math.max(1, Math.ceil(filesTotal / filePageSize))
  const eventsTotalPages = Math.max(1, Math.ceil(eventsTotal / eventPageSize))
  const cleanupLogTotalPages = Math.max(1, Math.ceil(cleanupLogTotal / cleanupLogPageSize))

  return (
    <section className="page watcher-page">
      <header className="page-header">
        <h2>Watcher Monitoring</h2>
        <p>Track service health, inspect files, and manage reparse/cleanup operations.</p>
      </header>

      {error ? <div className="error-msg">{error}</div> : null}
      {loading ? <p className="empty">Loading watcher dashboard...</p> : null}

      <div className="watcher-grid watcher-status-grid">
        <div className="panel">
          <h3>Service Status</h3>
          <p className="status-dot">
            <span className={`dot ${status?.running ? 'normal' : 'abnormal'}`} />
            {status?.running ? 'Running' : 'Stopped'}
          </p>
          <ul className="watch-path-list">
            {watchPaths.map((wp) => (
              <li key={wp.path}>
                <span className="mono">{wp.path}</span>
                <span className={`chip ${(wp.available ?? wp.accessible) ? 'chip-ok' : 'chip-danger'}`}>
                  {(wp.available ?? wp.accessible) ? 'Accessible' : 'Unavailable'}
                </span>
                <span className="chip">Files: {wp.file_count}</span>
              </li>
            ))}
          </ul>
        </div>

        <div className="panel">
          <h3>Disk Usage</h3>
          <div className="watcher-cards">
            {diskUsage.map((du) => {
              const total = du.total_bytes ?? du.total
              const used = du.used_bytes ?? du.used
              const free = du.free_bytes ?? du.free
              return (
                <article className="watcher-card" key={du.mount_path ?? du.path}>
                  <p className="mono">{du.mount_path ?? du.path}</p>
                  <p>{asPercent(du.usage_percent)}</p>
                  <div className="usage-track">
                    <div className="usage-fill" style={{ width: `${Math.min(100, Math.max(0, du.usage_percent ?? 0))}%` }} />
                  </div>
                  <small>
                    {toMb(used)} used / {toMb(total)} total / {toMb(free)} free
                  </small>
                </article>
              )
            })}
          </div>
        </div>
      </div>

      <div className="watcher-grid watcher-stats-grid">
        <div className="panel watcher-stat-panel">
          <h4>Today Total</h4>
          <p>{stats?.today.total ?? 0}</p>
        </div>
        <div className="panel watcher-stat-panel">
          <h4>This Week Total</h4>
          <p>{stats?.this_week.total ?? 0}</p>
        </div>
        <div className="panel watcher-stat-panel">
          <h4>Today Success</h4>
          <p>{asPercent(stats?.today.success_rate)}</p>
        </div>
        <div className="panel watcher-stat-panel">
          <h4>Week Success</h4>
          <p>{asPercent(stats?.this_week.success_rate)}</p>
        </div>
      </div>

      <div className="panel">
        <h3>Recent Events</h3>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Time</th>
                <th>Type</th>
                <th>Source File</th>
                <th>Error</th>
              </tr>
            </thead>
            <tbody>
              {events.map((evt) => (
                <tr key={evt.id}>
                  <td className="mono">{evt.event_datetime ?? '-'}</td>
                  <td>
                    <span className={`chip chip-${evt.event_type}`}>{evt.event_type}</span>
                  </td>
                  <td className="mono">{evt.source_file}</td>
                  <td>
                    {evt.error_message ? (
                      <details>
                        <summary>Show</summary>
                        <pre className="error-pre">{evt.error_message}</pre>
                      </details>
                    ) : (
                      '-'
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="panel-inline-controls">
          <button disabled={eventsPage <= 1} onClick={() => { const p = Math.max(1, eventsPage - 1); setEventsPage(p); void fetchEvents(p) }}>Prev</button>
          <span>Page {eventsPage} / {eventsTotalPages}</span>
          <button disabled={eventsPage >= eventsTotalPages} onClick={() => { const p = Math.min(eventsTotalPages, eventsPage + 1); setEventsPage(p); void fetchEvents(p) }}>Next</button>
          <span style={{ marginLeft: 'auto' }}>Total: {eventsTotal}</span>
        </div>
      </div>

      <div className="panel">
        <h3>File Browser</h3>
        <div className="controls">
          <select value={fileStatusFilter} onChange={(e) => setFileStatusFilter(e.target.value)}>
            <option value="">All Status</option>
            <option value="processed">Processed</option>
            <option value="failed">Failed</option>
            <option value="skipped">Skipped</option>
            <option value="pending">Unparsed</option>
          </select>
          <select value={watchPathFilter} onChange={(e) => setWatchPathFilter(e.target.value)}>
            <option value="">All Watch Paths</option>
            {watchPaths.map((wp) => <option key={wp.path} value={wp.path}>{wp.path}</option>)}
          </select>
        </div>

        {selectedFiles.size > 0 ? (
          <div className="panel-inline-controls">
            <span>{selectedFiles.size} selected</span>
            <button onClick={() => void handleReparse()}>Reparse</button>
            <button className="warn" onClick={openDeleteDialog}>Delete</button>
            <button onClick={handleBatchDownload}>Export Download</button>
          </div>
        ) : null}

        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th><input type="checkbox" checked={allSelectedOnPage} onChange={toggleSelectOnPage} /></th>
                <th>Filename</th>
                <th>Size</th>
                <th>Modified</th>
                <th>Status</th>
                <th>Last Parsed</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {files.map((f) => (
                <tr key={f.path}>
                  <td><input type="checkbox" checked={selectedFiles.has(f.path)} onChange={() => toggleSelectFile(f.path)} /></td>
                  <td className="mono">{f.path.split('/').at(-1)}</td>
                  <td>{toMb(f.size)}</td>
                  <td className="mono">{f.mtime}</td>
                  <td><span className={`chip chip-${f.status}`}>{f.status}</span></td>
                  <td className="mono">{f.parsed_at ?? '-'}</td>
                  <td><button onClick={() => handleDownload(f.path)}>Download</button></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="panel-inline-controls">
          <button disabled={filesPage <= 1} onClick={() => { const p = Math.max(1, filesPage - 1); setFilesPage(p); void fetchFiles(p) }}>Prev</button>
          <span>Page {filesPage} / {filesTotalPages}</span>
          <button disabled={filesPage >= filesTotalPages} onClick={() => { const p = Math.min(filesTotalPages, filesPage + 1); setFilesPage(p); void fetchFiles(p) }}>Next</button>
          <span style={{ marginLeft: 'auto' }}>Total: {filesTotal}</span>
        </div>
      </div>

      <div className="panel">
        <h3>Reparse Progress</h3>
        {reparseTasks.length === 0 ? <p className="empty">No active reparse tasks.</p> : null}
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Source File</th>
                <th>Status</th>
                <th>Error</th>
                <th>Completed At</th>
              </tr>
            </thead>
            <tbody>
              {reparseTasks.map((task) => (
                <tr key={task.id}>
                  <td>{task.id}</td>
                  <td className="mono">{task.source_file}</td>
                  <td><span className={`chip chip-${task.status}`}>{task.status}</span></td>
                  <td>{task.error_message ?? '-'}</td>
                  <td className="mono">{task.completed_at ?? '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="panel">
        <h3>Cleanup Configuration</h3>
        <div className="controls">
          <label className="inline-check">
            <input
              type="checkbox"
              checked={Boolean(cleanupConfig?.enabled)}
              onChange={(e) => setCleanupConfig((prev) => ({
                enabled: e.target.checked,
                threshold_percent: prev?.threshold_percent ?? 80,
                last_run_at: prev?.last_run_at ?? null,
                updated_at: prev?.updated_at ?? null,
              }))}
            />
            Enable Auto Cleanup
          </label>
          <input
            value={thresholdInput}
            onChange={(e) => setThresholdInput(e.target.value)}
            placeholder="Threshold (1-99)"
          />
          <button className="primary" onClick={() => void handleSaveCleanupConfig()}>Save Config</button>
        </div>
        {cleanupError ? <p className="error-msg">{cleanupError}</p> : null}
        <p>
          Last run: <span className="mono">{cleanupConfig?.last_run_at ?? '-'}</span>
        </p>
        <p>
          Current max disk usage: <strong>{asPercent(Math.max(0, ...diskUsage.map((d) => d.usage_percent ?? 0)))}</strong>
        </p>

        <h4>Cleanup Log</h4>
        <div className="controls">
          <select value={cleanupTriggerFilter} onChange={(e) => setCleanupTriggerFilter(e.target.value)}>
            <option value="">All Triggers</option>
            <option value="auto">Auto</option>
            <option value="manual">Manual</option>
          </select>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Deleted At</th>
                <th>Source File</th>
                <th>Size</th>
                <th>Trigger</th>
              </tr>
            </thead>
            <tbody>
              {cleanupLogs.map((row) => (
                <tr key={row.id}>
                  <td className="mono">{row.deleted_at ?? '-'}</td>
                  <td className="mono">{row.source_file}</td>
                  <td>{toMb(row.file_size_bytes)}</td>
                  <td><span className={`chip chip-${row.trigger}`}>{row.trigger}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="panel-inline-controls">
          <button disabled={cleanupLogPage <= 1} onClick={() => { const p = Math.max(1, cleanupLogPage - 1); setCleanupLogPage(p); void fetchCleanupLog(p) }}>Prev</button>
          <span>Page {cleanupLogPage} / {cleanupLogTotalPages}</span>
          <button disabled={cleanupLogPage >= cleanupLogTotalPages} onClick={() => { const p = Math.min(cleanupLogTotalPages, cleanupLogPage + 1); setCleanupLogPage(p); void fetchCleanupLog(p) }}>Next</button>
          <span style={{ marginLeft: 'auto' }}>Total: {cleanupLogTotal}</span>
        </div>
      </div>

      {deleteDialogOpen ? (
        <div className="delete-modal-backdrop">
          <div className="delete-modal">
            <h3>Confirm File Deletion</h3>
            <p>Delete {selectedFiles.size} selected file(s)? This cannot be undone.</p>
            <div className="delete-modal-footer">
              <button onClick={() => setDeleteDialogOpen(false)}>Cancel</button>
              <button className="warn" onClick={() => void confirmDeleteSelected()}>Delete</button>
            </div>
          </div>
        </div>
      ) : null}
    </section>
  )
}
