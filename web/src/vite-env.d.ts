/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Base URL of the DISHA API. Empty/unset means same-origin (Vite proxies /api in dev). */
  readonly VITE_API_BASE_URL?: string
  readonly VITE_GOOGLE_CLIENT_ID?: string
  readonly VITE_GOOGLE_AUTH_URL?: string
  readonly VITE_GOOGLE_REDIRECT_URI?: string
  readonly VITE_API_URL?: string
  readonly VITE_MEKO_MCP_URL?: string
  readonly VITE_MEKO_API_KEY?: string
  readonly VITE_APP_ENV?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
