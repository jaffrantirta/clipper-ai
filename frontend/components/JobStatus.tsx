const STAGES = [
  { key: 'downloading',  label: 'Download',  progress: 10 },
  { key: 'transcribing', label: 'Transcribe', progress: 30 },
  { key: 'analyzing',   label: 'Audio AI',   progress: 50 },
  { key: 'scoring',     label: 'LLM Score',  progress: 70 },
  { key: 'cutting',     label: 'Cut',        progress: 90 },
  { key: 'completed',   label: 'Done',       progress: 100 },
]

interface Props {
  status: string
  progress: number
  error?: string
}

export function JobStatus({ status, progress, error }: Props) {
  const failed = status === 'failed'
  const done = status === 'completed'
  const currentStage = STAGES.find((s) => s.key === status)
  const label = failed ? 'Failed' : (currentStage?.label ?? 'Queued')

  return (
    <div className="rounded-2xl bg-gray-900 border border-gray-800 p-5 space-y-4">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-gray-300">{label}</span>
        <span className="text-sm font-mono text-gray-400">{failed ? '' : `${progress}%`}</span>
      </div>

      {/* Progress bar */}
      <div className="h-2 rounded-full bg-gray-800 overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-500 ${
            failed ? 'bg-red-500 w-full' : done ? 'bg-emerald-400' : 'bg-violet-500'
          }`}
          style={!failed ? { width: `${progress}%` } : undefined}
        />
      </div>

      {/* Stage dots */}
      {!failed && (
        <div className="flex justify-between px-1">
          {STAGES.map((stage) => {
            const reached = progress >= stage.progress
            const active = status === stage.key
            return (
              <div key={stage.key} className="flex flex-col items-center gap-1.5">
                <div
                  className={`w-2 h-2 rounded-full transition-colors duration-300 ${
                    reached
                      ? active
                        ? 'bg-violet-400 ring-2 ring-violet-400/30'
                        : 'bg-emerald-400'
                      : 'bg-gray-700'
                  }`}
                />
                <span className="text-[10px] text-gray-500 hidden sm:block leading-none">
                  {stage.label}
                </span>
              </div>
            )
          })}
        </div>
      )}

      {failed && error && (
        <p className="text-sm text-red-400">{error}</p>
      )}
    </div>
  )
}
