import React from 'react'
import { AppSidebar } from '../common/AppSidebar'

export interface TeacherSidebarProps {
  activeTab?: string
  onTabChange?: (tab: string) => void
}

export function TeacherSidebar({
  activeTab = 'cases',
  onTabChange,
}: TeacherSidebarProps) {
  return (
    <AppSidebar
      role="faculty"
      activeTab={activeTab}
      onSelectTab={(tab) => onTabChange?.(tab)}
    />
  )
}
