'use client'

import { useEffect, useMemo, useRef, useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import type { Machine, SimMode, Telemetry } from '@/lib/mock-service'
import { stepTelemetry } from '@/lib/mock-service'

type MetricKey = 'rms' | 'temperature' | 'rpm' | 'kurtosis'

type Props = {
  machine: Machine
  mode: SimMode
  metric?: MetricKey
  height?: number
  showControls?: boolean
}

const labels: Record<MetricKey, string> = { rms: 'Vibration RMS', temperature: 'Temperature', rpm: 'RPM', kurtosis: 'Kurtosis' }
const units: Record<MetricKey, string> = { rms: 'mm/s', temperature: '°C', rpm: 'rpm', kurtosis: '' }

function getValue(point: Telemetry, metric: MetricKey) { return point[metric] }
function formatValue(value: number, metric: MetricKey) { return metric === 'rpm' ? value.toFixed(0) : value.toFixed(metric === 'temperature' ? 1 : 2) }

export function LiveTimeSeries({ machine, mode, metric: initialMetric = 'rms', height = 240, showControls = true }: Props) {
  const [metric, setMetric] = useState<MetricKey>(initialMetric)
  const [range, setRange] = useState<30 | 60 | 120>(60)
  const [series, setSeries] = useState<Telemetry[]>(() => machine.telemetry)
  const seriesRef = useRef(series)
  seriesRef.current = series

  useEffect(() => {
    setSeries(machine.telemetry)
  }, [machine.id])

  useEffect(() => {
    if (machine.status === 'STOPPED') return
    const timer = window.setInterval(() => {
      setSeries((previous) => {
        const last = previous.at(-1) ?? machine.telemetry.at(-1)!
        const next = stepTelemetry(last, mode)
        return [...previous.slice(-119), next]
      })
    }, 850)
    return () => window.clearInterval(timer)
  }, [machine.id, machine.status, mode])

  const visible = useMemo(() => series.slice(-range), [series, range])
  const values = visible.map((point) => getValue(point, metric))
  const latest = values.at(-1) ?? 0
  const min = useMemo(() => {
    const floor = metric === 'rpm' ? 1400 : metric === 'temperature' ? 48 : metric === 'rms' ? 0 : 2
    return Math.min(floor, ...values) - (metric === 'rpm' ? 5 : .15)
  }, [metric, values])
  const max = useMemo(() => {
    const ceiling = metric === 'rpm' ? 1520 : metric === 'temperature' ? 78 : metric === 'rms' ? 6 : 10
    return Math.max(ceiling, ...values) + (metric === 'rpm' ? 5 : .15)
  }, [metric, values])
  const points = values.map((value, index) => `${(index / Math.max(values.length - 1, 1)) * 100},${100 - ((value - min) / (max - min)) * 100}`).join(' ')
  const baseline = machine.baseline[metric === 'temperature' ? 'temperature' : metric === 'rpm' ? 'rpm' : metric === 'kurtosis' ? 'kurtosis' : 'rms']
  const baselineY = 100 - (((baseline[0] + baseline[1]) / 2 - min) / (max - min)) * 100
  const rawMarkerY = 100 - ((latest - min) / ((max - min) || 1)) * 100
  const markerY = Number.isFinite(rawMarkerY) ? rawMarkerY : 50

  return <div className="live-series-card">
    <div className="live-series-toolbar">
      <div><div className="eyebrow">Streaming telemetry</div><strong>{labels[metric]}</strong><span className="live-series-value">{formatValue(latest, metric)} {units[metric]}</span></div>
      {showControls && <div className="live-series-controls">
        <select aria-label="Signal metric" value={metric} onChange={(event) => setMetric(event.target.value as MetricKey)}>{Object.entries(labels).map(([key, label]) => <option key={key} value={key}>{label}</option>)}</select>
        <div className="segmented-control" role="group" aria-label="Chart time range">{([30, 60, 120] as const).map((item) => <button key={item} className={range === item ? 'active' : ''} onClick={() => setRange(item)}>{item}s</button>)}</div>
      </div>}
    </div>
    <div className="live-series-plot" style={{ height }}>
      <div className="chart-grid" />
      <svg viewBox="0 0 100 100" preserveAspectRatio="none" aria-label={`${labels[metric]} live chart`} role="img">
        <line x1="0" x2="100" y1={baselineY} y2={baselineY} stroke="var(--chart-amber)" strokeDasharray="1.5 2" opacity=".55" />
        <polyline points={`0,${baselineY} ${points}`} fill="none" stroke="var(--primary)" strokeOpacity=".12" strokeWidth="5" vectorEffect="non-scaling-stroke" />
        <polyline points={points} fill="none" stroke="var(--primary)" strokeWidth="2.3" vectorEffect="non-scaling-stroke" strokeLinejoin="round" strokeLinecap="round" />
        <motion.circle initial={{ cy: markerY }} animate={{ cy: markerY }} transition={{ type: 'spring', stiffness: 140, damping: 24 }} cx="100" cy={markerY} r="2.2" fill="var(--primary)" vectorEffect="non-scaling-stroke" />
      </svg>
      <div className="chart-axis top">{formatValue(max, metric)}</div><div className="chart-axis bottom">{formatValue(min, metric)}</div>
      <span className="chart-live-label"><i /> {machine.status === 'STOPPED' ? 'PAUSED' : `LIVE · ${new Date(visible.at(-1)?.timestamp ?? Date.now()).toLocaleTimeString([], { minute: '2-digit', second: '2-digit' })}`}</span>
    </div>
    <div className="live-series-footer"><span><i className="legend-dot blue" /> Actual signal</span><span><i className="legend-line" /> Baseline region</span><span>{range}s rolling window</span></div>
  </div>
}

export default LiveTimeSeries
