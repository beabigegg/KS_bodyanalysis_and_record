import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

type TrendPoint = {
  recipe_datetime: string
  value: number
}

type TrendSeries = {
  key: string
  points: TrendPoint[]
  reference?: {
    min_value?: string | null
    max_value?: string | null
    default_value?: string | null
  } | null
}

const palette = ['#007a63', '#da8a00', '#b7410e', '#1e4fa8', '#5a4cc5', '#5b7f1d']

function toNumber(value: string | null | undefined): number | null {
  if (!value) {
    return null
  }
  const num = Number(value)
  return Number.isFinite(num) ? num : null
}

export function TrendChart({ series }: { series: TrendSeries[] }) {
  const timeMap = new Map<string, Record<string, unknown>>()
  series.forEach((item) => {
    item.points.forEach((point) => {
      const existing = timeMap.get(point.recipe_datetime) || { time: point.recipe_datetime }
      existing[item.key] = point.value
      timeMap.set(point.recipe_datetime, existing)
    })
  })
  const merged = Array.from(timeMap.values()).sort((a, b) =>
    String(a.time).localeCompare(String(b.time)),
  )

  if (merged.length === 0) {
    return <p className="empty">No trend points.</p>
  }

  return (
    <div style={{ width: '100%', height: 360 }}>
      <ResponsiveContainer>
        <LineChart data={merged}>
          <CartesianGrid stroke="#e8ded0" strokeDasharray="3 3" />
          <XAxis dataKey="time" className="mono" />
          <YAxis />
          <Tooltip />
          <Legend />
          {series.map((item, idx) => (
            <Line
              key={item.key}
              type="monotone"
              dataKey={item.key}
              stroke={palette[idx % palette.length]}
              dot={false}
              strokeWidth={2}
            />
          ))}
          {series[0]?.reference ? (
            <>
              {toNumber(series[0].reference?.min_value) !== null ? (
                <ReferenceLine y={toNumber(series[0].reference?.min_value) ?? 0} stroke="#b7410e" strokeDasharray="4 4" />
              ) : null}
              {toNumber(series[0].reference?.max_value) !== null ? (
                <ReferenceLine y={toNumber(series[0].reference?.max_value) ?? 0} stroke="#b7410e" strokeDasharray="4 4" />
              ) : null}
              {toNumber(series[0].reference?.default_value) !== null ? (
                <ReferenceLine y={toNumber(series[0].reference?.default_value) ?? 0} stroke="#007a63" strokeDasharray="4 4" />
              ) : null}
            </>
          ) : null}
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

