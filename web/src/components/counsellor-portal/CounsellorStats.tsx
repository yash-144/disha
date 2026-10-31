import React from 'react'
import { Users, Folder, Calendar, CheckCircle2 } from 'lucide-react'
import { CounsellorScenarioData } from './counsellorDemoData'

interface CounsellorStatsProps {
  stats: CounsellorScenarioData['stats']
}

export function CounsellorStats({ stats }: CounsellorStatsProps) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5 select-none font-sans">
      {/* 1. Assigned Students Card (Pastel Purple) */}
      <div className="rounded-2xl bg-[#F4F0FD] p-4.5 border border-[#E9D5FF]/60 shadow-2xs flex flex-col justify-between transition hover:shadow-xs">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-full bg-white text-[#7C3AED] shadow-2xs flex items-center justify-center shrink-0">
            <Users className="w-4 h-4" />
          </div>
          <span className="text-xs font-bold text-[#1E2433]">Assigned Students</span>
        </div>

        <div className="mt-3">
          <div className="text-3xl font-extrabold tracking-tight text-[#1E2433]">
            {stats.assignedStudents.value}
          </div>
          <div className="text-[11px] font-semibold text-[#16A34A] mt-1 flex items-center gap-0.5">
            <span>{stats.assignedStudents.change}</span>
          </div>
        </div>
      </div>

      {/* 2. Active Cases Card (Pastel Blue) */}
      <div className="rounded-2xl bg-[#EAF3FD] p-4.5 border border-[#BAE6FD]/60 shadow-2xs flex flex-col justify-between transition hover:shadow-xs">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-full bg-white text-[#0284C7] shadow-2xs flex items-center justify-center shrink-0">
            <Folder className="w-4 h-4" />
          </div>
          <span className="text-xs font-bold text-[#1E2433]">Active Cases</span>
        </div>

        <div className="mt-3">
          <div className="text-3xl font-extrabold tracking-tight text-[#1E2433]">
            {stats.activeCases.value}
          </div>
          <div className="text-[11px] font-semibold text-[#16A34A] mt-1 flex items-center gap-0.5">
            <span>{stats.activeCases.change}</span>
          </div>
        </div>
      </div>

      {/* 3. Upcoming Sessions Card (Pastel Yellow) */}
      <div className="rounded-2xl bg-[#FEF7E9] p-4.5 border border-[#FDE68A]/60 shadow-2xs flex flex-col justify-between transition hover:shadow-xs">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-full bg-white text-[#D97706] shadow-2xs flex items-center justify-center shrink-0">
            <Calendar className="w-4 h-4" />
          </div>
          <span className="text-xs font-bold text-[#1E2433]">Upcoming Sessions</span>
        </div>

        <div className="mt-3">
          <div className="text-3xl font-extrabold tracking-tight text-[#1E2433]">
            {stats.upcomingSessions.value}
          </div>
          <div className="text-[11px] font-medium text-[#717E95] mt-1">
            {stats.upcomingSessions.label}
          </div>
        </div>
      </div>

      {/* 4. Follow-Ups Due Card (Pastel Green) */}
      <div className="rounded-2xl bg-[#EAF8EE] p-4.5 border border-[#BBF7D0]/60 shadow-2xs flex flex-col justify-between transition hover:shadow-xs">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-full bg-white text-[#16A34A] shadow-2xs flex items-center justify-center shrink-0">
            <CheckCircle2 className="w-4 h-4" />
          </div>
          <span className="text-xs font-bold text-[#1E2433]">Follow-Ups Due</span>
        </div>

        <div className="mt-3">
          <div className="text-3xl font-extrabold tracking-tight text-[#1E2433]">
            {stats.followUpsDue.value}
          </div>
          <div className="text-[11px] font-semibold text-[#16A34A] mt-1 flex items-center gap-0.5">
            <span>{stats.followUpsDue.change}</span>
          </div>
        </div>
      </div>
    </div>
  )
}

