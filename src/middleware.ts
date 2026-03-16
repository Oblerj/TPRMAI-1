import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

// Auth protection is handled at page level to avoid Edge Runtime issues
// with NextAuth v5 + complex JWT/session callbacks
export function middleware(request: NextRequest) {
  // Allow all requests - pages will check authentication
  return NextResponse.next()
}

export const config = {
  matcher: [
    '/dashboard/:path*',
    '/vendors/:path*',
    '/agents/:path*',
    '/findings/:path*',
    '/reports/:path*',
    '/admin/:path*',
  ],
}
