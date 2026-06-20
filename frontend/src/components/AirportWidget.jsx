import { Plane } from 'lucide-react'
import WidgetCard from './WidgetCard'

export default function AirportWidget({ airports }) {
  if (!airports || airports.length === 0) {
    return <WidgetCard title="Nearest Airports" icon={Plane} empty emptyMsg="No airport data available" />
  }

  return (
    <WidgetCard title="Nearest Airports" icon={Plane}>
      <div className="space-y-2">
        {airports.map((a, i) => (
          <div
            key={i}
            className={`flex items-center gap-3 p-2.5 rounded-lg ${i === 0 ? 'bg-surface-raised border border-accent/20' : 'bg-surface-raised'}`}
          >
            <div className="w-10 h-9 rounded-lg bg-border flex items-center justify-center flex-shrink-0">
              <span className="text-xs font-semibold text-accent">{a.iata_code || '—'}</span>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium text-text-primary truncate">{a.name}</p>
              <p className="text-[10px] text-text-muted">{a.city}{a.state ? `, ${a.state}` : ''}</p>
            </div>
            <div className="text-right flex-shrink-0">
              <p className="text-sm font-semibold text-accent tabular-nums">{a.distance_km}</p>
              <p className="text-[10px] text-text-muted">km</p>
            </div>
          </div>
        ))}
      </div>
    </WidgetCard>
  )
}
