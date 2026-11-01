import React, { useState } from 'react'
import {
  Calendar,
  Clock,
  Video,
  MapPin,
  Phone,
  Plus,
  CheckCircle2,
  XCircle,
  AlertCircle,
  RefreshCw,
  Search,
} from 'lucide-react'
import {
  useSessionsList,
  useCreateSession,
  useCompleteSession,
  useCancelSession,
  useRescheduleSession,
} from '../../lib/api/endpoints/sessions.hooks'
import { CounsellingSession } from '../../lib/api/endpoints/sessions'

export function ScheduleSessionsView({ title = 'Schedule & Consultations' }: { title?: string }) {
  const { data: sessions = [], isLoading, error, refetch } = useSessionsList()
  const createMutation = useCreateSession()
  const completeMutation = useCompleteSession()
  const cancelMutation = useCancelSession()
  const rescheduleMutation = useRescheduleSession()

  const [filterStatus, setFilterStatus] = useState<string>('all')
  const [searchTerm, setSearchTerm] = useState('')
  const [isScheduleModalOpen, setIsScheduleModalOpen] = useState(false)
  const [rescheduleTarget, setRescheduleTarget] = useState<CounsellingSession | null>(null)
  const [cancelTarget, setCancelTarget] = useState<CounsellingSession | null>(null)
  const [completeTarget, setCompleteTarget] = useState<CounsellingSession | null>(null)

  // Form states
  const [formData, setFormData] = useState({
    student_id: '',
    scheduled_at: '',
    duration_minutes: 45,
    mode: 'in_person',
    location: '',
    notes: '',
  })
  const [cancelReason, setCancelReason] = useState('')
  const [completionNotes, setCompletionNotes] = useState('')
  const [rescheduleDate, setRescheduleDate] = useState('')

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!formData.student_id || !formData.scheduled_at) return
    try {
      await createMutation.mutateAsync({
        student_id: formData.student_id,
        scheduled_at: new Date(formData.scheduled_at).toISOString(),
        duration_minutes: Number(formData.duration_minutes),
        mode: formData.mode,
        location: formData.location || undefined,
        notes: formData.notes || undefined,
      })
      setIsScheduleModalOpen(false)
      setFormData({
        student_id: '',
        scheduled_at: '',
        duration_minutes: 45,
        mode: 'in_person',
        location: '',
        notes: '',
      })
    } catch (err) {
      console.error(err)
    }
  }

  const handleComplete = async () => {
    if (!completeTarget) return
    try {
      await completeMutation.mutateAsync({
        id: completeTarget.id,
        notes: completionNotes || undefined,
      })
      setCompleteTarget(null)
      setCompletionNotes('')
    } catch (err) {
      console.error(err)
    }
  }

  const handleCancel = async () => {
    if (!cancelTarget || !cancelReason.trim()) return
    try {
      await cancelMutation.mutateAsync({
        id: cancelTarget.id,
        reason: cancelReason.trim(),
      })
      setCancelTarget(null)
      setCancelReason('')
    } catch (err) {
      console.error(err)
    }
  }

  const handleReschedule = async () => {
    if (!rescheduleTarget || !rescheduleDate) return
    try {
      await rescheduleMutation.mutateAsync({
        id: rescheduleTarget.id,
        scheduled_at: new Date(rescheduleDate).toISOString(),
      })
      setRescheduleTarget(null)
      setRescheduleDate('')
    } catch (err) {
      console.error(err)
    }
  }

  const filteredSessions = sessions.filter((s) => {
    const matchesStatus = filterStatus === 'all' || s.status.toLowerCase() === filterStatus.toLowerCase()
    const matchesSearch =
      searchTerm === '' ||
      (s.student_name && s.student_name.toLowerCase().includes(searchTerm.toLowerCase())) ||
      s.student_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (s.location && s.location.toLowerCase().includes(searchTerm.toLowerCase()))
    return matchesStatus && matchesSearch
  })

  return (
    <div className="space-y-6">
      {/* Top Header & Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 bg-white p-5 rounded-2xl border border-line shadow-xs">
        <div>
          <h2 className="text-xl font-bold text-gray-900">{title}</h2>
          <p className="text-sm text-gray-500 mt-1">
            Coordinate student advisory sessions, confidential counseling appointments, and office hours.
          </p>
        </div>
        <button
          type="button"
          onClick={() => setIsScheduleModalOpen(true)}
          className="inline-flex items-center gap-2 px-4 py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold rounded-xl shadow-xs transition"
        >
          <Plus className="w-4 h-4" />
          <span>Book Session</span>
        </button>
      </div>

      {/* Filters and Search Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
        <div className="flex items-center gap-1.5 p-1 bg-gray-100/80 rounded-xl w-fit">
          {['all', 'scheduled', 'completed', 'cancelled'].map((tab) => (
            <button
              key={tab}
              type="button"
              onClick={() => setFilterStatus(tab)}
              className={`px-3 py-1.5 text-xs font-semibold rounded-lg capitalize transition ${
                filterStatus === tab
                  ? 'bg-white text-gray-900 shadow-xs'
                  : 'text-gray-500 hover:text-gray-900'
              }`}
            >
              {tab}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-2">
          <div className="relative">
            <Search className="w-4 h-4 text-muted absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search student or location..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-9 pr-3 py-1.5 text-xs bg-white border border-line rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 w-64"
            />
          </div>
          <button
            type="button"
            onClick={() => void refetch()}
            className="p-2 text-gray-500 hover:text-gray-800 bg-white border border-line rounded-xl transition"
            title="Refresh"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Sessions Content */}
      {isLoading ? (
        <div className="p-12 text-center text-sm text-gray-500 bg-white rounded-2xl border border-line">
          Loading sessions...
        </div>
      ) : error ? (
        <div className="p-6 bg-red-50 text-red-700 rounded-2xl border border-red-200 text-sm flex items-center gap-3">
          <AlertCircle className="w-5 h-5 shrink-0" />
          <div>
            <p className="font-semibold">Unable to load sessions</p>
            <p className="text-xs text-red-600 mt-0.5">{(error as Error).message}</p>
          </div>
        </div>
      ) : filteredSessions.length === 0 ? (
        <div className="p-12 text-center bg-white rounded-2xl border border-line shadow-xs">
          <Calendar className="w-10 h-10 text-gray-300 mx-auto mb-3" />
          <h3 className="text-base font-semibold text-gray-800">No sessions found</h3>
          <p className="text-xs text-gray-500 mt-1 max-w-sm mx-auto">
            {filterStatus === 'all'
              ? 'There are currently no scheduled appointments or consultations.'
              : `No sessions found with status "${filterStatus}".`}
          </p>
          <button
            type="button"
            onClick={() => setIsScheduleModalOpen(true)}
            className="mt-4 inline-flex items-center gap-2 px-3.5 py-2 bg-blue-50 text-blue-700 text-xs font-semibold rounded-lg hover:bg-blue-100 transition"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Schedule First Session</span>
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredSessions.map((session) => {
            const date = new Date(session.scheduled_at)
            const dateStr = date.toLocaleDateString(undefined, {
              weekday: 'short',
              month: 'short',
              day: 'numeric',
            })
            const timeStr = date.toLocaleTimeString(undefined, {
              hour: 'numeric',
              minute: '2-digit',
            })

            const statusStyles =
              session.status === 'scheduled'
                ? 'bg-blue-50 text-blue-700 border-blue-200'
                : session.status === 'completed'
                ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                : 'bg-gray-100 text-gray-600 border-line'

            return (
              <div
                key={session.id}
                className="bg-white rounded-2xl p-5 border border-line shadow-xs flex flex-col justify-between hover:shadow-md transition"
              >
                <div>
                  <div className="flex items-center justify-between gap-2 mb-3">
                    <span
                      className={`text-[11px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded-full border ${statusStyles}`}
                    >
                      {session.status}
                    </span>
                    <span className="text-xs font-medium text-gray-500 flex items-center gap-1">
                      <Clock className="w-3.5 h-3.5" />
                      {session.duration_minutes}m
                    </span>
                  </div>

                  <h3 className="font-semibold text-gray-900 text-base">
                    {session.student_name || `Student (${session.student_id.slice(0, 8)})`}
                  </h3>
                  <p className="text-xs text-gray-500 mt-0.5 font-mono">
                    ID: {session.student_id}
                  </p>

                  <div className="mt-4 space-y-2 text-xs text-gray-600">
                    <div className="flex items-center gap-2">
                      <Calendar className="w-4 h-4 text-muted shrink-0" />
                      <span>{dateStr} at {timeStr}</span>
                    </div>

                    <div className="flex items-center gap-2 capitalize">
                      {session.mode === 'video' ? (
                        <Video className="w-4 h-4 text-indigo-500 shrink-0" />
                      ) : session.mode === 'phone' ? (
                        <Phone className="w-4 h-4 text-emerald-500 shrink-0" />
                      ) : (
                        <MapPin className="w-4 h-4 text-amber-500 shrink-0" />
                      )}
                      <span>
                        {session.mode.replace('_', ' ')}
                        {session.location ? ` • ${session.location}` : ''}
                      </span>
                    </div>

                    {session.notes && (
                      <div className="mt-2 p-2 bg-gray-50 rounded-lg text-xs text-gray-600 italic">
                        "{session.notes}"
                      </div>
                    )}
                  </div>
                </div>

                {/* Session Actions for Scheduled Sessions */}
                {session.status === 'scheduled' && (
                  <div className="mt-5 pt-4 border-t border-line flex items-center justify-between gap-2">
                    <button
                      type="button"
                      onClick={() => setCompleteTarget(session)}
                      className="inline-flex items-center gap-1 px-2.5 py-1.5 bg-emerald-50 text-emerald-700 hover:bg-emerald-100 text-xs font-medium rounded-lg transition"
                    >
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      Complete
                    </button>
                    <div className="flex items-center gap-1.5">
                      <button
                        type="button"
                        onClick={() => {
                          setRescheduleTarget(session)
                          setRescheduleDate(session.scheduled_at.slice(0, 16))
                        }}
                        className="px-2 py-1.5 text-xs text-gray-600 hover:text-gray-900 hover:bg-gray-50 rounded-lg transition"
                      >
                        Reschedule
                      </button>
                      <button
                        type="button"
                        onClick={() => setCancelTarget(session)}
                        className="p-1.5 text-red-500 hover:bg-red-50 rounded-lg transition"
                        title="Cancel Session"
                      >
                        <XCircle className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}

      {/* Book Session Modal */}
      {isScheduleModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-line animate-in fade-in duration-150">
            <h3 className="text-lg font-bold text-gray-900 mb-1">Book Consultation Session</h3>
            <p className="text-xs text-gray-500 mb-4">
              Schedule a one-on-one advising appointment or counselling check-in.
            </p>

            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">
                  Student ID or Reference *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. STU-CB368B3E or UUID"
                  value={formData.student_id}
                  onChange={(e) => setFormData({ ...formData, student_id: e.target.value })}
                  className="w-full px-3 py-2 text-xs border border-line rounded-xl focus:ring-2 focus:ring-blue-500 focus:outline-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-gray-700 mb-1">
                    Date & Time *
                  </label>
                  <input
                    type="datetime-local"
                    required
                    value={formData.scheduled_at}
                    onChange={(e) => setFormData({ ...formData, scheduled_at: e.target.value })}
                    className="w-full px-3 py-2 text-xs border border-line rounded-xl focus:ring-2 focus:ring-blue-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-gray-700 mb-1">
                    Duration
                  </label>
                  <select
                    value={formData.duration_minutes}
                    onChange={(e) =>
                      setFormData({ ...formData, duration_minutes: Number(e.target.value) })
                    }
                    className="w-full px-3 py-2 text-xs border border-line rounded-xl focus:ring-2 focus:ring-blue-500 focus:outline-none bg-white"
                  >
                    <option value={15}>15 Minutes</option>
                    <option value={30}>30 Minutes</option>
                    <option value={45}>45 Minutes</option>
                    <option value={60}>60 Minutes</option>
                    <option value={90}>90 Minutes</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-gray-700 mb-1">
                    Mode
                  </label>
                  <select
                    value={formData.mode}
                    onChange={(e) => setFormData({ ...formData, mode: e.target.value })}
                    className="w-full px-3 py-2 text-xs border border-line rounded-xl focus:ring-2 focus:ring-blue-500 focus:outline-none bg-white"
                  >
                    <option value="in_person">In-Person</option>
                    <option value="video">Google Meet / Video</option>
                    <option value="phone">Phone Consultation</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-gray-700 mb-1">
                    Location / Link
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. Room 204 or Meet URL"
                    value={formData.location}
                    onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                    className="w-full px-3 py-2 text-xs border border-line rounded-xl focus:ring-2 focus:ring-blue-500 focus:outline-none"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">
                  Session Agenda / Notes
                </label>
                <textarea
                  rows={2}
                  placeholder="Optional confidential notes or meeting agenda..."
                  value={formData.notes}
                  onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                  className="w-full px-3 py-2 text-xs border border-line rounded-xl focus:ring-2 focus:ring-blue-500 focus:outline-none"
                />
              </div>

              {createMutation.isError && (
                <p className="text-xs text-red-600 bg-red-50 p-2 rounded-lg">
                  {(createMutation.error as Error).message}
                </p>
              )}

              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setIsScheduleModalOpen(false)}
                  className="px-3 py-1.5 text-xs text-gray-600 hover:bg-gray-100 rounded-lg transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={createMutation.isPending}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-lg disabled:opacity-50 transition"
                >
                  {createMutation.isPending ? 'Scheduling...' : 'Schedule Session'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Complete Session Modal */}
      {completeTarget && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-line animate-in fade-in duration-150">
            <h3 className="text-lg font-bold text-gray-900 mb-1">Complete Consultation</h3>
            <p className="text-xs text-gray-500 mb-4">
              Mark session with{' '}
              <span className="font-medium text-gray-800">
                {completeTarget.student_name || completeTarget.student_id}
              </span>{' '}
              as concluded.
            </p>

            <div className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">
                  Completion Summary / Outcomes
                </label>
                <textarea
                  rows={3}
                  placeholder="Summary of recommendations, next steps or support provided..."
                  value={completionNotes}
                  onChange={(e) => setCompletionNotes(e.target.value)}
                  className="w-full px-3 py-2 text-xs border border-line rounded-xl focus:ring-2 focus:ring-emerald-500 focus:outline-none"
                />
              </div>

              {completeMutation.isError && (
                <p className="text-xs text-red-600 bg-red-50 p-2 rounded-lg">
                  {(completeMutation.error as Error).message}
                </p>
              )}

              <div className="flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setCompleteTarget(null)}
                  className="px-3 py-1.5 text-xs text-gray-600 hover:bg-gray-100 rounded-lg transition"
                >
                  Close
                </button>
                <button
                  type="button"
                  onClick={handleComplete}
                  disabled={completeMutation.isPending}
                  className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold rounded-lg disabled:opacity-50 transition"
                >
                  {completeMutation.isPending ? 'Marking Complete...' : 'Confirm Concluded'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Cancel Session Modal */}
      {cancelTarget && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-line animate-in fade-in duration-150">
            <h3 className="text-lg font-bold text-gray-900 mb-1">Cancel Consultation</h3>
            <p className="text-xs text-gray-500 mb-4">
              Please state a reason for cancelling this appointment. The student will be notified.
            </p>

            <div className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">
                  Cancellation Reason *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Schedule conflict, rescheduled by student request"
                  value={cancelReason}
                  onChange={(e) => setCancelReason(e.target.value)}
                  className="w-full px-3 py-2 text-xs border border-line rounded-xl focus:ring-2 focus:ring-red-500 focus:outline-none"
                />
              </div>

              {cancelMutation.isError && (
                <p className="text-xs text-red-600 bg-red-50 p-2 rounded-lg">
                  {(cancelMutation.error as Error).message}
                </p>
              )}

              <div className="flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setCancelTarget(null)}
                  className="px-3 py-1.5 text-xs text-gray-600 hover:bg-gray-100 rounded-lg transition"
                >
                  Keep Session
                </button>
                <button
                  type="button"
                  onClick={handleCancel}
                  disabled={cancelMutation.isPending || !cancelReason.trim()}
                  className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white text-xs font-semibold rounded-lg disabled:opacity-50 transition"
                >
                  {cancelMutation.isPending ? 'Cancelling...' : 'Cancel Appointment'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Reschedule Modal */}
      {rescheduleTarget && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-line animate-in fade-in duration-150">
            <h3 className="text-lg font-bold text-gray-900 mb-1">Reschedule Session</h3>
            <p className="text-xs text-gray-500 mb-4">
              Select a new date and time for the consultation.
            </p>

            <div className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">
                  New Date & Time *
                </label>
                <input
                  type="datetime-local"
                  required
                  value={rescheduleDate}
                  onChange={(e) => setRescheduleDate(e.target.value)}
                  className="w-full px-3 py-2 text-xs border border-line rounded-xl focus:ring-2 focus:ring-blue-500 focus:outline-none"
                />
              </div>

              {rescheduleMutation.isError && (
                <p className="text-xs text-red-600 bg-red-50 p-2 rounded-lg">
                  {(rescheduleMutation.error as Error).message}
                </p>
              )}

              <div className="flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setRescheduleTarget(null)}
                  className="px-3 py-1.5 text-xs text-gray-600 hover:bg-gray-100 rounded-lg transition"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleReschedule}
                  disabled={rescheduleMutation.isPending || !rescheduleDate}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-lg disabled:opacity-50 transition"
                >
                  {rescheduleMutation.isPending ? 'Updating...' : 'Update Time'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

