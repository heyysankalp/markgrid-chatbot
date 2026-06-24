import ReactMarkdown from 'react-markdown'
import { AlertTriangle } from 'lucide-react'
import SourceChips from './SourceChips'

export default function Message({ message }) {
  const isUser = message.role === 'user'

  if (isUser) {
    return (
      <div className="flex justify-end animate-slide-up">
        <div className="max-w-[75%] bg-brand-600 text-white rounded-2xl rounded-tr-sm px-4 py-3 shadow-md">
          <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex items-start gap-3 animate-slide-up">
      {/* Bot avatar */}
      <div className="w-8 h-8 rounded-full bg-gradient-to-br from-brand-500 to-brand-700 flex items-center justify-center flex-shrink-0 shadow-lg mt-0.5">
        <span className="text-xs font-bold text-white">M</span>
      </div>

      <div className="max-w-[80%] space-y-1">
        {/* Low confidence warning */}
        {message.low_confidence && (
          <div className="flex items-center gap-1.5 text-amber-400 text-xs mb-1">
            <AlertTriangle size={12} />
            <span>Low confidence — answer may be incomplete</span>
          </div>
        )}

        {/* Bot bubble */}
        <div className="bg-slate-800 border border-slate-700 rounded-2xl rounded-tl-sm px-4 py-3 shadow-md">
          <div className="prose-chat text-sm text-slate-200">
            <ReactMarkdown>{message.content}</ReactMarkdown>
          </div>
        </div>

        {/* Source chips below bubble */}
        <SourceChips sources={message.sources} />
      </div>
    </div>
  )
}
