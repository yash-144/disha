import React, { useState, useEffect } from 'react'
import { Target, CheckCircle2, Circle } from 'lucide-react'
import { ChecklistItem } from './counsellorDemoData'

interface WeeklyFocusChecklistProps {
  initialItems: ChecklistItem[]
}

export function WeeklyFocusChecklist({ initialItems }: WeeklyFocusChecklistProps) {
  const [items, setItems] = useState<ChecklistItem[]>(initialItems)

  // Sync if demo mode switches
  useEffect(() => {
    setItems(initialItems)
  }, [initialItems])

  const toggleItem = (id: string) => {
    setItems((prev) =>
      prev.map((item) => (item.id === id ? { ...item, completed: !item.completed } : item))
    )
  }

  const completedCount = items.filter((i) => i.completed).length

  return (
    <div className="bg-white rounded-3xl p-5 border border-gray-100 shadow-2xs flex flex-col font-sans select-none">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-lg bg-purple-50 text-[#7C3AED] flex items-center justify-center">
            <Target className="w-3.5 h-3.5" />
          </div>
          <h3 className="text-sm font-bold text-[#1E2433]">My Focus This Week</h3>
        </div>

        <span className="text-[11px] font-bold text-gray-400">
          {completedCount} of {items.length} done
        </span>
      </div>

      {/* Checklist items */}
      <div className="flex flex-col gap-2">
        {items.map((item) => (
          <button
            key={item.id}
            type="button"
            onClick={() => toggleItem(item.id)}
            className="flex items-center gap-2.5 p-2 rounded-xl hover:bg-gray-50/80 transition text-left group cursor-pointer"
          >
            {item.completed ? (
              <CheckCircle2 className="w-4 h-4 text-[#16A34A] fill-[#DCFCE7] shrink-0" />
            ) : (
              <Circle className="w-4 h-4 text-gray-300 group-hover:text-gray-400 shrink-0" />
            )}

            <span
              className={`text-xs transition-colors ${
                item.completed
                  ? 'text-gray-400 line-through font-normal'
                  : 'text-[#1E2433] font-medium group-hover:text-[#7C3AED]'
              }`}
            >
              {item.text}
            </span>
          </button>
        ))}
      </div>
    </div>
  )
}

