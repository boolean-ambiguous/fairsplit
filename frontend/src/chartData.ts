// Ported from the mockup's buildChartData(): a dual-bar (owed vs owe) chart
// overlaid with a net line that switches color at each zero-crossing.

export interface ChartBar {
  owedX: number
  owedY: number
  owedH: number
  oweX: number
  oweY: number
  oweH: number
  barW: number
}

export interface ChartSegment {
  pointsStr: string
  positive: boolean
}

export interface ChartData {
  bars: ChartBar[]
  baseline: number
  segments: ChartSegment[]
}

interface Snapshot {
  owed: number
  owe: number
}

export function buildChartData(snaps: Snapshot[]): ChartData {
  const W = 600
  const pad = 10
  const baseline = 100
  if (snaps.length === 0) return { bars: [], baseline, segments: [] }

  const maxVal = Math.max(1, ...snaps.map((s) => Math.max(s.owed, s.owe)))
  const xStep = snaps.length > 1 ? (W - 2 * pad) / (snaps.length - 1) : 0
  const barW = Math.max(4, Math.min(22, xStep * 0.5)) || 22
  const scale = (baseline - pad) / maxVal

  const bars: ChartBar[] = snaps.map((s, i) => {
    const x = pad + i * xStep
    const owedH = s.owed * scale
    const oweH = s.owe * scale
    return { owedX: x - barW / 2, owedY: baseline - owedH, owedH, oweX: x - barW / 2, oweY: baseline, oweH, barW }
  })

  const netPoints = snaps.map((s, i) => {
    const x = pad + i * xStep
    const net = s.owed - s.owe
    return { x, y: baseline - net * scale, net }
  })

  const rawSegments: { points: { x: number; y: number; net: number }[]; positive: boolean }[] = []
  let cur = [netPoints[0]]
  for (let i = 1; i < netPoints.length; i++) {
    const prev = netPoints[i - 1]
    const curPt = netPoints[i]
    if (prev.net >= 0 === (curPt.net >= 0)) {
      cur.push(curPt)
    } else {
      const t = prev.net / (prev.net - curPt.net)
      const zx = prev.x + t * (curPt.x - prev.x)
      cur.push({ x: zx, y: baseline, net: 0 })
      rawSegments.push({ points: cur, positive: prev.net >= 0 })
      cur = [{ x: zx, y: baseline, net: 0 }, curPt]
    }
  }
  rawSegments.push({ points: cur, positive: cur[cur.length - 1].net >= 0 })

  const segments: ChartSegment[] = rawSegments.map((seg) => ({
    pointsStr: seg.points.map((p) => `${p.x},${p.y}`).join(' '),
    positive: seg.positive,
  }))

  return { bars, baseline, segments }
}
