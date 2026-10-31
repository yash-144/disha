import React, { useState, useRef, useEffect } from 'react'
import {
  ChevronDown,
  Layers,
  UserCheck,
  HeartHandshake,
  ShieldCheck,
} from 'lucide-react'
import { useApp } from '../../context/AppContext'
import { UserRole } from '../../types'

interface RoleSwitcherProps {
  align?: 'left' | 'right'
  className?: string
}

interface RoleConfig {
  id: UserRole
  label: string
  portalName: string
  icon: React.ComponentType<{ className?: string }>
  badgeBg: string
  badgeText: string
  activeBg: string
  activeText: string
  iconColor: string
}

const ROLES: RoleConfig[] = [
  {
    id: 'instructor',
    label: 'Faculty Portal',
    portalName: 'Faculty & Mentors',
    icon: Layers,
    badgeBg: 'bg-blue-100',
    badgeText: 'text-blue-800',
    activeBg: 'bg-blue-50',
    activeText: 'text-blue-900',
    iconColor: 'text-blue-600',
  },
  {
    id: 'student',
    label: 'Student Portal',
    portalName: 'Students',
    icon: UserCheck,
    badgeBg: 'bg-purple-100',
    badgeText: 'text-purple-800',
    activeBg: 'bg-purple-50',
    activeText: 'text-purple-900',
    iconColor: 'text-purple-600',
  },
  {
    id: 'counsellor',
    label: 'Counsellor Portal',
    portalName: 'Student Counsellors',
    icon: HeartHandshake,
    badgeBg: 'bg-rose-100',
    badgeText: 'text-rose-800',
    activeBg: 'bg-rose-50',
    activeText: 'text-rose-900',
    iconColor: 'text-rose-600',
  },
  {
    id: 'admin',
    label: 'Administrator Portal',
    portalName: 'Institution Deans & Admins',
    icon: ShieldCheck,
    badgeBg: 'bg-amber-100',
    badgeText: 'text-amber-800',
    activeBg: 'bg-amber-50',
    activeText: 'text-amber-900',
    iconColor: 'text-amber-600',
  },
]

export function RoleSwitcher({ align = 'right', className = '' }: RoleSwitcherProps) {
  const { userRole, switchRole } = useApp()
  const [isOpen, setIsOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  const currentRole = ROLES.find((r) => r.id === userRole) || ROLES[0]
  const CurrentIcon = currentRole.icon

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setIsOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  return (
    <div className={`relative ${className}`} ref={dropdownRef}>
      {/* Current Role Trigger Button */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-1.5 bg-white border border-gray-200/90 rounded-full shadow-2xs hover:border-gray-300 hover:bg-gray-50/70 transition text-xs font-semibold text-[#1E2433] cursor-pointer"
        title="Switch Portal Role"
      >
        <CurrentIcon className={`w-3.5 h-3.5 ${currentRole.iconColor}`} />
        <span className="font-semibold">{currentRole.label}</span>
        <ChevronDown className="w-3 h-3 text-gray-400" />
      </button>

      {/* Role Selection Dropdown */}
      {isOpen && (
        <div
          className={`absolute top-full mt-2 w-60 bg-white rounded-2xl shadow-xl border border-gray-100 p-2 z-50 animate-in fade-in slide-in-from-top-2 duration-150 ${
            align === 'left' ? 'left-0' : 'right-0'
          }`}
        >
          <div className="px-3 py-1.5 border-b border-gray-100 mb-1 flex items-center justify-between">
            <span className="text-[11px] font-bold uppercase tracking-wider text-gray-400">
              Switch Portal
            </span>
            <span className="text-[10px] text-gray-400">4 Roles Available</span>
          </div>

          <div className="flex flex-col gap-1">
            {ROLES.map((role) => {
              const RoleIcon = role.icon
              const isActive = role.id === userRole

              if (isActive) {
                return (
                  <div
                    key={role.id}
                    className={`w-full flex items-center justify-between px-3 py-2 rounded-xl text-xs font-bold ${role.activeBg} ${role.activeText}`}
                  >
                    <div className="flex items-center gap-2.5">
                      <RoleIcon className={`w-4 h-4 ${role.iconColor}`} />
                      <div className="text-left">
                        <p className="leading-tight">{role.label}</p>
                        <p className="text-[10px] font-normal opacity-70">
                          {role.portalName}
                        </p>
                      </div>
                    </div>
                    <span
                      className={`text-[10px] ${role.badgeBg} ${role.badgeText} px-1.5 py-0.5 rounded-md font-bold`}
                    >
                      Active
                    </span>
                  </div>
                )
              }

              return (
                <button
                  key={role.id}
                  type="button"
                  onClick={() => {
                    setIsOpen(false)
                    switchRole(role.id)
                  }}
                  className="w-full flex items-center justify-between px-3 py-2 rounded-xl text-xs font-semibold text-gray-700 hover:bg-gray-50 transition text-left cursor-pointer group"
                >
                  <div className="flex items-center gap-2.5">
                    <RoleIcon
                      className={`w-4 h-4 text-gray-400 group-hover:${role.iconColor} transition-colors`}
                    />
                    <div>
                      <p className="leading-tight group-hover:text-[#1E2433] transition-colors">
                        {role.label}
                      </p>
                      <p className="text-[10px] text-gray-400 font-normal">
                        {role.portalName}
                      </p>
                    </div>
                  </div>
                  <span className="text-[10px] text-gray-300 group-hover:text-gray-500 font-mono transition-colors">
                    Switch →
                  </span>
                </button>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}

