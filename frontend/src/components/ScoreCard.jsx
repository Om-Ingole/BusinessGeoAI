import { useEffect, useRef, useState } from 'react'
import { BarChart2 } from 'lucide-react'
import WidgetCard from './WidgetCard'

const LABELS = {
  footfall_proxy: 'Footfall Proxy',
  transport_access: 'Transport',
  demographics: 'Demographics',
  poi_density: 'POI Density',
  crime_safety: 'Crime Safety',
  air_quality: 'Air Quality',
  business_density: 'Business',
  growth_potential: 'Growth',
}

function scoreBand(score) {
  if (score >= 8.5) return { label: 'Excellent', color: 'var(--success)' }
  if (score >= 7) return { label: 'Good', color: 'var(--accent)' }
  if (score >= 5) return { label: 'Average', color: 'var(--warning)' }
  return { label: 'Poor', color: 'var(--danger)' }
}

function useCountUp(target, duration = 800) {
  const [value, setValue] = useState(0)
  const rafRef = useRef(null)
  useEffect(() => {
    const start = performance.now()
    const tick = (now) => {
      const t = Math.min((now - start) / duration, 1)
      const eased = 1 - Math.pow(1 - t, 3)
      setValue(target * eased)
      if (t < 1) rafRef.current = requestAnimationFrame(tick)
    }
    rafRef.current = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(rafRef.current)
  }, [target, duration])
  return value
}

function BreakdownRow({ label, value }) {
  return (
    <div className="flex items-center gap-2">
      <span className="text-xs text-text-muted w-28 truncate">{label}</span>
      <div className="flex-1 h-1.5 bg-border rounded-full overflow-hidden">
        <div
          className="h-full bg-accent rounded-full transition-all duration-700"
          style={{ width: `${(value / 10) * 100}%` }}
        />
      </div>
      <span className="text-xs text-text-secondary w-7 text-right">{value.toFixed(1)}</span>
    </div>
  )
}

export default function ScoreCard({ score = 0, breakdown, dataConfidence }) {
  const animated = useCountUp(score)
  const band = scoreBand(score)

  return (
    <WidgetCard title="Viability Score" icon={BarChart2}>
      <div className="flex items-end justify-between mb-3">
        <div className="flex items-baseline gap-1">
          <span className="text-4xl font-bold text-text-primary tabular-nums">{animated.toFixed(1)}</span>
          <span className="text-text-muted text-lg">/10</span>
        </div>
        <span
          className="text-xs px-2 py-0.5 rounded-full font-medium"
          style={{ background: band.color + '22', color: band.color }}
        >
          {band.label}
        </span>
      </div>

      {typeof dataConfidence === 'number' && (
        <div className="mb-3">
          <span className="text-[10px] px-2 py-0.5 rounded-full border border-border text-text-muted">
            {Math.round(dataConfidence * 100)}% data confidence
          </span>
        </div>
      )}

      {breakdown && (
        <div className="space-y-2">
          {Object.entries(breakdown).map(([k, v]) => (
            <BreakdownRow key={k} label={LABELS[k] || k} value={Number(v) || 0} />
          ))}
        </div>
      )}
    </WidgetCard>
  )
}
