import { useQueries, useQuery } from '@tanstack/react-query'
import { facultyApi } from './faculty'
import { counsellorApi } from './counsellor'

export const useFacultyDashboard = () =>
  useQuery({ queryKey: ['faculty', 'dashboard'], queryFn: ({ signal }) => facultyApi.dashboard(signal) })
export const useFacultyCases = () =>
  useQuery({ queryKey: ['faculty', 'cases'], queryFn: ({ signal }) => facultyApi.cases(signal) })
export const useFacultySections = () =>
  useQuery({ queryKey: ['faculty', 'sections'], queryFn: ({ signal }) => facultyApi.sections(signal) })
export function useSectionStudents(sectionIds: string[]) {
  return useQueries({
    queries: sectionIds.map((id) => ({
      queryKey: ['faculty', 'section-students', id],
      queryFn: ({ signal }: { signal?: AbortSignal }) => facultyApi.sectionStudents(id, signal),
    })),
  })
}
/** Risk tiers keyed by student_id; empty when no scoring run exists (404/409) or access is denied. */
export function useTierByStudent() {
  return useQuery({
    queryKey: ['ml', 'students', 'all-tiers'],
    retry: false,
    queryFn: async ({ signal }) => {
      const page = await counsellorApi.mlStudents(undefined, signal).catch(() => null)
      const map: Record<string, string> = {}
      page?.items.forEach((s) => { if (s.student_id) map[s.student_id] = s.tier })
      return map
    },
  })
}
