import React from 'react'
import { ArrowRight } from 'lucide-react'
import { useApp } from '../../context/AppContext'
import { useSession } from '../../lib/auth/SessionProvider'
import { AccountMenu } from '../common/AccountMenu'
import { SignalArt } from '../common/SignalArt'
import { Wordmark } from '../common/AppSidebar'
import { LanguageSwitcher } from '../common/HeaderControls'
import { useT } from '../../i18n'

const FACTS = [
  { n: 'Weekly', t: 'risk score for every student in every course' },
  { n: 'Plain', t: 'language reasons behind every flag' },
  { n: 'One', t: 'named owner for every case, tracked to an outcome' },
]

export function HeroSection() {
  const { navigateTo } = useApp()
  const t = useT()
  const { status } = useSession()
  const signedIn = status === 'authenticated' || status === 'not_provisioned'
  const scrollTo = (id: string) => document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' })
  const goDashboard = () => navigateTo('dashboard')

  return (
    <section className="relative flex min-h-screen w-full flex-col bg-night px-4 py-6 font-sans text-white sm:px-8 lg:px-12 xl:px-16">
      <nav className="mx-auto flex w-full max-w-[1400px] items-center justify-between" aria-label="Site">
        <button onClick={() => navigateTo('landing')} className="cursor-pointer" aria-label="Disha home"><Wordmark /></button>
        <div className="hidden items-center gap-8 text-[13px] text-white/70 md:flex">
          <button onClick={() => scrollTo('why-disha')} className="cursor-pointer hover:text-white">{t('Why Disha')}</button>
          <button onClick={() => scrollTo('solutions')} className="cursor-pointer hover:text-white">{t('Solutions')}</button>
          <button onClick={() => scrollTo('faqs')} className="cursor-pointer hover:text-white">{t('FAQs')}</button>
        </div>
        <div className="flex items-center gap-3">
          <div className="[&_button]:border-white/25 [&_button]:bg-transparent [&_button]:text-white [&_button:hover]:bg-white/10"><LanguageSwitcher /></div>
          {signedIn ? (
            <>
              <button onClick={goDashboard} className="cursor-pointer rounded-md bg-white px-4 py-2 text-[13px] font-semibold text-ink hover:bg-white/90">{t('Go to dashboard')}</button>
              <AccountMenu tone="dark" />
            </>
          ) : (
            <>
              <button onClick={() => navigateTo('login')} className="hidden cursor-pointer px-2 text-[13px] text-white/80 hover:text-white sm:inline-block">{t('Sign in')}</button>
              <button onClick={() => navigateTo('login')} className="cursor-pointer rounded-md bg-white px-4 py-2 text-[13px] font-semibold text-ink hover:bg-white/90">{t('Get started')}</button>
            </>
          )}
        </div>
      </nav>

      <div className="mx-auto my-auto grid w-full max-w-[1400px] items-center gap-12 py-16 lg:grid-cols-12">
        <div className="lg:col-span-7">
          <h1 className="font-display text-[clamp(3rem,7.2vw,6rem)] leading-[0.98] tracking-tight">
            {t('Catch struggling students early.')}
            <span className="mt-2 block text-white/55">{t('No alert without action.')}</span>
          </h1>
          <p className="mt-7 max-w-lg text-base leading-relaxed text-white/70">
            {t('Disha scores risk every week, explains why, and turns each flag into a case with an owner.')}
          </p>
          <div className="mt-9 flex flex-wrap items-center gap-3">
            <button onClick={signedIn ? goDashboard : () => navigateTo('login')} className="inline-flex cursor-pointer items-center gap-2 rounded-md bg-accent px-6 py-3.5 text-sm font-semibold text-white transition hover:bg-[#2c63e8]">
              {signedIn ? t('Go to dashboard') : t('Sign in with Google')} <ArrowRight className="h-4 w-4" />
            </button>
            <button onClick={() => scrollTo('why-disha')} className="cursor-pointer rounded-md border border-white/25 px-6 py-3.5 text-sm font-medium text-white hover:bg-white/10">{t('How it works')}</button>
          </div>
        </div>
        <div className="lg:col-span-5"><SignalArt className="w-full" /></div>
      </div>

      <dl className="mx-auto grid w-full max-w-[1400px] gap-px border-t border-white/15 pt-6 sm:grid-cols-3">
        {FACTS.map((f) => (
          <div key={f.n} className="pr-6 pt-2">
            <dt className="font-display text-3xl">{f.n}</dt>
            <dd className="mt-1 text-[13px] text-white/60">{f.t}</dd>
          </div>
        ))}
      </dl>
    </section>
  )
}
