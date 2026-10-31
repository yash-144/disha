# 12 · Frontend Architecture

## 1. Facts about the current web app

| Item | Fact |
|---|---|
| Stack | Next.js 14 (App Router), React 18, TypeScript strict, Tailwind CSS 3, `gsap`, `lucide-react`, `@supabase/supabase-js` |
| Size | 52,024 source lines; 99 `.tsx` files, 93 of them client components (audit F2) |
| Route protection | None; no `middleware.ts`; every page renders for anyone (audit F2) |
| Demo layer | `?role=`, `?demo=`, `?walkthrough=` URL params and a `localStorage` flag switch on demo personas with pre-issued tokens and mock data (audit A5, S2) |
| State | `lib/skillhub-store.tsx` (2,187 lines) single React context for students, signals, cases, counsellor data, happiness, points, leaderboards, redemptions (audit F3) |
| API client | `lib/api.ts` (1,907 lines) mixes HTTP client with offline mock responses; base URL overridable from `localStorage` or `window.__DISHA_API_URL__` (audit F3, S8) |
| Server routes | `app/api/translate`, `app/api/shop/{balance,history,redeem}` run business logic in server memory (audit S5, F5) |
| Static-data features | Courses, community, messages, internships, rewards, shop render bundled data from `lib/skillhub-data.ts`, `lib/shop-data.ts` |
| Localisation | `lib/language-context.tsx` walks the DOM with `TreeWalker` + `MutationObserver`, posts every text node to Sarvam via `/api/translate`, caches in `localStorage`; `data-no-translate` used 0 times (audit F1, F6) |
| Quality gates | `eslint.ignoreDuringBuilds: true`; 132 `any` casts; `npm test` runs `tsc --noEmit` and three contract scripts; `__tests__/` unit files not run (audit F4) |
| Images | `next.config.mjs` allows optimisation for any `http`/`https` host (audit S8) |
| PWA | Service worker bypasses `/api` and caches static assets only |

Current pages: `/` (landing), `/login`, `/auth/callback`, `/onboarding`,
`/dashboard`, `/students`, `/students/[id]`, `/cases`, `/cases/[id]`,
`/analytics`, `/counselor/analytics`, `/request-support`, `/assessment`,
`/rewards`, `/shop`, `/courses`, `/community`, `/messages`, `/internships`,
`/calendar`, `/schedule`, `/documents`, `/documents/deploy`,
`/identity/deploy`, `/settings`, `/help`.

## 2. Requirements

### 2.1 Structure

| ID | Requirement | Audit |
|---|---|---|
| FE-01 | Route groups by audience: `(public)`, `(staff)`, `(student)`, `(admin)`; each group has a layout that checks the session and role on the server | F2 |
| FE-02 | `middleware.ts` refreshes the session and redirects unauthenticated users for every non-public route | F2 |
| FE-03 | Role for navigation and rendering comes from the server (`/auth/me`), never from URL or storage | F2, A5 |
| FE-04 | Feature folders by domain (`features/cases`, `features/signals`, `features/students`, `features/wellbeing`, …) each owning its components, hooks and API calls | F3 |
| FE-05 | No file over an agreed size (for example 400 lines) without review | F3 |
| FE-06 | Server components by default; client components only for interactivity | F2 |

### 2.2 Data

| ID | Requirement | Audit |
|---|---|---|
| FE-07 | A typed API client generated from the backend OpenAPI document | F3 |
| FE-08 | Server state through a query cache (TanStack Query or SWR) keyed per resource; no global store holding domain data | F3 |
| FE-09 | API base URL fixed at build time from environment | S8 |
| FE-10 | No mock responses, fixtures or personas in the production bundle; a demo, if needed, is a separate deployment pointing at a separate demo backend and database | A5, S2 |
| FE-11 | No business rules that affect students (points, eligibility, scoring) in the web app; it renders values computed by the API | F5 |
| FE-12 | No Next.js API routes containing business logic; if a BFF is used, it only forwards to the API with the user's session | S5, F5 |
| FE-13 | Optimistic concurrency: case screens send the version they loaded and handle 409 by reloading | A3 |

### 2.3 Session and security

| ID | Requirement |
|---|---|
| FE-14 | Session tokens in HTTP-only cookies; refresh handled server-side |
| FE-15 | Content Security Policy without `unsafe-inline` scripts where feasible |
| FE-16 | `next/image` remote patterns restricted to known hosts |
| FE-17 | Restricted fields (finance, counselling, reflections) never cached in browser storage |

### 2.4 Localisation

| ID | Requirement | Audit |
|---|---|---|
| FE-18 | UI strings come from message catalogues (one file per locale), loaded by an i18n library; components call `t(key)` | F1, F6 |
| FE-19 | Catalogue translation is done at build/authoring time (machine-assisted plus human review); no runtime translation of rendered DOM | F1, F6 |
| FE-20 | Record data (names, notes, explanations, reflections) is never sent to a translation service | F1 |
| FE-21 | Locale preference stored per user profile; no translated record data in `localStorage` | F1 |

Locales listed in ADR-007: `hi-IN`, `bn-IN`, `te-IN`, `mr-IN`, `ta-IN`,
`gu-IN`, `kn-IN`, `ml-IN`, `od-IN`, `pa-IN`, `as-IN`, plus English.

### 2.5 Quality

| ID | Requirement | Audit |
|---|---|---|
| FE-22 | ESLint runs in CI and blocks the build | F4 |
| FE-23 | `no-explicit-any` as error | F4 |
| FE-24 | Unit tests (Vitest/Jest + Testing Library) run by `npm test` | F4 |
| FE-25 | Accessibility checks (axe) on key pages; WCAG 2.1 AA target | F4 |
| FE-26 | End-to-end tests (Playwright) for the core journey per role | F4 |

## 3. Screens by audience (minimum set)

| Audience | Screens |
|---|---|
| Staff | Dashboard (my queue, overdue), Signals queue + review modal, Case list, Case detail (timeline, tasks, follow-ups, outcome), Student list, Student support view |
| Counsellor | Call requests, Escalations, Counselling tasks |
| Leadership | Cohort analytics (suppressed), Wellbeing aggregates |
| Admin | Members and invites, Roster and imports, Catalogue, Policy versions, Dead-letter notifications, Audit chain check |
| Student | Own support requests and case status (limited fields), Request counsellor call, Weekly pulse, Points and rewards (if enabled), Identity profile (if enabled) |
| Public | Landing, Sign-in, Accept invite |

Pages that currently render only bundled static data (courses, community,
messages, internships, calendar, schedule) need their own requirements and
backend modules before they are rebuilt. **Open decision:** which of these are
in scope.
