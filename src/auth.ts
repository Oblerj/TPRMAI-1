import NextAuth from "next-auth"

export const { handlers, signIn, signOut, auth } = NextAuth({
  // adapter: PrismaAdapter(prisma), // Disabled - using JWT sessions with manual user management
  providers: [
    {
      id: "oidc",
      name: "Sign In",
      type: "oidc",
      issuer: process.env.OIDC_ISSUER_URL,
      clientId: process.env.OIDC_CLIENT_ID,
      clientSecret: process.env.OIDC_CLIENT_SECRET,
      authorization: {
        params: {
          scope: "openid email profile",
        },
      },
      checks: ["none"], // Disable all OAuth checks for dev environment
      profile(profile) {
        console.log('[Auth Profile]', profile)
        // Extract role from token (could be string or array)
        let role = 'ANALYST'
        if (profile.role) {
          role = profile.role
        } else if (profile.roles) {
          role = Array.isArray(profile.roles) ? profile.roles[0] : profile.roles
        }

        return {
          id: profile.sub,
          name: profile.name || profile.preferred_username,
          email: profile.email || profile.preferred_username,
          role: role,
        }
      },
    },
  ],
  session: {
    strategy: "jwt",
  },
  pages: {
    signIn: '/login',
  },
  callbacks: {
    async signIn() {
      return true
    },
    async jwt({ token, user, profile }) {
      if (profile) {
        const prof = profile as any
        token.role = prof.role || prof.roles || 'ANALYST'
        token.email = prof.email
        token.sub = prof.sub
      }
      if (user) {
        token.role = (user as any).role
      }
      return token
    },
    async session({ session, token }) {
      const user = session.user as any
      if (user && token) {
        user.role = String(token.role || 'ANALYST')
        user.sub = String(token.sub || '')
      }
      return session
    },
  },
  debug: false,
})
