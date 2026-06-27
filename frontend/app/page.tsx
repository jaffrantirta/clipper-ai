'use client'

import { useEffect, useRef, useState } from 'react'
import { ClipCard } from '@/components/ClipCard'
import { JobStatus } from '@/components/JobStatus'

export interface Clip {
  clip_id: string
  start: number
  end: number
  duration: number
  score: number
  reason: string
  download_url: string
  thumbnail_url: string
  subtitle_url?: string
}

interface JobData {
  job_id: string
  status: string
  progress: number
  error?: string
  clips: Clip[]
}

type AspectRatio = '16:9' | '9:16' | '1:1' | '4:3'
type SubtitleStyle = 'default' | 'bold' | 'minimal'

const ASPECT_RATIOS: { value: AspectRatio; label: string; hint: string }[] = [
  { value: '16:9', label: '16:9', hint: 'Landscape' },
  { value: '9:16', label: '9:16', hint: 'Portrait' },
  { value: '1:1',  label: '1:1',  hint: 'Square' },
  { value: '4:3',  label: '4:3',  hint: 'Classic' },
]

const SUBTITLE_STYLES: { value: SubtitleStyle; label: string; hint: string }[] = [
  { value: 'default', label: 'Default', hint: 'White + outline' },
  { value: 'bold',    label: 'Bold',    hint: 'Large + thick outline' },
  { value: 'minimal', label: 'Minimal', hint: 'Small + clean' },
]

const TERMINAL_STATES = new Set(['completed', 'failed'])

