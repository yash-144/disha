import React from 'react'
import { FileCode2, FileText, Download, FolderGit2, BookOpen } from 'lucide-react'
import { useApp } from '../../context/AppContext'

const RESOURCES = [
  {
    title: 'React 19 Custom Hooks & Canvas Starter Repo',
    type: 'Code Repository',
    size: '4.2 MB',
    format: 'ZIP / Git',
    icon: FolderGit2,
    desc: 'Clean boilerplate with Vite, Tailwind v4, and collaborative HTML5 canvas primitives.',
  },
  {
    title: 'SQL Query Optimization & Indexing Cheatsheet',
    type: 'PDF Reference',
    size: '1.8 MB',
    format: 'PDF',
    icon: FileText,
    desc: 'EXPLAIN ANALYZE cheat sheet, B-Tree index rules, and common JOIN performance bottlenecks.',
  },
  {
    title: 'Figma Design System UI Kit & Tokens (2025)',
    type: 'Design Asset',
    size: '12.4 MB',
    format: 'FIG',
    icon: BookOpen,
    desc: 'Comprehensive typographic scale, neo-brutalist buttons, and responsive modal components.',
  },
  {
    title: 'AWS Certified Solutions Architect Exam Guide',
    type: 'Curriculum Guide',
    size: '2.5 MB',
    format: 'PDF',
    icon: FileText,
    desc: 'Study notes, VPC subnet math worksheets, and practice scenario breakdowns.',
  },
]

export function ResourcesTab() {
  const { addToast } = useApp()

  const handleDownload = (item: (typeof RESOURCES)[0]) => {
    addToast('Download Started', `Downloading "${item.title}" (${item.size})...`, 'success')
  }

  return (
    <div className="space-y-6 font-mono">
      <div className="border-2 border-ink bg-white p-4 shadow-[4px_4px_0_#0d1b3e]">
        <div className="flex items-center gap-2">
          <span className="rounded bg-accent px-2 py-0.5 text-[10px] font-bold text-white shadow-[1.5px_1.5px_0_#0d1b3e]">
            ASSET VAULT
          </span>
          <span className="text-xs text-muted">(Free for Cohort Learners)</span>
        </div>
        <h2 className="mt-1 text-lg font-bold text-ink sm:text-xl">Learning Resources &amp; Downloads</h2>
      </div>

      <div className="grid gap-5 sm:grid-cols-2">
        {RESOURCES.map((res) => {
          const Icon = res.icon
          return (
            <div
              key={res.title}
              className="flex flex-col justify-between border-2 border-ink bg-white p-5 shadow-[4px_4px_0_#0d1b3e] transition hover:-translate-y-1 hover:shadow-[6px_6px_0_#0d1b3e]"
            >
              <div>
                <div className="flex items-start justify-between">
                  <span className="flex h-11 w-11 items-center justify-center border-2 border-ink bg-accent text-white shadow-[2px_2px_0_#0d1b3e]">
                    <Icon className="h-5 w-5" />
                  </span>
                  <span className="border border-ink bg-paper px-2 py-0.5 text-[10px] font-bold text-ink shadow-[1px_1px_0_#0d1b3e]">
                    {res.format} · {res.size}
                  </span>
                </div>

                <h3 className="mt-3.5 text-sm font-bold text-ink leading-snug">{res.title}</h3>
                <p className="mt-1 text-xs text-muted leading-relaxed">{res.desc}</p>
              </div>

              <div className="mt-5 border-t-2 border-ink/10 pt-3 flex items-center justify-between">
                <span className="text-[11px] font-bold text-brand">{res.type}</span>
                <button
                  onClick={() => handleDownload(res)}
                  className="flex items-center gap-1.5 border-2 border-ink bg-accent px-3.5 py-1.5 text-xs font-bold text-white shadow-[2px_2px_0_#0d1b3e] transition hover:bg-accent-dark hover:-translate-x-0.5 hover:-translate-y-0.5"
                >
                  <Download className="h-3.5 w-3.5" /> Download
                </button>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
