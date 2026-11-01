# SkillsUp – Hackathon theme + Dashboard

Each folder is a drop-in `src/` for a Vite + React + TS + Tailwind v4 project.

    npm create vite@latest app -- --template react-ts
    cd app && npm i lucide-react tailwindcss @tailwindcss/vite

vite.config.ts: add `import tailwindcss from '@tailwindcss/vite'` and `plugins: [react(), tailwindcss()]`

Copy a folder's contents into `src/`, then in `main.tsx`:

    import './index.css'
    import Page from './index'   // hackathon-theme/index.tsx or dashboard/index.tsx
    createRoot(document.getElementById('root')!).render(<Page />)

Both use different `@theme` colours/fonts in index.css, so use one per app (or merge).

## DISHA web: configuration and development

    cp .env.example .env.local   # optional
    npm install
    npm run dev                  # http://localhost:5173

- `VITE_API_BASE_URL`: API base URL, fixed at build time. Leave empty in dev:
  Vite proxies `/api` to `http://localhost:8000` (override with `DISHA_API_PROXY_TARGET`).
- Sign-in is not wired up yet. `src/lib/auth/provider.ts` defines the `AuthProvider`
  seam (Supabase Google sign-in is the planned provider). Until one is registered the
  portals show "Sign-in is not set up yet".
- API client and conventions: `src/lib/api/README.md`.
- Checks: `npx tsc --noEmit` and `npm run build`.
