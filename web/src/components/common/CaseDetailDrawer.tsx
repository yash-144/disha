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
        reason: `Transitioned to ${toState} by ${userRole || 'staff'}`,
      },
      {
        onSuccess: () => setFeedbackMsg({ ok: true, text: `Case transitioned to ${toState}.` }),
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
        onSuccess: () => setFeedbackMsg({ ok: true, text: `Case outcome recorded as ${outcome}.` }),
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
          setFeedbackMsg({ ok: true, text: 'Note appended securely.' })
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
          setFeedbackMsg({ ok: true, text: 'Intervention linked to student trajectory.' })
        },
        onError: (e) => setFeedbackMsg({ ok: false, text: errorMessage(e) }),
      }
    )
  }

  return (
    <div className="fixed inset-0 z-50 overflow-hidden bg-black/40 backdrop-blur-xs flex justify-end">
      <div className="w-full max-w-2xl bg-white h-full shadow-2xl flex flex-col font-sans animate-in slide-in-from-right duration-200">
        {/* Header */}
        <div className="p-5 border-b border-gray-100 flex items-start justify-between bg-slate-900 text-white">
          <div>
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs px-2.5 py-0.5 rounded-full bg-white/10 uppercase tracking-wider">
                {caseItem?.priority || 'normal'} priority
              </span>
              <span className="text-xs px-2.5 py-0.5 rounded-full bg-indigo-500/30 text-indigo-200 font-semibold uppercase">
                {caseItem?.state || 'loading'}
              </span>
              {caseItem?.is_overdue && (
                <span className="text-xs px-2 py-0.5 rounded-full bg-rose-500 text-white font-bold flex items-center gap-1">
                  <AlertTriangle className="w-3 h-3" /> Overdue
                </span>
              )}
            </div>
            <h2 className="text-xl font-bold mt-2">
              {caseItem?.student_name ?? caseItem?.student_ref ?? 'Student Case'}
            </h2>
            <p className="text-xs text-slate-300 mt-0.5">
              Case ID: <span className="font-mono">{caseId}</span> • Version {caseItem?.version}
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
        <div className="flex border-b border-gray-100 px-5 bg-gray-50/50 text-xs font-semibold text-gray-500">
          {(['overview', 'interventions', 'followups', 'notes', 'audit'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`py-3 px-3 border-b-2 capitalize transition cursor-pointer ${
                activeTab === tab
                  ? 'border-indigo-600 text-indigo-600 font-bold'
                  : 'border-transparent hover:text-gray-900'
              }`}
            >
              {tab}
            </button>
          ))}
        </div>

        {/* Content Area */}
        <div className="flex-1 overflow-y-auto p-5 text-sm space-y-5">
          {isLoading ? (
            <div className="py-20 text-center text-gray-400 text-xs">Loading case details...</div>
          ) : activeTab === 'overview' ? (
            <div className="space-y-5">
              {/* Case Summary */}
              <div className="bg-gray-50 rounded-2xl p-4 border border-gray-100 text-xs leading-relaxed text-gray-700">
                <p className="font-bold text-gray-900 mb-1">Observation & Triage Context</p>
                {caseItem?.summary || 'No description provided.'}
              </div>

              {/* State Machine Action Bar */}
              <div className="bg-white rounded-2xl p-4 border border-gray-200/80 shadow-xs">
                <h3 className="text-xs font-bold uppercase tracking-wider text-gray-500 mb-3">
                  Workflow Lifecycle Transitions
                </h3>
                <div className="flex flex-wrap gap-2">
                  {caseItem?.state === 'suggested' && (
                    <>
                      <button
                        onClick={() => handleTransition('open')}
                        className="px-3.5 py-1.5 rounded-xl bg-purple-700 text-white font-bold text-xs hover:bg-purple-800 cursor-pointer"
                      >
                        Accept Case
                      </button>
                      <button
                        onClick={() => handleTransition('dismissed')}
                        className="px-3.5 py-1.5 rounded-xl border border-gray-200 text-gray-700 font-semibold text-xs hover:bg-gray-50 cursor-pointer"
                      >
                        Dismiss
                      </button>
                    </>
                  )}
                  {caseItem?.state === 'open' && (
                    <>
                      <button
                        onClick={() => handleTransition('in_review')}
                        className="px-3.5 py-1.5 rounded-xl bg-indigo-600 text-white font-bold text-xs hover:bg-indigo-700 cursor-pointer"
                      >
                        Start Review
                      </button>
                      <button
                        onClick={() => handleTransition('assigned')}
                        className="px-3.5 py-1.5 rounded-xl bg-blue-600 text-white font-bold text-xs hover:bg-blue-700 cursor-pointer"
                      >
                        Mark Assigned
                      </button>
                    </>
                  )}
                  {(caseItem?.state === 'in_review' || caseItem?.state === 'assigned') && (
                    <button
                      onClick={() => handleTransition('action_planned')}
                      className="px-3.5 py-1.5 rounded-xl bg-amber-600 text-white font-bold text-xs hover:bg-amber-700 cursor-pointer"
                    >
                      Plan Action
                    </button>
                  )}
                  {caseItem?.state === 'action_planned' && (
                    <button
                      onClick={() => handleTransition('in_progress')}
                      className="px-3.5 py-1.5 rounded-xl bg-emerald-600 text-white font-bold text-xs hover:bg-emerald-700 cursor-pointer"
                    >
                      Start Execution
                    </button>
                  )}
                  {caseItem?.state === 'in_progress' && (
                    <>
                      <button
                        onClick={() => handleTransition('follow_up_scheduled')}
                        className="px-3.5 py-1.5 rounded-xl bg-sky-600 text-white font-bold text-xs hover:bg-sky-700 cursor-pointer"
                      >
                        Schedule Follow-up
                      </button>
                      <button
                        onClick={() => handleTransition('closed')}
                        className="px-3.5 py-1.5 rounded-xl bg-slate-800 text-white font-bold text-xs hover:bg-slate-900 cursor-pointer"
                      >
                        Close Case
                      </button>
                    </>
                  )}
                  {caseItem?.state === 'closed' && (
                    <button
                      onClick={() => handleTransition('reopened')}
                      className="px-3.5 py-1.5 rounded-xl bg-rose-600 text-white font-bold text-xs hover:bg-rose-700 cursor-pointer"
                    >
                      Reopen Case
                    </button>
                  )}
                </div>
              </div>

              {/* Record Outcome (Closes the accountable loop) */}
              <div className="bg-white rounded-2xl p-4 border border-gray-200/80 shadow-xs">
                <h3 className="text-xs font-bold uppercase tracking-wider text-gray-500 mb-2">
                  Accountable Outcome Record
                </h3>
                <p className="text-xs text-gray-500 mb-3">
                  Did the student benefit from this intervention plan? (Requires 85% precision calibration feedback).
                </p>
                <div className="flex gap-2">
                  <button
                    onClick={() => handleOutcome('helped')}
                    className={`px-3 py-1.5 rounded-xl text-xs font-bold cursor-pointer ${
                      caseItem?.outcome === 'helped' ? 'bg-emerald-600 text-white' : 'bg-emerald-50 text-emerald-700 hover:bg-emerald-100'
                    }`}
                  >
                    ✓ Helped
                  </button>
                  <button
                    onClick={() => handleOutcome('mixed')}
                    className={`px-3 py-1.5 rounded-xl text-xs font-bold cursor-pointer ${
                      caseItem?.outcome === 'mixed' ? 'bg-amber-600 text-white' : 'bg-amber-50 text-amber-700 hover:bg-amber-100'
                    }`}
                  >
                    ~ Mixed
                  </button>
                  <button
                    onClick={() => handleOutcome('not_helped')}
                    className={`px-3 py-1.5 rounded-xl text-xs font-bold cursor-pointer ${
                      caseItem?.outcome === 'not_helped' ? 'bg-rose-600 text-white' : 'bg-rose-50 text-rose-700 hover:bg-rose-100'
                    }`}
                  >
                    ✗ Not Helped
                  </button>
                </div>
              </div>

              {/* AI Assistance Brief */}
              <div className="bg-indigo-50/70 border border-indigo-100 rounded-2xl p-4">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-1.5 text-xs font-bold text-indigo-900">
                    <Sparkles className="w-4 h-4 text-indigo-600" />
                    <span>AI Review Brief</span>
                  </div>
                  <button
                    onClick={() => aiBriefMutation.mutate(caseItem?.id || '')}
                    disabled={aiBriefMutation.isPending}
                    className="text-xs font-bold text-indigo-600 hover:text-indigo-800 disabled:opacity-50 cursor-pointer"
                  >
                    {aiBriefMutation.isPending ? 'Analyzing case...' : 'Generate AI Brief'}
                  </button>
                </div>
                {aiBriefMutation.data ? (
                  <div className="mt-2 text-xs space-y-2 text-indigo-950">
                    <p className="font-medium">{aiBriefMutation.data.summary}</p>
                    {aiBriefMutation.data.recommended_actions?.length > 0 && (
                      <div className="mt-2">
                        <span className="font-bold text-[11px] uppercase tracking-wider text-indigo-800 block mb-1">
                          Recommended Protocols
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
                    Click "Generate AI Brief" for automated signal synthesis and protocol recommendations.
                  </p>
                )}
              </div>
            </div>
          ) : activeTab === 'interventions' ? (
            <div className="space-y-4">
              <form onSubmit={handleAddIntervention} className="bg-gray-50 p-4 rounded-2xl border border-gray-100 space-y-3">
                <p className="text-xs font-bold text-gray-900">Attach Intervention Protocol</p>
                <div className="grid grid-cols-2 gap-2">
                  <input
                    type="text"
                    value={interventionTitle}
                    onChange={(e) => setInterventionTitle(e.target.value)}
                    placeholder="Intervention title (e.g. Peer Tutoring CS201)"
                    className="text-xs p-2 rounded-xl border border-gray-200 bg-white"
                    required
                  />
                  <select
                    value={selectedInterventionCat}
                    onChange={(e) => setSelectedInterventionCat(e.target.value)}
                    className="text-xs p-2 rounded-xl border border-gray-200 bg-white"
                  >
                    <option value="academic_advising">Academic Advising</option>
                    <option value="tutoring">Peer Tutoring</option>
                    <option value="counselling">Confidential Counselling</option>
                    <option value="financial_aid">Emergency Financial Aid</option>
                  </select>
                </div>
                <button
                  type="submit"
                  disabled={addInterventionMutation.isPending}
                  className="px-3.5 py-2 rounded-xl bg-slate-900 text-white font-bold text-xs hover:bg-slate-800 cursor-pointer disabled:opacity-50"
                >
                  {addInterventionMutation.isPending ? 'Attaching...' : 'Attach to Case'}
                </button>
              </form>

              <div className="space-y-2">
                <p className="text-xs font-bold text-gray-500 uppercase tracking-wider">Active Interventions</p>
                {interventions.length === 0 ? (
                  <p className="text-xs text-gray-400 italic">No interventions linked yet.</p>
                ) : (
                  interventions.map((inv) => (
                    <div key={inv.id} className="p-3 bg-white border border-gray-100 rounded-xl flex justify-between items-center text-xs">
                      <div>
                        <p className="font-bold text-gray-900">{inv.title}</p>
                        <p className="text-[#717E95] capitalize">{inv.category.replace('_', ' ')} • {inv.status}</p>
                      </div>
                      <span className="text-[11px] font-mono text-gray-400">
                        {inv.target_date ? new Date(inv.target_date).toLocaleDateString() : 'Ongoing'}
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
                  <span>Encrypted Case & Clinical Notes</span>
                </div>
                <textarea
                  rows={3}
                  value={noteContent}
                  onChange={(e) => setNoteContent(e.target.value)}
                  placeholder="Record intervention notes, student responses, or next steps..."
                  className="w-full text-xs p-3 rounded-2xl border border-gray-200 focus:outline-indigo-600 bg-white"
                  required
                />
                <button
                  type="submit"
                  disabled={addNoteMutation.isPending}
                  className="px-4 py-2 rounded-xl bg-indigo-600 text-white font-bold text-xs hover:bg-indigo-700 cursor-pointer disabled:opacity-50 flex items-center gap-1.5"
                >
                  <Send className="w-3.5 h-3.5" />
                  <span>{addNoteMutation.isPending ? 'Encrypting & Saving...' : 'Save Note'}</span>
                </button>
              </form>

              <div className="space-y-2 pt-2">
                <p className="text-xs font-bold text-gray-500 uppercase tracking-wider">Note History</p>
                {caseItem?.notes?.length ? (
                  caseItem.notes.map((n) => (
                    <div key={n.id} className="p-3 bg-gray-50 border border-gray-100 rounded-xl text-xs space-y-1">
                      <div className="flex justify-between text-gray-400 text-[10px]">
                        <span>{n.author_name || 'Staff Note'}</span>
                        <span>{new Date(n.created_at).toLocaleString()}</span>
                      </div>
                      <p className="text-gray-800">{n.content}</p>
                    </div>
                  ))
                ) : (
                  <p className="text-xs text-gray-400 italic">No notes recorded yet.</p>
                )}
              </div>
            </div>
          ) : activeTab === 'followups' ? (
            <div className="space-y-4">
              <div className="space-y-2">
                <p className="text-xs font-bold text-gray-500 uppercase tracking-wider">Scheduled Follow-ups</p>
                {followups.length === 0 ? (
                  <p className="text-xs text-gray-400 italic">No follow-ups scheduled for this case.</p>
                ) : (
                  followups.map((f) => (
                    <div key={f.id} className="p-3 bg-white border border-gray-100 rounded-xl flex justify-between items-center text-xs">
                      <div>
                        <p className="font-bold text-gray-900">{f.title}</p>
                        <p className="text-[#717E95]">{f.status}</p>
                      </div>
                      <span className="text-[11px] text-gray-500">
                        {new Date(f.scheduled_at).toLocaleString()}
                      </span>
                    </div>
                  ))
                )}
              </div>
            </div>
          ) : (
            <div className="space-y-3">
              <p className="text-xs font-bold text-gray-500 uppercase tracking-wider">Immutable Audit Trail</p>
              {events.length === 0 ? (
                <p className="text-xs text-gray-400 italic">No audit events recorded yet.</p>
              ) : (
                <div className="relative border-l-2 border-indigo-200 ml-3 space-y-4 py-2">
                  {events.map((ev) => (
                    <div key={ev.id} className="ml-4 relative">
                      <div className="absolute -left-[23px] top-1 w-3 h-3 rounded-full bg-indigo-600 ring-4 ring-white" />
                      <p className="text-xs font-bold text-gray-900">
                        Transitioned to <span className="text-indigo-600 uppercase font-mono">{ev.to_state}</span>
                      </p>
                      <p className="text-[11px] text-gray-500">{ev.reason || 'Workflow state transition'}</p>
                      <span className="text-[10px] text-gray-400 font-mono">
                        {new Date(ev.created_at).toLocaleString()}
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
