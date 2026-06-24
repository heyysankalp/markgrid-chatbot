import { useEffect, useRef, useState } from 'react'
import { Send, RotateCcw, Zap, AlertCircle } from 'lucide-react'
import Message from './Message'
import TypingIndicator from './TypingIndicator'
import SuggestedQuestions from './SuggestedQuestions'
import { useChat } from '../hooks/useChat'

export default function ChatWindow() {
  const { messages, loading, error, sendMessage, clearChat } = useChat()
  const [input, setInput] = useState('')
  const bottomRef   = useRef(null)
  const inputRef    = useRef(null)
  const messagesRef = useRef(null)

  // Only one message = welcome message → show suggestions
  const showSuggestions = messages.length === 1

  // Auto-scroll to bottom on new message
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  const handleSend = () => {
    if (!input.trim() || loading) return
    sendMessage(input)
    setInput('')
    inputRef.current?.focus()
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleSuggestion = (q) => {
    sendMessage(q)
    inputRef.current?.focus()
  }

  return (
    <div className="flex flex-col h-full">

      {/* ── Header ─────────────────────────────────────────────────────── */}
      <header className="flex items-center justify-between px-5 py-4 border-b border-slate-800 flex-shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-brand-500 to-brand-700 flex items-center justify-center shadow-lg">
            <Zap size={16} className="text-white" />
          </div>
          <div>
            <h1 className="text-sm font-semibold text-white leading-tight">Markgrid Assistant</h1>
            <p className="text-xs text-slate-500 leading-tight">AI Visibility Platform · Powered by RAG</p>
          </div>
        </div>

        <button
          onClick={clearChat}
          title="Clear chat"
          className="p-2 rounded-lg text-slate-500 hover:text-slate-300 hover:bg-slate-800 transition-colors"
        >
          <RotateCcw size={15} />
        </button>
      </header>

      {/* ── Messages ───────────────────────────────────────────────────── */}
      <div
        ref={messagesRef}
        className="flex-1 overflow-y-auto px-4 py-5 space-y-5 scroll-smooth"
      >
        {messages.map(msg => (
          <Message key={msg.id} message={msg} />
        ))}

        {loading && <TypingIndicator />}

        {/* Error toast */}
        {error && (
          <div className="flex items-center gap-2 text-red-400 text-xs bg-red-400/10 border border-red-400/20 rounded-xl px-4 py-2.5 animate-fade-in">
            <AlertCircle size={14} />
            <span>{error}</span>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* ── Suggested questions (only on fresh chat) ───────────────────── */}
      {showSuggestions && !loading && (
        <SuggestedQuestions onSelect={handleSuggestion} />
      )}

      {/* ── Input bar ──────────────────────────────────────────────────── */}
      <div className="px-4 pb-5 flex-shrink-0">
        <div className="flex items-end gap-2 bg-slate-800 border border-slate-700 rounded-2xl px-4 py-3
                        focus-within:border-brand-500/60 focus-within:ring-1 focus-within:ring-brand-500/20
                        transition-all duration-200">
          <textarea
            ref={inputRef}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask anything about Markgrid…"
            rows={1}
            className="flex-1 bg-transparent text-sm text-slate-200 placeholder-slate-500 resize-none
                       outline-none leading-relaxed max-h-36 overflow-y-auto"
            style={{ fieldSizing: 'content' }}
            disabled={loading}
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || loading}
            className="flex-shrink-0 w-8 h-8 rounded-xl bg-brand-600 hover:bg-brand-500 disabled:bg-slate-700
                       disabled:cursor-not-allowed flex items-center justify-center transition-colors duration-150
                       shadow-md hover:shadow-brand-500/20"
          >
            <Send size={14} className="text-white" />
          </button>
        </div>
        <p className="text-center text-xs text-slate-600 mt-2">
          Answers based on markgrid.ai content · May not reflect live changes
        </p>
      </div>

    </div>
  )
}
