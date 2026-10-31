import React from 'react'

export interface MessageItem {
  id: string
  name: string
  avatar: string
  message: string
  time: string
}

const DEFAULT_MESSAGES: MessageItem[] = [
  {
    id: 'msg-1',
    name: 'Asha Verma',
    avatar: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=150&q=80',
    message: 'Can we schedule a check-in...',
    time: '11:01',
  },
  {
    id: 'msg-2',
    name: 'Rohan Mehta',
    avatar: 'https://images.unsplash.com/photo-1539571696357-5a69c17a67c6?auto=format&fit=crop&w=150&q=80',
    message: "I've completed the intervent...",
    time: '09:38',
  },
  {
    id: 'msg-3',
    name: 'Neha Kapoor',
    avatar: 'https://images.unsplash.com/photo-1517841905240-472988babdf9?auto=format&fit=crop&w=150&q=80',
    message: 'Thank you for the guidance!',
    time: '09:18',
  },
]

interface RecentMessagesProps {
  messages?: MessageItem[]
  onViewAll?: () => void
}

export function RecentMessages({
  messages = DEFAULT_MESSAGES,
  onViewAll,
}: RecentMessagesProps) {
  return (
    <div className="bg-white rounded-2xl p-4 shadow-sm border border-gray-100/60 font-sans flex flex-col justify-between">
      <div className="flex items-center justify-between pb-3">
        <h2 className="text-sm font-bold text-[#1E2433]">Recent Messages</h2>
        <button
          onClick={onViewAll}
          className="text-xs font-medium text-[#717E95] hover:text-[#1E2433] transition"
        >
          View all
        </button>
      </div>

      <div className="space-y-3">
        {messages.map((item) => (
          <div key={item.id} className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-2.5 min-w-0">
              <img
                src={item.avatar}
                alt={item.name}
                className="w-8 h-8 rounded-full object-cover shrink-0"
              />
              <div className="min-w-0">
                <p className="text-xs font-bold text-[#1E2433] truncate leading-tight">
                  {item.name}
                </p>
                <p className="text-[11px] text-[#717E95] truncate mt-0.5">
                  {item.message}
                </p>
              </div>
            </div>
            <span className="text-[10px] text-[#94A3B8] font-medium shrink-0">
              {item.time}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}

