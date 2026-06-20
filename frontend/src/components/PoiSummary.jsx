import { Grid3x3 } from 'lucide-react'
import WidgetCard from './WidgetCard'

const POI_CONFIG = [
  { key: 'hospitals', label: 'Hospitals', color: '#ef4444' },
  { key: 'schools', label: 'Schools', color: '#3b82f6' },
  { key: 'pharmacies', label: 'Pharmacies', color: '#f97316' },
  { key: 'banks', label: 'Banks/ATM', color: '#8b5cf6' },
  { key: 'supermarkets', label: 'Markets', color: '#84cc16' },
  { key: 'corporates', label: 'Offices', color: '#f59e0b' },
  { key: 'housing', label: 'Housing', color: '#94a3b8' },
  { key: 'bus_stops', label: 'Bus Stops', color: '#06b6d4' },
]

export default function PoiSummary({ poi, radiusKm }) {
  return (
    <WidgetCard
      title="Nearby Places"
      icon={Grid3x3}
      empty={!poi}
      emptyMsg="No POI data available"
      action={<span className="text-[10px] text-text-muted">within {radiusKm} km</span>}
    >
      <div className="grid grid-cols-2 gap-2">
        {POI_CONFIG.map(({ key, label, color }) => {
          const count = poi?.[key]?.length || 0
          return (
            <div key={key} className="flex items-center justify-between bg-surface-raised rounded-lg px-2.5 py-2">
              <div className="flex items-center gap-2 min-w-0">
                <span className="w-2 h-2 rounded-full flex-shrink-0" style={{ background: color }} />
                <span className="text-xs text-text-secondary truncate">{label}</span>
              </div>
              <span className="text-sm font-semibold text-text-primary tabular-nums">{count}</span>
            </div>
          )
        })}
      </div>
    </WidgetCard>
  )
}
