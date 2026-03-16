import { redirect } from 'next/navigation'
import { auth } from '@/auth'

/**
 * Server-side authentication guard for pages
 * Call this at the top of server components to require authentication
 *
 * @param redirectTo - Where to redirect if not authenticated (default: /login)
 * @returns The authenticated session
 */
export async function requireAuth(redirectTo: string = '/login') {
  const session = await auth()

  if (!session || !session.user) {
    redirect(redirectTo)
  }

  return session
}

/**
 * Check if user has a specific role
 */
export function hasRole(session: any, ...roles: string[]): boolean {
  if (!session?.user?.role) return false
  return roles.includes(session.user.role)
}

/**
 * Require specific role(s) - redirects to /login if not authorized
 */
export async function requireRole(...roles: string[]) {
  const session = await requireAuth()

  if (!hasRole(session, ...roles)) {
    redirect('/login')
  }

  return session
}
