import React from 'react'
import {
  MessageSquare,
  CheckCheck,
  Bell,
  Clock,
  Sparkles,
  Shield,
  Calendar,
  AlertTriangle,
} from 'lucide-react'
import {
  useStudentNotifications,
  useMarkNotificationRead,
  useMarkAllNotificationsRead,
} from '../../lib/api/endpoints/student.hooks'
import { friendlyDateTime, friendlyError } from '../../lib/labels'

export function StudentMessagesPage() {
  const { data: notifications = [], isLoading, error, refetch } = useStudentNotifications()
  const markRead = useMarkNotificationRead()
  const markAllRead = useMarkAllNotificationsRead()

  const unreadCount = notifications.filter((n) => !n.is_read).length

  const getIcon = (type: string) => {
    switch (type?.toLowerCase()) {
      case 'session':
      case 'consultation':
        return <Calendar className="w-4 h-4 text-blue-600" />
      case 'alert':
      case 'urgent':
        return <AlertTriangle className="w-4 h-4 text-amber-600" />
      case 'mentor':
        return <Sparkles className="w-4 h-4 text-purple-600" />
      default:
        return <MessageSquare className="w-4 h-4 text-indigo-600" />
    }
  }

  return (
    <div className="space-y-5 font-sans">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 bg-white p-5 rounded-2xl border border-line shadow-xs">
        <div>
          <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2">
            <span>Messages</span>
            {unreadCount > 0 && (
              <span className="px-2.5 py-0.5 text-xs font-bold rounded-full bg-blue-100 text-blue-700">
                {unreadCount} new
              </span>
            )}
          </h2>
          <p className="text-xs text-gray-500 mt-1">
            Notes from your mentors and counsellors.
          </p>
        </div>

        {unreadCount > 0 && (
          <button
            type="button"
            onClick={() => markAllRead.mutate()}
            disabled={markAllRead.isPending}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-gray-50 hover:bg-gray-100 text-gray-700 text-xs font-semibold rounded-xl border border-line transition"
          >
            <CheckCheck className="w-4 h-4" />
            <span>Mark all as read</span>
          </button>
        )}
      </div>

      {/* Notifications List */}
      {isLoading ? (
        <div className="p-12 text-center text-sm text-gray-500 bg-white rounded-2xl border border-line">
          Loading…
        </div>
      ) : error ? (
        <div className="p-6 bg-red-50 text-red-700 rounded-2xl border border-red-200 text-xs">
          We could not load your messages. {friendlyError(error)}
        </div>
      ) : notifications.length === 0 ? (
        <div className="p-12 text-center bg-white rounded-2xl border border-line shadow-xs">
          <div className="w-12 h-12 rounded-full bg-blue-50 text-blue-600 flex items-center justify-center mx-auto mb-3">
            <Bell className="w-6 h-6" />
          </div>
          <h3 className="text-base font-semibold text-gray-800">No messages yet</h3>
          <p className="text-xs text-gray-500 mt-1 max-w-sm mx-auto">
            When a mentor or counsellor writes to you, you will see it here.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {notifications.map((n) => {
            const dateFormatted = friendlyDateTime(n.created_at)

            return (
              <div
                key={n.id}
                onClick={() => {
                  if (!n.is_read) {
                    markRead.mutate(n.id)
                  }
                }}
                className={`p-4 rounded-2xl border transition cursor-pointer flex items-start gap-3.5 ${
                  n.is_read
                    ? 'bg-white border-line text-gray-700 hover:bg-gray-50/50'
                    : 'bg-blue-50/30 border-blue-100 text-gray-900 shadow-xs hover:bg-blue-50/60'
                }`}
              >
                <div
                  className={`p-2 rounded-xl shrink-0 mt-0.5 ${
                    n.is_read ? 'bg-gray-100' : 'bg-blue-100 text-blue-700'
                  }`}
                >
                  {getIcon(n.notification_type)}
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-2">
                    <h4
                      className={`text-sm ${
                        n.is_read ? 'font-medium text-gray-800' : 'font-bold text-gray-900'
                      }`}
                    >
                      {n.title}
                    </h4>
                    <span className="text-xs text-muted shrink-0 flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {dateFormatted}
                    </span>
                  </div>

                  <p className="text-xs text-gray-600 mt-1 leading-relaxed">{n.body}</p>

                  {!n.is_read && (
                    <div className="mt-2.5 flex items-center gap-2">
                      <span className="inline-block w-2 h-2 rounded-full bg-blue-600" />
                      <span className="text-xs font-semibold text-blue-700">Unread</span>
                    </div>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

