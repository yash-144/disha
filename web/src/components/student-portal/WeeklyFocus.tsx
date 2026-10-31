import React, { useState, useEffect } from 'react'
import { Target, CheckCircle2, Circle } from 'lucide-react'

export interface FocusItem {
  id: string
  label: string
  done: boolean
}

interface WeeklyFocusProps {
  initialItems: FocusItem[]
}

export function WeeklyFocus({ initialItems }: WeeklyFocusProps) {
  const [items, setItems] = useState<FocusItem[]>(initialItems)

  // Sync when initialItems changes (e.g. switching demo modes)
  useEffect(() => {
    setItems(initialItems)
  }, [initialItems])

  const toggleItem = (id: string) => {
    setItems((prev) =>
      prev.map((item) => (item.id === id ? { ...item, done: !item.done } : item))
    )
  }

  return (
    <div className="bg-white rounded-2xl p-4.5 border border-gray-100/90 shadow-2xs flex flex-col justify-between select-none">
      {/* Header */}
      <div className="flex items-center gap-2 mb-3.5">
        <div className="w-5 h-5 flex items-center justify-center text-[#7C3AED]">
          <Target className="w-4 h-4" />
        </div>
        <h3 className="text-sm font-bold text-[#1E2433]">This Week's Focus</h3>
      </div>

      {/* Checklist */}
      <div className="flex flex-col gap-2.5">
        {items.map((item) => (
          <button
            key={item.id}
            type="button"
            onClick={() => toggleItem(item.id)}
            className="flex items-center gap-2.5 text-left group transition py-0.5"
          >
            {item.done ? (
              <CheckCircle2 className="w-4 h-4 text-[#22C55E] fill-[#DCFCE7] shrink-0" />
            ) : (
              <Circle className="w-4 h-4 text-[#CBD5E1] group-hover:text-[#94A3B8] transition-colors shrink-0" />
            )}
            <span
              className={`text-xs transition-colors ${
                item.done
                  ? 'text-[#64748B] line-through font-normal'
                  : 'text-[#1E2433] font-medium group-hover:text-[#4338CA]'
              }`}
            >
              {item.label}
            </span>
          </button>
        ))}
      </div>

      {/* Subtle completion footer */}
      <div className="pt-2 text-[10px] text-[#94A3B8] font-medium">
        {items.filter((i) => i.done).length} of {items.length} completed
      </div>
    </div>
  )
}

