import { useState, useCallback, useRef } from 'react'
import axios from 'axios'

export function useChat({ onReportUpdate } = {}) {
  const [sessionId, setSessionId] = useState(null)
  const [messages, setMessages] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)
  const [isAvailable, setIsAvailable] = useState(true)
  const analysisIdRef = useRef(null)

  const createSession = useCallback(async (analysisId = null) => {
    try {
      const { data } = await axios.post('/api/chat/session', {
        analysis_id: analysisId,
        user_id: 'anonymous',
      }, { timeout: 10000 })
      setSessionId(data.session_id)
      analysisIdRef.current = analysisId
      setMessages([])
      setError(null)
      return data.session_id
    } catch (err) {
      if (err.response?.status === 503) {
        setIsAvailable(false)
      }
      setError(err.response?.data?.detail || 'Failed to start chat session')
      return null
    }
  }, [])

  const sendMessage = useCallback(async (text, currentReport = null) => {
    if (!sessionId || !text.trim()) return

    const userMsg = { role: 'user', content: text, id: Date.now() }
    setMessages(prev => [...prev, userMsg])
    setIsLoading(true)
    setError(null)

    try {
      const { data } = await axios.post('/api/chat/message', {
        session_id: sessionId,
        analysis_id: analysisIdRef.current,
        message: text,
        current_report: currentReport,
        user_id: 'anonymous',
      }, { timeout: 60000 })

      const assistantMsg = {
        role: 'assistant',
        content: data.message,
        tool_calls: data.tool_calls || [],
        suggested_actions: data.suggested_actions || [],
        warnings: data.warnings || [],
        id: Date.now() + 1,
      }
      setMessages(prev => [...prev, assistantMsg])

      if (data.updated_report && onReportUpdate) {
        onReportUpdate(data.updated_report)
        analysisIdRef.current = data.updated_report._analysis_id || analysisIdRef.current
      }

      return data
    } catch (err) {
      if (err.response?.status === 503) setIsAvailable(false)
      const errMsg = err.response?.data?.detail || err.message || 'Request failed'
      setError(errMsg)
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `Error: ${errMsg}`,
        id: Date.now() + 1,
      }])
    } finally {
      setIsLoading(false)
    }
  }, [sessionId, onReportUpdate])

  const resetSession = useCallback(() => {
    setSessionId(null)
    setMessages([])
    setError(null)
    analysisIdRef.current = null
  }, [])

  return {
    sessionId,
    messages,
    isLoading,
    error,
    isAvailable,
    createSession,
    sendMessage,
    resetSession,
  }
}
