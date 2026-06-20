import { Navigation } from 'lucide-react'
import WidgetCard from './WidgetCard'

export default function TransportWidget({ poi, railwayStations }) {
  const busStops = poi?.bus_stops || []
  const metro = poi?.metro || []
  const railway = poi?.railway || []
  const stations = railwayStations || []

  const sections = [
    { label: 'Bus Stops', items: busStops.slice(0, 3), nameKey: 'name' },
    { label: 'Metro', items: metro.slice(0, 3), nameKey: 'name' },
    { label: 'Railway', items: stations.slice(0, 3), nameKey: 'station_name' },
    { label: 'OSM Railway', items: railway.slice(0, 2), nameKey: 'name' },
  ]

  const hasAny = sections.some(s => s.items.length > 0)

  return (
    <WidgetCard title="Transport Access" icon={Navigation} empty={!hasAny} emptyMsg="No transport data in radius">
      <div className="space-y-3">
        {sections.filter(s => s.items.length > 0).map(({ label, items, nameKey }) => (
          <div key={label}>
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-xs font-medium text-text-secondary">{label}</span>
              <span className="text-[10px] text-text-muted">{items.length}</span>
            </div>
            <div className="space-y-1">
              {items.map((item, i) => (
                <div key={i} className="flex items-center justify-between text-xs bg-surface-raised rounded-lg px-2.5 py-1.5">
                  <span className="text-text-primary truncate flex-1">{item[nameKey] || 'Unnamed'}</span>
                  {item.distance_km && (
                    <span className="text-text-muted ml-2 flex-shrink-0 tabular-nums">{item.distance_km} km</span>
                  )}
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </WidgetCard>
  )
}
