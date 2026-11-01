import React from 'react'
import { useSession } from '../../lib/auth/SessionProvider'
import { roleLabel } from '../../lib/auth/portals'
import { UserAvatar } from '../common/UserAvatar'
import { NotAvailable } from '../common/NotAvailable'

export function TeacherProfilePanel() {
  const { user, role } = useSession()
  return (
    <aside className="w-72 shrink-0 bg-[#F1F3FA] rounded-3xl p-5 flex flex-col gap-5 font-sans border border-gray-100/40">
      <div className="flex flex-col items-center">
        <UserAvatar name={user?.full_name} />
        <h2 className="text-base font-bold text-[#1E2433] mt-2.5">{user?.full_name}</h2>
        <p className="text-xs text-[#717E95] font-medium mt-0.5">{role ? roleLabel(role) : ''}</p>
      </div>
      <NotAvailable title="Agenda" />
    </aside>
  )
}
