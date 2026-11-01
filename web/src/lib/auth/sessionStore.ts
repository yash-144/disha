/**
 * Holds only the active campus (sent as X-Campus-ID). It is not a secret.
 * Credentials are owned by the AuthProvider (lib/auth/provider.ts).
 */

const STORAGE_KEY = 'disha.campus.v1'

type Listener = () => void

function read(): string | null {
  try {
    return sessionStorage.getItem(STORAGE_KEY)
  } catch {
    return null
  }
}

let campusId: string | null = read()
const listeners = new Set<Listener>()

export const sessionStore = {
  getCampusId(): string | null {
    return campusId
  },
  setCampusId(next: string | null) {
    campusId = next
    try {
      if (next) sessionStorage.setItem(STORAGE_KEY, next)
      else sessionStorage.removeItem(STORAGE_KEY)
    } catch {
      // ignore: kept in memory for this page load
    }
    listeners.forEach((l) => l())
  },
  subscribe(listener: Listener): () => void {
    listeners.add(listener)
    return () => listeners.delete(listener)
  },
}
