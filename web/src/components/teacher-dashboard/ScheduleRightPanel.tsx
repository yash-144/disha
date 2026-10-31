import React, { useState } from 'react'
import { Plus, Video, Calendar, Users, Check, X } from 'lucide-react'

export interface UpcomingSession {
  id: string
  title: string
  time: string
  iconType: 'calendar' | 'video' | 'users'
  avatars: string[]
  extraCount?: number
}

export interface PendingRequest {
  id: string
  title: string
  time: string
}

const INITIAL_UPCOMING_SESSIONS: UpcomingSession[] = [
  {
    id: 'up-1',
    title: 'Case Review Meeting',
    time: 'Today, 12:30 – 13:30',
    iconType: 'calendar',
    avatars: [
      'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=100&q=80',
      'https://images.unsplash.com/photo-1517841905240-472988babdf9?auto=format&fit=crop&w=100&q=80',
    ],
    extraCount: 2,
  },
  {
    id: 'up-2',
    title: '1-on-1 with Asha V.',
    time: 'Today, 14:30 – 15:15',
    iconType: 'video',
    avatars: [
      'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=100&q=80',
    ],
  },
  {
    id: 'up-3',
    title: '1-on-1 with Rohan M.',
    time: 'Today, 16:30 – 17:00',
    iconType: 'video',
    avatars: [
      'https://images.unsplash.com/photo-1539571696357-5a69c17a67c6?auto=format&fit=crop&w=100&q=80',
    ],
  },
  {
    id: 'up-4',
    title: 'Mentor Sync',
    time: 'Today, 18:00 – 19:00',
    iconType: 'users',
    avatars: [
      'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=100&q=80',
    ],
  },
]

const INITIAL_PENDING_REQUESTS: PendingRequest[] = [
  {
    id: 'pen-1',
    title: 'Check-in with Neha K.',
    time: 'Tomorrow, 11:00 – 11:30',
  },
  {
    id: 'pen-2',
    title: 'Case Discussion (Student Group)',
    time: '03 Jan, 15:00 – 15:45',
  },
]

interface ScheduleRightPanelProps {
  onScheduleClick: () => void
  onInstantCallClick: () => void
  onAcceptRequest?: (req: PendingRequest) => void
  onDeclineRequest?: (req: PendingRequest) => void
}

