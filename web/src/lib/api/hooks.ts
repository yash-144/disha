import { useQuery } from '@tanstack/react-query'
import { identityApi, type Me } from './endpoints/identity'
import { ApiError } from './errors'

/**
 * Query keys live here (or in the domain's own hooks file) so invalidation is
 * predictable. Convention: ['<domain>', '<resource>', ...params].
 */
export const queryKeys = {
  me: ['identity', 'me'] as const,
}

/** Example hook / pattern: the signed-in user's profile and campus memberships. */
export function useMe(options: { enabled?: boolean } = {}) {
  return useQuery<Me, ApiError>({
    queryKey: queryKeys.me,
    queryFn: ({ signal }) => identityApi.me(signal),
    enabled: options.enabled ?? true,
    staleTime: 5 * 60_000,
  })
}
