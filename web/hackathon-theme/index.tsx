import React, { useState } from 'react'
import {
  Search,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  GraduationCap,
  Star,
  Globe,
  User,
  Briefcase,
  Monitor,
  Palette,
  Database,
  Code2,
  Puzzle,
  Cloud,
  Lock,
  MousePointer2,
} from 'lucide-react'
import { Marquee } from './components/Marquee'
import { Team } from './components/Team'
import { Newsletter } from './components/Newsletter'
import { Testimonials } from './components/Testimonials'
import { LiveClasses } from './components/LiveClasses'
import { Blog } from './components/Blog'
import { Contact } from './components/Contact'
import { SiteFooter } from './components/SiteFooter'

export const args = {
  headline: 'Unlock your potential with',
  activeCategory: 1,
  learners: '7,000+',
  courseCount: '60+',
}

export const argTypes = {
  headline: { control: 'text' },
  activeCategory: { control: 'select', options: [0, 1, 2] },
  learners: { control: 'text' },
  courseCount: { control: 'text' },
}

type Props = Partial<typeof args> & { onSignIn?: () => void; onRegister?: () => void }

const HERO_IMG = 'https://cdn.magicpatterns.com/patterns/generated-images/cf713b69-9da2-455b-a3d7-92775f29b709.jpg'
const LAPTOP_IMG = 'https://cdn.magicpatterns.com/patterns/generated-images/9d356a42-5f62-4613-aa3b-347f8bacf20a.jpg'
const TECH_IMG = 'https://cdn.magicpatterns.com/patterns/generated-images/f238c607-7db1-425e-b3d6-ddc24822a851.jpg'

