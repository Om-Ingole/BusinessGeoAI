import { Activity } from 'lucide-react'
import WidgetCard from './WidgetCard'

const CATEGORY_LABELS = {
  hospitals: 'Hospitals', schools: 'Schools', pharmacies: 'Pharmacies',
  banks: 'Banks', supermarkets: 'Markets', corporates: 'Offices',
  housing: 'Housing', bus_stops: 'Bus Stops', metro: 'Metro', railway: 'Railway',
}

export default function FootfallWidget({ footfall, poi }) {
  if (!footfall) {
    return <WidgetCard title="Footfall Proxy" icon={Activity} empty emptyMsg="No footfall data available" />
  }

  const score = footfall.poi_density_score || 0
  const color = score >= 70 ? 'var(--success)' : score >= 40 ? 'var(--warning)' : 'var(--danger)'

  // Top 3 categories by count from poi
  const topCategories = poi
    ? Object.entries(poi)
        .filter(([k, v]) => Array.isArray(v) && CATEGORY_LABELS[k])
        .map(([k, v]) => ({ key: k, label: CATEGORY_LABELS[k], count: v.length }))
        .filter(c => c.count > 0)
        .sort((a, b) => b.count - a.count)
        .slice(0, 3)
    : []

  return (
    <WidgetCard title="Footfall Proxy" icon={Activity}>
      <div className="flex items-baseline gap-1 mb-2">
        <span className="text-3xl font-bold tabular-nums" style={{ color }}>{score.toFixed(0)}</span>
        <span className="text-text-muted text-sm">/100 density</span>
      </div>
      <div className="h-1.5 bg-border rounded-full overflow-hidden mb-3">
        <div className="h-full rounded-full transition-all duration-700" style={{ width: `${score}%`, background: color }} />
      </div>
      <p className="text-xs text-text-secondary mb-3">
        <span className="text-text-primary">{footfall.total_amenities}</span> total amenities in radius
        {footfall.peak_hours_est && <> · peak {footfall.peak_hours_est}</>}
      </p>
      {topCategories.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {topCategories.map(c => (
            <span key={c.key} className="text-[11px] px-2 py-0.5 rounded-full bg-surface-raised border border-border text-text-secondary">
              {c.label} · {c.count}
            </span>
          ))}
        </div>
      )}
    </WidgetCard>
  )
}
