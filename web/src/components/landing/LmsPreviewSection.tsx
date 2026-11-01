import React, { useState, useRef, useEffect } from 'react'
import {
  Monitor,
  Award,
  BarChart3,
  ArrowRight,
  Sparkles,
  Pencil,
  RotateCcw,
  Check,
  CheckCircle2,
  Lock,
} from 'lucide-react'
import { useApp } from '../../context/AppContext'

const COLORS = ['#1d5fd1', '#0f9d58', '#ef4444', '#111111']

export function LmsPreviewSection() {
  const { navigateTo, addToast } = useApp()
  const [activeTab, setActiveTab] = useState<'canvas' | 'quiz' | 'analytics'>('canvas')

  // Mini canvas state
  const canvasRef = useRef<HTMLCanvasElement | null>(null)
  const [selectedColor, setSelectedColor] = useState('#1d5fd1')
  const [isDrawing, setIsDrawing] = useState(false)

  // Quiz preview state
  const [quizSelected, setQuizSelected] = useState<number | null>(null)

  useEffect(() => {
    if (activeTab !== 'canvas') return
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    // Fill white
    ctx.fillStyle = '#ffffff'
    ctx.fillRect(0, 0, canvas.width, canvas.height)

    // Draw initial sample diagram
    ctx.strokeStyle = '#1d5fd1'
    ctx.lineWidth = 3
    ctx.strokeRect(60, 40, 160, 70)
    ctx.fillStyle = '#0d1b3e'
    ctx.font = 'bold 12px monospace'
    ctx.fillText('Client React 19', 85, 80)

    ctx.beginPath()
    ctx.moveTo(220, 75)
    ctx.lineTo(340, 75)
    ctx.strokeStyle = '#0f9d58'
    ctx.lineWidth = 2
    ctx.stroke()

    ctx.strokeStyle = '#0f9d58'
    ctx.strokeRect(340, 40, 160, 70)
    ctx.fillStyle = '#0d1b3e'
    ctx.fillText('Node.js / Go API', 360, 80)
  }, [activeTab])

  const startDraw = (e: React.MouseEvent<HTMLCanvasElement>) => {
    setIsDrawing(true)
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return
    const rect = canvas.getBoundingClientRect()
    ctx.beginPath()
    ctx.moveTo(e.clientX - rect.left, e.clientY - rect.top)
    ctx.strokeStyle = selectedColor
    ctx.lineWidth = 3
    ctx.lineCap = 'round'
  }

  const draw = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!isDrawing) return
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return
    const rect = canvas.getBoundingClientRect()
    ctx.lineTo(e.clientX - rect.left, e.clientY - rect.top)
    ctx.stroke()
  }

  const stopDraw = () => {
    setIsDrawing(false)
  }

  const clearMiniCanvas = () => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return
    ctx.fillStyle = '#ffffff'
    ctx.fillRect(0, 0, canvas.width, canvas.height)
  }

  return (
    <section className="border-t-4 border-ink bg-paper py-20 font-mono text-ink">
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        {/* Header */}
        <div className="text-center max-w-2xl mx-auto">
          <span className="inline-flex items-center gap-1.5 border-2 border-ink bg-accent px-3 py-0.5 text-xs font-bold text-white shadow-[2px_2px_0_#0d1b3e]">
            <Sparkles className="h-3.5 w-3.5" /> LIVE LMS TEST-DRIVE
          </span>
          <h2 className="mt-3 text-2xl font-bold text-ink sm:text-[34px]">
            Experience the <span className="text-brand">SkillsUp LMS Workstation</span>
          </h2>
          <p className="mt-2 text-xs text-muted sm:text-sm">
            Try out our signature interactive whiteboard and cohort assessment tools directly right
            now without signing in!
          </p>
        </div>

        {/* Feature Tab Buttons */}
        <div className="mt-10 flex flex-wrap justify-center gap-2">
          <button
            onClick={() => setActiveTab('canvas')}
            className={`flex items-center gap-2 border-2 border-ink px-4 py-2 text-xs font-bold shadow-[2px_2px_0_#0d1b3e] transition ${
              activeTab === 'canvas'
                ? 'bg-brand text-white -translate-y-0.5'
                : 'bg-white text-ink hover:bg-gray-100'
            }`}
          >
            <Monitor className="h-4 w-4" /> 1. Live Instructor Whiteboard
          </button>
          <button
            onClick={() => setActiveTab('quiz')}
            className={`flex items-center gap-2 border-2 border-ink px-4 py-2 text-xs font-bold shadow-[2px_2px_0_#0d1b3e] transition ${
              activeTab === 'quiz'
                ? 'bg-accent text-white -translate-y-0.5'
                : 'bg-white text-ink hover:bg-gray-100'
            }`}
          >
            <Award className="h-4 w-4" /> 2. Real-Time Quiz Engine
          </button>
          <button
            onClick={() => setActiveTab('analytics')}
            className={`flex items-center gap-2 border-2 border-ink px-4 py-2 text-xs font-bold shadow-[2px_2px_0_#0d1b3e] transition ${
              activeTab === 'analytics'
                ? 'bg-brand text-white -translate-y-0.5'
                : 'bg-white text-ink hover:bg-gray-100'
            }`}
          >
            <BarChart3 className="h-4 w-4" /> 3. Cohort Performance Ledger
          </button>
        </div>

        {/* Interactive Preview Surface (Styled with Dashboard Royal Frame Theme!) */}
        <div className="mt-8 border-4 border-ink rounded-2xl bg-gradient-to-br from-accent to-accent-dark p-2.5 sm:p-4 shadow-[8px_8px_0_#0d1b3e]">
          <div className="border-2 border-ink bg-white p-4 sm:p-6 rounded-xl">
            {activeTab === 'canvas' && (
              <div>
                <div className="flex flex-wrap items-center justify-between gap-3 border-b-2 border-ink/20 pb-3">
                  <div className="flex items-center gap-2">
                    <span className="h-2.5 w-2.5 rounded-full bg-accent animate-pulse" />
                    <span className="text-xs font-bold text-ink">Interactive Vector Canvas Demo</span>
                  </div>

                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-gray-500">Pick Pen Color:</span>
                    {COLORS.map((c) => (
                      <button
                        key={c}
                        onClick={() => setSelectedColor(c)}
                        className={`h-5 w-5 rounded-full border border-ink ${
                          selectedColor === c ? 'ring-2 ring-brand ring-offset-1' : ''
                        }`}
                        style={{ backgroundColor: c }}
                      />
                    ))}
                    <button
                      onClick={clearMiniCanvas}
                      className="ml-2 border border-ink bg-gray-100 px-2 py-0.5 text-xs font-bold text-ink hover:bg-gray-200"
                    >
                      Reset Canvas
                    </button>
                  </div>
                </div>

                <div className="relative mt-3 h-[220px] w-full overflow-hidden border-2 border-ink bg-white">
                  <canvas
                    ref={canvasRef}
                    width={800}
                    height={220}
                    onMouseDown={startDraw}
                    onMouseMove={draw}
                    onMouseUp={stopDraw}
                    onMouseLeave={stopDraw}
                    className="h-full w-full cursor-crosshair touch-none"
                  />
                  <div className="pointer-events-none absolute bottom-2 right-2 border border-ink bg-white/90 px-2 py-0.5 text-xs font-bold text-ink shadow-[1px_1px_0_#0d1b3e]">
                    Click &amp; drag to sketch diagrams on this live canvas!
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'quiz' && (
              <div className="space-y-4">
                <div className="border-b-2 border-ink/20 pb-2">
                  <span className="border border-ink bg-brand px-2 py-0.5 text-xs font-bold text-white shadow-xs">
                    SAMPLE QUESTION
                  </span>
                  <h3 className="mt-2 text-sm font-bold text-ink sm:text-base">
                    Why do React 19 Server Components eliminate bundle overhead for static libraries?
                  </h3>
                </div>

                <div className="grid gap-2.5 sm:grid-cols-2">
                  {[
                    'They run solely during build/server render and ship zero JavaScript to the client.',
                    'They convert JavaScript into WebAssembly automatically.',
                    'They require client-side hydration for every DOM node.',
                    'They disable CSS modules across components.',
                  ].map((ans, idx) => {
                    const isCorrect = idx === 0
                    const isSelected = quizSelected === idx
                    return (
                      <button
                        key={idx}
                        onClick={() => {
                          setQuizSelected(idx)
                          if (idx === 0) {
                            addToast('Correct Answer!', 'You mastered React 19 architecture!', 'success')
                          }
                        }}
                        className={`border-2 border-ink p-3 text-left text-xs font-bold transition shadow-[2px_2px_0_#0d1b3e] ${
                          isSelected
                            ? isCorrect
                              ? 'bg-emerald-100 text-emerald-950 border-emerald-600'
                              : 'bg-red-100 text-red-950 border-red-600'
                            : 'bg-white hover:bg-gray-50'
                        }`}
                      >
                        <span className="mr-2 inline-flex h-5 w-5 items-center justify-center border border-ink bg-white">
                          {String.fromCharCode(65 + idx)}
                        </span>
                        <span>{ans}</span>
                      </button>
                    )
                  })}
                </div>

                {quizSelected !== null && (
                  <p className="border border-ink bg-blue-50 p-2.5 text-xs text-brand font-bold animate-in fade-in">
                    {quizSelected === 0
                      ? '✓ Excellent! Server components execute exclusively on the server, producing rendered HTML without sending runtime JS.'
                      : '✗ Incorrect. Server components run on the server so that their code and dependencies do not get bundled into client JS.'}
                  </p>
                )}
              </div>
            )}

            {activeTab === 'analytics' && (
              <div>
                <div className="flex items-center justify-between border-b-2 border-ink/20 pb-2">
                  <span className="text-xs font-bold text-ink">Live Cohort CS402 Performance Matrix</span>
                  <span className="border border-ink bg-accent px-2 py-0.5 text-xs font-bold text-white">
                    96.8% PASS RATE
                  </span>
                </div>

                <div className="mt-4 grid grid-cols-3 gap-3">
                  <div className="border-2 border-ink bg-paper p-3 text-center shadow-[2px_2px_0_#0d1b3e]">
                    <span className="text-xs text-muted font-bold">Average Score</span>
                    <p className="text-xl font-bold text-brand">91.4%</p>
                  </div>
                  <div className="border-2 border-ink bg-paper p-3 text-center shadow-[2px_2px_0_#0d1b3e]">
                    <span className="text-xs text-muted font-bold">Graded PRs</span>
                    <p className="text-xl font-bold text-accent">142</p>
                  </div>
                  <div className="border-2 border-ink bg-paper p-3 text-center shadow-[2px_2px_0_#0d1b3e]">
                    <span className="text-xs text-muted font-bold">Attendance</span>
                    <p className="text-xl font-bold text-ink">98.2%</p>
                  </div>
                </div>
              </div>
            )}

            {/* Bottom Cockpit Jump Button */}
            <div className="mt-5 border-t-2 border-ink/10 pt-4 flex flex-wrap items-center justify-between gap-3">
              <span className="text-xs text-muted font-bold">
                Ready to manage your cohorts, whiteboard, and gradebook?
              </span>
              <button
                onClick={() => navigateTo('dashboard', 'overview')}
                className="flex items-center gap-2 border-2 border-ink bg-accent px-5 py-2 text-xs font-bold text-white shadow-[2.5px_2.5px_0_#0d1b3e] transition hover:bg-accent-dark hover:-translate-x-0.5 hover:-translate-y-0.5"
              >
                Launch LMS Dashboard <ArrowRight className="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