export default function LandingPage(props: Props) {
  const { headline, activeCategory, learners, courseCount, onSignIn, onRegister } = { ...args, ...props }
  const [active, setActive] = useState<number>(Number(activeCategory))

  return (
    <div style={{ '--color-brand': '#1d5fd1', '--color-brand-dark': '#123f94', '--color-ink': '#0d1b3e', '--color-muted': '#4b5568', fontFamily: "'Roboto Mono', ui-monospace, monospace" } as React.CSSProperties} className="min-h-full w-full overflow-x-hidden bg-[#f5f5f5] text-ink">
      {/* Hero */}
      <section className="relative overflow-hidden border-b-4 border-ink pb-16 text-ink">
        <div className="pointer-events-none absolute inset-0 opacity-[0.08] [background-image:linear-gradient(90deg,#1d5fd1_1px,transparent_1px),linear-gradient(#1d5fd1_1px,transparent_1px)] [background-size:24px_24px]" />
        <nav className="relative mx-auto flex max-w-6xl items-center justify-between gap-6 px-6 py-5">
          <span className="text-2xl font-bold tracking-tight">
            <span className="text-[#0f9d58]">Skills</span><span className="text-brand">U</span><span className="text-[#0f9d58]">P</span>
          </span>
          <ul className="hidden items-center gap-9 text-sm md:flex">
            <li className="font-semibold">Home</li>
            <li className="text-muted">Courses</li>
            <li className="text-muted">Blogs</li>
            <li className="text-muted">About us</li>
          </ul>
          <div className="flex items-center gap-4 text-sm">
            <button onClick={onSignIn} className="whitespace-nowrap font-medium">Sign In</button>
            <button
              onClick={onRegister}
              className="whitespace-nowrap bg-[#0f9d58] px-5 py-2 font-bold text-white transition-colors duration-150 hover:bg-[#0b7a43]"
            >
              Register
            </button>
          </div>
        </nav>

        <div className="relative mx-auto grid max-w-6xl items-center gap-10 px-6 pt-6 lg:grid-cols-[1.15fr_1fr]">
          <div>
            <h1 className="text-[32px] font-bold leading-tight tracking-tight text-brand sm:text-[44px]">
              {headline}
              <span className="block text-ink">SkillsUp's skills development courses.</span>
            </h1>
            <p className="mt-5 max-w-lg text-sm leading-relaxed text-muted">
              We Offer a rich tapestry of skills development courses.
              <br />
              Hone your abilities, advance your career, and shape your success journey.
            </p>

            <div className="mt-7 flex max-w-xl flex-wrap items-center gap-2 border-2 border-ink bg-white p-1.5 text-sm text-muted shadow-[4px_4px_0_#0d1b3e] sm:flex-nowrap">
              <div className="flex min-w-0 flex-1 items-center gap-2 pl-4">
                <Search className="h-4 w-4 shrink-0" />
                <input placeholder="Search the course" className="w-full min-w-0 bg-transparent py-2 outline-none placeholder:text-gray-400" />
              </div>
              <button className="hidden items-center gap-1 border-l border-gray-200 px-4 text-xs sm:flex">
                Categories <ChevronDown className="h-3 w-3" />
              </button>
              <button className="hidden items-center gap-1 border-l border-gray-200 px-4 text-xs sm:flex">
                Options <ChevronDown className="h-3 w-3" />
              </button>
              <button className="bg-[#0f9d58] px-8 py-2.5 font-bold text-white transition-colors duration-150 hover:bg-[#0b7a43]">
                Search
              </button>
            </div>

            <div className="mt-9 flex gap-10 pl-4">
              <Stat icon={<GraduationCap className="h-7 w-7 text-[#0f9d58]" />} value="30K+" label="Graduates" />
              <Stat icon={<Star className="h-6 w-6 fill-[#0f9d58] text-[#0f9d58]" />} value="4.5" label="Avg. Rating" />
              <Stat icon={<Globe className="h-6 w-6 text-brand" />} value="27+" label="Countries" />
            </div>
          </div>

          <div className="relative mx-auto aspect-square w-full max-w-[420px]">
            <div className="absolute inset-2 translate-x-3 translate-y-3 rounded-2xl bg-[#0f9d58]" />
            <div className="absolute inset-2 overflow-hidden rounded-2xl border-2 border-ink bg-white">
              <img src={HERO_IMG} alt="Student with books" className="h-full w-full object-cover object-top" />
            </div>
            <div className="absolute -right-2 top-[22%] flex items-center gap-2 border-2 border-ink bg-[#0f9d58] px-3 py-2 text-white">
              <span className="text-xl font-bold">{courseCount}</span>
              <span className="text-[10px] leading-tight">Industry<br />courses</span>
            </div>
            <div className="absolute left-[8%] top-[8%] flex h-10 w-10 items-center justify-center border-2 border-ink bg-brand text-xs font-bold text-white">AI</div>
            <div className="absolute -left-2 bottom-[14%] flex items-center gap-3 border-2 border-ink bg-white px-4 py-2.5 text-ink">
              <span className="flex h-8 w-8 items-center justify-center bg-brand text-white">
                <User className="h-4 w-4" />
              </span>
              <div>
                <p className="text-lg font-bold leading-none">{learners}</p>
                <p className="text-[10px] text-muted">Happy learners</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <Marquee />

      {/* Categories */}
      <section className="mx-auto max-w-6xl px-6 pt-24">
        <h2 className="text-center text-2xl font-bold text-brand">Explore Courses by Popular Categories</h2>
        <div className="mt-12 flex items-center gap-4">
          <button
            onClick={() => setActive((a) => (a + 2) % 3)}
            className="hidden h-9 w-9 shrink-0 items-center justify-center border-2 border-ink bg-white text-ink transition-colors duration-150 hover:bg-gray-100 sm:flex"
            aria-label="Previous"
          >
            <ChevronLeft className="h-5 w-5" />
          </button>
          <div className="grid flex-1 gap-6 sm:grid-cols-3 lg:px-12">
            {CATEGORIES.map((c, i) => {
              const Icon = c.icon
              const on = i === active
              return (
                <button
                  key={c.title}
                  onClick={() => setActive(i)}
                  className={`relative flex flex-col items-center border-2 border-ink px-6 py-8 text-center transition-[transform,box-shadow] duration-200 ease-out ${c.bg} ${
                    on ? '-translate-y-1 shadow-[6px_6px_0_#0d1b3e]' : 'shadow-none'
                  }`}
                >
                  <span className={`flex h-20 w-24 items-center justify-center ${c.iconBg}`}>
                    <Icon className={`h-10 w-10 ${c.iconColor}`} strokeWidth={1.5} />
                  </span>
                  <span className="mt-5 text-sm font-medium leading-snug">{c.title}</span>
                  <span className="mt-2 text-[11px] leading-relaxed text-muted">{c.desc}</span>
                  {on && <MousePointer2 className="absolute -bottom-3 right-1/3 h-6 w-6 fill-brand text-white" />}
                </button>
              )
            })}
          </div>
          <button
            onClick={() => setActive((a) => (a + 1) % 3)}
            className="hidden h-9 w-9 shrink-0 items-center justify-center border-2 border-ink bg-brand text-white transition-colors duration-150 hover:bg-brand-dark sm:flex"
            aria-label="Next"
          >
            <ChevronRight className="h-5 w-5" />
          </button>
        </div>
      </section>

      {/* Benefits */}
      <section className="mx-auto grid max-w-6xl items-center gap-14 px-6 pt-28 lg:grid-cols-2">
        <div className="relative mx-auto w-full max-w-[520px]">
          <div className="absolute -left-6 top-6 grid grid-cols-6 gap-2 opacity-40">
            {Array.from({ length: 36 }).map((_, i) => (
              <span key={i} className="h-1 w-1 rounded-full bg-brand" />
            ))}
          </div>
          <div className="relative ml-auto w-[78%]">
            <img src={LAPTOP_IMG} alt="Learner on laptop" className="aspect-[4/3] w-full rounded-sm object-cover" />
          </div>
          <div className="relative -mt-14 ml-[18%] w-[62%] overflow-hidden rounded-sm">
            <img src={TECH_IMG} alt="Digital skills" className="aspect-video w-full object-cover" />
          </div>
          <div className="absolute left-0 top-[-6%] w-[42%] border-2 border-ink bg-[#0f9d58] p-5 text-white sm:p-6">
            <p className="text-base font-semibold leading-snug sm:text-lg">
              Empower Your Future <span className="font-normal">with Skill Development: Your Path to Success</span>
            </p>
          </div>
        </div>

        <div>
          <h2 className="text-2xl font-bold leading-snug text-brand sm:text-[28px]">
            5 key benefits of learning
            <br />
            skill development courses from us
          </h2>
          <ul className="mt-7 space-y-3 text-sm leading-relaxed text-gray-600">
            {BENEFITS.map(([title, body]) => (
              <li key={title} className="flex gap-3">
                <span className="mt-1.5 h-2 w-2 shrink-0 bg-[#0f9d58]" />
                <span>
                  <span className="text-gray-800">{title}:</span> {body}
                </span>
              </li>
            ))}
          </ul>
          <button className="mt-9 bg-[#0f9d58] px-9 py-3 text-sm font-bold text-white transition-colors duration-150 hover:bg-[#0b7a43]">
            Know More →
          </button>
        </div>
      </section>

      {/* Top-rated courses */}
      <section className="mx-auto max-w-6xl px-6 pb-16 pt-28">
        <h2 className="text-center text-2xl font-bold text-brand">Explore Top-Rated Courses</h2>
        <div className="mt-10 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {COURSES.map((c) => {
            const Icon = c.icon
            return (
              <article key={c.title} className="flex flex-col overflow-hidden border-2 border-ink bg-white shadow-[4px_4px_0_#0d1b3e]">
                <div className={`relative flex aspect-[16/9] items-center justify-center border-b-2 border-ink ${c.thumb}`}>
                  <span className="absolute left-3 top-3 flex items-center gap-1 rounded bg-white/90 px-1.5 py-0.5 text-[9px] font-medium text-ink">
                    <Lock className="h-2.5 w-2.5" /> Paid
                  </span>
                  <Icon className="h-14 w-14 text-white" strokeWidth={1.4} />
                </div>
                <div className="flex flex-1 flex-col p-4">
                  <h3 className="text-sm font-semibold leading-snug">{c.title}</h3>
                  <p className="mt-1.5 text-[11px] leading-relaxed text-muted">{c.desc}</p>
                  <div className="mt-2 flex items-center gap-1">
                    {Array.from({ length: 5 }).map((_, i) => (
                      <Star key={i} className="h-3 w-3 fill-amber-400 text-amber-400" />
                    ))}
                    <span className="ml-1 text-[10px] text-muted">({c.reviews})</span>
                  </div>
                  <p className="mt-auto pt-3 text-sm font-semibold">
                    {c.price} <span className="ml-1 text-xs font-normal text-gray-400 line-through">{c.was}</span>
                  </p>
                </div>
              </article>
            )
          })}
        </div>
        <p className="mt-12 text-center text-sm font-bold text-brand underline underline-offset-4">View more courses</p>
      </section>

      <LiveClasses />
      <Testimonials />
      <Team />
      <Blog />
      <Newsletter />
      <Contact />
      <SiteFooter />
    </div>
  )
}

