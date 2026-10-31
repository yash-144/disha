import React from 'react'
import { Mail, Phone, MapPin } from 'lucide-react'

export function Contact() {
  return (
    <section className="border-t-4 border-ink bg-white">
      <div className="mx-auto grid max-w-6xl gap-12 px-6 py-20 lg:grid-cols-[0.9fr_1.1fr]">
        <div className="relative mx-auto w-full max-w-md lg:max-w-none">
          <div className="absolute inset-0 translate-x-3 translate-y-3 bg-[#0f9d58]" />
          <img src={CONTACT_IMG} alt="SkillsUp support team" className="relative aspect-[4/5] w-full border-2 border-ink object-cover" />
        </div>

        <div>
          <h2 className="text-2xl font-bold leading-snug text-brand sm:text-[28px]">
            We're here to help <span className="text-ink">and ready to hear from you.</span>
          </h2>
          <ul className="mt-6 flex flex-wrap gap-x-8 gap-y-3 text-xs text-muted">
            <li className="flex items-center gap-2"><Mail className="h-4 w-4 text-brand" /> hello@skillsup.in</li>
            <li className="flex items-center gap-2"><Phone className="h-4 w-4 text-brand" /> +91 80 4567 1200</li>
            <li className="flex items-center gap-2"><MapPin className="h-4 w-4 text-brand" /> Bengaluru, India</li>
          </ul>

          <form className="mt-8 grid gap-4 sm:grid-cols-2" onSubmit={(e) => e.preventDefault()}>
            <Field label="Full name" placeholder="Riya Sharma" />
            <Field label="Email" placeholder="riya@email.com" type="email" />
            <div className="sm:col-span-2">
              <Field label="Subject" placeholder="Question about the Web Dev Bootcamp" />
            </div>
            <label className="sm:col-span-2">
              <span className="text-xs font-bold">Message</span>
              <textarea
                rows={4}
                placeholder="Tell us how we can help"
                className="mt-1.5 w-full resize-none border-2 border-ink bg-[#f5f5f5] px-3 py-2.5 text-sm outline-none placeholder:text-gray-400 focus:bg-white"
              />
            </label>
            <button className="w-fit bg-brand px-8 py-3 text-sm font-bold text-white transition-colors duration-150 hover:bg-brand-dark">
              Send message →
            </button>
          </form>
        </div>
      </div>
    </section>
  )
}

function Field({ label, placeholder, type = 'text' }: { label: string; placeholder: string; type?: string }) {
  return (
    <label className="block">
      <span className="text-xs font-bold">{label}</span>
      <input
        type={type}
        placeholder={placeholder}
        className="mt-1.5 w-full border-2 border-ink bg-[#f5f5f5] px-3 py-2.5 text-sm outline-none placeholder:text-gray-400 focus:bg-white"
      />
    </label>
  )
}

const CONTACT_IMG = 'https://cdn.magicpatterns.com/patterns/generated-images/bfde084f-b3be-4f39-aaf5-47438b04e41d.jpg'
