import { MapContainer, TileLayer, Marker, Popup, Circle, useMap } from 'react-leaflet'
import L from 'leaflet'
import { useEffect, useMemo, useState } from 'react'

function getCategoryColor(cat) {
  const map = {
    hospitals: '#ef4444', pharmacies: '#f97316', schools: '#3b82f6',
    banks: '#8b5cf6', bus_stops: '#06b6d4', metro: '#06b6d4',
    railway: '#0ea5e9', supermarkets: '#84cc16', corporates: '#f59e0b',
    housing: '#94a3b8',
  }
  return map[cat] || '#64748b'
}

function getCategoryInitial(cat) {
  const map = {
    hospitals: 'H', pharmacies: 'Rx', schools: 'Sc', banks: 'Bk',
    bus_stops: 'Bu', metro: 'M', railway: 'Ry', supermarkets: 'Sm',
    corporates: 'Co', housing: 'Ho',
  }
  return map[cat] || '?'
}

function createMarkerIcon(category) {
  const color = getCategoryColor(category)
  const initial = getCategoryInitial(category)
  return L.divIcon({
    className: '',
    html: `<div style="width:28px;height:28px;border-radius:50%;background:${color};border:2px solid rgba(255,255,255,0.3);display:flex;align-items:center;justify-content:center;color:white;font-size:9px;font-weight:700;font-family:sans-serif;box-shadow:0 2px 4px rgba(0,0,0,0.4)">${initial}</div>`,
    iconSize: [28, 28],
    iconAnchor: [14, 14],
    popupAnchor: [0, -14],
  })
}

function createCenterIcon() {
  return L.divIcon({
    className: '',
    html: `<div style="position:relative;width:20px;height:20px">
      <div class="center-pulse-ring" style="position:absolute;inset:0;border-radius:50%;background:#14b8a6;opacity:0.5"></div>
      <div style="position:absolute;inset:4px;border-radius:50%;background:#14b8a6;border:2px solid #f8fafc;box-shadow:0 0 10px #14b8a6"></div>
    </div>`,
    iconSize: [20, 20],
    iconAnchor: [10, 10],
  })
}

function buildPopupHtml(item, category) {
  const providerBadge = item.provider === 'google'
    ? `<span style="background:#0d9488;color:white;font-size:9px;padding:1px 5px;border-radius:3px;margin-left:4px">Google</span>`
    : `<span style="background:#2563eb;color:white;font-size:9px;padding:1px 5px;border-radius:3px;margin-left:4px">OSM</span>`

  const rating = item.rating ? `<div style="color:#94a3b8;font-size:11px">${'★'} ${item.rating}${item.user_rating_count ? ` · ${item.user_rating_count.toLocaleString()} reviews` : ''}</div>` : ''
  const status = item.business_status === 'OPERATIONAL' ? `<span style="color:#22c55e;font-size:10px">Operational</span>` : ''
  const address = item.address ? `<div style="color:#64748b;font-size:10px;margin-top:2px">${item.address.substring(0, 60)}${item.address.length > 60 ? '…' : ''}</div>` : ''
  const mapsLink = item.google_maps_uri ? `<a href="${item.google_maps_uri}" target="_blank" rel="noopener" style="color:#14b8a6;font-size:11px;display:block;margin-top:6px">Open in Google Maps →</a>` : ''
  const dist = item.distance_km ? `<div style="color:#94a3b8;font-size:11px">${item.distance_km.toFixed ? item.distance_km.toFixed(1) : item.distance_km} km away</div>` : ''

  return `<div style="min-width:200px;max-width:250px;font-family:system-ui,sans-serif;background:#111827;color:#f8fafc;border-radius:8px;overflow:hidden">
    <div style="padding:10px 12px">
      <div style="font-weight:600;font-size:13px;margin-bottom:2px">${item.name || 'Unknown'}${providerBadge}</div>
      <div style="color:#94a3b8;font-size:11px;text-transform:capitalize;margin-bottom:4px">${category.replace(/_/g, ' ')}</div>
      ${dist}${rating}${status}${address}${mapsLink}
    </div>
  </div>`
}

function RecenterMap({ lat, lon }) {
  const map = useMap()
  useEffect(() => {
    map.setView([lat, lon], 14, { animate: true })
  }, [lat, lon, map])
  return null
}

const CATEGORY_ORDER = [
  'hospitals', 'pharmacies', 'schools', 'banks', 'supermarkets',
  'corporates', 'housing', 'bus_stops', 'metro', 'railway',
]

