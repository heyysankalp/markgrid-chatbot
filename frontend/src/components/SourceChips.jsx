import { ExternalLink } from 'lucide-react'

export default function SourceChips({ sources }) {
  if (!sources || sources.length === 0) return null

  return (
    <div className="mt-2.5 flex flex-wrap gap-2">
      <span className="text-xs text-slate-500 self-center">Sources:</span>
      {sources.map((url, i) => {
        // Extract a readable label from the URL
        const label = url
          .replace('https://', '')
          .replace('http://', '')
          .replace(/\/$/, '')

        return (
          <a
            key={i}
            href={url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-full
                       bg-brand-500/10 border border-brand-500/20 text-brand-400
                       hover:bg-brand-500/20 hover:border-brand-500/40 transition-all duration-150"
          >
            <ExternalLink size={10} />
            {label}
          </a>
        )
      })}
    </div>
  )
}
