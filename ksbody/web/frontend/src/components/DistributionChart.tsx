import {
  Bar,
  CartesianGrid,
  ComposedChart,
  Line,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

type HistogramBin = {
  start: number
  end: number
  count: number
}

type CurvePoint = {
  x: number
  y: number
}

type Props = {
  histogram: HistogramBin[]
  curve: CurvePoint[]
  minSpec: number | null
  maxSpec: number | null
}

export function DistributionChart({ histogram, curve, minSpec, maxSpec }: Props) {
  if (histogram.length === 0) {
    return <p className="empty">No distribution data.</p>
  }

  // Merge histogram bars with normal curve data by matching center values
  // Scale curve Y to match bar counts for overlay
  const totalCount = histogram.reduce((sum, bin) => sum + bin.count, 0)
  const binWidth = histogram.length > 1 ? histogram[1].start - histogram[0].start : 1

  const bars = histogram.map((bin) => {
    const center = (bin.start + bin.end) / 2
    // Find closest curve point to this bin center
    let curveY: number | undefined
    if (curve.length > 0) {
      let closest = curve[0]
      let minDist = Math.abs(curve[0].x - center)
      for (const pt of curve) {
        const dist = Math.abs(pt.x - center)
        if (dist < minDist) {
          minDist = dist
          closest = pt
        }
      }
      // Scale PDF value to count scale: pdf * totalCount * binWidth
      curveY = closest.y * totalCount * binWidth
    }
    return {
      range: `${bin.start.toFixed(2)}`,
      center,
      count: bin.count,
      normal: curveY,
    }
  })

  return (
    <div style={{ width: '100%', height: 340 }}>
      <ResponsiveContainer>
        <ComposedChart data={bars}>
          <CartesianGrid stroke="#e8ded0" strokeDasharray="3 3" />
          <XAxis dataKey="range" interval="preserveStartEnd" />
          <YAxis />
          <Tooltip />
          <Bar dataKey="count" fill="#007a63" />
          <Line type="monotone" dataKey="normal" stroke="#b7410e" dot={false} strokeWidth={2} />
          {minSpec !== null ? (
            <ReferenceLine x={minSpec.toFixed(2)} stroke="#1e4fa8" strokeDasharray="4 4" label="LSL" />
          ) : null}
          {maxSpec !== null ? (
            <ReferenceLine x={maxSpec.toFixed(2)} stroke="#1e4fa8" strokeDasharray="4 4" label="USL" />
          ) : null}
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  )
}
