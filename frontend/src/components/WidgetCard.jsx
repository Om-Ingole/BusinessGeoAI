export default function WidgetCard({ title, icon: Icon, children, empty, emptyMsg, className = '', action }) {
  return (
    <div className={`bg-surface rounded-lg border border-border p-4 fade-in ${className}`}>
      <div className="flex items-center gap-2 mb-3">
        {Icon && <Icon className="w-4 h-4 text-accent flex-shrink-0" />}
        <h3 className="text-sm font-medium text-text-primary">{title}</h3>
        {action && <div className="ml-auto">{action}</div>}
      </div>
      {empty ? (
        <p className="text-text-muted text-xs">{emptyMsg || 'No data available'}</p>
      ) : children}
    </div>
  )
}
