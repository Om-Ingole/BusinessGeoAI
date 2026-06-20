import { useState } from 'react'
import { Search, Loader2 } from 'lucide-react'

export default function SearchBar({ onSearch, isLoading, radius = 1 }) {
  const [query, setQuery] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!query.trim()) return

    // Detect if lat,lon format
    const latLonMatch = query.match(/^(-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)$/)
    if (latLonMatch) {
      onSearch({ lat: parseFloat(latLonMatch[1]), lon: parseFloat(latLonMatch[2]), radius_km: radius })
    } else {
      onSearch({ query: query.trim(), radius_km: radius })
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex gap-2 w-full items-center">
      <div className="flex-1 relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search address, pin code, or lat,lon"
          className="w-full pl-9 pr-3 py-2 bg-surface border border-border rounded-lg text-text-primary placeholder-text-muted focus:outline-none focus:border-accent transition-colors text-sm"
        />
      </div>
      <button
        type="submit"
        disabled={isLoading || !query.trim()}
        className="px-4 py-2 bg-accent text-bg-primary font-semibold rounded-lg hover:bg-teal-400 disabled:opacity-50 disabled:cursor-not-allowed transition-all text-sm whitespace-nowrap flex items-center gap-1.5"
      >
        {isLoading ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin" />
            Analyzing
          </>
        ) : 'Analyze'}
      </button>
    </form>
  )
}
