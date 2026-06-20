import { Wind } from 'lucide-react'
import WidgetCard from './WidgetCard'
import { aqiColor, aqiLabel } from '../utils/aqiColor'

export default function AqiWidget({ aqi }) {
  if (!aqi || aqi.error) {
    return <WidgetCard title="Air Quality" icon={Wind} empty emptyMsg={aqi?.error || 'No AQI data available'} />
  }

  const value = aqi.pollutant_avg
  const color = aqiColor(value)
  const label = aqiLabel(value)

  return (
    <WidgetCard title="Air Quality" icon={Wind}>
      <div className="flex items-end gap-3 mb-3">
        <span className="text-4xl font-bold tabular-nums" style={{ color }}>{value?.toFixed(0) ?? 'N/A'}</span>
        <span className="text-xs px-2 py-0.5 mb-1.5 rounded-full font-medium" style={{ background: color + '22', color }}>
          {label}
        </span>
      </div>
      <div className="text-xs text-text-secondary space-y-0.5">
        <p><span className="text-text-primary">{aqi.pollutant_id || 'PM2.5'}</span> · {aqi.station || 'Nearest station'}</p>
        {aqi.city && <p className="text-text-muted">{aqi.city}</p>}
        {aqi.distance_km && <p className="text-text-muted">{aqi.distance_km} km from location</p>}
      </div>
    </WidgetCard>
  )
}
