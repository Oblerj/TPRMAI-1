'use server'

import { signIn, signOut, auth } from '@/auth'

export async function handleOIDCSignIn() {
  // Check if user is already authenticated
  const session = await auth()

  // If already logged in, sign out first to clear all cookies
  // This ensures a clean PKCE flow
  if (session) {
    await signOut({ redirect: false })
  }

  // Start fresh authentication flow
  await signIn('oidc', { redirectTo: '/dashboard' })
}
