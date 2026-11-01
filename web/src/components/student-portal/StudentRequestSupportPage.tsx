import React, { useState } from 'react'
import { Send, HeartHandshake, Clock, CheckCircle2, AlertCircle } from 'lucide-react'
import { useSupportRequests, useCreateSupportRequest } from '../../lib/api/endpoints/student.hooks'
import { errorMessage } from '../../lib/api/errors'

const CATEGORIES = [
  'Academic Stress & Deadlines',
  'Emotional & Mental Wellbeing',
  'Peer Tutoring Request',
  'Exam Anxiety / No-Show',
  'Financial Assistance Inquiry',
  'Career & Department Guidance',
]

const SLOTS = [
  'Morning (09:00 AM - 12:00 PM)',
  'Afternoon (02:00 PM - 05:00 PM)',
  'Evening (05:00 PM - 07:00 PM)',
]

export function StudentRequestSupportPage() {
  const reqs = useSupportRequests()
  const createReq = useCreateSupportRequest()

  const [category, setCategory] = useState(CATEGORIES[0])
  const [preferredSlot, setPreferredSlot] = useState(SLOTS[0])
  const [studentNote, setStudentNote] = useState('')
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!studentNote.trim()) return

    setMsg(null)
    createReq.mutate(
      {
        category,
        preferred_slot: preferredSlot,
        student_note: studentNote.trim(),
      },
      {
        onSuccess: () => {
          setStudentNote('')
          setMsg({
            ok: true,
            text: 'Your confidential support request has been submitted. A designated campus counselor will reach out shortly.',
          })
        },
        onError: (err) => {
          setMsg({ ok: false, text: errorMessage(err) })
        },
      }
    )
  }

  return (
    <div className="mt-2 space-y-6 font-sans">
      {/* Submission Form */}
      <div className="bg-white rounded-3xl border border-gray-100 p-6 shadow-xs">
        <div className="flex items-center gap-2 mb-4">
          <div className="p-2 rounded-xl bg-purple-50 text-purple-700">
            <HeartHandshake className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-bold text-gray-900">Reach Out for Support</h2>
            <p className="text-xs text-gray-500">
              Your request is confidential and directly dispatched to our campus advisory radar.
            </p>
          </div>
        </div>

        {msg && (
          <div
            className={`p-3.5 rounded-2xl text-xs mb-4 flex items-center gap-2 ${
              msg.ok ? 'bg-emerald-50 text-emerald-800 border border-emerald-100' : 'bg-rose-50 text-rose-800 border border-rose-100'
            }`}
          >
            {msg.ok ? <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-600" /> : <AlertCircle className="w-4 h-4 shrink-0 text-rose-600" />}
            <span className="font-medium">{msg.text}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4 text-xs">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="font-bold text-gray-700 block mb-1.5 uppercase tracking-wider text-[10px]">
                Support Category
              </label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="w-full p-2.5 rounded-xl border border-gray-200 bg-gray-50/50 focus:bg-white focus:outline-purple-600 text-xs"
              >
                {CATEGORIES.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="font-bold text-gray-700 block mb-1.5 uppercase tracking-wider text-[10px]">
                Preferred Meeting Window
              </label>
              <select
                value={preferredSlot}
                onChange={(e) => setPreferredSlot(e.target.value)}
                className="w-full p-2.5 rounded-xl border border-gray-200 bg-gray-50/50 focus:bg-white focus:outline-purple-600 text-xs"
              >
                {SLOTS.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="font-bold text-gray-700 block mb-1.5 uppercase tracking-wider text-[10px]">
              How can we assist you? (Personal Reflection)
            </label>
            <textarea
              rows={4}
              value={studentNote}
              onChange={(e) => setStudentNote(e.target.value)}
              placeholder="Describe your current situation, challenge, or what kind of guidance would help you most right now..."
              className="w-full p-3 rounded-2xl border border-gray-200 bg-gray-50/50 focus:bg-white focus:outline-purple-600 text-xs leading-relaxed"
              required
            />
          </div>

          <button
            type="submit"
            disabled={createReq.isPending}
            className="px-5 py-2.5 rounded-full bg-purple-700 hover:bg-purple-800 text-white font-bold text-xs shadow-sm transition flex items-center gap-2 cursor-pointer disabled:opacity-50"
          >
            <Send className="w-3.5 h-3.5" />
            <span>{createReq.isPending ? 'Submitting Confidential Request...' : 'Send Support Request'}</span>
          </button>
        </form>
      </div>

      {/* History of Support Requests */}
      <div className="bg-white rounded-3xl border border-gray-100 p-6 shadow-xs">
        <h3 className="text-sm font-bold text-gray-900 mb-3">Your Support Requests History</h3>
        {reqs.isLoading ? (
          <p className="text-xs text-gray-400">Loading requests...</p>
        ) : !reqs.data?.length ? (
          <p className="text-xs text-gray-400 italic">No support requests submitted yet.</p>
        ) : (
          <div className="divide-y divide-gray-100 text-xs space-y-3 pt-1">
            {reqs.data.map((r) => (
              <div key={r.id} className="pt-3 first:pt-0 space-y-1.5">
                <div className="flex justify-between items-center">
                  <span className="font-bold text-gray-900">{r.category}</span>
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full uppercase ${
                    r.status === 'resolved' ? 'bg-emerald-50 text-emerald-700' : 'bg-amber-50 text-amber-700'
                  }`}>
                    {r.status}
                  </span>
                </div>
                <p className="text-gray-600 leading-relaxed">{r.student_note}</p>
                {r.faculty_response && (
                  <div className="bg-gray-50 p-2.5 rounded-xl border border-gray-100 text-gray-700 text-[11px]">
                    <span className="font-bold text-purple-700 block mb-0.5">Advisor Response:</span>
                    {r.faculty_response}
                  </div>
                )}
                <div className="text-[10px] text-gray-400">
                  Preferred Slot: {r.preferred_slot} • Submitted {new Date(r.created_at).toLocaleDateString()}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
