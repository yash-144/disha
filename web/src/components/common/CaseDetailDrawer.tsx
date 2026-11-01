import React, { useState } from 'react'
import {
  X,
  Clock,
  User,
  Shield,
  Sparkles,
  AlertTriangle,
  CheckCircle2,
  Calendar,
  FileText,
  Activity,
  Plus,
  Send,
  Lock,
} from 'lucide-react'
import {
  useCaseDetail,
  useCaseEvents,
  useCaseInterventions,
  useCaseFollowups,
  useTransitionCase,
  useAssignCase,
  useRecordCaseOutcome,
  useAddCaseIntervention,
  useAddCaseNote,
  useAiReviewBrief,
} from '../../lib/api/endpoints/cases.hooks'
import { useCatalogue } from '../../lib/api/endpoints/admin.hooks'
import { useMemberships } from '../../lib/api/endpoints/adminExtensions.hooks'
import { errorMessage } from '../../lib/api/errors'
import { CATEGORY_LABEL, NEXT_STEPS, categoryLabel, friendlyDate, friendlyDateTime, outcomeLabel, priorityLabel, roleName, stageLabel, statusLabel, studentName } from '../../lib/labels'

const TAB_LABEL = { overview: 'Overview', interventions: 'Support', followups: 'Follow-ups', notes: 'Notes', audit: 'History' } as const

interface CaseDetailDrawerProps {
  caseId: string | null
  onClose: () => void
  userRole?: string
}

