import { useState, useCallback, Suspense, lazy } from 'react'
import { MapPin, Building2, MessageSquare, TrendingUp, Train, Wind, Users, AlertTriangle, X } from 'lucide-react'
import { useLocationAnalysis } from './hooks/useLocationAnalysis'
import Header from './components/Header'
import MapView from './components/MapView'
import ScoreCard from './components/ScoreCard'
import AqiWidget from './components/AqiWidget'
import CrimeWidget from './components/CrimeWidget'
import DemographicsWidget from './components/DemographicsWidget'
import TransportWidget from './components/TransportWidget'
import AirportWidget from './components/AirportWidget'
import MsmeWidget from './components/MsmeWidget'
import PoiSummary from './components/PoiSummary'
import FootfallWidget from './components/FootfallWidget'
import AgentInsightsWidget from './components/AgentInsightsWidget'
import AnalysisProgress from './components/AnalysisProgress'

const ChatPanel = lazy(() => import('./components/ChatPanel'))

const SAMPLE_LOCATIONS = [
  'Koregaon Park, Pune',
  'Connaught Place, New Delhi',
  'Bandra West, Mumbai',
  'Indiranagar, Bengaluru',
  'T Nagar, Chennai',
]

const FEATURES = [
  { icon: Building2, label: 'Google Places' },
  { icon: MessageSquare, label: 'AI Chat' },
  { icon: TrendingUp, label: 'Competitor Signals' },
  { icon: Train, label: 'Transport Access' },
  { icon: Wind, label: 'AQI + Safety' },
  { icon: Users, label: 'Demographics' },
]

function EmptyState({ onSearch }) {
  return (
    <div className="flex-1 flex items-start justify-center pt-16 px-4 overflow-y-auto">
      <div className="max-w-xl w-full text-center">
        <MapPin className="w-12 h-12 text-accent mx-auto mb-4" />
        <h1 className="text-2xl font-semibold text-text-primary mb-2">
          Analyze any business location in India
        </h1>
        <p className="text-text-secondary text-sm mb-8">
          Search a place to evaluate footfall, nearby businesses, transport access, safety, AQI, and demographics.
        </p>
        <div className="flex flex-wrap gap-2 justify-center mb-6">
          {SAMPLE_LOCATIONS.map(loc => (
            <button
              key={loc}
              onClick={() => onSearch({ query: loc, radius_km: 1 })}
              className="px-3 py-1.5 bg-surface border border-border rounded-lg text-sm text-text-secondary hover:border-accent hover:text-accent transition-colors"
            >
              {loc}
            </button>
          ))}
        </div>
        <div className="flex flex-wrap gap-2 justify-center">
          {FEATURES.map(({ icon: Icon, label }) => (
            <span key={label} className="flex items-center gap-1.5 px-3 py-1.5 bg-surface border border-border rounded-full text-xs text-text-muted">
              <Icon className="w-3 h-3" /> {label}
            </span>
          ))}
        </div>
      </div>
    </div>
  )
}

