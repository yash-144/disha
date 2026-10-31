import React from 'react'
import { AppSidebar } from '../common/AppSidebar'

export type StudentNavId =
  | 'overview'
  | 'cases'
  | 'request-support'
  | 'assessment'
  | 'messages'
  | 'leaderboard'

export interface StudentSidebarProps {
  activeTab: StudentNavId
  onSelectTab: (tab: StudentNavId) => void
}

export function StudentSidebar({ activeTab, onSelectTab }: StudentSidebarProps) {
  return (
    <AppSidebar
      role="student"
      activeTab={activeTab}
      onSelectTab={(tab) => onSelectTab(tab as StudentNavId)}
    />
  )
}
