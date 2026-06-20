import { Users } from 'lucide-react'
import WidgetCard from './WidgetCard'

function fmt(n) {
  if (!n) return 'N/A'
  if (n >= 1e7) return `${(n / 1e7).toFixed(1)}Cr`
  if (n >= 1e5) return `${(n / 1e5).toFixed(1)}L`
  if (n >= 1e3) return `${(n / 1e3).toFixed(0)}K`
  return n.toString()
}

function Stat({ label, value }) {
  return (
    <div className="bg-surface-raised rounded-lg px-2.5 py-2">
      <p className="text-[10px] text-text-muted">{label}</p>
      <p className="text-sm font-semibold text-text-primary tabular-nums">{value}</p>
    </div>
  )
}

export default function DemographicsWidget({ demographics }) {
  if (!demographics) {
    return <WidgetCard title="Demographics" icon={Users} empty emptyMsg="No demographic data available" />
  }

  const d = demographics
  const urbanPct = d.urban_pct != null ? Math.min(100, Math.max(0, d.urban_pct)) : null

  return (
    <WidgetCard title="Demographics" icon={Users}>
      <div className="grid grid-cols-3 gap-2 mb-3">
        <Stat label="Population" value={fmt(d.total_population)} />
        <Stat label="Literacy" value={d.literacy_rate ? `${d.literacy_rate}%` : 'N/A'} />
        <Stat label="Sex ratio" value={d.sex_ratio || 'N/A'} />
      </div>
      {urbanPct != null && (
        <div>
          <div className="flex items-center justify-between text-xs mb-1">
            <span className="text-text-muted">Urban</span>
            <span className="text-text-secondary tabular-nums">{urbanPct}%</span>
          </div>
          <div className="h-1.5 bg-border rounded-full overflow-hidden">
            <div className="h-full bg-accent rounded-full transition-all duration-700" style={{ width: `${urbanPct}%` }} />
          </div>
        </div>
      )}
      <p className="text-xs text-text-muted mt-3">{d.district}{d.state ? `, ${d.state}` : ''}</p>
    </WidgetCard>
  )
}
