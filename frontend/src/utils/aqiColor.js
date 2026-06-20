export function aqiColor(value) {
  if (!value) return '#64748b'
  if (value <= 50) return '#22c55e'
  if (value <= 100) return '#84cc16'
  if (value <= 200) return '#f59e0b'
  if (value <= 300) return '#f97316'
  if (value <= 400) return '#ef4444'
  return '#7c3aed'
}

export function aqiLabel(value) {
  if (!value) return 'N/A'
  if (value <= 50) return 'Good'
  if (value <= 100) return 'Satisfactory'
  if (value <= 200) return 'Moderate'
  if (value <= 300) return 'Poor'
  if (value <= 400) return 'Very Poor'
  return 'Severe'
}

export function aqiBg(value) {
  if (!value) return 'bg-slate-700'
  if (value <= 50) return 'bg-green-500'
  if (value <= 100) return 'bg-lime-500'
  if (value <= 200) return 'bg-amber-500'
  if (value <= 300) return 'bg-orange-500'
  if (value <= 400) return 'bg-red-500'
  return 'bg-purple-700'
}
