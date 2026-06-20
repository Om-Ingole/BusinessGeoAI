import { Briefcase } from 'lucide-react'
import WidgetCard from './WidgetCard'

function fmt(n) {
  if (!n) return '0'
  if (n >= 1e5) return `${(n / 1e5).toFixed(1)}L`
  if (n >= 1e3) return `${(n / 1e3).toFixed(0)}K`
  return n.toString()
}

export default function MsmeWidget({ sectors }) {
  if (!sectors || sectors.length === 0) {
    return <WidgetCard title="Business Sectors" icon={Briefcase} empty emptyMsg="No MSME data for this district" />
  }

  const top = sectors.slice(0, 3)
  const max = Math.max(...top.map(s => s.enterprise_count || 0), 1)
  const total = sectors.reduce((sum, s) => sum + (s.enterprise_count || 0), 0)

  return (
    <WidgetCard
      title="Business Sectors"
      icon={Briefcase}
      action={<span className="text-[10px] text-text-muted">{fmt(total)} enterprises</span>}
    >
      <div className="space-y-2.5">
        {top.map((s, i) => {
          const count = s.enterprise_count || 0
          const pct = (count / max) * 100
          return (
            <div key={i} title={`${s.sector_name}: ${count.toLocaleString()} enterprises`}>
              <div className="flex items-center justify-between text-xs mb-1">
                <span className="text-text-secondary truncate pr-2">{s.sector_name}</span>
                <span className="text-text-primary tabular-nums flex-shrink-0">{fmt(count)}</span>
              </div>
              <div className="h-1.5 bg-border rounded-full overflow-hidden">
                <div className="h-full bg-accent rounded-full transition-all duration-700" style={{ width: `${pct}%` }} />
              </div>
            </div>
          )
        })}
      </div>
    </WidgetCard>
  )
}
