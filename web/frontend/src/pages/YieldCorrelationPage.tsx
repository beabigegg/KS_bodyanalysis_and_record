import { useState } from 'react'
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { api, type ApiResponse } from '../lib/api'

type StatusPayload = {
  configured: boolean
  message: string
}

type CorrelationPayload = {
  configured: boolean
  message?: string
  trend: Array<{
    recipe_datetime: string
    param_value: number
    yield_value: number
  }>
  scatter: Array<{
    x: number
    y: number
  }>
}

export function YieldCorrelationPage() {
  const [status, setStatus] = useState<StatusPayload | null>(null)
  const [machineId, setMachineId] = useState('')
  const [productType, setProductType] = useState('')
  const [paramName, setParamName] = useState('')
  const [result, setResult] = useState<CorrelationPayload | null>(null)
  const [error, setError] = useState('')

  const loadStatus = async () => {
    setError('')
    try {
      const response = await api.get<ApiResponse<StatusPayload>>('/yield-correlation/status')
      setStatus(response.data.data)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to check Oracle status')
    }
  }

  const query = async () => {
    setError('')
    try {
      const response = await api.get<ApiResponse<CorrelationPayload>>('/yield-correlation/query', {
        params: {
          machine_id: machineId,
          product_type: productType,
          param_name: paramName,
        },
      })
      setResult(response.data.data)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to query correlation')
    }
  }

  return (
    <section className="page">
      <header className="page-header">
        <h2>Yield Correlation</h2>
        <p>Dual-axis trend and scatter plot against Oracle yield data.</p>
      </header>

      <div className="panel" style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
        <button onClick={loadStatus}>Check Oracle status</button>
        <span>{status ? status.message : 'Status not checked yet.'}</span>
      </div>

      {status && !status.configured ? (
        <div className="panel">
          <h3 style={{ marginTop: 0 }}>Oracle connection is not configured</h3>
          <p className="empty">
            Configure `ORACLE_DSN`, `ORACLE_USER`, and `ORACLE_PASSWORD` in `.env` to enable this page.
          </p>
        </div>
      ) : null}

      {error ? <div className="panel" style={{ color: '#b7410e' }}>{error}</div> : null}

      <div className="panel controls">
        <input value={machineId} onChange={(e) => setMachineId(e.target.value)} placeholder="machine_id" />
        <input value={productType} onChange={(e) => setProductType(e.target.value)} placeholder="product_type" />
        <input value={paramName} onChange={(e) => setParamName(e.target.value)} placeholder="param_name" />
        <button className="primary" onClick={query}>
          Query correlation
        </button>
      </div>

      {result && result.configured ? (
        <>
          <div className="panel">
            <h3 style={{ marginTop: 0 }}>Trend (Param + Yield)</h3>
            <div style={{ width: '100%', height: 320 }}>
              <ResponsiveContainer>
                <LineChart data={result.trend}>
                  <CartesianGrid stroke="#e8ded0" strokeDasharray="3 3" />
                  <XAxis dataKey="recipe_datetime" className="mono" />
                  <YAxis yAxisId="left" />
                  <YAxis yAxisId="right" orientation="right" />
                  <Tooltip />
                  <Legend />
                  <Line yAxisId="left" type="monotone" dataKey="param_value" stroke="#007a63" dot={false} />
                  <Line yAxisId="right" type="monotone" dataKey="yield_value" stroke="#b7410e" dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
          <div className="panel">
            <h3 style={{ marginTop: 0 }}>Scatter Correlation</h3>
            <div style={{ width: '100%', height: 320 }}>
              <ResponsiveContainer>
                <ScatterChart>
                  <CartesianGrid stroke="#e8ded0" strokeDasharray="3 3" />
                  <XAxis dataKey="x" name="Param" />
                  <YAxis dataKey="y" name="Yield" />
                  <Tooltip />
                  <Scatter data={result.scatter} fill="#1e4fa8" />
                </ScatterChart>
              </ResponsiveContainer>
            </div>
          </div>
        </>
      ) : null}
    </section>
  )
}

