import React, { useState } from 'react'
import { ArrowRight, ArrowLeft } from 'lucide-react'
import { useApp } from '../../context/AppContext'
import { UserRole } from '../../types'

export function OnboardingView() {
  const { currentUser, setCurrentUser, switchRole, navigateTo } = useApp()

  const [step, setStep] = useState<1 | 2 | 3>(1)
  const [selectedRole, setSelectedRole] = useState<UserRole>(currentUser.role || 'student')
  const [fullName, setFullName] = useState(currentUser.name || 'Aarav Sharma')
  const [email, setEmail] = useState(currentUser.email || 'aarav.sharma@iitb.ac.in')
  const [campus, setCampus] = useState('IIT Bombay')
  const [idNumber, setIdNumber] = useState('2024CS-0842')

  // Step 2 State
  const [academicTrack, setAcademicTrack] = useState('Computer Science & Engineering')
  const [semester, setSemester] = useState('Semester 4 (Year 2)')
  const [targetCgpa, setTargetCgpa] = useState('8.50')
  const [facultyDept, setFacultyDept] = useState('Computer Science & Engineering')

  // Step 3 State
  const [attendanceAlertThreshold, setAttendanceAlertThreshold] = useState(75)
  const [enableMekoMemory, setEnableMekoMemory] = useState(true)
  const [alertChannels, setAlertChannels] = useState<{ email: boolean; sms: boolean; dashboard: boolean }>({
    email: true,
    sms: false,
    dashboard: true,
  })

  const handleFinishOnboarding = () => {
    switchRole(selectedRole)
    setCurrentUser((prev) => ({
      ...prev,
      name: fullName,
      email: email,
      role: selectedRole,
      title:
        selectedRole === 'student'
          ? `${academicTrack} Scholar`
          : selectedRole === 'instructor'
          ? `Faculty — ${facultyDept}`
          : selectedRole === 'counsellor'
          ? 'Academic Counsellor'
          : 'Campus Administrator',
    }))

    try {
      localStorage.setItem('disha_onboarding_completed', 'true')
    } catch {
      // ignore
    }

    navigateTo('dashboard', 'overview')
  }

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 font-sans antialiased selection:bg-slate-900 selection:text-white">
      {/* Top Header */}
      <header className="border-b border-slate-200/80 bg-white">
        <div className="mx-auto flex max-w-2xl items-center justify-between px-6 py-4">
          <button
            onClick={() => navigateTo('landing')}
            className="text-lg font-black tracking-widest text-slate-950 uppercase outline-none"
          >
            DISHA
          </button>

          <div className="flex items-center gap-6">
            <button
              onClick={handleFinishOnboarding}
              className="text-xs text-slate-500 hover:text-slate-900 transition font-medium"
            >
              Skip setup →
            </button>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="mx-auto max-w-2xl px-4 sm:px-6 py-10 sm:py-14">
        
        {/* Step Indicator Header */}
        <div className="mb-4 flex items-center justify-between text-xs font-medium text-slate-400 px-1">
          <div className="flex items-center gap-2">
            <span className={step === 1 ? 'text-slate-950 font-semibold' : ''}>1. Identity</span>
            <span className="text-slate-300">/</span>
            <span className={step === 2 ? 'text-slate-950 font-semibold' : ''}>2. Context</span>
            <span className="text-slate-300">/</span>
            <span className={step === 3 ? 'text-slate-950 font-semibold' : ''}>3. Risk Settings</span>
          </div>
          <span className="text-slate-500 font-medium">Step {step} of 3</span>
        </div>

        {/* Defined Border Box Container */}
        <div className="rounded-2xl border border-slate-200 bg-white p-6 sm:p-10 shadow-sm">
          
          {/* STEP 1: IDENTITY & ROLE */}
          {step === 1 && (
            <div className="space-y-7 animate-in fade-in duration-200">
              <div>
                <h1 className="text-2xl font-semibold tracking-tight text-slate-950">
                  Profile &amp; Role Setup
                </h1>
                <p className="mt-1 text-sm text-slate-500">
                  Select your campus persona and confirm institutional credentials.
                </p>
              </div>

              {/* Clean Role Selector */}
              <div className="space-y-2">
                <label className="text-xs font-semibold text-slate-700">Select Role</label>
                <div className="grid grid-cols-2 gap-2.5">
                  {[
                    { role: 'student', label: 'Student', desc: 'Attendance, risk radar & benchmarks' },
                    { role: 'instructor', label: 'Faculty', desc: 'Student signal reviews & course cases' },
                    { role: 'counsellor', label: 'Counsellor', desc: 'Confidential intervention workflows' },
                    { role: 'admin', label: 'Administrator', desc: 'Campus-wide retention analytics' },
                  ].map((item) => (
                    <button
                      key={item.role}
                      type="button"
                      onClick={() => {
                        setSelectedRole(item.role as any)
                        if (item.role === 'instructor') setIdNumber('FAC-7741')
                        else if (item.role === 'counsellor') setIdNumber('CNS-2098')
                        else if (item.role === 'admin') setIdNumber('ADM-1001')
                        else setIdNumber('2024CS-0842')
                      }}
                      className={`rounded-xl border p-4 text-left transition-all ${
                        selectedRole === item.role
                          ? 'border-slate-950 bg-slate-50 text-slate-950 shadow-2xs font-semibold'
                          : 'border-slate-200 bg-white text-slate-600 hover:border-slate-300'
                      }`}
                    >
                      <div className="text-sm font-semibold text-slate-950">{item.label}</div>
                      <div className="mt-1 text-xs text-slate-500 leading-relaxed font-normal">{item.desc}</div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Basic Info Inputs */}
              <div className="space-y-4 pt-1">
                <div>
                  <label className="text-xs font-semibold text-slate-700">Full Name</label>
                  <input
                    type="text"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    placeholder="e.g. Aarav Sharma"
                    className="mt-1.5 w-full rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 text-sm text-slate-900 outline-none transition focus:border-slate-950"
                  />
                </div>

                <div>
                  <label className="text-xs font-semibold text-slate-700">Institutional Email</label>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="name@institution.edu"
                    className="mt-1.5 w-full rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 text-sm text-slate-900 outline-none transition focus:border-slate-950"
                  />
                </div>

                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                  <div>
                    <label className="text-xs font-semibold text-slate-700">Campus / Institution</label>
                    <input
                      type="text"
                      value={campus}
                      onChange={(e) => setCampus(e.target.value)}
                      placeholder="e.g. IIT Bombay"
                      className="mt-1.5 w-full rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 text-sm text-slate-900 outline-none transition focus:border-slate-950"
                    />
                  </div>

                  <div>
                    <label className="text-xs font-semibold text-slate-700">
                      {selectedRole === 'student' ? 'Student Roll / Enrollment No.' : 'Institutional ID'}
                    </label>
                    <input
                      type="text"
                      value={idNumber}
                      onChange={(e) => setIdNumber(e.target.value)}
                      placeholder="e.g. 2024CS-0842"
                      className="mt-1.5 w-full rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 text-sm text-slate-900 outline-none transition focus:border-slate-950"
                    />
                  </div>
                </div>
              </div>

              {/* Action */}
              <div className="pt-4 flex justify-end border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setStep(2)}
                  className="flex items-center gap-2 rounded-xl bg-slate-950 px-6 py-3 text-xs font-semibold text-white transition hover:bg-slate-800"
                >
                  <span>Continue</span>
                  <ArrowRight className="h-4 w-4" />
                </button>
              </div>
            </div>
          )}

          {/* STEP 2: ACADEMIC CONTEXT */}
          {step === 2 && (
            <div className="space-y-7 animate-in fade-in duration-200">
              <div>
                <h1 className="text-2xl font-semibold tracking-tight text-slate-950">
                  Academic Context
                </h1>
                <p className="mt-1 text-sm text-slate-500">
                  Specify academic program and benchmark details for signal calibration.
                </p>
              </div>

              {selectedRole === 'student' ? (
                <div className="space-y-5">
                  <div>
                    <label className="text-xs font-semibold text-slate-700">Department / Academic Track</label>
                    <input
                      type="text"
                      value={academicTrack}
                      onChange={(e) => setAcademicTrack(e.target.value)}
                      placeholder="e.g. Computer Science & Engineering"
                      className="mt-1.5 w-full rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 text-sm text-slate-900 outline-none transition focus:border-slate-950"
                    />
                  </div>

                  <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                    <div>
                      <label className="text-xs font-semibold text-slate-700">Current Standing</label>
                      <select
                        value={semester}
                        onChange={(e) => setSemester(e.target.value)}
                        className="mt-1.5 w-full rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 text-sm text-slate-900 outline-none transition focus:border-slate-950"
                      >
                        <option>Semester 1 (Year 1)</option>
                        <option>Semester 2 (Year 1)</option>
                        <option>Semester 3 (Year 2)</option>
                        <option>Semester 4 (Year 2)</option>
                        <option>Semester 5 (Year 3)</option>
                        <option>Semester 6 (Year 3)</option>
                        <option>Semester 7 (Year 4)</option>
                        <option>Semester 8 (Year 4)</option>
                      </select>
                    </div>

                    <div>
                      <label className="text-xs font-semibold text-slate-700">Target SGPA Benchmark</label>
                      <input
                        type="number"
                        step="0.01"
                        min="4.0"
                        max="10.0"
                        value={targetCgpa}
                        onChange={(e) => setTargetCgpa(e.target.value)}
                        className="mt-1.5 w-full rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 text-sm text-slate-900 outline-none transition focus:border-slate-950"
                      />
                    </div>
                  </div>
                </div>
              ) : (
                <div className="space-y-5">
                  <div>
                    <label className="text-xs font-semibold text-slate-700">Faculty Department / Academic Unit</label>
                    <input
                      type="text"
                      value={facultyDept}
                      onChange={(e) => setFacultyDept(e.target.value)}
                      placeholder="e.g. Computer Science & Engineering"
                      className="mt-1.5 w-full rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 text-sm text-slate-900 outline-none transition focus:border-slate-950"
                    />
                  </div>

                  <div>
                    <label className="text-xs font-semibold text-slate-700">Intervention SLA Window</label>
                    <select
                      className="mt-1.5 w-full rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 text-sm text-slate-900 outline-none transition focus:border-slate-950"
                    >
                      <option>24 Hours (Urgent Early Warning)</option>
                      <option>48 Hours (Standard SLA)</option>
                      <option>72 Hours (Extended Review)</option>
                    </select>
                  </div>
                </div>
              )}

              {/* Navigation Controls */}
              <div className="pt-4 flex items-center justify-between border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setStep(1)}
                  className="flex items-center gap-1.5 text-xs font-medium text-slate-500 hover:text-slate-900 transition"
                >
                  <ArrowLeft className="h-4 w-4" /> Back
                </button>

                <button
                  type="button"
                  onClick={() => setStep(3)}
                  className="flex items-center gap-2 rounded-xl bg-slate-950 px-6 py-3 text-xs font-semibold text-white transition hover:bg-slate-800"
                >
                  <span>Continue</span>
                  <ArrowRight className="h-4 w-4" />
                </button>
              </div>
            </div>
          )}

          {/* STEP 3: PREFERENCES & COMPLETION */}
          {step === 3 && (
            <div className="space-y-7 animate-in fade-in duration-200">
              <div>
                <h1 className="text-2xl font-semibold tracking-tight text-slate-950">
                  Risk Benchmark &amp; Notifications
                </h1>
                <p className="mt-1 text-sm text-slate-500">
                  Configure early-warning attendance floor and dispatch alerts.
                </p>
              </div>

              {/* Attendance Threshold Slider */}
              <div className="rounded-xl border border-slate-200 p-5 space-y-3">
                <div className="flex items-center justify-between">
                  <div>
                    <span className="text-xs font-semibold text-slate-900">Attendance Alert Threshold</span>
                    <p className="text-xs text-slate-500">Flags risk when attendance falls below this benchmark.</p>
                  </div>
                  <span className="text-xs font-bold text-slate-950">
                    {attendanceAlertThreshold}%
                  </span>
                </div>
                <input
                  type="range"
                  min="60"
                  max="90"
                  step="5"
                  value={attendanceAlertThreshold}
                  onChange={(e) => setAttendanceAlertThreshold(Number(e.target.value))}
                  className="w-full accent-slate-950"
                />
                <div className="flex justify-between text-[11px] text-slate-400">
                  <span>60%</span>
                  <span className="font-medium text-slate-600">75% (UGC Standard)</span>
                  <span>90%</span>
                </div>
              </div>

              {/* Notification Channels */}
              <div className="space-y-3">
                <label className="text-xs font-semibold text-slate-700">Notification Channels</label>
                <div className="grid grid-cols-1 gap-2.5 sm:grid-cols-3">
                  {[
                    { key: 'dashboard', label: 'Cockpit Banner', desc: 'In-app alert triage' },
                    { key: 'email', label: 'Campus Email', desc: 'Critical case notices' },
                    { key: 'sms', label: 'SMS Alerts', desc: 'Urgent escalations' },
                  ].map((item) => (
                    <label
                      key={item.key}
                      className="flex cursor-pointer items-start gap-2.5 rounded-xl border border-slate-200 p-3 hover:border-slate-300 transition"
                    >
                      <input
                        type="checkbox"
                        checked={(alertChannels as any)[item.key]}
                        onChange={(e) =>
                          setAlertChannels((prev) => ({ ...prev, [item.key]: e.target.checked }))
                        }
                        className="mt-0.5 accent-slate-950"
                      />
                      <div>
                        <div className="text-xs font-medium text-slate-950">{item.label}</div>
                        <div className="text-[11px] text-slate-500">{item.desc}</div>
                      </div>
                    </label>
                  ))}
                </div>
              </div>

              {/* Universal Context Memory Toggle */}
              <div className="flex items-center justify-between rounded-xl border border-slate-200 p-4">
                <div>
                  <span className="text-xs font-semibold text-slate-900">Meko Universal Context Memory</span>
                  <p className="text-xs text-slate-500">Synchronizes case notes and longitudinal student histories.</p>
                </div>
                <button
                  type="button"
                  onClick={() => setEnableMekoMemory(!enableMekoMemory)}
                  className={`rounded-full px-3 py-1 text-xs font-medium transition ${
                    enableMekoMemory ? 'bg-slate-950 text-white' : 'bg-slate-100 text-slate-500'
                  }`}
                >
                  {enableMekoMemory ? 'Enabled' : 'Disabled'}
                </button>
              </div>

              {/* Summary Review Strip */}
              <div className="rounded-xl border border-slate-100 bg-slate-50 p-4 text-xs text-slate-600 flex flex-wrap items-center justify-between gap-2">
                <div>
                  <span className="text-slate-400">Account: </span>
                  <span className="font-semibold text-slate-900">{fullName}</span> ({selectedRole})
                </div>
                <div>
                  <span className="text-slate-400">Campus: </span>
                  <span className="font-semibold text-slate-900">{campus}</span>
                </div>
              </div>

              {/* Navigation Controls */}
              <div className="pt-4 flex items-center justify-between border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setStep(2)}
                  className="flex items-center gap-1.5 text-xs font-medium text-slate-500 hover:text-slate-900 transition"
                >
                  <ArrowLeft className="h-4 w-4" /> Back
                </button>

                <button
                  type="button"
                  onClick={handleFinishOnboarding}
                  className="flex items-center gap-2 rounded-xl bg-slate-950 px-7 py-3 text-xs font-semibold text-white transition hover:bg-slate-800"
                >
                  <span>Complete Setup &amp; Enter Cockpit</span>
                  <ArrowRight className="h-4 w-4" />
                </button>
              </div>
            </div>
          )}

        </div>

      </main>
    </div>
  )
}
