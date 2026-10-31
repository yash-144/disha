import React from 'react'
import { Calendar, Play, Clock } from 'lucide-react'

export interface InterventionRow {
  id: string
  student: {
    name: string
    avatar: string
  }
  intervention: string
  nextAction: string
  status: 'Scheduled' | 'In Progress' | 'Pending'
}

const DEFAULT_INTERVENTIONS: InterventionRow[] = [
  {
    id: 'int-1',
    student: {
      name: 'Asha Verma',
      avatar: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=150&q=80',
    },
    intervention: 'Mentor Check-in',
    nextAction: '14 Oct, 17:30',
    status: 'Scheduled',
  },
  {
    id: 'int-2',
    student: {
      name: 'Rohan Mehta',
      avatar: 'https://images.unsplash.com/photo-1539571696357-5a69c17a67c6?auto=format&fit=crop&w=150&q=80',
    },
    intervention: 'CBT Session',
    nextAction: '15 Oct, 14:00',
    status: 'In Progress',
  },
  {
    id: 'int-3',
    student: {
      name: 'Neha Kapoor',
      avatar: 'https://images.unsplash.com/photo-1517841905240-472988babdf9?auto=format&fit=crop&w=150&q=80',
    },
    intervention: 'Stress Management',
    nextAction: '16 Oct, 11:00',
    status: 'Pending',
  },
]

interface ActiveInterventionsProps {
  interventions?: InterventionRow[]
  onViewAll?: () => void
}

export function ActiveInterventions({
  interventions = DEFAULT_INTERVENTIONS,
  onViewAll,
}: ActiveInterventionsProps) {
  const renderStatusPill = (status: InterventionRow['status']) => {
    switch (status) {
      case 'Scheduled':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] font-semibold bg-[#EAF7EE] text-[#16A34A]">
            <Calendar className="w-3 h-3" />
            <span>Scheduled</span>
          </span>
        )
      case 'In Progress':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] font-semibold bg-[#EBF3FC] text-[#2563EB]">
            <Play className="w-3 h-3 fill-current" />
            <span>In Progress</span>
          </span>
        )
      case 'Pending':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] font-semibold bg-[#FEF6E8] text-[#D97706]">
            <Clock className="w-3 h-3" />
            <span>Pending</span>
          </span>
        )
      default:
        return null
    }
  }

  return (
    <div className="bg-white rounded-2xl p-4 shadow-sm border border-gray-100/60 font-sans">
      <div className="flex items-center justify-between pb-3">
        <h2 className="text-sm font-bold text-[#1E2433]">Active Interventions</h2>
        <button
          onClick={onViewAll}
          className="text-xs font-medium text-[#717E95] hover:text-[#1E2433] transition"
        >
          View all
        </button>
      </div>

      <div className="w-full overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="border-b border-gray-100/80 text-[11px] font-semibold text-[#94A3B8]">
              <th className="pb-2.5 font-medium">Student</th>
              <th className="pb-2.5 font-medium">Intervention</th>
              <th className="pb-2.5 font-medium">Next Action</th>
              <th className="pb-2.5 font-medium">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50/80">
            {interventions.map((row) => (
              <tr key={row.id} className="hover:bg-gray-50/40 transition-colors">
                <td className="py-2.5 pr-3">
                  <div className="flex items-center gap-2">
                    <img
                      src={row.student.avatar}
                      alt={row.student.name}
                      className="w-6 h-6 rounded-full object-cover shrink-0"
                    />
                    <span className="text-xs font-semibold text-[#1E2433]">
                      {row.student.name}
                    </span>
                  </div>
                </td>
                <td className="py-2.5 pr-3 text-xs text-[#505D75] font-normal">
                  {row.intervention}
                </td>
                <td className="py-2.5 pr-3 text-xs text-[#505D75] font-normal">
                  {row.nextAction}
                </td>
                <td className="py-2.5">
                  {renderStatusPill(row.status)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

