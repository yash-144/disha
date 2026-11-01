import React from 'react'
import { X, Calendar, Clock, User, Share2, ThumbsUp, Bookmark } from 'lucide-react'
import { useApp } from '../../context/AppContext'

export function BlogModal() {
  const { activeBlogPost, setActiveBlogPost, addToast } = useApp()

  if (!activeBlogPost) return null

  const handleShare = () => {
    navigator.clipboard?.writeText?.(window.location.href)
    addToast('Post link copied!', 'Share with your study group or colleagues.', 'info')
  }

  const handleBookmark = () => {
    addToast('Bookmarked!', `"${activeBlogPost.title}" added to your saved articles.`, 'success')
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-xs animate-in fade-in overflow-y-auto">
      <div className="relative my-8 max-h-[90vh] w-full max-w-3xl overflow-hidden rounded-2xl border-4 border-ink bg-white shadow-[10px_10px_0_#0d1b3e] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between border-b-2 border-ink bg-paper px-6 py-4">
          <div className="flex items-center gap-2">
            <span className={`px-2 py-0.5 text-xs font-bold text-white ${activeBlogPost.tagBg}`}>
              {activeBlogPost.tag}
            </span>
            <span className="text-xs text-muted flex items-center gap-1">
              <Clock className="h-3.5 w-3.5" /> {activeBlogPost.readTime}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleBookmark}
              className="rounded p-1 text-gray-600 hover:bg-gray-200"
              title="Bookmark"
            >
              <Bookmark className="h-4 w-4" />
            </button>
            <button
              onClick={handleShare}
              className="rounded p-1 text-gray-600 hover:bg-gray-200"
              title="Share"
            >
              <Share2 className="h-4 w-4" />
            </button>
            <button
              onClick={() => setActiveBlogPost(null)}
              className="rounded p-1 text-gray-600 hover:bg-gray-200 hover:text-black"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="overflow-y-auto p-6 space-y-5">
          <img
            src={activeBlogPost.img}
            alt={activeBlogPost.title}
            className="aspect-[21/9] w-full rounded-xl border-2 border-ink object-cover shadow-[4px_4px_0_#0d1b3e]"
          />

          <h2 className="text-xl font-bold leading-snug sm:text-2xl text-ink">
            {activeBlogPost.title}
          </h2>

          <div className="flex items-center gap-4 border-y border-gray-100 py-3 text-xs text-muted">
            <span className="flex items-center gap-1.5 font-medium text-ink">
              <User className="h-3.5 w-3.5 text-brand" /> {activeBlogPost.author}
            </span>
            <span className="flex items-center gap-1.5">
              <Calendar className="h-3.5 w-3.5" /> {activeBlogPost.date}
            </span>
          </div>

          <div className="space-y-4 text-sm leading-relaxed text-gray-700">
            {activeBlogPost.content.map((paragraph, idx) => (
              <p key={idx}>{paragraph}</p>
            ))}
          </div>

          <div className="mt-8 rounded-xl border-2 border-ink bg-paper p-4 flex items-center justify-between">
            <div>
              <p className="text-xs font-bold text-ink">Did you find this article valuable?</p>
              <p className="text-[11px] text-muted">Join over 7,000+ engineers reading SkillsUp weekly digest.</p>
            </div>
            <button
              onClick={() => addToast('Thank you!', 'Your feedback helps improve our community content.', 'success')}
              className="flex items-center gap-1.5 border border-ink bg-white px-3 py-1.5 text-xs font-bold shadow-[2px_2px_0_#0d1b3e] hover:bg-gray-50"
            >
              <ThumbsUp className="h-3.5 w-3.5 text-brand" /> Helpful
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
