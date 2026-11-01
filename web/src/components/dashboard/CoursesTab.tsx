import React, { useState } from 'react'
import {
  Plus,
  BookOpen,
  Clock,
  Star,
  Users,
  Search,
  CheckCircle,
  MoreVertical,
  X,
  Code2,
  Trash2,
  Lock,
} from 'lucide-react'
import { useApp } from '../../context/AppContext'
import { Course } from '../../types'

export function CoursesTab() {
  const { courses, addNewCourse, addToast, setActiveCourseDetail } = useApp()
  const [showAddModal, setShowAddModal] = useState(false)
  const [search, setSearch] = useState('')
  const [newTitle, setNewTitle] = useState('')
  const [newCategory, setNewCategory] = useState<'web' | 'data' | 'design' | 'cloud' | 'business'>('web')
  const [newDuration, setNewDuration] = useState('24 Hours')
  const [newPrice, setNewPrice] = useState('₹1,599')
  const [newDesc, setNewDesc] = useState('')

  const handleCreateCourse = (e: React.FormEvent) => {
    e.preventDefault()
    if (!newTitle.trim()) return

    addNewCourse({
      title: newTitle,
      category: newCategory,
      categoryLabel:
        newCategory === 'web'
          ? 'Computer Science & IT'
          : newCategory === 'data'
          ? 'Data & SQL'
          : newCategory === 'design'
          ? 'Design & Multimedia'
          : 'Cloud Infrastructure',
      duration: newDuration,
      price: newPrice,
      originalPrice: '₹3,999',
      desc: newDesc || 'In-depth practical curriculum designed for production engineering.',
    })

    setShowAddModal(false)
    setNewTitle('')
    setNewDesc('')
    addToast('Course Created!', `Course "${newTitle}" has been added to the syllabus catalog.`, 'success')
  }

  const filtered = courses.filter((c) =>
    c.title.toLowerCase().includes(search.toLowerCase()) ||
    c.categoryLabel.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div className="space-y-6 font-mono">
      {/* Header and Add Button */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-2 border-ink bg-white p-4 shadow-[4px_4px_0_#0d1b3e]">
        <div>
          <div className="flex items-center gap-2">
            <span className="rounded bg-brand px-2 py-0.5 text-[10px] font-bold text-white shadow-[1.5px_1.5px_0_#0d1b3e]">
              CURRICULUM REPO
            </span>
            <span className="text-xs text-muted">({courses.length} Bootcamps)</span>
          </div>
          <h2 className="mt-1 text-lg font-bold text-ink sm:text-xl">Course Catalog &amp; Syllabi</h2>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center border-2 border-ink bg-paper px-3 py-1.5 text-xs shadow-[2px_2px_0_#0d1b3e]">
            <Search className="mr-2 h-3.5 w-3.5 text-gray-400" />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search courses..."
              className="w-36 bg-transparent outline-none sm:w-48 text-xs font-medium text-ink"
            />
          </div>

          <button
            onClick={() => setShowAddModal(true)}
            className="flex items-center gap-1.5 border-2 border-ink bg-accent px-4 py-2 text-xs font-bold text-white shadow-[2px_2px_0_#0d1b3e] transition hover:bg-accent-dark hover:-translate-x-0.5 hover:-translate-y-0.5"
          >
            <Plus className="h-4 w-4" /> Add Course
          </button>
        </div>
      </div>

      {/* Courses List */}
      <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
        {filtered.map((course) => (
          <div
            key={course.id}
            className="flex flex-col justify-between border-2 border-ink bg-white p-5 shadow-[4px_4px_0_#0d1b3e] transition hover:-translate-y-1 hover:shadow-[6px_6px_0_#0d1b3e]"
          >
            <div>
              <div className="flex items-start justify-between">
                <span className="border border-ink bg-accent px-2 py-0.5 text-[10px] font-bold text-white shadow-[1.5px_1.5px_0_#0d1b3e]">
                  {course.categoryLabel}
                </span>
                <span className="flex items-center gap-1 text-xs font-bold text-amber-500">
                  <Star className="h-3.5 w-3.5 fill-amber-400" /> {course.rating}
                </span>
              </div>

              <h3 className="mt-3 text-sm font-bold leading-snug text-ink">{course.title}</h3>
              <p className="mt-1.5 text-xs text-muted line-clamp-2 leading-relaxed">{course.desc}</p>

              <div className="mt-4 flex items-center gap-3 border-y border-ink/10 py-2 text-[11px] text-gray-600">
                <span className="flex items-center gap-1">
                  <Clock className="h-3.5 w-3.5 text-brand" /> {course.duration}
                </span>
                <span className="flex items-center gap-1">
                  <BookOpen className="h-3.5 w-3.5 text-accent" /> {course.modules.length} Modules
                </span>
              </div>

              {/* Progress Bar */}
              <div className="mt-3">
                <div className="flex justify-between text-[10px] text-gray-600 font-bold">
                  <span>Cohort Completion</span>
                  <span className="text-brand">84%</span>
                </div>
                <div className="mt-1 h-2 w-full border border-ink bg-gray-100 overflow-hidden">
                  <div className="h-full bg-brand" style={{ width: '84%' }} />
                </div>
              </div>
            </div>

            <div className="mt-5 border-t-2 border-ink/10 pt-3 flex items-center justify-between">
              <div>
                <span className="text-sm font-bold text-ink">{course.price}</span>
                <span className="ml-1 text-[10px] text-gray-400 line-through">{course.originalPrice}</span>
              </div>
              <button
                onClick={() => setActiveCourseDetail(course)}
                className="border-2 border-ink bg-paper px-3 py-1 text-xs font-bold text-ink shadow-[2px_2px_0_#0d1b3e] transition hover:bg-white hover:text-brand"
              >
                View Syllabus →
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Add Course Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-xs animate-in fade-in">
          <div className="w-full max-w-lg border-4 border-ink bg-white p-6 shadow-[8px_8px_0_#0d1b3e]">
            <div className="flex items-center justify-between border-b-2 border-ink/20 pb-3">
              <h3 className="text-base font-bold text-ink">Publish New Course to Catalog</h3>
              <button
                onClick={() => setShowAddModal(false)}
                className="border border-ink p-1 text-gray-600 hover:bg-gray-100"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <form onSubmit={handleCreateCourse} className="mt-4 space-y-3.5">
              <div>
                <label className="text-xs font-bold text-ink">Course Title *</label>
                <input
                  required
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  placeholder="e.g. Microservices with Docker and Go"
                  className="mt-1 w-full border-2 border-ink p-2 text-xs outline-none focus:bg-paper"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-bold text-ink">Category Track</label>
                  <select
                    value={newCategory}
                    onChange={(e) => setNewCategory(e.target.value as any)}
                    className="mt-1 w-full border-2 border-ink p-2 text-xs font-bold outline-none"
                  >
                    <option value="web">Web Development</option>
                    <option value="data">Data &amp; SQL</option>
                    <option value="design">UI/UX Design</option>
                    <option value="cloud">Cloud Architecture</option>
                    <option value="business">Business</option>
                  </select>
                </div>

                <div>
                  <label className="text-xs font-bold text-ink">Estimated Duration</label>
                  <input
                    value={newDuration}
                    onChange={(e) => setNewDuration(e.target.value)}
                    placeholder="e.g. 30 Hours"
                    className="mt-1 w-full border-2 border-ink p-2 text-xs outline-none focus:bg-paper"
                  />
                </div>
              </div>

              <div>
                <label className="text-xs font-bold text-ink">Enrollment Fee</label>
                <input
                  value={newPrice}
                  onChange={(e) => setNewPrice(e.target.value)}
                  placeholder="e.g. ₹1,599"
                  className="mt-1 w-full border-2 border-ink p-2 text-xs outline-none focus:bg-paper"
                />
              </div>

              <div>
                <label className="text-xs font-bold text-ink">Course Description</label>
                <textarea
                  rows={3}
                  value={newDesc}
                  onChange={(e) => setNewDesc(e.target.value)}
                  placeholder="Outline syllabus learning objectives and technologies covered..."
                  className="mt-1 w-full border-2 border-ink p-2 text-xs outline-none focus:bg-paper"
                />
              </div>

              <div className="mt-5 flex justify-end gap-2 border-t-2 border-ink/20 pt-4">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="border-2 border-ink bg-gray-100 px-4 py-2 text-xs font-bold text-gray-700 hover:bg-gray-200"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="border-2 border-ink bg-accent px-5 py-2 text-xs font-bold text-white shadow-[2px_2px_0_#0d1b3e] hover:bg-accent-dark"
                >
                  Publish Course
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
