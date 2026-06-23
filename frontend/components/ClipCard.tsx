import type { Clip } from '@/app/page'

function fmt(s: number) {
  const m = Math.floor(s / 60)
  const sec = Math.floor(s % 60)
  return `${m}:${String(sec).padStart(2, '0')}`
}

function ScoreBar({ score }: { score: number }) {
  const pct = Math.round((score / 10) * 100)
  const color =
    score >= 8.5 ? 'bg-emerald-400' : score >= 7 ? 'bg-violet-400' : 'bg-yellow-400'
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 rounded-full bg-gray-700 overflow-hidden">
        <div className={`h-full rounded-full transition-all ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs font-semibold text-gray-300 w-7 text-right tabular-nums">
        {score.toFixed(1)}
      </span>
    </div>
  )
}

export function ClipCard({ clip }: { clip: Clip }) {
  return (
    <div className="rounded-2xl bg-gray-900 border border-gray-800 overflow-hidden flex flex-col">
      {/* Video preview — hover to play */}
      <div className="relative aspect-video bg-gray-800 group cursor-pointer">
        <video
          src={clip.download_url}
          poster={clip.thumbnail_url}
          className="w-full h-full object-cover"
          preload="metadata"
          muted
          playsInline
          onMouseEnter={(e) => (e.currentTarget as HTMLVideoElement).play()}
          onMouseLeave={(e) => {
            const v = e.currentTarget as HTMLVideoElement
            v.pause()
            v.currentTime = 0
          }}
        />
        {/* Play overlay */}
        <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-0 transition-opacity pointer-events-none">
          <div className="w-12 h-12 rounded-full bg-black/60 flex items-center justify-center">
            <svg className="w-5 h-5 text-white ml-0.5" fill="currentColor" viewBox="0 0 24 24">
              <path d="M8 5v14l11-7z" />
            </svg>
          </div>
        </div>
        {/* Timestamp badge */}
        <span className="absolute bottom-2 right-2 text-xs bg-black/70 px-2 py-0.5 rounded-md font-mono">
          {fmt(clip.start)} – {fmt(clip.end)}
        </span>
      </div>

      {/* Metadata */}
      <div className="p-4 flex flex-col gap-3 flex-1">
        <ScoreBar score={clip.score} />
        <p className="text-sm text-gray-300 leading-relaxed line-clamp-3">{clip.reason}</p>
        <div className="flex items-center justify-between mt-auto pt-3 border-t border-gray-800">
          <span className="text-xs text-gray-500 tabular-nums">{clip.duration.toFixed(1)}s</span>
          <a
            href={clip.download_url}
            download={`clip-${clip.clip_id}.mp4`}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-violet-600 hover:bg-violet-500 text-xs font-semibold transition-colors"
          >
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            Download
          </a>
        </div>
      </div>
    </div>
  )
}
