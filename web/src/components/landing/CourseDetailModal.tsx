import React, { useState } from 'react'
import {
  X,
  Star,
  Clock,
  BookOpen,
  Award,
  CheckCircle,
  PlayCircle,
  ChevronDown,
  ChevronUp,
  Share2,
} from 'lucide-react'
import { useApp } from '../../context/AppContext'

export function CourseDetailModal() {
  const { activeCourseDetail, setActiveCourseDetail, enrollInCourse, enrolledCourseIds, addToast } = useApp()
  const [openModuleIndex, setOpenModuleIndex] = useState<number>(0)

  if (!activeCourseDetail) return null

  const isEnrolled = enrolledCourseIds.includes(activeCourseDetail.id)

  const handleShare = () => {
    navigator.clipboard?.writeText?.(window.location.href)
    addToast('Link Copied!', 'Course link copied to your clipboard.', 'info')
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-xs animate-in fade-in overflow-y-auto">
      <div className="relative my-8 max-h-[90vh] w-full max-w-3xl overflow-hidden rounded-2xl border-4 border-ink bg-white shadow-[10px_10px_0_#0d1b3e] flex flex-col">
        {/* Top Header */}
        <div className="flex items-center justify-between border-b-2 border-ink bg-[#f5f7fc] px-6 py-4">
          <div className="flex items-center gap-2">
            <span className={`px-2 py-0.5 text-xs font-bold text-white ${activeCourseDetail.badgeColor || 'bg-brand'}`}>
              {activeCourseDetail.categoryLabel}
            </span>
            <span className="text-xs text-muted">· {activeCourseDetail.level}</span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleShare}
              className="rounded p-1 text-gray-600 hover:bg-gray-200"
              title="Share course"
            >
              <Share2 className="h-4 w-4" />
            </button>
            <button
              onClick={() => setActiveCourseDetail(null)}
              className="rounded p-1 text-gray-600 hover:bg-gray-200 hover:text-black"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>

        {/* Scrollable Content */}
        <div className="overflow-y-auto p-6 space-y-6">
          {/* Title & Stats */}
          <div>
            <h2 className="text-xl font-bold leading-tight sm:text-2xl text-ink">
              {activeCourseDetail.title}
            </h2>
            <p className="mt-2 text-xs leading-relaxed text-muted sm:text-sm">
              {activeCourseDetail.desc}
            </p>

            <div className="mt-4 flex flex-wrap items-center gap-4 text-xs">
              <div className="flex items-center gap-1 font-bold text-amber-500">
                <Star className="h-4 w-4 fill-amber-400 text-amber-400" />
                <span>{activeCourseDetail.rating}</span>
                <span className="font-normal text-muted">({activeCourseDetail.reviewsCount} reviews)</span>
              </div>
              <div className="flex items-center gap-1 text-gray-700">
                <Clock className="h-4 w-4 text-brand" />
                <span>{activeCourseDetail.duration} Total Duration</span>
              </div>
              <div className="flex items-center gap-1 text-gray-700">
                <BookOpen className="h-4 w-4 text-[#0f9d58]" />
                <span>{activeCourseDetail.lecturesCount} Lessons</span>
              </div>
              <div className="flex items-center gap-1 text-gray-700">
                <Award className="h-4 w-4 text-purple-600" />
                <span>Certificate Included</span>
              </div>
            </div>
          </div>

          {/* Instructor Snapshot */}
          <div className="flex items-center gap-3 rounded-xl border-2 border-ink bg-[#f8fafc] p-3.5">
            <img
              src={activeCourseDetail.instructorAvatar}
              alt={activeCourseDetail.instructorName}
              className="h-12 w-12 rounded-full border border-ink object-cover"
            />
            <div>
              <p className="text-xs text-muted">Course Instructor</p>
              <p className="text-sm font-bold text-ink">{activeCourseDetail.instructorName}</p>
              <p className="text-[11px] text-gray-600">{activeCourseDetail.instructorTitle}</p>
            </div>
          </div>

          {/* Curriculum Accordion */}
          <div>
            <h3 className="text-sm font-bold text-ink mb-3 flex items-center justify-between">
              <span>Syllabus &amp; Learning Modules</span>
              <span className="text-xs font-normal text-muted">{activeCourseDetail.modules.length} Modules</span>
            </h3>

            <div className="space-y-2">
              {activeCourseDetail.modules.map((mod, idx) => {
                const isOpen = openModuleIndex === idx
                return (
                  <div key={mod.title} className="rounded-lg border-2 border-ink bg-white overflow-hidden">
                    <button
                      onClick={() => setOpenModuleIndex(isOpen ? -1 : idx)}
                      className="flex w-full items-center justify-between bg-[#f5f7fc] p-3 text-left text-xs font-bold hover:bg-gray-100"
                    >
                      <span className="flex items-center gap-2">
                        <PlayCircle className="h-4 w-4 text-brand" />
                        {mod.title}
                      </span>
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] font-normal text-muted">{mod.duration}</span>
                        {isOpen ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                      </div>
                    </button>

                    {isOpen && (
                      <ul className="divide-y divide-gray-100 p-3 text-xs text-gray-700 space-y-1.5">
                        {mod.lessons.map((lesson, lIdx) => (
                          <li key={lIdx} className="flex items-center gap-2 pt-1">
                            <CheckCircle className="h-3.5 w-3.5 text-[#0f9d58] shrink-0" />
                            <span>{lesson}</span>
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                )
              })}
            </div>
          </div>

          {/* Prerequisites */}
          <div className="rounded-lg border border-gray-200 bg-gray-50 p-3.5 text-xs">
            <h4 className="font-bold text-ink mb-1.5">Prerequisites:</h4>
            <ul className="list-disc pl-4 space-y-1 text-gray-600">
              {activeCourseDetail.prerequisites.map((p, idx) => (
                <li key={idx}>{p}</li>
              ))}
            </ul>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="border-t-2 border-ink bg-[#f5f7fc] px-6 py-4 flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="flex items-baseline gap-2">
              <span className="text-2xl font-bold text-ink">{activeCourseDetail.price}</span>
              <span className="text-sm text-gray-400 line-through">{activeCourseDetail.originalPrice}</span>
              <span className="text-xs font-bold text-[#0f9d58]">Save 68%</span>
            </div>
            <p className="text-[10px] text-muted">Lifetime access with 30-day money-back guarantee</p>
          </div>

          <div className="flex items-center gap-3">
            {isEnrolled ? (
              <button
                disabled
                className="flex items-center gap-2 border-2 border-ink bg-gray-200 px-6 py-2.5 text-xs font-bold text-gray-700"
              >
                <CheckCircle className="h-4 w-4 text-[#0f9d58]" /> Already Enrolled
              </button>
            ) : (
              <button
                onClick={() => enrollInCourse(activeCourseDetail.id)}
                className="border-2 border-ink bg-[#0f9d58] px-8 py-2.5 text-xs font-bold text-white shadow-[3px_3px_0_#0d1b3e] transition hover:bg-[#0b7a43]"
              >
                Enroll Now →
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
