import { MapPin } from 'lucide-react'
import SearchBar from './SearchBar'
import ReportExport from './ReportExport'

const BUSINESS_TYPES = [
  { value: '', label: 'Any business' },
  { value: 'retail', label: 'Retail' },
  { value: 'cafe', label: 'Cafe' },
  { value: 'clinic', label: 'Clinic' },
  { value: 'pharmacy', label: 'Pharmacy' },
  { value: 'restaurant', label: 'Restaurant' },
  { value: 'office', label: 'Office' },
  { value: 'supermarket', label: 'Supermarket' },
  { value: 'qsr', label: 'QSR' },
  { value: 'education', label: 'Education' },
]

const RADIUS_OPTIONS = [0.5, 1, 2, 5]

const PROVIDER_STYLE = {
  google: 'border-accent/40 text-accent bg-accent/10',
  osm: 'border-accent-blue/40 text-accent-blue bg-accent-blue/10',
  hybrid: 'border-purple-500/40 text-purple-300 bg-purple-500/10',
  fallback: 'border-warning/40 text-warning bg-warning/10',
}
const PROVIDER_LABEL = { google: 'Google', osm: 'OSM', hybrid: 'Hybrid', fallback: 'Fallback' }

export default function Header({
  onSearch,
  isLoading,
  data,
  businessType,
  onBusinessTypeChange,
  radius,
  onRadiusChange,
}) {
  const provider = data?.provider

  return (
    <header className="h-16 flex-shrink-0 border-b border-border bg-bg-secondary flex items-center gap-3 px-4">
      {/* Brand */}
      <div className="flex items-center gap-2 flex-shrink-0">
        <MapPin className="w-6 h-6 text-accent" />
        <div className="leading-tight">
          <h1 className="text-base font-semibold text-text-primary">BusinessGeo AI</h1>
          <p className="hidden lg:block text-[10px] text-text-muted -mt-0.5">
            AI location intelligence for business decisions
          </p>
        </div>
      </div>

      {/* Search (center) */}
      <div className="flex-1 max-w-2xl mx-auto">
        <SearchBar onSearch={onSearch} isLoading={isLoading} radius={radius} />
      </div>

      {/* Controls (right) */}
      <div className="flex items-center gap-2 flex-shrink-0">
        <select
          value={radius}
          onChange={(e) => onRadiusChange(Number(e.target.value))}
          className="hidden sm:block px-2 py-2 bg-surface border border-border rounded-lg text-text-primary focus:outline-none focus:border-accent transition-colors text-xs cursor-pointer"
          title="Search radius"
        >
          {RADIUS_OPTIONS.map(r => (
            <option key={r} value={r}>{r} km</option>
          ))}
        </select>

        <select
          value={businessType}
          onChange={(e) => onBusinessTypeChange(e.target.value)}
          className="hidden sm:block px-2 py-2 bg-surface border border-border rounded-lg text-text-primary focus:outline-none focus:border-accent transition-colors text-xs cursor-pointer"
          title="Business type"
        >
          {BUSINESS_TYPES.map(t => (
            <option key={t.value} value={t.value}>{t.label}</option>
          ))}
        </select>

        {provider && (
          <span className={`hidden md:inline-block text-[10px] px-2 py-1 rounded-full border font-medium ${PROVIDER_STYLE[provider] || PROVIDER_STYLE.osm}`}>
            {PROVIDER_LABEL[provider] || provider}
          </span>
        )}

        {data && <ReportExport data={data} />}
      </div>
    </header>
  )
}
