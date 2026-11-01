import { friendlyError } from '../labels'

/**
 * Typed API error. Normalises the three error shapes the DISHA API returns:
 *  1. DishaBaseException: { error, status_code, details, request_id }   (api/app/core/exceptions.py)
 *  2. FastAPI HTTPException: { detail: string }
 *  3. FastAPI validation (422): { detail: [{ loc, msg, type }] }
 */
export interface FieldError {
  /** Dotted path without the leading "body"/"query" segment, e.g. "email". */
  field: string
  message: string
}

export interface ApiErrorInit {
  status: number
  message: string
  details?: Record<string, unknown>
  fieldErrors?: FieldError[]
  requestId?: string | null
  body?: unknown
}

export class ApiError extends Error {
  readonly status: number
  /** Extra structured data from the server (`details` of DishaBaseException). */
  readonly details: Record<string, unknown>
  readonly fieldErrors: FieldError[]
  readonly requestId: string | null
  /** Raw parsed response body (or undefined when not JSON). */
  readonly body: unknown

  constructor(init: ApiErrorInit) {
    super(init.message)
    this.name = 'ApiError'
    this.status = init.status
    this.details = init.details ?? {}
    this.fieldErrors = init.fieldErrors ?? []
    this.requestId = init.requestId ?? null
    this.body = init.body
  }

  get isUnauthorized() {
    return this.status === 401
  }
  get isForbidden() {
    return this.status === 403
  }
  get isNotFound() {
    return this.status === 404
  }
  /** Optimistic-concurrency failure (blueprint FE-13): reload and retry. */
  get isConflict() {
    return this.status === 409
  }
  /**
   * 403 because the signed-in Google account has no DISHA membership yet.
   * Matches the API's "not provisioned" / "no active membership" wording.
   */
  get isNotProvisioned() {
    return this.status === 403 && /not provisioned|no active membership/i.test(this.message)
  }
  /** Network failure or non-HTTP problem (status 0). */
  get isNetwork() {
    return this.status === 0
  }
}

export function isApiError(e: unknown): e is ApiError {
  return e instanceof ApiError
}

/**
 * Message that is safe to show people: one short plain sentence, no status codes, ids or field names.
 * A server message is kept only when it already reads like a sentence.
 */
export function errorMessage(e: unknown): string {
  if (e instanceof ApiError) {
    const m = e.message ?? ''
    const plain = e.status >= 400 && e.status < 500 && e.status !== 422 && e.status !== 401 && m.length > 8 && m.length < 140 && !/[_{}\[\]:]|\d{3,}|\b[0-9a-f]{8}-[0-9a-f]{4}\b|Traceback|Error\b|HTTP|request/i.test(m)
    return plain ? m : friendlyError(e)
  }
  return friendlyError(e)
}

function asRecord(v: unknown): Record<string, unknown> | null {
  return v && typeof v === 'object' && !Array.isArray(v) ? (v as Record<string, unknown>) : null
}

export function parseErrorBody(
  status: number,
  body: unknown,
  headerRequestId: string | null,
  statusText: string,
): ApiError {
  const rec = asRecord(body)
  let message = statusText || `Request failed (${status})`
  let details: Record<string, unknown> = {}
  let fieldErrors: FieldError[] = []
  let requestId = headerRequestId

  if (rec) {
    if (typeof rec.error === 'string') {
      message = rec.error
      details = asRecord(rec.details) ?? {}
    } else if (typeof rec.detail === 'string') {
      message = rec.detail
    } else if (Array.isArray(rec.detail)) {
      fieldErrors = rec.detail.flatMap((item) => {
        const it = asRecord(item)
        if (!it) return []
        const loc = Array.isArray(it.loc) ? it.loc.slice(1).join('.') : ''
        return [{ field: loc, message: typeof it.msg === 'string' ? it.msg : 'Invalid value' }]
      })
      message = fieldErrors.length
        ? fieldErrors.map((f) => (f.field ? `${f.field}: ${f.message}` : f.message)).join('; ')
        : 'The request was not valid.'
    }
    if (typeof rec.request_id === 'string') requestId = rec.request_id
  }

  return new ApiError({ status, message, details, fieldErrors, requestId, body })
}
