const SUGGESTIONS = [
  "What is Markgrid?",
  "What are the pricing plans?",
  "What is Model Share?",
  "How does the Creator Audit work?",
  "What is Neuro-Marketing?",
  "Which industries does Markgrid serve?",
  "How do I contact sales?",
  "What AI platforms does Markgrid track?",
]

export default function SuggestedQuestions({ onSelect }) {
  return (
    <div className="px-4 pb-4">
      <p className="text-xs text-slate-500 mb-3 text-center">Suggested questions</p>
      <div className="flex flex-wrap gap-2 justify-center">
        {SUGGESTIONS.map((q, i) => (
          <button
            key={i}
            onClick={() => onSelect(q)}
            className="text-xs px-3 py-1.5 rounded-full border border-slate-700 text-slate-400
                       hover:border-brand-500/50 hover:text-brand-400 hover:bg-brand-500/5
                       transition-all duration-150 cursor-pointer"
          >
            {q}
          </button>
        ))}
      </div>
    </div>
  )
}
