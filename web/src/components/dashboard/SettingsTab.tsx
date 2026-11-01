import React, { useState } from 'react'
import { User, Mail, Shield, Bell, Save, CheckCircle } from 'lucide-react'
import { useApp } from '../../context/AppContext'

export function SettingsTab() {
  const { currentUser, setCurrentUser, addToast, userRole, switchRole } = useApp()
  const [name, setName] = useState(currentUser.name)
  const [title, setTitle] = useState(currentUser.title)
  const [email, setEmail] = useState(currentUser.email)
  const [bio, setBio] = useState(currentUser.bio)
  const [notifyClass, setNotifyClass] = useState(true)
  const [notifyQuiz, setNotifyQuiz] = useState(true)
  const [notifyEmailDigest, setNotifyEmailDigest] = useState(false)

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault()
    setCurrentUser((prev) => ({
      ...prev,
      name,
      title,
      email,
      bio,
    }))
    addToast('Profile Updated', 'Your profile information has been saved successfully.', 'success')
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6 font-mono">
      <div className="border-2 border-ink bg-white p-4 shadow-[4px_4px_0_#0d1b3e]">
        <div className="flex items-center gap-2">
          <span className="rounded bg-brand px-2 py-0.5 text-[10px] font-bold text-white shadow-[1.5px_1.5px_0_#0d1b3e]">
            SYSTEM CONFIG
          </span>
          <span className="text-xs text-muted">Preferences &amp; Identity</span>
        </div>
        <h2 className="mt-1 text-lg font-bold text-ink sm:text-xl">Account &amp; Workstation Settings</h2>
      </div>

      <form onSubmit={handleSave} className="space-y-6">
        {/* Profile Card */}
        <div className="border-2 border-ink bg-white p-6 shadow-[4px_4px_0_#0d1b3e] space-y-4">
          <h3 className="text-sm font-bold text-ink border-b-2 border-ink/20 pb-2">
            Profile Information
          </h3>

          <div className="flex items-center gap-4">
            <img
              src={currentUser.avatar}
              alt={currentUser.name}
              className="h-16 w-16 border-2 border-ink object-cover shadow-[2px_2px_0_#0d1b3e]"
            />
            <div>
              <p className="text-sm font-bold text-ink">{currentUser.name}</p>
              <p className="text-xs text-accent font-bold capitalize">{userRole} Account Active</p>
              <button
                type="button"
                onClick={() => addToast('Avatar Update', 'Image upload dialog simulated.', 'info')}
                className="mt-1 text-xs font-bold text-brand hover:underline"
              >
                Change Avatar Photo →
              </button>
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label className="text-xs font-bold text-ink">Display Name</label>
              <input
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="mt-1 w-full border-2 border-ink p-2 text-xs outline-none focus:bg-paper"
              />
            </div>

            <div>
              <label className="text-xs font-bold text-ink">Email Address</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="mt-1 w-full border-2 border-ink p-2 text-xs outline-none focus:bg-paper"
              />
            </div>
          </div>

          <div>
            <label className="text-xs font-bold text-ink">Professional Title / Headline</label>
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="mt-1 w-full border-2 border-ink p-2 text-xs outline-none focus:bg-paper"
            />
          </div>

          <div>
            <label className="text-xs font-bold text-ink">Instructor Biography</label>
            <textarea
              rows={3}
              value={bio}
              onChange={(e) => setBio(e.target.value)}
              className="mt-1 w-full border-2 border-ink p-2 text-xs outline-none focus:bg-paper"
            />
          </div>
        </div>

        {/* Notification Settings */}
        <div className="border-2 border-ink bg-white p-6 shadow-[4px_4px_0_#0d1b3e] space-y-4">
          <h3 className="text-sm font-bold text-ink border-b-2 border-ink/20 pb-2">
            Notification Rules &amp; Alerts
          </h3>

          <div className="space-y-3">
            <label className="flex items-center justify-between cursor-pointer border border-ink/20 p-2.5 hover:bg-gray-50">
              <span className="text-xs font-bold text-ink">Live Cohort Room Alerts</span>
              <input
                type="checkbox"
                checked={notifyClass}
                onChange={(e) => setNotifyClass(e.target.checked)}
                className="h-4 w-4 accent-brand cursor-pointer"
              />
            </label>

            <label className="flex items-center justify-between cursor-pointer border border-ink/20 p-2.5 hover:bg-gray-50">
              <span className="text-xs font-bold text-ink">Assessment Submission Ping</span>
              <input
                type="checkbox"
                checked={notifyQuiz}
                onChange={(e) => setNotifyQuiz(e.target.checked)}
                className="h-4 w-4 accent-brand cursor-pointer"
              />
            </label>

            <label className="flex items-center justify-between cursor-pointer border border-ink/20 p-2.5 hover:bg-gray-50">
              <span className="text-xs font-bold text-ink">Weekly Performance Digest Email</span>
              <input
                type="checkbox"
                checked={notifyEmailDigest}
                onChange={(e) => setNotifyEmailDigest(e.target.checked)}
                className="h-4 w-4 accent-brand cursor-pointer"
              />
            </label>
          </div>
        </div>

        {/* Save CTA */}
        <div className="flex justify-end">
          <button
            type="submit"
            className="flex items-center gap-2 border-2 border-ink bg-accent px-6 py-2.5 text-xs font-bold text-white shadow-[2px_2px_0_#0d1b3e] transition hover:bg-accent-dark hover:-translate-x-0.5 hover:-translate-y-0.5"
          >
            <Save className="h-4 w-4" /> Save Profile Preferences
          </button>
        </div>
      </form>
    </div>
  )
}
