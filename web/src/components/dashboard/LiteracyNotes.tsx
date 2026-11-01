import React, { useState, useEffect } from 'react'
import { Bold, Italic, List, Code, CheckSquare, Sparkles, Save, BookOpen } from 'lucide-react'
import { useApp } from '../../context/AppContext'

const DEFAULT_NOTE = `# Lesson Plan: React 19 Server Components & Hooks

### Learning Objectives:
1. Understand client vs server component boundaries
2. Leverage \`useTransition\` for seamless non-blocking tab switches
3. Build responsive collaborative canvas with HTML5 2D contexts

### Homework & Mini-Project:
- Refactor the class whiteboard with real-time undo history.
- Submit code sandbox link before Friday 6:00 PM IST.`

export function LiteracyNotes() {
  const { addToast } = useApp()
  const [noteContent, setNoteContent] = useState(() => {
    return localStorage.getItem('skillsup_literacy_note') || DEFAULT_NOTE
  })
  const [wordCount, setWordCount] = useState(0)

  useEffect(() => {
    const words = noteContent.trim().split(/\s+/).filter(Boolean).length
    setWordCount(words)
    localStorage.setItem('skillsup_literacy_note', noteContent)
  }, [noteContent])

  const insertSyntax = (prefix: string, suffix: string = '') => {
    setNoteContent((prev) => prev + `\n${prefix} ` + suffix)
  }

  const handleManualSave = () => {
    localStorage.setItem('skillsup_literacy_note', noteContent)
    addToast('Lesson Notes Saved', 'Notes stored safely for this session.', 'success')
  }

  return (
    <div className="flex flex-col border-2 border-ink bg-white p-3 font-mono shadow-[2px_2px_0_#0d1b3e]">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b-2 border-ink/20 pb-2">
        <div className="flex items-center gap-2">
          <BookOpen className="h-4 w-4 text-brand" />
          <span className="text-xs font-bold text-ink">Lesson Scratchpad &amp; Syntax Notes</span>
        </div>
        <div className="flex items-center gap-1.5">
          <button
            onClick={() => insertSyntax('**Bold Text**')}
            title="Bold"
            className="border border-ink bg-gray-50 p-1 text-ink hover:bg-gray-200"
          >
            <Bold className="h-3.5 w-3.5" />
          </button>
          <button
            onClick={() => insertSyntax('*Italic Text*')}
            title="Italic"
            className="border border-ink bg-gray-50 p-1 text-ink hover:bg-gray-200"
          >
            <Italic className="h-3.5 w-3.5" />
          </button>
          <button
            onClick={() => insertSyntax('- Bullet point item')}
            title="Bullet list"
            className="border border-ink bg-gray-50 p-1 text-ink hover:bg-gray-200"
          >
            <List className="h-3.5 w-3.5" />
          </button>
          <button
            onClick={() => insertSyntax('```typescript\n// code example here\n```')}
            title="Code block"
            className="border border-ink bg-gray-50 p-1 text-ink hover:bg-gray-200"
          >
            <Code className="h-3.5 w-3.5" />
          </button>
          <button
            onClick={() => insertSyntax('- [ ] Task todo')}
            title="Checkbox"
            className="border border-ink bg-gray-50 p-1 text-ink hover:bg-gray-200"
          >
            <CheckSquare className="h-3.5 w-3.5" />
          </button>
          <button
            onClick={handleManualSave}
            className="ml-2 flex items-center gap-1 border border-ink bg-[#0f9d58] px-2.5 py-1 text-[11px] font-bold text-white shadow-[1px_1px_0_#0d1b3e] transition hover:bg-[#0b7a43]"
          >
            <Save className="h-3 w-3" /> Save Notes
          </button>
        </div>
      </div>

      <textarea
        value={noteContent}
        onChange={(e) => setNoteContent(e.target.value)}
        rows={8}
        className="mt-2 w-full resize-y border-2 border-ink bg-[#f8fafd] p-3 font-mono text-xs leading-relaxed text-ink outline-none focus:bg-white"
        placeholder="Type lesson outline, student notes, code snippets, or discussion prompts here..."
      />

      <div className="mt-2 flex items-center justify-between text-[10px] text-gray-500 font-bold">
        <span className="flex items-center gap-1">
          <Sparkles className="h-3 w-3 text-[#0f9d58]" /> Auto-saves every stroke locally
        </span>
        <span>{wordCount} words · Markdown supported</span>
      </div>
    </div>
  )
}
