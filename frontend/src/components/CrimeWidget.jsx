import { Shield } from 'lucide-react'
import WidgetCard from './WidgetCard'

export default function CrimeWidget({ crime }) {
  if (!crime) {
    return <WidgetCard title="Crime & Safety" icon={Shield} empty emptyMsg="No crime data available for this district" />
  }

  const latest = crime.latest_crimes_per_lakh
  const latestRecord = (crime.records || []).slice(-1)[0]
  const year = latestRecord?.year || crime.year

  const color = latest == null ? 'var(--text-muted)'
    : latest < 100 ? 'var(--success)'
    : latest <= 300 ? 'var(--warning)'
    : 'var(--danger)'
  const severity = latest == null ? 'N/A'
    : latest < 100 ? 'Low'
    : latest <= 300 ? 'Moderate'
    : 'High'

  return (
    <WidgetCard title="Crime & Safety" icon={Shield}>
      <div className="flex items-end gap-3 mb-2">
        <div className="flex items-baseline gap-1">
          <span className="text-4xl font-bold tabular-nums" style={{ color }}>{latest?.toFixed(0) ?? 'N/A'}</span>
          <span className="text-text-muted text-xs">per lakh</span>
        </div>
        <span className="text-xs px-2 py-0.5 mb-1.5 rounded-full font-medium" style={{ background: color + '22', color }}>
          {severity} risk
        </span>
      </div>
      <p className="text-xs text-text-secondary">
        {crime.district}{crime.state ? `, ${crime.state}` : ''}
        {year && <span className="text-text-muted"> · {year}</span>}
      </p>
    </WidgetCard>
  )
}