export default function Home() {
  const [url, setUrl] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [jobData, setJobData] = useState<JobData | null>(null)
  const [submitError, setSubmitError] = useState('')
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  // Options
  const [aspectRatio, setAspectRatio] = useState<AspectRatio>('16:9')
  const [minDuration, setMinDuration] = useState(5)
  const [maxDuration, setMaxDuration] = useState(60)
  const [addSubtitles, setAddSubtitles] = useState(false)
  const [subtitleStyle, setSubtitleStyle] = useState<SubtitleStyle>('default')

  const stopPolling = () => {
    if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null }
  }

  const pollStatus = async (jobId: string) => {
    try {
      const res = await fetch(`/api/status/${jobId}`)
      if (!res.ok) return
      const data: JobData = await res.json()
      setJobData(data)
      if (TERMINAL_STATES.has(data.status)) { stopPolling(); setSubmitting(false) }
    } catch { /* retry next tick */ }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const trimmed = url.trim()
    if (!trimmed) return

    setSubmitError('')
    setJobData(null)
    setSubmitting(true)
    stopPolling()

    try {
      const res = await fetch('/api/clip', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          youtube_url: trimmed,
          aspect_ratio: aspectRatio,
          min_duration: minDuration,
          max_duration: maxDuration,
          add_subtitles: addSubtitles,
          subtitle_style: subtitleStyle,
        }),
      })
      if (!res.ok) {
        let message = `Server error ${res.status}`
        try {
          const err = await res.json()
          message = err.detail ?? message
        } catch {
          const text = await res.text().catch(() => '')
          if (text) message = text
        }
        throw new Error(message)
      }
      const { job_id } = await res.json()
      pollRef.current = setInterval(() => pollStatus(job_id), 3000)
      pollStatus(job_id)
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : 'Something went wrong')
      setSubmitting(false)
    }
  }

  useEffect(() => () => stopPolling(), [])

  const isProcessing = jobData && !TERMINAL_STATES.has(jobData.status)
  const isActive = submitting || !!isProcessing

  return (
    <main className="min-h-screen bg-gray-950 text-white">
      <div className="max-w-5xl mx-auto px-4 py-12 space-y-8">

        {/* Header */}
        <div className="text-center">
          <h1 className="text-5xl font-extrabold tracking-tight mb-3 bg-gradient-to-r from-violet-400 to-cyan-400 bg-clip-text text-transparent">
            Clipper AI
          </h1>
          <p className="text-gray-400 text-lg">
            Paste a YouTube URL — AI finds and clips the best moments automatically.
          </p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="flex gap-3">
            <input
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://youtube.com/watch?v=..."
              disabled={isActive}
              className="flex-1 px-4 py-3 rounded-xl bg-gray-800 border border-gray-700 placeholder-gray-500 focus:outline-none focus:border-violet-500 disabled:opacity-50 text-sm"
            />
            <button
              type="submit"
              disabled={isActive || !url.trim()}
              className="px-6 py-3 rounded-xl bg-violet-600 hover:bg-violet-500 disabled:opacity-40 disabled:cursor-not-allowed font-semibold transition-colors text-sm whitespace-nowrap"
            >
              {isActive ? 'Processing…' : 'Find Clips'}
            </button>
          </div>

          {/* Settings panel */}
          <div className="rounded-xl bg-gray-900 border border-gray-800 p-4 space-y-4">
            {/* Aspect Ratio */}
            <div className="flex flex-wrap items-center gap-3">
              <span className="text-xs font-medium text-gray-400 w-28 shrink-0">Aspect ratio</span>
              <div className="flex gap-2 flex-wrap">
                {ASPECT_RATIOS.map(({ value, label, hint }) => (
                  <button
                    key={value}
                    type="button"
                    disabled={isActive}
                    onClick={() => setAspectRatio(value)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors disabled:opacity-40 ${
                      aspectRatio === value
                        ? 'bg-violet-600 text-white'
                        : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
                    }`}
                  >
                    {label}
                    <span className="ml-1 text-gray-400 font-normal">{hint}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Duration */}
            <div className="flex flex-wrap items-center gap-3">
              <span className="text-xs font-medium text-gray-400 w-28 shrink-0">Clip duration</span>
              <div className="flex items-center gap-2 text-sm">
                <label className="text-gray-400 text-xs">Min</label>
                <input
                  type="number"
                  min={1}
                  max={maxDuration - 1}
                  value={minDuration}
                  disabled={isActive}
                  onChange={(e) => setMinDuration(Math.max(1, Number(e.target.value)))}
                  className="w-16 px-2 py-1 rounded-lg bg-gray-800 border border-gray-700 text-center text-xs focus:outline-none focus:border-violet-500 disabled:opacity-40"
                />
                <span className="text-gray-600">—</span>
                <label className="text-gray-400 text-xs">Max</label>
                <input
                  type="number"
                  min={minDuration + 1}
                  max={600}
                  value={maxDuration}
                  disabled={isActive}
                  onChange={(e) => setMaxDuration(Math.max(minDuration + 1, Number(e.target.value)))}
                  className="w-16 px-2 py-1 rounded-lg bg-gray-800 border border-gray-700 text-center text-xs focus:outline-none focus:border-violet-500 disabled:opacity-40"
                />
                <span className="text-gray-500 text-xs">seconds</span>
              </div>
            </div>

            {/* Subtitles */}
            <div className="space-y-3">
              <div className="flex items-center gap-3">
                <span className="text-xs font-medium text-gray-400 w-28 shrink-0">Burn subtitles</span>
                <button
                  type="button"
                  disabled={isActive}
                  onClick={() => setAddSubtitles((v) => !v)}
                  className={`relative w-10 h-5 rounded-full transition-colors disabled:opacity-40 ${
                    addSubtitles ? 'bg-violet-600' : 'bg-gray-700'
                  }`}
                >
                  <span
                    className={`absolute top-0.5 left-0.5 w-4 h-4 rounded-full bg-white transition-transform ${
                      addSubtitles ? 'translate-x-5' : 'translate-x-0'
                    }`}
                  />
                </button>
                <span className="text-xs text-gray-500">
                  {addSubtitles ? 'Burned into video + SRT download available' : 'No subtitles'}
                </span>
              </div>

              {addSubtitles && (
                <div className="flex flex-wrap items-center gap-3">
                  <span className="text-xs font-medium text-gray-400 w-28 shrink-0">Style</span>
                  <div className="flex gap-2 flex-wrap">
                    {SUBTITLE_STYLES.map(({ value, label, hint }) => (
                      <button
                        key={value}
                        type="button"
                        disabled={isActive}
                        onClick={() => setSubtitleStyle(value)}
                        className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors disabled:opacity-40 ${
                          subtitleStyle === value
                            ? 'bg-violet-600 text-white'
                            : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
                        }`}
                      >
                        {label}
                        <span className="ml-1 text-gray-400 font-normal">{hint}</span>
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </form>

        {/* Submit error */}
        {submitError && (
          <div className="px-4 py-3 rounded-xl bg-red-900/40 border border-red-700 text-red-300 text-sm">
            {submitError}
          </div>
        )}

        {/* Progress */}
        {jobData && (
          <JobStatus status={jobData.status} progress={jobData.progress} error={jobData.error} />
        )}

        {/* Clips */}
        {jobData?.status === 'completed' && (
          jobData.clips.length > 0 ? (
            <div>
              <h2 className="text-xl font-semibold mb-5 text-gray-200">
                {jobData.clips.length} clip{jobData.clips.length !== 1 ? 's' : ''} found
              </h2>
              <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
                {[...jobData.clips].sort((a, b) => b.score - a.score).map((clip) => (
                  <ClipCard key={clip.clip_id} clip={clip} />
                ))}
              </div>
            </div>
          ) : (
            <p className="text-center py-16 text-gray-500">
              No notable clips found in this video. Try adjusting the duration range or try another video.
            </p>
          )
        )}
      </div>
    </main>
  )
}
