import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

type ControlPoint = {
  recipe_datetime: string
  value: number
  out_of_control: boolean
}

type Summary = {
  ucl: number
  lcl: number
  mean: number
}

export function ControlChart({ points, summary }: { points: ControlPoint[]; summary: Summary }) {
  if (points.length === 0) {
    return <p className="empty">No control chart points.</p>
  }

  return (
    <div style={{ width: '100%', height: 340 }}>
      <ResponsiveContainer>
        <LineChart data={points}>
          <CartesianGrid stroke="#e8ded0" strokeDasharray="3 3" />
          <XAxis dataKey="recipe_datetime" className="mono" />
          <YAxis />
          <Tooltip />
          <ReferenceLine y={summary.mean} stroke="#007a63" label="CL" />
          <ReferenceLine y={summary.ucl} stroke="#b7410e" strokeDasharray="4 4" label="UCL" />
          <ReferenceLine y={summary.lcl} stroke="#b7410e" strokeDasharray="4 4" label="LCL" />
          <Line
            type="monotone"
            dataKey="value"
            stroke="#1e4fa8"
            strokeWidth={2}
            dot={({ cx, cy, payload }) => (
              <circle cx={cx} cy={cy} r={payload.out_of_control ? 4 : 2.5} fill={payload.out_of_control ? '#b7410e' : '#1e4fa8'} />
            )}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

