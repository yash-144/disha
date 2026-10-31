/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Base URL of the DISHA API. Empty/unset means same-origin (Vite proxies /api in dev). */
  readonly VITE_API_BASE_URL?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
