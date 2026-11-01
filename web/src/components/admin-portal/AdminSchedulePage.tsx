import React from 'react'
import { ScheduleSessionsView } from '../common/ScheduleSessionsView'

export function AdminSchedulePage() {
  return (
    <div className="flex-1">
      <ScheduleSessionsView title="Sessions and calls with students" />
    </div>
  )
}
