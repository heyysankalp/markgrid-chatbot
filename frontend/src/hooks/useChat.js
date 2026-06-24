import { useState, useCallback, useRef } from 'react'

const API_BASE = ''

export function useChat() {
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      role: 'assistant',
      content: "Hi! I'm the Markgrid assistant. Ask me anything about the platform — features, pricing, solutions, or how to get started.",
      sources: [],
      low_confidence: false,
    },
  ])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const messagesRef = useRef(messages)

  // Keep ref in sync with state
  const updateMessages = (updater) => {
    setMessages(prev => {
      const next = typeof updater === 'function' ? updater(prev) : updater
      messagesRef.current = next
      return next
    })
  }

  const sendMessage = useCallback(async (text) => {
    if (!text.trim() || loading) return

    const userMsg = {
      id: Date.now().toString(),
      role: 'user',
      content: text.trim(),
    }

    // Add user message and update ref
    updateMessages(prev => [...prev, userMsg])
    setLoading(true)
    setError(null)

    try {
      // Read from ref — always has latest messages including ones just added
      const history = messagesRef.current
        .filter(m => m.id !== 'welcome')
        .map(m => ({ role: m.role, content: m.content }))

      const res = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text.trim(), history }),
      })

      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail || `Server error ${res.status}`)
      }

      const data = await res.json()

      const botMsg = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: data.answer,
        sources: data.sources || [],
        low_confidence: data.low_confidence || false,
      }

      updateMessages(prev => [...prev, botMsg])

    } catch (err) {
      setError(err.message)
      updateMessages(prev => prev.filter(m => m.id !== userMsg.id))
    } finally {
      setLoading(false)
    }
  }, [loading])

  const clearChat = useCallback(() => {
    const initial = [
      {
        id: 'welcome',
        role: 'assistant',
        content: "Hi! I'm the Markgrid assistant. Ask me anything about the platform — features, pricing, solutions, or how to get started.",
        sources: [],
        low_confidence: false,
      },
    ]
    messagesRef.current = initial
    setMessages(initial)
    setError(null)
  }, [])

  return { messages, loading, error, sendMessage, clearChat }
}