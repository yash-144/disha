import React, { useState } from 'react'
import { Mail, Phone, MapPin, Send, CheckCircle2 } from 'lucide-react'
import { useApp } from '../../context/AppContext'

const CONTACT_IMG = 'https://images.unsplash.com/photo-1522071820081-009f0129c71c?auto=format&fit=crop&w=700&q=80'

export function ContactSection() {
  const { addToast } = useApp()
  const [fullName, setFullName] = useState('')
  const [email, setEmail] = useState('')
  const [subject, setSubject] = useState('')
  const [message, setMessage] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)
    setTimeout(() => {
      setIsSubmitting(false)
      addToast(
        'Message Sent Successfully!',
        `Thank you ${fullName || 'learner'}, our advisors will reach out at ${email}.`,
        'success'
      )
      setFullName('')
      setEmail('')
      setSubject('')
      setMessage('')
    }, 600)
  }

  return (
    <section className="border-t-4 border-ink bg-white">
      <div className="mx-auto grid max-w-6xl gap-12 px-6 py-20 lg:grid-cols-[0.9fr_1.1fr]">
        {/* Support photo with neo-brutalist shadow */}
        <div className="relative mx-auto w-full max-w-md lg:max-w-none">
          <div className="absolute inset-0 translate-x-3 translate-y-3 bg-[#0f9d58]" />
          <img
            src={CONTACT_IMG}
            alt="SkillsUp support team"
            className="relative aspect-[4/5] w-full border-4 border-ink object-cover shadow-md"
          />
        </div>

        {/* Form Container */}
        <div>
          <span className="text-xs font-bold uppercase tracking-wider text-[#0f9d58]">
            Get In Touch
          </span>
          <h2 className="mt-1 text-2xl font-bold leading-snug text-brand sm:text-[32px]">
            We're here to help <span className="text-ink">and ready to hear from you.</span>
          </h2>

          <ul className="mt-6 flex flex-wrap gap-x-8 gap-y-3 text-xs text-muted">
            <li className="flex items-center gap-2">
              <Mail className="h-4 w-4 text-brand" /> admissions@skillsup.in
            </li>
            <li className="flex items-center gap-2">
              <Phone className="h-4 w-4 text-brand" /> +91 (80) 4567 1200
            </li>
            <li className="flex items-center gap-2">
              <MapPin className="h-4 w-4 text-brand" /> Bengaluru &amp; Remote Global
            </li>
          </ul>

          <form onSubmit={handleSubmit} className="mt-8 grid gap-4 sm:grid-cols-2">
            <div>
              <label className="text-xs font-bold text-ink">Full Name *</label>
              <input
                required
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Riya Sharma"
                className="mt-1.5 w-full border-2 border-ink bg-[#f5f5f5] px-3 py-2.5 text-xs font-medium outline-none placeholder:text-gray-400 focus:bg-white focus:ring-1 focus:ring-brand"
              />
            </div>

            <div>
              <label className="text-xs font-bold text-ink">Email Address *</label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="riya@example.com"
                className="mt-1.5 w-full border-2 border-ink bg-[#f5f5f5] px-3 py-2.5 text-xs font-medium outline-none placeholder:text-gray-400 focus:bg-white focus:ring-1 focus:ring-brand"
              />
            </div>

            <div className="sm:col-span-2">
              <label className="text-xs font-bold text-ink">Inquiry Subject</label>
              <input
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                placeholder="Question regarding Web Dev Bootcamp & Live Schedule"
                className="mt-1.5 w-full border-2 border-ink bg-[#f5f5f5] px-3 py-2.5 text-xs font-medium outline-none placeholder:text-gray-400 focus:bg-white focus:ring-1 focus:ring-brand"
              />
            </div>

            <div className="sm:col-span-2">
              <label className="text-xs font-bold text-ink">Message *</label>
              <textarea
                required
                rows={4}
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder="Tell us about your learning goals or questions..."
                className="mt-1.5 w-full resize-none border-2 border-ink bg-[#f5f5f5] px-3 py-2.5 text-xs font-medium outline-none placeholder:text-gray-400 focus:bg-white focus:ring-1 focus:ring-brand"
              />
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="flex w-fit items-center gap-2 border-2 border-ink bg-brand px-8 py-3 text-xs font-bold text-white shadow-[3px_3px_0_#0d1b3e] transition hover:bg-brand-dark"
            >
              {isSubmitting ? 'Sending...' : 'Send Message'} <Send className="h-3.5 w-3.5" />
            </button>
          </form>
        </div>
      </div>
    </section>
  )
}
