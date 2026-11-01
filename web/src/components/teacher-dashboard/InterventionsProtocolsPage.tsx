import React, { useState } from 'react'
import { categoryLabel } from '../../lib/labels'
import { QueryState, EmptyState } from '../common/QueryState'
import { useCatalogue } from '../../lib/api/endpoints/admin.hooks'
import { BookOpen, ShieldCheck, Clock, Users, Sparkles, Filter } from 'lucide-react'

export function InterventionsProtocolsPage() {
  const catalogue = useCatalogue()
  const [filterCat, setFilterCat] = useState<string>('ALL')

  return (
    <main className="flex-1 p-4 font-sans space-y-4 overflow-y-auto">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2">
        <div>
          <h1 className="text-lg font-bold text-ink">Ways to help students</h1>
          <p className="text-xs text-muted">
            Support options you can suggest when a student is struggling.
          </p>
        </div>

        {/* Filter Pills */}
        <div className="flex items-center gap-1.5 p-1 bg-white border border-line rounded-full text-xs font-semibold text-gray-500">
          <Filter className="w-3.5 h-3.5 ml-2 text-muted" />
          {[['ALL', 'All'], ['academic', 'Study'], ['counselling', 'Counselling'], ['financial', 'Money'], ['tutoring', 'Tutoring']].map(([cat, catLabel]) => (
            <button
              key={cat}
              onClick={() => setFilterCat(cat)}
              className={`px-3 py-1 rounded-full transition cursor-pointer ${
                filterCat === cat ? 'bg-indigo-600 text-white font-bold' : 'hover:text-gray-900'
              }`}
            >
              {catLabel}
            </button>
          ))}
        </div>
      </div>

      <QueryState
        query={catalogue}
        empty={<EmptyState title="No support options yet" message="Your campus admin can add them." />}
      >
        {(rows) => {
          const filtered = filterCat === 'ALL' ? rows : rows.filter((r) => r.category?.toLowerCase().includes(filterCat))

          return (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3.5">
              {filtered.map((item) => (
                <div
                  key={item.id}
                  className="bg-white rounded-2xl border border-line p-4 shadow-xs flex flex-col justify-between space-y-3"
                >
                  <div className="space-y-1.5">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700">
                        {categoryLabel(item.category) || 'Support'}
                      </span>
                      <span className={`text-xs font-bold ${item.is_active ? 'text-emerald-600' : 'text-muted'}`}>
                        {item.is_active ? '● Available' : '○ Not available'}
                      </span>
                    </div>

                    <h3 className="text-sm font-bold text-ink leading-snug">{item.name}</h3>
                    {item.description && (
                      <p className="text-xs text-muted leading-relaxed line-clamp-3">
                        {item.description}
                      </p>
                    )}
                  </div>

                </div>
              ))}
            </div>
          )
        }}
      </QueryState>
    </main>
  )
}
