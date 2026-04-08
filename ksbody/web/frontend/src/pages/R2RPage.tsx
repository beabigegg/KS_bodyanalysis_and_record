import { useEffect, useMemo, useState } from 'react'
import { api, type ApiResponse } from '../lib/api'
import { ControlChart } from '../components/ControlChart'
import { DistributionChart } from '../components/DistributionChart'

type DashboardItem = {
  param_name: string
  status: 'normal' | 'warning' | 'abnormal'
  is_watchlist: boolean
  count: number
  cpk: number | null
}

type StatsPayload = {
  summary: {
    mean: number
    std_dev: number
    ucl: number
    lcl: number
    cp: number | null
    cpk: number | null
    count: number
    min_spec: number | null
    max_spec: number | null
  }
  points: Array<{
    recipe_datetime: string
    value: number
    out_of_control: boolean
  }>
  histogram: Array<{
    start: number
    end: number
    count: number
  }>
}

type CurvePayload = Array<{ x: number; y: number }>

const WATCHLIST_KEY = 'ks-r2r-watchlist'

export function R2RPage() {
  const [machineId, setMachineId] = useState('')
  const [productType, setProductType] = useState('')
  const [dashboard, setDashboard] = useState<DashboardItem[]>([])
  const [selectedParam, setSelectedParam] = useState('')
  const [stats, setStats] = useState<StatsPayload | null>(null)
  const [curve, setCurve] = useState<CurvePayload>([])
  const [watchlist, setWatchlist] = useState<string[]>(() => {
    const saved = localStorage.getItem(WATCHLIST_KEY)
    if (!saved) {
      return []
    }
    try {
      return JSON.parse(saved) as string[]
    } catch {
      return []
    }
  })
  const watchlistCsv = useMemo(() => watchlist.join(','), [watchlist])

  useEffect(() => {
    localStorage.setItem(WATCHLIST_KEY, JSON.stringify(watchlist))
  }, [watchlist])

  const [error, setError] = useState('')

  const queryDashboard = async () => {
    if (!machineId || !productType) {
      return
    }
    setError('')
    try {
      const response = await api.get<ApiResponse<DashboardItem[]>>('/r2r/dashboard', {
        params: {
          machine_id: machineId,
          product_type: productType,
          watchlist: watchlistCsv,
        },
      })
      setDashboard(response.data.data)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load dashboard')
    }
  }

  const queryStats = async (paramName: string) => {
    setSelectedParam(paramName)
    setError('')
    try {
      const response = await api.get<ApiResponse<StatsPayload | null>>('/r2r/stats', {
        params: {
          machine_id: machineId,
          product_type: productType,
          param_name: paramName,
        },
      })
      const stat = response.data.data
      if (!stat) {
        setStats(null)
        setCurve([])
        return
      }
      setStats(stat)
      const curveResponse = await api.get<ApiResponse<CurvePayload>>('/r2r/normal-curve', {
        params: {
          mean_value: stat.summary.mean,
          std_dev: stat.summary.std_dev,
        },
      })
      setCurve(curveResponse.data.data)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load stats')
    }
  }

  return (
    <section className="page">
      <header className="page-header">
        <h2>R2R SPC Dashboard</h2>
        <p>Xbar control chart, distribution, and watchlist persistence.</p>
      </header>

      <div className="panel controls">
        <input value={machineId} onChange={(e) => setMachineId(e.target.value)} placeholder="machine_id" />
        <input value={productType} onChange={(e) => setProductType(e.target.value)} placeholder="product_type" />
        <button className="primary" onClick={queryDashboard}>
          Load dashboard
        </button>
      </div>

      {error ? <div className="panel" style={{ color: '#b7410e' }}>{error}</div> : null}

      <div className="panel">
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Watch</th>
                <th>Param</th>
                <th>Status</th>
                <th>Count</th>
                <th>Cpk</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {dashboard.map((item) => (
                <tr key={item.param_name}>
                  <td>
                    <input
                      type="checkbox"
                      checked={watchlist.includes(item.param_name)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setWatchlist((prev) => Array.from(new Set([...prev, item.param_name])))
                        } else {
                          setWatchlist((prev) => prev.filter((value) => value !== item.param_name))
                        }
                      }}
                    />
                  </td>
                  <td>{item.param_name}</td>
                  <td>
                    <span className="status-dot">
                      <span className={`dot ${item.status}`} />
                      {item.status}
                    </span>
                  </td>
                  <td>{item.count}</td>
                  <td>{item.cpk?.toFixed(3) ?? ''}</td>
                  <td>
                    <button onClick={() => void queryStats(item.param_name)}>View SPC</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {stats ? (
        <>
          <div className="panel">
            <h3 style={{ marginTop: 0 }}>Control Chart: {selectedParam}</h3>
            <ControlChart points={stats.points} summary={stats.summary} />
            <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', marginTop: 10 }}>
              <span>Mean: {stats.summary.mean.toFixed(4)}</span>
              <span>Std Dev: {stats.summary.std_dev.toFixed(4)}</span>
              <span>Cp: {stats.summary.cp?.toFixed(3) ?? '-'}</span>
              <span>Cpk: {stats.summary.cpk?.toFixed(3) ?? '-'}</span>
            </div>
          </div>
          <div className="panel">
            <h3 style={{ marginTop: 0 }}>Distribution</h3>
            <DistributionChart
              histogram={stats.histogram}
              curve={curve}
              minSpec={stats.summary.min_spec}
              maxSpec={stats.summary.max_spec}
            />
          </div>
        </>
      ) : null}
    </section>
  )
}
