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