export default function MapView({ location, poi, radiusKm = 1, provider }) {
  const lat = location?.lat || 20.5937
  const lon = location?.lon || 78.9629
  const radiusM = radiusKm * 1000

  // Categories present in the data, in a sensible order
  const presentCategories = useMemo(() => {
    if (!poi) return []
    return CATEGORY_ORDER.filter(c => Array.isArray(poi[c]) && poi[c].length > 0)
  }, [poi])

  const [activeCategories, setActiveCategories] = useState(() => new Set(presentCategories))

  // Reset active filters when the set of present categories changes
  useEffect(() => {
    setActiveCategories(new Set(presentCategories))
  }, [presentCategories])

  const toggleCategory = (cat) => {
    setActiveCategories(prev => {
      const next = new Set(prev)
      if (next.has(cat)) next.delete(cat)
      else next.add(cat)
      return next
    })
  }

  const totalPois = useMemo(() => {
    if (!poi) return 0
    return presentCategories.reduce((sum, c) => sum + (poi[c]?.length || 0), 0)
  }, [poi, presentCategories])

  return (
    <div className="flex flex-col h-full relative">
      <div className="flex-1 min-h-0 relative">
        <MapContainer
          center={[lat, lon]}
          zoom={14}
          className="w-full h-full"
          style={{ minHeight: '100%' }}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          {location && (
            <>
              <RecenterMap lat={lat} lon={lon} />
              <Circle
                center={[lat, lon]}
                radius={radiusM}
                pathOptions={{ color: '#14b8a6', fillColor: '#14b8a6', fillOpacity: 0.06, weight: 1.5 }}
              />
              <Marker position={[lat, lon]} icon={createCenterIcon()}>
                <Popup>
                  <div style={{ padding: '8px 10px', minWidth: 160 }}>
                    <div style={{ fontWeight: 600, fontSize: 13 }}>
                      {location.display_address?.split(',').slice(0, 2).join(', ') || 'Selected Location'}
                    </div>
                    <div style={{ color: '#94a3b8', fontSize: 11 }}>{lat.toFixed(4)}, {lon.toFixed(4)}</div>
                  </div>
                </Popup>
              </Marker>
            </>
          )}

          {poi && presentCategories.map(category =>
            activeCategories.has(category) &&
            poi[category].slice(0, 30).map((item, idx) => {
              if (!item.lat || !item.lon) return null
              return (
                <Marker
                  key={`${category}-${idx}`}
                  position={[item.lat, item.lon]}
                  icon={createMarkerIcon(category)}
                >
                  <Popup>
                    <div dangerouslySetInnerHTML={{ __html: buildPopupHtml(item, category) }} />
                  </Popup>
                </Marker>
              )
            })
          )}
        </MapContainer>

        {/* Filter chips (floating top-right) */}
        {presentCategories.length > 0 && (
          <div className="absolute top-3 right-3 z-[500] flex flex-col items-end gap-1 max-h-[70%] overflow-y-auto">
            {presentCategories.map(cat => {
              const active = activeCategories.has(cat)
              const color = getCategoryColor(cat)
              return (
                <button
                  key={cat}
                  onClick={() => toggleCategory(cat)}
                  style={{
                    background: active ? 'rgba(17,24,39,0.93)' : 'rgba(17,24,39,0.6)',
                    border: `1px solid ${active ? '#334155' : '#263244'}`,
                    color: active ? '#f8fafc' : '#64748b',
                    opacity: active ? 1 : 0.7,
                  }}
                  className="flex items-center gap-1.5 px-2 py-1 rounded-lg text-[10px] font-medium backdrop-blur transition-all"
                >
                  <span className="w-2 h-2 rounded-full flex-shrink-0" style={{ background: color, opacity: active ? 1 : 0.4 }} />
                  <span className="capitalize">{cat.replace(/_/g, ' ')}</span>
                  <span style={{ color: '#64748b' }}>{poi[cat]?.length}</span>
                </button>
              )
            })}
          </div>
        )}
      </div>

      {/* Toolbar (bottom) */}
      <div className="flex-shrink-0 flex items-center gap-2 px-3 py-2 text-xs" style={{ background: '#111827', borderTop: '1px solid #263244', color: '#94a3b8' }}>
        <span>Radius: <span style={{ color: '#f8fafc' }}>{radiusKm} km</span></span>
        <span style={{ color: '#64748b' }}>&middot;</span>
        <span><span style={{ color: '#f8fafc' }}>{totalPois}</span> places</span>
        {provider && (
          <>
            <span style={{ color: '#64748b' }}>&middot;</span>
            <span style={{ color: '#94a3b8', border: '1px solid #263244', borderRadius: 4, padding: '1px 5px', fontSize: 10, textTransform: 'uppercase' }}>{provider}</span>
          </>
        )}
      </div>
    </div>
  )
}
