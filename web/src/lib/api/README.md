# API layer

Real HTTP only. There are no mock or fallback responses; a screen without an
endpoint yet shows an empty/"coming soon" state, not fake data.

## Pieces

- `client.ts`: `api.get/post/put/patch/delete`. Adds `Authorization: Bearer <token>`
  (from the `AuthProvider`, `lib/auth/provider.ts`), `X-Campus-ID` (active
  membership's campus; the API requires it for campus-scoped routes) and
  `X-Request-ID`. On 401 it tries `provider.refresh()` once, replays, then
  signs out. Pass `schema` (zod) to validate and type a response.
- `errors.ts`: `ApiError` (`status`, `message`, `details`, `fieldErrors`,
  `requestId`; helpers `isForbidden`, `isConflict`, ...). Parses the API's
  `{error, details, request_id}`, `{detail}` and 422 `{detail: [...]}` shapes.
- `queryClient.ts`: shared TanStack Query client (no retry on 4xx).
- `hooks.ts`: query keys and `useMe` (the pattern to copy).

## Adding an endpoint (portal agents)

1. `endpoints/<domain>.ts`: zod schemas + a plain object of functions that call `api`.
   Mirror the backend module (`api/app/modules/<domain>`). Paths start with `/api/v1/...`.
   ```ts
   export const casesApi = {
     list: (signal?: AbortSignal) => api.get('/api/v1/cases/', { schema: caseListSchema, signal }),
     update: (id: string, body: CaseUpdate) => api.patch(`/api/v1/cases/${id}`, body, { schema: caseSchema }),
   }
   ```
2. `hooks.ts` (or `endpoints/<domain>.hooks.ts` if it grows): `useQuery`/`useMutation`
   wrappers with keys `['<domain>', '<resource>', ...params]`. Mutations invalidate
   the affected keys. Case screens send the loaded `version` and reload on 409 (`error.isConflict`).
3. Render with `QueryState`; never read domain data from `AppContext`.

## Loading / empty / error

`components/common/QueryState.tsx`:

```tsx
const cases = useCases()
<QueryState query={cases} empty={<EmptyState title="No cases" message="..." />}>
  {(rows) => <CaseTable rows={rows} />}
</QueryState>
```

`LoadingSkeleton`, `EmptyState`, `ErrorState` (with retry and request reference)
are also exported for custom layouts. Forms show `error.fieldErrors` next to fields
and `error.message` otherwise. Do not store restricted fields (finance, counselling,
reflections) in browser storage.

## Session

`useSession()` (`lib/auth/SessionProvider.tsx`) gives `status`, `user` (from
`GET /api/v1/identity/me`), `membership`, `role`, `portal`, `signOut`. The role
always comes from the server. Roles map to portals in `lib/auth/portals.ts`
(faculty/mentor/hod -> instructor, institution_admin/platform_admin -> admin).
