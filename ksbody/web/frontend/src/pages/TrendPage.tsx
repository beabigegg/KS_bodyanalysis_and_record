import { useState } from 'react'
import { api, type ApiResponse } from '../lib/api'
import { TrendChart } from '../components/TrendChart'

type TrendSeriesApi = {
  key: string
  points: Array<{
    recipe_datetime: string
    param_value: string | number
  }>
  reference?: {
    min_value?: string | null
    max_value?: string | null
    default_value?: string | null
  } | null
}

type TrendPayload = {
  series: TrendSeriesApi[]
}

type TrendSeriesView = {
  key: string
  points: Array<{ recipe_datetime: string; value: number }>
  reference?: {
    min_value?: string | null
    max_value?: string | null
    default_value?: string | null
  } | null
}

export function TrendPage() {
  const [machineId, setMachineId] = useState('')
  const [machines, setMachines] = useState('')
  const [productType, setProductType] = useState('')
  const [bop, setBop] = useState('')
  const [waferPn, setWaferPn] = useState('')
  const [paramName, setParamName] = useState('')
  const [params, setParams] = useState('')
  const [start, setStart] = useState('')
  const [end, setEnd] = useState('')
  const [series, setSeries] = useState<TrendSeriesView[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const applyRange = (days: number) => {
    const now = new Date()
    const from = new Date(now.getTime() - days * 24 * 60 * 60 * 1000)
    setStart(from.toISOString().slice(0, 16))
    setEnd(now.toISOString().slice(0, 16))
  }

  const queryTrend = async () => {
    if (!paramName) {
      return
    }
    setLoading(true)
    setError('')
    try {
      const response = await api.get<ApiResponse<TrendPayload>>('/trend', {
        params: {
          machine_id: machineId || undefined,
          machines: machines || undefined,
          product_type: productType || undefined,
          bop: bop || undefined,
          wafer_pn: waferPn || undefined,
          param_name: paramName,
          params: params || undefined,
          start: start ? new Date(start).toISOString() : undefined,
          end: end ? new Date(end).toISOString() : undefined,
        },
      })
      const normalized: TrendSeriesView[] = response.data.data.series.map((item) => ({
        key: item.key,
        reference: item.reference,
        points: item.points
          .map((point) => ({
            recipe_datetime: point.recipe_datetime,
            value: Number(point.param_value),
          }))
          .filter((point) => Number.isFinite(point.value)),
      }))
      setSeries(normalized)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load trend data')
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="page">
      <header className="page-header">
        <h2>Trend Analysis</h2>
        <p>Single or multi-machine parameter overlays with time range control.</p>
      </header>

      <div className="panel controls">
        <input value={machineId} onChange={(e) => setMachineId(e.target.value)} placeholder="machine_id" />
        <input value={machines} onChange={(e) => setMachines(e.target.value)} placeholder="machines csv" />
        <input value={productType} onChange={(e) => setProductType(e.target.value)} placeholder="product_type" />
        <input value={bop} onChange={(e) => setBop(e.target.value)} placeholder="bop" />
        <input value={waferPn} onChange={(e) => setWaferPn(e.target.value)} placeholder="wafer_pn" />
        <input value={paramName} onChange={(e) => setParamName(e.target.value)} placeholder="param_name (required)" />
        <input value={params} onChange={(e) => setParams(e.target.value)} placeholder="params csv" />
        <input type="datetime-local" value={start} onChange={(e) => setStart(e.target.value)} />
        <input type="datetime-local" value={end} onChange={(e) => setEnd(e.target.value)} />
      </div>

      <div className="panel" style={{ display: 'flex', gap: 8 }}>
        <button onClick={() => applyRange(30)}>Last 30 days</button>
        <button onClick={() => applyRange(90)}>Last 90 days</button>
        <button className="primary" onClick={queryTrend} disabled={loading}>
          {loading ? 'Loading...' : 'Run trend query'}
        </button>
      </div>

      {error ? <div className="panel" style={{ color: '#b7410e' }}>{error}</div> : null}

      <div className="panel">
        <TrendChart series={series} />
      </div>
    </section>
  )
}
