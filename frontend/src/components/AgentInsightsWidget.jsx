import { Brain } from 'lucide-react'
import WidgetCard from './WidgetCard'

export default function AgentInsightsWidget({ insights }) {
  if (!insights) return null

  const { summary, best_use_cases = [], risks = [], opportunities = [], confidence, data_quality } = insights

  const confBadge = typeof confidence === 'number' ? (
    <span className="text-[10px] px-2 py-0.5 rounded-full border border-border text-text-muted">
      {Math.round(confidence * 100)}% conf
    </span>
  ) : null

  return (
    <WidgetCard title="AI Insights" icon={Brain} action={confBadge}>
      <div className="space-y-3">
        {summary && (
          <p className="text-sm text-text-secondary leading-relaxed">{summary}</p>
        )}

        {best_use_cases.length > 0 && (
          <div>
            <p className="text-[10px] uppercase tracking-wide text-text-muted mb-1.5">Best fit</p>
            <div className="flex flex-wrap gap-1.5">
              {best_use_cases.map(uc => (
                <span key={uc} className="text-[11px] px-2 py-0.5 rounded-full bg-accent/10 border border-accent/30 text-accent">
                  {uc}
                </span>
              ))}
            </div>
          </div>
        )}

        {opportunities.length > 0 && (
          <div>
            <p className="text-[10px] uppercase tracking-wide text-text-muted mb-1.5">Opportunities</p>
            <div className="space-y-1.5">
              {opportunities.slice(0, 3).map((opp, i) => (
                <div key={i} className="border-l-2 border-success pl-2.5 py-0.5">
                  <span className="text-xs font-medium text-text-primary">{opp.title}</span>
                  {opp.evidence && <span className="text-xs text-text-secondary"> — {opp.evidence}</span>}
                </div>
              ))}
            </div>
          </div>
        )}

        {risks.length > 0 && (
          <div>
            <p className="text-[10px] uppercase tracking-wide text-text-muted mb-1.5">Risks</p>
            <div className="space-y-1.5">
              {risks.slice(0, 3).map((risk, i) => (
                <div
                  key={i}
                  className={`border-l-2 pl-2.5 py-0.5 ${risk.severity === 'high' ? 'border-danger' : 'border-warning'}`}
                >
                  <span className="text-xs font-medium text-text-primary">{risk.title}</span>
                  {risk.evidence && <span className="text-xs text-text-secondary"> — {risk.evidence}</span>}
                </div>
              ))}
            </div>
          </div>
        )}

        {data_quality?.missing_sources?.length > 0 && (
          <p className="text-[10px] text-text-muted">
            Missing data: {data_quality.missing_sources.join(', ')}
          </p>
        )}
      </div>
    </WidgetCard>
  )
}
