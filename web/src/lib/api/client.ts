import type { ZodType } from 'zod'
import { sessionStore } from '../auth/sessionStore'
import { getAccessToken, getAuthProvider } from '../auth/provider'
import { ApiError, parseErrorBody } from './errors'

/**
 * Typed fetch wrapper for the DISHA API. Real requests only; there are no
 * fallback or fake responses anywhere in this module.
 *
 * - Base URL is fixed at build time (VITE_API_BASE_URL). Empty = same-origin,
 *   which in dev is proxied to the API by Vite.
 * - Auth: `Authorization: Bearer <token>` from the registered AuthProvider (lib/auth/provider.ts).
 * - Tenancy: `X-Campus-ID: <active campus>` (required by get_tenancy_context).
 * - Every request carries a fresh `X-Request-ID`; the API echoes it back and
 *   it is attached to ApiError for support/debugging.
 * - On 401 for an authenticated request, the provider's refresh() is tried once
 *   and the request replayed. A second 401 signs the user out.
 */

export const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/+$/, '')

type Query = Record<string, string | number | boolean | null | undefined | readonly (string | number)[]>

export interface RequestOptions<T = unknown> {
  query?: Query
  /** JSON-serialised request body. */
  body?: unknown
  /** Send no Authorization/X-Campus-ID headers (public endpoints). */
  auth?: boolean
  /** Override the campus for this call (defaults to the active campus). */
  campusId?: string | null
  headers?: Record<string, string>
  signal?: AbortSignal
  /** Validate and type the JSON response at runtime. */
  schema?: ZodType<T>
  /** Internal: set when this call is the post-refresh replay. */
  _retried?: boolean
}

type UnauthorizedListener = () => void

let refreshInFlight: Promise<string | null> | null = null
const unauthorizedListeners = new Set<UnauthorizedListener>()

/** Called after a 401 that could not be recovered (the user has been signed out). */
export function onUnauthorized(listener: UnauthorizedListener): () => void {
  unauthorizedListeners.add(listener)
  return () => unauthorizedListeners.delete(listener)
}

/** Single-flight token refresh through the registered auth provider. */
function refreshAccessToken(): Promise<string | null> {
  const refresh = getAuthProvider().refresh
  if (!refresh) return Promise.resolve(null)
  if (!refreshInFlight) {
    refreshInFlight = refresh()
      .catch(() => null)
      .finally(() => {
        refreshInFlight = null
      })
  }
  return refreshInFlight
}

function newRequestId(): string {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) return crypto.randomUUID()
  return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`
}

function buildUrl(path: string, query?: Query): string {
  const url = `${API_BASE_URL}${path.startsWith('/') ? path : `/${path}`}`
  if (!query) return url
  const params = new URLSearchParams()
  for (const [key, value] of Object.entries(query)) {
    if (value === undefined || value === null) continue
    if (Array.isArray(value)) value.forEach((v) => params.append(key, String(v)))
    else params.append(key, String(value))
  }
  const qs = params.toString()
  return qs ? `${url}${url.includes('?') ? '&' : '?'}${qs}` : url
}

async function readBody(res: Response): Promise<unknown> {
  if (res.status === 204 || res.status === 205) return undefined
  const text = await res.text()
  if (!text) return undefined
  try {
    return JSON.parse(text)
  } catch {
    return text
  }
}

export async function request<T = unknown>(
  method: string,
  path: string,
  options: RequestOptions<T> = {},
): Promise<T> {
  const { query, body, auth = true, campusId, headers: extraHeaders, signal, schema } = options

  const headers: Record<string, string> = {
    Accept: 'application/json',
    'X-Request-ID': newRequestId(),
    ...extraHeaders,
  }
  if (body !== undefined) headers['Content-Type'] = 'application/json'

  let sentToken: string | null = null
  if (auth) {
    sentToken = await getAccessToken()
    if (sentToken) headers.Authorization = `Bearer ${sentToken}`
    const campus = campusId === undefined ? sessionStore.getCampusId() : campusId
    if (campus) headers['X-Campus-ID'] = campus
  }

  let res: Response
  try {
    res = await fetch(buildUrl(path, query), {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
      signal,
    })
  } catch (err) {
    if (err instanceof DOMException && err.name === 'AbortError') throw err
    throw new ApiError({
      status: 0,
      message: 'Cannot reach the DISHA server. Check your connection and try again.',
    })
  }

  const requestId = res.headers.get('X-Request-ID') ?? headers['X-Request-ID']

  if (!res.ok) {
    if (res.status === 401 && auth && sentToken && !options._retried) {
      // One refresh, one replay. A second 401 means the session is dead: sign out.
      const fresh = await refreshAccessToken()
      if (fresh) return request<T>(method, path, { ...options, _retried: true })
      await getAuthProvider().signOut?.()
      unauthorizedListeners.forEach((l) => l())
    } else if (res.status === 401 && auth && options._retried) {
      await getAuthProvider().signOut?.()
      unauthorizedListeners.forEach((l) => l())
    }
    throw parseErrorBody(res.status, await readBody(res), requestId, res.statusText)
  }

  const data = await readBody(res)
  if (schema) {
    const parsed = schema.safeParse(data)
    if (!parsed.success) {
      throw new ApiError({
        status: res.status,
        message: 'The server returned a response in an unexpected format.',
        details: { issues: parsed.error.issues.map((i) => `${i.path.join('.')}: ${i.message}`) },
        requestId,
        body: data,
      })
    }
    return parsed.data
  }
  return data as T
}

export const api = {
  get: <T = unknown>(path: string, options?: RequestOptions<T>) => request<T>('GET', path, options),
  post: <T = unknown>(path: string, body?: unknown, options?: RequestOptions<T>) =>
    request<T>('POST', path, { ...options, body }),
  put: <T = unknown>(path: string, body?: unknown, options?: RequestOptions<T>) =>
    request<T>('PUT', path, { ...options, body }),
  patch: <T = unknown>(path: string, body?: unknown, options?: RequestOptions<T>) =>
    request<T>('PATCH', path, { ...options, body }),
  delete: <T = unknown>(path: string, options?: RequestOptions<T>) => request<T>('DELETE', path, options),
}

export { ApiError, isApiError, errorMessage } from './errors'
