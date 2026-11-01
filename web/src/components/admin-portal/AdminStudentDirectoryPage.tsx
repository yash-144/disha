import React, { useState } from 'react'
import { QueryState, EmptyState } from '../common/QueryState'
import { errorMessage } from '../../lib/api/errors'
import { useInvitations, useInvite, useMemberships } from '../../lib/api/endpoints/admin.hooks'

export function AdminStudentDirectoryPage() {
  const members = useMemberships()
  const invites = useInvitations()
  const invite = useInvite()
  const [email, setEmail] = useState('')
  const [role, setRole] = useState('student')
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null)
  const send = () => {
    setMsg(null)
    invite.mutate({ email, role, expires_in_days: 14 }, {
      onSuccess: () => { setMsg({ ok: true, text: `Invitation created for ${email}.` }); setEmail('') },
      onError: (e) => setMsg({ ok: false, text: errorMessage(e) }),
    })
  }
  return (
    <div className="flex flex-col gap-4 font-sans text-xs">
      <section className="flex flex-wrap items-end gap-3 rounded-2xl border border-gray-100 bg-white p-4">
        <label className="flex flex-col gap-1">Email
          <input value={email} onChange={(e) => setEmail(e.target.value)} type="email" className="rounded-lg border border-gray-200 px-2 py-1" />
        </label>
        <label className="flex flex-col gap-1">Role
          <select value={role} onChange={(e) => setRole(e.target.value)} className="rounded-lg border border-gray-200 px-2 py-1">
            {['student', 'faculty', 'mentor', 'counsellor', 'hod', 'institution_admin'].map((r) => <option key={r}>{r}</option>)}
          </select>
        </label>
        <button type="button" disabled={!email || invite.isPending} onClick={send} className="rounded-full bg-purple-700 px-4 py-2 font-bold text-white disabled:opacity-50">Invite</button>
        {msg && <p role={msg.ok ? 'status' : 'alert'} className={msg.ok ? 'text-emerald-700' : 'text-red-600'}>{msg.text}</p>}
      </section>
      <QueryState query={members} empty={<EmptyState title="No members" />}>
        {(rows) => (
          <table className="w-full rounded-2xl bg-white text-left">
            <thead><tr className="text-[#717E95]"><th className="p-2">Name</th><th>Email</th><th>Role</th><th>Department</th><th>Active</th></tr></thead>
            <tbody>
              {rows.map((m) => (
                <tr key={m.membership_id} className="border-t border-gray-100"><td className="p-2">{m.full_name}</td><td>{m.email}</td><td>{m.role}</td><td>{m.department ?? ''}</td><td>{m.is_active ? 'yes' : 'no'}</td></tr>
              ))}
            </tbody>
          </table>
        )}
      </QueryState>
      <h3 className="font-bold">Invitations</h3>
      <QueryState query={invites} empty={<EmptyState title="No invitations" />}>
        {(rows) => (
          <ul className="rounded-2xl border border-gray-100 bg-white">
            {rows.map((i) => <li key={i.id} className="flex justify-between p-3"><span>{i.email} ({i.role})</span><span>{i.status}</span></li>)}
          </ul>
        )}
      </QueryState>
    </div>
  )
}
