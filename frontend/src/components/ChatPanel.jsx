import { useState, useEffect, useRef } from 'react'
import { Bot, Send, ChevronDown, ChevronUp, AlertTriangle, Loader2 } from 'lucide-react'
import { useChat } from '../hooks/useChat'

const QUICK_ACTIONS = [
  'Is this good for retail?',
  'Find competitors',
  'Explain the score',
  'Compare another area',
  'Run 2 km radius',
  'Top risks',
  'Best business here?',
]

function ToolCallBadge({ calls = [] }) {
  if (!calls.length) return null
  return (
    <div className="flex flex-wrap gap-1 mb-1">
      {calls.map((tc, i) => (
        <span key={i} className={`text-[9px] px-1.5 py-0.5 rounded border ${
          tc.status === 'error' ? 'border-danger/40 text-danger' : 'border-accent/40 text-accent'
        }`}>
          {tc.name.replace(/_tool$/, '').replace(/_/g, ' ')}
        </span>
      ))}
    </div>
  )
}

function MessageBubble({ msg }) {
  const isUser = msg.role === 'user'
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-3`}>
      <div className={`max-w-[88%] ${isUser ? 'order-2' : ''}`}>
        {!isUser && <ToolCallBadge calls={msg.tool_calls} />}
        <div className={`text-xs rounded-lg px-3 py-2 leading-relaxed whitespace-pre-wrap ${
          isUser
            ? 'bg-accent text-bg-primary rounded-br-sm font-medium'
            : 'bg-surface-raised border border-border text-text-primary rounded-bl-sm'
        }`}>
          {msg.content}
        </div>
        {!isUser && msg.warnings?.length > 0 && (
          <p className="text-[9px] text-warning mt-0.5 px-1 flex items-center gap-1">
            <AlertTriangle className="w-2.5 h-2.5" /> {msg.warnings.join(' · ')}
          </p>
        )}
      </div>
    </div>
  )
}

export default function ChatPanel({ data, businessType, onReportUpdate }) {
  const [collapsed, setCollapsed] = useState(false)
  const [input, setInput] = useState('')
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)

  const { sessionId, messages, isLoading, error, isAvailable, createSession, sendMessage } = useChat({ onReportUpdate })

  // Auto-scroll to latest message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  // Create a session on mount / when report appears
  useEffect(() => {
    if (!sessionId) {
      createSession(data?._analysis_id || null)
    }
  }, [])

  useEffect(() => {
    if (data && !sessionId) {
      createSession(data._analysis_id || null)
    }
  }, [data])

  const handleSend = async (text = input) => {
    const msg = text.trim()
    if (!msg || isLoading || !sessionId) return
    setInput('')
    // Attach business type as context for the assistant
    const context = businessType ? { ...data, _business_type: businessType } : data
    await sendMessage(msg, context)
    inputRef.current?.focus()
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  if (!isAvailable) {
    return (
      <div className="bg-surface rounded-lg border border-border p-4">
        <div className="flex items-center gap-2 mb-2">
          <Bot className="w-4 h-4 text-accent flex-shrink-0" />
          <h3 className="text-sm font-medium text-text-primary">BusinessGeo Assistant</h3>
        </div>
        <p className="text-xs text-text-muted">
          AI chat requires GOOGLE_GENAI_API_KEY to be configured.
        </p>
      </div>
    )
  }

  const locName = data?.location?.display_address?.split(',')[0]
  const score = data?.viability_score

  return (
    <div className="bg-surface rounded-lg border border-border flex flex-col overflow-hidden">
      {/* Header */}
      <button
        onClick={() => setCollapsed(c => !c)}
        className="px-4 py-3 flex items-center gap-2 text-left w-full"
      >
        <Bot className="w-4 h-4 text-accent flex-shrink-0" />
        <div className="min-w-0 flex-1">
          <h3 className="text-sm font-medium text-text-primary">BusinessGeo Assistant</h3>
          {locName && (
            <p className="text-[10px] text-text-muted truncate">
              {locName}{score != null ? ` · ${score}/10` : ''}
            </p>
          )}
        </div>
        {isLoading && <Loader2 className="w-4 h-4 text-accent animate-spin flex-shrink-0" />}
        {collapsed ? <ChevronDown className="w-4 h-4 text-text-muted" /> : <ChevronUp className="w-4 h-4 text-text-muted" />}
      </button>

      {!collapsed && (
        <>
          {/* Messages */}
          <div className="px-3 pb-2 max-h-72 overflow-y-auto border-t border-border pt-3">
            {messages.length === 0 && (
              <p className="text-xs text-text-muted text-center py-2 mb-2">
                {data ? 'Ask about this location, or try a quick prompt below.' : 'Search a location first, or ask me to analyze one.'}
              </p>
            )}
            {messages.map(msg => <MessageBubble key={msg.id} msg={msg} />)}
            {isLoading && (
              <div className="flex justify-start mb-3">
                <div className="bg-surface-raised border border-border rounded-lg rounded-bl-sm px-3 py-2 flex items-center gap-1.5">
                  <span className="text-[10px] text-text-muted">Analyzing location</span>
                  <div className="flex gap-1">
                    {[0, 1, 2].map(i => (
                      <span key={i} className="w-1 h-1 rounded-full bg-accent/60 animate-bounce" style={{ animationDelay: `${i * 0.15}s` }} />
                    ))}
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Quick prompts (horizontal scroll) */}
          <div className="px-3 pb-2 flex gap-1.5 overflow-x-auto">
            {(messages.length > 0 && messages[messages.length - 1]?.suggested_actions?.length > 0
              ? messages[messages.length - 1].suggested_actions
              : QUICK_ACTIONS
            ).slice(0, 6).map(action => (
              <button
                key={action}
                onClick={() => handleSend(action)}
                disabled={!sessionId || isLoading}
                className="text-[10px] px-2 py-1 rounded-full border border-border text-text-secondary hover:border-accent hover:text-accent transition-colors disabled:opacity-40 whitespace-nowrap flex-shrink-0"
              >
                {action}
              </button>
            ))}
          </div>

          {error && <p className="text-[10px] text-danger px-4 pb-1">{error}</p>}

          {/* Input */}
          <div className="px-3 pb-3 pt-1 border-t border-border">
            <div className="flex gap-2 items-end">
              <textarea
                ref={inputRef}
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={sessionId ? 'Ask about this location…' : 'Starting session…'}
                disabled={!sessionId || isLoading}
                rows={1}
                className="flex-1 bg-bg-primary border border-border rounded-lg px-3 py-2 text-xs text-text-primary placeholder-text-muted resize-none focus:outline-none focus:border-accent disabled:opacity-50 transition-colors"
                style={{ minHeight: '36px', maxHeight: '100px' }}
              />
              <button
                onClick={() => handleSend()}
                disabled={!sessionId || isLoading || !input.trim()}
                className="w-9 h-9 rounded-lg bg-accent text-bg-primary flex items-center justify-center hover:bg-teal-400 disabled:opacity-40 transition-all flex-shrink-0"
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
