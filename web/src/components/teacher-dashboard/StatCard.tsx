import React from 'react'
import { LucideIcon } from 'lucide-react'

interface StatCardProps {
  title: string
  value: number | string
  icon: LucideIcon
  variant: 'yellow' | 'blue' | 'purple'
}

export function StatCard({ title, value, icon: Icon, variant }: StatCardProps) {
  const variantStyles = {
    yellow: {
      bg: 'bg-[#FDF2D5]',
      titleColor: 'text-[#614F23]',
      iconColor: 'text-[#614F23]',
    },
    blue: {
      bg: 'bg-[#E5EEFB]',
      titleColor: 'text-[#284873]',
      iconColor: 'text-[#2563EB]',
    },
    purple: {
      bg: 'bg-[#ECE8FB]',
      titleColor: 'text-[#524077]',
      iconColor: 'text-[#7C3AED]',
    },
  }[variant]

  return (
    <div
      className={`${variantStyles.bg} rounded-2xl p-4 flex flex-col justify-between shadow-2xs font-sans transition-transform hover:-translate-y-0.5 duration-150`}
    >
      <span className={`text-xs font-bold tracking-tight ${variantStyles.titleColor}`}>
        {title}
      </span>

      <div className="flex items-center justify-between mt-3">
        <span className="text-3xl font-bold tracking-tight text-[#1E2433]">
          {value}
        </span>
        <div className="flex items-center justify-center w-8 h-8 rounded-full bg-white/90 shadow-2xs">
          <Icon className={`w-4 h-4 ${variantStyles.iconColor}`} />
        </div>
      </div>
    </div>
  )
}

