import { Download, Printer } from 'lucide-react'

export default function ReportExport({ data }) {
  const handleExportJson = () => {
    const json = JSON.stringify(data, null, 2)
    const blob = new Blob([json], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    const loc = data.location?.display_address?.split(',')[0] || 'location'
    const date = new Date().toISOString().slice(0, 10)
    a.download = `businessgeo-report-${loc.replace(/\s+/g, '-')}-${date}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  const handlePrint = () => window.print()

  return (
    <div className="flex gap-2">
      <button
        onClick={handleExportJson}
        className="flex items-center gap-1.5 px-2.5 py-2 bg-surface border border-border hover:border-accent hover:text-accent rounded-lg text-xs text-text-secondary transition-colors"
        title="Export report as JSON"
      >
        <Download className="w-3.5 h-3.5" />
        <span className="hidden lg:inline">Export JSON</span>
      </button>
      <button
        onClick={handlePrint}
        className="flex items-center gap-1.5 px-2.5 py-2 bg-surface border border-border hover:border-accent hover:text-accent rounded-lg text-xs text-text-secondary transition-colors"
        title="Print report"
      >
        <Printer className="w-3.5 h-3.5" />
        <span className="hidden lg:inline">Print Report</span>
      </button>
    </div>
  )
}