export default function App() {
  const [radiusKm, setRadiusKm] = useState(1)
  const [businessType, setBusinessType] = useState('')
  const [liveData, setLiveData] = useState(null)
  const [dismissWarning, setDismissWarning] = useState(false)
  const { mutate, data: fetchedData, isPending, error, isError } = useLocationAnalysis()

  // data can come from search OR from a chat-triggered analysis
  const data = liveData || fetchedData

  const handleSearch = useCallback((params) => {
    setRadiusKm(params.radius_km || 1)
    setLiveData(null)
    setDismissWarning(false)
    mutate({ ...params, business_type: businessType || undefined })
  }, [mutate, businessType])

  // Called when ADK chat triggers a new analysis
  const handleChatReportUpdate = useCallback((updatedReport) => {
    setLiveData(updatedReport)
    setDismissWarning(false)
    const loc = updatedReport.location
    if (loc?.lat) setRadiusKm(1)
  }, [])

  const isPartial = data?.partial
  const warnings = data?.warnings || []
  const showWarning = data && !dismissWarning && (isPartial || warnings.length > 0)

  return (
    <div className="flex flex-col h-screen overflow-hidden bg-bg-primary" style={{ fontFamily: 'Inter, sans-serif' }}>
      <Header
        onSearch={handleSearch}
        isLoading={isPending}
        data={data}
        businessType={businessType}
        onBusinessTypeChange={setBusinessType}
        radius={radiusKm}
        onRadiusChange={setRadiusKm}
      />

      {showWarning && (
        <div className="bg-warning/10 border-b border-warning/30 px-4 py-2 flex items-center gap-2 text-warning text-xs flex-shrink-0">
          <AlertTriangle className="w-3.5 h-3.5 flex-shrink-0" />
          <span className="truncate">Partial data: {warnings.join('; ') || 'Some sources unavailable'}</span>
          <button onClick={() => setDismissWarning(true)} className="ml-auto hover:text-warning/70 flex-shrink-0">
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      <div className="flex-1 flex overflow-hidden flex-col md:flex-row">
        {/* Empty state */}
        {!data && !isPending && !isError && <EmptyState onSearch={handleSearch} />}

        {/* Loading */}
        {isPending && (
          <div className="flex-1 flex items-center justify-center">
            <AnalysisProgress />
          </div>
        )}

        {/* Error */}
        {isError && !data && (
          <div className="flex-1 flex items-center justify-center px-4">
            <div className="bg-danger/10 border border-danger/40 rounded-lg p-6 max-w-md text-center">
              <p className="text-danger font-semibold mb-2">Analysis Failed</p>
              <p className="text-text-secondary text-sm">{error?.response?.data?.detail || error?.message || 'Unknown error'}</p>
              <p className="text-xs text-text-muted mt-2">Try adding the city/state name for better geocoding.</p>
            </div>
          </div>
        )}

        {/* Dashboard */}
        {data && (
          <>
            {/* Left panel */}
            <div className="w-full md:w-72 flex-shrink-0 overflow-y-auto border-b md:border-b-0 md:border-r border-border bg-bg-secondary p-3 space-y-3">
              <ScoreCard
                score={data.viability_score}
                breakdown={data.score_breakdown}
                dataConfidence={data.data_confidence ?? data.agent_insights?.confidence}
              />
              {data.agent_insights && <AgentInsightsWidget insights={data.agent_insights} />}
              <PoiSummary poi={data.poi} radiusKm={radiusKm} />
              <FootfallWidget footfall={data.footfall_proxy} poi={data.poi} />
            </div>

            {/* Center: map */}
            <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
              <div className="flex items-center justify-between px-4 py-2 border-b border-border bg-bg-secondary flex-shrink-0">
                <div className="min-w-0">
                  <h2 className="text-sm font-medium text-text-primary truncate">
                    {data.location.display_address?.split(',').slice(0, 3).join(', ')}
                  </h2>
                  <p className="text-[10px] text-text-muted truncate">
                    {data.location.lat?.toFixed(4)}, {data.location.lon?.toFixed(4)}
                    {data.location.district && ` · ${data.location.district}`}
                    {data.location.state && `, ${data.location.state}`}
                    {data.location.pin_code && ` · PIN ${data.location.pin_code}`}
                  </p>
                </div>
                {data.generated_at && (
                  <span className="text-[10px] text-text-muted flex-shrink-0 ml-2 hidden lg:block">
                    {new Date(data.generated_at).toLocaleString('en-IN')}
                  </span>
                )}
              </div>
              <div className="flex-1 min-h-[360px] md:min-h-0">
                <MapView
                  location={data.location}
                  poi={data.poi}
                  radiusKm={radiusKm}
                  provider={data.provider}
                />
              </div>
            </div>

            {/* Right panel */}
            <div className="w-full md:w-80 flex-shrink-0 overflow-y-auto border-t md:border-t-0 md:border-l border-border bg-bg-secondary p-3 space-y-3">
              <Suspense fallback={null}>
                <ChatPanel
                  data={data}
                  businessType={businessType}
                  onReportUpdate={handleChatReportUpdate}
                />
              </Suspense>
              <AqiWidget aqi={data.aqi} />
              <CrimeWidget crime={data.crime} />
              <DemographicsWidget demographics={data.demographics} />
              <TransportWidget poi={data.poi} railwayStations={data.railway_stations} />
              <AirportWidget airports={data.airports} />
              <MsmeWidget sectors={data.msme_sectors} />
            </div>
          </>
        )}
      </div>
    </div>
  )
}