function Stat({ icon, value, label }: { icon: React.ReactNode; value: string; label: string }) {
  return (
    <div className="flex flex-col items-center text-center">
      {icon}
      <span className="mt-1.5 text-base font-semibold leading-none">{value}</span>
      <span className="mt-1 text-[11px] text-muted">{label}</span>
    </div>
  )
}

const CATEGORIES = [
  {
    title: 'Business and Entrepreneurship',
    desc: 'Learn to start, run and grow a business with practical, real-world skills.',
    icon: Briefcase,
    bg: 'bg-white',
    iconBg: 'bg-[#0f9d58]',
    iconColor: 'text-white',
  },
  {
    title: 'Computer Science & IT',
    desc: 'Master programming, data and cloud technologies driving the digital world.',
    icon: Monitor,
    bg: 'bg-white',
    iconBg: 'bg-brand',
    iconColor: 'text-white',
  },
  {
    title: 'Design and Multimedia',
    desc: 'Create compelling visuals, interfaces and media that capture attention.',
    icon: Palette,
    bg: 'bg-white',
    iconBg: 'bg-[#0f9d58]',
    iconColor: 'text-white',
  },
]

const BENEFITS: [string, string][] = [
  ['Expert-led Learning', 'Gain skills from industry experts, ensuring quality education.'],
  ['Diverse Catalog', 'Choose from various courses to match your goals.'],
  ['Practical Skills', 'Acquire immediately applicable, hands-on knowledge.'],
  ['Flexible Study', 'Learn at your pace, fitting into your busy schedule.'],
  ['Certifications & Career Growth', 'Enhance your resume and job prospects with our certified courses.'],
]

