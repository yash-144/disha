import React, { useState } from 'react'
import {
  Plus,
  KeyRound,
  Users,
  Copy,
  Calendar,
  X,
  BookOpen,
  CheckCircle,
  Radio,
} from 'lucide-react'
import { useApp } from '../../context/AppContext'

export function ClassesTab() {
  const { activeClasses, addNewClass, addToast } = useApp()
  const [showAddClassModal, setShowAddClassModal] = useState(false)
  const [name, setName] = useState('')
  const [code, setCode] = useState('')
  const [subject, setSubject] = useState('Computer Science')
  const [term, setTerm] = useState('Jul 1, 2025 - Aug 20, 2025')

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault()
    if (!name.trim()) return

    const newCode = code || `CS${Math.floor(100 + Math.random() * 900)}`
    addNewClass({
      name,
      code: newCode,
      subject,
      term,
    })

    setShowAddClassModal(false)
    setName('')
    setCode('')
    addToast('Cohort Initialized!', `Cohort class ${newCode} (${name}) created.`, 'success')
  }

  const copyCode = (c: string) => {
    navigator.clipboard?.writeText?.(c)
    addToast('Code Copied!', `Access code ${c} copied to clipboard.`, 'success')
  }

  return (
    <div className="space-y-6 font-mono">
      <div className="flex flex-wrap items-center justify-between gap-4 border-2 border-ink bg-white p-4 shadow-[4px_4px_0_#0d1b3e]">
        <div>
          <div className="flex items-center gap-2">
            <span className="rounded bg-accent px-2 py-0.5 text-xs font-bold text-white shadow-[1.5px_1.5px_0_#0d1b3e]">
              ACTIVE COHORTS
            </span>
            <span className="text-xs text-muted">({activeClasses.length} Scheduled)</span>
          </div>
          <h2 className="mt-1 text-lg font-bold text-ink sm:text-xl">Active Cohort Classes</h2>
        </div>

        <button
          onClick={() => setShowAddClassModal(true)}
          className="flex items-center gap-1.5 border-2 border-ink bg-accent px-4 py-2 text-xs font-bold text-white shadow-[2px_2px_0_#0d1b3e] transition hover:bg-accent-dark hover:-translate-x-0.5 hover:-translate-y-0.5"
        >
          <Plus className="h-4 w-4" /> Add New Class
        </button>
      </div>

      <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
        {activeClasses.map((cls) => (
          <div
            key={cls.id}
            className="flex flex-col justify-between border-2 border-ink bg-white p-5 shadow-[4px_4px_0_#0d1b3e] transition hover:-translate-y-1 hover:shadow-[6px_6px_0_#0d1b3e]"
          >
            <div>
              <div className="flex items-start justify-between">
                <span className="border border-ink bg-accent px-2 py-0.5 text-xs font-bold text-white shadow-[1.5px_1.5px_0_#0d1b3e]">
                  {cls.code}
                </span>
                <span className="flex items-center gap-1 text-xs font-bold text-emerald-700">
                  <Radio className="h-2.5 w-2.5 text-accent animate-pulse" /> Live Room
                </span>
              </div>

              <h3 className="mt-3 text-sm font-bold text-ink leading-snug">{cls.name}</h3>
              <p className="mt-1 text-xs text-muted">{cls.subject}</p>

              <div className="mt-4 flex items-center justify-between border-2 border-ink bg-paper p-2 text-xs">
                <span className="flex items-center gap-1.5 text-gray-700 text-xs">
                  <KeyRound className="h-3.5 w-3.5 text-amber-500" />
                  Code: <span className="font-mono font-bold text-brand">{cls.accessCode}</span>
                </span>
                <button
                  onClick={() => copyCode(cls.accessCode)}
                  className="border border-ink bg-white px-2 py-0.5 text-xs font-bold text-ink shadow-[1px_1px_0_#0d1b3e] hover:bg-gray-100"
                  title="Copy Access Code"
                >
                  Copy
                </button>
              </div>

              <div className="mt-4 space-y-1 text-xs text-gray-600 border-t border-ink/10 pt-3">
                <p className="flex items-center gap-1.5 text-xs">
                  <Calendar className="h-3.5 w-3.5 text-brand" />
                  <span>{cls.term}</span>
                </p>
                <p className="flex items-center gap-1.5 text-xs font-bold text-accent">
                  <Users className="h-3.5 w-3.5" />
                  <span>{cls.activeStudents} active students in cohort</span>
                </p>
              </div>
            </div>

            <div className="mt-5 border-t-2 border-ink/10 pt-3 flex items-center justify-between text-xs">
              <span className="text-xs text-gray-400 font-mono">Created: {cls.createdAt}</span>
              <button
                onClick={() => addToast('Class Settings', `Managing cohort session for ${cls.code}.`, 'info')}
                className="border-2 border-ink bg-paper px-2.5 py-1 text-xs font-bold text-brand shadow-[1.5px_1.5px_0_#0d1b3e] hover:bg-white"
              >
                Manage Room →
              </button>
            </div>
          </div>
        ))}
      </div>

      {showAddClassModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-xs animate-in fade-in">
          <div className="w-full max-w-md border-4 border-ink bg-white p-6 shadow-[8px_8px_0_#0d1b3e]">
            <div className="flex items-center justify-between border-b-2 border-ink/20 pb-3">
              <h3 className="text-base font-bold text-ink">Create New Class Cohort</h3>
              <button
                onClick={() => setShowAddClassModal(false)}
                className="border border-ink p-1 text-gray-600 hover:bg-gray-100"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <form onSubmit={handleCreate} className="mt-4 space-y-3.5">
              <div>
                <label className="text-xs font-bold text-ink">Class Name *</label>
                <input
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. CS501: Distributed Cloud Architecture"
                  className="mt-1 w-full border-2 border-ink p-2 text-xs outline-none focus:bg-paper"
                />
              </div>

              <div>
                <label className="text-xs font-bold text-ink">Course Code (e.g. CS501)</label>
                <input
                  value={code}
                  onChange={(e) => setCode(e.target.value)}
                  placeholder="CS501"
                  className="mt-1 w-full border-2 border-ink p-2 text-xs outline-none focus:bg-paper"
                />
              </div>

              <div>
                <label className="text-xs font-bold text-ink">Subject Track</label>
                <select
                  value={subject}
                  onChange={(e) => setSubject(e.target.value)}
                  className="mt-1 w-full border-2 border-ink p-2 text-xs font-bold outline-none"
                >
                  <option>Computer Science</option>
                  <option>Data Systems</option>
                  <option>Design</option>
                  <option>Business Management</option>
                </select>
              </div>

              <div>
                <label className="text-xs font-bold text-ink">Term Schedule</label>
                <input
                  value={term}
                  onChange={(e) => setTerm(e.target.value)}
                  placeholder="Jul 1, 2025 - Aug 20, 2025"
                  className="mt-1 w-full border-2 border-ink p-2 text-xs outline-none focus:bg-paper"
                />
              </div>

              <div className="mt-5 flex justify-end gap-2 border-t-2 border-ink/20 pt-4">
                <button
                  type="button"
                  onClick={() => setShowAddClassModal(false)}
                  className="border-2 border-ink bg-gray-100 px-4 py-2 text-xs font-bold text-gray-700 hover:bg-gray-200"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="border-2 border-ink bg-accent px-5 py-2 text-xs font-bold text-white shadow-[2px_2px_0_#0d1b3e] hover:bg-accent-dark"
                >
                  Launch Cohort
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
