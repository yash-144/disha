import React from 'react'
import { Sparkles, ArrowRight } from 'lucide-react'

interface PortalPlaceholderProps {
  portalName: string
  pageTitle: string
  routePath: string
  icon: React.ComponentType<{ className?: string }>
  description?: string
  capabilities?: string[]
}

export function PortalPlaceholder({
  portalName,
  pageTitle,
  routePath,
  icon: Icon,
  description,
  capabilities = [],
}: PortalPlaceholderProps) {
  return (
    <div className="flex-1 flex flex-col justify-center items-center py-12 px-4 select-none font-sans">
      <div className="max-w-xl w-full bg-white rounded-3xl p-8 sm:p-10 border border-gray-100 shadow-2xs text-center flex flex-col items-center">
        {/* Soft pastel icon container */}
        <div className="w-16 h-16 rounded-2xl bg-[#EDE8FB] text-[#7C3AED] flex items-center justify-center mb-5 shadow-2xs">
          <Icon className="w-8 h-8" />
        </div>

        {/* Badges: Portal Name + Route */}
        <div className="flex items-center gap-2 flex-wrap justify-center mb-2">
          <span className="text-[11px] font-bold uppercase tracking-wider text-purple-700 bg-purple-50 px-2.5 py-1 rounded-full border border-purple-100">
            {portalName}
          </span>
          <span className="text-[11px] font-mono text-gray-500 bg-gray-50 px-2.5 py-1 rounded-full border border-gray-200/70">
            {routePath}
          </span>
        </div>

        {/* Title */}
        <h2 className="text-2xl font-bold tracking-tight text-[#1E2433] mt-2">
          {pageTitle}
        </h2>

        {/* Description */}
        <p className="text-xs text-[#717E95] max-w-md mt-2.5 leading-relaxed font-medium">
          {description ||
            `The ${pageTitle} module is established as part of the DISHA multi-role portal architecture. Detailed workflows and page interfaces will be implemented in subsequent milestones.`}
        </p>

        {/* Planned capabilities preview */}
        {capabilities.length > 0 && (
          <div className="w-full mt-6 pt-6 border-t border-gray-100 text-left">
            <span className="text-[11px] font-bold text-gray-400 uppercase tracking-wider block mb-2.5">
              Configured Module Scope
            </span>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {capabilities.map((cap, idx) => (
                <div
                  key={idx}
                  className="flex items-center gap-2 p-2 rounded-xl bg-gray-50/70 border border-gray-100 text-xs text-[#334155] font-medium"
                >
                  <ArrowRight className="w-3 h-3 text-purple-500 shrink-0" />
                  <span className="truncate">{cap}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Architectural readiness indicator */}
        <div className="mt-6 flex items-center gap-1.5 text-[11px] text-emerald-700 bg-emerald-50 px-3 py-1.5 rounded-full border border-emerald-200">
          <Sparkles className="w-3.5 h-3.5 text-emerald-600" />
          <span className="font-semibold">Navigation and routing active • Ready for interface design</span>
        </div>
      </div>
    </div>
  )
}