const COURSES = [
  {
    title: 'The Complete 2024 Web Development Bootcamp',
    desc: 'Become a full-stack web developer with just one course. HTML, CSS, JavaScript, Node and more.',
    icon: Code2,
    thumb: 'bg-[#0f9d58]',
    reviews: '2,345',
    price: '₹1,599',
    was: '₹2,459',
  },
  {
    title: 'Advance Database Management and SQL',
    desc: 'Design, query and optimise relational databases with confidence using SQL.',
    icon: Database,
    thumb: 'bg-[#1d5fd1]',
    reviews: '1,128',
    price: '₹1,599',
    was: '₹2,459',
  },
  {
    title: 'Visual Elements of User Interface Design',
    desc: 'Learn the visual principles behind great interfaces: layout, colour, type and more.',
    icon: Puzzle,
    thumb: 'bg-[#0f9d58]',
    reviews: '987',
    price: '₹1,749',
    was: '₹2,959',
  },
  {
    title: '[NEW] Ultimate AWS Certified Cloud Program',
    desc: 'Prepare for the AWS certification with hands-on labs and real-world projects.',
    icon: Cloud,
    thumb: 'bg-[#0d1b3e]',
    reviews: '3,412',
    price: '₹1,599',
    was: '₹2,459',
  },
]
