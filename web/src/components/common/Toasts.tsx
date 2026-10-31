import React from 'react'
import { CheckCircle2, AlertCircle, Info, X } from 'lucide-react'
import { useApp } from '../../context/AppContext'

export function Toasts() {
  const { toasts, removeToast } = useApp()

  if (toasts.length === 0) return null

  return (
    <div className="fixed bottom-5 right-5 z-50 flex max-w-sm flex-col gap-2.5">
      {toasts.map((t) => {
        const isSuccess = t.type === 'success'
        const isError = t.type === 'error'
        const isWarning = t.type === 'warning'

        return (
          <div
            key={t.id}
            className={`flex items-start gap-3 rounded-lg border-2 border-ink p-3.5 shadow-[4px_4px_0_#0d1b3e] transition-all duration-200 animate-in slide-in-from-bottom-2 ${
              isSuccess
                ? 'bg-[#ecfdf5] text-emerald-950'
                : isError
                ? 'bg-[#fef2f2] text-red-950'
                : isWarning
                ? 'bg-[#fffbeb] text-amber-950'
                : 'bg-white text-ink'
            }`}
          >
            <span className="mt-0.5 shrink-0">
              {isSuccess && <CheckCircle2 className="h-5 w-5 text-emerald-600" />}
              {isError && <AlertCircle className="h-5 w-5 text-red-600" />}
              {isWarning && <AlertCircle className="h-5 w-5 text-amber-600" />}
              {t.type === 'info' && <Info className="h-5 w-5 text-brand" />}
            </span>

            <div className="min-w-0 flex-1">
              <p className="text-xs font-bold leading-snug">{t.title}</p>
              {t.message && <p className="mt-0.5 text-[11px] leading-relaxed opacity-90">{t.message}</p>}
            </div>

            <button
              onClick={() => removeToast(t.id)}
              className="p-0.5 text-gray-400 hover:text-black"
              aria-label="Close notification"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          </div>
        )
      })}
    </div>
  )
}
