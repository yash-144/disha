import { z } from 'zod'
import { api } from '../client'

/**
 * Identity endpoints (api/app/modules/identity/routes.py).
 * Sign-in is not wired up yet (see lib/auth/provider.ts); this endpoint returns
 * the profile and campus memberships of the authenticated user.
 */

export const membershipSchema = z.object({
  id: z.string().nullish(),
  campus_id: z.string(),
  role: z.string(),
  department: z.string().nullish(),
  is_active: z.boolean().default(true),
})

export const meSchema = z.object({
  id: z.string(),
  email: z.string(),
  full_name: z.string(),
  is_active: z.boolean(),
  created_at: z.string(),
  memberships: z.array(membershipSchema).default([]),
})

export type Membership = z.infer<typeof membershipSchema>
export type Me = z.infer<typeof meSchema>

export const identityApi = {
  /** GET /api/v1/identity/me */
  me: (signal?: AbortSignal) => api.get('/api/v1/identity/me', { schema: meSchema, signal }),
}
