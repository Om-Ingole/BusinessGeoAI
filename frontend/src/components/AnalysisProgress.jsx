import { useEffect, useState } from 'react'

const STEPS = [
  { label: 'Resolving location coordinates',  detail: 'Geocoding via Nominatim / Google Maps',         duration: 2500 },
  { label: 'Checking analysis cache',          detail: 'Looking for a recent result (24 hr TTL)',        duration: 800  },
  { label: 'Fetching nearby places',           detail: 'Querying OpenStreetMap Overpass / Google Places', duration: 9000 },
  { label: 'Checking air quality',             detail: 'CPCB real-time AQI stations',                   duration: 3000 },
  { label: 'Loading transport data',           detail: 'Airports, metro & railway stations',             duration: 1500 },
  { label: 'Analyzing demographics & crime',   detail: 'Census 2011 · NCRB district data',              duration: 1500 },
  { label: 'Computing viability score',        detail: '8-dimension weighted model',                     duration: 800  },
  { label: 'Generating insights',              detail: 'Risks, opportunities & use-case analysis',       duration: 800  },
]

const TOTAL_MS = STEPS.reduce((s, st) => s + st.duration, 0)

export default function AnalysisProgress() {
  const [stepIndex, setStepIndex] = useState(0)
  const [elapsed, setElapsed]     = useState(0)

  // Advance steps on a timer derived from each step's duration
  useEffect(() => {
    let current = 0
    const timers = []

    STEPS.forEach((step, i) => {
      const t = setTimeout(() => setStepIndex(i), current)
      timers.push(t)
      current += step.duration
    })

    return () => timers.forEach(clearTimeout)
  }, [])

  // Smooth elapsed ticker for the progress bar
  useEffect(() => {
    const start = Date.now()
    const id = setInterval(() => {
      const ms = Date.now() - start
      setElapsed(Math.min(ms, TOTAL_MS))
    }, 80)
    return () => clearInterval(id)
  }, [])

  const progress = Math.min((elapsed / TOTAL_MS) * 100, 97) // never reach 100 until real done

  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] px-4">
      {/* Spinner */}
      <div className="relative w-14 h-14 mb-6">
        <div className="absolute inset-0 rounded-full border-2 border-accent/20 pulse-ring" />
        <div className="w-14 h-14 rounded-full border-2 border-t-accent border-border animate-spin" />
      </div>

      <p className="text-text-primary font-semibold text-sm mb-4 text-center">
        BusinessGeo AI is analyzing your location
      </p>

      {/* Active step */}
      <p className="text-text-primary font-medium text-sm mb-1 text-center transition-all duration-300">
        {STEPS[stepIndex].label}&hellip;
      </p>
      <p className="text-text-secondary/70 text-xs mb-6 text-center">
        {STEPS[stepIndex].detail}
      </p>

      {/* Progress bar */}
      <div className="w-64 h-1.5 bg-border rounded-full overflow-hidden mb-6">
        <div
          className="h-full bg-accent rounded-full transition-all duration-100"
          style={{ width: `${progress}%` }}
        />
      </div>

      {/* Step list */}
      <div className="flex flex-col gap-1.5 w-64">
        {STEPS.map((step, i) => {
          const done    = i < stepIndex
          const active  = i === stepIndex
          const pending = i > stepIndex
          return (
            <div key={i} className={`flex items-center gap-2 text-xs transition-opacity duration-300 ${pending ? 'opacity-30' : 'opacity-100'}`}>
              {/* Icon */}
              <span className="w-4 h-4 flex-shrink-0 flex items-center justify-center">
                {done && (
                  <svg className="w-3.5 h-3.5 text-accent" viewBox="0 0 12 12" fill="none">
                    <path d="M2 6l3 3 5-5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                )}
                {active && (
                  <span className="w-2 h-2 rounded-full bg-accent animate-pulse" />
                )}
                {pending && (
                  <span className="w-1.5 h-1.5 rounded-full bg-border" />
                )}
              </span>
              <span className={active ? 'text-accent font-medium' : done ? 'text-text-secondary' : 'text-text-secondary/50'}>
                {step.label}
              </span>
            </div>
          )
        })}
      </div>
    </div>
  )
}
