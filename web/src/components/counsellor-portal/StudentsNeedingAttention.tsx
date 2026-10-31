import React from 'react'
import { ArrowRight } from 'lucide-react'
import { CounsellorStudentItem } from './counsellorDemoData'

interface StudentsNeedingAttentionProps {
  students: CounsellorStudentItem[]
  onViewAll?: () => void
  onSelectStudent?: (student: CounsellorStudentItem) => void
}

export function StudentsNeedingAttention({
  students,
  onViewAll,
  onSelectStudent,
}: StudentsNeedingAttentionProps) {
  const getPriorityBadgeClass = (priority: CounsellorStudentItem['priority']) => {
    switch (priority) {
      case 'High Priority':
        return 'bg-[#FEE2E2] text-[#DC2626] border border-[#FECACA]'
      case 'Medium':
        return 'bg-[#FEF3C7] text-[#D97706] border border-[#FDE68A]'
      case 'Low':
      default:
        return 'bg-[#DCFCE7] text-[#16A34A] border border-[#BBF7D0]'
    }
  }

  return (
    <div className="bg-white rounded-3xl p-5 border border-gray-100 shadow-2xs flex flex-col justify-between font-sans select-none">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-bold text-[#1E2433]">Students Needing Attention</h3>

        {onViewAll && (
          <button
            type="button"
            onClick={onViewAll}
            className="inline-flex items-center gap-1 text-xs font-semibold text-purple-700 hover:text-purple-900 transition cursor-pointer"
          >
            <span>View All</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        )}
      </div>

      {/* Students List */}
      <div className="flex flex-col gap-2.5">
        {students.map((student) => (
          <div
            key={student.id}
            onClick={() => onSelectStudent?.(student)}
            className="flex items-center justify-between p-2.5 rounded-2xl border border-gray-100 hover:border-purple-200 hover:bg-purple-50/20 transition cursor-pointer group"
          >
            {/* Left: Initials Avatar + Info */}
            <div className="flex items-center gap-3 min-w-0">
              <div
                className={`w-9 h-9 rounded-full flex items-center justify-center font-bold text-xs shrink-0 ${student.avatarBg} ${student.avatarText}`}
              >
                {student.initials}
              </div>

              <div className="min-w-0">
                <h4 className="text-xs font-bold text-[#1E2433] group-hover:text-purple-900 transition truncate">
                  {student.name}
                </h4>
                <p className="text-[11px] text-[#717E95] truncate font-medium mt-0.5">
                  {student.subtitle}
                </p>
              </div>
            </div>

            {/* Right: Priority Badge */}
            <div className="shrink-0 ml-3">
              <span
                className={`text-[10px] font-bold px-2.5 py-0.5 rounded-full ${getPriorityBadgeClass(
                  student.priority
                )}`}
              >
                {student.priority}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