export function ScheduleRightPanel({
  onScheduleClick,
  onInstantCallClick,
  onAcceptRequest,
  onDeclineRequest,
}: ScheduleRightPanelProps) {
  const [upcomingSessions, setUpcomingSessions] = useState<UpcomingSession[]>(INITIAL_UPCOMING_SESSIONS)
  const [pendingRequests, setPendingRequests] = useState<PendingRequest[]>(INITIAL_PENDING_REQUESTS)

  const handleAccept = (req: PendingRequest) => {
    setPendingRequests((prev) => prev.filter((p) => p.id !== req.id))
    setUpcomingSessions((prev) => [
      ...prev,
      {
        id: `acc-${Date.now()}`,
        title: req.title,
        time: req.time,
        iconType: 'calendar',
        avatars: [
          'https://images.unsplash.com/photo-1517841905240-472988babdf9?auto=format&fit=crop&w=100&q=80',
        ],
      },
    ])
    onAcceptRequest?.(req)
  }

  const handleDecline = (req: PendingRequest) => {
    setPendingRequests((prev) => prev.filter((p) => p.id !== req.id))
    onDeclineRequest?.(req)
  }

  const renderIcon = (type: UpcomingSession['iconType']) => {
    switch (type) {
      case 'calendar':
        return <Calendar className="w-4 h-4 text-[#7C3AED]" />
      case 'video':
        return <Video className="w-4 h-4 text-[#2563EB]" />
      case 'users':
        return <Users className="w-4 h-4 text-[#1E2433]" />
    }
  }

  return (
    <aside className="w-76 xl:w-80 shrink-0 flex flex-col gap-4 font-sans">
      {/* A. Quick Actions */}
      <div className="space-y-2">
        <button
          type="button"
          onClick={onScheduleClick}
          className="w-full flex items-center justify-center gap-2 py-3 px-4 rounded-2xl bg-[#1E2433] text-white text-xs font-semibold shadow-xs hover:bg-[#2B3347] transition cursor-pointer"
        >
          <Plus className="w-4 h-4" />
          <span>Schedule a Session</span>
        </button>

        <button
          type="button"
          onClick={onInstantCallClick}
          className="w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-2xl bg-white text-[#1E2433] text-xs font-semibold border border-gray-200/90 shadow-2xs hover:bg-gray-50 transition cursor-pointer"
        >
          <Video className="w-4 h-4 text-[#1E2433]" />
          <span>Start Instant Call</span>
        </button>
      </div>

      {/* B. Upcoming Sessions */}
      <div>
        <div className="flex items-center justify-between pb-2.5">
          <h2 className="text-sm font-bold text-[#1E2433]">Upcoming Sessions</h2>
          <button
            type="button"
            className="text-xs font-medium text-[#717E95] hover:text-[#1E2433] transition"
          >
            View All
          </button>
        </div>

        <div className="space-y-2">
          {upcomingSessions.map((session) => (
            <div
              key={session.id}
              className="bg-white rounded-2xl p-2.5 px-3 flex items-center justify-between shadow-2xs border border-gray-100/60 hover:shadow-xs transition"
            >
              <div className="flex items-center gap-2.5 min-w-0">
                <span className="flex items-center justify-center w-7 h-7 rounded-xl bg-gray-50 shrink-0">
                  {renderIcon(session.iconType)}
                </span>
                <div className="min-w-0">
                  <h3 className="text-xs font-bold text-[#1E2433] truncate leading-tight">
                    {session.title}
                  </h3>
                  <p className="text-[10px] text-[#717E95] font-medium mt-0.5">
                    {session.time}
                  </p>
                </div>
              </div>

              {/* Avatars */}
              <div className="flex items-center -space-x-1.5 shrink-0 ml-2">
                {session.avatars.map((url, i) => (
                  <img
                    key={i}
                    src={url}
                    alt="Participant"
                    className="w-5 h-5 rounded-full object-cover border border-white"
                  />
                ))}
                {session.extraCount ? (
                  <span className="flex items-center justify-center w-5 h-5 rounded-full bg-[#1E2433] text-white text-[8px] font-bold border border-white">
                    +{session.extraCount}
                  </span>
                ) : null}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* C. Pending Requests */}
      <div>
        <div className="flex items-center justify-between pb-2.5 pt-1">
          <h2 className="text-sm font-bold text-[#1E2433]">
            Pending Requests ({pendingRequests.length})
          </h2>
        </div>

        {pendingRequests.length === 0 ? (
          <div className="bg-white/60 rounded-2xl p-4 text-center border border-dashed border-gray-200">
            <p className="text-xs text-gray-500 font-medium">
              No pending session requests.
            </p>
          </div>
        ) : (
          <div className="space-y-2">
            {pendingRequests.map((req) => (
              <div
                key={req.id}
                className="bg-white rounded-2xl p-3 flex items-center justify-between shadow-2xs border border-gray-100/60"
              >
                <div className="flex items-center gap-2.5 min-w-0">
                  <span className="flex items-center justify-center w-7 h-7 rounded-xl bg-gray-50 text-gray-600 shrink-0">
                    <Calendar className="w-4 h-4 text-gray-500" />
                  </span>
                  <div className="min-w-0">
                    <h3 className="text-xs font-bold text-[#1E2433] truncate leading-tight">
                      {req.title}
                    </h3>
                    <p className="text-[10px] text-[#717E95] font-medium mt-0.5">
                      {req.time}
                    </p>
                  </div>
                </div>

                {/* Actions: Accept & Decline */}
                <div className="flex items-center gap-1.5 shrink-0 ml-2">
                  <button
                    type="button"
                    onClick={() => handleAccept(req)}
                    aria-label={`Accept ${req.title}`}
                    className="flex items-center justify-center w-6 h-6 rounded-full bg-[#EAF7EE] text-[#16A34A] border border-[#BBF7D0] hover:bg-[#DCFCE7] transition cursor-pointer"
                  >
                    <Check className="w-3.5 h-3.5 stroke-[2.5]" />
                  </button>
                  <button
                    type="button"
                    onClick={() => handleDecline(req)}
                    aria-label={`Decline ${req.title}`}
                    className="flex items-center justify-center w-6 h-6 rounded-full bg-[#FEE2E2] text-[#DC2626] border border-[#FECACA] hover:bg-[#FEE2E2] transition cursor-pointer"
                  >
                    <X className="w-3.5 h-3.5 stroke-[2.5]" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </aside>
  )
}

