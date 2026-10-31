import React from 'react'
import { Calendar, FileText, Check, ChevronRight } from 'lucide-react'

export interface UpdateItem {
  id: string
  title: string
  subtitle: string
  iconType: 'calendar' | 'document' | 'check'
  color: string
}

interface RecentUpdatesProps {
  updates: UpdateItem[]
}

export function RecentUpdates({ updates }: RecentUpdatesProps) {
  const getIcon = (type: UpdateItem['iconType'], color: string) => {
    switch (type) {
      case 'calendar':
        return (
          <div className="w-8 h-8 rounded-full bg-[#ECE8FB] text-[#7C3AED] flex items-center justify-center shrink-0">
            <Calendar className="w-4 h-4" />
          </div>
        )
      case 'document':
        return (
          <div className="w-8 h-8 rounded-full bg-[#EDE8FB] text-[#6366F1] flex items-center justify-center shrink-0">
            <FileText className="w-4 h-4" />
          </div>
        )
      case 'check':
        return (
          <div className="w-8 h-8 rounded-full bg-[#DCFCE7] text-[#16A34A] flex items-center justify-center shrink-0">
            <Check className="w-4 h-4 stroke-[2.5]" />
          </div>
        )
      default:
        return (
          <div className="w-8 h-8 rounded-full bg-gray-100 text-gray-600 flex items-center justify-center shrink-0">
            <FileText className="w-4 h-4" />
          </div>
        )
    }
  }

  return (
    <div className="bg-white rounded-2xl p-4.5 border border-gray-100/90 shadow-2xs select-none">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-bold text-[#1E2433]">Recent Updates</h3>
        <button
          type="button"
          className="text-xs font-semibold text-[#717E95] hover:text-[#1E2433] transition"
        >
          View all
        </button>
      </div>

      {/* List */}
      <div className="flex flex-col gap-2.5">
        {updates.map((item) => (
          <div
            key={item.id}
            className="flex items-center justify-between p-2.5 rounded-xl border border-gray-100 hover:border-gray-200 hover:bg-gray-50/50 transition cursor-pointer group"
          >
            <div className="flex items-center gap-3">
              {getIcon(item.iconType, item.color)}
              <div>
                <p className="text-xs font-bold text-[#1E2433] group-hover:text-[#4338CA] transition-colors">
                  {item.title}
                </p>
                <p className="text-[11px] text-[#717E95] mt-0.5">
                  {item.subtitle}
                </p>
              </div>
            </div>

            <ChevronRight className="w-4 h-4 text-[#94A3B8] group-hover:text-[#1E2433] group-hover:translate-x-0.5 transition-all" />
          </div>
        ))}
      </div>
    </div>
  )
}

