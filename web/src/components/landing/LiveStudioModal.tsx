import React, { useState } from 'react'
import {
  X,
  Radio,
  Users,
  Send,
  Hand,
  Volume2,
  VolumeX,
  Maximize2,
  Smile,
  HelpCircle,
  CheckCircle,
} from 'lucide-react'
import { useApp } from '../../context/AppContext'
import { useSession } from '../../lib/auth/SessionProvider'

interface ChatMessage {
  id: string
  sender: string
  text: string
  time: string
  isInstructor?: boolean
}

export function LiveStudioModal() {
  const { activeLiveModal, setActiveLiveModal, addToast } = useApp()
  const { user, role } = useSession()
  const [isMuted, setIsMuted] = useState(false)
  const [handRaised, setHandRaised] = useState(false)
  const [chatInput, setChatInput] = useState('')
  const [pollVoted, setPollVoted] = useState<number | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'm1',
      sender: 'Joseph Jackson',
      text: 'Welcome everyone! Today we are building a collaborative canvas from scratch with React hooks.',
      time: '12:31 PM',
      isInstructor: true,
    },
    {
      id: 'm2',
      sender: 'A student',
      text: 'Super excited for this session! Audio is crystal clear.',
      time: '12:32 PM',
    },
    {
      id: 'm3',
      sender: 'Tanvi Verma',
      text: 'Will the whiteboard code snippet be uploaded to resources after class?',
      time: '12:33 PM',
    },
  ])

  if (!activeLiveModal) return null

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault()
    if (!chatInput.trim()) return

    const newMsg: ChatMessage = {
      id: `msg-${Date.now()}`,
      sender: user?.full_name ?? 'Guest',
      text: chatInput,
      time: 'Just now',
      isInstructor: (role === 'faculty' || role === 'mentor' || role === 'hod'),
    }
    setMessages((prev) => [...prev, newMsg])
    setChatInput('')
  }

  const toggleHandRaise = () => {
    setHandRaised(!handRaised)
    addToast(
      !handRaised ? '✋ Hand Raised' : 'Hand Lowered',
      !handRaised ? 'The instructor has been notified of your question.' : undefined,
      'info'
    )
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-3 backdrop-blur-sm animate-in fade-in">
      <div className="relative flex h-[92vh] w-full max-w-5xl flex-col overflow-hidden rounded-2xl border-4 border-ink bg-white shadow-[12px_12px_0_#0d1b3e]">
        {/* Top bar */}
        <div className="flex items-center justify-between border-b-2 border-ink bg-ink px-5 py-3 text-white">
          <div className="flex items-center gap-3">
            <span className="flex items-center gap-1.5 rounded bg-red-600 px-2 py-0.5 text-xs font-bold text-white animate-pulse">
              <Radio className="h-3 w-3" /> LIVE
            </span>
            <span className="text-xs font-bold tracking-tight sm:text-sm truncate max-w-md">
              {activeLiveModal.title}
            </span>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1 text-xs text-emerald-400">
              <Users className="h-3.5 w-3.5" />
              <span>{activeLiveModal.viewersCount} watching</span>
            </div>
            <button
              onClick={() => setActiveLiveModal(null)}
              className="rounded p-1 text-gray-400 hover:text-white"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>

        {/* Main Grid: Stream & Interactive Chat */}
        <div className="grid flex-1 overflow-hidden lg:grid-cols-[1fr_320px]">
          {/* Video Stream Stage */}
          <div className="relative flex flex-col justify-between bg-black p-4 text-white">
            {/* Stream visual background */}
            <div className="relative flex flex-1 items-center justify-center overflow-hidden rounded-xl border border-white/10 bg-gradient-to-br from-gray-900 to-black">
              {/* Speaker Video Avatar */}
              <div className="flex flex-col items-center text-center p-6">
                <div className="relative">
                  <img
                    src="https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=300&q=80"
                    alt="Instructor"
                    className="h-28 w-28 rounded-full border-4 border-emerald-500 object-cover shadow-2xl"
                  />
                  <span className="absolute bottom-1 right-1 flex h-6 w-6 items-center justify-center rounded-full bg-emerald-500 text-xs">
                    🎙️
                  </span>
                </div>
                <h3 className="mt-4 text-lg font-bold text-white">{activeLiveModal.instructor}</h3>
                <p className="text-xs text-gray-400">Presenting: Full-Stack React 19 State Architecture</p>

                {/* Simulated Audio Spectrum Wave */}
                <div className="mt-6 flex items-end gap-1.5 h-8">
                  {[18, 28, 12, 32, 22, 14, 30, 26, 16, 24, 32, 20].map((h, i) => (
                    <span
                      key={i}
                      className="w-1.5 rounded-full bg-emerald-400 animate-pulse"
                      style={{
                        height: `${h}px`,
                        animationDelay: `${i * 120}ms`,
                      }}
                    />
                  ))}
                </div>
              </div>

              {/* Live Overlay Badges */}
              <div className="absolute left-4 top-4 rounded bg-black/60 px-3 py-1 text-xs font-mono text-emerald-400 backdrop-blur-xs">
                1080p 60fps · Low Latency
              </div>

              {/* Live Poll Widget */}
              <div className="absolute bottom-4 left-4 right-4 sm:right-auto sm:max-w-xs rounded-xl border border-white/20 bg-gray-950/85 p-3 text-xs backdrop-blur-md">
                <p className="flex items-center gap-1.5 font-bold text-amber-400">
                  <HelpCircle className="h-3.5 w-3.5" /> Quick Check-in Poll:
                </p>
                <p className="mt-1 text-xs text-gray-300">Are you ready to build the whiteboard canvas?</p>
                <div className="mt-2 flex gap-2">
                  <button
                    onClick={() => {
                      setPollVoted(0)
                      addToast('Vote Recorded', 'You voted: Absolutely!', 'success')
                    }}
                    className={`flex-1 rounded border px-2 py-1 text-xs font-bold transition ${
                      pollVoted === 0
                        ? 'border-emerald-500 bg-emerald-500/20 text-emerald-400'
                        : 'border-white/20 hover:bg-white/10'
                    }`}
                  >
                    {pollVoted === 0 && <CheckCircle className="inline mr-1 h-3 w-3" />} Absolutely (84%)
                  </button>
                  <button
                    onClick={() => {
                      setPollVoted(1)
                      addToast('Vote Recorded', 'You voted: Need 5 mins', 'info')
                    }}
                    className={`flex-1 rounded border px-2 py-1 text-xs font-bold transition ${
                      pollVoted === 1
                        ? 'border-emerald-500 bg-emerald-500/20 text-emerald-400'
                        : 'border-white/20 hover:bg-white/10'
                    }`}
                  >
                    Need 5 mins (16%)
                  </button>
                </div>
              </div>
            </div>

            {/* Video Controls Bar */}
            <div className="mt-3 flex items-center justify-between rounded-lg bg-gray-900/80 px-4 py-2 text-xs">
              <div className="flex items-center gap-3">
                <button
                  onClick={() => setIsMuted(!isMuted)}
                  className="rounded p-1.5 text-gray-300 hover:text-white"
                  title={isMuted ? 'Unmute' : 'Mute'}
                >
                  {isMuted ? <VolumeX className="h-4 w-4 text-red-400" /> : <Volume2 className="h-4 w-4" />}
                </button>
                <span className="text-xs text-gray-400">Elapsed: 42:15 / 90:00</span>
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={toggleHandRaise}
                  className={`flex items-center gap-1.5 rounded border px-3 py-1 text-xs font-bold transition ${
                    handRaised
                      ? 'border-amber-400 bg-amber-400 text-black'
                      : 'border-white/20 text-white hover:bg-white/10'
                  }`}
                >
                  <Hand className="h-3.5 w-3.5" />
                  <span>{handRaised ? 'Hand Raised' : 'Raise Hand'}</span>
                </button>
                <button
                  onClick={() => addToast('Display settings', 'Full screen mode enabled', 'info')}
                  className="rounded p-1.5 text-gray-300 hover:text-white"
                >
                  <Maximize2 className="h-4 w-4" />
                </button>
              </div>
            </div>
          </div>

          {/* Real-Time Live Chat */}
          <div className="flex flex-col border-t-2 border-ink bg-paper lg:border-l-2 lg:border-t-0">
            <div className="border-b border-gray-200 bg-white px-4 py-3 text-xs font-bold text-ink">
              Cohort Live Chat &amp; Q&amp;A
            </div>

            {/* Messages list */}
            <div className="flex-1 overflow-y-auto p-3 space-y-2.5 text-xs">
              {messages.map((m) => (
                <div
                  key={m.id}
                  className={`rounded-lg border p-2.5 ${
                    m.isInstructor
                      ? 'border-brand/40 bg-blue-50/80'
                      : 'border-gray-200 bg-white'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span
                      className={`font-bold ${
                        m.isInstructor ? 'text-brand flex items-center gap-1' : 'text-gray-800'
                      }`}
                    >
                      {m.sender} {m.isInstructor && <span className="rounded bg-brand px-1 text-xs text-white">Host</span>}
                    </span>
                    <span className="text-xs text-gray-400">{m.time}</span>
                  </div>
                  <p className="mt-1 text-xs leading-relaxed text-gray-700">{m.text}</p>
                </div>
              ))}
            </div>

            {/* Input bar */}
            <form onSubmit={handleSendMessage} className="border-t border-gray-200 bg-white p-2.5">
              <div className="flex items-center gap-2 rounded-lg border-2 border-ink bg-paper px-3 py-1.5">
                <input
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  placeholder="Ask a question or share thoughts..."
                  className="min-w-0 flex-1 bg-transparent text-xs outline-none"
                />
                <button
                  type="button"
                  onClick={() => setChatInput((prev) => prev + ' 🚀')}
                  className="text-gray-400 hover:text-black"
                >
                  <Smile className="h-4 w-4" />
                </button>
                <button
                  type="submit"
                  className="rounded bg-brand p-1.5 text-white transition hover:bg-brand-dark"
                >
                  <Send className="h-3.5 w-3.5" />
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  )
}