export function CaseDetailDrawer({ caseId, onClose, userRole }: CaseDetailDrawerProps) {
  const { data: caseItem, isLoading } = useCaseDetail(caseId)
  const { data: events = [] } = useCaseEvents(caseId)
  const { data: interventions = [] } = useCaseInterventions(caseId)
  const { data: followups = [] } = useCaseFollowups(caseId)
  const catalogue = useCatalogue()
  const memberships = useMemberships()

  const transitionMutation = useTransitionCase()
  const assignMutation = useAssignCase()
  const outcomeMutation = useRecordCaseOutcome()
  const addInterventionMutation = useAddCaseIntervention()
  const addNoteMutation = useAddCaseNote()
  const aiBriefMutation = useAiReviewBrief()

  const [activeTab, setActiveTab] = useState<'overview' | 'interventions' | 'followups' | 'notes' | 'audit'>('overview')
  const [noteContent, setNoteContent] = useState('')
  const [selectedInterventionCat, setSelectedInterventionCat] = useState('')
  const [interventionTitle, setInterventionTitle] = useState('')
  const [targetDate, setTargetDate] = useState('')
  const [feedbackMsg, setFeedbackMsg] = useState<{ ok: boolean; text: string } | null>(null)

  if (!caseId) return null

  const handleTransition = (toState: string) => {
    if (!caseItem) return
    setFeedbackMsg(null)
    transitionMutation.mutate(
      {
        id: caseItem.id,
        to_state: toState,
        expected_version: caseItem.version,
        reason: `${stageLabel(toState)} (by ${roleName(userRole || 'staff')})`,
      },
      {
        onSuccess: () => setFeedbackMsg({ ok: true, text: `Done. This case is now: ${stageLabel(toState)}.` }),
        onError: (e) => setFeedbackMsg({ ok: false, text: errorMessage(e) }),
      }
    )
  }

  const handleOutcome = (outcome: 'helped' | 'mixed' | 'not_helped') => {
    if (!caseItem) return
    setFeedbackMsg(null)
    outcomeMutation.mutate(
      {
        id: caseItem.id,
        outcome,
        expected_version: caseItem.version,
      },
      {
        onSuccess: () => setFeedbackMsg({ ok: true, text: `Saved: ${outcomeLabel(outcome)}.` }),
        onError: (e) => setFeedbackMsg({ ok: false, text: errorMessage(e) }),
      }
    )
  }

  const handleAddNote = (e: React.FormEvent) => {
    e.preventDefault()
    if (!caseItem || !noteContent.trim()) return
    addNoteMutation.mutate(
      { caseId: caseItem.id, content: noteContent.trim() },
      {
        onSuccess: () => {
          setNoteContent('')
          setFeedbackMsg({ ok: true, text: 'Note saved.' })
        },
        onError: (e) => setFeedbackMsg({ ok: false, text: errorMessage(e) }),
      }
    )
  }

  const handleAddIntervention = (e: React.FormEvent) => {
    e.preventDefault()
    if (!caseItem || !interventionTitle.trim()) return
    addInterventionMutation.mutate(
      {
        id: caseItem.id,
        title: interventionTitle.trim(),
        category: selectedInterventionCat || 'academic_advising',
        target_date: targetDate || undefined,
      },
      {
        onSuccess: () => {
          setInterventionTitle('')
          setSelectedInterventionCat('')
          setTargetDate('')
          setFeedbackMsg({ ok: true, text: 'Support added to this case.' })
        },
        onError: (e) => setFeedbackMsg({ ok: false, text: errorMessage(e) }),
      }
    )
  }

  return (
    <div className="fixed inset-0 z-50 overflow-hidden bg-black/40 backdrop-blur-xs flex justify-end">
      <div className="w-full max-w-2xl bg-white h-full shadow-2xl flex flex-col font-sans animate-in slide-in-from-right duration-200">
        {/* Header */}
        <div className="p-5 border-b border-line flex items-start justify-between bg-slate-900 text-white">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs px-2.5 py-0.5 rounded-full bg-white/10 font-semibold">
                {priorityLabel(caseItem?.priority)} priority
              </span>
              <span className="text-xs px-2.5 py-0.5 rounded-full bg-indigo-500/30 text-indigo-200 font-semibold">
                {caseItem ? stageLabel(caseItem.state) : 'Loading…'}
              </span>
              {caseItem?.is_overdue && (
                <span className="text-xs px-2 py-0.5 rounded-full bg-rose-500 text-white font-bold flex items-center gap-1">
                  <AlertTriangle className="w-3 h-3" /> Overdue
                </span>
              )}
            </div>
            <h2 className="text-xl font-bold mt-2">
              {studentName(caseItem?.student_name, caseItem?.student_ref)}
            </h2>
            <p className="text-xs text-slate-300 mt-0.5">
              {caseItem?.student_name && caseItem?.student_ref ? `Student ${caseItem.student_ref} · ` : ''}Opened {friendlyDate(caseItem?.created_at)}
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-full hover:bg-white/10 text-slate-400 hover:text-white transition cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Feedback Alert */}
        {feedbackMsg && (
          <div className={`p-3 text-xs font-medium ${feedbackMsg.ok ? 'bg-emerald-50 text-emerald-800' : 'bg-rose-50 text-rose-800'}`}>
            {feedbackMsg.text}
          </div>
        )}

        {/* Nav Tabs */}
        <div className="flex border-b border-line px-5 bg-gray-50/50 text-xs font-semibold text-gray-500">
          {(['overview', 'interventions', 'followups', 'notes', 'audit'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`py-3 px-3 border-b-2 transition cursor-pointer ${
                activeTab === tab
                  ? 'border-indigo-600 text-indigo-600 font-bold'
                  : 'border-transparent hover:text-gray-900'
              }`}
            >
              {TAB_LABEL[tab]}
            </button>
          ))}
        </div>

        {/* Content Area */}
        <div className="flex-1 overflow-y-auto p-5 text-sm space-y-5">
          {isLoading ? (
            <div className="py-20 text-center text-muted text-xs">Loading…</div>
          ) : activeTab === 'overview' ? (
            <div className="space-y-5">
              {/* Case Summary */}
              <div className="bg-gray-50 rounded-2xl p-4 border border-line text-xs leading-relaxed text-gray-700">
                <p className="font-bold text-gray-900 mb-1">What we noticed</p>
                {caseItem?.summary || 'No details were added.'}
              </div>

              {/* Next steps */}
              <div className="bg-white rounded-2xl p-4 border border-line shadow-xs">
                <h3 className="text-xs font-bold text-gray-500 mb-3">What would you like to do next?</h3>
                <div className="flex flex-wrap gap-2">
                  {(NEXT_STEPS[caseItem?.state ?? ''] ?? []).map((st) => (
                    <button
                      key={st.to}
                      onClick={() => handleTransition(st.to)}
                      disabled={transitionMutation.isPending}
                      className={`px-3.5 py-1.5 rounded-xl font-bold text-xs cursor-pointer disabled:opacity-50 ${
                        st.tone === 'primary' ? 'bg-purple-700 text-white hover:bg-purple-800' : st.tone === 'danger' ? 'bg-rose-600 text-white hover:bg-rose-700' : 'border border-line text-gray-700 hover:bg-gray-50'
                      }`}
                    >
                      {st.label}
                    </button>
                  ))}
                  {(NEXT_STEPS[caseItem?.state ?? ''] ?? []).length === 0 && <p className="text-xs text-muted">Nothing more to do on this case.</p>}
                </div>
              </div>

              {/* Record Outcome (Closes the accountable loop) */}
              <div className="bg-white rounded-2xl p-4 border border-line shadow-xs">
                <h3 className="text-xs font-bold text-gray-500 mb-2">
                  How did it go?
                </h3>
                <p className="text-xs text-gray-500 mb-3">
                  Did the student benefit from the support?
                </p>
                <div className="flex gap-2">
                  <button
                    onClick={() => handleOutcome('helped')}
                    className={`px-3 py-1.5 rounded-xl text-xs font-bold cursor-pointer ${
                      caseItem?.outcome === 'helped' ? 'bg-emerald-600 text-white' : 'bg-emerald-50 text-emerald-700 hover:bg-emerald-100'
                    }`}
                  >
                    It helped
                  </button>
                  <button
                    onClick={() => handleOutcome('mixed')}
                    className={`px-3 py-1.5 rounded-xl text-xs font-bold cursor-pointer ${
                      caseItem?.outcome === 'mixed' ? 'bg-amber-600 text-white' : 'bg-amber-50 text-amber-700 hover:bg-amber-100'
                    }`}
                  >
                    It helped a little
                  </button>
                  <button
                    onClick={() => handleOutcome('not_helped')}
                    className={`px-3 py-1.5 rounded-xl text-xs font-bold cursor-pointer ${
                      caseItem?.outcome === 'not_helped' ? 'bg-rose-600 text-white' : 'bg-rose-50 text-rose-700 hover:bg-rose-100'
                    }`}
                  >
                    It did not help
                  </button>
                </div>
              </div>

              {/* AI Assistance Brief */}
              <div className="bg-indigo-50/70 border border-indigo-100 rounded-2xl p-4">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-1.5 text-xs font-bold text-indigo-900">
                    <Sparkles className="w-4 h-4 text-indigo-600" />
                    <span>Quick summary</span>
                  </div>
                  <button
                    onClick={() => aiBriefMutation.mutate(caseItem?.id || '')}
                    disabled={aiBriefMutation.isPending}
                    className="text-xs font-bold text-indigo-600 hover:text-indigo-800 disabled:opacity-50 cursor-pointer"
                  >
                    {aiBriefMutation.isPending ? 'Writing…' : 'Write a summary'}
                  </button>
                </div>
                {aiBriefMutation.data ? (
                  <div className="mt-2 text-xs space-y-2 text-indigo-950">
                    <p className="font-medium">{aiBriefMutation.data.summary}</p>
                    {aiBriefMutation.data.recommended_actions?.length > 0 && (
                      <div className="mt-2">
                        <span className="font-bold text-xs text-indigo-800 block mb-1">
                          Suggested next steps
                        </span>
                        <ul className="list-disc list-inside space-y-0.5 text-indigo-900">
                          {aiBriefMutation.data.recommended_actions.map((act, i) => (
                            <li key={i}>{act}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                ) : (
                  <p className="text-xs text-indigo-700/80">
                    Get a short summary of this case and suggested next steps.
                  </p>
                )}
              </div>
            </div>
          ) : activeTab === 'interventions' ? (
            <div className="space-y-4">
              <form onSubmit={handleAddIntervention} className="bg-gray-50 p-4 rounded-2xl border border-line space-y-3">
                <p className="text-xs font-bold text-gray-900">Add support for this student</p>
                <div className="grid grid-cols-2 gap-2">
                  <input
                    type="text"
                    value={interventionTitle}
                    onChange={(e) => setInterventionTitle(e.target.value)}
                    placeholder="What will you do? (e.g. Peer tutoring)"
                    className="text-xs p-2 rounded-xl border border-line bg-white"
                    required
                  />
                  <select
                    value={selectedInterventionCat}
                    onChange={(e) => setSelectedInterventionCat(e.target.value)}
                    className="text-xs p-2 rounded-xl border border-line bg-white"
                  >
                    {Object.entries(CATEGORY_LABEL).slice(0, 4).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
                  </select>
                </div>
                <button
                  type="submit"
                  disabled={addInterventionMutation.isPending}
                  className="px-3.5 py-2 rounded-xl bg-slate-900 text-white font-bold text-xs hover:bg-slate-800 cursor-pointer disabled:opacity-50"
                >
                  {addInterventionMutation.isPending ? 'Adding…' : 'Add'}
                </button>
              </form>

              <div className="space-y-2">
                <p className="text-xs font-bold text-gray-500">Support so far</p>
                {interventions.length === 0 ? (
                  <p className="text-xs text-muted italic">No support added yet.</p>
                ) : (
                  interventions.map((inv) => (
                    <div key={inv.id} className="p-3 bg-white border border-line rounded-xl flex justify-between items-center text-xs">
                      <div>
                        <p className="font-bold text-gray-900">{inv.title}</p>
                        <p className="text-muted">{categoryLabel(inv.category)} · {statusLabel(inv.status)}</p>
                      </div>
                      <span className="text-xs text-muted">
                        {inv.target_date ? friendlyDate(inv.target_date) : 'Ongoing'}
                      </span>
                    </div>
                  ))
                )}
              </div>
            </div>
          ) : activeTab === 'notes' ? (
            <div className="space-y-4">
              <form onSubmit={handleAddNote} className="space-y-2">
                <div className="flex items-center gap-1.5 text-xs font-bold text-slate-700">
                  <Lock className="w-3.5 h-3.5 text-amber-600" />
                  <span>Private notes</span>
                </div>
                <textarea
                  rows={3}
                  value={noteContent}
                  onChange={(e) => setNoteContent(e.target.value)}
                  placeholder="What happened, how the student responded, what comes next…"
                  className="w-full text-xs p-3 rounded-2xl border border-line focus:outline-indigo-600 bg-white"
                  required
                />
                <button
                  type="submit"
                  disabled={addNoteMutation.isPending}
                  className="px-4 py-2 rounded-xl bg-indigo-600 text-white font-bold text-xs hover:bg-indigo-700 cursor-pointer disabled:opacity-50 flex items-center gap-1.5"
                >
                  <Send className="w-3.5 h-3.5" />
                  <span>{addNoteMutation.isPending ? 'Saving…' : 'Save Note'}</span>
                </button>
              </form>

              <div className="space-y-2 pt-2">
                <p className="text-xs font-bold text-gray-500">Earlier notes</p>
                {caseItem?.notes?.length ? (
                  caseItem.notes.map((n) => (
                    <div key={n.id} className="p-3 bg-gray-50 border border-line rounded-xl text-xs space-y-1">
                      <div className="flex justify-between text-muted text-xs">
                        <span>{n.author_name || 'Staff'}</span>
                        <span>{friendlyDateTime(n.created_at)}</span>
                      </div>
                      <p className="text-gray-800">{n.content}</p>
                    </div>
                  ))
                ) : (
                  <p className="text-xs text-muted italic">No notes recorded yet.</p>
                )}
              </div>
            </div>
          ) : activeTab === 'followups' ? (
            <div className="space-y-4">
              <div className="space-y-2">
                <p className="text-xs font-bold text-gray-500">Planned follow-ups</p>
                {followups.length === 0 ? (
                  <p className="text-xs text-muted italic">No follow-ups planned yet.</p>
                ) : (
                  followups.map((f) => (
                    <div key={f.id} className="p-3 bg-white border border-line rounded-xl flex justify-between items-center text-xs">
                      <div>
                        <p className="font-bold text-gray-900">{f.title}</p>
                        <p className="text-muted">{statusLabel(f.status)}</p>
                      </div>
                      <span className="text-xs text-gray-500">
                        {friendlyDateTime(f.scheduled_at)}
                      </span>
                    </div>
                  ))
                )}
              </div>
            </div>
          ) : (
            <div className="space-y-3">
              <p className="text-xs font-bold text-gray-500">History of this case</p>
              {events.length === 0 ? (
                <p className="text-xs text-muted italic">Nothing has happened yet.</p>
              ) : (
                <div className="relative border-l-2 border-indigo-200 ml-3 space-y-4 py-2">
                  {events.map((ev) => (
                    <div key={ev.id} className="ml-4 relative">
                      <div className="absolute -left-[23px] top-1 w-3 h-3 rounded-full bg-indigo-600 ring-4 ring-panel" />
                      <p className="text-xs font-bold text-gray-900">
                        Moved to <span className="text-indigo-600">{stageLabel(ev.to_state)}</span>
                      </p>
                      <p className="text-xs text-gray-500">{ev.reason && !/^Transitioned to/.test(ev.reason) ? ev.reason : ''}</p>
                      <span className="text-xs text-muted">
                        {friendlyDateTime(ev.created_at)}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

